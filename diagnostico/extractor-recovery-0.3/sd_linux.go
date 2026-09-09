//go:build linux

package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"syscall"
)

type sdTarget struct {
	Proof        SDProof
	Root         string
	Dev          uint64
	Marker       []byte
	PackageInode uint64
	PackageBytes int64
}

func readSDProof(m Mount) (SDProof, error) {
	p := SDProof{Mount: m}
	// Report mount mode before probing sysfs, so a RO SD fails explicitly.
	if m.Point != SDMountPoint || m.Root != "/" {
		return p, fmt.Errorf("SD: montaje esperado ausente")
	}
	if !m.Writable || m.ReadOnly {
		return p, fmt.Errorf("SD: montaje de recovery es RO; no se remonta automaticamente")
	}
	if m.FS != "vfat" {
		return p, fmt.Errorf("SD: filesystem %q no es vfat", m.FS)
	}
	sys, e := filepath.EvalSymlinks("/sys/dev/block/" + m.Device)
	if e != nil {
		return p, fmt.Errorf("SD: sysfs del volumen no accesible: %w", e)
	}
	p.PartitionSysfs = sys
	p.DiskSysfs = filepath.Dir(sys)
	p.DiskName = filepath.Base(p.DiskSysfs)
	if !strings.HasPrefix(p.DiskSysfs, "/sys/devices/") || !sdDiskName.MatchString(p.DiskName) {
		return p, fmt.Errorf("SD: padre no es mmcblk fisico")
	}
	device, e := attr(filepath.Join(sys, "dev"))
	if e != nil || device != m.Device {
		return p, fmt.Errorf("SD: st_dev/mount y sysfs diferentes")
	}
	if p.DiskDevice, e = attr(filepath.Join(p.DiskSysfs, "dev")); e != nil {
		return p, e
	}
	if p.PartitionNumber, e = numAttr(filepath.Join(sys, "partition")); e != nil {
		return p, fmt.Errorf("SD: falta numero de particion: %w", e)
	}
	if p.StartSector, e = numAttr(filepath.Join(sys, "start")); e != nil {
		return p, e
	}
	sectors, e := numAttr(filepath.Join(sys, "size"))
	if e != nil || sectors <= 0 || sectors > (1<<40)/512 {
		return p, fmt.Errorf("SD: tamano particion sysfs invalido")
	}
	p.PartitionBytes = sectors * 512
	sectors, e = numAttr(filepath.Join(p.DiskSysfs, "size"))
	if e != nil || sectors <= 0 || sectors > (1<<40)/512 {
		return p, fmt.Errorf("SD: tamano padre sysfs invalido")
	}
	p.DiskBytes = sectors * 512
	card, e := filepath.EvalSymlinks(filepath.Join(p.DiskSysfs, "device"))
	if e != nil || !strings.HasPrefix(card, "/sys/devices/") || !strings.HasPrefix(p.DiskSysfs, card+"/") {
		return p, fmt.Errorf("SD: relacion tarjeta/disco no verificable")
	}
	if p.CardType, e = attr(filepath.Join(card, "type")); e != nil {
		return p, fmt.Errorf("SD: tipo de tarjeta no legible")
	}
	if p.Removable, e = attr(filepath.Join(p.DiskSysfs, "removable")); e != nil {
		return p, e
	}
	cid, e := attr(filepath.Join(card, "cid"))
	if e != nil || len(cid) != 32 {
		return p, fmt.Errorf("SD: CID no verificable")
	}
	if _, e = hex.DecodeString(cid); e != nil {
		return p, fmt.Errorf("SD: CID invalido")
	}
	h := sha256.Sum256([]byte(cid))
	p.CIDHash = hex.EncodeToString(h[:])
	if e = validateSDProof(p); e != nil {
		return p, e
	}
	for _, path := range []string{sys, p.DiskSysfs} {
		ro, e := attr(filepath.Join(path, "ro"))
		if e != nil || ro != "0" {
			return p, fmt.Errorf("SD: tarjeta o particion protegida contra escritura")
		}
	}
	// Read-only opens validate the actual kernel sizes; never write raw SD.
	for _, b := range []struct {
		name, dev string
		size      int64
	}{
		{filepath.Base(sys), m.Device, p.PartitionBytes}, {p.DiskName, p.DiskDevice, p.DiskBytes},
	} {
		var node string
		for _, candidate := range []string{"/dev/block/" + b.name, "/dev/" + b.name} {
			st, e := os.Stat(candidate)
			if e == nil && st.Mode()&os.ModeDevice != 0 && st.Mode()&os.ModeCharDevice == 0 && mm(uint64(st.Sys().(*syscall.Stat_t).Rdev)) == b.dev {
				node = candidate
				break
			}
		}
		if node == "" {
			return p, fmt.Errorf("SD: nodo %s no accesible", b.name)
		}
		file, e := openBlock(node, b.dev, b.size)
		if e != nil {
			return p, fmt.Errorf("SD: ioctl/tamano de %s: %w", b.name, e)
		}
		if e = file.Close(); e != nil {
			return p, e
		}
	}
	st, e := ordinary(m.Point, true)
	if e != nil {
		return p, fmt.Errorf("SD: directorio del montaje: %w", e)
	}
	if mm(uint64(st.Sys().(*syscall.Stat_t).Dev)) != m.Device {
		return p, fmt.Errorf("SD: directorio cambio de dispositivo")
	}
	return p, nil
}

