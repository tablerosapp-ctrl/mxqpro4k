"""Build extractor 0.2 ARM32 with CNV8b RK v3 trust, entirely on the PC.

The source directory 0.2 must be frozen before use. Existing output directories
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
import struct
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORE = ROOT / "diagnostico/extractor-recovery-0.2"
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
PRIOR_RK1 = ROOT / "privado/extractor-rk1-20260908/TVBASE-EXTRACTOR-0.1-RK1-ARM32-RECOVERY.zip"
PRIOR_RK1_SHA = "0f7fe7a5f609290f69597c599ac8c72954b4fc7e04957cd27b279a368f060c38"
VERSION = "0.2"
PACKAGE_ID = "TVBASE-EXTRACTOR-0.2-RK2-ARM32"
BINARY_ENTRY = "META-INF/com/google/android/update-binary"
META_ENTRY = "tvbase/extractor.json"
SCRIPT_ENTRY = "META-INF/com/google/android/updater-script"
CERT_ENTRY = "META-INF/com/android/otacert"


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


def build(build_dir, output_dir):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    require(os.name == "nt", "This recipe requires the existing Windows toolchain")
    require(not build_dir.is_relative_to(output_dir) and not output_dir.is_relative_to(build_dir), "Separate build/output directories required")
    tool_paths = (GO, JAVA, ECJ, HELPER, JAVA_SOURCE, CERT, KEYFILE, PRIOR_RK1)
    for path in tool_paths + (KEY,):
        require(path.is_file(), "Missing local input: " + relative(path))
    helper = load_signer()
    require(sha(CERT) == "10a7b524d14750a12b44472524340df6b300f1b648fb63c3b17a161bde1e08d7", "Rockchip certificate changed")
    require(sha(KEY) == "6062eea9d9d0c993906564ca644ef7b1ada2d2038bffb7343ac78b7714c955e7", "Rockchip key changed")
    require(sha(PRIOR_RK1) == PRIOR_RK1_SHA, "Sealed predecessor changed")
    cert = x509.load_pem_x509_certificate(CERT.read_bytes())
    trust = helper.trust_cnv8b_v3_key(KEYFILE, cert)
    source_hashes = sources()
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
        run([GO, "build", "-mod=readonly", "-trimpath", "-buildvcs=false", "-ldflags=-s -w", "-o", binary, "."], "arm32-compile.log", env)
        run([GO, "test", "-mod=readonly", "-c", "-o", linux_tests, "."], "arm32-tests-compile.log", env)
        elf = inspect_elf(binary)
        build_info = run([GO, "version", "-m", binary], "arm32-build-info.log", env)
        for setting in ("CGO_ENABLED=0", "GOOS=linux", "GOARCH=arm", "GOARM=5"):
            require(setting in build_info, "Missing build setting " + setting)
        metadata = dict(
            schema="tvbase-recovery-extractor-1", version=VERSION, package_id=PACKAGE_ID,
            package_variant="RK2", operation="capture_read_only", architecture="ARM32",
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
            recovery_execution_tested=False,
            signature_scope="CNV8b recovery v3/RSA-SHA256 development trust; new RK2 package physical acceptance pending",
            predecessor_package_sha256=PRIOR_RK1_SHA,
        )
        entries = {
            BINARY_ENTRY: binary.read_bytes(),
            META_ENTRY: (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode(),
            SCRIPT_ENTRY: b'ui_print("TV Base extractor 0.2: solo lectura; destino SD validado; no instala ROM");\n',
            CERT_ENTRY: cert.public_bytes(serialization.Encoding.PEM),
        }
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
        reject("RK2 package with P291 certificate", lambda: helper.verify_zip(final, old_cert))
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
            schema="tvbase-extractor-rk2-build-1", state="verified_pc",
            version=VERSION, extractor_version=VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
            source_directory=relative(CORE), build_directory=relative(build_dir), output_directory=relative(output_dir),
            package=final.name, package_file=relative(final), bytes=final.stat().st_size, sha256=sha(final),
            binary=relative(binary), binary_bytes=binary.stat().st_size, binary_sha256=sha(binary), extractor_sha256=sha(binary),
            sources=source_hashes, sources_unchanged=True, immutable_inputs=tool_hashes,
            immutable_inputs_unchanged=True, go_version=go_version,
            go_host_tests=dict(os="windows", arch="amd64", count=len(passed), passed=passed),
            linux_tests_compiled=True, linux_tests_sha256=sha(linux_tests), linux_tests_executed=False,
            elf=elf, metadata=metadata, trust=trust, signature=signature, negative_tests=negative_tests,
            command_logs=logs, java_class_sha256=sha(java_out / "VerifyWholeZip.class"),
            members=[dict(name=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in entries.items()],
            python_verified=True, openjdk_verified=True, crc_verified=True,
            physical_acceptance=False, physical_extraction=False, sd_written=False, usb_written=False,
            tv_contacted=False,
            limits=["RK1 executed on the target; this changed RK2 binary/package has not been executed on a TV",
                    "Public development key is laboratory compatibility, not production update security",
                    "Host tests and compiled Linux tests do not demonstrate sysfs/mount proof on this physical recovery",
                    "Read-only capture does not mount, reformat, flash or reboot; recovery can write its own logs",
                    "No restoration or atomic snapshot is implemented; unavailable or busy sources may be omitted"],
        )
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
    args = parser.parse_args()
    build(new_private_directory(args.build_dir), new_private_directory(args.output_dir))


if __name__ == "__main__":
    main()
