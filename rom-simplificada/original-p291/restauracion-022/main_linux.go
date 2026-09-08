//go:build linux

package main

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

var ui io.Writer = os.Stderr

func say(s string)       { fmt.Fprintln(ui, "ui_print "+s); fmt.Fprintln(ui, "ui_print") }
func progress(v float64) { fmt.Fprintf(ui, "set_progress %.3f\n", v) }

func hashWithRecoveryProgress(path string, size int64, label string) (string, error) {
	last := time.Time{}
	return hashBackupSource(path, size, func(n int64) {
		if time.Since(last) >= 5*time.Second {
			say(fmt.Sprintf("%s: %d/%d bytes", label, n, size))
			last = time.Now()
		}
	})
}

type Target struct {
	Layout       BlockLayout
	Image        Image
	Path         string
	Size         int64
	Device       uint64
	MajorMinor   string
	Disk         string
	Backup       string
	OriginalHash string
}

func readText(p string) string {
	b, _ := os.ReadFile(p)
	return strings.TrimSpace(strings.Trim(string(b), "\x00"))
}
func mm(r uint64) string {
	major := (r>>8)&0xfff | (r>>32)&0xfffff000
	minor := r&255 | (r>>12)&0xffffff00
	return fmt.Sprintf("%d:%d", major, minor)
}
func prepareTargets(p *Package) ([]Target, error) {
	if os.Geteuid() != 0 {
		return nil, fmt.Errorf("se requiere recovery con acceso root")
	}
	found := false
	procs, _ := filepath.Glob("/proc/[0-9]*/cmdline")
	for _, f := range procs {
		b, _ := os.ReadFile(f)
		cmd := strings.Split(string(b), "\x00")[0]
		if cmd == "/sbin/recovery" || cmd == "/system/bin/recovery" || cmd == "recovery" {
			found = true
			break
		}
	}
	if !found {
		return nil, fmt.Errorf("este instalador solo funciona dentro del recovery")
	}
	dt := readText("/proc/device-tree/amlogic-dt-id")
	if dt == "" {
		dt = readText("/sys/firmware/devicetree/base/amlogic-dt-id")
	}
	if dt != p.Manifest.DT {
		return nil, fmt.Errorf("placa no admitida: %q; se requiere %s", dt, p.Manifest.DT)
	}
	for _, s := range []string{"/dev/block/by-name/boot_a", "/dev/block/boot_a", "/dev/block/mapper/system"} {
		if _, e := os.Stat(s); e == nil {
			return nil, fmt.Errorf("esquema A/B o dinamico no admitido")
		}
	}
	var ts []Target
	seen := map[uint64]bool{}
	disk := ""
	for _, im := range p.Manifest.Images {
		candidates := []string{"/dev/block/by-name/" + im.Name, "/dev/block/" + im.Name}
		extra, _ := filepath.Glob("/dev/block/platform/*/by-name/" + im.Name)
		candidates = append(candidates, extra...)
		path := ""
		for _, c := range candidates {
			if _, e := os.Stat(c); e == nil {
				path = c
				break
			}
		}
		if path == "" {
			return nil, fmt.Errorf("falta particion %s", im.Name)
		}
		layout, e := inspectBlock(path, im.Name)
		if e != nil {
			return nil, fmt.Errorf("fase destinos, %s: %w", im.Name, e)
		}
		size, r, d := int64(layout.Bytes), layout.Device, layout.ParentPath
		if size != im.Size || mm(r) != im.MajorMinor {
			return nil, fmt.Errorf("%s no coincide con geometria original: %d/%s", im.Name, size, mm(r))
		}
		if seen[r] {
			return nil, fmt.Errorf("dos nombres apuntan a la misma particion")
		}
		seen[r] = true
		if disk != "" && disk != d {
			return nil, fmt.Errorf("las particiones no pertenecen al mismo eMMC")
		}
		disk = d
		ts = append(ts, Target{Layout: layout, Image: im, Path: path, Size: size, Device: r, MajorMinor: mm(r), Disk: d})
	}
	// Refuse enabled AVB rather than changing its policy or bootloader.
	for _, path := range []string{"/dev/block/by-name/vbmeta", "/dev/block/vbmeta"} {
		if f, e := os.Open(path); e == nil {
			b := make([]byte, 4096)
			n, e := f.Read(b)
			f.Close()
			if e != nil {
				return nil, e
			}
			for _, v := range b[:n] {
				if v != 0 {
					return nil, fmt.Errorf("vbmeta no vacio: requiere revisar verificacion de arranque")
				}
			}
			break
		}
	}
	mountBytes, mountError := os.ReadFile("/proc/self/mountinfo")
	if mountError != nil {
		return nil, mountError
	}
	mountInfo := string(mountBytes)
	for _, line := range strings.Split(mountInfo, "\n") {
		fields := strings.Fields(line)
		if len(fields) < 6 {
			continue
		}
		for _, t := range ts {
			if fields[2] == t.MajorMinor {
				return nil, fmt.Errorf("particion %s montada en %s: desmontarla desde recovery antes de instalar", t.Image.Name, fields[4])
			}
		}
	}
	if p.Manifest.Operation == "install_reviewed_with_userdata_migration" {
		actual, e := fileHash(ts[len(ts)-1].Path, ts[len(ts)-1].Size)
		if e != nil || actual != originalBootSHA256 {
			return nil, fmt.Errorf("boot actual no es el original adquirido; revisar antes de primera instalacion")
		}
	}
	return ts, nil
}
func syncDir(path string) error {
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	return f.Sync()
}
func targetsUnmounted(ts []Target) error {
	raw, err := os.ReadFile("/proc/self/mountinfo")
	if err != nil {
		return err
	}
	for _, line := range strings.Split(string(raw), "\n") {
		fields := strings.Fields(line)
		if len(fields) < 6 {
			continue
		}
		for _, t := range ts {
			if fields[2] == t.MajorMinor {
				return fmt.Errorf("destino %s montado durante operacion", t.Image.Name)
			}
		}
	}
	return nil
}
func usbDirectory() (string, error) { return usbDirectoryWithRemount(true) }
func usbDirectoryWithRemount(allowRemount bool) (string, error) {
	raw, e := os.ReadFile("/proc/mounts")
	if e != nil {
		return "", e
	}
	var candidates [][]string
	for _, line := range strings.Split(string(raw), "\n") {
		f := strings.Fields(line)
		if len(f) < 4 || (f[2] != "vfat" && f[2] != "exfat") {
			continue
		}
		path := strings.ReplaceAll(f[1], `\040`, " ")
		if readText(filepath.Join(path, "TVBASE-MEDIA.txt")) != mediaID {
			continue
		}
		st, e := os.Stat(f[0])
		if e != nil || st.Mode()&os.ModeDevice == 0 || st.Mode()&os.ModeCharDevice != 0 {
			continue
		}
		r := uint64(st.Sys().(*syscall.Stat_t).Rdev)
		sy, e := filepath.EvalSymlinks("/sys/dev/block/" + mm(r))
		if e != nil || !strings.Contains(sy, "/usb") {
			continue
		}
		candidates = append(candidates, []string{f[0], path, f[2], f[3]})
	}
	if len(candidates) != 1 {
		return "", fmt.Errorf("se requiere un unico pendrive TVBASE fisico montado; encontrados %d", len(candidates))
	}
	c := candidates[0]
	if strings.Contains(","+c[3]+",", ",ro,") {
		if !allowRemount {
			return "", fmt.Errorf("el pendrive cambio a solo lectura; se conserva el fallo")
		}
		if e = syscall.Mount(c[0], c[1], c[2], syscall.MS_REMOUNT|syscall.MS_NODEV|syscall.MS_NOSUID|syscall.MS_NOEXEC, ""); e != nil {
			return "", e
		}
		return usbDirectoryWithRemount(false)
	}
	return c[1], nil
}
func flash(p *Package, ts []Target, dir string) (result error) {
	if e := checkBootEnvironment(ts[0].Disk); e != nil {
		return e
	}
	usb := filepath.Dir(dir)
	if e := targetSetGuard(ts, usb); e != nil {
		return e
	}
	log, e := os.OpenFile(filepath.Join(dir, "instalacion.log"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	defer func() {
		if e := log.Close(); result == nil {
			result = e
		}
	}()
	if e = syncDir(dir); e != nil {
		return e
	}
	for i, t := range ts {
		if e = targetSetGuard(ts, usb); e != nil {
			return e
		}

		if e = targetSetGuard(ts, usb); e != nil {
			return e
		}
		// Recheck every path immediately before a destructive open.
		layout, e := inspectBlock(t.Path, t.Image.Name)
		if e != nil {
			return fmt.Errorf("antes de flash %s: %w", t.Image.Name, e)
		}
		if layout != t.Layout {
			return fmt.Errorf("antes de flash: cambio layout %s", t.Image.Name)
		}
		if _, e = fmt.Fprintln(log, "INICIO", t.Image.Name, time.Now().UTC().Format(time.RFC3339)); e != nil {
			return e
		}
		if e = log.Sync(); e != nil {
			return e
		}
		say("Instalando " + t.Image.Name + ". No desconectar la alimentacion.")
		in, e := p.Entries[t.Image.Entry].Open()
		if e != nil {
			return e
		}
		out, e := os.OpenFile(t.Path, os.O_WRONLY, 0)
		if e != nil {
			in.Close()
			return e
		}
		last := -1
		sum, e := copyExact(out, in, t.Image.Size, func(n int64) {
			pc := int(n * 100 / t.Image.Size)
			if pc != last {
				last = pc
				progress(.5 + .45*(float64(i)+float64(n)/float64(t.Image.Size))/float64(len(ts)))
			}
		})
		in.Close()
		if e == nil {
			e = out.Sync()
		}
		ce := out.Close()
		if e == nil {
			e = ce
		}
		if e != nil {
			return e
		}
		if sum != t.Image.SHA256 {
			return fmt.Errorf("hash al escribir incorrecto: %s", t.Image.Name)
		}
		say("Verificando " + t.Image.Name)
		check, e := hashWithRecoveryProgress(t.Path, t.Image.Size, "Verificando "+t.Image.Name)
		if e != nil || check != t.Image.SHA256 {
			return fmt.Errorf("verificacion de memoria fallo: %s (%v)", t.Image.Name, e)
		}
		if _, e = fmt.Fprintln(log, "VERIFICADO", t.Image.Name, check); e != nil {
			return e
		}
		if e = log.Sync(); e != nil {
			return e
		}
	}
	return nil
}
func run() error {
	if len(os.Args) < 4 || os.Args[1] != "3" {
		return errors.New("usar desde recovery, interfaz3")
	}
	fd, e := strconv.Atoi(os.Args[2])
	if e != nil || fd < 3 {
		return errors.New("descriptor recovery invalido")
	}
	ui = os.NewFile(uintptr(fd), "recovery-ui")
	if ui == nil {
		return errors.New("sin salida recovery")
	}
	say("Restaurador original P291 0.2.2: cinco particiones, sin borrar userdata.")
	p, e := loadPackage(os.Args[3])
	if e != nil {
		return e
	}
	defer p.ZIP.Close()
	ts, e := prepareTargets(p)
	if e != nil {
		return e
	}
	if e = checkBootEnvironment(ts[0].Disk); e != nil {
		return e
	}
	usb, e := usbDirectory()
	if e != nil {
		return e
	}
	packagePath, e := filepath.EvalSymlinks(os.Args[3])
	if e != nil {
		return e
	}
	rootPath, e := filepath.EvalSymlinks(usb)
	if e != nil {
		return e
	}
	if !strings.HasPrefix(packagePath, rootPath+string(os.PathSeparator)) {
		return fmt.Errorf("abrir el ZIP directamente desde el USB marcado")
	}
	if e = rejectIncompleteMigration(usb); e != nil {
		return e
	}
	say("Comprobando las cinco imagenes originales antes de restaurar.")
	lastVerify := time.Time{}
	if e = p.verifyWithProgress(func(im Image, n int64) {
		if time.Since(lastVerify) >= 5*time.Second {
			say(fmt.Sprintf("Comprobando %s: %d/%d bytes", im.Name, n, im.Size))
			lastVerify = time.Now()
		}
	}); e != nil {
		return e
	}
	dir, records, e := backupFive(ts, usb)
	if e != nil {
		return e
	}
	if e = persistBackupSet(dir, records, ts); e != nil {
		return e
	}
	if e = backupSetStillValid(dir, records, ts, usb); e != nil {
		return e
	}
	if e = writeDurableJSON(filepath.Join(dir, "10-restore-started.json"), map[string]any{"state": "restore_started", "userdata_untouched": true}); e != nil {
		return e
	}
	if e = flash(p, ts, dir); e != nil {
		return e
	}
	if e = writeDurableJSON(filepath.Join(dir, "90-restored-verified.json"), map[string]any{"state": "restored_verified", "package_id": allowedPackageID, "userdata_untouched": true}); e != nil {
		return e
	}
	progress(1)
	say("Cinco particiones originales restauradas y releidas. Se conservan los datos existentes.")
	say("Este ZIP no recupera el respaldo anterior de userdata. Reiniciar desde recovery.")
	return nil
}
func main() {
	if e := run(); e != nil {
		say("ERROR: " + e.Error())
		say("Conservar el respaldo y permanecer en recovery si ya comenzo la escritura.")
		os.Exit(1)
	}
}