func findSD() (sdTarget, error) {
	ms, e := currentMounts()
	if e != nil {
		return sdTarget{}, e
	}
	var candidates []Mount
	for _, m := range ms {
		if m.Point == SDMountPoint {
			candidates = append(candidates, m)
		}
	}
	if len(candidates) != 1 {
		return sdTarget{}, fmt.Errorf("SD: se requiere un montaje en /mnt/external_sd; encontrados %d", len(candidates))
	}
	p, e := readSDProof(candidates[0])
	if e != nil {
		return sdTarget{}, e
	}
	root := filepath.Join(SDMountPoint, "TVBASE-EXTRACCION")
	st, e := ordinary(root, true)
	if e != nil {
		return sdTarget{}, fmt.Errorf("SD: falta carpeta TVBASE-EXTRACCION preparada: %w", e)
	}
	mp := filepath.Join(root, "MEDIA.json")
	if _, e = ordinary(mp, false); e != nil {
		return sdTarget{}, fmt.Errorf("SD: falta MEDIA.json preparado")
	}
	b, e := bounded(mp, 4096)
	if e != nil {
		return sdTarget{}, e
	}
	var marker Media
	if strictJSON(b, &marker) != nil || marker.Schema != "tvbase-recovery-media-1" || marker.MediaID != SDMediaID {
		return sdTarget{}, fmt.Errorf("SD: marcador no corresponde a esta entrega RK3229-C")
	}
	dev := uint64(st.Sys().(*syscall.Stat_t).Dev)
	if mm(dev) != p.Mount.Device {
		return sdTarget{}, fmt.Errorf("SD: carpeta preparada fuera de la tarjeta")
	}
	if len(os.Args) != 4 || os.Args[3] != SDPackagePath {
		return sdTarget{}, fmt.Errorf("SD: paquete debe ejecutarse desde /mnt/external_sd/update.zip")
	}
	pkg, e := ordinary(SDPackagePath, false)
	if e != nil {
		return sdTarget{}, fmt.Errorf("SD: paquete no verificable: %w", e)
	}
	if e = validateSDPackage(os.Args[3], uint64(pkg.Sys().(*syscall.Stat_t).Dev), dev); e != nil {
		return sdTarget{}, e
	}
	return sdTarget{Proof: p, Root: root, Dev: dev, Marker: b, PackageInode: uint64(pkg.Sys().(*syscall.Stat_t).Ino), PackageBytes: pkg.Size()}, nil
}

func (u sdTarget) verify() error {
	ms, e := currentMounts()
	if e != nil {
		return e
	}
	var match []Mount
	for _, m := range ms {
		if m.Point == SDMountPoint {
			match = append(match, m)
		}
	}
	if len(match) != 1 {
		return fmt.Errorf("SD: montaje desaparecio o cambio")
	}
	p, e := readSDProof(match[0])
	if e != nil {
		return e
	}
	if !reflect.DeepEqual(p, u.Proof) {
		return fmt.Errorf("SD: identidad, geometria o montaje cambio")
	}
	st, e := ordinary(u.Root, true)
	if e != nil || uint64(st.Sys().(*syscall.Stat_t).Dev) != u.Dev {
		return fmt.Errorf("SD: destino preparado cambio")
	}
	mp := filepath.Join(u.Root, "MEDIA.json")
	if _, e = ordinary(mp, false); e != nil {
		return e
	}
	b, e := bounded(mp, 4096)
	if e != nil || !bytes.Equal(b, u.Marker) {
		return fmt.Errorf("SD: marcador cambio")
	}
	pkg, e := ordinary(SDPackagePath, false)
	if e != nil || uint64(pkg.Sys().(*syscall.Stat_t).Dev) != u.Dev || uint64(pkg.Sys().(*syscall.Stat_t).Ino) != u.PackageInode || pkg.Size() != u.PackageBytes {
		return fmt.Errorf("SD: paquete cambio de tarjeta/archivo")
	}
	return nil
}
