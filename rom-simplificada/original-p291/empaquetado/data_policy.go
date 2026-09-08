package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

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
			return fmt.Errorf("userdata contiene %q; migracion separada pendiente, no se borro nada", entry.Name())
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
