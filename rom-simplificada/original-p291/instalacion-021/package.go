package main

import (
	"archive/zip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
)

const mediaID = "TVBASE-P291-20260906-4dc82786"
const originalBootSHA256 = "13e027a3aae1af232d1d700421486f32b7958a9fa0a157d8cbd3c47243ab697d"

var allowedPackageID = "TVBASE-P291-A9-0.2.1"
var allowedOperation = "install_reviewed_with_userdata_migration"
var names = []string{"system", "vendor", "product", "odm", "boot"}

type Geometry struct {
	Size       int64
	MajorMinor string
}

var expectedGeometry = map[string]Geometry{
	"system": {1342177280, "179:18"}, "vendor": {943718400, "179:16"},
	"product": {134217728, "179:19"}, "odm": {134217728, "179:17"},
	"boot": {16777216, "179:11"},
}

var platformImageHashes = map[string]string{
	"system":  "e602d62182400f2b785b9044dd28b767791bcafb411146f988b719c6e722dc7b",
	"vendor":  "57c1f319e1c1f7df6918b2ffd513b1b0a63611e498fa6000826ee34206ef9fee",
	"product": "c8550c937cb85257e58d8d70414b9162141d9e20cf199406d4ca3cfacf8ab00e",
	"odm":     "97836d5a1b016b64d3875c82cb5f3b4daee0f56d8eea3675b4231086429cbe67",
	"boot":    "c1a71479498bdfd8368fb1ade42ae293cb97f6087c43c3a8f8f31535725113fc",
}
var originalImageHashes = map[string]string{
	"system":  "249611912b7b1fa277d169f8612f9a719df3abf99dc98ed8e817657e2c9beb2c",
	"vendor":  "d542fc091469a7c1223c1d5091f8ec6b3456f38dd1218b779d18d1942190d2a7",
	"product": "ef2c71f6208e25fa1cc9d5c12cb04972ac20d772e2c11a76972859403b530075",
	"odm":     "97836d5a1b016b64d3875c82cb5f3b4daee0f56d8eea3675b4231086429cbe67",
	"boot":    originalBootSHA256,
}

type Image struct {
	Name           string `json:"name"`
	Entry          string `json:"entry"`
	Size           int64  `json:"size"`
	SHA256         string `json:"sha256"`
	MajorMinor     string `json:"major_minor"`
	OriginalSHA256 string `json:"original_sha256"`
}
type Manifest struct {
	Format          int     `json:"format"`
	ID              string  `json:"id"`
	DT              string  `json:"dt_id"`
	Media           string  `json:"media_id"`
	Operation       string  `json:"operation"`
	DataPolicy      string  `json:"data_policy"`
	PlatformVersion string  `json:"platform_version"`
	DataBytes       int64   `json:"data_bytes"`
	DataMajorMinor  string  `json:"data_major_minor"`
	FilesystemBytes int64   `json:"filesystem_bytes"`
	Images          []Image `json:"images"`
}
type Package struct {
	ZIP      *zip.ReadCloser
	Manifest Manifest
	Entries  map[string]*zip.File
}

