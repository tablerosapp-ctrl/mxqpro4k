package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// These fixtures exercise the engine using ordinary host files. They do not
// validate Linux block-device identity, Android recovery or physical USB sync.
type testDestination struct {
	dir            string
	created        []string
	beforeRead     func(string) error
	createFailure  func(string) error
	fileSyncError  error
	fileCloseError error
	dirSyncError   error
	dirSyncFailAt  int
	shortWrite     bool
	syncCount      int
}

var testSafeName = regexp.MustCompile(`^(?:[a-f0-9]{64}\.part-[0-9]{6}\.img\.partial|report\.json|failed-report\.json)$`)

func (d *testDestination) CreateExclusive(name string) (SyncWriteCloser, error) {
	if !testSafeName.MatchString(name) {
		return nil, fmt.Errorf("unsafe generated name %q", name)
	}
	if d.createFailure != nil {
		if err := d.createFailure(name); err != nil {
			return nil, err
		}
	}
	f, err := os.OpenFile(filepath.Join(d.dir, name), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return nil, err
	}
	d.created = append(d.created, name)
	return &testOutput{file: f, destination: d}, nil
}

func (d *testDestination) OpenRead(name string) (io.ReadCloser, error) {
	if !testSafeName.MatchString(name) {
		return nil, errors.New("unsafe name")
	}
	if d.beforeRead != nil {
		if err := d.beforeRead(name); err != nil {
			return nil, err
		}
	}
	path := filepath.Join(d.dir, name)
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() {
		return nil, errors.New("non-regular destination")
	}
	return os.Open(path)
}

func (d *testDestination) Sync() error {
	d.syncCount++
	// Host tests deliberately simulate directory sync; platform tests own the
	// actual filesystem syscall and policy for unsupported filesystems.
	if d.dirSyncFailAt == 0 || d.dirSyncFailAt == d.syncCount {
		return d.dirSyncError
	}
	return nil
}

type testOutput struct {
	file        *os.File
	destination *testDestination
}

func (o *testOutput) Write(p []byte) (int, error) {
	if o.destination.shortWrite && len(p) > 1 {
		return o.file.Write(p[:len(p)-1])
	}
	return o.file.Write(p)
}

func (o *testOutput) Sync() error {
	if o.destination.fileSyncError != nil {
		return o.destination.fileSyncError
	}
	return o.file.Sync()
}

func (o *testOutput) Close() error {
	return errors.Join(o.file.Close(), o.destination.fileCloseError)
}

func fixtureSource(name string, count int) Source {
	return Source{Name: name, Device: "fixture:" + name, Bytes: int64(count), MajorMinor: "fixture:" + name, Kind: "host-test-file"}
}

func fixtureHooks(t *testing.T, inputs map[string][]byte) (CaptureHooks, *testDestination, *int) {
	t.Helper()
	d := &testDestination{dir: t.TempDir()}
	opens := new(int)
	h := CaptureHooks{
		OpenSource: func(s Source) (io.ReadCloser, error) {
			*opens++
			data, ok := inputs[s.Name]
			if !ok {
				return nil, errors.New("unknown fixture source")
			}
			return io.NopCloser(bytes.NewReader(data)), nil
		},
		Revalidate:  func() error { return nil },
		FreeBytes:   func() (uint64, error) { return 1 << 50, nil },
		Destination: d,
	}
	return h, d, opens
}

func digestString(data []byte) string {
	digest := sha256.Sum256(data)
	return hex.EncodeToString(digest[:])
}

func readFixtureReport(t *testing.T, d *testDestination, name string) Report {
	t.Helper()
	data, err := os.ReadFile(filepath.Join(d.dir, name))
	if err != nil {
		t.Fatal(err)
	}
	var report Report
	if err := json.Unmarshal(data, &report); err != nil {
		t.Fatal(err)
	}
	return report
}

