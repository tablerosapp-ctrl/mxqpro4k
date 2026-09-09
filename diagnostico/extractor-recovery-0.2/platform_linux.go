//go:build linux

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"unsafe"
)

var diskPattern = regexp.MustCompile(`^mmcblk[0-9]+$`)
var bootPattern = regexp.MustCompile(`^(mmcblk[0-9]+)boot[01]$`)
var usbPattern = regexp.MustCompile(`/usb[0-9]+/`)

func mm(r uint64) string {
	return fmt.Sprintf("%d:%d", (r>>8)&0xfff|(r>>32)&0xfffff000, r&255|(r>>12)&0xffffff00)
}
func bounded(path string, limit int64) ([]byte, error) {
	f, e := os.Open(path)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	b, e := io.ReadAll(io.LimitReader(f, limit+1))
	if e != nil {
		return nil, e
	}
	if int64(len(b)) > limit {
		return nil, fmt.Errorf("archivo excede limite: %s", path)
	}
	return b, nil
}
func attr(path string) (string, error) {
	p, e := filepath.EvalSymlinks(path)
	if e != nil || p != filepath.Clean(path) {
		return "", fmt.Errorf("atributo ausente/redirigido %s", path)
	}
	b, e := bounded(path, 4096)
	if e != nil {
		return "", e
	}
	s := strings.TrimSpace(string(b))
	if s == "" || strings.ContainsAny(s, "\x00\r\n") {
		return "", fmt.Errorf("atributo invalido %s", path)
	}
	return s, nil
}
func numAttr(path string) (int64, error) {
	s, e := attr(path)
	if e != nil {
		return 0, e
	}
	return strconv.ParseInt(s, 10, 64)
}
func currentMounts() ([]Mount, error) {
	b, e := bounded("/proc/self/mountinfo", 1<<20)
	if e != nil {
		return nil, e
	}
	mounts, e := parseMounts(b)
	if e != nil {
		return nil, e
	}
	sw, e := bounded("/proc/swaps", 65536)
	if os.IsNotExist(e) {
		return mounts, nil
	}
	if e != nil {
		return nil, e
	}
	for i, line := range strings.Split(strings.TrimSpace(string(sw)), "\n") {
		if i == 0 {
			continue
		}
		f := strings.Fields(line)
		if len(f) < 5 {
			return nil, fmt.Errorf("swap no verificable")
		}
		path, e := unescapeMount(f[0])
		if e != nil {
			return nil, e
		}
		st, e := os.Stat(path)
		if e != nil {
			return nil, fmt.Errorf("swap inaccesible")
		}
		dev := uint64(st.Sys().(*syscall.Stat_t).Dev)
		if st.Mode()&os.ModeDevice != 0 && st.Mode()&os.ModeCharDevice == 0 {
			dev = uint64(st.Sys().(*syscall.Stat_t).Rdev)
		}
		mounts = append(mounts, Mount{Device: mm(dev), Point: path, FS: "swap", ReadOnly: false})
	}
	return mounts, nil
}
func blockSize(f *os.File) (int64, error) {
	var n uint64
	op := uintptr(0x80001272) | (unsafe.Sizeof(uintptr(0)) << 16)
	_, _, e := syscall.Syscall(syscall.SYS_IOCTL, f.Fd(), op, uintptr(unsafe.Pointer(&n)))
	if e != 0 {
		return 0, e
	}
	if n == 0 || n > 1<<40 {
		return 0, fmt.Errorf("tamano de bloques fuera de limite")
	}
	return int64(n), nil
}
func openBlock(path, dev string, size int64) (*os.File, error) {
	resolved, e := filepath.EvalSymlinks(path)
	if e != nil || !strings.HasPrefix(resolved, "/dev/") {
		return nil, fmt.Errorf("nodo de origen invalido")
	}
	fd, e := syscall.Open(resolved, syscall.O_RDONLY|syscall.O_CLOEXEC|syscall.O_NOFOLLOW, 0)
	if e != nil {
		return nil, e
	}
	f := os.NewFile(uintptr(fd), resolved)
	st, e := f.Stat()
	if e != nil {
		f.Close()
		return nil, e
	}
	if st.Mode()&os.ModeDevice == 0 || st.Mode()&os.ModeCharDevice != 0 || mm(uint64(st.Sys().(*syscall.Stat_t).Rdev)) != dev {
		f.Close()
		return nil, fmt.Errorf("identidad de bloques cambio")
	}
	n, e := blockSize(f)
	if e != nil || n != size {
		f.Close()
		return nil, fmt.Errorf("tamano de origen distinto: %v", e)
	}
	return f, nil
}

