package main

import (
	"fmt"
	"regexp"
	"strings"
)

const (
	SDMountPoint           = "/mnt/external_sd"
	SDPackagePath          = SDMountPoint + "/update.zip"
	SDMediaID              = "tvbase-recovery-sd-rk3229-c-20260909"
	SDDiskBytes      int64 = 8053063680
	SDPartitionBytes int64 = 8052015104
	SDStartSector    int64 = 2048
)

var sdDiskName = regexp.MustCompile(`^mmcblk[0-9]+$`)
var sdCIDHash = regexp.MustCompile(`^[0-9a-f]{64}$`)
var sdHostPath = regexp.MustCompile(`/mmc_host/mmc[0-9]+/mmc[0-9]+:[0-9a-fA-F]+/block/`)

// SDProof is derived afresh from mountinfo, sysfs, stat and read-only ioctl.
// Windows reader identity is not a Linux SD CID; no CID is guessed from it.
type SDProof struct {
	Mount           Mount  `json:"mount"`
	PartitionSysfs  string `json:"partition_sysfs"`
	DiskSysfs       string `json:"disk_sysfs"`
	DiskName        string `json:"disk_name"`
	DiskDevice      string `json:"disk_device"`
	CardType        string `json:"card_type"`
	Removable       string `json:"removable"`
	CIDHash         string `json:"cid_sha256"`
	DiskBytes       int64  `json:"disk_bytes"`
	PartitionBytes  int64  `json:"partition_bytes"`
	StartSector     int64  `json:"start_sector"`
	PartitionNumber int64  `json:"partition_number"`
}

// This release is intentionally tied to the prepared SD geometry and CNV8b
// package mount point. It is not a generic removable-media fallback.
func validateSDProof(p SDProof) error {
	if p.Mount.Point != SDMountPoint || p.Mount.Root != "/" {
		return fmt.Errorf("SD: no es montaje raiz /mnt/external_sd")
	}
	if !p.Mount.Writable || p.Mount.ReadOnly {
		return fmt.Errorf("SD: recovery la monto solo lectura; se requiere RW sin remontar")
	}
	if p.Mount.FS != "vfat" {
		return fmt.Errorf("SD: filesystem %q, se requiere FAT32/vfat", p.Mount.FS)
	}
	major, _, e := parseMM(p.Mount.Device)
	diskMajor, _, de := parseMM(p.DiskDevice)
	if e != nil || de != nil || major != 179 || diskMajor != 179 || p.Mount.Device == p.DiskDevice {
		return fmt.Errorf("SD: dispositivo y padre MMC no verificables")
	}
	if !sdDiskName.MatchString(p.DiskName) || !strings.HasPrefix(p.DiskSysfs, "/sys/devices/") ||
		!strings.HasSuffix(p.DiskSysfs, "/block/"+p.DiskName) || !sdHostPath.MatchString(p.DiskSysfs) ||
		strings.Contains(p.DiskSysfs, "/virtual/") || strings.Contains(p.DiskSysfs, "/usb") ||
		p.PartitionSysfs != p.DiskSysfs+"/"+p.DiskName+"p1" {
		return fmt.Errorf("SD: particion no es hija directa de una tarjeta fisica MMC")
	}
	if p.CardType != "SD" {
		return fmt.Errorf("SD: type=%q; se requiere SD, nunca eMMC interna", p.CardType)
	}
	// type SD is the discriminator. Some controllers report removable=0 even
	// for their SD slot; this flag is checked and recorded, not used as proof.
	if p.Removable != "0" && p.Removable != "1" || !sdCIDHash.MatchString(p.CIDHash) {
		return fmt.Errorf("SD: identidad CID/removable no verificable")
	}
	if p.DiskBytes != SDDiskBytes || p.PartitionBytes != SDPartitionBytes ||
		p.StartSector != SDStartSector || p.PartitionNumber != 1 {
		return fmt.Errorf("SD: geometria distinta (disco %d, particion %d, inicio %d)", p.DiskBytes, p.PartitionBytes, p.StartSector)
	}
	return nil
}

func separateDestination(p SDProof, facts []BlockFact) error {
	if e := validateSDProof(p); e != nil {
		return e
	}
	for _, f := range facts {
		if f.MajorMinor == p.Mount.Device || f.MajorMinor == p.DiskDevice ||
			f.SysPath == p.DiskSysfs || strings.HasPrefix(f.SysPath, p.DiskSysfs+"/") ||
			strings.HasPrefix(p.DiskSysfs, f.SysPath+"/") {
			return fmt.Errorf("SD: destino y origen no son independientes: %s", f.Name)
		}
	}
	return nil
}

func validateSDPackage(path string, packageDevice, targetDevice uint64) error {
	if path != SDPackagePath || packageDevice != targetDevice {
		return fmt.Errorf("SD: paquete debe pertenecer a la misma tarjeta en /mnt/external_sd/update.zip")
	}
	return nil
}
