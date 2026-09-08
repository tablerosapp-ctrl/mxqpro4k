//go:build linux

package main

import (
	"fmt"
	"os"
)

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