// Inspect nodes by stat only; no block node is opened for writing, no RPMB IO.
func deviceNodes() (map[string][]string, error) {
	out := map[string][]string{}
	count := 0
	e := filepath.WalkDir("/dev/block", func(path string, d os.DirEntry, e error) error {
		if e != nil {
			return e
		}
		count++
		if count > 6000 {
			return fmt.Errorf("demasiados nodos de bloques")
		}
		if d.IsDir() {
			if strings.Count(strings.TrimPrefix(path, "/dev/block"), "/") > 9 {
				return filepath.SkipDir
			}
			return nil
		}
		st, e := os.Stat(path)
		if os.IsNotExist(e) {
			return nil
		}
		if e != nil {
			return e
		}
		if st.Mode()&os.ModeDevice != 0 && st.Mode()&os.ModeCharDevice == 0 {
			k := mm(uint64(st.Sys().(*syscall.Stat_t).Rdev))
			out[k] = append(out[k], path)
		}
		return nil
	})
	for k := range out {
		sort.Strings(out[k])
	}
	return out, e
}
func inspectFact(name, sys, parent, kind string, nodes map[string][]string) (BlockFact, error) {
	f := BlockFact{Name: name, SysPath: sys, Parent: parent, Kind: kind}
	var e error
	if f.MajorMinor, e = attr(filepath.Join(sys, "dev")); e != nil {
		return f, e
	}
	sectors, e := numAttr(filepath.Join(sys, "size"))
	if e != nil || sectors <= 0 || sectors > (1<<40)/512 {
		return f, fmt.Errorf("tamano sysfs invalido")
	}
	f.Bytes = sectors * 512
	if kind == "partition" {
		if f.Start, e = numAttr(filepath.Join(sys, "start")); e != nil {
			return f, e
		}
		if n, e := numAttr(filepath.Join(sys, "partition")); e != nil || n <= 0 {
			return f, fmt.Errorf("numero particion invalido")
		}
	}
	ro, e := attr(filepath.Join(sys, "ro"))
	if e != nil || ro != "0" && ro != "1" {
		return f, fmt.Errorf("atributo ro invalido")
	}
	f.ReadOnlyDevice = ro == "1"
	hs, e := os.ReadDir(filepath.Join(sys, "holders"))
	if e != nil {
		return f, e
	}
	f.Holders = []string{}
	for _, h := range hs {
		f.Holders = append(f.Holders, h.Name())
	}
	sort.Strings(f.Holders)
	f.Aliases = nodes[f.MajorMinor]
	if len(f.Aliases) == 0 {
		for _, p := range []string{"/dev/block/" + name, "/dev/" + name} {
			if st, e := os.Stat(p); e == nil && st.Mode()&os.ModeDevice != 0 && st.Mode()&os.ModeCharDevice == 0 && mm(uint64(st.Sys().(*syscall.Stat_t).Rdev)) == f.MajorMinor {
				f.Aliases = append(f.Aliases, p)
			}
		}
	}
	if len(f.Aliases) == 0 {
		return f, fmt.Errorf("no existe nodo para %s", name)
	}
	f.Path = f.Aliases[0]
	file, e := openBlock(f.Path, f.MajorMinor, f.Bytes)
	if e != nil {
		return f, e
	}
	e = file.Close()
	return f, e
}

