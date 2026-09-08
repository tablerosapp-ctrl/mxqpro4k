//go:build linux

package main

import (
	"fmt"
	"os"
)

func checkBootEnvironment(disk string) error {
	size, r, actual, e := block("/dev/block/env")
	if e != nil {
		return e
	}
	if size != 8388608 || mm(r) != "179:4" || actual != disk {
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