func validSHA(s string) bool {
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 32 && hex.EncodeToString(b) == s
}
func validateManifest(m Manifest) error {
	if m.Format != 3 || m.ID != allowedPackageID || m.DT != "gxlx2_p291_1g" || m.Media != mediaID || m.Operation != allowedOperation || len(m.Images) != len(names) {
		return fmt.Errorf("perfil de paquete no permitido")
	}
	switch m.Operation {
	case "install_reviewed_with_userdata_migration":
		if m.DataPolicy != "backup_raw_userdata_then_format_ext4" || m.PlatformVersion != "0.2.0" || m.DataBytes != userdataBytes || m.DataMajorMinor != "179:20" || m.FilesystemBytes != userdataFilesystemBytes {
			return fmt.Errorf("contrato de respaldo y preparacion de datos no permitido")
		}
	default:
		return fmt.Errorf("operacion no admitida")
	}
	for i, im := range m.Images {
		g := expectedGeometry[names[i]]
		if im.Name != names[i] || im.Entry != "tvbase/"+im.Name+".img" || im.Size != g.Size || im.MajorMinor != g.MajorMinor {
			return fmt.Errorf("geometria exacta no coincide: %s", im.Name)
		}
		if !validSHA(im.SHA256) || !validSHA(im.OriginalSHA256) {
			return fmt.Errorf("SHA256 invalido")
		}
		if im.SHA256 != platformImageHashes[im.Name] || im.OriginalSHA256 != originalImageHashes[im.Name] {
			return fmt.Errorf("payload/origen no es la revision inmutable aprobada: %s", im.Name)
		}
	}
	return nil
}
func loadPackage(path string) (*Package, error) {
	z, e := zip.OpenReader(path)
	if e != nil {
		return nil, e
	}
	p := &Package{ZIP: z, Entries: map[string]*zip.File{}}
	fail := func(e error) (*Package, error) { z.Close(); return nil, e }
	for _, f := range z.File {
		if _, ok := p.Entries[f.Name]; ok {
			return fail(fmt.Errorf("entrada ZIP duplicada: %s", f.Name))
		}
		p.Entries[f.Name] = f
	}
	f := p.Entries["tvbase/manifest.json"]
	if f == nil || f.UncompressedSize64 > 32768 {
		return fail(fmt.Errorf("manifiesto ausente o invalido"))
	}
	r, e := f.Open()
	if e != nil {
		return fail(e)
	}
	d := json.NewDecoder(io.LimitReader(r, 32769))
	d.DisallowUnknownFields()
	e = d.Decode(&p.Manifest)
	if e == nil {
		var extra any
		if end := d.Decode(&extra); end != io.EOF {
			e = fmt.Errorf("datos adicionales tras manifiesto")
		}
	}
	r.Close()
	if e != nil {
		return fail(e)
	}
	if e = validateManifest(p.Manifest); e != nil {
		return fail(e)
	}
	for _, im := range p.Manifest.Images {
		f := p.Entries[im.Entry]
		if f == nil || int64(f.UncompressedSize64) != im.Size {
			return fail(fmt.Errorf("tamano ZIP incorrecto: %s", im.Name))
		}
	}
	return p, nil
}
func copyExact(dst io.Writer, src io.Reader, n int64, tick func(int64)) (string, error) {
	h := sha256.New()
	buf := make([]byte, 1<<20)
	var done int64
	for done < n {
		chunk := int64(len(buf))
		if n-done < chunk {
			chunk = n - done
		}
		got, e := io.ReadFull(src, buf[:chunk])
		if e != nil {
			return "", fmt.Errorf("lectura incompleta en %d: %w", done, e)
		}
		w, e := dst.Write(buf[:got])
		if e != nil {
			return "", e
		}
		if w != got {
			return "", io.ErrShortWrite
		}
		h.Write(buf[:got])
		done += int64(got)
		if tick != nil {
			tick(done)
		}
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}
func (p *Package) verify() error {
	return p.verifyWithProgress(nil)
}
func (p *Package) verifyWithProgress(tick func(Image, int64)) error {
	for _, im := range p.Manifest.Images {
		r, e := p.Entries[im.Entry].Open()
		if e != nil {
			return e
		}
		s, e := copyExact(io.Discard, r, im.Size, func(n int64) {
			if tick != nil {
				tick(im, n)
			}
		})
		if e == nil {
			var extra [1]byte
			n, last := r.Read(extra[:])
			if n != 0 || last != io.EOF {
				e = fmt.Errorf("final ZIP/CRC invalido: %s", im.Name)
			}
		}
		r.Close()
		if e != nil {
			return e
		}
		if s != im.SHA256 {
			return fmt.Errorf("hash incorrecto: %s", im.Name)
		}
	}
	return nil
}
func fileHash(path string, n int64) (string, error) {
	f, e := os.Open(path)
	if e != nil {
		return "", e
	}
	defer f.Close()
	return copyExact(io.Discard, f, n, nil)
}
