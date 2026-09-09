package main

import (
	"bytes"
	"errors"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func bufferedFixtureReport() SourceReport {
	return SourceReport{Source: fixtureSource("mmcblk0p10", 4), ID: strings.Repeat("a", 64), Status: "not_attempted"}
}

func TestBufferedReadsTwiceBeforeAnyDestinationWrite(t *testing.T) {
	h, d, _ := fixtureHooks(t, nil)
	h.AvailableMemory = func() (uint64, error) { return 1 << 30, nil }
	var sequence []string
	h.OpenSource = func(Source) (io.ReadCloser, error) {
		sequence = append(sequence, "source")
		return io.NopCloser(strings.NewReader("abcd")), nil
	}
	d.createFailure = func(string) error { sequence = append(sequence, "write"); return nil }
	d.beforeRead = func(string) error { sequence = append(sequence, "read_destination"); return nil }
	r := bufferedFixtureReport()
	if e := captureBufferedBackupSized(&r, 0, h, make([]byte, 2), 4); e != nil {
		t.Fatal(e)
	}
	if !reflect.DeepEqual(sequence, []string{"source", "source", "write", "read_destination"}) {
		t.Fatal(sequence)
	}
	if r.Status != "verified" || r.VerificationOrder != "source_source_destination" || r.SHA256 != digestString([]byte("abcd")) || r.SHA256 != r.RereadSHA256 || len(r.Parts) != 1 || r.Parts[0].Status != "verified" {
		t.Fatalf("%+v", r)
	}
}

type bufferedTestReader struct {
	io.Reader
	closeError error
}

func (r bufferedTestReader) Close() error { return r.closeError }

func TestBufferedRejectsSourceAndMemoryFailuresBeforeDataWrite(t *testing.T) {
	cases := []string{"memory_missing", "memory_error", "memory_low", "first_open", "first_short", "first_long", "first_close", "second_open", "second_short", "second_long", "second_close", "second_changed", "second_revalidation", "third_revalidation"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			h, d, _ := fixtureHooks(t, nil)
			h.AvailableMemory = func() (uint64, error) {
				if name == "memory_error" {
					return 0, errors.New("meminfo failure")
				}
				if name == "memory_low" {
					return bufferedBackupMemoryMargin + 3, nil
				}
				return 1 << 30, nil
			}
			if name == "memory_missing" {
				h.AvailableMemory = nil
			}
			opens, revalidations := 0, 0
			h.OpenSource = func(Source) (io.ReadCloser, error) {
				opens++
				prefix := "first"
				if opens == 2 {
					prefix = "second"
				}
				if name == prefix+"_open" {
					return nil, errors.New("open failure")
				}
				data := "abcd"
				if name == prefix+"_short" {
					data = "abc"
				}
				if name == prefix+"_long" {
					data = "abcde"
				}
				if name == "second_changed" && opens == 2 {
					data = "ABCD"
				}
				var ce error
				if name == prefix+"_close" {
					ce = errors.New("close failure")
				}
				return bufferedTestReader{strings.NewReader(data), ce}, nil
			}
			h.Revalidate = func() error {
				revalidations++
				if name == "second_revalidation" && revalidations == 2 || name == "third_revalidation" && revalidations == 3 {
					return errors.New("identity changed")
				}
				return nil
			}
			r := bufferedFixtureReport()
			if e := captureBufferedBackupSized(&r, 0, h, make([]byte, 2), 4); e == nil || r.Status == "verified" {
				t.Fatalf("%+v %v", r, e)
			}
			if len(d.created) != 0 || len(r.Parts) != 0 {
				t.Fatalf("wrote data before two valid source reads %+v", d.created)
			}
			if name == "second_changed" && (r.SHA256 == r.RereadSHA256 || r.RereadSHA256 != digestString([]byte("ABCD"))) {
				t.Fatal("second source hash not retained")
			}
		})
	}
}

func TestBufferedRetainsDestinationAndRevalidationFailures(t *testing.T) {
	cases := []string{"create", "short_write", "file_sync", "file_close", "destination_open", "destination_changed", "destination_short", "destination_long", "directory_sync", "before_verify", "after_verify"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			h, d, _ := fixtureHooks(t, map[string][]byte{"mmcblk0p10": []byte("abcd")})
			h.AvailableMemory = func() (uint64, error) { return 1 << 30, nil }
			if name == "create" {
				d.createFailure = func(string) error { return errors.New("create failure") }
			}
			if name == "short_write" {
				d.shortWrite = true
			}
			if name == "file_sync" {
				d.fileSyncError = errors.New("sync failure")
			}
			if name == "file_close" {
				d.fileCloseError = errors.New("close failure")
			}
			if name == "directory_sync" {
				d.dirSyncError = errors.New("dir sync failure")
			}
			d.beforeRead = func(file string) error {
				if name == "destination_open" {
					return errors.New("read failure")
				}
				mutated := map[string]string{"destination_changed": "ABCD", "destination_short": "abc", "destination_long": "abcde"}[name]
				if mutated != "" {
					return os.WriteFile(filepath.Join(d.dir, file), []byte(mutated), 0600)
				}
				return nil
			}
			checks := 0
			h.Revalidate = func() error {
				checks++
				if name == "before_verify" && checks == 4 || name == "after_verify" && checks == 5 {
					return errors.New("identity changed")
				}
				return nil
			}
			r := bufferedFixtureReport()
			if e := captureBufferedBackupSized(&r, 0, h, make([]byte, 2), 4); e == nil || r.Status == "verified" {
				t.Fatalf("%+v %v", r, e)
			}
			if len(r.Parts) != 1 || r.Parts[0].Status == "verified" {
				t.Fatalf("lost failure scope %+v", r)
			}
		})
	}
}

