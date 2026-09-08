"""PC-only negative protocol and one-launch checks. No ADB subprocess is run."""
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("entry_lan", HERE / "entrada-lan09.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NONCE = "1234567890abcdef1234567890abcdef"
APK = "/data/app/local.tvbase.acceso-abc==/base.apk"


def value(state):
    result = {"state": state, "nonce": NONCE, "reset_requested": False,
              "userdata_wiped": False, "firmware_images_written": False}
    if state == "prepared":
        result.update(env_readback_verified=True, bcb_readback_verified=True,
                      manifest_sha256="a" * 64,
                      report="/mnt/media_rw/ABCD-1234/TVBASE-entrada09-" + NONCE)
    return result


def output(*values, exit_code=0, nonce=NONCE):
    return ("\n".join("TVBASE_ENTRY:" + json.dumps(v) for v in values)
            + "\n\nTVBASE_EXIT:" + nonce + ":" + str(exit_code) + "\n").encode()


class Protocol(unittest.TestCase):
    def reject(self, raw, op="status", code=0):
        with self.assertRaises(m.ClientError):
            m.parse_result(raw, NONCE, op, code)

    def test_valid_launch(self):
        self.assertEqual(m.parse_result(output(value("stage"), value("launched")), NONCE, "launch")["result"]["state"], "launched")

    def test_valid_prepared(self):
        self.assertEqual(m.parse_result(output(value("prepared")), NONCE, "status")["remote_exit"], 0)

    def test_valid_stage(self):
        self.assertEqual(m.parse_result(output(value("stage")), NONCE, "status")["result"]["state"], "stage")

    def test_incomplete_remote_one_is_preserved(self):
        self.assertEqual(m.parse_result(output(value("incomplete"), exit_code=1), NONCE, "launch")["result"]["state"], "incomplete")

    def test_incomplete_stored_with_zero(self):
        self.assertEqual(m.parse_result(output(value("incomplete")), NONCE, "status")["result"]["state"], "incomplete")

    def test_no_exit(self):
        self.reject(b"TVBASE_ENTRY:" + json.dumps(value("stage")).encode() + b"\n")

    def test_exit_only(self):
        self.reject(("TVBASE_EXIT:" + NONCE + ":0\n").encode())

    def test_no_final_newline(self):
        self.reject(output(value("stage"))[:-1])

    def test_wrong_event_nonce(self):
        v = value("stage"); v["nonce"] = "0" * 32
        self.reject(output(v))

    def test_wrong_exit_nonce(self):
        self.reject(output(value("stage"), nonce="0" * 32))

    def test_trailing_entry(self):
        self.reject(output(value("stage")) + b"TVBASE_ENTRY:{}\n")

    def test_duplicate_exit(self):
        self.reject(output(value("stage")) + ("TVBASE_EXIT:" + NONCE + ":0\n").encode())

    def test_two_terminals(self):
        self.reject(output(value("prepared"), value("incomplete")))

    def test_stage_after_terminal(self):
        self.reject(output(value("prepared"), value("stage")))

    def test_duplicate_json_key(self):
        raw = output(value("stage")).replace(b'"state": "stage"', b'"state": "stage", "state": "prepared"')
        self.reject(raw)

    def test_nan_json(self):
        raw = output(value("stage")).replace(b'"state": "stage"', b'"extra": NaN, "state": "stage"')
        self.reject(raw)

    def test_unknown_state(self):
        self.reject(output(value("success")))

    def test_launched_is_not_status(self):
        self.reject(output(value("launched")))

    def test_prepared_is_not_launch(self):
        self.reject(output(value("prepared")), "launch")

    def test_launch_stage_is_not_ack(self):
        self.reject(output(value("stage")), "launch")

    def test_prepared_without_readback(self):
        v = value("prepared"); del v["env_readback_verified"]
        self.reject(output(v))

    def test_prepared_numeric_true(self):
        v = value("prepared"); v["env_readback_verified"] = 1
        self.reject(output(v))

    def test_prepared_empty_sha(self):
        v = value("prepared"); v["manifest_sha256"] = ""
        self.reject(output(v))

    def test_prepared_foreign_report(self):
        v = value("prepared"); v["report"] = "/mnt/media_rw/../../data"
        self.reject(output(v))

    def test_unexpected_reset(self):
        v = value("stage"); v["reset_requested"] = True
        self.reject(output(v))

    def test_missing_effect_field(self):
        v = value("stage"); del v["userdata_wiped"]
        self.reject(output(v))

    def test_nonzero_launch(self):
        self.reject(output(value("launched"), exit_code=1), "launch")

    def test_local_failure(self):
        self.reject(output(value("stage")), code=1)

    def test_leading_zero_exit(self):
        self.reject(output(value("stage")).replace(b":0\n", b":00\n"))

    def test_utf8_corrupt(self):
        self.reject(b"\xff" + output(value("stage")))

    def test_crlf_not_binary_exec(self):
        self.reject(output(value("stage")).replace(b"\n", b"\r\n"))

    def test_unknown_output(self):
        self.reject(b"success\n" + output(value("stage")))

    def test_output_limit(self):
        self.reject(b" " * (m.MAX_OUTPUT + 1))

    def test_shell_injection_rejected(self):
        for apk in (APK + ";id", "/data/app/../base.apk", "/data/app/a$(id)/base.apk", "/data/app/a'/base.apk"):
            with self.subTest(apk=apk), self.assertRaises(m.ClientError):
                m.entry_command(apk, NONCE, "launch")

    def test_only_public_helper_operations(self):
        for operation in ("prepare", "reboot", "status;id"):
            with self.subTest(operation=operation), self.assertRaises(m.ClientError):
                m.entry_command(APK, NONCE, operation)

    def test_nonce_injection(self):
        with self.assertRaises(m.ClientError):
            m.entry_command(APK, NONCE + ";id", "launch")

    def test_command_uses_existing_root_and_no_reset(self):
        command = m.entry_command(APK, NONCE, "status")
        self.assertIn("/system/xbin/su 0", command)
        self.assertIn("PreparationHelper status " + NONCE, command)
        self.assertNotIn("timeout", command)
        self.assertNotIn("reboot", command)

    def test_check_marker_required(self):
        with self.assertRaises(m.ClientError):
            m.check_output(b"0\n", NONCE, "root_uid", 0)


class Workflow(unittest.TestCase):
    def setUp(self):
        m.PRIVATE.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=m.PRIVATE, prefix="test-lan09-")
        self.home = Path(self.temp.name)
        self.private = self.home / "private"
        self.session = self.home / "session.json"
        self.session.write_text(json.dumps({"target": "192.168.10.25:5555"}))
        self.calls = []
        self.mode = "normal"

    def tearDown(self):
        self.temp.cleanup()

    def factory(self, attempt, target):
        owner = self
        class Fake:
            def run(self, label, command):
                owner.calls.append(label)
                nonce = attempt.data["nonce"]
                if label in ("launch", "status"):
                    saved = json.loads(attempt.path.read_text())
                    assert saved["launch_issued"] is True
                    assert saved["nonce"] == nonce
                    assert json.loads((owner.private / "LAN09-ACTIVE.json").read_text())["nonce"] == nonce
                    if owner.mode == "timeout" and label == "launch":
                        raise subprocess.TimeoutExpired(["fixture-PC-no-ADB"], 30, output=b"partial")
                    v = value("launched" if label == "launch" else "stage"); v["nonce"] = nonce
                    return output(v, nonce=nonce), 0
                responses = {
                    "shell_uid": b"2000\n", "root_uid": b"0\n", "api": b"28\n",
                    "dt": b"gxlx2_p291_1g\0", "build": (m.BUILD + "\n").encode(), "kernel": b"4.9.113\n",
                    "apk_path": ("package:" + APK + "\n").encode(), "apk_size": (str(m.APK_BYTES) + "\n").encode(),
                    "apk_sha": (m.APK_SHA + "  " + APK + "\n").encode(), "active": b""
                }
                if owner.mode == "active": responses["active"] = (m.ACTIVE + "\n").encode()
                if owner.mode == "wrong_hash": responses["apk_sha"] = ("0" * 64 + "  " + APK + "\n").encode()
                if owner.mode == "wrong_dt": responses["dt"] = b"gxlx_p271_1g\0"
                return responses[label] + ("\nTVBASE_CHECK:" + nonce + ":" + label + ":0\n").encode(), 0
        return Fake()

    def prepare(self, accepted=True):
        with redirect_stdout(io.StringIO()):
            return m.prepare(self.session, self.private, accepted, "Fixture PC; no autorización física", self.factory)

    def stored_path(self):
        return Path(json.loads((self.private / "LAN09-ACTIVE.json").read_text())["attempt"])

    def test_missing_acceptance_has_no_io_or_adb(self):
        with self.assertRaises(m.ClientError): self.prepare(False)
        self.assertEqual(self.calls, [])
        self.assertFalse(self.private.exists())

    def test_missing_note_has_no_adb(self):
        with self.assertRaises(m.ClientError):
            m.prepare(self.session, self.private, True, "", self.factory)
        self.assertEqual(self.calls, [])

    def test_preexisting_active_blocks_launch(self):
        self.mode = "active"
        with self.assertRaises(m.ClientError): self.prepare()
        self.assertNotIn("launch", self.calls)
        self.assertFalse(json.loads(self.stored_path().read_text())["launch_issued"])

    def test_wrong_hash_blocks_launch(self):
        self.mode = "wrong_hash"
        with self.assertRaises(m.ClientError): self.prepare()
        self.assertNotIn("launch", self.calls)

    def test_wrong_dt_blocks_launch(self):
        self.mode = "wrong_dt"
        with self.assertRaises(m.ClientError): self.prepare()
        self.assertNotIn("launch", self.calls)

    def test_launch_is_once_and_nonce_durable_before_call(self):
        attempt = self.prepare()
        self.assertEqual(attempt.data["state"], "launched")
        with self.assertRaises(m.ClientError): self.prepare()
        self.assertEqual(self.calls.count("launch"), 1)

    def test_timeout_never_relaunches_and_status_can_continue(self):
        self.mode = "timeout"
        with self.assertRaises(subprocess.TimeoutExpired): self.prepare()
        path = self.stored_path()
        before = json.loads(path.read_text())
        self.assertEqual(before["state"], "indeterminate")
        self.assertTrue(before["launch_issued"])
        self.mode = "normal"
        result = m.status(path, self.session, self.private, self.factory)
        self.assertEqual(result.data["nonce"], before["nonce"])
        self.assertEqual(self.calls.count("launch"), 1)
        self.assertEqual(self.calls.count("status"), 1)

    def test_failed_preflight_cannot_be_status_relaunch(self):
        self.mode = "active"
        with self.assertRaises(m.ClientError): self.prepare()
        before = list(self.calls)
        with self.assertRaises(m.ClientError):
            m.status(self.stored_path(), self.session, self.private, self.factory)
        self.assertEqual(self.calls, before)

    def test_session_target_change_rejected_before_adb(self):
        attempt = self.prepare()
        self.session.write_text(json.dumps({"target": "192.168.10.26:5555"}))
        before = list(self.calls)
        with self.assertRaises(m.ClientError): m.status(attempt.path, self.session, self.private, self.factory)
        self.assertEqual(self.calls, before)

    def test_public_ip_rejected(self):
        self.session.write_text(json.dumps({"target": "198.51.100.25:5555"}))
        with self.assertRaises(m.ClientError): self.prepare()
        self.assertEqual(self.calls, [])

    def test_transport_timeout_records_without_remote_kill(self):
        target = m.load_session(self.session)
        attempt = m.new_attempt(self.private, self.session, target, "Fixture PC")
        def runner(args, **kwargs):
            self.assertEqual(args[3], "exec-out")
            self.assertEqual(len(args), 5)
            self.assertNotIn("shell", kwargs)
            self.assertNotIn("kill", args[-1])
            raise subprocess.TimeoutExpired(args, 30, output=b"partial", stderr=b"lost")
        transport = m.Transport(attempt, target, runner=runner)
        with self.assertRaises(m.ClientError): transport.run("status", m.entry_command(APK, attempt.data["nonce"], "status"))
        row = json.loads(attempt.path.read_text())["observations"][0]
        self.assertTrue(row["timeout"])
        self.assertFalse(row["remote_cancel_requested"])
        self.assertEqual(row["stdout_sha256"], m.digest(b"partial"))

    def test_persistence_error_prevents_launch(self):
        real = m.durable_replace
        def failing(path, data):
            if path.name == "attempt.json" and json.loads(data)["state"] == "launch_in_flight":
                raise OSError("fixture fsync failure")
            return real(path, data)
        with patch.object(m, "durable_replace", failing):
            with self.assertRaises(OSError): self.prepare()
        self.assertNotIn("launch", self.calls)


class LocalPipes(unittest.TestCase):
    def test_small_pc_child_output_complete(self):
        result = m.bounded_process([sys.executable, "-c", "import sys;print('ok');sys.stderr.write('error\\n')"], 5, 0)
        self.assertEqual(result.stdout.strip(), b"ok")
        self.assertEqual(result.stderr.strip(), b"error")
        self.assertFalse(result.output_limit)
        self.assertFalse(result.incomplete_pipe)

    def test_excessive_pc_child_output_is_bounded(self):
        result = m.bounded_process([sys.executable, "-c", "import os;os.write(1,b'x'*1048576)"], 5, 0)
        self.assertTrue(result.output_limit)
        self.assertLessEqual(len(result.stdout), m.MAX_OUTPUT)
        self.assertLessEqual(len(result.stderr), m.MAX_OUTPUT)

    def test_timeout_only_stops_pc_child(self):
        result = m.bounded_process([sys.executable, "-c", "import time;print('partial',flush=True);time.sleep(5)"], 0.1, 0)
        self.assertTrue(result.timed_out)
        self.assertIn(b"partial", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
