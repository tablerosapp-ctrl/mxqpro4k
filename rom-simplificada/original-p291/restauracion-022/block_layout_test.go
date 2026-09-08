package main

import (
	"fmt"
	"strings"
	"testing"
)

// Source-shaped fixtures, not a claimed sysfs acquisition from the TV.
// Amlogic add_emmc_each_part names the child pname and assigns disk_to_dev
// as its direct parent; upstream names the equivalent child mmcblkNpN.
const fixtureDisk = "/sys/devices/platform/emmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0"

func fixtureFacts(name string, traditional bool) BlockFacts {
	p := p291Blocks[name]
	base := name
	if traditional {
		base = fmt.Sprintf("mmcblk0p%d", p.Minor)
	}
	return BlockFacts{
		PartitionPath: fixtureDisk + "/" + base, ClassDiskPath: fixtureDisk, RdevDiskPath: fixtureDisk,
		Device: uint64(179<<8) | p.Minor, ParentDevice: 179 << 8,
		IOCTLBytes: p.Bytes, ParentIOCTLBytes: p291DiskBytes,
		Dev: fmt.Sprintf("179:%d", p.Minor), Partition: fmt.Sprint(p.Minor),
		Start: "2048", Sectors: fmt.Sprint(p.Bytes / 512), ParentDev: p291DiskDev,
		ParentSectors: fmt.Sprint(p291DiskBytes / 512), ParentType: "MMC",
	}
}

func TestP291NamedAndConventionalPartitions(t *testing.T) {
	for _, name := range []string{"system", "vendor", "product", "odm", "boot", "env", "data"} {
		for _, traditional := range []bool{false, true} {
			t.Run(fmt.Sprintf("%s/traditional=%v", name, traditional), func(t *testing.T) {
				got, err := validateBlockLayout(name, fixtureFacts(name, traditional))
				if err != nil {
					t.Fatal(err)
				}
				if got.Name != name || got.ParentPath != fixtureDisk || got.Start != 2048 || got.MajorMinor != fmt.Sprintf("179:%d", p291Blocks[name].Minor) {
					t.Fatalf("incorrect observation: %+v", got)
				}
			})
		}
	}
}

func TestP291RejectsWrongBlockIdentity(t *testing.T) {
	cases := []struct {
		name   string
		change func(*BlockFacts)
	}{
		{"crossed_logical_name", func(f *BlockFacts) { f.PartitionPath = fixtureDisk + "/vendor" }},
		{"crossed_conventional_number", func(f *BlockFacts) { f.PartitionPath = fixtureDisk + "/mmcblk0p16" }},
		{"crossed_fstat_rdev", func(f *BlockFacts) { f.Device = 179<<8 | 16 }},
		{"crossed_sysfs_dev", func(f *BlockFacts) { f.Dev = "179:16" }},
		{"missing_dev", func(f *BlockFacts) { f.Dev = "" }},
		{"wrong_partition", func(f *BlockFacts) { f.Partition = "16" }},
		{"missing_partition", func(f *BlockFacts) { f.Partition = "" }},
		{"negative_partition", func(f *BlockFacts) { f.Partition = "-18" }},
		{"whole_disk", func(f *BlockFacts) { f.PartitionPath = fixtureDisk; f.Partition = "" }},
		{"boot0", func(f *BlockFacts) { f.PartitionPath = fixtureDisk + "boot0" }},
		{"rpmb", func(f *BlockFacts) { f.PartitionPath = fixtureDisk + "/mmcblk0rpmb" }},
		{"device_mapper", func(f *BlockFacts) { f.PartitionPath = "/sys/devices/virtual/block/dm-0" }},
		{"usb_ancestor", func(f *BlockFacts) {
			f.PartitionPath = strings.Replace(f.PartitionPath, "platform/emmc", "platform/usb1/1-1", 1)
		}},
		{"sd_type", func(f *BlockFacts) { f.ParentType = "SD" }},
		{"missing_type", func(f *BlockFacts) { f.ParentType = "" }},
		{"wrong_parent_fstat", func(f *BlockFacts) { f.ParentDevice = 179<<8 | 32 }},
		{"wrong_parent_dev", func(f *BlockFacts) { f.ParentDev = "179:32" }},
		{"different_class_parent", func(f *BlockFacts) { f.ClassDiskPath = fixtureDisk + "-other" }},
		{"different_rdev_parent", func(f *BlockFacts) { f.RdevDiskPath = fixtureDisk + "-other" }},
		{"nested_partition_symlink_target", func(f *BlockFacts) { f.PartitionPath = fixtureDisk + "/unexpected/system" }},
		{"canonical_path_escape", func(f *BlockFacts) { f.PartitionPath = fixtureDisk + "/../mmcblk0/system" }},
		{"non_sysfs_target", func(f *BlockFacts) { f.PartitionPath = "/tmp/block/mmcblk0/system" }},
		{"wrong_ioctl", func(f *BlockFacts) { f.IOCTLBytes -= 512 }},
		{"wrong_sysfs_size", func(f *BlockFacts) { f.Sectors = "1" }},
		{"missing_size", func(f *BlockFacts) { f.Sectors = "" }},
		{"sysfs_ioctl_scaled_wrong", func(f *BlockFacts) { f.Sectors = fmt.Sprint(f.IOCTLBytes) }},
		{"wrong_parent_ioctl", func(f *BlockFacts) { f.ParentIOCTLBytes -= 512 }},
		{"wrong_parent_sysfs_size", func(f *BlockFacts) { f.ParentSectors = "14942207" }},
		{"zero_start", func(f *BlockFacts) { f.Start = "0" }},
		{"missing_start", func(f *BlockFacts) { f.Start = "" }},
		{"negative_start", func(f *BlockFacts) { f.Start = "-1" }},
		{"start_extra_newline", func(f *BlockFacts) { f.Start = "2048\n" }},
		{"start_nul", func(f *BlockFacts) { f.Start = "2048\x00" }},
		{"end_outside_parent", func(f *BlockFacts) { f.Start = fmt.Sprint(p291DiskBytes/512 - 1) }},
		{"unsigned_interval_overflow", func(f *BlockFacts) { f.Start = "18446744073709551615" }},
		{"decimal_overflow", func(f *BlockFacts) { f.Start = "18446744073709551616" }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := fixtureFacts("system", false)
			tc.change(&f)
			if _, err := validateBlockLayout("system", f); err == nil {
				t.Fatal("accepted invalid layout")
			}
		})
	}
	if _, err := validateBlockLayout("recovery", fixtureFacts("system", false)); err == nil {
		t.Fatal("accepted unapproved target")
	}
}

