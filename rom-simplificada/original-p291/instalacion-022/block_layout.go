package main

import (
	"fmt"
	"path"
	"regexp"
	"strconv"
	"strings"
)

const p291DiskBytes uint64 = 7650410496
const p291DiskDev = "179:0"

type blockProfile struct {
	Bytes uint64
	Minor uint64
}

var p291Blocks = map[string]blockProfile{
	"system": {1342177280, 18}, "vendor": {943718400, 16},
	"product": {134217728, 19}, "odm": {134217728, 17},
	"boot": {16777216, 11}, "env": {8388608, 4}, "data": {3495952384, 20},
}

// Paths are canonical POSIX sysfs paths, even when fixtures run on Windows.
// Start offsets were not captured originally: check bounds/non-overlap and
// freeze the first observed layout for all subsequent pre-write checks.
type BlockFacts struct {
	PartitionPath, ClassDiskPath, RdevDiskPath string
	Device, ParentDevice                       uint64
	IOCTLBytes, ParentIOCTLBytes               uint64
	Dev, Partition, Start, Sectors             string
	ParentDev, ParentSectors, ParentType       string
}

type BlockLayout struct {
	Name, PartitionPath, ParentPath, DiskName, MajorMinor string
	Device, ParentDevice, Bytes, ParentBytes              uint64
	Partition, Start, Sectors                             uint64
}

func deviceNumber(r uint64) string {
	major := (r>>8)&0xfff | (r>>32)&0xfffff000
	minor := r&255 | (r>>12)&0xffffff00
	return fmt.Sprintf("%d:%d", major, minor)
}

func decimalAttribute(label, raw string) (uint64, error) {
	if raw == "" {
		return 0, fmt.Errorf("sysfs %s ausente o vacio", label)
	}
	for _, c := range raw {
		if c < '0' || c > '9' {
			return 0, fmt.Errorf("sysfs %s no decimal: %q", label, raw)
		}
	}
	n, err := strconv.ParseUint(raw, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("sysfs %s fuera de rango: %w", label, err)
	}
	return n, nil
}

func physicalSysfsPath(p string) bool {
	if p != path.Clean(p) || !strings.HasPrefix(p, "/sys/devices/") || strings.Contains(p, "\\") {
		return false
	}
	for _, part := range strings.Split(p, "/") {
		if part == "virtual" || strings.HasPrefix(strings.ToLower(part), "usb") {
			return false
		}
	}
	return true
}

var diskNamePattern = regexp.MustCompile(`^mmcblk[0-9]+$`)

func validateBlockLayout(name string, f BlockFacts) (BlockLayout, error) {
	reject := func(format string, args ...any) (BlockLayout, error) {
		return BlockLayout{}, fmt.Errorf("particion %s: %s", name, fmt.Sprintf(format, args...))
	}
	expected, ok := p291Blocks[name]
	if !ok {
		return reject("nombre no autorizado")
	}
	expectedDev := fmt.Sprintf("179:%d", expected.Minor)
	if deviceNumber(f.Device) != expectedDev || f.Dev != expectedDev {
		return reject("dev fstat/sysfs=%s/%q; esperado %s", deviceNumber(f.Device), f.Dev, expectedDev)
	}
	if f.IOCTLBytes != expected.Bytes {
		return reject("ioctl bytes=%d; esperado %d", f.IOCTLBytes, expected.Bytes)
	}
	if !physicalSysfsPath(f.PartitionPath) {
		return reject("ruta sysfs no fisica/canonica: %q", f.PartitionPath)
	}
	parent := path.Dir(f.PartitionPath)
	disk := path.Base(parent)
	if !diskNamePattern.MatchString(disk) || path.Base(path.Dir(parent)) != "block" {
		return reject("padre no es disco eMMC: %q", parent)
	}
	if f.ClassDiskPath != parent || f.RdevDiskPath != parent {
		return reject("padre no coincide con /sys/class/block/%s y /sys/dev/block/%s", disk, p291DiskDev)
	}
	if deviceNumber(f.ParentDevice) != p291DiskDev || f.ParentDev != p291DiskDev {
		return reject("dev del padre=%s/%q; esperado %s", deviceNumber(f.ParentDevice), f.ParentDev, p291DiskDev)
	}
	if f.ParentType != "MMC" {
		return reject("device/type del padre=%q; esperado MMC", f.ParentType)
	}
	if f.ParentIOCTLBytes != p291DiskBytes {
		return reject("ioctl del disco=%d; esperado %d", f.ParentIOCTLBytes, p291DiskBytes)
	}
	partno, err := decimalAttribute("partition", f.Partition)
	if err != nil {
		return reject("%v", err)
	}
	if partno != expected.Minor {
		return reject("partition=%d; esperado %d", partno, expected.Minor)
	}
	base := path.Base(f.PartitionPath)
	conventional := fmt.Sprintf("%sp%d", disk, partno)
	if base != name && base != conventional {
		return reject("nombre sysfs=%q; esperado %q o %q", base, name, conventional)
	}
	start, err := decimalAttribute("start", f.Start)
	if err != nil {
		return reject("%v", err)
	}
	sectors, err := decimalAttribute("size", f.Sectors)
	if err != nil {
		return reject("%v", err)
	}
	parentSectors, err := decimalAttribute("parent/size", f.ParentSectors)
	if err != nil {
		return reject("%v", err)
	}
	if sectors != expected.Bytes/512 || expected.Bytes%512 != 0 {
		return reject("size sysfs=%d sectores; esperado %d", sectors, expected.Bytes/512)
	}
	if parentSectors != p291DiskBytes/512 {
		return reject("size sysfs del padre=%d; esperado %d", parentSectors, p291DiskBytes/512)
	}
	// Subtraction avoids overflow for deliberately malformed unsigned values.
	if start == 0 || start >= parentSectors || sectors > parentSectors-start {
		return reject("intervalo start=%d size=%d fuera del disco", start, sectors)
	}
	return BlockLayout{Name: name, PartitionPath: f.PartitionPath, ParentPath: parent,
		DiskName: disk, MajorMinor: expectedDev, Device: f.Device, ParentDevice: f.ParentDevice,
		Bytes: f.IOCTLBytes, ParentBytes: f.ParentIOCTLBytes, Partition: partno, Start: start, Sectors: sectors}, nil
}

func validateLayoutSet(existing map[string]BlockLayout, next BlockLayout) error {
	if previous, ok := existing[next.Name]; ok && previous != next {
		return fmt.Errorf("cambio la identidad/geometria observada de %s (start anterior %d, actual %d)", next.Name, previous.Start, next.Start)
	}
	for name, previous := range existing {
		if name == next.Name {
			continue
		}
		if previous.ParentPath != next.ParentPath || previous.ParentDevice != next.ParentDevice || previous.ParentBytes != next.ParentBytes {
			return fmt.Errorf("%s/%s no pertenecen al mismo padre eMMC", name, next.Name)
		}
		if previous.Device == next.Device {
			return fmt.Errorf("%s/%s comparten dispositivo", name, next.Name)
		}
		if next.Start < previous.Start+previous.Sectors && previous.Start < next.Start+next.Sectors {
			return fmt.Errorf("intervalos superpuestos: %s/%s", name, next.Name)
		}
	}
	return nil
}
