//go:build linux

package main

import (
	"bytes"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"syscall"
	"time"
)

var ui io.Writer = os.Stderr

func say(s string) {
	s = strings.NewReplacer("\n", " ", "\r", " ", "\x00", " ").Replace(s)
	fmt.Fprintln(ui, "ui_print "+s)
	fmt.Fprintln(ui, "ui_print")
}

type Media struct {
	Schema  string `json:"schema"`
	MediaID string `json:"media_id"`
}
type ProfilePlan struct {
	Schema       string `json:"schema"`
	APKCaptureID string `json:"apk_capture_id"`
	APKDeviceID  string `json:"apk_device_id"`
	APKZipSHA256 string `json:"apk_zip_sha256"`
	ExpectedDT   string `json:"expected_dt"`
	Profile      string `json:"profile"`
	DisplayName  string `json:"display_name"`
	Operation    string `json:"operation"`
}

func strictJSON(b []byte, v any) error {
	d := json.NewDecoder(bytes.NewReader(b))
	d.DisallowUnknownFields()
	if e := d.Decode(v); e != nil {
		return e
	}
	var extra any
	if e := d.Decode(&extra); e != io.EOF {
		return fmt.Errorf("JSON con datos adicionales")
	}
	return nil
}
func readDT() string {
	for _, p := range []string{"/proc/device-tree/amlogic-dt-id", "/sys/firmware/devicetree/base/amlogic-dt-id", "/proc/device-tree/compatible", "/sys/firmware/devicetree/base/compatible"} {
		b, e := bounded(p, 4096)
		if e == nil && len(b) > 0 {
			return strings.TrimSpace(strings.ReplaceAll(string(b), "\x00", " "))
		}
	}
	return ""
}
func recoveryContext() error {
	if os.Geteuid() != 0 {
		return fmt.Errorf("se requiere el contexto privilegiado del recovery")
	}
	ps, e := filepath.Glob("/proc/[0-9]*/cmdline")
	if e != nil || len(ps) > 4096 {
		return fmt.Errorf("procesos no verificables")
	}
	found := false
	for _, p := range ps {
		b, e := bounded(p, 16384)
		if e != nil {
			continue
		}
		first := strings.Split(string(b), "\x00")[0]
		name := filepath.Base(first)
		if name == "zygote" || name == "zygote64" || name == "system_server" {
			return fmt.Errorf("Android esta activo: no copiar bloques")
		}
		if name == "recovery" {
			found = true
		}
	}
	if !found {
		return fmt.Errorf("no se encontro recovery activo")
	}
	return nil
}
func ordinary(path string, dir bool) (os.FileInfo, error) {
	p, e := filepath.EvalSymlinks(path)
	if e != nil || p != filepath.Clean(path) {
		return nil, fmt.Errorf("ruta ausente o con enlaces: %s", path)
	}
	st, e := os.Stat(path)
	if e != nil {
		return nil, e
	}
	if dir && !st.IsDir() || !dir && !st.Mode().IsRegular() {
		return nil, fmt.Errorf("tipo de archivo incorrecto")
	}
	return st, nil
}

type usbTarget struct {
	Mount         Mount
	Root, SysPath string
	Dev           uint64
	Marker        []byte
}

