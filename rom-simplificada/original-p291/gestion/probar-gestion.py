"""Meaningful cryptographic/policy regressions on the host JVM, no device/network."""
import hashlib
import json
import subprocess
import re
import time
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path
import manifest_tool
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JAVA = ROOT / "tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe"
ECJ = ROOT / "tools/compilar-android/ecj-3.39.0.jar"


def run():
    receipt = json.loads((HERE / "compilacion-resultado.json").read_text(encoding="utf-8"))
    apk = ROOT / receipt["apk"]
    out = HERE / "privado" / ("tests-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f"))
    out.mkdir(parents=True, exist_ok=False)
    core = ROOT / "rom-simplificada/componentes/gestion-tvbase/UpdateCore.java"
    commands = [
        [JAVA, "-jar", ECJ, "-8", "-encoding", "UTF-8", "-d", out, core, HERE / "CoreTest.java", HERE / "PolicyCheck.java"],
        [JAVA, "-cp", out, "local.tvbase.gestion.CoreTest", apk, apk.parent / "assets/owner.conf"],
    ]
    outputs = []
    for command in commands:
        result = subprocess.run([str(v) for v in command], capture_output=True, creationflags=0x08000000)
        outputs.append(result.stdout + result.stderr)
        if result.returncode:
            (out / "tests.log").write_bytes(b"\n".join(outputs))
            raise RuntimeError("Pruebas fallidas; ver " + str(out / "tests.log"))
    text = b"\n".join(outputs).decode("utf-8", "replace")
    count = int(text.rsplit("PASSED=", 1)[1].splitlines()[0])
    # Reserved .invalid host is a parser fixture only. No HTTP client is invoked.
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_file, pub_file = out / "ephemeral-test-key.pem", out / "ephemeral-test-public.pem"
    key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    pub_file.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    cert = re.search(r"certificate SHA-256 digest: ([0-9a-f]{64})",
                     (apk.parent / "signature.txt").read_text(encoding="utf-8")).group(1)
    packages = out / "package-policy.json"
    packages.write_text(json.dumps([{"package": "local.tvbase.gestion", "certificateSha256": cert, "role": "app"}]))
    configuration = out / "fixture-owner.conf"
    manifest_tool.config(SimpleNamespace(out=configuration, public_key=pub_file, manifest_url="https://updates.invalid/manifest",
                                        hosts="updates.invalid", packages=packages, auto_apps=True, auto_browser=False,
                                        poll_hours=24, maintenance_start_utc="03:00", maintenance_minutes=120))
    now = int(time.time())
    spec = {"sequence": 1, "issuedAt": now - 60, "expiresAt": now + 3600,
            "apks": [{"package": "local.tvbase.gestion", "versionCode": 1, "minSdk": 28, "maxSdk": 28,
                      "abis": ["none"], "bytes": apk.stat().st_size, "sha256": receipt["sha256"],
                      "certificateSha256": cert, "url": "https://updates.invalid/manager.apk"}]}
    spec_file, envelope = out / "fixture-spec.json", out / "fixture-manifest.signed"
    spec_file.write_text(json.dumps(spec), encoding="utf-8")
    manifest_tool.sign(spec_file, key_file, envelope)
    check = subprocess.run([str(JAVA), "-cp", str(out), "local.tvbase.gestion.PolicyCheck",
                            str(configuration), str(envelope)], capture_output=True, creationflags=0x08000000)
    outputs.append(check.stdout + check.stderr)
    if check.returncode or b"MANIFEST_VALID=1" not in check.stdout or b"POLICY_VALID enabled=true" not in check.stdout:
        (out / "tests.log").write_bytes(b"\n".join(outputs))
        raise RuntimeError("Python/JVM manifest interoperability failed")
    count += 2
    log = b"\n".join(outputs)
    (out / "tests.log").write_bytes(log)
    result = {"tests": count, "exit_code": 0, "network_used": False, "device_used": False,
              "apk_sha256": receipt["sha256"], "core_sha256": hashlib.sha256(core.read_bytes()).hexdigest(),
              "log_sha256": hashlib.sha256(log).hexdigest(),
              "scope": "Host JVM: signature, replay/time/policy/API/ABI guards and actual compiled APK metadata. Android adapter not executed."}
    (HERE / "pruebas-resultado.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
