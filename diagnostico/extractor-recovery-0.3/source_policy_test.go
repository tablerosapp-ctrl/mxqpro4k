package main

import (
	"encoding/json"
	"strings"
	"testing"
)

// Independent geometry/aliases copied from the physical recovery inventory.
// No CID, APK identifiers, or arbitrary paths from that private report appear.
const recoveryCBlockFixture = `[{"name":"mmcblk0","device":"/dev/block/mmcblk0","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0","major_minor":"179:0","parent":"","kind":"emmc_user_area","bytes":7818182656,"aliases":["/dev/block/mmcblk0","/dev/block/platform/30020000.rksdmmc/mmcblk0"],"holders":[],"read_only_device":false},{"name":"mmcblk0p1","device":"/dev/block/mmcblk0p1","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p1","major_minor":"179:1","parent":"mmcblk0","kind":"partition","bytes":4194304,"start_sector":8192,"aliases":["/dev/block/mmcblk0p1","/dev/block/platform/30020000.rksdmmc/by-name/parameter","/dev/block/platform/30020000.rksdmmc/by-num/p1","/dev/block/platform/30020000.rksdmmc/mmcblk0p1"],"holders":[],"read_only_device":false},{"name":"mmcblk0p10","device":"/dev/block/mmcblk0p10","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p10","major_minor":"179:10","parent":"mmcblk0","kind":"partition","bytes":67108864,"start_sector":196608,"aliases":["/dev/block/mmcblk0p10","/dev/block/platform/30020000.rksdmmc/by-name/backup","/dev/block/platform/30020000.rksdmmc/by-num/p10","/dev/block/platform/30020000.rksdmmc/mmcblk0p10"],"holders":[],"read_only_device":false},{"name":"mmcblk0p11","device":"/dev/block/mmcblk0p11","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p11","major_minor":"179:11","parent":"mmcblk0","kind":"partition","bytes":134217728,"start_sector":327680,"aliases":["/dev/block/mmcblk0p11","/dev/block/platform/30020000.rksdmmc/by-name/cache","/dev/block/platform/30020000.rksdmmc/by-num/p11","/dev/block/platform/30020000.rksdmmc/mmcblk0p11"],"holders":[],"read_only_device":false},{"name":"mmcblk0p12","device":"/dev/block/mmcblk0p12","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p12","major_minor":"179:12","parent":"mmcblk0","kind":"partition","bytes":16777216,"start_sector":589824,"aliases":["/dev/block/mmcblk0p12","/dev/block/platform/30020000.rksdmmc/by-name/metadata","/dev/block/platform/30020000.rksdmmc/by-num/p12","/dev/block/platform/30020000.rksdmmc/mmcblk0p12"],"holders":[],"read_only_device":false},{"name":"mmcblk0p13","device":"/dev/block/mmcblk0p13","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p13","major_minor":"179:13","parent":"mmcblk0","kind":"partition","bytes":4194304,"start_sector":622592,"aliases":["/dev/block/mmcblk0p13","/dev/block/platform/30020000.rksdmmc/by-name/kpanic","/dev/block/platform/30020000.rksdmmc/by-num/p13","/dev/block/platform/30020000.rksdmmc/mmcblk0p13"],"holders":[],"read_only_device":false},{"name":"mmcblk0p14","device":"/dev/block/mmcblk0p14","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p14","major_minor":"179:14","parent":"mmcblk0","kind":"partition","bytes":2147483648,"start_sector":630784,"aliases":["/dev/block/mmcblk0p14","/dev/block/platform/30020000.rksdmmc/by-name/system","/dev/block/platform/30020000.rksdmmc/by-num/p14","/dev/block/platform/30020000.rksdmmc/mmcblk0p14"],"holders":[],"read_only_device":false},{"name":"mmcblk0p15","device":"/dev/block/mmcblk0p15","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p15","major_minor":"179:15","parent":"mmcblk0","kind":"partition","bytes":5347737600,"start_sector":4825088,"aliases":["/dev/block/mmcblk0p15","/dev/block/platform/30020000.rksdmmc/by-name/userdata","/dev/block/platform/30020000.rksdmmc/by-num/p15","/dev/block/platform/30020000.rksdmmc/mmcblk0p15"],"holders":[],"read_only_device":false},{"name":"mmcblk0p2","device":"/dev/block/mmcblk0p2","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p2","major_minor":"179:2","parent":"mmcblk0","kind":"partition","bytes":4194304,"start_sector":16384,"aliases":["/dev/block/mmcblk0p2","/dev/block/platform/30020000.rksdmmc/by-name/uboot","/dev/block/platform/30020000.rksdmmc/by-num/p2","/dev/block/platform/30020000.rksdmmc/mmcblk0p2"],"holders":[],"read_only_device":false},{"name":"mmcblk0p3","device":"/dev/block/mmcblk0p3","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p3","major_minor":"179:3","parent":"mmcblk0","kind":"partition","bytes":8388608,"start_sector":24576,"aliases":["/dev/block/mmcblk0p3","/dev/block/platform/30020000.rksdmmc/by-name/trust","/dev/block/platform/30020000.rksdmmc/by-num/p3","/dev/block/platform/30020000.rksdmmc/mmcblk0p3"],"holders":[],"read_only_device":false},{"name":"mmcblk0p4","device":"/dev/block/mmcblk0p4","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p4","major_minor":"179:4","parent":"mmcblk0","kind":"partition","bytes":4194304,"start_sector":40960,"aliases":["/dev/block/mmcblk0p4","/dev/block/platform/30020000.rksdmmc/by-name/misc","/dev/block/platform/30020000.rksdmmc/by-num/p4","/dev/block/platform/30020000.rksdmmc/mmcblk0p4"],"holders":[],"read_only_device":false},{"name":"mmcblk0p5","device":"/dev/block/mmcblk0p5","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p5","major_minor":"179:5","parent":"mmcblk0","kind":"partition","bytes":1048576,"start_sector":49152,"aliases":["/dev/block/mmcblk0p5","/dev/block/platform/30020000.rksdmmc/by-name/baseparamer","/dev/block/platform/30020000.rksdmmc/by-num/p5","/dev/block/platform/30020000.rksdmmc/mmcblk0p5"],"holders":[],"read_only_device":false},{"name":"mmcblk0p6","device":"/dev/block/mmcblk0p6","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p6","major_minor":"179:6","parent":"mmcblk0","kind":"partition","bytes":15728640,"start_sector":51200,"aliases":["/dev/block/mmcblk0p6","/dev/block/platform/30020000.rksdmmc/by-name/resource","/dev/block/platform/30020000.rksdmmc/by-num/p6","/dev/block/platform/30020000.rksdmmc/mmcblk0p6"],"holders":[],"read_only_device":false},{"name":"mmcblk0p7","device":"/dev/block/mmcblk0p7","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p7","major_minor":"179:7","parent":"mmcblk0","kind":"partition","bytes":12582912,"start_sector":81920,"aliases":["/dev/block/mmcblk0p7","/dev/block/platform/30020000.rksdmmc/by-name/kernel","/dev/block/platform/30020000.rksdmmc/by-num/p7","/dev/block/platform/30020000.rksdmmc/mmcblk0p7"],"holders":[],"read_only_device":false},{"name":"mmcblk0p8","device":"/dev/block/mmcblk0p8","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p8","major_minor":"179:8","parent":"mmcblk0","kind":"partition","bytes":12582912,"start_sector":106496,"aliases":["/dev/block/mmcblk0p8","/dev/block/platform/30020000.rksdmmc/by-name/boot","/dev/block/platform/30020000.rksdmmc/by-num/p8","/dev/block/platform/30020000.rksdmmc/mmcblk0p8"],"holders":[],"read_only_device":false},{"name":"mmcblk0p9","device":"/dev/block/mmcblk0p9","sysfs":"/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/mmcblk0p9","major_minor":"179:9","parent":"mmcblk0","kind":"partition","bytes":33554432,"start_sector":131072,"aliases":["/dev/block/mmcblk0p9","/dev/block/platform/30020000.rksdmmc/by-name/recovery","/dev/block/platform/30020000.rksdmmc/by-num/p9","/dev/block/platform/30020000.rksdmmc/mmcblk0p9"],"holders":[],"read_only_device":false}]`

