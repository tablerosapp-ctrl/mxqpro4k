package main

// This file is the platform-independent capture engine. It deliberately has no
// device discovery, path opening, mounting, network, deletion or reboot code.

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
)

const (
	PartBytes         int64  = 1 << 30
	SpaceReserve      uint64 = 128 << 20
	MaxSourceBytes    int64  = 1 << 40
	MaxSources               = 64
	captureBufferSize        = 256 << 10
)

// Source is an immutable description supplied by the platform's read-only
// resolver. Device is metadata; the engine never opens it as a filesystem path.
type Source struct {
	Name       string   `json:"name"`
	Device     string   `json:"device"`
	Bytes      int64    `json:"bytes"`
	MajorMinor string   `json:"major_minor"`
	Kind       string   `json:"kind"`
	Aliases    []string `json:"aliases,omitempty"`
}

type Omission struct {
	Name   string `json:"name"`
	Device string `json:"device,omitempty"`
	Reason string `json:"reason"`
}

type CapturePlan struct {
	Sources []Source   `json:"sources"`
	Omitted []Omission `json:"omitted,omitempty"`
}

type SyncWriteCloser interface {
	io.Writer
	Sync() error
	Close() error
}

// Destination must be confined to the one new, validated output directory.
// CreateExclusive MUST use exclusive creation of regular files only; OpenRead
// MUST reject symlinks and non-regular files. Neither method may replace files.
// Sync must persist directory metadata or fail; explicitly unsupported sync can
// only be handled by the platform policy, never silently swallowed here.
type Destination interface {
	CreateExclusive(name string) (SyncWriteCloser, error)
	OpenRead(name string) (io.ReadCloser, error)
	Sync() error
}

type Progress struct {
	Stage       string
	SourceID    string
	Name        string
	SourceIndex int
	PartIndex   int
	BytesDone   int64
	BytesTotal  int64
}

// OpenSource MUST open the resolved source read-only and validate its identity,
// size and geometry on every call. Revalidate MUST verify the original plan,
// mounts, block topology and destination identity without changing them.
type CaptureHooks struct {
	OpenSource      func(Source) (io.ReadCloser, error)
	Revalidate      func() error
	FreeBytes       func() (uint64, error)
	Destination     Destination
	Progress        func(Progress)
	BufferedBackup  bool
	AvailableMemory func() (uint64, error)
}

type PartReport struct {
	Index    int    `json:"index"`
	Name     string `json:"name"`
	Expected int64  `json:"expected_bytes"`
	Copied   int64  `json:"copied_bytes"`
	SHA256   string `json:"sha256,omitempty"`
	Status   string `json:"status"`
	Error    string `json:"error,omitempty"`
}

type SourceReport struct {
	Source            Source       `json:"source"`
	ID                string       `json:"id"`
	Status            string       `json:"status"`
	SHA256            string       `json:"sha256,omitempty"`
	RereadSHA256      string       `json:"reread_sha256,omitempty"`
	Parts             []PartReport `json:"parts,omitempty"`
	Error             string       `json:"error,omitempty"`
	VerificationOrder string       `json:"verification_order,omitempty"`
}

type Report struct {
	Format        string         `json:"format"`
	Status        string         `json:"status"`
	ExpectedBytes uint64         `json:"expected_bytes"`
	RequiredBytes uint64         `json:"required_bytes"`
	FreeBytes     uint64         `json:"free_bytes_at_preflight"`
	PartBytes     int64          `json:"part_bytes"`
	Sources       []SourceReport `json:"sources"`
	Omitted       []Omission     `json:"omitted,omitempty"`
	Error         string         `json:"error,omitempty"`
	Limit         string         `json:"limit"`
}

// Capture copies each source in <=1 GiB parts, syncs and rereads each part, then
// reopens and rereads the full source. It stops on any error and preserves every
// file already created. The fixed .partial names are intentional: only a
// verified manifest identifies usable parts; extensions are never proof.
//
// A persisted report status "data_verified" describes verified bytes, not an
// independently signed receipt or a tested restore. Capture's nil error also
// requires the report's own sync, reread and directory sync to have succeeded.
// A failed-report.json, when present, always takes precedence over report.json.
func Capture(plan CapturePlan, hooks CaptureHooks) (Report, error) {
	return captureWithPartBytes(plan, hooks, PartBytes)
}