func TestMemoryEstimateForLinux310AndAvailable(t *testing.T) {
	base := "MemTotal: 1048576 kB\nMemFree: 200000 kB\nBuffers: 10000 kB\nCached: 30000 kB\nShmem: 5000 kB\nDirty: 3000 kB\nWriteback: 2000 kB\n"
	got, e := parseMemoryAvailable([]byte(base))
	if e != nil || got != 230000*1024 {
		t.Fatalf("%d %v", got, e)
	}
	got, e = parseMemoryAvailable([]byte(base + "MemAvailable: 250000 kB\n"))
	if e != nil || got != 250000*1024 {
		t.Fatalf("%d %v", got, e)
	}
	zero := strings.Replace(base, "Shmem: 5000", "Shmem: 300000", 1)
	got, e = parseMemoryAvailable([]byte(zero))
	if e != nil || got != 0 {
		t.Fatalf("underflow must saturate: %d %v", got, e)
	}
	cases := []string{
		"MemAvailable: 100 kB\n", strings.Replace(base, "MemTotal: 1048576", "MemTotal: 500000", 1),
		strings.Replace(base, "Writeback: 2000 kB\n", "", 1), base + "Cached: 30000 kB\n",
		strings.Replace(base, "MemFree: 200000 kB", "MemFree: -1 kB", 1), strings.Replace(base, "MemFree: 200000 kB", "MemFree: +1 kB", 1),
		strings.Replace(base, "MemFree: 200000 kB", "MemFree: 200000 MB", 1), strings.Replace(base, "MemFree: 200000 kB", "MemFree: 18446744073709551615 kB", 1),
		base + "MemAvailable: 1048577 kB\n", strings.Replace(base, "MemFree: 200000", "MemFree: 1030000", 1),
		strings.Replace(base, "Shmem: 5000", "Shmem: 1048577", 1), base + "MemAvailable: 100 kB\nMemAvailable: 100 kB\n",
	}
	for i, s := range cases {
		if _, e := parseMemoryAvailable([]byte(s)); e == nil {
			t.Fatalf("invalid memory fixture accepted %d", i)
		}
	}
}

func bufferedExactSource(t *testing.T) Source {
	f, _, _ := cFixture(t)
	p := cFact(t, f, "mmcblk0p10")
	return Source{Name: p.Name, Device: p.Path, Bytes: p.Bytes, MajorMinor: p.MajorMinor, Kind: p.Kind, Aliases: p.Aliases}
}
func TestBufferedPlanOnlyExactBackupLast(t *testing.T) {
	source := bufferedExactSource(t)
	available := func() (uint64, error) { return 1 << 30, nil }
	if e := validateBufferedBackupPlan(CapturePlan{Sources: []Source{source}}, PartBytes, available); e != nil {
		t.Fatal(e)
	}
	for _, name := range []string{"size", "kind", "device", "major", "alias", "not_last", "part_size", "missing_memory"} {
		t.Run(name, func(t *testing.T) {
			s := bufferedExactSource(t)
			p := CapturePlan{Sources: []Source{s}}
			part := PartBytes
			memory := available
			switch name {
			case "size":
				p.Sources[0].Bytes--
			case "kind":
				p.Sources[0].Kind = "emmc_user_area"
			case "device":
				p.Sources[0].Device = "other"
			case "major":
				p.Sources[0].MajorMinor = "179:11"
			case "alias":
				p.Sources[0].Aliases = nil
			case "not_last":
				p.Sources = append(p.Sources, fixtureSource("later", 4))
			case "part_size":
				part = 4
			case "missing_memory":
				memory = nil
			}
			if e := validateBufferedBackupPlan(p, part, memory); e == nil {
				t.Fatal("invalid buffered plan accepted")
			}
		})
	}
}

type repeatedByteReader struct {
	left  int64
	value byte
}

func (r *repeatedByteReader) Read(p []byte) (int, error) {
	if r.left == 0 {
		return 0, io.EOF
	}
	n := len(p)
	if int64(n) > r.left {
		n = int(r.left)
	}
	for i := 0; i < n; i++ {
		p[i] = r.value
	}
	r.left -= int64(n)
	return n, nil
}

func TestBufferedEnginePreservesEarlierVerifiedSourceOnLastMismatch(t *testing.T) {
	h, d, _ := fixtureHooks(t, nil)
	h.BufferedBackup = true
	h.AvailableMemory = func() (uint64, error) { return 1 << 30, nil }
	backupOpens := 0
	h.OpenSource = func(s Source) (io.ReadCloser, error) {
		if s.Name == "boot_fixture" {
			return io.NopCloser(bytes.NewReader([]byte("BOOT"))), nil
		}
		backupOpens++
		return io.NopCloser(&repeatedByteReader{left: bufferedBackupBytes, value: byte(backupOpens)}), nil
	}
	r, e := Capture(CapturePlan{Sources: []Source{fixtureSource("boot_fixture", 4), bufferedExactSource(t)}}, h)
	if e == nil || !strings.Contains(e.Error(), "consecutive reads") || len(r.Sources) != 2 || r.Sources[0].Status != "verified" || r.Sources[1].Status != "failed" || len(r.Sources[1].Parts) != 0 {
		t.Fatalf("%+v %v", r, e)
	}
	if backupOpens != 2 || r.Sources[1].SHA256 == r.Sources[1].RereadSHA256 || r.Sources[1].VerificationOrder != "source_source_destination" {
		t.Fatal("source comparison not genuine")
	}
	saved := readFixtureReport(t, d, "failed-report.json")
	if saved.Sources[0].Status != "verified" || saved.Sources[1].Status != "failed" {
		t.Fatal("partial success erased")
	}
	if len(d.created) != 2 {
		t.Fatalf("expected previous part and failure report only: %v", d.created)
	}
}