func cFixture(t *testing.T) ([]BlockFact, map[string]string, string) {
	t.Helper()
	var f []BlockFact
	if e := json.Unmarshal([]byte(recoveryCBlockFixture), &f); e != nil {
		t.Fatal(e)
	}
	hash := strings.Repeat("1", 64)
	return f, map[string]string{"mmcblk0_cid_sha256": hash}, hash
}
func cFact(t *testing.T, facts []BlockFact, n string) *BlockFact {
	t.Helper()
	for i := range facts {
		if facts[i].Name == n {
			return &facts[i]
		}
	}
	t.Fatal("fixture missing " + n)
	return nil
}
func hasChosen(chosen []BlockFact, name string) bool {
	for _, f := range chosen {
		if f.Name == name {
			return true
		}
	}
	return false
}
func skipReason(skips []Skip, name string) string {
	for _, s := range skips {
		if s.Name == name {
			return s.Reason
		}
	}
	return ""
}

func TestCDefersBackupButNeverSelectsContainingDisk(t *testing.T) {
	cases := []struct {
		name   string
		mounts []Mount
		count  int
		bytes  int64
	}{
		{"cache_rw", []Mount{{Device: "179:11", Writable: true}}, 14, 7679770624},
		{"cache_ro", []Mount{{Device: "179:11", ReadOnly: true}}, 15, 7813988352},
		{"nothing_mounted", nil, 15, 7813988352},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			facts, ident, expected := cFixture(t)
			chosen, skips, e := chooseRK3229CSources(facts, c.mounts, "rockchip,rk3229", ident, expected)
			if e != nil {
				t.Fatal(e)
			}
			if len(chosen) != c.count || hasChosen(chosen, "mmcblk0") || !hasChosen(chosen, "mmcblk0p10") {
				t.Fatalf("unsafe selection %+v", chosen)
			}
			if skipReason(skips, "mmcblk0p10") != "" || !strings.Contains(skipReason(skips, "mmcblk0"), "politica de orden") {
				t.Fatalf("missing truthful omissions %+v", skips)
			}
			var size int64
			for i, f := range chosen {
				size += f.Bytes
				if i > 0 && f.Name != "mmcblk0p10" && f.Start <= chosen[i-1].Start {
					t.Fatal("not physical order")
				}
			}
			if size != c.bytes {
				t.Fatalf("bytes %d expected %d", size, c.bytes)
			}
			if chosen[len(chosen)-3].Name != "mmcblk0p14" || chosen[len(chosen)-2].Name != "mmcblk0p15" || chosen[len(chosen)-1].Name != "mmcblk0p10" {
				t.Fatal("backup must follow system/userdata and all other selected sources")
			}
		})
	}
}