func inventory() ([]BlockFact, []Skip, map[string]string, error) {
	nodes, e := deviceNodes()
	if e != nil {
		return nil, nil, nil, e
	}
	entries, e := os.ReadDir("/sys/class/block")
	if e != nil || len(entries) > 512 {
		return nil, nil, nil, fmt.Errorf("inventario sysfs invalido: %v", e)
	}
	disks := map[string]string{}
	var facts []BlockFact
	var skips []Skip
	identity := map[string]string{}
	for _, d := range entries {
		if !diskPattern.MatchString(d.Name()) {
			continue
		}
		p, e := filepath.EvalSymlinks("/sys/class/block/" + d.Name())
		if e != nil {
			return nil, nil, nil, e
		}
		if !strings.HasPrefix(p, "/sys/devices/") || strings.Contains(p, "/virtual/") || usbPattern.MatchString(p) {
			continue
		}
		card, e := filepath.EvalSymlinks(filepath.Join(p, "device"))
		if e != nil || !strings.HasPrefix(card, "/sys/devices/") || usbPattern.MatchString(card) || !strings.HasPrefix(p, card+"/") {
			return nil, nil, nil, fmt.Errorf("tarjeta MMC no verificada")
		}
		typ, e := attr(filepath.Join(card, "type"))
		if e != nil {
			skips = append(skips, Skip{d.Name(), "tipo de memoria no comprobado"})
			continue
		}
		rem, e := attr(filepath.Join(p, "removable"))
		if e != nil {
			return nil, nil, nil, e
		}
		if typ != "MMC" || rem != "0" {
			skips = append(skips, Skip{d.Name(), "no es eMMC interna no removible"})
			continue
		}
		disks[d.Name()] = p
		cid, e := attr(filepath.Join(card, "cid"))
		if e == nil {
			h := sha256.Sum256([]byte(cid))
			identity[d.Name()+"_cid_sha256"] = hex.EncodeToString(h[:])
		}
	}
	for _, d := range entries {
		name := d.Name()
		p, e := filepath.EvalSymlinks("/sys/class/block/" + name)
		if e != nil {
			return nil, nil, nil, e
		}
		parent, kind := "", ""
		if disks[name] == p {
			kind = "emmc_user_area"
		} else if m := bootPattern.FindStringSubmatch(name); m != nil && disks[m[1]] != "" && filepath.Dir(p) == disks[m[1]] {
			parent = m[1]
			kind = "emmc_boot_area"
		} else {
			for n, dp := range disks {
				if filepath.Dir(p) == dp {
					if _, e := os.Stat(filepath.Join(p, "partition")); e == nil {
						parent = n
						kind = "partition"
					}
				}
			}
		}
		if kind == "" {
			if !strings.HasPrefix(name, "loop") && !strings.HasPrefix(name, "ram") && !strings.HasPrefix(name, "zram") {
				skips = append(skips, Skip{name, "no es area eMMC soportada; RPMB/MTD/UFS/mappers no se copian por este adaptador"})
			}
			continue
		}
		if kind == "emmc_boot_area" {
			nested, e := os.ReadDir(p)
			if e != nil {
				return nil, nil, nil, e
			}
			hasChild := false
			for _, n := range nested {
				if _, e := os.Stat(filepath.Join(p, n.Name(), "partition")); e == nil {
					hasChild = true
				}
			}
			if hasChild {
				skips = append(skips, Skip{name, "area boot con particiones hijas no soportadas"})
				continue
			}
		}
		f, e := inspectFact(name, p, parent, kind, nodes)
		if e != nil {
			return nil, nil, nil, fmt.Errorf("inventario %s: %w", name, e)
		}
		facts = append(facts, f)
	}
	sort.Slice(facts, func(i, j int) bool { return facts[i].Name < facts[j].Name })
	return facts, skips, identity, nil
}

type linuxDestination struct {
	path   string
	device uint64
	verify func() error
	fd     int
}