// The production entry point cannot change the part size. Small parts are used
// only by unit tests so boundary checks do not require GiB fixture files.
func captureWithPartBytes(plan CapturePlan, hooks CaptureHooks, partBytes int64) (Report, error) {
	r := Report{Format: "tvbase-recovery-capture-0.1", Status: "failed", PartBytes: partBytes,
		Omitted: append([]Omission(nil), plan.Omitted...),
		Limit:   "Selected read-only sources only; not proof of complete eMMC acquisition, authenticity, absence of malware, or successful restoration. A failed-report.json takes precedence. Part files retain .partial names; use per-source status. A nil engine error is required for report persistence and directory sync."}
	if err := validatePlan(plan, partBytes); err != nil {
		r.Error = err.Error()
		return r, err
	}
	if hooks.OpenSource == nil || hooks.Revalidate == nil || hooks.FreeBytes == nil || hooks.Destination == nil {
		err := errors.New("missing mandatory capture hook")
		r.Error = err.Error()
		return r, err
	}
	if hooks.BufferedBackup {
		if err := validateBufferedBackupPlan(plan, partBytes, hooks.AvailableMemory); err != nil {
			r.Error = err.Error()
			return r, err
		}
	}
	// Copy descriptors so callbacks cannot accidentally mutate the plan's slices.
	for _, source := range plan.Sources {
		source.Aliases = append([]string(nil), source.Aliases...)
		encoded, _ := json.Marshal(source)
		digest := sha256.Sum256(encoded)
		r.Sources = append(r.Sources, SourceReport{Source: source, ID: hex.EncodeToString(digest[:]), Status: "not_attempted"})
		r.ExpectedBytes += uint64(source.Bytes)
	}
	r.RequiredBytes = r.ExpectedBytes + SpaceReserve
	// Failure before revalidation must not attempt to write to an untrusted path.
	if err := hooks.Revalidate(); err != nil {
		return failReport(r, fmt.Errorf("preflight revalidation: %w", err), -1, hooks, false)
	}
	free, err := hooks.FreeBytes()
	if err != nil {
		return failReport(r, fmt.Errorf("preflight free space: %w", err), -1, hooks, true)
	}
	r.FreeBytes = free
	if free < r.RequiredBytes {
		return failReport(r, fmt.Errorf("insufficient space: have %d, require %d", free, r.RequiredBytes), -1, hooks, true)
	}
	buf := make([]byte, captureBufferSize)
	for i := range r.Sources {
		if err := hooks.Revalidate(); err != nil {
			return failReport(r, fmt.Errorf("before source %d: %w", i, err), i, hooks, false)
		}
		var err error
		if hooks.BufferedBackup && r.Sources[i].Source.Name == "mmcblk0p10" {
			err = captureBufferedBackup(&r.Sources[i], i, hooks, buf)
		} else {
			err = captureOne(&r.Sources[i], i, hooks, partBytes, buf)
		}
		if err != nil {
			return failReport(r, fmt.Errorf("source %q: %w", r.Sources[i].Source.Name, err), i, hooks, true)
		}
	}
	if err := hooks.Revalidate(); err != nil {
		return failReport(r, fmt.Errorf("final revalidation: %w", err), len(r.Sources), hooks, false)
	}
	r.Status = "data_verified"
	if err := writeReport(hooks.Destination, "report.json", r); err != nil {
		return failReport(r, fmt.Errorf("persist report: %w", err), len(r.Sources), hooks, true)
	}
	return r, nil
}

func validatePlan(plan CapturePlan, partBytes int64) error {
	if len(plan.Sources) == 0 || len(plan.Sources) > MaxSources {
		return fmt.Errorf("source count must be 1..%d", MaxSources)
	}
	if partBytes <= 0 || partBytes > PartBytes {
		return errors.New("invalid part size")
	}
	if len(plan.Omitted) > 256 {
		return errors.New("too many omission records")
	}
	devices, identities := map[string]bool{}, map[string]bool{}
	for i, s := range plan.Sources {
		if s.Bytes <= 0 || s.Bytes > MaxSourceBytes {
			return fmt.Errorf("source %d size must be 1..%d", i, MaxSourceBytes)
		}
		for _, value := range []string{s.Name, s.Device, s.MajorMinor, s.Kind} {
			if value == "" || len(value) > 1024 || strings.ContainsRune(value, 0) {
				return fmt.Errorf("source %d has missing or invalid metadata", i)
			}
		}
		if len(s.Aliases) > 128 {
			return fmt.Errorf("source %d has too many aliases", i)
		}
		for _, alias := range s.Aliases {
			if len(alias) > 1024 || strings.ContainsRune(alias, 0) {
				return fmt.Errorf("source %d has invalid alias", i)
			}
		}
		if devices[s.Device] || identities[s.MajorMinor] {
			return fmt.Errorf("source %d duplicates device or major:minor identity", i)
		}
		devices[s.Device], identities[s.MajorMinor] = true, true
	}
	return nil
}

