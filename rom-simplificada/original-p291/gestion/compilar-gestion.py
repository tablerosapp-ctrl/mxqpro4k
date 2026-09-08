"""Compile the standalone update manager offline. Never accesses a TV or USB."""
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "rom-simplificada/componentes/gestion-tvbase"
JAVA = ROOT / "tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe"
TOOLS = ROOT / "tools/verificacion-apk/build-tools-37/android-37.0"
SDK = ROOT / "tools/compilar-android/android-28.jar"
ECJ = ROOT / "tools/compilar-android/ecj-3.39.0.jar"
KEY = ROOT / "rom-simplificada/claves-desarrollo/componentes.jks"
PASSWORD = KEY.with_name("password.txt")


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def build(owner=None):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    out = HERE / "privado" / ("build-" + stamp)
    out.mkdir(parents=True, exist_ok=False)
    log = out / "build.log"
    for required in (JAVA, TOOLS / "aapt2.exe", SDK, ECJ, KEY, PASSWORD):
        if not required.is_file():
            raise FileNotFoundError(required)
    original_keys = {str(p): sha(p) for p in (KEY, PASSWORD)}

    def run(args):
        result = subprocess.run([str(x) for x in args], capture_output=True,
                                creationflags=0x08000000)
        with log.open("ab") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError("Falló una herramienta; consultar el registro local: " + str(log))
        return result.stdout

    assets = out / "assets"
    assets.mkdir()
    selected = Path(owner).resolve() if owner else SOURCE / "assets/owner.conf"
    shutil.copyfile(selected, assets / "owner.conf")
    host_classes = out / "host-classes"
    host_classes.mkdir()
    run([JAVA, "-jar", ECJ, "-8", "-encoding", "UTF-8", "-d", host_classes,
         SOURCE / "UpdateCore.java", HERE / "PolicyCheck.java"])
    run([JAVA, "-cp", host_classes, "local.tvbase.gestion.PolicyCheck", assets / "owner.conf"])
    classes = out / "classes"
    classes.mkdir()
    run([JAVA, "-jar", ECJ, "-8", "-encoding", "UTF-8", "-bootclasspath", SDK,
         "-d", classes, *sorted(SOURCE.glob("*.java"))])
    dex = out / "dex"
    dex.mkdir()
    run([JAVA, "-cp", TOOLS / "lib/d8.jar", "com.android.tools.r8.D8", "--min-api", "28",
         "--lib", SDK, "--output", dex, *sorted(classes.rglob("*.class"))])
    unsigned = out / "unsigned.apk"
    run([TOOLS / "aapt2.exe", "link", "-I", SDK, "--manifest", SOURCE / "AndroidManifest.xml",
         "-A", assets, "--min-sdk-version", "28", "--target-sdk-version", "28",
         "--no-resource-deduping", "--no-resource-removal", "-o", unsigned])
    with zipfile.ZipFile(unsigned, "a") as z:
        z.write(dex / "classes.dex", "classes.dex")
    aligned = out / "aligned.apk"
    run([TOOLS / "zipalign.exe", "-f", "4", unsigned, aligned])
    final = out / "TVBaseGestion-0.1.apk"
    run([JAVA, "-jar", TOOLS / "lib/apksigner.jar", "sign", "--ks", KEY,
         "--ks-key-alias", "tvbase-development", "--ks-pass", "file:" + str(PASSWORD),
         "--out", final, aligned])
    proof = run([JAVA, "-jar", TOOLS / "lib/apksigner.jar", "verify", "--verbose",
                 "--print-certs", "--min-sdk-version", "28", "--max-sdk-version", "28", final])
    (out / "signature.txt").write_bytes(proof)
    badging = run([TOOLS / "aapt2.exe", "dump", "badging", final])
    (out / "badging.txt").write_bytes(badging)
    assert original_keys == {str(p): sha(p) for p in (KEY, PASSWORD)}, "Signing inputs changed"
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p)
                     for p in sorted(SOURCE.rglob("*")) if p.is_file()}
    disabled = (assets / "owner.conf").read_bytes() == b"TVBASE-OWNER-1\nenabled=false\n"
    receipt = {
        "component": "local.tvbase.gestion", "version": "0.1-experimental",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "apk": final.relative_to(ROOT).as_posix(), "bytes": final.stat().st_size,
        "sha256": sha(final), "signature_verification_api28_exit": 0,
        "configuration_sha256": sha(assets / "owner.conf"),
        "configuration_disabled": disabled, "signing_inputs_unchanged": True,
        "source_sha256": source_hashes,
        "integration_apk": "/system/priv-app/TVBaseGestion/TVBaseGestion.apk",
        "integration_allowlist": "/system/etc/permissions/privapp-permissions-tvbase-gestion.xml",
        "image_integrated": False, "physical_device_tested": False,
        "remote_installation_tested": False
    }
    (HERE / "compilacion-resultado.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-config", help="Local policy supplied by the owner; default stays disabled")
    args = parser.parse_args()
    print(json.dumps(build(args.owner_config), indent=2, ensure_ascii=False))
