package main

import (
	"fmt"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// Mount reflects both mount and superblock options; a read-only bind of a
// writable filesystem does not qualify as a stable raw source.
type Mount struct {
	Device, Root, Point, FS string
	ReadOnly, Writable      bool
}

func unescapeMount(s string) (string, error) {
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		if s[i] != '\\' {
			b.WriteByte(s[i])
			continue
		}
		if i+3 >= len(s) {
			return "", fmt.Errorf("escape mountinfo truncado")
		}
		v, e := strconv.ParseUint(s[i+1:i+4], 8, 8)
		if e != nil || (v != 32 && v != 9 && v != 10 && v != 92) {
			return "", fmt.Errorf("escape mountinfo invalido")
		}
		b.WriteByte(byte(v))
		i += 3
	}
	return b.String(), nil
}
func hasOption(options, value string) bool {
	for _, v := range strings.Split(options, ",") {
		if v == value {
			return true
		}
	}
	return false
}
func parseMounts(b []byte) ([]Mount, error) {
	var out []Mount
	for _, line := range strings.Split(strings.TrimSpace(string(b)), "\n") {
		if line == "" {
			continue
		}
		f := strings.Fields(line)
		sep := -1
		for i, v := range f {
			if v == "-" {
				sep = i
				break
			}
		}
		if len(f) < 10 || sep < 6 || len(f) < sep+4 {
			return nil, fmt.Errorf("mountinfo malformado")
		}
		if _, _, e := parseMM(f[2]); e != nil {
			return nil, e
		}
		root, e := unescapeMount(f[3])
		if e != nil {
			return nil, e
		}
		point, e := unescapeMount(f[4])
		if e != nil {
			return nil, e
		}
		if !strings.HasPrefix(point, "/") {
			return nil, fmt.Errorf("montaje relativo")
		}
		out = append(out, Mount{f[2], root, point, f[sep+1], hasOption(f[5], "ro") && hasOption(f[sep+3], "ro"), hasOption(f[5], "rw") && hasOption(f[sep+3], "rw")})
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("sin mountinfo")
	}
	return out, nil
}
func parseMM(s string) (uint64, uint64, error) {
	f := strings.Split(s, ":")
	if len(f) != 2 {
		return 0, 0, fmt.Errorf("major:minor invalido")
	}
	a, e := strconv.ParseUint(f[0], 10, 32)
	if e != nil {
		return 0, 0, e
	}
	b, e := strconv.ParseUint(f[1], 10, 32)
	if e != nil {
		return 0, 0, e
	}
	return a, b, nil
}
func safeRelative(name string) bool {
	return name != "" && name != "." && name != ".." && filepath.Base(name) == name && !strings.ContainsAny(name, "/\\:\x00\r\n")
}

type BlockFact struct {
	Name           string   `json:"name"`
	Path           string   `json:"device"`
	SysPath        string   `json:"sysfs"`
	MajorMinor     string   `json:"major_minor"`
	Parent         string   `json:"parent"`
	Kind           string   `json:"kind"`
	Bytes          int64    `json:"bytes"`
	Start          int64    `json:"start_sector,omitempty"`
	Aliases        []string `json:"aliases"`
	Holders        []string `json:"holders"`
	ReadOnlyDevice bool     `json:"read_only_device"`
}
type Skip struct{ Name, Reason string }

// Selection does not change mounts. A whole eMMC user area is preferred only
// when every exposed descendant is stable. Otherwise safe partitions are kept.
func chooseSources(facts []BlockFact, mounts []Mount) ([]BlockFact, []Skip, error) {
	byName := map[string]BlockFact{}
	devs := map[string]bool{}
	var disks []string
	for _, f := range facts {
		if !safeRelative(f.Name) || f.Bytes <= 0 || f.Bytes > 1<<40 || devs[f.MajorMinor] {
			return nil, nil, fmt.Errorf("inventario de bloques invalido")
		}
		if _, _, e := parseMM(f.MajorMinor); e != nil {
			return nil, nil, e
		}
		devs[f.MajorMinor] = true
		byName[f.Name] = f
		if f.Kind == "emmc_user_area" {
			disks = append(disks, f.Name)
		}
	}
	sort.Strings(disks)
	var chosen []BlockFact
	var skips []Skip
	stable := func(f BlockFact) bool {
		if len(f.Holders) > 0 {
			return false
		}
		for _, m := range mounts {
			if m.Device == f.MajorMinor && !m.ReadOnly {
				return false
			}
		}
		return true
	}
	for _, name := range disks {
		disk := byName[name]
		children := []BlockFact{}
		whole := stable(disk)
		for _, f := range facts {
			if f.Parent == name && f.Kind == "partition" {
				if f.Start < 0 || f.Bytes%512 != 0 || f.Start > (disk.Bytes-f.Bytes)/512 {
					return nil, nil, fmt.Errorf("particion fuera del disco: %s", f.Name)
				}
				children = append(children, f)
				whole = whole && stable(f)
			}
		}
		sort.Slice(children, func(i, j int) bool { return children[i].Start < children[j].Start })
		for i := 1; i < len(children); i++ {
			if children[i].Start < children[i-1].Start+children[i-1].Bytes/512 {
				return nil, nil, fmt.Errorf("particiones superpuestas")
			}
		}
		if whole {
			chosen = append(chosen, disk)
		} else {
			skips = append(skips, Skip{name, "area completa omitida: montaje RW o dispositivo en uso; se evalua cada particion"})
			for _, f := range children {
				if stable(disk) && stable(f) {
					chosen = append(chosen, f)
				} else {
					skips = append(skips, Skip{f.Name, "particion o padre con montaje RW/holders activos; no se desmonta ni remonta"})
				}
			}
		}
	}
	for _, f := range facts {
		if f.Kind == "emmc_boot_area" {
			if _, ok := byName[f.Parent]; !ok {
				return nil, nil, fmt.Errorf("boot area sin padre")
			}
			if stable(f) {
				chosen = append(chosen, f)
			} else {
				skips = append(skips, Skip{f.Name, "area boot en uso"})
			}
		}
	}
	sort.Slice(chosen, func(i, j int) bool { return chosen[i].Name < chosen[j].Name })
	return chosen, skips, nil
}