func captureOne(r *SourceReport, sourceIndex int, hooks CaptureHooks, partBytes int64, buf []byte) (resultErr error) {
	r.Status = "copying"
	source := r.Source
	reader, err := hooks.OpenSource(source)
	if err != nil {
		return fmt.Errorf("open read-only source: %w", err)
	}
	closed := false
	defer func() {
		if !closed {
			resultErr = errors.Join(resultErr, reader.Close())
		}
	}()
	wholeHash := sha256.New()
	var copied int64
	for copied < source.Bytes {
		if err := hooks.Revalidate(); err != nil {
			return fmt.Errorf("before part: %w", err)
		}
		count := partBytes
		if remaining := source.Bytes - copied; remaining < count {
			count = remaining
		}
		index := len(r.Parts)
		part := PartReport{Index: index, Name: fmt.Sprintf("%s.part-%06d.img.partial", r.ID, index), Expected: count, Status: "incomplete"}
		r.Parts = append(r.Parts, part)
		p := &r.Parts[index]
		out, err := hooks.Destination.CreateExclusive(p.Name)
		if err != nil {
			p.Error = err.Error()
			return fmt.Errorf("create part %d exclusively: %w", index, err)
		}
		partHash := sha256.New()
		progress := &progressReader{reader: io.LimitReader(reader, count), notify: hooks.Progress,
			state: Progress{Stage: "copy", SourceID: r.ID, Name: source.Name, SourceIndex: sourceIndex, PartIndex: index, BytesDone: copied, BytesTotal: source.Bytes}}
		p.Copied, err = io.CopyBuffer(io.MultiWriter(out, partHash, wholeHash), progress, buf)
		if err == nil && p.Copied != count {
			err = fmt.Errorf("short source read: got %d of %d bytes in part", p.Copied, count)
		}
		if err == nil {
			err = out.Sync()
		}
		err = errors.Join(err, out.Close())
		if err != nil {
			p.Error = err.Error()
			return fmt.Errorf("copy/sync part %d: %w", index, err)
		}
		p.SHA256, p.Status = hex.EncodeToString(partHash.Sum(nil)), "copied_synced"
		copied += p.Copied
	}
	if err := requireEOF(reader); err != nil {
		return fmt.Errorf("source exceeds planned size or trailing read failed: %w", err)
	}
	err = reader.Close()
	closed = true
	if err != nil {
		return fmt.Errorf("close copied source: %w", err)
	}
	r.SHA256 = hex.EncodeToString(wholeHash.Sum(nil))
	if err := hooks.Revalidate(); err != nil {
		return fmt.Errorf("before destination verification: %w", err)
	}
	var checked int64
	for i := range r.Parts {
		p := &r.Parts[i]
		reader, err := hooks.Destination.OpenRead(p.Name)
		if err != nil {
			p.Error = err.Error()
			return fmt.Errorf("open part %d for reread: %w", i, err)
		}
		progress := &progressReader{reader: reader, notify: hooks.Progress,
			state: Progress{Stage: "verify_destination", SourceID: r.ID, Name: source.Name, SourceIndex: sourceIndex, PartIndex: i, BytesDone: checked, BytesTotal: source.Bytes}}
		digest, err := hashExact(progress, p.Expected, buf)
		err = errors.Join(err, reader.Close())
		if err == nil && digest != p.SHA256 {
			err = errors.New("destination SHA256 mismatch")
		}
		if err != nil {
			p.Error = err.Error()
			return fmt.Errorf("verify part %d: %w", i, err)
		}
		p.Status = "destination_verified"
		checked += p.Expected
	}
	if err := hooks.Revalidate(); err != nil {
		return fmt.Errorf("before source reread: %w", err)
	}
	reader, err = hooks.OpenSource(source)
	if err != nil {
		return fmt.Errorf("reopen source: %w", err)
	}
	progress := &progressReader{reader: reader, notify: hooks.Progress,
		state: Progress{Stage: "verify_source", SourceID: r.ID, Name: source.Name, SourceIndex: sourceIndex, PartIndex: -1, BytesTotal: source.Bytes}}
	r.RereadSHA256, err = hashExact(progress, source.Bytes, buf)
	err = errors.Join(err, reader.Close())
	if err != nil {
		return fmt.Errorf("source reread: %w", err)
	}
	if r.RereadSHA256 != r.SHA256 {
		return errors.New("source changed between copy and reread (SHA256 mismatch)")
	}
	if err := hooks.Revalidate(); err != nil {
		return fmt.Errorf("after source reread: %w", err)
	}
	if err := hooks.Destination.Sync(); err != nil {
		return fmt.Errorf("persist part directory: %w", err)
	}
	for i := range r.Parts {
		r.Parts[i].Status = "verified"
	}
	r.Status = "verified"
	if hooks.Progress != nil {
		hooks.Progress(Progress{Stage: "verified", SourceID: r.ID, Name: source.Name, SourceIndex: sourceIndex, PartIndex: -1, BytesDone: source.Bytes, BytesTotal: source.Bytes})
	}
	return nil
}

