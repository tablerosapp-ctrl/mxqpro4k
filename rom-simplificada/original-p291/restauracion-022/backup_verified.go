package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)

const userdataBytes int64 = 3495952384
const userdataFilesystemBytes int64 = userdataBytes - 16384
const backupSpaceMargin uint64 = 512 << 20

type BackupEvidence struct {
	Name              string `json:"name"`
	File              string `json:"file"`
	Bytes             int64  `json:"bytes"`
	SHA256            string `json:"sha256"`
	USBReadSHA256     string `json:"usb_read_sha256"`
	SourceAfterSHA256 string `json:"source_after_sha256"`
	State             string `json:"state"`
}

// Injection points exercise real binary file copies and failed durability
// without a block device. Production uses only the defaults below.
type BackupHooks struct {
	Guard         func() error
	SyncFile      func(*os.File) error
	SyncDirectory func(string) error
	AfterCopy     func() error
	Tick          func(int64)
	Stage         func(string)
}

func syncDirectoryFile(path string) error {
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	return f.Sync()
}

func backupVerifiedFile(name, source, destination string, size int64, expected string, h BackupHooks) (BackupEvidence, error) {
	result := BackupEvidence{Name: name, File: filepath.Base(destination), Bytes: size}
	if size <= 0 || size > 0xffffffff || (expected != "" && !validSHA(expected)) {
		return result, fmt.Errorf("geometria/hash invalido para respaldo")
	}
	guard := h.Guard
	if guard == nil {
		guard = func() error { return nil }
	}
	syncFile := h.SyncFile
	if syncFile == nil {
		syncFile = func(f *os.File) error { return f.Sync() }
	}
	syncDirectory := h.SyncDirectory
	if syncDirectory == nil {
		syncDirectory = syncDirectoryFile
	}
	if e := guard(); e != nil {
		return result, e
	}
	if _, e := os.Lstat(destination); !os.IsNotExist(e) {
		return result, fmt.Errorf("destino de respaldo ya existe o no es comprobable")
	}
	partial := destination + ".parcial"
	in, e := os.Open(source)
	if e != nil {
		return result, e
	}
	out, e := os.OpenFile(partial, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		in.Close()
		return result, e
	}
	if h.Stage != nil {
		h.Stage("copiando")
	}
	sum, e := copyExact(out, in, size, h.Tick)
	closeInput := in.Close()
	if e == nil {
		e = closeInput
	}
	if e == nil {
		e = syncFile(out)
	}
	closeOutput := out.Close()
	if e == nil {
		e = closeOutput
	}
	if e != nil {
		return result, e
	}
	result.SHA256 = sum
	if expected != "" && sum != expected {
		return result, fmt.Errorf("origen %s difiere del original conocido", name)
	}
	if h.AfterCopy != nil {
		if e = h.AfterCopy(); e != nil {
			return result, e
		}
	}
	if e = guard(); e != nil {
		return result, e
	}
	info, e := os.Lstat(partial)
	if e != nil || !info.Mode().IsRegular() || info.Size() != size {
		return result, fmt.Errorf("tamano o tipo de copia incorrecto")
	}
	if h.Stage != nil {
		h.Stage("releyendo pendrive")
	}
	readback, e := hashBackupSource(partial, size, h.Tick)
	if e != nil || readback != sum {
		return result, fmt.Errorf("relectura USB incorrecta para %s: %v", name, e)
	}
	result.USBReadSHA256 = readback
	if e = guard(); e != nil {
		return result, e
	}
	if h.Stage != nil {
		h.Stage("comprobando origen estable")
	}
	sourceAfter, e := hashBackupSource(source, size, h.Tick)
	if e != nil || sourceAfter != sum {
		return result, fmt.Errorf("origen cambio durante respaldo %s: %v", name, e)
	}
	result.SourceAfterSHA256 = sourceAfter
	if e = guard(); e != nil {
		return result, e
	}
	if e = os.Rename(partial, destination); e != nil {
		return result, e
	}
	if e = syncDirectory(filepath.Dir(destination)); e != nil {
		return result, e
	}
	result.State = "verified"
	return result, nil
}

func hashBackupSource(path string, size int64, tick func(int64)) (string, error) {
	f, e := os.Open(path)
	if e != nil {
		return "", e
	}
	defer f.Close()
	return copyExact(io.Discard, f, size, tick)
}

func requireVerifiedBackups(records []BackupEvidence, required map[string]int64) error {
	if len(records) != len(required) {
		return fmt.Errorf("faltan respaldos")
	}
	seen := map[string]bool{}
	for _, r := range records {
		n, ok := required[r.Name]
		if !ok || seen[r.Name] || r.Bytes != n || r.State != "verified" || !validSHA(r.SHA256) || r.USBReadSHA256 != r.SHA256 || r.SourceAfterSHA256 != r.SHA256 || r.File != r.Name+".img" {
			return fmt.Errorf("respaldo no verificado: %s", r.Name)
		}
		seen[r.Name] = true
	}
	return nil
}

type MigrationStages struct {
	Backup                func() error
	PersistVerifiedBackup func() error
	Format                func() error
	VerifyFreshUnmounted  func() error
	Flash                 func() error
}

// Destructive stages are unreachable after any failed backup or durability
// check. A failed format/empty check prevents every system-image write.
func executeMigration(s MigrationStages) error {
	for _, step := range []func() error{s.Backup, s.PersistVerifiedBackup, s.Format, s.VerifyFreshUnmounted, s.Flash} {
		if step == nil {
			return fmt.Errorf("etapa de migracion ausente")
		}
	}
	for _, step := range []func() error{s.Backup, s.PersistVerifiedBackup, s.Format, s.VerifyFreshUnmounted, s.Flash} {
		if e := step(); e != nil {
			return e
		}
	}
	return nil
}
