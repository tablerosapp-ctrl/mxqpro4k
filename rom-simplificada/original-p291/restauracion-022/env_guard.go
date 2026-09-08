package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"regexp"
)

const normalBootCommand = "run storeboot"
const originalPreboot = "run factory_reset_poweroff_protect;run init_display;run upgrade_check;run storeargs;run upgrade_sadckey;run switch_bootmode;"
const originalRecoveryCommand = "setenv bootargs ${bootargs} aml_dt=${aml_dt} recovery_part={recovery_part} recovery_offset={recovery_offset};if imgread kernel ${recovery_part} ${loadaddr} ${recovery_offset}; then bootm ${loadaddr}; fi"

func requireNormalBootEnvironment(record []byte) error {
	if len(record) != 65536 {
		return fmt.Errorf("registro ENV incompleto")
	}
	if crc32.ChecksumIEEE(record[4:]) != binary.LittleEndian.Uint32(record) {
		return fmt.Errorf("CRC32 de ENV incorrecto")
	}
	end := bytes.Index(record[4:], []byte{0, 0})
	if end <= 0 {
		return fmt.Errorf("ENV sin terminador doble")
	}
	end += 4
	for _, b := range record[end+2:] {
		if b != 0 {
			return fmt.Errorf("relleno de registro ENV inesperado")
		}
	}
	values := map[string]string{}
	keyPattern := regexp.MustCompile(`^[A-Za-z0-9_]+$`)
	for _, entry := range bytes.Split(record[4:end], []byte{0}) {
		pair := bytes.SplitN(entry, []byte{'='}, 2)
		if len(pair) != 2 || !keyPattern.Match(pair[0]) {
			return fmt.Errorf("clave ENV incorrecta")
		}
		name := string(pair[0])
		if _, exists := values[name]; exists {
			return fmt.Errorf("clave ENV duplicada")
		}
		for _, b := range pair[1] {
			if b != 10 && (b < 32 || b > 126) {
				return fmt.Errorf("valor ENV no ASCII")
			}
		}
		values[name] = string(pair[1])
	}
	if values["bootcmd"] != normalBootCommand {
		return fmt.Errorf("entrada temporal a recovery aun pendiente; conservar el menu y no formatear")
	}
	if values["preboot"] != originalPreboot || values["recovery_from_flash"] != originalRecoveryCommand || values["recovery_part"] != "recovery" || values["recovery_offset"] != "0" {
		return fmt.Errorf("flujo de arranque/recovery difiere del original revisado")
	}
	return nil
}
