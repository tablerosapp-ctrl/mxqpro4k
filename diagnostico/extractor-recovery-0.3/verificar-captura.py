"""Read-only PC verification of ONE native recovery capture directory.

Never opens the device paths recorded in JSON, extracts files, joins image
parts, changes the capture, or interprets userdata. Receipts are not signatures
or proof of physical identity, complete storage coverage, or a working restore.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

MAX_SOURCES = 64
MAX_SOURCE_BYTES = 1 << 40
MAX_PARTS = 1024
MAX_PART_BYTES = 1 << 30
SPACE_RESERVE = 128 << 20
MAX_FILES = MAX_SOURCES * MAX_PARTS + 3
MAX_JSON = 32 << 20
CHUNK = 1 << 20
SHA = re.compile(r"[0-9a-f]{64}\Z")
CAPTURE_ID = re.compile(r"[0-9a-f]{32}\Z")
UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
MM = re.compile(r"(?:0|[1-9][0-9]*):(?:0|[1-9][0-9]*)\Z")
PART = re.compile(r"[0-9a-f]{64}\.part-[0-9]{6}\.img\.partial\Z")
RESULT_SCHEMA = "tvbase-recovery-result-1"
ASSOCIATION = "matched_device_tree_profile_not_proof_of_physical_identity"
METADATA = {"inventario.json", "report.json", "resultado.json"}
FAILURES = {"failed-report.json", "resultado-error.json"}


class InvalidCapture(ValueError):
    """A fixed error code, safe to print without input content or private paths."""


def need(condition, code):
    if not condition:
        raise InvalidCapture(code)


def integer(value, minimum=0, maximum=MAX_SOURCE_BYTES):
    need(type(value) is int and minimum <= value <= maximum, "invalid_integer")
    return value


def text(value, maximum=4096, empty=False):
    need(type(value) is str and (empty or value) and len(value) <= maximum,
         "invalid_text")
    need(all(ord(c) >= 32 and not 0xD800 <= ord(c) <= 0xDFFF for c in value),
         "invalid_text")
    return value


def digest(value):
    need(type(value) is str and SHA.fullmatch(value) is not None, "invalid_sha256")
    return value


def boolean(value):
    need(type(value) is bool, "invalid_boolean")
    return value


def mm(value):
    text(value, 64)
    need(type(value) is str and MM.fullmatch(value) is not None, "invalid_device_id")
    for item in value.split(":"):
        integer(int(item), 0, (1 << 32) - 1)
    return value


def basename(value):
    text(value, 1024)
    need(value not in {".", ".."} and not any(c in value for c in "/\\:")
         and not value.endswith((".", " ")), "unsafe_basename")
    return value


def posix_path(value, prefix=None):
    text(value, 4096)
    # POSIX paths are metadata only: mmc0:0001 and bus aliases legitimately
    # contain colons. They must never be treated as Windows filesystem paths.
    need(value.startswith("/") and "\\" not in value
         and str(PurePosixPath(value)) == value
         and ".." not in PurePosixPath(value).parts, "invalid_recorded_path")
    if prefix:
        need(value.startswith(prefix), "invalid_recorded_path")
    return value


def obj(value, required, optional=()):
    need(type(value) is dict and set(required) <= value.keys()
         and value.keys() <= set(required) | set(optional), "invalid_object_schema")
    return value


def array(value, maximum, *, nullable=False):
    if nullable and value is None:
        return []
    need(type(value) is list and len(value) <= maximum, "invalid_array")
    return value


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def bad_constant(_value):
    raise InvalidCapture("nonfinite_json_number")


def strict_json(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicates,
                          parse_constant=bad_constant)
    except InvalidCapture:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise InvalidCapture("invalid_json") from exc


def info_key(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink


def ordinary(path, *, directory=False):
    need(path.is_absolute() and ".." not in path.parts, "ambiguous_capture_path")
    for item in (*reversed(path.parents), path):
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode)
             and not getattr(info, "st_file_attributes", 0) & 0x400,
             "symlink_or_reparse_point")
        want_dir = item != path or directory
        need(stat.S_ISDIR(info.st_mode) if want_dir else stat.S_ISREG(info.st_mode),
             "nonordinary_entry")
        if not want_dir:
            need(info.st_nlink == 1, "hardlinked_file")
    need(path.resolve(strict=True) == path, "redirected_path")
    return info


class CaptureReader:
    def __init__(self, capture):
        raw = Path(capture)
        need(".." not in raw.parts, "ambiguous_capture_path")
        self.root = raw.absolute()
        self.root_info = info_key(ordinary(self.root, directory=True))
        self.files = self.scan()
        # Presence is sufficient, including a malformed or truncated receipt.
        need(not (FAILURES & self.files.keys()), "capture_marked_failed")

    def scan(self):
        need(info_key(ordinary(self.root, directory=True)) == self.root_info,
             "capture_directory_changed")
        files = {}
        folded = set()
        with os.scandir(self.root) as entries:
            for entry in entries:
                need(len(files) < MAX_FILES, "too_many_files")
                basename(entry.name)
                need(entry.name.casefold() not in folded, "duplicate_filename")
                folded.add(entry.name.casefold())
                files[entry.name] = info_key(ordinary(self.root / entry.name))
        return files

    def open(self, name):
        basename(name)
        need(name in self.files, "missing_file")
        path = self.root / name
        before = ordinary(path)
        need(info_key(before) == self.files[name], "capture_file_changed")
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0)
                     | getattr(os, "O_NOFOLLOW", 0))
        stream = os.fdopen(fd, "rb")
        if info_key(os.fstat(stream.fileno())) != self.files[name]:
            stream.close()
            raise InvalidCapture("capture_file_changed")
        return stream

    def unchanged(self, stream, name):
        need(info_key(os.fstat(stream.fileno())) == self.files[name]
             == info_key(ordinary(self.root / name)), "capture_file_changed")

    def json(self, name, limit=MAX_JSON):
        need(name in self.files and self.files[name][2] <= limit, "missing_or_large_json")
        with self.open(name) as stream:
            data = stream.read(limit + 1)
            need(len(data) == self.files[name][2] and len(data) <= limit,
                 "json_size_changed")
            self.unchanged(stream, name)
        return strict_json(data), hashlib.sha256(data).hexdigest()

    def hash_part(self, name, expected, whole):
        need(name in self.files and self.files[name][2] == expected, "part_size_mismatch")
        part = hashlib.sha256()
        with self.open(name) as stream:
            left = expected
            while left:
                block = stream.read(min(left, CHUNK))
                need(bool(block), "short_part_read")
                part.update(block)
                whole.update(block)
                left -= len(block)
            need(stream.read(1) == b"", "part_has_extra_bytes")
            self.unchanged(stream, name)
        return part.hexdigest()

    def finish(self, allowed):
        need(self.files.keys() == set(allowed), "unexpected_or_missing_files")
        need(self.scan() == self.files, "capture_directory_changed")


def aliases(value):
    values = array(value, 128, nullable=True)
    for item in values:
        posix_path(item, "/dev/")
    need(len(set(values)) == len(values), "duplicate_alias")
    return values


def validate_source(source):
    obj(source, {"name", "device", "bytes", "major_minor", "kind"}, {"aliases"})
    basename(source["name"])
    posix_path(source["device"], "/dev/")
    integer(source["bytes"], 1)
    mm(source["major_minor"])
    text(source["kind"], 128)
    need(source["kind"] in {"emmc_user_area", "partition", "emmc_boot_area"},
         "unsupported_source_kind")
    aliases(source.get("aliases", []))
    return source


def source_id(source):
    # encoding/json marshals Go Source fields in declaration order and escapes
    # HTML plus U+2028/U+2029. Empty Aliases is omitted by its omitempty tag.
    ordered = {key: source[key] for key in ("name", "device", "bytes", "major_minor", "kind")}
    if source.get("aliases"):
        ordered["aliases"] = source["aliases"]
    encoded = json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))
    for character, escaped in (("<", r"\u003c"), (">", r"\u003e"), ("&", r"\u0026"),
                               ("\u2028", r"\u2028"), ("\u2029", r"\u2029")):
        encoded = encoded.replace(character, escaped)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def omissions(value, *, inventory=False):
    rows = array(value, 1024 if inventory else 256, nullable=True)
    normalized = []
    for row in rows:
        if inventory:
            obj(row, {"Name", "Reason"})
            text(row["Name"], 1024)
            text(row["Reason"], 4096)
            normalized.append({"name": row["Name"], "reason": row["Reason"]})
        else:
            obj(row, {"name", "reason"}, {"device"})
            text(row["name"], 1024)
            text(row["reason"], 4096)
            if "device" in row:
                posix_path(row["device"], "/dev/")
            normalized.append(row)
    return normalized


def validate_sd_destination(p, inv):
    """Check recorded SD policy only; never open recorded sysfs/device paths."""
    obj(p, {"mount", "partition_sysfs", "disk_sysfs", "disk_name", "disk_device",
            "card_type", "removable", "cid_sha256", "disk_bytes", "partition_bytes",
            "start_sector", "partition_number"})
    m = obj(p["mount"], {"Device", "Root", "Point", "FS", "ReadOnly", "Writable"})
    need(m["Point"] == "/mnt/external_sd" and m["Root"] == "/" and m["FS"] == "vfat"
         and m["Writable"] is True and m["ReadOnly"] is False, "invalid_sd_mount")
    mm(m["Device"])
    mm(p["disk_device"])
    need(m["Device"].startswith("179:") and p["disk_device"].startswith("179:")
         and m["Device"] != p["disk_device"], "invalid_sd_device")
    need(type(p["disk_name"]) is str and re.fullmatch(r"mmcblk[0-9]+", p["disk_name"])
         is not None, "invalid_sd_device")
    disk = posix_path(p["disk_sysfs"], "/sys/devices/")
    partition = posix_path(p["partition_sysfs"], "/sys/devices/")
    need(disk.endswith("/block/" + p["disk_name"])
         and re.search(r"/mmc_host/mmc[0-9]+/mmc[0-9]+:[0-9a-fA-F]+/block/", disk)
         is not None and "/virtual/" not in disk and "/usb" not in disk
         and partition == disk + "/" + p["disk_name"] + "p1", "invalid_sd_topology")
    need(p["card_type"] == "SD" and p["removable"] in ("0", "1"), "invalid_sd_card_type")
    digest(p["cid_sha256"])
    for field, expected in {"disk_bytes": 8053063680, "partition_bytes": 8052015104,
                            "start_sector": 2048, "partition_number": 1}.items():
        need(integer(p[field]) == expected, "invalid_sd_geometry")
    need(sum(1 for row in inv["mounts"] if row["Point"] == "/mnt/external_sd") == 1
         and m in inv["mounts"], "sd_mount_not_in_inventory")
    for block in inv["blocks"] or []:
        path = block["sysfs"]
        need(block["major_minor"] not in (m["Device"], p["disk_device"])
             and path != disk and not path.startswith(disk + "/")
             and not disk.startswith(path + "/"), "sd_destination_overlaps_source")


def validate_source_policy(inv):
    """Validate recorded scope; no CID lookup, sysfs or block access on PC."""
    p = obj(inv["source_policy"], {"id", "expected_identity_bound", "deferred_source",
                                  "reason", "whole_user_area_allowed"})
    need(p == {"id": "rk3229-c-backup-last-1", "expected_identity_bound": True,
               "deferred_source": "mmcblk0p10", "reason": "observed_source_changed_during_reread",
               "whole_user_area_allowed": False}, "invalid_source_policy")
    need(p["expected_identity_bound"] is True and p["whole_user_area_allowed"] is False,
         "invalid_source_policy")
    need(inv["dt_identity"] == "rockchip,rk3229" and "destination" in inv,
         "source_policy_profile_mismatch")
    blocks = {b["name"]: b for b in (inv["blocks"] or [])}
    need("mmcblk0" in blocks and "mmcblk0p10" in blocks, "source_policy_blocks_missing")
    disk, deferred = blocks["mmcblk0"], blocks["mmcblk0p10"]
    need(disk["kind"] == "emmc_user_area" and disk["bytes"] == 7818182656
         and disk["major_minor"] == "179:0", "source_policy_disk_mismatch")
    need(deferred["kind"] == "partition" and deferred["bytes"] == 67108864
         and deferred.get("start_sector") == 196608 and deferred["parent"] == "mmcblk0"
         and deferred["major_minor"] == "179:10"
         and "/dev/block/platform/30020000.rksdmmc/by-name/backup" in deferred["aliases"],
         "source_policy_deferred_mismatch")
    need("mmcblk0_cid_sha256" in inv["emmc_identity_hashes"], "source_policy_identity_missing")
    digest(inv["emmc_identity_hashes"]["mmcblk0_cid_sha256"])


def validate_policy_source(inv, source, row=None, index=None, count=None):
    if "source_policy" not in inv:
        need(row is None or "verification_order" not in row, "unrecognized_verification_order")
        return
    need(source["name"] != "mmcblk0" and source["major_minor"] != "179:0"
         and source["kind"] != "emmc_user_area", "whole_source_in_deferred_report")
    backup = source["name"] == "mmcblk0p10" or source["major_minor"] == "179:10"
    if backup:
        need(source["name"] == "mmcblk0p10" and source["major_minor"] == "179:10",
             "deferred_source_identity_mismatch")
        if row is not None:
            need(index == count - 1, "backup_not_last")
            not_started = (row.get("status") in {"omitted", "failed"} and not row.get("parts")
                           and "sha256" not in row and "reread_sha256" not in row
                           and "verification_order" not in row)
            need(not_started or row.get("verification_order") == "source_source_destination",
                 "backup_verification_order_mismatch")
    elif row is not None:
        need("verification_order" not in row, "unexpected_verification_order")


def validate_inventory(inv, capture_id, *, inventory_only):
    obj(inv, {"schema", "capture_id", "profile_plan", "dt_identity", "emmc_identity_hashes",
              "blocks", "mounts", "omitted", "captured_wall_time", "wall_clock_trusted", "coverage"},
        {"kernel", "proc_partitions", "destination", "source_policy"})
    need(inv["schema"] == "tvbase-recovery-inventory-1" and inv["capture_id"] == capture_id,
         "inventory_identity_mismatch")
    need(inv["wall_clock_trusted"] is False, "unsupported_clock_claim")
    text(inv["dt_identity"], empty=inventory_only)
    text(inv["captured_wall_time"], 128)
    text(inv["coverage"], 4096)
    for key in ("kernel", "proc_partitions"):
        if key in inv:
            need(type(inv[key]) is str and len(inv[key]) <= 65536, "invalid_inventory_text")
    need(type(inv["emmc_identity_hashes"]) is dict and len(inv["emmc_identity_hashes"]) <= 512,
         "invalid_identity_hashes")
    for key, value in inv["emmc_identity_hashes"].items():
        need(re.fullmatch(r"mmcblk[0-9]+_cid_sha256", key) is not None, "invalid_identity_hashes")
        digest(value)
    blocks = {}
    devices = set()
    for block in array(inv["blocks"], 512, nullable=True):
        obj(block, {"name", "device", "sysfs", "major_minor", "parent", "kind", "bytes",
                    "aliases", "holders", "read_only_device"}, {"start_sector"})
        source = {key: block[key] for key in ("name", "device", "bytes", "major_minor", "kind", "aliases")}
        validate_source(source)
        posix_path(block["sysfs"], "/sys/devices/")
        text(block["parent"], 1024, empty=True)
        integer(block.get("start_sector", 0))
        boolean(block["read_only_device"])
        for holder in array(block["holders"], 512, nullable=True):
            basename(holder)
        need(block["name"] not in blocks and block["major_minor"] not in devices,
             "duplicate_inventory_block")
        blocks[block["name"]] = source
        devices.add(block["major_minor"])
    for mount in array(inv["mounts"], 32768):
        obj(mount, {"Device", "Root", "Point", "FS", "ReadOnly", "Writable"})
        mm(mount["Device"])
        text(mount["Root"], empty=mount["FS"] == "swap")
        text(mount["Point"])
        text(mount["FS"], 128)
        boolean(mount["ReadOnly"])
        boolean(mount["Writable"])
        need(not (mount["ReadOnly"] and mount["Writable"]), "contradictory_mount_flags")
    if "destination" in inv:
        validate_sd_destination(inv["destination"], inv)
    omitted = omissions(inv["omitted"], inventory=True)
    if "source_policy" in inv:
        validate_source_policy(inv)
    plan = inv["profile_plan"]
    if inventory_only:
        need(plan is None, "inventory_only_has_plan")
    else:
        obj(plan, {"schema", "apk_capture_id", "apk_device_id", "apk_zip_sha256", "expected_dt",
                   "profile", "display_name", "operation"})
        need(plan["schema"] == "tvbase-recovery-plan-1" and plan["operation"] == "capture_read_only"
             and plan["expected_dt"] == inv["dt_identity"], "profile_plan_mismatch")
        for key in ("apk_capture_id", "apk_device_id"):
            need(type(plan[key]) is str and UUID.fullmatch(plan[key]) is not None, "invalid_apk_uuid")
        digest(plan["apk_zip_sha256"])
        basename(plan["profile"])
        text(plan["display_name"], 4096, empty=True)
    return blocks, omitted, plan


def verify_capture(capture):
    reader = CaptureReader(capture)
    result, _ = reader.json("resultado.json", 65536)
    need(type(result) is dict and result.get("schema") == RESULT_SCHEMA, "invalid_result_schema")
    capture_id = result.get("capture_id")
    need(type(capture_id) is str and CAPTURE_ID.fullmatch(capture_id) is not None, "invalid_capture_id")
    inventory_only = result.get("status") == "inventory_only"
    if inventory_only:
        obj(result, {"schema", "status", "capture_id", "images_copied", "reason"})
        need(result["images_copied"] is False and result["reason"] == "no_matching_apk_plan",
             "invalid_inventory_only_result")
    else:
        obj(result, {"schema", "status", "capture_id", "apk_capture_id", "apk_device_id",
                     "apk_zip_sha256", "association_scope", "report_sha256", "source_count",
                     "omitted_count", "all_device_storage_copied", "device_written_by_extractor",
                     "restore_tested"})
        need(result["status"] == "selected_sources_verified", "capture_not_complete")
        need(result["association_scope"] == ASSOCIATION, "unsupported_identity_claim")
        for key in ("all_device_storage_copied", "device_written_by_extractor", "restore_tested"):
            need(result[key] is False, "unsupported_physical_claim")
        digest(result["report_sha256"])
        integer(result["source_count"], 1, MAX_SOURCES)
        integer(result["omitted_count"], 0, 256)
    inv, _ = reader.json("inventario.json", 8 << 20)
    blocks, inv_omitted, plan = validate_inventory(inv, capture_id, inventory_only=inventory_only)
    summary = {"schema": "tvbase-recovery-pc-verification-1", "status": "inventory_only",
               "capture_id": capture_id, "verified_bytes": 0, "source_count": 0, "part_count": 0,
               "all_device_storage_copied": False, "physical_device_state_verified": False,
               "restore_tested": False, "capture_modified": False, "userdata_content_interpreted": False}
    if inventory_only:
        reader.finish({"inventario.json", "resultado.json"})
        return summary
    for key in ("apk_capture_id", "apk_device_id", "apk_zip_sha256"):
        need(result[key] == plan[key], "result_plan_mismatch")
    report, report_sha = reader.json("report.json")
    need(report_sha == result["report_sha256"], "report_sha256_mismatch")
    obj(report, {"format", "status", "expected_bytes", "required_bytes", "free_bytes_at_preflight",
                 "part_bytes", "sources", "limit"}, {"omitted", "error"})
    need(report["format"] == "tvbase-recovery-capture-0.1" and report["status"] == "data_verified"
         and report.get("error", "") == "", "report_not_verified")
    text(report["limit"], 4096)
    part_bytes = integer(report["part_bytes"], 1, MAX_PART_BYTES)
    sources = array(report["sources"], MAX_SOURCES)
    need(len(sources) == result["source_count"], "source_count_mismatch")
    omitted = omissions(report.get("omitted"))
    need(len(omitted) == result["omitted_count"] and omitted == inv_omitted, "omissions_mismatch")
    expected = integer(report["expected_bytes"], 1, MAX_SOURCES * MAX_SOURCE_BYTES)
    required = integer(report["required_bytes"], 1, MAX_SOURCES * MAX_SOURCE_BYTES + SPACE_RESERVE)
    free = integer(report["free_bytes_at_preflight"], 0, (1 << 64) - 1)
    need(required == expected + SPACE_RESERVE and free >= required, "invalid_preflight_sizes")
    allowed = set(METADATA)
    identities = {key: set() for key in ("id", "name", "device", "major_minor")}
    total = 0
    # Validate all metadata and filenames before reading potentially huge parts.
    scheduled = []
    for source_index, row in enumerate(sources):
        obj(row, {"source", "id", "status", "sha256", "reread_sha256", "parts"}, {"error", "verification_order"})
        source = validate_source(row["source"])
        validate_policy_source(inv, source, row, source_index, len(sources))
        need(row["status"] == "verified" and row.get("error", "") == "", "source_not_verified")
        digest(row["id"])
        need(row["id"] == source_id(source), "source_id_mismatch")
        need(digest(row["sha256"]) == digest(row["reread_sha256"]), "source_reread_mismatch")
        for key in identities:
            value = row["id"] if key == "id" else source[key]
            need(value not in identities[key], "duplicate_source")
            identities[key].add(value)
        inventory_source = blocks.get(source["name"])
        need(inventory_source is not None and source_id(source) == source_id(inventory_source),
             "source_inventory_mismatch")
        parts = array(row["parts"], MAX_PARTS)
        need(len(parts) == (source["bytes"] + part_bytes - 1) // part_bytes, "part_count_mismatch")
        source_total = 0
        for index, part in enumerate(parts):
            obj(part, {"index", "name", "expected_bytes", "copied_bytes", "sha256", "status"}, {"error"})
            need(integer(part["index"], 0, MAX_PARTS - 1) == index, "part_order_mismatch")
            name = basename(part["name"])
            need(PART.fullmatch(name) is not None and name == f'{row["id"]}.part-{index:06d}.img.partial',
                 "part_name_mismatch")
            need(name not in allowed, "duplicate_part")
            allowed.add(name)
            size = min(part_bytes, source["bytes"] - source_total)
            need(integer(part["expected_bytes"], 1, MAX_PART_BYTES) == size
                 and integer(part["copied_bytes"], 1, MAX_PART_BYTES) == size, "part_declared_size_mismatch")
            need(part["status"] == "verified" and part.get("error", "") == "", "part_not_verified")
            digest(part["sha256"])
            source_total += size
        need(source_total == source["bytes"], "source_size_mismatch")
        total += source_total
        scheduled.append(row)
    need(total == expected, "total_size_mismatch")
    need(reader.files.keys() == allowed, "unexpected_or_missing_files")
    for row in scheduled:
        whole = hashlib.sha256()
        for part in row["parts"]:
            need(reader.hash_part(part["name"], part["expected_bytes"], whole) == part["sha256"],
                 "part_sha256_mismatch")
        need(whole.hexdigest() == row["sha256"], "source_sha256_mismatch")
    reader.finish(allowed)
    summary.update(status="selected_sources_verified_pc", verified_bytes=total,
                   source_count=len(sources), part_count=len(allowed) - len(METADATA),
                   report_sha256=report_sha)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path,
                        help="One native CAPTURAS/TVBASE-* folder; read only")
    args = parser.parse_args(argv)
    try:
        result = verify_capture(args.capture)
    except (InvalidCapture, OSError, UnicodeError, OverflowError, RecursionError) as exc:
        result = {"schema": "tvbase-recovery-pc-verification-1", "status": "failed",
                  "error": str(exc) if isinstance(exc, InvalidCapture) else "filesystem_or_encoding_error",
                  "verified_bytes": 0, "all_device_storage_copied": False,
                  "physical_device_state_verified": False, "restore_tested": False,
                  "capture_modified": False, "userdata_content_interpreted": False}
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
