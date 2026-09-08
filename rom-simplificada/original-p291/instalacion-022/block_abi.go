package main

// Linux BLKGETSIZE64 encodes sizeof(size_t), although its output is uint64.
// ARM32/compat therefore needs 0x80041272, not the native 64-bit command.
func blockSizeIOCTL(pointerBytes uintptr) uintptr {
	return 0x80001272 | (pointerBytes << 16)
}
