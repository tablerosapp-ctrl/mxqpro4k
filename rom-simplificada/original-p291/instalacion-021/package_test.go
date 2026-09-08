package main

import (
	"archive/zip"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"testing"
)

func reviewedFixtureManifest() Manifest {
	m := Manifest{Format: 3, ID: allowedPackageID, DT: "gxlx2_p291_1g", Media: mediaID, Operation: allowedOperation, DataPolicy: "backup_raw_userdata_then_format_ext4", PlatformVersion: "0.2.0", DataBytes: userdataBytes, DataMajorMinor: "179:20", FilesystemBytes: userdataFilesystemBytes}
	for _, name := range names {
		g := expectedGeometry[name]
		m.Images = append(m.Images, Image{Name: name, Entry: "tvbase/" + name + ".img", Size: g.Size, MajorMinor: g.MajorMinor, SHA256: platformImageHashes[name], OriginalSHA256: originalImageHashes[name]})
	}
	return m
}
func TestActualOriginalGeometry(t *testing.T) {
	if expectedGeometry["system"].Size != 1342177280 || expectedGeometry["vendor"].Size != 943718400 || expectedGeometry["boot"].Size != 16777216 {
		t.Fatal("original geometry changed")
	}
	if expectedGeometry["vendor"].MajorMinor != "179:16" {
		t.Fatal("original vendor identity changed")
	}
}
func TestManifestGuards(t *testing.T) {
	if e := validateManifest(reviewedFixtureManifest()); e != nil {
		t.Fatal(e)
	}
	cases := []struct {
		name   string
		change func(*Manifest)
	}{
		{"old format", func(m *Manifest) { m.Format = 2 }},
		{"wrong data size", func(m *Manifest) { m.DataBytes-- }},
		{"wrong footer reservation", func(m *Manifest) { m.FilesystemBytes += 16384 }},
		{"wrong platform version", func(m *Manifest) { m.PlatformVersion = "0.1.2" }},
		{"old package", func(m *Manifest) { m.ID = "TVBASE-P291-A9-0.1.2" }},
		{"wrong board", func(m *Manifest) { m.DT = "gxlx_p271_1g" }},
		{"wrong media", func(m *Manifest) { m.Media = "another" }},
		{"wrong operation", func(m *Manifest) { m.Operation = "unreviewed" }},
		{"no migration policy", func(m *Manifest) { m.DataPolicy = "" }},
		{"automatic wipe", func(m *Manifest) { m.DataPolicy = "wipe_automatically" }},
		{"missing image", func(m *Manifest) { m.Images = m.Images[:4] }},
		{"candidate vendor size", func(m *Manifest) { m.Images[1].Size = 335544320 }},
		{"too large partition", func(m *Manifest) { m.Images[1].Size++ }},
		{"wrong major minor", func(m *Manifest) { m.Images[1].MajorMinor = "179:19" }},
		{"bootloader target", func(m *Manifest) { m.Images[0].Name = "bootloader" }},
		{"path traversal", func(m *Manifest) { m.Images[0].Entry = "../../system.img" }},
		{"malformed hash", func(m *Manifest) { m.Images[0].SHA256 = "" }},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			m := reviewedFixtureManifest()
			c.change(&m)
			if validateManifest(m) == nil {
				t.Fatal("unsafe manifest accepted")
			}
		})
	}
}
func fixturePackage(t *testing.T, extraJSON bool, corrupt bool) string {
	t.Helper()
	old := expectedGeometry
	oldHashes, oldOriginals := platformImageHashes, originalImageHashes
	platformImageHashes = map[string]string{}
	originalImageHashes = map[string]string{}
	t.Cleanup(func() { platformImageHashes = oldHashes; originalImageHashes = oldOriginals })
	reduced := map[string]Geometry{}
	for n, g := range old {
		reduced[n] = Geometry{4096, g.MajorMinor}
	}
	expectedGeometry = reduced
	t.Cleanup(func() { expectedGeometry = old }) // PC fixture only, never linked into the ARM build.
	m := reviewedFixtureManifest()
	content := bytes.Repeat([]byte{0, 10, 13, 255}, 1024)
	h := sha256.Sum256(content)
	sum := hex.EncodeToString(h[:])
	path := filepath.Join(t.TempDir(), "fixture.zip")
	f, e := os.Create(path)
	if e != nil {
		t.Fatal(e)
	}
	z := zip.NewWriter(f)
	for i := range m.Images {
		m.Images[i].SHA256 = sum
		platformImageHashes[m.Images[i].Name] = sum
		originalImageHashes[m.Images[i].Name] = sum
		m.Images[i].OriginalSHA256 = sum
		w, _ := z.Create(m.Images[i].Entry)
		if corrupt && i == 0 {
			w.Write(bytes.Repeat([]byte{1}, len(content)))
		} else {
			w.Write(content)
		}
	}
	w, _ := z.Create("tvbase/manifest.json")
	json.NewEncoder(w).Encode(m)
	if extraJSON {
		io.WriteString(w, "{}")
	}
	z.Close()
	f.Close()
	return path
}
func TestPayloadAndCRC(t *testing.T) {
	p, e := loadPackage(fixturePackage(t, false, false))
	if e != nil {
		t.Fatal(e)
	}
	defer p.ZIP.Close()
	if e = p.verify(); e != nil {
		t.Fatal(e)
	}
}
func TestChangedPayloadRejected(t *testing.T) {
	p, e := loadPackage(fixturePackage(t, false, true))
	if e != nil {
		t.Fatal(e)
	}
	defer p.ZIP.Close()
	if p.verify() == nil {
		t.Fatal("changed payload accepted")
	}
}
func TestTrailingManifestRejected(t *testing.T) {
	if p, e := loadPackage(fixturePackage(t, true, false)); e == nil {
		p.ZIP.Close()
		t.Fatal("trailing JSON accepted")
	}
}
func TestFreshDataRealState(t *testing.T) {
	t.Run("empty", func(t *testing.T) {
		if e := requireEmptyDataDirectory(t.TempDir()); e != nil {
			t.Fatal(e)
		}
	})
	t.Run("empty lostfound", func(t *testing.T) {
		d := t.TempDir()
		os.Mkdir(filepath.Join(d, "lost+found"), 0700)
		if e := requireEmptyDataDirectory(d); e != nil {
			t.Fatal(e)
		}
	})
	for _, name := range []string{"app", "system", "media", "TVBASE-MIGRATED.txt"} {
		t.Run(name, func(t *testing.T) {
			d := t.TempDir()
			os.WriteFile(filepath.Join(d, name), []byte("marker cannot prove migration"), 0600)
			if requireEmptyDataDirectory(d) == nil {
				t.Fatal("nonempty userdata accepted")
			}
		})
	}
	t.Run("lostfound has data", func(t *testing.T) {
		d := t.TempDir()
		os.Mkdir(filepath.Join(d, "lost+found"), 0700)
		os.WriteFile(filepath.Join(d, "lost+found", "orphan"), []byte{1}, 0600)
		if requireEmptyDataDirectory(d) == nil {
			t.Fatal("orphan data accepted")
		}
	})
}
func TestFreshDataMount(t *testing.T) {
	good := "31 20 179:20 / /data ro,seclabel - ext4 /dev/block/data ro"
	if e := requireDataReadOnlyMount(good, "179:20"); e != nil {
		t.Fatal(e)
	}
	for _, bad := range []string{"", "31 20 8:1 / /data ro - ext4 /dev/block/other ro", "31 20 179:20 / /data rw - ext4 /dev/block/data rw", good + "\n32 20 179:20 / /elsewhere rw - ext4 /dev/block/mmcblk0p20 rw"} {
		if requireDataReadOnlyMount(bad, "179:20") == nil {
			t.Fatal("unsafe userdata mount accepted")
		}
	}
}

type shortWriter struct{}

func (shortWriter) Write(b []byte) (int, error) { return len(b) - 1, nil }
func TestExactCopy(t *testing.T) {
	if _, e := copyExact(io.Discard, bytes.NewReader([]byte{1}), 2, nil); e == nil {
		t.Fatal("short source accepted")
	}
	if _, e := copyExact(shortWriter{}, bytes.NewReader([]byte{1, 2}), 2, nil); e == nil {
		t.Fatal("short destination accepted")
	}
}
