//go:build windows

package main

import (
	"fmt"
	"os"
)

// The Windows build can only verify a package; all device-writing code is Linux-only.
func main() {
	if len(os.Args) != 2 {
		panic("ruta del ZIP requerida")
	}
	p, e := loadPackage(os.Args[1])
	if e != nil {
		panic(e)
	}
	defer p.ZIP.Close()
	if e = p.verify(); e != nil {
		panic(e)
	}
	fmt.Println("Manifest and all five raw partition images accepted by the installer verifier")
}
