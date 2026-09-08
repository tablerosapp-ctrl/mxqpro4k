package main

import "testing"

func TestBlockSizeIOCTLArchitecture(t *testing.T) {
	for _, fixture := range []struct{ pointerBytes, request uintptr }{
		{4, 0x80041272}, // Linux ARM32, including a 32-bit process on ARM64.
		{8, 0x80081272}, // Linux native 64-bit ABI.
	} {
		if actual := blockSizeIOCTL(fixture.pointerBytes); actual != fixture.request {
			t.Fatalf("pointer bytes %d: ioctl %#x, expected %#x", fixture.pointerBytes, actual, fixture.request)
		}
	}
}
