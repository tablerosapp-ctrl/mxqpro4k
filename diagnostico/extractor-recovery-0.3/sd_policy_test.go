package main

import (
	"fmt"
	"io"
	"strings"
	"testing"
)

func sdFixture() SDProof {
	p := "/sys/devices/platform/rksdmmc/mmc_host/mmc1/mmc1:0001/block/mmcblk1"
	return SDProof{
		Mount:          Mount{Device: "179:65", Root: "/", Point: SDMountPoint, FS: "vfat", Writable: true},
		PartitionSysfs: p + "/mmcblk1p1", DiskSysfs: p, DiskName: "mmcblk1", DiskDevice: "179:64",
		CardType: "SD", Removable: "1", CIDHash: strings.Repeat("a", 64), DiskBytes: SDDiskBytes,
		PartitionBytes: SDPartitionBytes, StartSector: SDStartSector, PartitionNumber: 1,
	}
}

func TestSDProofRequiresPreparedPhysicalSD(t *testing.T) {
	for _, rem := range []string{"0", "1"} {
		p := sdFixture()
		p.Removable = rem
		if e := validateSDProof(p); e != nil {
			t.Fatalf("valid SD removable=%s: %v", rem, e)
		}
	}
	cases := map[string]func(*SDProof){
		"readonly":            func(p *SDProof) { p.Mount.Writable = false; p.Mount.ReadOnly = true },
		"contradictory_ro_rw": func(p *SDProof) { p.Mount.ReadOnly = true },
		"mount_missing_rw":    func(p *SDProof) { p.Mount.Writable = false },
		"bind_mount":          func(p *SDProof) { p.Mount.Root = "/subdirectory" },
		"wrong_slot":          func(p *SDProof) { p.Mount.Point = "/mnt/usb_storage" },
		"filesystem":          func(p *SDProof) { p.Mount.FS = "fuse" },
		"internal_emmc":       func(p *SDProof) { p.CardType = "MMC" },
		"unknown_type":        func(p *SDProof) { p.CardType = "SDIO" },
		"no_cid":              func(p *SDProof) { p.CIDHash = "" },
		"invalid_removable":   func(p *SDProof) { p.Removable = "unknown" },
		"different_capacity":  func(p *SDProof) { p.DiskBytes = 7818182656 },
		"different_partition": func(p *SDProof) { p.PartitionBytes -= 512 },
		"different_offset":    func(p *SDProof) { p.StartSector = 0 },
		"different_number":    func(p *SDProof) { p.PartitionNumber = 2 },
		"virtual":             func(p *SDProof) { p.DiskSysfs = strings.Replace(p.DiskSysfs, "/platform/", "/virtual/", 1) },
		"usb":                 func(p *SDProof) { p.DiskSysfs = strings.Replace(p.DiskSysfs, "/platform/", "/usb1/", 1) },
		"child_not_direct":    func(p *SDProof) { p.PartitionSysfs = p.DiskSysfs + "/other/mmcblk1p1" },
		"non_mmc_device":      func(p *SDProof) { p.Mount.Device = "8:1" },
		"whole_disk_mount":    func(p *SDProof) { p.Mount.Device = p.DiskDevice },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			p := sdFixture()
			change(&p)
			if validateSDProof(p) == nil {
				t.Fatal("unsafe proof accepted")
			}
		})
	}
}

func TestSDSeparationFromEverySource(t *testing.T) {
	p := sdFixture()
	f := BlockFact{Name: "mmcblk0", MajorMinor: "179:0", SysPath: "/sys/devices/platform/rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0"}
	if e := separateDestination(p, []BlockFact{f}); e != nil {
		t.Fatal(e)
	}
	for name, change := range map[string]func(*BlockFact){
		"same_partition_device": func(f *BlockFact) { f.MajorMinor = p.Mount.Device },
		"same_disk_device":      func(f *BlockFact) { f.MajorMinor = p.DiskDevice },
		"same_sysfs":            func(f *BlockFact) { f.SysPath = p.DiskSysfs },
		"child_sysfs":           func(f *BlockFact) { f.SysPath = p.PartitionSysfs },
		"ancestor_sysfs":        func(f *BlockFact) { f.SysPath = strings.TrimSuffix(p.DiskSysfs, "/mmcblk1") },
	} {
		t.Run(name, func(t *testing.T) {
			g := f
			change(&g)
			if separateDestination(p, []BlockFact{g}) == nil {
				t.Fatal("overlap accepted")
			}
		})
	}
}

func TestSDPackageMustShareDestination(t *testing.T) {
	if validateSDPackage(SDPackagePath, 77, 77) != nil {
		t.Fatal("same SD rejected")
	}
	for _, tc := range []struct {
		path string
		dev  uint64
	}{{"/tmp/update.zip", 77}, {"/mnt/usb_storage/update.zip", 77}, {SDPackagePath, 88}} {
		if validateSDPackage(tc.path, tc.dev, 77) == nil {
			t.Fatal("foreign package accepted")
		}
	}
}

func TestSDExactCapacityPreflightWithoutAllocatingDevice(t *testing.T) {
	const emmcBytes int64 = 7818182656
	for _, tc := range []struct {
		name     string
		free     uint64
		boot     int64
		wantOpen bool
	}{
		{"observed_sd_free", 8033837056, 0, true},
		{"observed_sd_with_8m_boot", 8033837056, 8 << 20, true},
		{"one_byte_below_reserve", uint64(emmcBytes) + SpaceReserve - 1, 0, false},
		{"exact_reserve", uint64(emmcBytes) + SpaceReserve, 0, true},
		{"unexpected_large_boot", 8033837056, 128 << 20, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			h, _, _ := fixtureHooks(t, map[string][]byte{})
			opened := false
			h.FreeBytes = func() (uint64, error) { return tc.free, nil }
			h.OpenSource = func(Source) (io.ReadCloser, error) { opened = true; return nil, fmt.Errorf("fixture stop before IO") }
			plan := CapturePlan{Sources: []Source{{Name: "mmcblk0", Device: "/dev/block/mmcblk0", Bytes: emmcBytes, MajorMinor: "179:0", Kind: "emmc_user_area"}}}
			if tc.boot > 0 {
				plan.Sources = append(plan.Sources, Source{Name: "mmcblk0boot0", Device: "/dev/block/mmcblk0boot0", Bytes: tc.boot, MajorMinor: "179:32", Kind: "emmc_boot_area"})
			}
			r, e := Capture(plan, h)
			if e == nil || opened != tc.wantOpen || r.RequiredBytes != uint64(emmcBytes+tc.boot)+SpaceReserve {
				t.Fatalf("opened=%v require=%d error=%v", opened, r.RequiredBytes, e)
			}
		})
	}
}
