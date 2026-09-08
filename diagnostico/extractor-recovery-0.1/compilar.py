"""Build and verify two recovery extraction ZIPs locally; never access a TV or USB.

Both --build-dir and --output-dir must name NEW directories inside this project.
Existing attempts and receipts are preserved. No signing material is printed.
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
VERSION = "0.1"
GO = ROOT / "tools/instalador-go/go/bin/go.exe"
JAVA = ROOT / "tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe"
ECJ = ROOT / "tools/compilar-android/ecj-3.39.0.jar"
PRIOR = ROOT / "rom-simplificada/original-p291/instalacion-022"
HELPER = PRIOR / "firma_ota_v1.py"
JAVA_SOURCE = PRIOR / "VerifyWholeZip.java"
HELPER_SHA256 = "aeb2b7d212e6472a9334c3ce7586effff3d7dc767266cb35233c25e02dc3f54e"
JAVA_SOURCE_SHA256 = "b9380030c31be175756c8f29bf74d88476b8d6154201e3ceca11bd3389fd7de8"
SIGNING = ROOT / "tools/firmar-ota"
CERT = SIGNING / "testkey.x509.pem"
KEY = SIGNING / "testkey.pk8"
RECOVERY_KEYS = ROOT / "diagnostico/primer-tv-lan-20260907-184926/privado/recovery-original-analisis/res--keys"
BINARY_ENTRY = "META-INF/com/google/android/update-binary"
META_ENTRY = "tvbase/extractor.json"
SCRIPT_ENTRY = "META-INF/com/google/android/updater-script"
CERT_ENTRY = "META-INF/com/android/otacert"
TARGETS = (
    {"name": "ARM32", "arch": "arm", "goarm": "5", "goarm64": "", "elf_class": 1, "machine": 40},
    {"name": "ARM64", "arch": "arm64", "goarm": "", "goarm64": "v8.0", "elf_class": 2, "machine": 183},
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def new_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def new_directory_path(value):
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    require(path.is_relative_to(ROOT) and path != ROOT, "Output must stay inside the project")
    require(not path.exists(), "Refusing an existing directory; keep this attempt and choose a new one")
    require(not HERE.is_relative_to(path), "Output cannot be an ancestor of the source directory")
    return path


def sources():
    paths = sorted(HERE.glob("*.go"))
    require(paths and (HERE / "go.mod").is_file(), "Missing extractor Go sources or go.mod")
    require(any(path.name.endswith("_test.go") for path in paths), "Extractor host tests are required")
    for path in paths:
        require("//go:embed" not in path.read_text(encoding="utf-8"), "Embedded inputs require an explicit build contract")
    paths += [HERE / "go.mod", Path(__file__).resolve()]
    if (HERE / "go.sum").exists():
        paths.append(HERE / "go.sum")
    return {relative(path): sha(path) for path in paths}


def inspect_elf(path, target):
    data = Path(path).read_bytes()
    require(len(data) >= 64 and data[:4] == b"\x7fELF", "Missing ELF header")
    require(data[4] == target["elf_class"] and data[5:7] == b"\x01\x01", "Wrong ELF class, byte order, or version")
    require(struct.unpack_from("<HHI", data, 16) == (2, target["machine"], 1), "Expected a native static executable for the selected ABI")
    if target["elf_class"] == 1:
        offset = struct.unpack_from("<I", data, 28)[0]
        flags = struct.unpack_from("<I", data, 36)[0]
        stride, count = struct.unpack_from("<HH", data, 42)
        expected_stride = 32
        require(flags >> 24 == 5 and flags & 0x400 == 0, "ARM32 must use EABI5 without the hard-float ABI flag")
    else:
        offset = struct.unpack_from("<Q", data, 32)[0]
        flags = struct.unpack_from("<I", data, 48)[0]
        stride, count = struct.unpack_from("<HH", data, 54)
        expected_stride = 56
    require(stride == expected_stride and 0 < count < 128 and offset + count * stride <= len(data), "Invalid ELF program-header table")
    types = [struct.unpack_from("<I", data, offset + index * stride)[0] for index in range(count)]
    require(1 in types and 2 not in types and 3 not in types, "Binary must have load segments and no PT_DYNAMIC or PT_INTERP")
    return {"elf_class_bits": 32 if data[4] == 1 else 64, "machine": target["machine"],
            "type": "ET_EXEC", "little_endian": True, "flags": flags,
            "program_headers": count, "pt_interp_absent": True, "pt_dynamic_absent": True}


def load_signer():
    require(sha(HELPER) == HELPER_SHA256, "Immutable signing helper changed")
    require(sha(JAVA_SOURCE) == JAVA_SOURCE_SHA256, "Immutable OpenJDK verifier source changed")
    # Do not create __pycache__ beside the immutable 0.2.2 sources.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("tvbase_existing_ota_v1", HELPER)
    require(spec is not None and spec.loader is not None, "Cannot load existing signing helper")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def build(build_dir, output_dir):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    require(os.name == "nt", "This recipe uses the existing Windows Go/OpenJDK toolchain")
    for path in (GO, JAVA, ECJ, HELPER, JAVA_SOURCE, CERT, KEY, RECOVERY_KEYS):
        require(path.is_file(), "Missing required local build input: " + relative(path))
    require(not build_dir.is_relative_to(output_dir) and not output_dir.is_relative_to(build_dir), "Build and output directories must be separate")
    source_hashes = sources()
    helper = load_signer()
    cert = x509.load_pem_x509_certificate(CERT.read_bytes())
    trust = helper.trust_original_v1_key(RECOVERY_KEYS, cert)
    private_key_hash = sha(KEY)
    tool_paths = (GO, JAVA, ECJ, HELPER, JAVA_SOURCE, CERT, RECOVERY_KEYS)
    tool_hashes = {relative(path): sha(path) for path in tool_paths}
    build_dir.mkdir(parents=True, exist_ok=False)
    output_dir.mkdir(parents=True, exist_ok=False)
    logs = []

    def run(args, name, env=None):
        log = build_dir / name
        require(not log.exists(), "Refusing to overwrite a command log")
        process = subprocess.run([str(arg) for arg in args], cwd=HERE, env=env,
                                 capture_output=True, creationflags=0x08000000)
        with log.open("xb") as stream:
            stream.write(process.stdout)
            stream.write(process.stderr)
            stream.flush()
            os.fsync(stream.fileno())
        logs.append({"file": relative(log), "sha256": sha(log), "exit": process.returncode})
        require(process.returncode == 0, "Build command failed; inspect " + relative(log))
        return process.stdout.decode("utf-8", errors="strict")

    try:
        env = os.environ.copy()
        env.update(GOROOT=str(GO.parents[1]), GOCACHE=str(build_dir / "go-cache"),
                   GOMODCACHE=str(build_dir / "go-mod-cache"), GOTMPDIR=str(build_dir / "go-tmp"),
                   GOPATH=str(build_dir / "go-path"), GOCACHEPROG="",
                   GOPROXY="off", GOSUMDB="off", GOTOOLCHAIN="local", GOWORK="off", GOENV="off",
                   GO111MODULE="on", GOFLAGS="", GOEXPERIMENT="", CGO_ENABLED="0",
                   GOOS="windows", GOARCH="amd64", GOARM="", GOARM64="")
        (build_dir / "go-tmp").mkdir()
        go_version = run([GO, "version"], "go-version.log", env).strip()
        test_output = run([GO, "test", "-mod=readonly", "-count=1", "-json", "."], "go-tests.jsonl", env)
        events = [json.loads(line) for line in test_output.splitlines() if line.startswith("{")]
        passed = [row["Test"] for row in events if row.get("Action") == "pass" and "Test" in row]
        require(passed and not any(row.get("Action") == "fail" for row in events), "Host tests must run and pass")
        java_out = build_dir / "openjdk"
        java_out.mkdir()
        run([JAVA, "-jar", ECJ, "-8", "-encoding", "UTF-8", "-d", java_out, JAVA_SOURCE], "openjdk-compile.log")
        records = []
        for target in TARGETS:
            target_dir = build_dir / target["name"]
            target_dir.mkdir()
            env.update(GOOS="linux", GOARCH=target["arch"], GOARM=target["goarm"], GOARM64=target["goarm64"])
            binary = target_dir / "update-binary"
            run([GO, "build", "-mod=readonly", "-trimpath", "-buildvcs=false", "-ldflags=-s -w", "-o", binary, "."], target["name"] + "-compile.log", env)
            linux_tests = target_dir / "tests-not-executed"
            run([GO, "test", "-mod=readonly", "-c", "-o", linux_tests, "."], target["name"] + "-test-compile.log", env)
            elf = inspect_elf(binary, target)
            build_info = run([GO, "version", "-m", binary], target["name"] + "-build-info.log", env)
            for setting in ("CGO_ENABLED=0", "GOOS=linux", "GOARCH=" + target["arch"]):
                require(setting in build_info, "Build information lacks " + setting)
            if target["goarm"]:
                require("GOARM=5" in build_info, "ARM32 build did not use GOARM=5")
            else:
                require("GOARM64=v8.0" in build_info, "ARM64 build did not use baseline ARMv8.0")
            metadata = {
                "schema": "tvbase-recovery-extractor-1", "version": VERSION,
                "package_id": "TVBASE-EXTRACTOR-" + VERSION + "-" + target["name"],
                "operation": "capture_read_only", "architecture": target["name"],
                "goos": "linux", "goarch": target["arch"], "goarm": target["goarm"],
                "goarm64": target["goarm64"], "cgo_enabled": False,
                "recovery_arguments": ["api_version_1_2_or_3", "status_fd", "package_zip_path"],
                "media_directory": "TVBASE-EXTRACCION", "media_config": "MEDIA.json",
                "media_schema": "tvbase-recovery-media-1", "device_images_in_package": False,
                "default_capture": "inventory_only", "image_capture_requires_matching_apk_plan": True,
                "plans_directory": "PLANES", "plan_schema": "tvbase-recovery-plan-1",
                "plan_source": "validated_android_recognition_capture", "plan_match": "exact_dt_identity",
                "extractor_sha256": sha(binary), "source_sha256": source_hashes,
                "recovery_execution_tested": False,
                "signature_scope": "Original P291 recovery v1 key; other recovery trust is unverified",
            }
            unsigned = target_dir / "unsigned.zip"
            final = output_dir / (metadata["package_id"] + "-RECOVERY.zip")
            entries = {
                BINARY_ENTRY: binary.read_bytes(),
                META_ENTRY: (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                SCRIPT_ENTRY: b'ui_print("TV Base extractor: inventario; imagenes solo con plan APK coincidente");\n',
                CERT_ENTRY: cert.public_bytes(serialization.Encoding.PEM),
            }
            with zipfile.ZipFile(unsigned, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=False) as archive:
                for name, content in entries.items():
                    info = zipfile.ZipInfo(name, (2026, 9, 8, 0, 0, 0))
                    info.create_system = 3
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = (0o100755 if name == BINARY_ENTRY else 0o100644) << 16
                    archive.writestr(info, content)
            key = serialization.load_der_private_key(KEY.read_bytes(), password=None)
            signature = helper.sign_zip(unsigned, final, cert, key)
            del key
            require(helper.verify_zip(final, cert) == signature, "Signature verification results differ")
            with zipfile.ZipFile(final) as archive:
                require(len(archive.infolist()) == len(entries) and set(archive.namelist()) == set(entries), "Unexpected or duplicate ZIP member")
                require(archive.testzip() is None, "ZIP CRC check failed")
                require(json.loads(archive.read(META_ENTRY)) == metadata, "Extractor metadata changed")
                for name, content in entries.items():
                    require(archive.read(name) == content and archive.getinfo(name).file_size == len(content), "ZIP content changed: " + name)
                require(archive.getinfo(BINARY_ENTRY).external_attr >> 16 == 0o100755, "Extractor executable mode changed")
            java_output = run([JAVA, "-Xmx256m", "--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED",
                               "--add-exports=java.base/sun.security.x509=ALL-UNNAMED", "-cp", java_out,
                               "VerifyWholeZip", final], target["name"] + "-openjdk-signature.log")
            require("OpenJDK PKCS7 whole-file RSA/SHA1 signature verified" in java_output, "Missing independent signature confirmation")
            records.append({"architecture": target["name"], "file": relative(final),
                            "bytes": final.stat().st_size, "sha256": sha(final),
                            "binary_file": relative(binary), "binary_bytes": binary.stat().st_size,
                            "binary_sha256": sha(binary), "elf": elf, "metadata": metadata,
                            "linux_tests_compiled": True, "linux_tests_sha256": sha(linux_tests), "linux_tests_executed": False,
                            "members": [{"name": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()} for name, content in entries.items()],
                            "signature": signature, "python_signature_verified": True,
                            "openjdk_signature_verified": True, "zip_crc_verified": True,
                            "zip_member_content_verified": True})
        require(sources() == source_hashes, "Extractor sources changed during the build")
        require({relative(path): sha(path) for path in tool_paths} == tool_hashes, "A build input changed")
        require(sha(KEY) == private_key_hash, "Signing input changed")
        receipt = {"schema": "tvbase-recovery-extractor-build-1", "state": "built_verified_pc",
                   "version": VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
                   "build_directory": relative(build_dir), "output_directory": relative(output_dir),
                   "go_version": go_version, "source_sha256": source_hashes, "tool_input_sha256": tool_hashes,
                   "go_host_tests": {"os": "windows", "arch": "amd64", "count": len(passed), "passed": passed},
                   "java_verifier_class_sha256": sha(java_out / "VerifyWholeZip.class"),
                   "recovery_v1_trust": trust, "signing_inputs_unchanged": True,
                   "sources_unchanged": True, "packages": records, "command_logs": logs,
                   "tv_contacted": False, "usb_prepared": False, "physical_recovery_tested": False,
                   "limits": ["Local build and signature verification do not prove execution on a TV",
                              "Without an exact DT match to a plan from a validated APK capture, only inventory is saved",
                              "ARM32 and ARM64 are independent choices; no automatic architecture dispatch",
                              "Original P291 recovery trust does not certify P271 or Rockchip recovery trust",
                              "Legacy test key and SHA1 are compatibility measures, not production update security",
                              "The extractor does not implement entry to recovery or restoration"]}
        new_json(output_dir / "COMPILACION.json", receipt)
        new_json(build_dir / "RESULTADO.json", {"state": "built_verified_pc", "receipt": relative(output_dir / "COMPILACION.json"), "sha256": sha(output_dir / "COMPILACION.json")})
        print(json.dumps({"state": receipt["state"], "receipt": relative(output_dir / "COMPILACION.json"),
                          "packages": [{key: row[key] for key in ("architecture", "file", "bytes", "sha256")} for row in records]}, ensure_ascii=False, indent=2))
    except Exception as exc:
        new_json(build_dir / "FALLO.json", {"state": "failed_preserved", "created_at": datetime.now(timezone.utc).isoformat(),
                                           "error_type": type(exc).__name__, "error": str(exc), "command_logs": logs,
                                           "output_must_not_be_delivered": True})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", required=True, help="New private work directory, relative to the project or absolute")
    parser.add_argument("--output-dir", required=True, help="New output directory containing both ZIPs and COMPILACION.json")
    args = parser.parse_args()
    build_dir = new_directory_path(args.build_dir)
    output_dir = new_directory_path(args.output_dir)
    build(build_dir, output_dir)


if __name__ == "__main__":
    main()
