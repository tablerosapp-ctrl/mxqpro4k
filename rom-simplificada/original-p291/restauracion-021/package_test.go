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
	m := Manifest{Format: 2, ID: allowedPackageID, DT: "gxlx2_p291_1g", Media: mediaID, Operation: allowedOperation, DataPolicy: "fresh_userdata_required"}
	if allowedOperation == "restore_original" {
		m.DataPolicy = "preserve_existing_userdata"
	}
	for _, name := range names {
		g := expectedGeometry[name]
		m.Images = append(m.Images, Image{Name: name, Entry: "tvbase/" + name + ".img", Size: g.Size, MajorMinor: g.MajorMinor, SHA256: originalImageHashes[name], OriginalSHA256: originalImageHashes[name]})
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
		{"old format", func(m *Manifest) { m.Format = 1 }},
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
		{"foreign original", func(m *Manifest) {
			m.Images[0].SHA256 = hex.EncodeToString(make([]byte, 32))
			m.Images[0].OriginalSHA256 = m.Images[0].SHA256
		}},
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
	oldHashes := originalImageHashes
	originalImageHashes = map[string]string{}
	for k, v := range oldHashes {
		originalImageHashes[k] = v
	}
	t.Cleanup(func() { originalImageHashes = oldHashes })
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
		m.Images[i].OriginalSHA256 = sum
		originalImageHashes[m.Images[i].Name] = sum
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