func TestCRejectsUnboundWrongOrMissingIdentity(t *testing.T) {
	cases := []string{"unbound", "bad_binding", "uppercase_binding", "missing_identity", "wrong_cid", "extra_identity", "missing_dt", "other_dt"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			facts, ident, expected := cFixture(t)
			dt := "rockchip,rk3229"
			switch name {
			case "unbound":
				expected = ""
			case "bad_binding":
				expected = "wrong"
			case "uppercase_binding":
				expected = strings.Repeat("A", 64)
			case "missing_identity":
				ident = map[string]string{}
			case "wrong_cid":
				ident["mmcblk0_cid_sha256"] = strings.Repeat("2", 64)
			case "extra_identity":
				ident["mmcblk2_cid_sha256"] = expected
			case "missing_dt":
				dt = ""
			case "other_dt":
				dt = "rockchip,rk3228"
			}
			if _, _, e := chooseRK3229CSources(facts, nil, dt, ident, expected); e == nil {
				t.Fatal("accepted wrong binding")
			}
		})
	}
}

func TestCRejectsWrongMapAndAliasAmbiguity(t *testing.T) {
	cases := []string{"backup_alias_changed", "backup_alias_missing", "backup_alias_extra", "backup_alias_duplicated", "backup_size", "backup_start", "backup_path", "backup_sysfs", "backup_device", "backup_parent", "backup_kind", "system_size_android_map", "userdata_start", "parent_bytes", "parent_path", "parent_sysfs", "parent_alias", "duplicate_fact", "unknown_fact", "missing_fact", "extra_boot_area"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			facts, ident, expected := cFixture(t)
			p := cFact(t, facts, "mmcblk0p10")
			disk := cFact(t, facts, "mmcblk0")
			switch name {
			case "backup_alias_changed":
				p.Aliases[1] = strings.Replace(p.Aliases[1], "/backup", "/system", 1)
			case "backup_alias_missing":
				p.Aliases = p.Aliases[:3]
			case "backup_alias_extra":
				p.Aliases = append(p.Aliases, "/dev/block/platform/30020000.rksdmmc/by-name/other")
			case "backup_alias_duplicated":
				p.Aliases[3] = p.Aliases[1]
			case "backup_size":
				p.Bytes += 512
			case "backup_start":
				p.Start++
			case "backup_path":
				p.Path = "/dev/block/mmcblk1p10"
			case "backup_sysfs":
				p.SysPath += "/child"
			case "backup_device":
				p.MajorMinor = "179:11"
			case "backup_parent":
				p.Parent = "mmcblk1"
			case "backup_kind":
				p.Kind = "emmc_user_area"
			case "system_size_android_map":
				cFact(t, facts, "mmcblk0p14").Bytes = 5347737600
			case "userdata_start":
				cFact(t, facts, "mmcblk0p15").Start--
			case "parent_bytes":
				disk.Bytes += 512
			case "parent_path":
				disk.Path = "/dev/block/mmcblk1"
			case "parent_sysfs":
				disk.SysPath += "/nested"
			case "parent_alias":
				disk.Aliases = nil
			case "duplicate_fact":
				*p = *cFact(t, facts, "mmcblk0p1")
			case "unknown_fact":
				p.Name = "mmcblk0p99"
			case "missing_fact":
				facts = facts[:len(facts)-1]
			case "extra_boot_area":
				facts = append(facts, BlockFact{Name: "mmcblk0boot0", Kind: "emmc_boot_area", Bytes: 4194304, MajorMinor: "179:32", Parent: "mmcblk0"})
			}
			if _, _, e := chooseRK3229CSources(facts, nil, "rockchip,rk3229", ident, expected); e == nil {
				t.Fatal("accepted wrong map/alias")
			}
		})
	}
}

