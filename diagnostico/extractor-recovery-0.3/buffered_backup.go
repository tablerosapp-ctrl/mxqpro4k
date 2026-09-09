package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
)

const bufferedBackupBytes int64 = 64 << 20
const bufferedBackupMemoryMargin uint64 = 64 << 20

func validateBufferedBackupPlan(plan CapturePlan, partBytes int64, available func() (uint64, error)) error {
	if available == nil {
		return errors.New("buffered backup requires MemAvailable callback")
	}
	for i, source := range plan.Sources {
		if source.Name != "mmcblk0p10" {
			continue
		}
		if i != len(plan.Sources)-1 || source.Bytes != bufferedBackupBytes || partBytes < bufferedBackupBytes ||
			source.Kind != "partition" || source.Device != "/dev/block/mmcblk0p10" || source.MajorMinor != "179:10" {
			return errors.New("buffered backup only accepts the final exact 64 MiB backup partition")
		}
		if !sameAliasSet(source.Aliases, []string{"/dev/block/mmcblk0p10", rk3229CBlockPlatform + "by-name/backup", rk3229CBlockPlatform + "by-num/p10", rk3229CBlockPlatform + "mmcblk0p10"}) {
			return errors.New("buffered backup alias differs")
		}
	}
	return nil
}

// MemAvailable is preferred when exposed. On Linux 3.10 the conservative
// fallback discounts shared and dirty/writeback pages from the listed caches.
// Both are estimates; neither guarantees that a later allocation cannot fail.
func parseMemoryAvailable(data []byte) (uint64, error) {
	wanted := map[string]bool{"MemAvailable:": true, "MemTotal:": true, "MemFree:": true, "Buffers:": true, "Cached:": true, "Shmem:": true, "Dirty:": true, "Writeback:": true}
	values := map[string]uint64{}
	for _, line := range strings.Split(string(data), "\n") {
		fields := strings.Fields(line)
		if len(fields) == 0 || !wanted[fields[0]] {
			continue
		}
		if _, ok := values[fields[0]]; ok || len(fields) != 3 || fields[2] != "kB" {
			return 0, errors.New("memory field malformed or duplicate")
		}
		for _, c := range fields[1] {
			if c < '0' || c > '9' {
				return 0, errors.New("memory field is not an unsigned decimal")
			}
		}
		n, e := strconv.ParseUint(fields[1], 10, 64)
		if e != nil || n > ^uint64(0)/1024 {
			return 0, errors.New("memory field invalid or overflow")
		}
		values[fields[0]] = n * 1024
	}
	total, ok := values["MemTotal:"]
	if !ok || total == 0 {
		return 0, errors.New("MemTotal not exposed or invalid")
	}
	if available, ok := values["MemAvailable:"]; ok {
		if available > total {
			return 0, errors.New("MemAvailable exceeds MemTotal")
		}
		return available, nil
	}
	if total < 512<<20 {
		return 0, errors.New("memory estimate requires at least 512 MiB MemTotal")
	}
	for _, name := range []string{"MemFree:", "Buffers:", "Cached:", "Shmem:", "Dirty:", "Writeback:"} {
		value, ok := values[name]
		if !ok || value > total {
			return 0, fmt.Errorf("memory estimate missing or invalid %s", name)
		}
	}
	add := func(a, b uint64) (uint64, error) {
		if b > ^uint64(0)-a {
			return 0, errors.New("memory estimate overflow")
		}
		return a + b, nil
	}
	sum, e := add(values["MemFree:"], values["Buffers:"])
	if e != nil {
		return 0, e
	}
	sum, e = add(sum, values["Cached:"])
	if e != nil {
		return 0, e
	}
	if sum > total {
		return 0, errors.New("memory estimate components exceed total")
	}
	discount, e := add(values["Shmem:"], values["Dirty:"])
	if e != nil {
		return 0, e
	}
	discount, e = add(discount, values["Writeback:"])
	if e != nil {
		return 0, e
	}
	if discount >= sum {
		return 0, nil
	}
	return sum - discount, nil
}

func captureBufferedBackup(r *SourceReport, sourceIndex int, hooks CaptureHooks, buf []byte) error {
	return captureBufferedBackupSized(r, sourceIndex, hooks, buf, bufferedBackupBytes)
}