func TestP291LayoutFrozenAndNonoverlapping(t *testing.T) {
	known := map[string]BlockLayout{}
	start := uint64(2048)
	// The numeric starts are artificial, chosen only to exercise seven
	// non-overlapping intervals with the real observed sizes/rdev/partno.
	for _, name := range []string{"env", "boot", "vendor", "odm", "system", "product", "data"} {
		f := fixtureFacts(name, false)
		f.Start = fmt.Sprint(start)
		layout, err := validateBlockLayout(name, f)
		if err != nil {
			t.Fatal(err)
		}
		if err = validateLayoutSet(known, layout); err != nil {
			t.Fatal(err)
		}
		known[name] = layout
		start += layout.Sectors + 2048
	}
	for _, layout := range known {
		if err := validateLayoutSet(known, layout); err != nil {
			t.Fatal(err)
		}
	}
	for _, field := range []string{"start", "canonical_path", "parent", "rdev", "size"} {
		t.Run("revalidation_"+field, func(t *testing.T) {
			changed := known["system"]
			switch field {
			case "start":
				changed.Start++
			case "canonical_path":
				changed.PartitionPath = fixtureDisk + "/mmcblk0p18"
			case "parent":
				changed.ParentPath += "-other"
			case "rdev":
				changed.Device++
			case "size":
				changed.Bytes += 512
			}
			if validateLayoutSet(known, changed) == nil {
				t.Fatal("accepted drift after preflight")
			}
		})
	}
	t.Run("overlap", func(t *testing.T) {
		other := known["vendor"]
		other.Start = known["system"].Start
		single := map[string]BlockLayout{"system": known["system"]}
		if validateLayoutSet(single, other) == nil {
			t.Fatal("accepted overlapping partitions")
		}
	})
	t.Run("same_device", func(t *testing.T) {
		other := known["vendor"]
		other.Device = known["system"].Device
		single := map[string]BlockLayout{"system": known["system"]}
		if validateLayoutSet(single, other) == nil {
			t.Fatal("accepted shared device")
		}
	})
	t.Run("different_physical_parent", func(t *testing.T) {
		other := known["vendor"]
		other.ParentPath += "-other"
		single := map[string]BlockLayout{"system": known["system"]}
		if validateLayoutSet(single, other) == nil {
			t.Fatal("accepted mixed physical parents")
		}
	})
}