func TestCaptureSplitsRereadsAndReports(t *testing.T) {
	data := []byte("0123456789abcdefghijkl")
	source := fixtureSource("system", len(data))
	source.Aliases = []string{"/dev/block/by-name/system"}
	hooks, dest, opens := fixtureHooks(t, map[string][]byte{"system": data})
	stages := map[string]int{}
	hooks.Progress = func(p Progress) {
		stages[p.Stage]++
		if p.SourceID == "" || p.Name != "system" || p.BytesDone < 0 || p.BytesDone > int64(len(data)) {
			t.Fatalf("invalid progress %+v", p)
		}
	}
	plan := CapturePlan{Sources: []Source{source}, Omitted: []Omission{{Name: "userdata", Reason: "mounted read-write"}}}
	r, err := captureWithPartBytes(plan, hooks, 7)
	if err != nil {
		t.Fatal(err)
	}
	if *opens != 2 || r.Status != "data_verified" || r.RequiredBytes != uint64(len(data))+SpaceReserve || len(r.Omitted) != 1 {
		t.Fatalf("unexpected report: opens=%d %+v", *opens, r)
	}
	s := r.Sources[0]
	if s.Status != "verified" || s.SHA256 != digestString(data) || s.RereadSHA256 != s.SHA256 || len(s.Parts) != 4 {
		t.Fatalf("unexpected source: %+v", s)
	}
	var restored []byte
	for i, p := range s.Parts {
		if p.Status != "verified" || p.Copied != p.Expected || p.Copied > 7 || p.Index != i || !strings.HasSuffix(p.Name, ".partial") {
			t.Fatalf("unexpected part: %+v", p)
		}
		b, err := os.ReadFile(filepath.Join(dest.dir, p.Name))
		if err != nil || digestString(b) != p.SHA256 {
			t.Fatalf("part %d read: %v", i, err)
		}
		restored = append(restored, b...)
	}
	if !bytes.Equal(restored, data) {
		t.Fatal("concatenated parts differ")
	}
	for _, stage := range []string{"copy", "verify_destination", "verify_source", "verified"} {
		if stages[stage] == 0 {
			t.Fatalf("missing progress stage %s", stage)
		}
	}
	saved := readFixtureReport(t, dest, "report.json")
	if saved.Status != r.Status || saved.Sources[0].SHA256 != s.SHA256 || dest.syncCount != 2 {
		t.Fatalf("unverified report persistence: %+v", saved)
	}
}

func TestCaptureSizeBoundaries(t *testing.T) {
	for _, count := range []int{1, 6, 7, 8, 14, 15} {
		t.Run(fmt.Sprint(count), func(t *testing.T) {
			data := bytes.Repeat([]byte{'X'}, count)
			h, _, _ := fixtureHooks(t, map[string][]byte{"boot": data})
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", count)}}, h, 7)
			if err != nil || len(r.Sources[0].Parts) != (count+6)/7 {
				t.Fatalf("boundary %d: %+v %v", count, r, err)
			}
		})
	}
}

func TestCaptureRejectsShortAndLongSource(t *testing.T) {
	for _, tc := range []struct {
		name    string
		data    string
		planned int
		message string
	}{
		{"short-first", "abc", 4, "short source read"},
		{"short-next-part", "abcdefgh", 12, "short source read"},
		{"long", "abcde", 4, "trailing data"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			h, d, opens := fixtureHooks(t, map[string][]byte{"boot": []byte(tc.data)})
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", tc.planned)}}, h, 7)
			if err == nil || !strings.Contains(err.Error(), tc.message) || r.Status != "failed" || *opens != 1 {
				t.Fatalf("expected size failure, got %+v %v", r, err)
			}
			if r.Sources[0].Status != "failed" || len(r.Sources[0].Parts) == 0 {
				t.Fatalf("failure not tracked: %+v", r)
			}
			if _, err := os.Stat(filepath.Join(d.dir, r.Sources[0].Parts[0].Name)); err != nil {
				t.Fatalf("partial lost: %v", err)
			}
			if readFixtureReport(t, d, "failed-report.json").Status != "failed" {
				t.Fatal("missing failure report")
			}
		})
	}
}

func TestCaptureRejectsChangingSource(t *testing.T) {
	h, d, _ := fixtureHooks(t, nil)
	reads := 0
	h.OpenSource = func(Source) (io.ReadCloser, error) {
		reads++
		if reads == 1 {
			return io.NopCloser(strings.NewReader("original")), nil
		}
		return io.NopCloser(strings.NewReader("mutated!")), nil
	}
	r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 8)}}, h, 7)
	if err == nil || !strings.Contains(err.Error(), "source changed") || r.Sources[0].SHA256 == r.Sources[0].RereadSHA256 {
		t.Fatalf("source change not rejected: %+v %v", r, err)
	}
	if r.Sources[0].Parts[0].Status != "destination_verified" || readFixtureReport(t, d, "failed-report.json").Status != "failed" {
		t.Fatal("source instability falsely promoted parts to verified")
	}
}

