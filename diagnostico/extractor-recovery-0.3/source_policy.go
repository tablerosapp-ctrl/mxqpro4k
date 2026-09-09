package main

import (
	"fmt"
	"sort"
)

// Supplied only by the private build using -X main.rk3229CExpectedCID=<sha256>.
// An unbound build refuses extraction. Never commit a physical device identity.
var rk3229CExpectedCID = ""

const (
	RK3229CPolicyID      = "rk3229-c-backup-last-1"
	rk3229CSysfs         = "/sys/devices/30020000.rksdmmc/mmc_host/mmc0/mmc0:0001/block/mmcblk0"
	rk3229CBlockPlatform = "/dev/block/platform/30020000.rksdmmc/"
)

type SourcePolicyProof struct {
	ID                    string `json:"id"`
	ExpectedIdentityBound bool   `json:"expected_identity_bound"`
	DeferredSource        string `json:"deferred_source"`
	Reason                string `json:"reason"`
	WholeUserAreaAllowed  bool   `json:"whole_user_area_allowed"`
}

func rk3229CPolicyProof() SourcePolicyProof {
	return SourcePolicyProof{RK3229CPolicyID, true, "mmcblk0p10", "observed_source_changed_during_reread", false}
}

type rk3229CPartition struct {
	Alias        string
	Start, Bytes int64
}

// This is the recovery map physically read in the failed 0.2 capture, not the
// different Android map. p1 is parameter; system/userdata are p14/p15.
var rk3229CPartitions = []rk3229CPartition{
	{"parameter", 8192, 4194304},
	{"uboot", 16384, 4194304},
	{"trust", 24576, 8388608},
	{"misc", 40960, 4194304},
	{"baseparamer", 49152, 1048576},
	{"resource", 51200, 15728640},
	{"kernel", 81920, 12582912},
	{"boot", 106496, 12582912},
	{"recovery", 131072, 33554432},
	{"backup", 196608, 67108864},
	{"cache", 327680, 134217728},
	{"metadata", 589824, 16777216},
	{"kpanic", 622592, 4194304},
	{"system", 630784, 2147483648},
	{"userdata", 4825088, 5347737600},
}

func sameAliasSet(got, want []string) bool {
	if len(got) != len(want) {
		return false
	}
	seen := map[string]bool{}
	for _, s := range got {
		if seen[s] {
			return false
		}
		seen[s] = true
	}
	for _, s := range want {
		if !seen[s] {
			return false
		}
	}
	return true
}

// Guards apply on initial selection and every later source revalidation. The
// hash binds this policy to the observed eMMC; it is not an authenticity proof
// against a hostile kernel. No policy fallback exists for other variants.
func validateRK3229C(facts []BlockFact, dt string, identity map[string]string, expectedCID string) error {
	if !sdCIDHash.MatchString(expectedCID) {
		return fmt.Errorf("politica C: compilacion sin identidad eMMC fijada")
	}
	if dt != "rockchip,rk3229" || len(identity) != 1 || identity["mmcblk0_cid_sha256"] != expectedCID {
		return fmt.Errorf("politica C: DT/CID de eMMC distinto o no disponible")
	}
	if len(facts) != len(rk3229CPartitions)+1 {
		return fmt.Errorf("politica C: cantidad de bloques distinta del mapa recovery verificado")
	}
	byName := map[string]BlockFact{}
	for _, f := range facts {
		if _, ok := byName[f.Name]; ok {
			return fmt.Errorf("politica C: bloque duplicado")
		}
		byName[f.Name] = f
	}
	disk, ok := byName["mmcblk0"]
	if !ok || disk.Kind != "emmc_user_area" || disk.Parent != "" || disk.Start != 0 ||
		disk.Bytes != 7818182656 || disk.MajorMinor != "179:0" || disk.Path != "/dev/block/mmcblk0" ||
		disk.SysPath != rk3229CSysfs || !sameAliasSet(disk.Aliases, []string{"/dev/block/mmcblk0", rk3229CBlockPlatform + "mmcblk0"}) {
		return fmt.Errorf("politica C: padre eMMC no corresponde al mapa recovery verificado")
	}
	for i, p := range rk3229CPartitions {
		n := i + 1
		name := fmt.Sprintf("mmcblk0p%d", n)
		f, ok := byName[name]
		aliases := []string{"/dev/block/" + name, rk3229CBlockPlatform + "by-name/" + p.Alias,
			fmt.Sprintf("%sby-num/p%d", rk3229CBlockPlatform, n), rk3229CBlockPlatform + name}
		if !ok || f.Kind != "partition" || f.Parent != "mmcblk0" || f.Start != p.Start || f.Bytes != p.Bytes ||
			f.MajorMinor != fmt.Sprintf("179:%d", n) || f.Path != "/dev/block/"+name ||
			f.SysPath != rk3229CSysfs+"/"+name || !sameAliasSet(f.Aliases, aliases) {
			return fmt.Errorf("politica C: particion %s/geometria/alias no corresponde al mapa recovery verificado", name)
		}
	}
	return nil
}

func chooseRK3229CSources(facts []BlockFact, mounts []Mount, dt string, identity map[string]string, expectedCID string) ([]BlockFact, []Skip, error) {
	if e := validateRK3229C(facts, dt, identity, expectedCID); e != nil {
		return nil, nil, e
	}
	chosen, skips, e := chooseSourcesConfigured(facts, mounts, false)
	if e != nil {
		return nil, nil, e
	}
	for _, f := range chosen {
		if f.Kind != "partition" {
			return nil, nil, fmt.Errorf("politica C: seleccion incluye un area completa")
		}
	}
	// Preserve verified preceding sources if the final backup attempt changes
	// again. All sources retain the same three hashes and stop-on-error engine.
	sort.Slice(chosen, func(i, j int) bool {
		if chosen[i].Name == "mmcblk0p10" {
			return false
		}
		if chosen[j].Name == "mmcblk0p10" {
			return true
		}
		return chosen[i].Start < chosen[j].Start
	})
	return chosen, skips, nil
}
