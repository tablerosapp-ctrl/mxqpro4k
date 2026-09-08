//go:build linux

package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
	"unsafe"
)

var observedLayouts = map[string]BlockLayout{}
var observedPaths = map[string]string{}

func blockNode(path string) (size, rdev uint64, result error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, 0, fmt.Errorf("abrir bloques %s solo lectura: %w", path, err)
	}
	defer func() {
		if err := f.Close(); result == nil {
			result = err
		}
	}()
	st, err := f.Stat()
	if err != nil {
		return 0, 0, err
	}
	if st.Mode()&os.ModeDevice == 0 || st.Mode()&os.ModeCharDevice != 0 {
		return 0, 0, fmt.Errorf("no es dispositivo de bloques: %s", path)
	}
	rdev = uint64(st.Sys().(*syscall.Stat_t).Rdev)
	_, _, errno := syscall.Syscall(syscall.SYS_IOCTL, f.Fd(), blockSizeIOCTL(unsafe.Sizeof(uintptr(0))), uintptr(unsafe.Pointer(&size)))
	if errno != 0 {
		return 0, 0, fmt.Errorf("ioctl tamano %s: %w", path, errno)
	}
	return size, rdev, nil
}

// Read attributes only after resolving the kernel-owned device directories.
// Ordinary class/rdev/device links are expected; individual attributes may not
// be redirected through symlinks. Never turn a failed read into a zero value.
func blockAttribute(path string) (value string, result error) {
	canonical, err := filepath.EvalSymlinks(path)
	if err != nil {
		return "", fmt.Errorf("resolver atributo %s: %w", path, err)
	}
	if canonical != filepath.Clean(path) {
		return "", fmt.Errorf("atributo sysfs redirigido: %s -> %s", path, canonical)
	}
	st, err := os.Lstat(path)
	if err != nil || !st.Mode().IsRegular() {
		return "", fmt.Errorf("atributo sysfs ausente/no regular %s: %v", path, err)
	}
	f, err := os.Open(path)
	if err != nil {
		return "", fmt.Errorf("leer atributo %s: %w", path, err)
	}
	defer func() {
		if err := f.Close(); result == nil {
			result = err
		}
	}()
	raw, err := io.ReadAll(io.LimitReader(f, 257))
	if err != nil {
		return "", fmt.Errorf("leer atributo %s: %w", path, err)
	}
	if len(raw) == 0 || len(raw) > 256 || strings.ContainsAny(string(raw), "\x00\r") {
		return "", fmt.Errorf("atributo sysfs vacio/excesivo/invalido: %s", path)
	}
	value = strings.TrimSuffix(string(raw), "\n")
	if strings.Contains(value, "\n") {
		return "", fmt.Errorf("atributo sysfs multilinea: %s", path)
	}
	return value, nil
}

func inspectBlock(path, name string) (BlockLayout, error) {
	f := BlockFacts{}
	var err error
	if f.IOCTLBytes, f.Device, err = blockNode(path); err != nil {
		return BlockLayout{}, err
	}
	if f.PartitionPath, err = filepath.EvalSymlinks("/sys/dev/block/" + deviceNumber(f.Device)); err != nil {
		return BlockLayout{}, fmt.Errorf("%s: resolver sysfs rdev: %w", name, err)
	}
	parent := filepath.Dir(f.PartitionPath)
	disk := filepath.Base(parent)
	if !diskNamePattern.MatchString(disk) {
		return BlockLayout{}, fmt.Errorf("%s: padre sysfs no eMMC: %s", name, parent)
	}
	if f.ClassDiskPath, err = filepath.EvalSymlinks("/sys/class/block/" + disk); err != nil {
		return BlockLayout{}, fmt.Errorf("%s: resolver clase del disco: %w", name, err)
	}
	if f.RdevDiskPath, err = filepath.EvalSymlinks("/sys/dev/block/" + p291DiskDev); err != nil {
		return BlockLayout{}, fmt.Errorf("%s: resolver rdev del disco: %w", name, err)
	}
	if f.ParentIOCTLBytes, f.ParentDevice, err = blockNode("/dev/block/" + disk); err != nil {
		return BlockLayout{}, err
	}
	devicePath, err := filepath.EvalSymlinks(filepath.Join(parent, "device"))
	if err != nil || !physicalSysfsPath(devicePath) {
		return BlockLayout{}, fmt.Errorf("%s: device del disco no fisico: %q (%v)", name, devicePath, err)
	}
	for _, item := range []struct {
		path string
		out  *string
	}{
		{filepath.Join(f.PartitionPath, "dev"), &f.Dev},
		{filepath.Join(f.PartitionPath, "partition"), &f.Partition},
		{filepath.Join(f.PartitionPath, "start"), &f.Start},
		{filepath.Join(f.PartitionPath, "size"), &f.Sectors},
		{filepath.Join(parent, "dev"), &f.ParentDev},
		{filepath.Join(parent, "size"), &f.ParentSectors},
		{filepath.Join(devicePath, "type"), &f.ParentType},
	} {
		if *item.out, err = blockAttribute(item.path); err != nil {
			return BlockLayout{}, fmt.Errorf("validando %s: %w", name, err)
		}
	}
	layout, err := validateBlockLayout(name, f)
	if err != nil {
		return BlockLayout{}, err
	}
	if err = validateLayoutSet(observedLayouts, layout); err != nil {
		return BlockLayout{}, err
	}
	observedLayouts[name] = layout
	observedPaths[name] = path
	return layout, nil
}

func revalidateBlockLayouts(phase string) error {
	names := make([]string, 0, len(observedPaths))
	for name := range observedPaths {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		if _, err := inspectBlock(observedPaths[name], name); err != nil {
			return fmt.Errorf("%s, revalidando layout %s: %w", phase, name, err)
		}
	}
	return nil
}