// expectedBytes is fixed to 64 MiB by the production wrapper. Small ordinary
// fixtures test the same sequence without allocating 64 MiB per error case.
func captureBufferedBackupSized(r *SourceReport, sourceIndex int, hooks CaptureHooks, buf []byte, expectedBytes int64) error {
	r.Status, r.VerificationOrder = "reading_source_to_memory", "source_source_destination"
	if r.Source.Bytes != expectedBytes || expectedBytes <= 0 || expectedBytes > bufferedBackupBytes || hooks.AvailableMemory == nil {
		return errors.New("buffered backup size or memory hook invalid")
	}
	available, e := hooks.AvailableMemory()
	if e != nil {
		return fmt.Errorf("backup memory budget: %w", e)
	}
	if available < uint64(expectedBytes)+bufferedBackupMemoryMargin {
		return fmt.Errorf("backup memory budget: have %d bytes, require %d; previous verified sources preserved", available, uint64(expectedBytes)+bufferedBackupMemoryMargin)
	}
	if e = hooks.Revalidate(); e != nil {
		return fmt.Errorf("before buffered source: %w", e)
	}
	ram := make([]byte, int(expectedBytes))
	reader, e := hooks.OpenSource(r.Source)
	if e != nil {
		return fmt.Errorf("open buffered source: %w", e)
	}
	progress := &progressReader{reader: reader, notify: hooks.Progress, state: Progress{Stage: "read_source_to_memory", SourceID: r.ID, Name: r.Source.Name, SourceIndex: sourceIndex, PartIndex: -1, BytesTotal: expectedBytes}}
	var readErr error
	for off := int64(0); off < expectedBytes; {
		end := off + int64(len(buf))
		if end > expectedBytes {
			end = expectedBytes
		}
		if end == off {
			readErr = errors.New("empty copy buffer")
			break
		}
		_, readErr = io.ReadFull(progress, ram[off:end])
		if readErr != nil {
			break
		}
		off = end
	}
	if readErr == nil {
		readErr = requireEOF(reader)
	}
	readErr = errors.Join(readErr, reader.Close())
	if readErr != nil {
		return fmt.Errorf("read buffered source: %w", readErr)
	}
	hash := sha256.Sum256(ram)
	r.SHA256 = hex.EncodeToString(hash[:])
	if e = hooks.Revalidate(); e != nil {
		return fmt.Errorf("before consecutive source reread: %w", e)
	}
	reader, e = hooks.OpenSource(r.Source)
	if e != nil {
		return fmt.Errorf("reopen buffered source: %w", e)
	}
	progress = &progressReader{reader: reader, notify: hooks.Progress, state: Progress{Stage: "verify_source_before_sd", SourceID: r.ID, Name: r.Source.Name, SourceIndex: sourceIndex, PartIndex: -1, BytesTotal: expectedBytes}}
	r.RereadSHA256, e = hashExact(progress, expectedBytes, buf)
	e = errors.Join(e, reader.Close())
	if e != nil {
		return fmt.Errorf("buffered source reread: %w", e)
	}
	if r.SHA256 != r.RereadSHA256 {
		return errors.New("source changed between consecutive reads (SHA256 mismatch); backup bytes were not written to SD")
	}
	if e = hooks.Revalidate(); e != nil {
		return fmt.Errorf("before buffered destination write: %w", e)
	}
	r.Status = "copying_verified_memory"
	r.Parts = append(r.Parts, PartReport{Index: 0, Name: fmt.Sprintf("%s.part-%06d.img.partial", r.ID, 0), Expected: expectedBytes, Status: "incomplete"})
	p := &r.Parts[0]
	out, e := hooks.Destination.CreateExclusive(p.Name)
	if e != nil {
		p.Error = e.Error()
		return fmt.Errorf("create buffered part: %w", e)
	}
	partHash := sha256.New()
	progress = &progressReader{reader: bytes.NewReader(ram), notify: hooks.Progress, state: Progress{Stage: "copy_memory_to_sd", SourceID: r.ID, Name: r.Source.Name, SourceIndex: sourceIndex, PartIndex: 0, BytesTotal: expectedBytes}}
	p.Copied, e = io.CopyBuffer(io.MultiWriter(out, partHash), progress, buf)
	if e == nil && p.Copied != expectedBytes {
		e = errors.New("short buffered destination write")
	}
	if e == nil {
		e = out.Sync()
	}
	e = errors.Join(e, out.Close())
	if e != nil {
		p.Error = e.Error()
		return fmt.Errorf("write/sync buffered part: %w", e)
	}
	p.SHA256 = hex.EncodeToString(partHash.Sum(nil))
	if p.SHA256 != r.SHA256 {
		return errors.New("memory copy SHA256 differs from first source read")
	}
	p.Status = "copied_synced"
	if e = hooks.Revalidate(); e != nil {
		return fmt.Errorf("before buffered destination verification: %w", e)
	}
	reader, e = hooks.Destination.OpenRead(p.Name)
	if e != nil {
		p.Error = e.Error()
		return fmt.Errorf("open buffered destination: %w", e)
	}
	progress = &progressReader{reader: reader, notify: hooks.Progress, state: Progress{Stage: "verify_destination", SourceID: r.ID, Name: r.Source.Name, SourceIndex: sourceIndex, PartIndex: 0, BytesTotal: expectedBytes}}
	digest, e := hashExact(progress, expectedBytes, buf)
	e = errors.Join(e, reader.Close())
	if e == nil && digest != r.SHA256 {
		e = errors.New("destination SHA256 mismatch")
	}
	if e != nil {
		p.Error = e.Error()
		return fmt.Errorf("verify buffered destination: %w", e)
	}
	p.Status = "destination_verified"
	if e = hooks.Revalidate(); e != nil {
		return fmt.Errorf("after buffered destination verification: %w", e)
	}
	if e = hooks.Destination.Sync(); e != nil {
		return fmt.Errorf("persist buffered part directory: %w", e)
	}
	p.Status, r.Status = "verified", "verified"
	if hooks.Progress != nil {
		hooks.Progress(Progress{Stage: "verified", SourceID: r.ID, Name: r.Source.Name, SourceIndex: sourceIndex, PartIndex: -1, BytesDone: expectedBytes, BytesTotal: expectedBytes})
	}
	return nil
}
