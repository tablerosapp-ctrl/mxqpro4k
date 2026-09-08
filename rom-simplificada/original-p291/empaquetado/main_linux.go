//go:build linux

package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

var ui io.Writer = os.Stderr

func say(s string)       { fmt.Fprintln(ui, "ui_print "+s); fmt.Fprintln(ui, "ui_print") }
func progress(v float64) { fmt.Fprintf(ui, "set_progress %.3f\n", v) }

type Target struct {
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
func block(path string) (int64, uint64, string, error) {
	f, e := os.Open(path)
	if e != nil {
		return 0, 0, "", e
	}
	defer f.Close()
	s, e := f.Stat()
	if e != nil {
		return 0, 0, "", e
	}
	if s.Mode()&os.ModeDevice == 0 || s.Mode()&os.ModeCharDevice != 0 {
		return 0, 0, "", fmt.Errorf("no es particion de bloques: %s", path)
	}
	r := uint64(s.Sys().(*syscall.Stat_t).Rdev)
	var size uint64
	_, _, errno := syscall.Syscall(syscall.SYS_IOCTL, f.Fd(), uintptr(0x80081272), uintptr(unsafe.Pointer(&size)))
	if errno != 0 {
		return 0, 0, "", errno
	}
	sy, e := filepath.EvalSymlinks("/sys/dev/block/" + mm(r))
	if e != nil {
		return 0, 0, "", e
	}
	base := filepath.Base(sy)
	if !regexp.MustCompile(`^mmcblk[0-9]+p[1-9][0-9]*$`).MatchString(base) {
		return 0, 0, "", fmt.Errorf("destino no eMMC particionada: %s", base)
	}
	disk := base[:strings.LastIndex(base, "p")]
	if readText("/sys/class/block/"+disk+"/device/type") != "MMC" {
		return 0, 0, "", fmt.Errorf("destino no MMC interna")
	}
	if size == 0 || size > 4<<30 {
		return 0, 0, "", fmt.Errorf("tamano de particion no admitido")
	}
	return int64(size), r, disk, nil
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
		size, r, d, e := block(path)
		if e != nil {
			return nil, e
		}
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
		ts = append(ts, Target{Image: im, Path: path, Size: size, Device: r, MajorMinor: mm(r), Disk: d})
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
	mountInfo := readText("/proc/self/mountinfo")
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
	if p.Manifest.Operation == "install_reviewed" {
		actual, e := fileHash(ts[len(ts)-1].Path, ts[len(ts)-1].Size)
		if e != nil || actual != originalBootSHA256 {
			return nil, fmt.Errorf("boot actual no es el original adquirido; revisar antes de primera instalacion")
		}
		if e = checkFreshUserdata(disk); e != nil {
			return nil, e
		}
	}
	return ts, nil
}
func checkFreshUserdata(disk string) error {
	size, r, d, e := block("/dev/block/data")
	if e != nil {
		return e
	}
	if size != 3495952384 || mm(r) != "179:20" || d != disk {
		return fmt.Errorf("userdata no coincide con la geometria original")
	}
	if e = requireDataReadOnlyMount(readText("/proc/self/mountinfo"), mm(r)); e != nil {
		return e
	}
	return requireEmptyDataDirectory("/data")
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
	for _, line := range strings.Split(readText("/proc/self/mountinfo"), "\n") {
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
func usbDirectory() (string, error) {
	for _, line := range strings.Split(readText("/proc/mounts"), "\n") {
		f := strings.Fields(line)
		if len(f) < 4 || (f[2] != "vfat" && f[2] != "exfat") {
			continue
		}
		path := strings.ReplaceAll(f[1], `\040`, " ")
		if readText(filepath.Join(path, "TVBASE-MEDIA.txt")) != mediaID {
			continue
		}
		stat, e := os.Stat(f[0])
		if e != nil || stat.Mode()&os.ModeDevice == 0 {
			continue
		}
		r := uint64(stat.Sys().(*syscall.Stat_t).Rdev)
		sy, e := filepath.EvalSymlinks("/sys/dev/block/" + mm(r))
		if e != nil || !strings.Contains(sy, "/usb") {
			continue
		}
		if strings.Contains(","+f[3]+",", ",ro,") {
			if e = syscall.Mount(f[0], path, f[2], syscall.MS_REMOUNT|syscall.MS_NODEV|syscall.MS_NOSUID|syscall.MS_NOEXEC, ""); e != nil {
				return "", fmt.Errorf("USB solo lectura: %w", e)
			}
		}
		return path, nil
	}
	return "", fmt.Errorf("no se encontro el pendrive TVBASE montado; no se escribio Android")
}
func backup(ts []Target, usb string) (string, error) {
	var total int64
	for _, t := range ts {
		total += t.Size
		if t.Size >= 0xffffffff {
			return "", fmt.Errorf("copia excede limite FAT32")
		}
	}
	var fs syscall.Statfs_t
	if e := syscall.Statfs(usb, &fs); e != nil {
		return "", e
	}
	if uint64(fs.Bavail)*uint64(fs.Bsize) < uint64(total)+(256<<20) {
		return "", fmt.Errorf("espacio insuficiente para respaldo completo")
	}
	dir, e := os.MkdirTemp(usb, "TVBASE-respaldo-")
	if e != nil {
		return "", e
	}
	if e = syncDir(usb); e != nil {
		return dir, e
	}
	say("Guardando cinco particiones originales en el pendrive. No es un respaldo de userdata.")
	for i := range ts {
		t := &ts[i]
		say("Respaldando " + t.Image.Name)
		t.Backup = t.Image.Name + ".img"
		dst := filepath.Join(dir, t.Backup)
		if e = targetsUnmounted(ts); e != nil {
			return dir, e
		}
		in, e := os.Open(t.Path)
		if e != nil {
			return dir, e
		}
		out, e := os.OpenFile(dst, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			in.Close()
			return dir, e
		}
		s, e := copyExact(out, in, t.Size, nil)
		in.Close()
		if e == nil {
			e = out.Sync()
		}
		ce := out.Close()
		if e == nil {
			e = ce
		}
		if e != nil {
			return dir, e
		}
		t.OriginalHash = s
		check, e := fileHash(dst, t.Size)
		if e != nil || check != s {
			return dir, fmt.Errorf("respaldo no verificado: %s (%v)", t.Image.Name, e)
		}
		if e = syncDir(dir); e != nil {
			return dir, e
		}
		progress(.2 + .3*float64(i+1)/float64(len(ts)))
	}
	data, _ := json.MarshalIndent(ts, "", "  ")
	f, e := os.OpenFile(filepath.Join(dir, "respaldo.json"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return dir, e
	}
	_, e = f.Write(data)
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e == nil {
		e = ce
	}
	if e == nil {
		e = syncDir(dir)
	}
	return dir, e
}
func flash(p *Package, ts []Target, dir string) error {
	log, e := os.OpenFile(filepath.Join(dir, "instalacion.log"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	defer log.Close()
	if e = syncDir(dir); e != nil {
		return e
	}
	for i, t := range ts {
		if e = targetsUnmounted(ts); e != nil {
			return e
		}
		if p.Manifest.Operation == "install_reviewed" {
			if e = checkFreshUserdata(t.Disk); e != nil {
				return e
			}
		}
		// Recheck every path immediately before a destructive open.
		size, r, _, e := block(t.Path)
		if e != nil || r != t.Device || size != t.Size {
			return fmt.Errorf("cambio el destino %s", t.Image.Name)
		}
		fmt.Fprintln(log, "INICIO", t.Image.Name, time.Now().UTC().Format(time.RFC3339))
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
		check, e := fileHash(t.Path, t.Image.Size)
		if e != nil || check != t.Image.SHA256 {
			return fmt.Errorf("verificacion de memoria fallo: %s (%v)", t.Image.Name, e)
		}
		fmt.Fprintln(log, "VERIFICADO", t.Image.Name, check)
		if e = log.Sync(); e != nil {
			return e
		}
	}
	syscall.Sync()
	progress(1)
	say("ROM instalada y leida correctamente. Respaldo: " + filepath.Base(dir))
	say("Reiniciar desde recovery. El primer arranque puede tardar.")
	return nil
}
func run() error {
	if len(os.Args) < 4 || os.Args[1] != "3" {
		return errors.New("usar desde recovery, interfaz de instalacion 3")
	}
	fd, e := strconv.Atoi(os.Args[2])
	if e != nil || fd < 3 {
		return errors.New("descriptor de recovery invalido")
	}
	ui = os.NewFile(uintptr(fd), "recovery-ui")
	if ui == nil {
		return errors.New("sin salida recovery")
	}
	say("TVBASE P291 original - paquete experimental 0.2.0")
	p, e := loadPackage(os.Args[3])
	if e != nil {
		return e
	}
	defer p.ZIP.Close()
	if p.Manifest.Operation == "restore_original" {
		say("Restauracion de cinco particiones OEM. Se conserva userdata sin sanearla.")
	} else {
		say("La ROM exige userdata limpia preparada por separado. Este ZIP no borra ni migra datos.")
	}
	ts, e := prepareTargets(p)
	if e != nil {
		return e
	}
	usb, e := usbDirectory()
	if e != nil {
		return e
	}
	say("Comprobando integridad de todas las imagenes...")
	if e = p.verify(); e != nil {
		return e
	}
	progress(.2)
	dir, e := backup(ts, usb)
	if e != nil {
		return e
	}
	say("Respaldo verificado. Se reemplazan system, vendor, product, odm y boot.")
	return flash(p, ts, dir)
}
func main() {
	if e := run(); e != nil {
		say("ERROR: " + e.Error())
		say("Si ya comenzo la escritura, conservar el respaldo y permanecer en recovery.")
		os.Exit(1)
	}
}
