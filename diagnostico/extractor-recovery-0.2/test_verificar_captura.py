"""Small regular-file fixtures only; no USB, raw device, mount or firmware IO."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("recovery_capture_verifier", HERE / "verificar-captura.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)
CAPTURE_ID = "0123456789abcdef0123456789abcdef"
APK_ID = "01234567-89ab-cdef-0123-456789abcdef"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    return sha(data)


def fixture(root, *, inventory_only=False):
    root.mkdir()
    plan = {"schema": "tvbase-recovery-plan-1", "apk_capture_id": APK_ID,
            "apk_device_id": APK_ID, "apk_zip_sha256": "a" * 64,
            "expected_dt": "gxlx_p271_1g", "profile": "p271", "display_name": "Fixture PC",
            "operation": "capture_read_only"}
    inventory = {"schema": "tvbase-recovery-inventory-1", "capture_id": CAPTURE_ID,
                 "profile_plan": None if inventory_only else plan,
                 "dt_identity": "gxlx_p271_1g", "emmc_identity_hashes": {}, "blocks": [],
                 "mounts": [{"Device": "8:1", "Root": "/", "Point": "/udisk", "FS": "vfat",
                             "ReadOnly": False, "Writable": True}], "omitted": [],
                 "captured_wall_time": "2020-01-01T00:00:00Z", "wall_clock_trusted": False,
                 "coverage": "Fixture data only; no physical device."}
    result = {"schema": "tvbase-recovery-result-1", "capture_id": CAPTURE_ID}
    if inventory_only:
        inventory["blocks"] = None
        inventory["omitted"] = None
        result.update(status="inventory_only", images_copied=False, reason="no_matching_apk_plan")
        write_json(root / "inventario.json", inventory)
        write_json(root / "resultado.json", result)
        return inventory, None, result
    report = {"format": "tvbase-recovery-capture-0.1", "status": "data_verified", "expected_bytes": 0,
              "required_bytes": 0, "free_bytes_at_preflight": 1 << 30, "part_bytes": 7,
              "sources": [], "limit": "Fixture only; no complete eMMC or tested restore claim."}
    for number, (name, content) in enumerate((("system", b"system fixture: alpha beta"),
                                               ("data", b"opaque userdata fixture\x00\xffbeta")), 1):
        source = {"name": name, "device": "/dev/block/" + name, "bytes": len(content),
                  "major_minor": f"179:{number}", "kind": "partition",
                  "aliases": ["/dev/block/" + name]}
        # Independent ASCII reproduction of Go Source JSON field order.
        ident = sha(json.dumps(source, separators=(",", ":")).encode("ascii"))
        row = {"source": source, "id": ident, "status": "verified", "sha256": sha(content),
               "reread_sha256": sha(content), "parts": []}
        for index, offset in enumerate(range(0, len(content), report["part_bytes"])):
            payload = content[offset:offset + report["part_bytes"]]
            filename = f"{ident}.part-{index:06d}.img.partial"
            (root / filename).write_bytes(payload)
            row["parts"].append({"index": index, "name": filename, "expected_bytes": len(payload),
                                 "copied_bytes": len(payload), "sha256": sha(payload), "status": "verified"})
        report["sources"].append(row)
        report["expected_bytes"] += len(content)
        inventory["blocks"].append(dict(source, sysfs="/sys/devices/platform/soc/mmc_host/mmc0/mmc0:0001/block/mmcblk0/" + name,
                                        parent="mmcblk0", start_sector=number * 100, holders=[],
                                        read_only_device=False))
    report["required_bytes"] = report["expected_bytes"] + V.SPACE_RESERVE
    result.update(status="selected_sources_verified", apk_capture_id=APK_ID, apk_device_id=APK_ID,
                  apk_zip_sha256=plan["apk_zip_sha256"], association_scope=V.ASSOCIATION,
                  source_count=2, omitted_count=0, all_device_storage_copied=False,
                  device_written_by_extractor=False, restore_tested=False)
    write_json(root / "inventario.json", inventory)
    result["report_sha256"] = write_json(root / "report.json", report)
    write_json(root / "resultado.json", result)
    return inventory, report, result


class VerificationTests(unittest.TestCase):
    def setUp(self):
        # The resolved parent is explicitly inside this workspace; tests never
        # enumerate, remove, or alter any external directory or physical media.
        self.temp = tempfile.TemporaryDirectory(prefix="fixture-verify-", dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name).resolve()
        self.assertEqual(self.parent.parent, HERE)
        self.root = self.parent / "capture"
        self.inventory, self.report, self.result = fixture(self.root)

    def save_report(self):
        self.result["report_sha256"] = write_json(self.root / "report.json", self.report)
        write_json(self.root / "resultado.json", self.result)

    def with_sd_destination(self):
        disk = "/sys/devices/platform/rksdmmc/mmc_host/mmc1/mmc1:0001/block/mmcblk1"
        mount = {"Device": "179:65", "Root": "/", "Point": "/mnt/external_sd", "FS": "vfat",
                 "ReadOnly": False, "Writable": True}
        self.inventory["mounts"].append(mount)
        self.inventory["destination"] = {
            "mount": copy.deepcopy(mount), "partition_sysfs": disk + "/mmcblk1p1",
            "disk_sysfs": disk, "disk_name": "mmcblk1", "disk_device": "179:64",
            "card_type": "SD", "removable": "0", "cid_sha256": "a" * 64,
            "disk_bytes": 8053063680, "partition_bytes": 8052015104,
            "start_sector": 2048, "partition_number": 1}
        return self.inventory["destination"]

    def test_sd_destination_and_old_usb_inventory_compatible(self):
        before = V.verify_capture(self.root)
        self.with_sd_destination()
        write_json(self.root / "inventario.json", self.inventory)
        self.assertEqual(V.verify_capture(self.root)["verified_bytes"], before["verified_bytes"])

    def test_sd_invalid_type_geometry_mount_and_overlap(self):
        p = self.with_sd_destination()
        good = copy.deepcopy(self.inventory)
        for field, value, code in (
            ("card_type", "MMC", "invalid_sd_card_type"),
            ("disk_bytes", 7818182656, "invalid_sd_geometry"),
            ("partition_number", 2, "invalid_sd_geometry"),
            ("cid_sha256", "", "invalid_sha256"),
        ):
            with self.subTest(field=field):
                self.inventory = copy.deepcopy(good)
                self.inventory["destination"][field] = value
                write_json(self.root / "inventario.json", self.inventory)
                self.rejects(code)
        self.inventory = copy.deepcopy(good)
        self.inventory["destination"]["mount"]["Writable"] = False
        write_json(self.root / "inventario.json", self.inventory)
        self.rejects("invalid_sd_mount")
        self.inventory = copy.deepcopy(good)
        self.inventory["mounts"].pop()
        write_json(self.root / "inventario.json", self.inventory)
        self.rejects("sd_mount_not_in_inventory")
        self.inventory = copy.deepcopy(good)
        self.inventory["blocks"][0]["sysfs"] = p["partition_sysfs"]
        write_json(self.root / "inventario.json", self.inventory)
        self.rejects("sd_destination_overlaps_source")

    def rejects(self, code=None):
        with self.assertRaises(V.InvalidCapture) as caught:
            V.verify_capture(self.root)
        if code:
            self.assertEqual(str(caught.exception), code)

    def test_two_sources_exact_hashes_and_no_modification(self):
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.iterdir()}
        answer = V.verify_capture(self.root)
        self.assertEqual(answer["status"], "selected_sources_verified_pc")
        self.assertEqual(answer["verified_bytes"], self.report["expected_bytes"])
        self.assertEqual(answer["source_count"], 2)
        self.assertEqual(answer["part_count"], sum(len(r["parts"]) for r in self.report["sources"]))
        for key in ("all_device_storage_copied", "physical_device_state_verified", "restore_tested",
                    "capture_modified", "userdata_content_interpreted"):
            self.assertIs(answer[key], False)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.iterdir()})

    def test_inventory_only_is_distinct_and_has_no_images(self):
        root = self.parent / "inventory"
        fixture(root, inventory_only=True)
        answer = V.verify_capture(root)
        self.assertEqual((answer["status"], answer["verified_bytes"], answer["source_count"]),
                         ("inventory_only", 0, 0))
        (root / "unclaimed.img.partial").write_bytes(b"not a backup")
        with self.assertRaisesRegex(V.InvalidCapture, "unexpected_or_missing_files"):
            V.verify_capture(root)

    def test_corrupt_part(self):
        path = self.root / self.report["sources"][1]["parts"][0]["name"]
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        self.rejects("part_sha256_mismatch")

    def test_short_and_extra_part_bytes(self):
        path = self.root / self.report["sources"][0]["parts"][0]["name"]
        data = path.read_bytes()
        for payload in (data[:-1], data + b"X"):
            with self.subTest(size=len(payload)):
                path.write_bytes(payload)
                self.rejects("part_size_mismatch")

    def test_missing_part_and_extra_part(self):
        path = self.root / self.report["sources"][0]["parts"][0]["name"]
        data = path.read_bytes()
        path.unlink()
        self.rejects("unexpected_or_missing_files")
        path.write_bytes(data)
        (self.root / (("e" * 64) + ".part-000000.img.partial")).write_bytes(b"extra")
        self.rejects("unexpected_or_missing_files")

    def test_failure_marker_precedes_even_corrupt_success_metadata(self):
        for name in V.FAILURES:
            with self.subTest(name=name):
                marker = self.root / name
                marker.write_bytes(b"{")
                with mock.patch.object(V.CaptureReader, "json", side_effect=AssertionError("read success first")):
                    self.rejects("capture_marked_failed")
                marker.unlink()

    def test_duplicate_json_keys_and_nonfinite_numbers(self):
        original = (self.root / "resultado.json").read_bytes()
        for data in (original.replace(b'"status":', b'"status":"inventory_only","status":', 1),
                     original.replace(b'"source_count": 2', b'"source_count": NaN'),
                     original.replace(b'"source_count": 2', b'"source_count": Infinity')):
            with self.subTest(data=data[:40]):
                (self.root / "resultado.json").write_bytes(data)
                self.rejects()

    def test_report_hash_and_aggregate_source_hash(self):
        (self.root / "report.json").write_bytes((self.root / "report.json").read_bytes() + b" ")
        self.rejects("report_sha256_mismatch")
        self.report["sources"][0]["sha256"] = "a" * 64
        self.report["sources"][0]["reread_sha256"] = "a" * 64
        self.save_report()
        self.rejects("source_sha256_mismatch")

    def test_order_and_duplicate_parts(self):
        row = self.report["sources"][0]
        original = copy.deepcopy(row["parts"])
        row["parts"][0], row["parts"][1] = row["parts"][1], row["parts"][0]
        self.save_report()
        self.rejects("part_order_mismatch")
        row["parts"] = copy.deepcopy(original)
        row["parts"][1] = copy.deepcopy(row["parts"][0])
        self.save_report()
        self.rejects("part_order_mismatch")

    def test_traversal_and_invalid_part_basename(self):
        part = self.report["sources"][0]["parts"][0]
        for name in ("../outside", "/outside", r"C:\outside", "a/b.partial", "a\\b.partial", "x:stream", "x."):
            with self.subTest(name=name):
                part["name"] = name
                self.save_report()
                self.rejects()

    def test_boolean_negative_and_oversized_sizes(self):
        for value in (True, False, -1, 0, 1 << 41, "12", 12.0):
            with self.subTest(value=value):
                self.report["sources"][0]["source"]["bytes"] = value
                self.save_report()
                self.rejects("invalid_integer")

    def test_boolean_indices_and_counts(self):
        self.report["sources"][0]["parts"][0]["index"] = False
        self.save_report()
        self.rejects("invalid_integer")
        self.report["sources"][0]["parts"][0]["index"] = 0
        self.result["source_count"] = True
        self.save_report()
        self.rejects("invalid_integer")

    def test_verified_states_and_error_fields(self):
        report = copy.deepcopy(self.report)
        for target, key, value in ((self.report, "status", "failed"),
                                   (self.report["sources"][0], "status", "copying"),
                                   (self.report["sources"][0]["parts"][0], "status", "destination_verified"),
                                   (self.report["sources"][0], "error", "error")):
            with self.subTest(key=key, value=value):
                prior = target.get(key)
                target[key] = value
                self.save_report()
                self.rejects()
                if prior is None:
                    del target[key]
                else:
                    target[key] = prior
        self.assertEqual(self.report, report)

    def test_duplicate_sources_and_limits(self):
        original = copy.deepcopy(self.report["sources"])
        self.report["sources"][1] = copy.deepcopy(self.report["sources"][0])
        self.save_report()
        self.rejects("duplicate_source")
        self.report["sources"] = [copy.deepcopy(original[0]) for _ in range(65)]
        self.result["source_count"] = 65
        self.save_report()
        self.rejects("invalid_integer")
        self.report["sources"] = original
        self.result["source_count"] = 2
        self.report["sources"][0]["parts"] *= 300
        self.save_report()
        self.rejects("invalid_array")

    def test_identity_metadata_and_inventory_mismatch(self):
        self.report["sources"][0]["id"] = "b" * 64
        self.save_report()
        self.rejects("source_id_mismatch")
        self.report["sources"][0]["id"] = V.source_id(self.report["sources"][0]["source"])
        self.save_report()
        self.inventory["blocks"][0]["bytes"] += 1
        write_json(self.root / "inventario.json", self.inventory)
        self.rejects("source_inventory_mismatch")

    def test_preflight_and_total_consistency(self):
        for key, value in (("required_bytes", 1), ("free_bytes_at_preflight", 0), ("expected_bytes", True)):
            with self.subTest(key=key):
                prior = self.report[key]
                self.report[key] = value
                self.save_report()
                self.rejects()
                self.report[key] = prior
        self.report["expected_bytes"] += 1
        self.report["required_bytes"] += 1
        self.save_report()
        self.rejects("total_size_mismatch")

    def test_unknown_field_and_unsupported_physical_claim(self):
        self.result["unexpected"] = 1
        write_json(self.root / "resultado.json", self.result)
        self.rejects("invalid_object_schema")
        del self.result["unexpected"]
        self.result["all_device_storage_copied"] = True
        write_json(self.root / "resultado.json", self.result)
        self.rejects("unsupported_physical_claim")

    def test_wrong_container_types_fail_closed(self):
        for value in ([], {}, True, 1, None):
            with self.subTest(kind=value):
                self.report["sources"][0]["source"]["kind"] = value
                self.save_report()
                self.rejects("invalid_text")

    def test_nullable_holders_and_posix_bus_colons(self):
        for block in self.inventory["blocks"]:
            block["holders"] = None
        write_json(self.root / "inventario.json", self.inventory)
        self.assertEqual(V.verify_capture(self.root)["status"], "selected_sources_verified_pc")
        self.assertEqual(V.posix_path("/dev/block/platform/123:45/by-name/system", "/dev/"),
                         "/dev/block/platform/123:45/by-name/system")

    def test_symlink_file_and_root(self):
        target = self.root / self.report["sources"][0]["parts"][0]["name"]
        linked = self.parent / "external"
        linked.write_bytes(target.read_bytes())
        target.unlink()
        try:
            target.symlink_to(linked)
        except OSError:
            self.skipTest("OS does not permit this test account to create symbolic links")
        self.rejects("symlink_or_reparse_point")
        root_link = self.parent / "capture-link"
        root_link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(V.InvalidCapture, "symlink_or_reparse_point"):
            V.verify_capture(root_link)

    def test_reparse_and_nonordinary_entries(self):
        path = self.root / "resultado.json"
        original_lstat = Path.lstat

        def fake_lstat(item, *args, **kwargs):
            result = original_lstat(item, *args, **kwargs)
            if item == path:
                return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
            return result

        with mock.patch.object(Path, "lstat", fake_lstat):
            self.rejects("symlink_or_reparse_point")
        (self.root / "unexpected-directory").mkdir()
        self.rejects("nonordinary_entry")

    def test_hardlinked_file(self):
        path = self.root / self.report["sources"][0]["parts"][0]["name"]
        try:
            os.link(path, self.parent / "extra-link")
        except OSError:
            self.skipTest("Hard links unavailable on this fixture filesystem")
        self.rejects("hardlinked_file")

    def test_new_failure_marker_during_hashing_is_detected(self):
        real = V.CaptureReader.hash_part
        seen = False

        def mutate(reader, *args):
            nonlocal seen
            value = real(reader, *args)
            if not seen:
                (self.root / "failed-report.json").write_bytes(b"{")
                seen = True
            return value

        with mock.patch.object(V.CaptureReader, "hash_part", mutate):
            self.rejects("capture_directory_changed")

    def test_recorded_devices_are_never_opened(self):
        real = V.os.open
        opened = []

        def observe(path, *args, **kwargs):
            opened.append(Path(path))
            self.assertEqual(Path(path).parent, self.root)
            return real(path, *args, **kwargs)

        with mock.patch.object(V.os, "open", observe):
            V.verify_capture(self.root)
        self.assertTrue(opened)

    def test_cli_safe_json_success_and_failure(self):
        command = [sys.executable, "-B", str(HERE / "verificar-captura.py"), "--capture", str(self.root)]
        done = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["status"], "selected_sources_verified_pc")
        (self.root / "resultado-error.json").write_bytes(b"private contents must not be printed")
        failed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(failed.returncode, 1)
        answer = json.loads(failed.stdout)
        self.assertEqual(answer["error"], "capture_marked_failed")
        self.assertNotIn("private contents", failed.stdout + failed.stderr)
        self.assertNotIn(str(self.root), failed.stdout + failed.stderr)


if __name__ == "__main__":
    unittest.main()
