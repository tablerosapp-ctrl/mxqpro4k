//go:build linux

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

func writeDurableJSON(path string, value any) error {
	data, e := json.MarshalIndent(value, "", "  ")
	if e != nil {
		return e
	}
	data = append(data, '\n')
	f, e := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	n, e := f.Write(data)
	if e == nil && n != len(data) {
		e = fmt.Errorf("recibo escrito parcialmente")
	}
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e == nil {
		e = ce
	}
	if e != nil {
		return e
	}
	if e = syncDir(filepath.Dir(path)); e != nil {
		return e
	}
	got, e := os.ReadFile(path)
	if e != nil {
		return e
	}
	if !bytes.Equal(got, data) {
		return fmt.Errorf("recibo no persistio correctamente")
	}
	return nil
}

func rejectIncompleteMigration(usb string) error {
	entries, e := os.ReadDir(usb)
	if e != nil {
		return e
	}
	for _, entry := range entries {
		if !strings.HasPrefix(entry.Name(), "TVBASE-respaldo-rest021-") {
			continue
		}
		if !entry.IsDir() || entry.Type()&os.ModeSymlink != 0 {
			return fmt.Errorf("respaldo anterior con tipo inesperado")
		}
		dir := filepath.Join(usb, entry.Name())
		_, started := os.Lstat(filepath.Join(dir, "10-restore-started.json"))
		_, finished := os.Lstat(filepath.Join(dir, "90-restored-verified.json"))
		if started == nil && os.IsNotExist(finished) {
			return fmt.Errorf("instalacion anterior incompleta: %s; conservar su respaldo y revisar antes de repetir", entry.Name())
		}
		if started != nil && !os.IsNotExist(started) {
			return started
		}
		if finished != nil && !os.IsNotExist(finished) {
			return finished
		}
	}
	return nil
}

func targetSetGuard(ts []Target, usb string) error {
	current, e := usbDirectoryWithRemount(false)
	if e != nil {
		return e
	}
	if filepath.Clean(current) != filepath.Clean(usb) {
		return fmt.Errorf("cambio el montaje USB")
	}
	if e = targetsUnmounted(ts); e != nil {
		return e
	}
	for _, t := range ts {
		size, r, disk, e := block(t.Path)
		if e != nil || size != t.Size || r != t.Device || disk != t.Disk {
			return fmt.Errorf("cambio el destino %s", t.Image.Name)
		}
	}
	return nil
}

func backupFive(ts []Target, usb string) (string, []BackupEvidence, error) {
	var total uint64
	for _, t := range ts {
		if t.Size <= 0 || t.Size > 0xffffffff {
			return "", nil, fmt.Errorf("respaldo supera FAT32")
		}
		total += uint64(t.Size)
	}
	if len(ts) != 5 || total != 2571108352 {
		return "", nil, fmt.Errorf("conjunto de cinco respaldos inesperado")
	}
	var fs syscall.Statfs_t
	if e := syscall.Statfs(usb, &fs); e != nil {
		return "", nil, e
	}
	if uint64(fs.Bavail)*uint64(fs.Bsize) < total+backupSpaceMargin {
		return "", nil, fmt.Errorf("se necesitan al menos 3107979264 bytes libres para el respaldo")
	}
	dir, e := os.MkdirTemp(usb, "TVBASE-respaldo-rest021-")
	if e != nil {
		return "", nil, e
	}
	if e = syncDir(usb); e != nil {
		return dir, nil, e
	}
	records := []BackupEvidence{}
	for _, t := range ts {
		phase := "copiando"
		last := time.Time{}
		hooks := BackupHooks{Guard: func() error { return targetSetGuard(ts, usb) },
			Stage: func(s string) { phase = s; say(t.Image.Name + ": " + s) },
			Tick: func(n int64) {
				if time.Since(last) >= 5*time.Second {
					say(fmt.Sprintf("%s: %s %d/%d bytes", t.Image.Name, phase, n, t.Size))
					last = time.Now()
				}
			},
		}
		result, e := backupVerifiedFile(t.Image.Name, t.Path, filepath.Join(dir, t.Image.Name+".img"), t.Size, "", hooks)
		if e != nil {
			return dir, records, e
		}
		records = append(records, result)
	}
	return dir, records, nil
}

func requiredBackups(ts []Target) map[string]int64 {
	expected := map[string]int64{}
	for _, t := range ts {
		expected[t.Image.Name] = t.Size
	}
	return expected
}

func persistBackupSet(dir string, records []BackupEvidence, ts []Target) error {
	if e := requireVerifiedBackups(records, requiredBackups(ts)); e != nil {
		return e
	}
	return writeDurableJSON(filepath.Join(dir, "00-backup-verified.json"), map[string]any{
		"format": 1, "state": "backup_verified", "package_id": allowedPackageID, "dt_id": "gxlx2_p291_1g", "media_id": mediaID,
		"records": records, "userdata_untouched": true, "created_utc": time.Now().UTC().Format(time.RFC3339),
	})
}

func backupSetStillValid(dir string, records []BackupEvidence, ts []Target, usb string) error {
	if e := requireVerifiedBackups(records, requiredBackups(ts)); e != nil {
		return e
	}
	for _, r := range records {
		if e := targetSetGuard(ts, usb); e != nil {
			return e
		}
		path := filepath.Join(dir, r.File)
		st, e := os.Lstat(path)
		if e != nil || !st.Mode().IsRegular() || st.Size() != r.Bytes {
			return fmt.Errorf("el respaldo %s cambio", r.Name)
		}
		say("Comprobacion final del respaldo " + r.Name)
		sum, e := hashWithRecoveryProgress(path, r.Bytes, "Comprobando respaldo "+r.Name)
		if e != nil || sum != r.SHA256 {
			return fmt.Errorf("el respaldo %s ya no coincide", r.Name)
		}
	}
	return targetSetGuard(ts, usb)
}
