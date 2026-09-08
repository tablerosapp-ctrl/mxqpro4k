package main

import (
	"encoding/binary"
	"hash/crc32"
	"strings"
	"testing"
)

func environmentFixture(entries []string) []byte {
	record := make([]byte, 65536)
	copy(record[4:], []byte(strings.Join(entries, "\x00")+"\x00\x00"))
	binary.LittleEndian.PutUint32(record, crc32.ChecksumIEEE(record[4:]))
	return record
}
func goodEnvEntries() []string {
	return []string{"bootcmd=" + normalBootCommand, "preboot=" + originalPreboot, "recovery_from_flash=" + originalRecoveryCommand, "recovery_part=recovery", "recovery_offset=0", "runtime_variable=allowed after saveenv", "irremote_update=original\nline"}
}
func TestNormalEnvironmentAndRuntimeVariables(t *testing.T) {
	if e := requireNormalBootEnvironment(environmentFixture(goodEnvEntries())); e != nil {
		t.Fatal(e)
	}
}
func TestPendingRecoveryAndMalformedEnvironmentStopBeforeFormat(t *testing.T) {
	for _, name := range []string{"pending-command", "changed-preboot", "changed-recovery", "changed-partition", "duplicate", "bad-crc", "short", "padding"} {
		t.Run(name, func(t *testing.T) {
			entries := goodEnvEntries()
			switch name {
			case "pending-command":
				entries[0] = "bootcmd=if setenv bootcmd 'run storeboot'; then if saveenv; then run recovery_from_flash; run storeboot; else run storeboot; fi; else run storeboot; fi"
			case "changed-preboot":
				entries[1] = "preboot=run something_else"
			case "changed-recovery":
				entries[2] = "recovery_from_flash=run another"
			case "changed-partition":
				entries[3] = "recovery_part=boot"
			case "duplicate":
				entries = append(entries, "bootcmd=run storeboot")
			}
			record := environmentFixture(entries)
			switch name {
			case "bad-crc":
				record[0] ^= 1
			case "short":
				record = record[:65535]
			case "padding":
				record[len(record)-1] = 1
				binary.LittleEndian.PutUint32(record, crc32.ChecksumIEEE(record[4:]))
			}
			if requireNormalBootEnvironment(record) == nil {
				t.Fatal("unsafe environment accepted")
			}
		})
	}
}