func usbProof(m Mount) (string, error) {
	if !m.Writable || m.Root != "/" {
		return "", fmt.Errorf("USB no es montaje raiz de escritura")
	}
	if m.FS != "vfat" && m.FS != "exfat" && m.FS != "ext4" {
		return "", fmt.Errorf("filesystem USB no compatible")
	}
	p, e := filepath.EvalSymlinks("/sys/dev/block/" + m.Device)
	if e != nil || !strings.HasPrefix(p, "/sys/devices/") || !usbPattern.MatchString(p) {
		return "", fmt.Errorf("montaje no acreditado como USB fisico")
	}
	st, e := ordinary(m.Point, true)
	if e != nil {
		return "", e
	}
	if mm(uint64(st.Sys().(*syscall.Stat_t).Dev)) != m.Device {
		return "", fmt.Errorf("montaje y st_dev diferentes")
	}
	return p, nil
}
func findUSB() (usbTarget, error) {
	ms, e := currentMounts()
	if e != nil {
		return usbTarget{}, e
	}
	var found []usbTarget
	for _, m := range ms {
		sys, e := usbProof(m)
		if e != nil {
			continue
		}
		root := filepath.Join(m.Point, "TVBASE-EXTRACCION")
		st, e := ordinary(root, true)
		if e != nil {
			continue
		}
		mp := filepath.Join(root, "MEDIA.json")
		if _, e := ordinary(mp, false); e != nil {
			continue
		}
		b, e := bounded(mp, 4096)
		if e != nil {
			continue
		}
		var marker Media
		if strictJSON(b, &marker) != nil || marker.Schema != "tvbase-recovery-media-1" || marker.MediaID != "tvbase-recovery-kingston-20260908" {
			continue
		}
		dev := uint64(st.Sys().(*syscall.Stat_t).Dev)
		if mm(dev) != m.Device {
			continue
		}
		found = append(found, usbTarget{m, root, sys, dev, b})
	}
	if len(found) != 1 {
		return usbTarget{}, fmt.Errorf("se requiere un unico pendrive marcado y montado por recovery; encontrados %d", len(found))
	}
	return found[0], nil
}
func (u usbTarget) verify() error {
	ms, e := currentMounts()
	if e != nil {
		return e
	}
	ok := false
	for _, m := range ms {
		if m.Device == u.Mount.Device && m.Point == u.Mount.Point && m.Root == u.Mount.Root {
			sys, e := usbProof(m)
			if e == nil && sys == u.SysPath {
				ok = true
			}
		}
	}
	if !ok {
		return fmt.Errorf("USB desconectado o montaje cambiado")
	}
	if _, e := ordinary(u.Root, true); e != nil {
		return e
	}
	p := filepath.Join(u.Root, "MEDIA.json")
	if _, e := ordinary(p, false); e != nil {
		return e
	}
	b, e := bounded(p, 4096)
	if e != nil || !bytes.Equal(b, u.Marker) {
		return fmt.Errorf("marcador USB cambio")
	}
	return nil
}
func loadPlan(root, dt string) (*ProfilePlan, error) {
	dir := filepath.Join(root, "PLANES")
	if _, e := ordinary(dir, true); e != nil {
		return nil, e
	}
	files, e := os.ReadDir(dir)
	if e != nil || len(files) > 64 {
		return nil, fmt.Errorf("carpeta PLANES invalida")
	}
	var matches []*ProfilePlan
	for _, f := range files {
		if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") {
			continue
		}
		p := filepath.Join(dir, f.Name())
		if _, e := ordinary(p, false); e != nil {
			return nil, e
		}
		b, e := bounded(p, 16384)
		if e != nil {
			return nil, e
		}
		var plan ProfilePlan
		if e = strictJSON(b, &plan); e != nil {
			return nil, fmt.Errorf("plan JSON invalido: %w", e)
		}
		if plan.Schema != "tvbase-recovery-plan-1" || plan.Operation != "capture_read_only" || len(plan.ExpectedDT) == 0 || len(plan.ExpectedDT) > 4096 || len(plan.APKZipSHA256) != 64 || !safeRelative(plan.Profile) || len(plan.Profile) > 80 || len(plan.APKCaptureID) != 36 || len(plan.APKDeviceID) != 36 {
			return nil, fmt.Errorf("plan no corresponde al contrato")
		}
		if _, e := hex.DecodeString(plan.APKZipSHA256); e != nil {
			return nil, e
		}
		if dt != "" && plan.ExpectedDT == dt {
			copy := plan
			matches = append(matches, &copy)
		}
	}
	if len(matches) > 1 {
		return nil, fmt.Errorf("mas de un plan coincide: revisar en PC antes de extraer")
	}
	if len(matches) == 0 {
		return nil, nil
	}
	return matches[0], nil
}
func run() error {
	if e := recoveryContext(); e != nil {
		return e
	}
	say("TV Base - Extraccion de originales 0.1. No instala ni formatea.")
	usb, e := findUSB()
	if e != nil {
		return e
	}
	dt := readDT()
	plan, e := loadPlan(usb.Root, dt)
	if e != nil {
		return e
	}
	facts, skips, ident, e := inventory()
	if e != nil {
		return e
	}
	mounts, e := currentMounts()
	if e != nil {
		return e
	}
	chosen, selectedSkips, e := chooseSources(facts, mounts)
	if e != nil {
		return e
	}
	skips = append(skips, selectedSkips...)
	random := make([]byte, 16)
	if _, e = io.ReadFull(rand.Reader, random); e != nil {
		return e
	}
	captureID := hex.EncodeToString(random)
	profile := "sin-plan"
	if plan != nil {
		profile = plan.Profile
	}
	parent := filepath.Join(usb.Root, "CAPTURAS")
	if _, e = ordinary(parent, true); e != nil {
		return e
	}
	if e = usb.verify(); e != nil {
		return e
	}
	output := filepath.Join(parent, "TVBASE-"+profile+"-"+captureID)
	dest, e := newDestination(usb, parent, filepath.Base(output))
	if e != nil {
		return e
	}
	defer syscall.Close(dest.fd)
	if e = dest.check(); e != nil {
		return e
	}
	info := map[string]any{"schema": "tvbase-recovery-inventory-1", "capture_id": captureID, "profile_plan": plan, "dt_identity": dt, "emmc_identity_hashes": ident, "blocks": facts, "mounts": mounts, "omitted": skips, "captured_wall_time": time.Now().UTC().Format(time.RFC3339), "wall_clock_trusted": false, "coverage": "Only reported accessible areas; not RPMB, a tested restore, malware attestation, or universal device support."}
	if b, e := bounded("/proc/version", 8192); e == nil {
		info["kernel"] = string(b)
	}
	if b, e := bounded("/proc/partitions", 65536); e == nil {
		info["proc_partitions"] = string(b)
	}
	if e = dest.json("inventario.json", info); e != nil {
		return e
	}
	if plan == nil {
		say("INVENTARIO GUARDADO. Falta el plan asociado a la captura APK; no se copiaron imagenes.")
		return dest.json("resultado.json", map[string]any{"schema": "tvbase-recovery-result-1", "status": "inventory_only", "capture_id": captureID, "images_copied": false, "reason": "no_matching_apk_plan"})
	}
	if len(chosen) == 0 {
		return fmt.Errorf("inventario guardado, pero no hay areas eMMC estables para copiar")
	}
	baseline := append([]BlockFact(nil), facts...)
	baselineDT := dt
	revalidate := func() error {
		if e := usb.verify(); e != nil {
			return e
		}
		if e := recoveryContext(); e != nil {
			return e
		}
		if readDT() != baselineDT {
			return fmt.Errorf("cambio identidad DT")
		}
		now, _, nowIdent, e := inventory()
		if e != nil {
			return e
		}
		if !reflect.DeepEqual(now, baseline) || !reflect.DeepEqual(nowIdent, ident) {
			return fmt.Errorf("cambio el inventario de bloques")
		}
		ms, e := currentMounts()
		if e != nil {
			return e
		}
		cs, _, e := chooseSources(now, ms)
		if e != nil {
			return e
		}
		if !reflect.DeepEqual(cs, chosen) {
			return fmt.Errorf("cambio disponibilidad/montaje de los origenes")
		}
		return nil
	}
	cp := CapturePlan{}
	for _, f := range chosen {
		cp.Sources = append(cp.Sources, Source{Name: f.Name, Device: f.Path, Bytes: f.Bytes, MajorMinor: f.MajorMinor, Kind: f.Kind, Aliases: f.Aliases})
	}
	for _, s := range skips {
		cp.Omitted = append(cp.Omitted, Omission{Name: s.Name, Reason: s.Reason})
	}
	last := time.Time{}
	report, e := Capture(cp, CaptureHooks{OpenSource: func(s Source) (io.ReadCloser, error) { return openBlock(s.Device, s.MajorMinor, s.Bytes) }, Revalidate: revalidate, FreeBytes: dest.free, Destination: dest, Progress: func(p Progress) {
		if time.Since(last) > 3*time.Second || p.BytesDone == p.BytesTotal {
			say(fmt.Sprintf("%s %s: %d / %d MiB", p.Stage, p.Name, p.BytesDone>>20, p.BytesTotal>>20))
			last = time.Now()
		}
	}})
	if e != nil {
		_ = dest.json("resultado-error.json", map[string]any{"schema": "tvbase-recovery-result-1", "status": "failed", "error": e.Error(), "capture_id": captureID})
		return e
	}
	b, e := bounded(filepath.Join(output, "report.json"), 4<<20)
	if e != nil {
		return e
	}
	h := sha256.Sum256(b)
	result := map[string]any{"schema": "tvbase-recovery-result-1", "status": "selected_sources_verified", "capture_id": captureID, "apk_capture_id": plan.APKCaptureID, "apk_device_id": plan.APKDeviceID, "apk_zip_sha256": plan.APKZipSHA256, "association_scope": "matched_device_tree_profile_not_proof_of_physical_identity", "report_sha256": hex.EncodeToString(h[:]), "source_count": len(report.Sources), "omitted_count": len(report.Omitted), "all_device_storage_copied": false, "device_written_by_extractor": false, "restore_tested": false}
	if e = dest.json("resultado.json", result); e != nil {
		return e
	}
	say("COPIA Y RELECTURA TERMINADAS. Revisar alcance y zonas omitidas en PC.")
	say("Archivos guardados en TVBASE-EXTRACCION/CAPTURAS. No se reinicia automaticamente.")
	return nil
}
func main() {
	if len(os.Args) == 2 && os.Args[1] == "--help" {
		fmt.Println("TV Base extractor 0.1; solo protocolo update-binary desde recovery. Sin plan APK coincidente guarda inventario; no instala ROM.")
		return
	}
	if len(os.Args) != 4 || (os.Args[1] != "1" && os.Args[1] != "2" && os.Args[1] != "3") {
		fmt.Fprintln(os.Stderr, "Solo se admite ejecucion por recovery (API, pipeFD, packageZIP).")
		os.Exit(1)
	}
	fd, e := strconv.Atoi(os.Args[2])
	if e != nil || fd < 3 || fd > 1024 {
		os.Exit(1)
	}
	f := os.NewFile(uintptr(fd), "recovery-status")
	st, e := f.Stat()
	if e != nil || st.Mode()&os.ModeNamedPipe == 0 {
		os.Exit(1)
	}
	ui = f
	if _, e := ordinary(os.Args[3], false); e != nil {
		say("ERROR: paquete de origen no verificable")
		os.Exit(1)
	}
	if e = run(); e != nil {
		say("ERROR DE EXTRACCION: " + e.Error())
		say("Conservar archivos y mensaje; no repetir automaticamente.")
		os.Exit(1)
	}
}
