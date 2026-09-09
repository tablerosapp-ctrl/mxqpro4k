"""Build extractor 0.3 ARM32 with CNV8b RK v3 trust, entirely on the PC.

The source directory 0.3 must be frozen before use. Existing output directories
are rejected and all failed attempts are retained. No media or TV is accessed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORE = ROOT / "diagnostico/extractor-recovery-0.3"
GO = ROOT / "tools/instalador-go/go/bin/go.exe"
JAVA = ROOT / "tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe"
ECJ = ROOT / "tools/compilar-android/ecj-3.39.0.jar"
HELPER = ROOT / "diagnostico/extractor-recovery-rk1/firma_ota_v3.py"
JAVA_SOURCE = ROOT / "diagnostico/extractor-recovery-rk1/VerifyWholeZip.java"
HELPER_SHA = "8a09a4e6963be53fc3f61ba267c99120fa4ef86ab6d149f62d9d220da945d6be"
JAVA_SOURCE_SHA = "5392c03a15969d3a18ef3406a159869a074a121ea3afbd58cb163fe0a8e016fa"
MATERIAL = ROOT / "privado/rockchip-cnv8b-20260908/firma-rk-publica"
CERT = MATERIAL / "testkey.x509.pem"
KEY = MATERIAL / "testkey.pk8"
KEYFILE = ROOT / "privado/rockchip-cnv8b-20260908/recovery-files/res--keys"
PRIOR_RK2 = ROOT / "privado/extractor-rk2-release-20260909-0138/TVBASE-EXTRACTOR-0.2-RK2-ARM32-RECOVERY.zip"
PRIOR_RK2_SHA = "3d9e6a18c023ccc4a355aab738537655049016634dcf855990b307aa619486cd"
VERSION = "0.3"
PACKAGE_ID = "TVBASE-EXTRACTOR-0.3-RK3-ARM32"
BINARY_ENTRY = "META-INF/com/google/android/update-binary"
META_ENTRY = "tvbase/extractor.json"
SCRIPT_ENTRY = "META-INF/com/google/android/updater-script"
CERT_ENTRY = "META-INF/com/android/otacert"
INVENTORY_SHA = "4191609c6241c99d7a6c9754de4aa95c78d7b264cc173d8551ff85c91c24258a"
CID_LINKER_SYMBOL = "main.rk3229CExpectedCID"
PRIOR_FAILURE = ROOT / "privado/extractor-rk3-build-20260909-01/FALLO.json"
PRIOR_FAILED_RECIPE = ROOT / "privado/extractor-rk3-build-20260909-01/compilar-fallido.py"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def save(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    require(Path(path).read_bytes() == data, "PC readback differs: " + relative(path))


def save_json(path, value):
    save(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def new_private_directory(value):
    path = (ROOT / value).resolve()
    require(path.is_relative_to(ROOT / "privado") and path != ROOT / "privado",
            "Use a new directory below privado")
    require(not path.exists(), "Keep prior attempts; output directory must not exist")
    return path


def identity_input(value):
    path = (ROOT / value).resolve()
    require(path.is_relative_to(ROOT / "privado") and path.is_file(), "Private inventory required")
    require(sha(path) == INVENTORY_SHA, "The captured RK3229-C recovery inventory differs")
    inventory = json.loads(path.read_text(encoding="utf-8"))
    require(inventory.get("schema") == "tvbase-recovery-inventory-1" and
            inventory.get("dt_identity") == "rockchip,rk3229", "Unexpected recovery inventory profile")
    cid_hash = inventory.get("emmc_identity_hashes", {}).get("mmcblk0_cid_sha256")
    require(isinstance(cid_hash, str) and re.fullmatch(r"[0-9a-f]{64}", cid_hash),
            "Missing private eMMC identity hash")
    require(cid_hash != "0" * 64, "Empty eMMC identity hash")
    return path, cid_hash


def sources():
    paths = sorted(CORE.glob("*.go"))
    require(paths and any(p.name.endswith("_test.go") for p in paths), "Missing core source/tests")
    require((CORE / "go.mod").is_file(), "Missing go.mod")
    for path in paths:
        require("//go:embed" not in path.read_text(encoding="utf-8"), "Unspecified embedded build input")
    paths += [CORE / "go.mod", Path(__file__).resolve()]
    if (CORE / "go.sum").exists():
        paths.append(CORE / "go.sum")
    return {relative(path): sha(path) for path in paths}


def load_signer():
    require(sha(HELPER) == HELPER_SHA, "Sealed RK1 signing helper differs")
    require(sha(JAVA_SOURCE) == JAVA_SOURCE_SHA, "Sealed RK1 Java source differs")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("tvbase_sealed_rk_v3", HELPER)
    require(spec is not None and spec.loader is not None, "Cannot import existing signer")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def inspect_elf(path):
    data = Path(path).read_bytes()
    require(len(data) >= 64 and data[:7] == b"\x7fELF\x01\x01\x01", "ARM32 little-endian ELF required")
    require(struct.unpack_from("<HHI", data, 16) == (2, 40, 1), "Native ARM ET_EXEC required")
    offset = struct.unpack_from("<I", data, 28)[0]
    flags = struct.unpack_from("<I", data, 36)[0]
    stride, count = struct.unpack_from("<HH", data, 42)
    require(flags >> 24 == 5 and flags & 0x400 == 0, "EABI5 without hard-float ABI required")
    require(stride == 32 and 0 < count < 128 and offset + count * stride <= len(data), "Invalid ELF program headers")
    types = [struct.unpack_from("<I", data, offset + i * stride)[0] for i in range(count)]
    require(1 in types and 2 not in types and 3 not in types, "Static ELF must have no PT_INTERP/PT_DYNAMIC")
    return dict(elf_class_bits=32, machine=40, type="ET_EXEC", little_endian=True, flags=flags,
                program_headers=count, pt_interp_absent=True, pt_dynamic_absent=True)


def verify_linked_identity(path, expected):
    """Read the actual Go string variable using its ELF32 symbol and PT_LOAD.

    trimpath omits ldflags from Go build info. Keep symbols (-w, without -s)
    and inspect the linked value instead of relying on a recorded command.
    The returned evidence never includes the private string or its address.
    """
    data = Path(path).read_bytes()
    inspect_elf(path)
    phoff, shoff = struct.unpack_from("<II", data, 28)
    phsize, phcount, shsize, shcount = struct.unpack_from("<HHHH", data, 42)
    require(phsize == 32 and shsize == 40 and 0 < shcount < 256,
            "Unexpected ELF header dimensions for binding verification")
    require(shoff + shcount * shsize <= len(data), "ELF sections outside file")
    sections = [struct.unpack_from("<10I", data, shoff + i * shsize) for i in range(shcount)]
    symtabs = [entry for entry in sections if entry[1] == 2]
    require(len(symtabs) == 1, "Exactly one static ELF symbol table required")
    symtab = symtabs[0]
    require(symtab[6] < shcount and symtab[9] == 16 and symtab[5] % 16 == 0,
            "ELF symbol table geometry invalid")
    require(symtab[4] + symtab[5] <= len(data), "ELF symbols outside file")
    strings = sections[symtab[6]]
    require(strings[1] == 3 and strings[4] + strings[5] <= len(data), "Invalid ELF symbol string table")
    names = data[strings[4]:strings[4] + strings[5]]
    found = []
    for offset in range(symtab[4], symtab[4] + symtab[5], 16):
        name_at, value, size, info, other, section_index = struct.unpack_from("<IIIBBH", data, offset)
        require(name_at < len(names), "ELF symbol name outside table")
        end = names.find(b"\0", name_at)
        require(end >= 0, "ELF symbol name not terminated")
        if names[name_at:end] == CID_LINKER_SYMBOL.encode():
            require(info & 15 == 1 and size == 8 and 0 < section_index < shcount,
                    "Private binding symbol is not an allocated Go string")
            require(sections[section_index][2] & 2 != 0, "Binding symbol section is not allocated")
            found.append(value)
    require(len(found) == 1, "Exact private binding symbol is absent or duplicated")
    loads = [struct.unpack_from("<8I", data, phoff + i * phsize) for i in range(phcount)]

    def at_virtual(address, length):
        matches = []
        for entry in loads:
            kind, file_offset, virtual, physical, file_size, memory_size, flags, align = entry
            if kind == 1 and virtual <= address and address + length <= virtual + file_size:
                start = file_offset + address - virtual
                require(start + length <= len(data), "Linked string data outside ELF")
                matches.append(data[start:start + length])
        require(len(matches) == 1, "Linked string not in exactly one file-backed load segment")
        return matches[0]

    pointer, length = struct.unpack("<II", at_virtual(found[0], 8))
    require(length == 64 and at_virtual(pointer, length) == expected.encode(),
            "Linked identity string differs from private inventory")
    return dict(method="ELF32_symbol_Go_string_pointer_and_length_PT_LOAD",
                exact_symbol_verified=True, exact_private_value_verified=True,
                value_bytes=length, value_published=False)


def build(build_dir, output_dir, inventory_file, cid_hash):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    require(os.name == "nt", "This recipe requires the existing Windows toolchain")
    require(not build_dir.is_relative_to(output_dir) and not output_dir.is_relative_to(build_dir), "Separate build/output directories required")
    tool_paths = (GO, JAVA, ECJ, HELPER, JAVA_SOURCE, CERT, KEYFILE, PRIOR_RK2, inventory_file,
                  PRIOR_FAILURE, PRIOR_FAILED_RECIPE)
    for path in tool_paths + (KEY,):
        require(path.is_file(), "Missing local input: " + relative(path))
    helper = load_signer()
    require(sha(CERT) == "10a7b524d14750a12b44472524340df6b300f1b648fb63c3b17a161bde1e08d7", "Rockchip certificate changed")
    require(sha(KEY) == "6062eea9d9d0c993906564ca644ef7b1ada2d2038bffb7343ac78b7714c955e7", "Rockchip key changed")
    require(sha(PRIOR_RK2) == PRIOR_RK2_SHA, "Sealed predecessor changed")
    require(sha(PRIOR_FAILURE) == "7af66c06ff0ee758fb4b6a44b17b272718c5973cd325b0715fcbac41232530ae" and
            sha(PRIOR_FAILED_RECIPE) == "fc858dfe736742459cb2bdc3db40fee45709b214c5193d3b9f0b101a0824c5bb",
            "Preserved first failed build evidence changed")
    cert = x509.load_pem_x509_certificate(CERT.read_bytes())
    trust = helper.trust_cnv8b_v3_key(KEYFILE, cert)
    source_hashes = sources()
    require((CORE / "source_policy.go").is_file() and
            'var rk3229CExpectedCID = ""' in (CORE / "source_policy.go").read_text(encoding="utf-8"),
            "Core linker variable is not the reviewed string binding")
    for name in source_hashes:
        require(cid_hash.encode() not in (ROOT / name).read_bytes(), "Private identity embedded in public source")
    tool_hashes = {relative(path): sha(path) for path in tool_paths}
    build_dir.mkdir(parents=True, exist_ok=False)
    output_dir.mkdir(parents=True, exist_ok=False)
    logs = []

    def run(args, name, env=None, success=True, cwd=CORE):
        result = subprocess.run([str(arg) for arg in args], cwd=cwd, env=env,
                                capture_output=True, creationflags=0x08000000)
        log = build_dir / name
        save(log, result.stdout + result.stderr)
        logs.append(dict(file=relative(log), exit=result.returncode, sha256=sha(log)))
        require((result.returncode == 0) == success, "Unexpected command result: " + relative(log))
        return result.stdout.decode("utf-8", errors="strict")

    try:
        env = os.environ.copy()
        env.update(GOROOT=str(GO.parents[1]), GOCACHE=str(build_dir / "go-cache"),
                   GOMODCACHE=str(build_dir / "go-mod-cache"), GOTMPDIR=str(build_dir / "go-tmp"),
                   GOPATH=str(build_dir / "go-path"), GOCACHEPROG="", GOPROXY="off", GOSUMDB="off",
                   GOTOOLCHAIN="local", GOWORK="off", GOENV="off", GO111MODULE="on", GOFLAGS="",
                   GOEXPERIMENT="", CGO_ENABLED="0", GOOS="windows", GOARCH="amd64", GOARM="", GOARM64="")
        (build_dir / "go-tmp").mkdir()
        go_version = run([GO, "version"], "go-version.log", env).strip()
        text = run([GO, "test", "-mod=readonly", "-count=1", "-json", "."], "go-tests.jsonl", env)
        events = [json.loads(line) for line in text.splitlines() if line.startswith("{")]
        passed = [row["Test"] for row in events if row.get("Action") == "pass" and "Test" in row]
        require(passed and not any(row.get("Action") == "fail" for row in events), "Host tests must run and pass")
        env.update(GOOS="linux", GOARCH="arm", GOARM="5", GOARM64="")
        binary = build_dir / "update-binary"
        linux_tests = build_dir / "linux-tests-not-executed"
        binding = CID_LINKER_SYMBOL + "=" + cid_hash
        run([GO, "build", "-mod=readonly", "-trimpath", "-buildvcs=false", "-ldflags=-w -X " + binding, "-o", binary, "."], "arm32-compile.log", env)
        run([GO, "test", "-mod=readonly", "-c", "-o", linux_tests, "."], "arm32-tests-compile.log", env)
        elf = inspect_elf(binary)
        build_info = run([GO, "version", "-m", binary], "arm32-build-info.log", env)
        for setting in ("CGO_ENABLED=0", "GOOS=linux", "GOARCH=arm", "GOARM=5"):
            require(setting in build_info, "Missing build setting " + setting)
        binding_verification = verify_linked_identity(binary, cid_hash)
        save_json(build_dir / "PRIVATE-BINDING.json", dict(
            schema="tvbase-rk3229-c-private-build-binding-1", inventory=relative(inventory_file),
            inventory_sha256=INVENTORY_SHA, cid_sha256=cid_hash, linker_symbol=CID_LINKER_SYMBOL,
            binary_sha256=sha(binary), public_disclosure=False))
        metadata = dict(
            schema="tvbase-recovery-extractor-1", version=VERSION, package_id=PACKAGE_ID,
            package_variant="RK3", operation="capture_read_only", architecture="ARM32",
            goos="linux", goarch="arm", goarm="5", cgo_enabled=False,
            media_directory="TVBASE-EXTRACCION", media_config="MEDIA.json",
            media_schema="tvbase-recovery-media-1", media_id="tvbase-recovery-sd-rk3229-c-20260909",
            destination="same_external_sd_as_package", package_path="/mnt/external_sd/update.zip",
            destination_fs="vfat", destination_requires_rw_mount=True,
            destination_requires_physical_sd_proof=True, usb_fallback=False,
            device_images_in_package=False, default_capture="inventory_only",
            image_capture_requires_matching_apk_plan=True, plans_directory="PLANES",
            plan_schema="tvbase-recovery-plan-1", plan_source="validated_android_recognition_capture",
            plan_match="exact_dt_identity", source_sha256=source_hashes, extractor_sha256=sha(binary),
            source_policy="rk3229-c-backup-last-1",
            source_policy_deferred_source="mmcblk0p10",
            source_policy_deferred_position="last",
            source_policy_deferred_reason="observed_source_changed_during_reread",
            whole_user_area_allowed=False,
            source_policy_requires_exact_recovery_layout=True,
            source_policy_requires_exact_private_emmc_cid=True,
            private_identity_value_in_metadata=False,
            source_verification="ordinary_sources:copy_destination_source;deferred_backup:source_source_destination",
            deferred_backup_variant="two_matching_source_reads_in_ram_before_writing_sd",
            deferred_backup_bytes=67108864,
            deferred_backup_memory_budget_bytes=134217728,
            deferred_backup_fallback_minimum_memtotal_bytes=536870912,
            source_hash_mismatch_always_fatal=True,
            recovery_execution_tested=False,
            signature_scope="CNV8b recovery v3/RSA-SHA256 development trust; new RK3 package physical acceptance pending",
            predecessor_package_sha256=PRIOR_RK2_SHA,
        )
        entries = {
            BINARY_ENTRY: binary.read_bytes(),
            META_ENTRY: (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode(),
            SCRIPT_ENTRY: b'ui_print("TV Base extractor 0.3: solo lectura; destino SD validado; no instala ROM");\n',
            CERT_ENTRY: cert.public_bytes(serialization.Encoding.PEM),
        }
        require(cid_hash.encode() not in entries[META_ENTRY], "Private eMMC identity leaked into metadata")
        unsigned = build_dir / "unsigned.zip"
        with zipfile.ZipFile(unsigned, "x", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as archive:
            for name, data in entries.items():
                info = zipfile.ZipInfo(name, (2026, 9, 9, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if name == BINARY_ENTRY else 0o100644) << 16
                archive.writestr(info, data)
        final = output_dir / (PACKAGE_ID + "-RECOVERY.zip")
        key = serialization.load_der_private_key(KEY.read_bytes(), password=None)
        signature = helper.sign_zip(unsigned, final, cert, key)
        del key
        require(helper.verify_zip(final, cert) == signature, "Signature replay differs")
        with zipfile.ZipFile(final) as archive:
            require(len(archive.infolist()) == len(entries) and set(archive.namelist()) == set(entries), "Unexpected ZIP members")
            require(archive.testzip() is None, "CRC failure")
            for name, data in entries.items():
                require(archive.read(name) == data, "Member differs: " + name)
            require(archive.getinfo(BINARY_ENTRY).external_attr >> 16 == 0o100755, "Executable mode differs")
        java_out = build_dir / "java"
        java_out.mkdir()
        run([JAVA, "-jar", ECJ, "-8", "-encoding", "UTF-8", "-d", java_out, JAVA_SOURCE], "java-compile.log")
        java_args = [JAVA, "-Xmx128m", "--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED",
                     "--add-exports=java.base/sun.security.x509=ALL-UNNAMED", "-cp", java_out, "VerifyWholeZip"]
        java_positive = run(java_args + [final, CERT], "java-positive.log")
        require("OpenJDK PKCS7 whole-file RSA/SHA256 signature verified" in java_positive, "Missing independent signature confirmation")
        negative_tests = []

        def reject(name, action):
            try:
                action()
            except Exception as exc:
                negative_tests.append(dict(name=name, rejected=True, exception=type(exc).__name__))
            else:
                raise ValueError("Negative test incorrectly accepted: " + name)

        old_cert_file = ROOT / "tools/firmar-ota/testkey.x509.pem"
        old_cert = x509.load_pem_x509_certificate(old_cert_file.read_bytes())
        reject("P291 certificate incompatible with RK v3", lambda: helper.trust_cnv8b_v3_key(KEYFILE, old_cert))
        reject("RK3 package with P291 certificate", lambda: helper.verify_zip(final, old_cert))
        broken = bytearray(final.read_bytes())
        broken[64] ^= 1
        tampered = build_dir / "negative-content.zip"
        save(tampered, broken)
        reject("signed content corruption", lambda: helper.verify_zip(tampered, cert))
        run(java_args + [tampered, CERT], "java-negative-content.log", success=False)
        run(java_args + [final, old_cert_file], "java-negative-trust.log", success=False)
        broken = bytearray(final.read_bytes())
        broken[-3] ^= 1
        footer = build_dir / "negative-footer.zip"
        save(footer, broken)
        reject("OTA footer corruption", lambda: helper.verify_zip(footer, cert))
        require(sources() == source_hashes, "Sources changed during build")
        require({relative(path): sha(path) for path in tool_paths} == tool_hashes, "Immutable input changed during build")
        require(sha(KEY) == "6062eea9d9d0c993906564ca644ef7b1ada2d2038bffb7343ac78b7714c955e7", "Signing key changed during build")
        receipt = dict(
            schema="tvbase-extractor-rk3-build-1", state="verified_pc",
            version=VERSION, extractor_version=VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
            source_directory=relative(CORE), build_directory=relative(build_dir), output_directory=relative(output_dir),
            package=final.name, package_file=relative(final), bytes=final.stat().st_size, sha256=sha(final),
            binary=relative(binary), binary_bytes=binary.stat().st_size, binary_sha256=sha(binary), extractor_sha256=sha(binary),
            sources=source_hashes, sources_unchanged=True, immutable_inputs=tool_hashes,
            identity_binding=dict(inventory_sha256=INVENTORY_SHA, linker_symbol=CID_LINKER_SYMBOL,
                                  required=True, embedded_in_private_binary=True,
                                  linked_value_verification=binding_verification, value_published=False),
            prior_failed_attempt=dict(receipt=relative(PRIOR_FAILURE), receipt_sha256=sha(PRIOR_FAILURE),
                                      recipe=relative(PRIOR_FAILED_RECIPE), recipe_sha256=sha(PRIOR_FAILED_RECIPE),
                                      explanation="Go trimpath omitted ldflags from build info; first guard falsely rejected before signing. Replaced by exact ELF symbol value verification.",
                                      failed_attempt_preserved=True, failed_package_delivered=False),
            immutable_inputs_unchanged=True, go_version=go_version,
            go_host_tests=dict(os="windows", arch="amd64", count=len(passed), passed=passed),
            linux_tests_compiled=True, linux_tests_sha256=sha(linux_tests), linux_tests_executed=False,
            elf=elf, metadata=metadata, trust=trust, signature=signature, negative_tests=negative_tests,
            command_logs=logs, java_class_sha256=sha(java_out / "VerifyWholeZip.class"),
            members=[dict(name=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in entries.items()],
            python_verified=True, openjdk_verified=True, crc_verified=True,
            physical_acceptance=False, physical_extraction=False, sd_written=False, usb_written=False,
            tv_contacted=False,
            limits=["RK2 executed and copied blocks on the target, then rejected changed backup p10; new RK3 not executed on a TV",
                    "Public development key is laboratory compatibility, not production update security",
                    "Host tests and compiled Linux tests do not demonstrate sysfs/mount proof on this physical recovery",
                    "Read-only capture does not mount, reformat, flash or reboot; recovery can write its own logs",
                    "No restoration or atomic snapshot is implemented; unavailable or busy sources may be omitted"],
        )
        require(cid_hash not in json.dumps(receipt, ensure_ascii=False), "Private eMMC identity leaked into public receipt")
        save_json(output_dir / "COMPILACION.json", receipt)
        save_json(build_dir / "RESULTADO.json", dict(state="verified_pc", receipt=relative(output_dir / "COMPILACION.json"), sha256=sha(output_dir / "COMPILACION.json")))
        print(json.dumps({key: receipt[key] for key in ("state", "package", "bytes", "sha256", "binary_sha256", "physical_acceptance")}, indent=2))
    except Exception as exc:
        save_json(build_dir / "FALLO.json", dict(state="failed_preserved", error_type=type(exc).__name__, error=str(exc),
                                               command_logs=logs, output_must_not_be_delivered=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--inventory", required=True, help="Private, hash-pinned inventory from the failed RK2 extraction")
    args = parser.parse_args()
    inventory_file, cid_hash = identity_input(args.inventory)
    build(new_private_directory(args.build_dir), new_private_directory(args.output_dir), inventory_file, cid_hash)


if __name__ == "__main__":
    main()