func TestCaptureRejectsRereadSizeChange(t *testing.T) {
	for _, second := range []string{"abc", "abcde"} {
		t.Run(second, func(t *testing.T) {
			h, _, _ := fixtureHooks(t, nil)
			reads := 0
			h.OpenSource = func(Source) (io.ReadCloser, error) {
				reads++
				data := "abcd"
				if reads == 2 {
					data = second
				}
				return io.NopCloser(strings.NewReader(data)), nil
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if err == nil || !strings.Contains(err.Error(), "source reread") || r.Status != "failed" {
				t.Fatalf("reread size mismatch accepted: %+v %v", r, err)
			}
		})
	}
}

func TestCaptureRejectsDestinationCorruption(t *testing.T) {
	for _, corruption := range []string{"changed", "short", "long"} {
		t.Run(corruption, func(t *testing.T) {
			h, d, opens := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
			d.beforeRead = func(name string) error {
				if !strings.HasSuffix(name, ".partial") {
					return nil
				}
				data := map[string]string{"changed": "abXd", "short": "abc", "long": "abcde"}[corruption]
				return os.WriteFile(filepath.Join(d.dir, name), []byte(data), 0600)
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if err == nil || !strings.Contains(err.Error(), "verify part") || r.Status != "failed" || *opens != 1 {
				t.Fatalf("corruption accepted: %+v %v", r, err)
			}
		})
	}
}

func TestCaptureNeverOverwritesExistingFiles(t *testing.T) {
	h, d, _ := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
	plan := CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}
	first, err := captureWithPartBytes(plan, h, 7)
	if err != nil {
		t.Fatal(err)
	}
	part := first.Sources[0].Parts[0].Name
	before, _ := os.ReadFile(filepath.Join(d.dir, part))
	reportBefore, _ := os.ReadFile(filepath.Join(d.dir, "report.json"))
	r, err := captureWithPartBytes(plan, h, 7)
	if err == nil || !strings.Contains(err.Error(), "exclusively") || r.Status != "failed" {
		t.Fatalf("second capture accepted: %+v %v", r, err)
	}
	after, _ := os.ReadFile(filepath.Join(d.dir, part))
	reportAfter, _ := os.ReadFile(filepath.Join(d.dir, "report.json"))
	if !bytes.Equal(before, after) || !bytes.Equal(reportBefore, reportAfter) {
		t.Fatal("capture overwrote existing bytes")
	}
	failureBefore, _ := os.ReadFile(filepath.Join(d.dir, "failed-report.json"))
	if _, err := captureWithPartBytes(plan, h, 7); err == nil {
		t.Fatal("third capture accepted")
	}
	failureAfter, _ := os.ReadFile(filepath.Join(d.dir, "failed-report.json"))
	if !bytes.Equal(failureBefore, failureAfter) {
		t.Fatal("failure report overwritten")
	}
}

func TestCaptureReportsSuccessfulFailedAndOmittedSources(t *testing.T) {
	h, d, opens := fixtureHooks(t, map[string][]byte{"boot": []byte("good"), "system": []byte("bad"), "vendor": []byte("next")})
	plan := CapturePlan{Sources: []Source{fixtureSource("boot", 4), fixtureSource("system", 4), fixtureSource("vendor", 4)},
		Omitted: []Omission{{Name: "userdata", Reason: "mounted read-write"}}}
	r, err := captureWithPartBytes(plan, h, 7)
	if err == nil || *opens != 3 || r.Sources[0].Status != "verified" || r.Sources[1].Status != "failed" || r.Sources[2].Status != "omitted" || len(r.Omitted) != 2 {
		t.Fatalf("unexpected partial outcome: %+v %v", r, err)
	}
	saved := readFixtureReport(t, d, "failed-report.json")
	if saved.Sources[0].SHA256 != digestString([]byte("good")) || saved.Sources[2].Status != "omitted" {
		t.Fatal("failure receipt lost completed or omitted source")
	}
}

func TestCaptureFailsOnSyncCloseAndShortWrite(t *testing.T) {
	for _, kind := range []string{"file-sync", "directory-sync", "close", "short-write"} {
		t.Run(kind, func(t *testing.T) {
			h, d, _ := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
			sentinel := errors.New("injected EIO")
			switch kind {
			case "file-sync":
				d.fileSyncError = sentinel
			case "directory-sync":
				d.dirSyncError = sentinel
			case "close":
				d.fileCloseError = sentinel
			case "short-write":
				d.shortWrite = true
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if err == nil || r.Status != "failed" || len(r.Sources[0].Parts) != 1 {
				t.Fatalf("IO failure accepted: %+v %v", r, err)
			}
			if _, err := os.Stat(filepath.Join(d.dir, r.Sources[0].Parts[0].Name)); err != nil {
				t.Fatalf("partial not preserved: %v", err)
			}
			if _, err := os.Stat(filepath.Join(d.dir, "report.json")); !os.IsNotExist(err) {
				t.Fatal("success report written after part failure")
			}
		})
	}
}

func TestCapturePreflightSpaceAndHooks(t *testing.T) {
	for _, mode := range []string{"exact", "one-less", "space-error", "revalidate-error", "missing-hook"} {
		t.Run(mode, func(t *testing.T) {
			h, d, opens := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
			h.FreeBytes = func() (uint64, error) { return SpaceReserve + 4, nil }
			switch mode {
			case "one-less":
				h.FreeBytes = func() (uint64, error) { return SpaceReserve + 3, nil }
			case "space-error":
				h.FreeBytes = func() (uint64, error) { return 0, errors.New("statfs denied") }
			case "revalidate-error":
				h.Revalidate = func() error { return errors.New("mount changed") }
			case "missing-hook":
				h.OpenSource = nil
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if mode == "exact" {
				if err != nil {
					t.Fatal(err)
				}
				return
			}
			if err == nil || r.Status != "failed" || *opens != 0 {
				t.Fatalf("preflight failure accepted: %+v %v", r, err)
			}
			for _, name := range d.created {
				if strings.HasSuffix(name, ".partial") {
					t.Fatal("payload created before preflight passed")
				}
			}
			if (mode == "revalidate-error" || mode == "missing-hook") && len(d.created) != 0 {
				t.Fatal("write attempted without valid mandatory hooks")
			}
		})
	}
}

func TestCaptureRevalidatesDuringAndAfterCopy(t *testing.T) {
	for _, failAt := range []int{2, 3, 4, 5, 6, 7} {
		t.Run(fmt.Sprint(failAt), func(t *testing.T) {
			h, d, _ := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
			calls := 0
			h.Revalidate = func() error {
				calls++
				if calls >= failAt {
					return errors.New("identity changed")
				}
				return nil
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if err == nil || !strings.Contains(err.Error(), "identity changed") || r.Status != "failed" {
				t.Fatalf("revalidation failure accepted: %+v %v", r, err)
			}
			for _, name := range d.created {
				if strings.HasSuffix(name, ".json") {
					t.Fatal("wrote receipt to unvalidated changed destination")
				}
			}
		})
	}
}

func TestCaptureSafeNamesForUntrustedMetadata(t *testing.T) {
	for _, name := range []string{"../../outside", `C:\\unsafe\\target`, "a/b", ".", "área", "system\nboot"} {
		t.Run(name, func(t *testing.T) {
			h, d, _ := fixtureHooks(t, map[string][]byte{name: []byte("abcd")})
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource(name, 4)}}, h, 7)
			if err != nil {
				t.Fatal(err)
			}
			for _, created := range d.created {
				if !testSafeName.MatchString(created) {
					t.Fatalf("metadata leaked into filename %q", created)
				}
			}
			if r.Sources[0].Source.Name != name {
				t.Fatal("metadata was silently changed")
			}
		})
	}
}

func TestCaptureInvalidPlansWriteNothing(t *testing.T) {
	valid := fixtureSource("boot", 4)
	invalid := map[string]CapturePlan{
		"empty":     {},
		"zero":      {Sources: []Source{fixtureSource("boot", 0)}},
		"negative":  {Sources: []Source{fixtureSource("boot", -1)}},
		"duplicate": {Sources: []Source{valid, valid}},
	}
	large := valid
	large.Bytes = MaxSourceBytes + 1
	invalid["too-large"] = CapturePlan{Sources: []Source{large}}
	missing := valid
	missing.MajorMinor = ""
	invalid["missing-identity"] = CapturePlan{Sources: []Source{missing}}
	nul := valid
	nul.Name = "a\x00b"
	invalid["nul"] = CapturePlan{Sources: []Source{nul}}
	tooMany := make([]Source, MaxSources+1)
	for i := range tooMany {
		tooMany[i] = fixtureSource(fmt.Sprint(i), 4)
	}
	invalid["too-many"] = CapturePlan{Sources: tooMany}
	for name, plan := range invalid {
		t.Run(name, func(t *testing.T) {
			h, d, opens := fixtureHooks(t, nil)
			if _, err := captureWithPartBytes(plan, h, 7); err == nil || *opens != 0 || len(d.created) != 0 {
				t.Fatalf("invalid plan touched storage: %v", err)
			}
		})
	}
}

func TestCaptureReportPersistenceFailure(t *testing.T) {
	for _, mode := range []string{"existing", "corrupt", "open-denied"} {
		t.Run(mode, func(t *testing.T) {
			h, d, _ := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
			if mode == "existing" {
				if err := os.WriteFile(filepath.Join(d.dir, "report.json"), []byte("prior report"), 0600); err != nil {
					t.Fatal(err)
				}
			}
			d.beforeRead = func(name string) error {
				if name != "report.json" {
					return nil
				}
				if mode == "corrupt" {
					return os.WriteFile(filepath.Join(d.dir, name), []byte("corrupted"), 0600)
				}
				if mode == "open-denied" {
					return errors.New("reread denied")
				}
				return nil
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if err == nil || !strings.Contains(err.Error(), "persist report") || r.Status != "failed" || r.Sources[0].Status != "verified" {
				t.Fatalf("receipt failure accepted: %+v %v", r, err)
			}
			if readFixtureReport(t, d, "failed-report.json").Status != "failed" {
				t.Fatal("missing superseding failure report")
			}
			if mode == "existing" {
				data, _ := os.ReadFile(filepath.Join(d.dir, "report.json"))
				if string(data) != "prior report" {
					t.Fatal("existing report overwritten")
				}
			}
		})
	}
}

func TestCaptureFinalDirectorySyncFailureSupersedesVerifiedDataReport(t *testing.T) {
	h, d, _ := fixtureHooks(t, map[string][]byte{"boot": []byte("abcd")})
	d.dirSyncFailAt, d.dirSyncError = 2, errors.New("final directory EIO")
	r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
	if err == nil || !strings.Contains(err.Error(), "final directory EIO") || r.Status != "failed" {
		t.Fatalf("final sync error accepted: %+v %v", r, err)
	}
	// The original receipt accurately describes verified payload bytes. A
	// separate failure receipt records that closing the transaction failed.
	if readFixtureReport(t, d, "report.json").Status != "data_verified" {
		t.Fatal("unexpected payload receipt")
	}
	failure := readFixtureReport(t, d, "failed-report.json")
	if failure.Status != "failed" || !strings.Contains(failure.Error, "final directory EIO") || d.syncCount != 3 {
		t.Fatalf("missing superseding error receipt: %+v", failure)
	}
}

type failingReader struct {
	reader   io.Reader
	readErr  error
	closeErr error
}

func (r *failingReader) Read(b []byte) (int, error) {
	n, err := r.reader.Read(b)
	if err == io.EOF && r.readErr != nil {
		return n, r.readErr
	}
	return n, err
}

func (r *failingReader) Close() error { return r.closeErr }

func TestCaptureSourceIOErrors(t *testing.T) {
	for _, mode := range []string{"open", "read", "close", "reopen"} {
		t.Run(mode, func(t *testing.T) {
			h, _, _ := fixtureHooks(t, nil)
			opens := 0
			h.OpenSource = func(Source) (io.ReadCloser, error) {
				opens++
				if mode == "open" || (mode == "reopen" && opens == 2) {
					return nil, errors.New("source denied")
				}
				r := &failingReader{reader: strings.NewReader("abcd")}
				if mode == "read" {
					r.readErr = errors.New("source EIO")
				}
				if mode == "close" {
					r.closeErr = errors.New("source close EIO")
				}
				return r, nil
			}
			r, err := captureWithPartBytes(CapturePlan{Sources: []Source{fixtureSource("boot", 4)}}, h, 7)
			if err == nil || r.Status != "failed" || r.Sources[0].Status != "failed" {
				t.Fatalf("source IO error accepted: %+v %v", r, err)
			}
		})
	}
}
