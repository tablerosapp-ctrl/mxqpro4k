package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func validateFreshSuperblock(sb []byte) error {
	if len(sb) != 1024 {
		return fmt.Errorf("superblock incompleto")
	}
	u16 := func(at int) uint16 { return binary.LittleEndian.Uint16(sb[at:]) }
	u32 := func(at int) uint32 { return binary.LittleEndian.Uint32(sb[at:]) }
	if u16(56) != 0xef53 || u32(4) != 853500 || u32(20) != 0 || u32(24) != 2 || u16(88) != 256 || u16(58) != 1 {
		return fmt.Errorf("ext4 creado no coincide con geometria/estado requerido")
	}
	if u32(92) != 0x3c || u32(96) != 0x242 || u32(100) != 0x7b {
		return fmt.Errorf("features ext4 difieren de las originales compatibles")
	}
	return nil
}

// The real mount/device is checked separately on Linux. This function only
// checks content. No marker can substitute for a clean userdata filesystem.
func requireEmptyDataDirectory(path string) error {
	info, e := os.Lstat(path)
	if e != nil {
		return e
	}
	if !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return fmt.Errorf("userdata no es un directorio real")
	}
	entries, e := os.ReadDir(path)
	if e != nil {
		return e
	}
	for _, entry := range entries {
		if entry.Name() != "lost+found" || !entry.IsDir() || entry.Type()&os.ModeSymlink != 0 {
			return fmt.Errorf("userdata contiene %q; no se continuara la instalacion", entry.Name())
		}
		inner, e := os.ReadDir(filepath.Join(path, "lost+found"))
		if e != nil {
			return e
		}
		if len(inner) != 0 {
			return fmt.Errorf("lost+found contiene datos; revisar antes de instalar")
		}
	}
	return nil
}
func requireDataReadOnlyMount(info, expectedMM string) error {
	found := 0
	for _, line := range strings.Split(info, "\n") {
		fields := strings.Fields(line)
		if len(fields) < 6 {
			continue
		}
		if fields[4] == "/data" {
			found++
			if fields[2] != expectedMM || !strings.Contains(","+fields[5]+",", ",ro,") || strings.Contains(","+fields[5]+",", ",rw,") {
				return fmt.Errorf("/data debe estar montada solo lectura desde userdata real")
			}
		} else if fields[2] == expectedMM {
			return fmt.Errorf("userdata tambien esta montada en otro destino")
		}
	}
	if found != 1 {
		return fmt.Errorf("montaje /data no acreditado; preparar userdata por operacion separada")
	}
	return nil
}
