"""Create owner configuration and sign manifests offline; no key generation or network."""
import argparse
import base64
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

APK_KEYS = {"package", "versionCode", "minSdk", "maxSdk", "abis", "bytes",
            "sha256", "certificateSha256", "url"}
ABIS = {"none", "armeabi-v7a", "arm64-v8a", "x86", "x86_64"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def line(key, value):
    value = str(value)
    need(value and value == value.strip() and not any(c in value for c in "\r\n\0"), "Invalid field")
    return key + "=" + value + "\n"


def https(value):
    parsed = urlsplit(value)
    need(parsed.scheme == "https" and parsed.hostname and not parsed.username
         and not parsed.password and not parsed.fragment and parsed.port in (None, 443)
         and parsed.hostname == parsed.hostname.lower(), "HTTPS URL required")
    return parsed.hostname


def sha(value):
    need(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value), "Invalid SHA256")


def integer(value, low, high):
    need(type(value) is int and low <= value <= high, "Integer outside range")


def package(value):
    need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+", value), "Invalid package")


def payload(spec):
    need(set(spec) == {"sequence", "issuedAt", "expiresAt", "apks"}, "Unknown or missing manifest keys")
    integer(spec["sequence"], 1, 2**63 - 1)
    integer(spec["issuedAt"], 1, 4102444800)
    integer(spec["expiresAt"], spec["issuedAt"] + 1, min(spec["issuedAt"] + 2678400, 4102444800))
    need(type(spec["apks"]) is list and 1 <= len(spec["apks"]) <= 16, "One to sixteen APKs required")
    out = "TVBASE-UPDATES-1\n"
    for key in ("sequence", "issuedAt", "expiresAt"):
        out += line(key, spec[key])
    out += line("count", len(spec["apks"]))
    seen = set()
    for i, apk in enumerate(spec["apks"]):
        need(set(apk) == APK_KEYS, "Unknown or missing APK keys")
        package(apk["package"])
        need(apk["package"] not in seen, "Duplicate package")
        seen.add(apk["package"])
        integer(apk["versionCode"], 1, 2**63 - 1)
        integer(apk["minSdk"], 1, 1000)
        integer(apk["maxSdk"], apk["minSdk"], 1000)
        integer(apk["bytes"], 1, 536870912)
        sha(apk["sha256"])
        sha(apk["certificateSha256"])
        https(apk["url"])
        need(type(apk["abis"]) is list and apk["abis"] and len(set(apk["abis"])) == len(apk["abis"])
             and set(apk["abis"]) <= ABIS and ("none" not in apk["abis"] or len(apk["abis"]) == 1), "Invalid ABIs")
        for key in ("package", "versionCode", "minSdk", "maxSdk", "abis", "bytes",
                    "sha256", "certificateSha256", "url"):
            value = ",".join(apk[key]) if key == "abis" else apk[key]
            out += line("apk." + str(i) + "." + key, value)
    data = out.encode("utf-8")
    need(len(data) <= 65536, "Manifest too large")
    return data


def sign(spec_path, key_path, output):
    need(not output.exists(), "Output already exists; keep published sequences immutable")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    data = payload(spec)
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    need(isinstance(key, rsa.RSAPrivateKey) and 2048 <= key.key_size <= 8192, "RSA 2048–8192 key required")
    signature = key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    envelope = "TVBASE-SIGNED-1\n" + line("payload", base64.b64encode(data).decode("ascii"))
    envelope += line("signature", base64.b64encode(signature).decode("ascii"))
    with output.open("xb") as stream:
        stream.write(envelope.encode("utf-8"))
    return {"output": str(output), "sequence": spec["sequence"], "apks": len(spec["apks"])}


def config(args):
    need(not args.out.exists(), "Output already exists")
    key = serialization.load_pem_public_key(args.public_key.read_bytes())
    need(isinstance(key, rsa.RSAPublicKey) and 2048 <= key.key_size <= 8192, "RSA 2048–8192 key required")
    host = https(args.manifest_url)
    hosts = args.hosts.split(",")
    need(len(hosts) == len(set(hosts)) and host in hosts, "Unique hosts including manifest host required")
    for h in hosts:
        need(https("https://" + h + "/") == h, "Invalid host")
    need(re.fullmatch(r"(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", args.maintenance_start_utc), "Invalid UTC time")
    integer(args.maintenance_minutes, 15, 240)
    integer(args.poll_hours, 1, 168)
    policies = json.loads(args.packages.read_text(encoding="utf-8"))
    need(type(policies) is list and 1 <= len(policies) <= 16, "Package policies required")
    names = []
    for p in policies:
        need(set(p) == {"package", "certificateSha256", "role"}, "Unknown package policy fields")
        package(p["package"])
        sha(p["certificateSha256"])
        need(p["role"] in ("app", "browser"), "Invalid role")
        names.append(p["package"])
    need(len(names) == len(set(names)), "Duplicate package policy")
    der = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    out = "TVBASE-OWNER-1\nenabled=true\n"
    for k, v in (
        ("manifestUrl", args.manifest_url), ("publicKey", base64.b64encode(der).decode("ascii")),
        ("hosts", args.hosts), ("autoApps", str(args.auto_apps).lower()),
        ("autoBrowser", str(args.auto_browser).lower()), ("pollHours", args.poll_hours),
        ("maintenanceStartUtc", args.maintenance_start_utc), ("maintenanceMinutes", args.maintenance_minutes),
        ("packages", ",".join(names)),
    ):
        out += line(k, v)
    for p in policies:
        out += line("package." + p["package"] + ".certificate", p["certificateSha256"])
        out += line("package." + p["package"] + ".role", p["role"])
    with args.out.open("xb") as stream:
        stream.write(out.encode("utf-8"))
    return {"output": str(args.out), "packages": len(names), "network_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    signer = commands.add_parser("sign")
    signer.add_argument("--spec", type=Path, required=True)
    signer.add_argument("--key", type=Path, required=True, help="Owner RSA private PEM; kept outside public Git")
    signer.add_argument("--out", type=Path, required=True)
    owner = commands.add_parser("config")
    owner.add_argument("--public-key", type=Path, required=True)
    owner.add_argument("--manifest-url", required=True)
    owner.add_argument("--hosts", required=True)
    owner.add_argument("--packages", type=Path, required=True)
    owner.add_argument("--auto-apps", action="store_true")
    owner.add_argument("--auto-browser", action="store_true")
    owner.add_argument("--poll-hours", type=int, default=24)
    owner.add_argument("--maintenance-start-utc", default="03:00")
    owner.add_argument("--maintenance-minutes", type=int, default=120)
    owner.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = sign(args.spec, args.key, args.out) if args.operation == "sign" else config(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
