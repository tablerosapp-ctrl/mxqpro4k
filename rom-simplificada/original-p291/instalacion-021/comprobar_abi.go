//go:build ignore

// Compile explicitly with block_abi.go. This probe cannot run an installer:
// it only opens two fixed partition aliases read-only and queries their sizes.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"syscall"
	"unsafe"
)

func main() {
	if len(os.Args) != 1 || os.Geteuid() != 0 {
		fmt.Fprintln(os.Stderr, "probe requires UID0 and no arguments")
		os.Exit(1)
	}
	dt, err := os.ReadFile("/proc/device-tree/amlogic-dt-id")
	if err != nil || strings.Trim(string(dt), "\x00\r\n ") != "gxlx2_p291_1g" {
		fmt.Fprintln(os.Stderr, "unexpected device profile")
		os.Exit(1)
	}
	rows := []map[string]any{}
	for _, target := range []struct {
		path  string
		bytes uint64
		minor uint64
	}{{"/dev/block/env", 8388608, 4}, {"/dev/block/data", 3495952384, 20}} {
		f, err := os.Open(target.path)
		if err != nil {
			panic(err)
		}
		st, err := f.Stat()
		if err != nil {
			panic(err)
		}
		dev := uint64(st.Sys().(*syscall.Stat_t).Rdev)
		if st.Mode()&os.ModeDevice == 0 || st.Mode()&os.ModeCharDevice != 0 || ((dev>>8)&0xfff|(dev>>32)&0xfffff000) != 179 || (dev&255|(dev>>12)&0xffffff00) != target.minor {
			panic("unexpected block target")
		}
		var size, legacySize uint64
		request := blockSizeIOCTL(unsafe.Sizeof(uintptr(0)))
		_, _, legacyErr := syscall.Syscall(syscall.SYS_IOCTL, f.Fd(), 0x80081272, uintptr(unsafe.Pointer(&legacySize)))
		_, _, currentErr := syscall.Syscall(syscall.SYS_IOCTL, f.Fd(), request, uintptr(unsafe.Pointer(&size)))
		if err = f.Close(); err != nil {
			panic(err)
		}
		if currentErr != 0 || size != target.bytes {
			panic(fmt.Sprintf("query %s failed: size=%d errno=%d", target.path, size, currentErr))
		}
		rows = append(rows, map[string]any{"path": target.path, "bytes": size, "ioctl": fmt.Sprintf("%#x", request), "errno": int(currentErr), "legacy_errno": int(legacyErr), "legacy_size": legacySize, "opened_readonly": true})
	}
	if err = json.NewEncoder(os.Stdout).Encode(map[string]any{"state": "passed", "pointer_bytes": unsafe.Sizeof(uintptr(0)), "partitions": rows}); err != nil {
		panic(err)
	}
}