func TestCRetainsMountAndHolderGuards(t *testing.T) {
	cases := []string{"parent_rw", "parent_holders", "system_rw", "system_holders", "mixed_ro_bind"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			facts, ident, expected := cFixture(t)
			var mounts []Mount
			switch name {
			case "parent_rw":
				mounts = []Mount{{Device: "179:0", Writable: true}}
			case "parent_holders":
				cFact(t, facts, "mmcblk0").Holders = []string{"dm-0"}
			case "system_rw":
				mounts = []Mount{{Device: "179:14", Writable: true}}
			case "system_holders":
				cFact(t, facts, "mmcblk0p14").Holders = []string{"dm-0"}
			case "mixed_ro_bind":
				mounts = []Mount{{Device: "179:14", ReadOnly: false, Writable: false}}
			}
			chosen, skips, e := chooseRK3229CSources(facts, mounts, "rockchip,rk3229", ident, expected)
			if e != nil {
				t.Fatal(e)
			}
			if hasChosen(chosen, "mmcblk0") || hasChosen(chosen, "mmcblk0p14") {
				t.Fatal("busy source selected")
			}
			if strings.HasPrefix(name, "parent_") && len(chosen) != 0 {
				t.Fatal("busy parent leaked partitions")
			}
			if strings.HasPrefix(name, "parent_") {
				if skipReason(skips, "mmcblk0p10") == "" {
					t.Fatal("busy parent must omit backup too")
				}
			} else if !hasChosen(chosen, "mmcblk0p10") {
				t.Fatal("backup must be tried when stable")
			}
		})
	}
}

func TestCSelectionIndependentOfInventoryAndAliasOrder(t *testing.T) {
	facts, ident, expected := cFixture(t)
	for left, right := 0, len(facts)-1; left < right; left, right = left+1, right-1 {
		facts[left], facts[right] = facts[right], facts[left]
	}
	for i := range facts {
		a := facts[i].Aliases
		for left, right := 0, len(a)-1; left < right; left, right = left+1, right-1 {
			a[left], a[right] = a[right], a[left]
		}
	}
	chosen, _, e := chooseRK3229CSources(facts, nil, "rockchip,rk3229", ident, expected)
	if e != nil || len(chosen) != 15 {
		t.Fatalf("%+v %v", chosen, e)
	}
	if chosen[0].Name != "mmcblk0p1" || chosen[14].Name != "mmcblk0p10" {
		t.Fatal("unexpected source order")
	}
}

func TestCPolicyProofHasExplicitCoverage(t *testing.T) {
	p := rk3229CPolicyProof()
	if p.ID != "rk3229-c-backup-last-1" || !p.ExpectedIdentityBound || p.WholeUserAreaAllowed || p.DeferredSource != "mmcblk0p10" || p.Reason != "observed_source_changed_during_reread" {
		t.Fatalf("%+v", p)
	}
	b, e := json.Marshal(p)
	if e != nil || strings.Contains(string(b), strings.Repeat("1", 64)) {
		t.Fatal("private binding leaked into policy proof")
	}
}

func TestCDoesNotReadBackupWhenMountedRWOrHeld(t *testing.T) {
	for _, held := range []bool{false, true} {
		facts, ident, expected := cFixture(t)
		var mounts []Mount
		if held {
			cFact(t, facts, "mmcblk0p10").Holders = []string{"dm-0"}
		} else {
			mounts = []Mount{{Device: "179:10", Writable: true}}
		}
		chosen, skips, e := chooseRK3229CSources(facts, mounts, "rockchip,rk3229", ident, expected)
		if e != nil || hasChosen(chosen, "mmcblk0p10") || hasChosen(chosen, "mmcblk0") || skipReason(skips, "mmcblk0p10") == "" {
			t.Fatalf("%+v %+v %v", chosen, skips, e)
		}
	}
}
