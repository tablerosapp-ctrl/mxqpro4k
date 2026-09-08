//go:build linux

package main

import (
	"bytes"
	"context"
	"encoding/binary"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

const formatterPath = "/sbin/mke2fs_static"
const formatterSHA = "2b1799d99503493f46f130f861889e0f03eb00d39cc633212890823bf1f86525"
const formatterConfigSHA = "dcd4750293852e9b06f6de4c51c24d3d3941e67f221872965c6f02251509cd02"

func checkBootEnvironment(disk string) error {
	layout, e := inspectBlock("/dev/block/env", "env")
	if e != nil {
		return fmt.Errorf("fase ENV: %w", e)
	}
	if layout.Bytes != 8388608 || layout.MajorMinor != "179:4" || layout.ParentPath != disk {
		return fmt.Errorf("ENV no corresponde al P291")
	}
	f, e := os.Open("/dev/block/env")
	if e != nil {
		return e
	}
	defer f.Close()
	record := make([]byte, 65536)
	if _, e = f.ReadAt(record, 0); e != nil {
		return e
	}
	return requireNormalBootEnvironment(record)
}

func dataTarget(disk string) (Target, error) {
	layout, e := inspectBlock("/dev/block/data", "data")
	if e != nil {
		return Target{}, fmt.Errorf("fase userdata: %w", e)
	}
	size, r := int64(layout.Bytes), layout.Device
	if size != userdataBytes || mm(r) != "179:20" || layout.ParentPath != disk {
		return Target{}, fmt.Errorf("userdata no coincide con P291 original")
	}
	holders, e := os.ReadDir("/sys/dev/block/179:20/holders")
	if e != nil || len(holders) != 0 {
		return Target{}, fmt.Errorf("userdata tiene un mapping o propietario inesperado")
	}
	return Target{Layout: layout, Image: Image{Name: "data", Size: size, MajorMinor: "179:20"}, Path: "/dev/block/data", Size: size, Device: r, MajorMinor: "179:20", Disk: disk}, nil
}

func detachDataNormally(t Target) error {
	info, e := os.ReadFile("/proc/self/mountinfo")
	if e != nil {
		return e
	}
	mounted := false
	for _, line := range strings.Split(string(info), "\n") {
		f := strings.Fields(line)
		if len(f) < 6 {
			continue
		}
		if strings.HasPrefix(f[4], "/data/") {
			return fmt.Errorf("hay un montaje dependiente dentro de /data")
		}
		if f[2] == t.MajorMinor {
			if f[4] != "/data" || mounted {
				return fmt.Errorf("userdata montada en un destino inesperado")
			}
			mounted = true
		} else if f[4] == "/data" {
			return fmt.Errorf("/data no corresponde al dispositivo esperado")
		}
	}
	if mounted {
		say("Desmontando los datos antes del respaldo.")
		if e = syscall.Unmount("/data", 0); e != nil {
			return fmt.Errorf("no se pudo desmontar /data normalmente: %w", e)
		}
	}
	return targetsUnmounted([]Target{t})
}

func checkFormatter() error {
	for _, item := range []struct {
		path, sum string
		size      int64
	}{{formatterPath, formatterSHA, 697820}, {"/etc/mke2fs.conf", formatterConfigSHA, 0}} {
		st, e := os.Lstat(item.path)
		if e != nil || !st.Mode().IsRegular() || st.Mode()&os.ModeSymlink != 0 || (item.size > 0 && st.Size() != item.size) {
			return fmt.Errorf("herramienta/configuracion de recovery inesperada: %s", item.path)
		}
		sum, e := fileHash(item.path, st.Size())
		if e != nil || sum != item.sum {
			return fmt.Errorf("SHA de recovery inesperado: %s", item.path)
		}
	}
	return nil
}

func requireUnmountedData(t Target) error {
	current, e := dataTarget(t.Disk)
	if e != nil {
		return e
	}
	if current.Layout != t.Layout {
		return fmt.Errorf("cambio userdata")
	}
	if e = revalidateBlockLayouts("userdata antes de formato/montaje/escritura"); e != nil {
		return e
	}
	return targetsUnmounted([]Target{t})
}

func checkOriginalDataReadable(t Target) error {
	if e := requireUnmountedData(t); e != nil {
		return e
	}
	f, e := os.Open(t.Path)
	if e != nil {
		return e
	}
	defer f.Close()
	sb := make([]byte, 1024)
	if _, e = f.ReadAt(sb, 1024); e != nil {
		return e
	}
	blocks := uint64(binary.LittleEndian.Uint32(sb[4:]))
	logBlock := binary.LittleEndian.Uint32(sb[24:])
	if binary.LittleEndian.Uint16(sb[56:]) != 0xef53 || logBlock != 2 || blocks == 0 || blocks*4096 > uint64(t.Size) {
		return fmt.Errorf("userdata no es ext4 directamente legible; no se cambiara su cifrado ni se formateara")
	}
	return nil
}

// A bounded combined-output sink prevents an unexpected child process from
// exhausting recovery RAM. The child exit status is always checked separately.
type boundedOutput struct {
	data      []byte
	truncated bool
}

func (w *boundedOutput) Write(p []byte) (int, error) {
	n := len(p)
	left := (1 << 20) - len(w.data)
	if len(p) > left {
		p = p[:left]
		w.truncated = true
	}
	w.data = append(w.data, p...)
	return n, nil
}

func formatUserdata(t Target, dir string) error {
	if e := requireUnmountedData(t); e != nil {
		return e
	}
	if e := checkFormatter(); e != nil {
		return e
	}
	if e := checkBootEnvironment(t.Disk); e != nil {
		return e
	}
	if e := writeDurableJSON(filepath.Join(dir, "10-format-started.json"), map[string]any{"state": "format_started", "device": t.MajorMinor, "bytes": t.Size, "filesystem_bytes": userdataFilesystemBytes}); e != nil {
		return e
	}
	say("Respaldo completo verificado. Preparando el almacenamiento interno limpio.")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	command := exec.CommandContext(ctx, formatterPath, "-F", "-t", "ext4", "-b", "4096", "-E", "nodiscard,lazy_itable_init=0,lazy_journal_init=0", t.Path, "853500")
	command.Env = []string{"PATH=/sbin", "LANG=C", "LC_ALL=C", "MKE2FS_CONFIG=/etc/mke2fs.conf"}
	output := &boundedOutput{}
	command.Stdout = output
	command.Stderr = output
	finished := make(chan error, 1)
	if e := command.Start(); e != nil {
		return e
	}
	go func() { finished <- command.Wait() }()
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()
	var runError error
	waiting := true
	for waiting {
		select {
		case runError = <-finished:
			waiting = false
		case <-ticker.C:
			say("Creando ext4; mantener conectada la alimentacion.")
		}
	}
	exitCode := -1
	if command.ProcessState != nil {
		exitCode = command.ProcessState.ExitCode()
	}
	if e := writeDurableJSON(filepath.Join(dir, "11-format-result.json"), map[string]any{"exit": exitCode, "timeout": ctx.Err() != nil, "output_truncated": output.truncated, "output": string(output.data)}); e != nil {
		return e
	}
	if runError != nil || exitCode != 0 || ctx.Err() != nil || output.truncated {
		return fmt.Errorf("fallo formateador (exit %d): %v", exitCode, runError)
	}
	if e := requireUnmountedData(t); e != nil {
		return e
	}
	// The backup includes this footer. Remove the old encryption metadata only
	// after backup and successful filesystem creation, within the data target.
	file, e := os.OpenFile(t.Path, os.O_RDWR, 0)
	if e != nil {
		return e
	}
	zero := make([]byte, 16384)
	n, e := file.WriteAt(zero, userdataFilesystemBytes)
	if e == nil && n != len(zero) {
		e = fmt.Errorf("escritura corta de footer")
	}
	if e == nil {
		e = file.Sync()
	}
	closeError := file.Close()
	if e == nil {
		e = closeError
	}
	if e != nil {
		return e
	}
	check, e := os.Open(t.Path)
	if e != nil {
		return e
	}
	defer check.Close()
	sb := make([]byte, 1024)
	if _, e = check.ReadAt(sb, 1024); e != nil {
		return e
	}
	if e = validateFreshSuperblock(sb); e != nil {
		return e
	}
	tail := make([]byte, 16384)
	if _, e = check.ReadAt(tail, userdataFilesystemBytes); e != nil {
		return e
	}
	if !bytes.Equal(tail, zero) {
		return fmt.Errorf("footer no quedo limpio")
	}
	return requireUnmountedData(t)
}

func verifyFreshDataAndUnmount(disk string) error {
	t, e := dataTarget(disk)
	if e != nil {
		return e
	}
	if e = requireUnmountedData(t); e != nil {
		return e
	}
	st, e := os.Lstat("/data")
	if e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return fmt.Errorf("punto /data no valido")
	}
	if e = syscall.Mount(t.Path, "/data", "ext4", syscall.MS_RDONLY|syscall.MS_NODEV|syscall.MS_NOSUID|syscall.MS_NOEXEC, "noload"); e != nil {
		return e
	}
	result := requireDataReadOnlyMount(readText("/proc/self/mountinfo"), t.MajorMinor)
	if result == nil {
		result = requireEmptyDataDirectory("/data")
	}
	unmountError := syscall.Unmount("/data", 0)
	if unmountError != nil {
		return fmt.Errorf("no se pudo desmontar /data tras verificarla: %w", unmountError)
	}
	if result != nil {
		return result
	}
	return requireUnmountedData(t)
}
