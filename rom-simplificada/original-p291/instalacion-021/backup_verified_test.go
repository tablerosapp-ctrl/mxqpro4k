package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestFormattedDataSuperblockMustMatchRuntimeProfile(t *testing.T) {
	sb := make([]byte, 1024)
	for at, value := range map[int]uint32{4: 853500, 20: 0, 24: 2, 92: 0x3c, 96: 0x242, 100: 0x7b} {
		binary.LittleEndian.PutUint32(sb[at:], value)
	}
	binary.LittleEndian.PutUint16(sb[56:], 0xef53)
	binary.LittleEndian.PutUint16(sb[58:], 1)
	binary.LittleEndian.PutUint16(sb[88:], 256)
	if e := validateFreshSuperblock(sb); e != nil {
		t.Fatal(e)
	}
	for _, offset := range []int{4, 20, 24, 56, 58, 88, 92, 96, 100} {
		bad := append([]byte{}, sb...)
		bad[offset] ^= 1
		if validateFreshSuperblock(bad) == nil {
			t.Fatal("bad ext4 field accepted", offset)
		}
	}
	if validateFreshSuperblock(sb[:900]) == nil {
		t.Fatal("short superblock accepted")
	}
}

func TestBackupPreservesBinaryAndProvesThreeHashes(t *testing.T) {
	for _, content := range [][]byte{bytes.Repeat([]byte{0, 10, 13, 255, 128}, 1024), bytes.Repeat([]byte("\r\n\x00unchanged\n"), 700), bytes.Repeat([]byte{255}, 8192)} {
		dir := t.TempDir()
		source := filepath.Join(dir, "source.bin")
		destination := filepath.Join(dir, "data.img")
		if e := os.WriteFile(source, content, 0600); e != nil {
			t.Fatal(e)
		}
		directorySynced := false
		got, e := backupVerifiedFile("data", source, destination, int64(len(content)), "", BackupHooks{SyncDirectory: func(string) error { directorySynced = true; return nil }})
		if e != nil {
			t.Fatal(e)
		}
		if !directorySynced || got.State != "verified" || got.SHA256 != got.USBReadSHA256 || got.SHA256 != got.SourceAfterSHA256 {
			t.Fatal(got)
		}
		actual, e := os.ReadFile(destination)
		if e != nil || !bytes.Equal(content, actual) {
			t.Fatal("binary content changed", e)
		}
		if _, e = os.Stat(destination + ".parcial"); !os.IsNotExist(e) {
			t.Fatal("partial not promoted")
		}
	}
}

func TestBackupFailuresNeverBecomeVerified(t *testing.T) {
	for _, name := range []string{"short-source", "wrong-source-hash", "file-sync", "directory-sync", "changed-source", "changed-usb", "appended-usb", "guard-mounted", "existing-file"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			source := filepath.Join(dir, "source.bin")
			destination := filepath.Join(dir, "data.img")
			content := bytes.Repeat([]byte{0, 10, 13, 255}, 2048)
			os.WriteFile(source, content, 0600)
			hooks := BackupHooks{SyncDirectory: func(string) error { return nil }}
			size := int64(len(content))
			expected := ""
			switch name {
			case "short-source":
				size++
			case "wrong-source-hash":
				expected = strings.Repeat("0", 64)
			case "file-sync":
				hooks.SyncFile = func(*os.File) error { return errors.New("injected durable write failure") }
			case "directory-sync":
				hooks.SyncDirectory = func(string) error { return errors.New("injected directory synchronization failure") }
			case "changed-source":
				hooks.AfterCopy = func() error { return os.WriteFile(source, bytes.Repeat([]byte{1}, len(content)), 0600) }
			case "changed-usb":
				hooks.AfterCopy = func() error { return os.WriteFile(destination+".parcial", bytes.Repeat([]byte{1}, len(content)), 0600) }
			case "appended-usb":
				hooks.AfterCopy = func() error {
					f, e := os.OpenFile(destination+".parcial", os.O_APPEND|os.O_WRONLY, 0)
					if e != nil {
						return e
					}
					defer f.Close()
					_, e = f.Write([]byte{1})
					return e
				}
			case "guard-mounted":
				hooks.Guard = func() error { return errors.New("source mounted during operation") }
			case "existing-file":
				os.WriteFile(destination, []byte("preserve previous backup"), 0600)
			}
			got, e := backupVerifiedFile("data", source, destination, size, expected, hooks)
			if e == nil || got.State == "verified" {
				t.Fatal("failure accepted", got, e)
			}
			if name == "existing-file" {
				b, _ := os.ReadFile(destination)
				if string(b) != "preserve previous backup" {
					t.Fatal("old backup changed")
				}
			}
		})
	}
}

func TestNoFormattingAfterBackupOrSyncFailure(t *testing.T) {
	for _, failing := range []int{-1, 0, 1, 2, 3, 4} {
		var called []int
		stage := func(index int) func() error {
			return func() error {
				called = append(called, index)
				if index == failing {
					return errors.New("injected stage failure")
				}
				return nil
			}
		}
		err := executeMigration(MigrationStages{Backup: stage(0), PersistVerifiedBackup: stage(1), Format: stage(2), VerifyFreshUnmounted: stage(3), Flash: stage(4)})
		if failing < 0 {
			if err != nil || len(called) != 5 {
				t.Fatal(called, err)
			}
		} else {
			if err == nil || len(called) != failing+1 {
				t.Fatal("continued after failure", called, err)
			}
		}
	}
}

func TestIncompleteOrUnstableBackupSetCannotFormat(t *testing.T) {
	size := int64(8192)
	sum := strings.Repeat("a", 64)
	good := BackupEvidence{Name: "data", File: "data.img", Bytes: size, SHA256: sum, USBReadSHA256: sum, SourceAfterSHA256: sum, State: "verified"}
	required := map[string]int64{"data": size}
	if e := requireVerifiedBackups([]BackupEvidence{good}, required); e != nil {
		t.Fatal(e)
	}
	for _, mutate := range []func(*BackupEvidence){func(r *BackupEvidence) { r.State = "copied" }, func(r *BackupEvidence) { r.SourceAfterSHA256 = "" }, func(r *BackupEvidence) { r.USBReadSHA256 = strings.Repeat("b", 64) }, func(r *BackupEvidence) { r.Bytes-- }, func(r *BackupEvidence) { r.File = "../data.img" }} {
		bad := good
		mutate(&bad)
		if requireVerifiedBackups([]BackupEvidence{bad}, required) == nil {
			t.Fatal("bad evidence accepted")
		}
	}
	if requireVerifiedBackups(nil, required) == nil || requireVerifiedBackups([]BackupEvidence{good, good}, required) == nil {
		t.Fatal("incomplete/duplicate backup set accepted")
	}
}