func hashExact(reader io.Reader, count int64, buf []byte) (string, error) {
	h := sha256.New()
	n, err := io.CopyBuffer(h, io.LimitReader(reader, count), buf)
	if err != nil {
		return "", err
	}
	if n != count {
		return "", fmt.Errorf("short reread: got %d, expected %d", n, count)
	}
	if err := requireEOF(reader); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func requireEOF(reader io.Reader) error {
	var one [1]byte
	n, err := io.ReadFull(reader, one[:])
	if n != 0 {
		return errors.New("unexpected trailing data")
	}
	if err != io.EOF {
		return fmt.Errorf("expected EOF: %w", err)
	}
	return nil
}

type progressReader struct {
	reader io.Reader
	notify func(Progress)
	state  Progress
}

func (r *progressReader) Read(b []byte) (int, error) {
	n, err := r.reader.Read(b)
	r.state.BytesDone += int64(n)
	if n > 0 && r.notify != nil {
		r.notify(r.state)
	}
	return n, err
}

func failReport(r Report, cause error, index int, hooks CaptureHooks, mayWrite bool) (Report, error) {
	r.Status, r.Error = "failed", cause.Error()
	for i := range r.Sources {
		if i == index && r.Sources[i].Status != "verified" {
			r.Sources[i].Status, r.Sources[i].Error = "failed", cause.Error()
		} else if r.Sources[i].Status == "not_attempted" {
			r.Sources[i].Status, r.Sources[i].Error = "omitted", "capture stopped before this source"
			r.Omitted = append(r.Omitted, Omission{Name: r.Sources[i].Source.Name, Device: r.Sources[i].Source.Device, Reason: "capture stopped before this source"})
		}
	}
	if mayWrite {
		// Revalidate even on failure: a detached/replaced destination must never
		// receive a "best effort" receipt at the stale path.
		if err := hooks.Revalidate(); err != nil {
			cause = errors.Join(cause, fmt.Errorf("cannot safely persist failure: %w", err))
		} else if err := writeReport(hooks.Destination, "failed-report.json", r); err != nil {
			cause = errors.Join(cause, fmt.Errorf("persist failure report: %w", err))
		}
	}
	r.Error = cause.Error()
	return r, cause
}

func writeReport(destination Destination, name string, report Report) error {
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	file, err := destination.CreateExclusive(name)
	if err != nil {
		return err
	}
	n, err := file.Write(data)
	if err == nil && n != len(data) {
		err = io.ErrShortWrite
	}
	if err == nil {
		err = file.Sync()
	}
	err = errors.Join(err, file.Close())
	if err != nil {
		return err
	}
	fileRead, err := destination.OpenRead(name)
	if err != nil {
		return err
	}
	// The receipt is small, but the limit also rejects a corrupt growing file.
	reread, err := io.ReadAll(io.LimitReader(fileRead, int64(len(data))+1))
	err = errors.Join(err, fileRead.Close())
	if err != nil {
		return err
	}
	if !bytes.Equal(reread, data) {
		return errors.New("report reread mismatch")
	}
	return destination.Sync()
}
