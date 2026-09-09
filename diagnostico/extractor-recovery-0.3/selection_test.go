package main

import "testing"

func TestMountParsing(t *testing.T) {
	m, e := parseMounts([]byte("29 0 179:1 / /system ro,relatime - ext4 /dev/block/system ro\n30 0 8:1 / /usb\\040drive rw - vfat /dev/sda1 rw\n"))
	if e != nil || len(m) != 2 || !m[0].ReadOnly || m[1].Point != "/usb drive" {
		t.Fatalf("%+v %v", m, e)
	}
	m, e = parseMounts([]byte("29 0 179:1 / /system ro - ext4 /dev/system rw\n"))
	if e != nil || m[0].ReadOnly {
		t.Fatal("bind RO no es superblock RO")
	}
	for _, s := range []string{"bad", "29 0 179:1 / /bad\\0zz ro - ext4 /dev/system ro", ""} {
		if _, e := parseMounts([]byte(s)); e == nil {
			t.Fatal(s)
		}
	}
}
func testFacts() []BlockFact {
	return []BlockFact{{Name: "mmcblk0", MajorMinor: "179:0", Kind: "emmc_user_area", Bytes: 8192}, {Name: "system", MajorMinor: "179:1", Parent: "mmcblk0", Kind: "partition", Start: 1, Bytes: 2048}, {Name: "cache", MajorMinor: "179:2", Parent: "mmcblk0", Kind: "partition", Start: 5, Bytes: 2048}, {Name: "mmcblk0boot0", MajorMinor: "179:32", Parent: "mmcblk0", Kind: "emmc_boot_area", Bytes: 2048}}
}
func TestWholeAndPartialSelection(t *testing.T) {
	f := testFacts()
	s, k, e := chooseSources(f, nil)
	if e != nil || len(s) != 2 || len(k) != 0 {
		t.Fatalf("%+v %+v %v", s, k, e)
	}
	s, k, e = chooseSources(f, []Mount{{Device: "179:2", ReadOnly: false}})
	if e != nil || len(s) != 2 || len(k) != 2 {
		t.Fatalf("%+v %+v %v", s, k, e)
	}
	for _, v := range s {
		if v.Name == "cache" || v.Name == "mmcblk0" {
			t.Fatal(v)
		}
	}
}
func TestHoldersAndOverlap(t *testing.T) {
	f := testFacts()
	f[1].Holders = []string{"dm-0"}
	s, _, e := chooseSources(f, nil)
	if e != nil {
		t.Fatal(e)
	}
	for _, v := range s {
		if v.Name == "mmcblk0" || v.Name == "system" {
			t.Fatal(v)
		}
	}
	f = testFacts()
	f[2].Start = 2
	if _, _, e := chooseSources(f, nil); e == nil {
		t.Fatal("overlap")
	}
	f = testFacts()
	f[1].Bytes = 1 << 41
	if _, _, e := chooseSources(f, nil); e == nil {
		t.Fatal("size")
	}
}
func TestBusyParentBlocksChildren(t *testing.T) {
	for _, holders := range []bool{false, true} {
		f := testFacts()
		var mounts []Mount
		if holders {
			f[0].Holders = []string{"dm-0"}
		} else {
			mounts = []Mount{{Device: "179:0", ReadOnly: false}}
		}
		s, _, e := chooseSources(f, mounts)
		if e != nil {
			t.Fatal(e)
		}
		for _, v := range s {
			if v.Kind != "emmc_boot_area" {
				t.Fatalf("busy parent leaked %s", v.Name)
			}
		}
	}
}
func TestWritableRequiresBothFlags(t *testing.T) {
	for _, opts := range []string{"ro - vfat /dev/sda1 rw", "rw - vfat /dev/sda1 ro"} {
		m, e := parseMounts([]byte("1 0 8:1 / /usb " + opts))
		if e != nil || m[0].Writable || m[0].ReadOnly {
			t.Fatalf("%+v %v", m, e)
		}
	}
}