func checkedDirectoryFD(path string, dev uint64) (int, error) {
	fd, e := syscall.Open(path, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if e != nil {
		return -1, e
	}
	var st syscall.Stat_t
	if e = syscall.Fstat(fd, &st); e != nil || uint64(st.Dev) != dev {
		syscall.Close(fd)
		return -1, fmt.Errorf("directorio no pertenece al SD")
	}
	return fd, nil
}
func newDestination(u sdTarget, parent, name string) (*linuxDestination, error) {
	if !safeRelative(name) {
		return nil, fmt.Errorf("nombre de captura invalido")
	}
	if e := u.verify(); e != nil {
		return nil, e
	}
	root, e := checkedDirectoryFD(u.Root, u.Dev)
	if e != nil {
		return nil, e
	}
	defer syscall.Close(root)
	pfd, e := syscall.Openat(root, "CAPTURAS", syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if e != nil {
		return nil, e
	}
	defer syscall.Close(pfd)
	var st syscall.Stat_t
	if e = syscall.Fstat(pfd, &st); e != nil || uint64(st.Dev) != u.Dev {
		return nil, fmt.Errorf("CAPTURAS fuera del SD")
	}
	if e = u.verify(); e != nil {
		return nil, e
	}
	if e = syscall.Mkdirat(pfd, name, 0700); e != nil {
		return nil, e
	}
	if e = syscall.Fsync(pfd); e != nil {
		return nil, e
	}
	fd, e := syscall.Openat(pfd, name, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if e != nil {
		return nil, e
	}
	if e = syscall.Fstat(fd, &st); e != nil || uint64(st.Dev) != u.Dev {
		syscall.Close(fd)
		return nil, fmt.Errorf("captura fuera del SD")
	}
	return &linuxDestination{path: filepath.Join(parent, name), device: u.Dev, verify: u.verify, fd: fd}, nil
}
func (d *linuxDestination) check() error {
	if e := d.verify(); e != nil {
		return e
	}
	p, e := filepath.EvalSymlinks(d.path)
	if e != nil || p != d.path {
		return fmt.Errorf("directorio de salida redirigido")
	}
	st, e := os.Stat(p)
	if e != nil || !st.IsDir() || uint64(st.Sys().(*syscall.Stat_t).Dev) != d.device {
		return fmt.Errorf("salida cambio de volumen")
	}
	var pinned syscall.Stat_t
	if e = syscall.Fstat(d.fd, &pinned); e != nil || uint64(pinned.Dev) != d.device || pinned.Ino != st.Sys().(*syscall.Stat_t).Ino {
		return fmt.Errorf("directorio fijado cambio")
	}
	return nil
}
func (d *linuxDestination) CreateExclusive(name string) (SyncWriteCloser, error) {
	if !safeRelative(name) {
		return nil, fmt.Errorf("nombre de salida invalido")
	}
	if e := d.check(); e != nil {
		return nil, e
	}
	fd, e := syscall.Openat(d.fd, name, syscall.O_WRONLY|syscall.O_CREAT|syscall.O_EXCL|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0600)
	if e != nil {
		return nil, e
	}
	f := os.NewFile(uintptr(fd), name)
	st, e := f.Stat()
	if e != nil || !st.Mode().IsRegular() || uint64(st.Sys().(*syscall.Stat_t).Dev) != d.device {
		f.Close()
		return nil, fmt.Errorf("salida no es archivo ordinario del SD")
	}
	return f, nil
}
func (d *linuxDestination) OpenRead(name string) (io.ReadCloser, error) {
	if !safeRelative(name) {
		return nil, fmt.Errorf("nombre invalido")
	}
	if e := d.check(); e != nil {
		return nil, e
	}
	fd, e := syscall.Openat(d.fd, name, syscall.O_RDONLY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if e != nil {
		return nil, e
	}
	f := os.NewFile(uintptr(fd), name)
	st, e := f.Stat()
	if e != nil || !st.Mode().IsRegular() || uint64(st.Sys().(*syscall.Stat_t).Dev) != d.device {
		f.Close()
		return nil, fmt.Errorf("lectura salida invalida")
	}
	return f, nil
}
func syncDir(path string) error {
	fd, e := syscall.Open(path, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if e != nil {
		return e
	}
	e = syscall.Fsync(fd)
	ce := syscall.Close(fd)
	if e != nil {
		return e
	}
	return ce
}
func (d *linuxDestination) Sync() error {
	if e := d.check(); e != nil {
		return e
	}
	return syscall.Fsync(d.fd)
}
func (d *linuxDestination) free() (uint64, error) {
	if e := d.check(); e != nil {
		return 0, e
	}
	var s syscall.Statfs_t
	if e := syscall.Fstatfs(d.fd, &s); e != nil {
		return 0, e
	}
	if s.Bsize <= 0 {
		return 0, fmt.Errorf("tamano de bloque SD invalido")
	}
	return s.Bavail * uint64(s.Bsize), nil
}
func (d *linuxDestination) json(name string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	b = append(b, '\n')
	f, e := d.CreateExclusive(name)
	if e != nil {
		return e
	}
	n, e := f.Write(b)
	if e == nil && n != len(b) {
		e = io.ErrShortWrite
	}
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e != nil {
		return e
	}
	if ce != nil {
		return ce
	}
	r, e := d.OpenRead(name)
	if e != nil {
		return e
	}
	got, e := io.ReadAll(io.LimitReader(r, int64(len(b))+1))
	ce = r.Close()
	if e != nil {
		return e
	}
	if ce != nil {
		return ce
	}
	if !reflect.DeepEqual(got, b) {
		return fmt.Errorf("relectura JSON distinta")
	}
	return d.Sync()
}
