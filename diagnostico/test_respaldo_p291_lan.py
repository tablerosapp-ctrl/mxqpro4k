"""PC-only regression tests for respaldar-p291-lan.py; never launches ADB.

Run from the project: python -B diagnostico/test_respaldo_p291_lan.py
The generated receipt records the tested source and test hashes. Fixture images
contain all byte values in 64 KiB, including CR, LF and NUL. A local Python child
replaces ADB's stdout; remote metadata and SHA responses are explicit mocks.
No test instantiates Backup normally, opens the private TV session or contacts TV.

Public fixture addresses, deliberately literal for review:
- 10.23.45.67: fictional RFC1918 test endpoint; never contacted.
- 203.0.113.99: TEST-NET-3 public-address rejection fixture; never contacted.
- fixture.invalid: reserved invalid hostname; never resolved or contacted.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import unittest
from unittest import mock
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'diagnostico/respaldar-p291-lan.py'
DEFAULT_RECEIPT = ROOT / 'diagnostico/respaldo-p291-lan/EVIDENCIA-SANEADA.json'
spec = importlib.util.spec_from_file_location('p291_backup_under_test', SOURCE)
backup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup_module)
LOCAL_POPEN = backup_module.subprocess.Popen
FIXTURE_BYTES = bytes(range(256))*256
FIXTURE_SHA256 = hashlib.sha256(FIXTURE_BYTES).hexdigest()


class GuardTests(unittest.TestCase):
    def test_positive_private_endpoint(self):
        self.assertEqual(backup_module.parse_target('10.23.45.67:5555'), '10.23.45.67:5555')

    def test_positive_block_alias(self):
        listing = 'brw------- 1 root root 179, 11 2019-12-31 21:00 /dev/block/boot\r\r\n'
        self.assertEqual(backup_module.parse_alias(listing, 'boot'), (179, 11))

    def test_positive_read_only_mount(self):
        text = '/dev/block/system /system ext4 ro,seclabel 0 0\r\r\n'
        self.assertEqual(backup_module.parse_mounts(text, 'system', True),
                         [{'mountpoint': '/system', 'filesystem': 'ext4', 'options': 'ro,seclabel'}])

    def test_negative_public_endpoint(self):
        with self.assertRaises(RuntimeError):
            backup_module.parse_target('203.0.113.99:5555')

    def test_negative_wrong_port(self):
        with self.assertRaises(RuntimeError):
            backup_module.parse_target('10.23.45.67:5556')

    def test_negative_hostname(self):
        with self.assertRaises(ValueError):
            backup_module.parse_target('fixture.invalid:5555')

    def test_negative_symlink_alias(self):
        text = 'lrwxrwxrwx 1 root root 1 2019-12-31 21:00 /dev/block/boot -> /tmp/other'
        with self.assertRaises(RuntimeError):
            backup_module.parse_alias(text, 'boot')

    def test_negative_read_write_mount(self):
        with self.assertRaises(RuntimeError):
            backup_module.parse_mounts('/dev/block/system /system ext4 rw,seclabel 0 0', 'system', True)

    def test_negative_wrong_mountpoint(self):
        with self.assertRaises(RuntimeError):
            backup_module.parse_mounts('/dev/block/system /wrong ext4 ro,seclabel 0 0', 'system', True)

    def test_closed_partition_stages(self):
        self.assertEqual(backup_module.STAGES['critical'],
                         ('bootloader', 'recovery', 'boot', 'misc', 'env', 'dtbo', 'vbmeta', 'tee'))
        self.assertEqual(backup_module.STAGES['system'], ('system', 'vendor', 'product', 'odm'))
        self.assertNotIn('data', backup_module.PARTITIONS)
        self.assertNotIn('cache', backup_module.PARTITIONS)


class BinaryProtocolTests(unittest.TestCase):
    def run_fixture(self, mode):
        private = (ROOT/'privado').resolve()
        self.assertTrue(private.is_relative_to(ROOT) and private != ROOT)
        private.mkdir(exist_ok=True)
        # Only this newly generated and checked temporary directory is removed.
        with tempfile.TemporaryDirectory(prefix='fixture-backup-formal-', dir=private) as generated:
            output = Path(generated).resolve()
            self.assertTrue(output.is_relative_to(private))
            instance = backup_module.Backup.__new__(backup_module.Backup)
            instance.output = output
            instance.receipt = output/'manifest.json'
            instance.target = 'fixture.invalid:5555'
            instance.state = {'partitions': [], 'commands': []}
            instance.metadata = mock.Mock(return_value={
                'major': 179, 'minor': 11, 'bytes': len(FIXTURE_BYTES), 'mounts': []})
            expected_remote_hash = '0'*64 if mode == 'bad_sha' else FIXTURE_SHA256
            instance.command = mock.Mock(return_value=expected_remote_hash+'  /dev/block/boot')
            launches = []

            def substitute_adb(argv, **kwargs):
                self.assertEqual(Path(argv[0]).resolve(), backup_module.ADB.resolve())
                self.assertEqual(argv[1:4], ['-s', 'fixture.invalid:5555', 'exec-out'])
                self.assertEqual(len(argv), 5)
                self.assertIn('/system/bin/toybox cat /dev/block/boot;', argv[4])
                nonce = re.search(r'TVBASE_RAW_([0-9a-f]{32})_EXIT', argv[4]).group(1)
                if mode == 'wrong_nonce':
                    nonce = 'f'*32 if nonce != 'f'*32 else 'a'*32
                status = 7 if mode == 'exit_7' else 0
                footer = f'\nTVBASE_RAW_{nonce}_EXIT={status}\n'.encode('ascii')
                suffix = b'EXTR' if mode == 'extra_four_bytes' else b''
                payload_length = len(FIXTURE_BYTES)-(1 if mode == 'short_payload' else 0)
                local_code = (
                    'import sys;'
                    f'sys.stdout.buffer.write((bytes(range(256))*256)[:{payload_length}]);'
                    f'sys.stdout.buffer.write({footer+suffix!r});'
                    'sys.stdout.buffer.flush()'
                )
                launches.append('local_python_fixture')
                # No ADB invocation reaches the OS: use the saved, real Popen
                # exclusively for Python's local binary-output fixture process.
                return LOCAL_POPEN([sys.executable, '-B', '-c', local_code], **kwargs)

            with mock.patch.dict(backup_module.PARTITIONS, {'boot': (179, 11, len(FIXTURE_BYTES))}), \
                    mock.patch.object(backup_module.subprocess, 'Popen', side_effect=substitute_adb), \
                    contextlib.redirect_stdout(io.StringIO()):
                if mode == 'success':
                    instance.partition('boot')
                else:
                    with self.assertRaises(RuntimeError):
                        instance.partition('boot')
            self.assertEqual(launches, ['local_python_fixture'])
            row = instance.state['partitions'][0]
            final = output/'boot.img'
            partial = output/'boot.img.parcial'
            if mode == 'success':
                self.assertEqual(final.read_bytes(), FIXTURE_BYTES)
                self.assertEqual(final.stat().st_size, len(FIXTURE_BYTES))
                self.assertFalse(partial.exists())
                self.assertEqual(row['state'], 'verified')
                self.assertEqual(row['copy_exit'], 0)
                self.assertEqual(row['transport_exit'], 0)
                self.assertTrue(row['footer_verified'])
                self.assertEqual(row['sha256'], FIXTURE_SHA256)
                self.assertEqual(instance.metadata.call_count, 2)
            else:
                self.assertFalse(final.exists())
                self.assertTrue(partial.exists())
                self.assertNotEqual(row['state'], 'verified')
                if mode in ('exit_7', 'bad_sha', 'wrong_nonce', 'short_payload'):
                    self.assertGreater(partial.stat().st_size, len(FIXTURE_BYTES))
                if mode == 'exit_7':
                    self.assertEqual(row['copy_exit'], 7)
                    self.assertTrue(row['footer_verified'])
                if mode == 'bad_sha':
                    self.assertEqual(row['copy_exit'], 0)
                    self.assertNotEqual(row['pc_sha256'], row['remote_sha256_after'])
            self.assertTrue(instance.receipt.is_file())

    def test_binary_preserves_cr_lf_nul_and_removes_only_verified_footer(self):
        self.run_fixture('success')

    def test_binary_remote_exit_7_keeps_partial(self):
        self.run_fixture('exit_7')

    def test_binary_remote_sha_mismatch_keeps_partial(self):
        self.run_fixture('bad_sha')

    def test_binary_wrong_nonce_is_rejected(self):
        self.run_fixture('wrong_nonce')

    def test_binary_four_extra_bytes_are_rejected(self):
        self.run_fixture('extra_four_bytes')

    def test_binary_one_byte_short_payload_is_rejected(self):
        self.run_fixture('short_payload')


class RecordedResult(unittest.TextTestResult):
    def startTest(self, test):
        self.started_at = time.monotonic()
        super().startTest(test)

    def stopTest(self, test):
        failures = [item[0] for item in self.failures+self.errors]
        self.records.append({'test': test.id(), 'passed': test not in failures,
                             'seconds': round(time.monotonic()-self.started_at, 4)})
        super().stopTest(test)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    receipt = args.receipt.resolve()
    if not receipt.is_relative_to(ROOT/'diagnostico'):
        raise SystemExit('Receipt must stay under this project diagnostico directory')
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    began = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    after = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    passed = result.wasSuccessful() and before == after
    evidence = {
        'schema': 1, 'state': 'passed' if passed else 'failed',
        'recorded_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'source': SOURCE.relative_to(ROOT).as_posix(), 'source_sha256': before,
        'source_unchanged_after_tests': before == after,
        'tests_source': Path(__file__).resolve().relative_to(ROOT).as_posix(),
        'tests_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'tests_run': result.testsRun, 'seconds': round(time.monotonic()-began, 4),
        'results': result.records, 'binary_fixture_bytes': len(FIXTURE_BYTES),
        'binary_fixture_sha256': FIXTURE_SHA256,
        'guard_positive_cases': 3, 'guard_negative_cases': 6,
        'closed_stage_selection_cases': 1, 'binary_protocol_cases': 6,
        'adb_launched': False, 'tv_contacted': False, 'usb_accessed': False,
        'real_backup_modified': False, 'physically_validated_by_this_suite': False,
        'scope': [
            'Imports existing source; does not instantiate Backup normally or read TV session.',
            'Metadata and remote SHA are mocks; local Python replaces the ADB binary stream.',
            'Exercises real image writing, fsync, local reread, footer validation and rename.',
            'Temporary fixtures are created and removed only under private workspace storage.',
            'Does not establish device compatibility, network behavior or restoration.',
        ],
        'public_fixture_addresses': {
            '10.23.45.67': 'Fictional RFC1918 endpoint for positive/private-port checks; never contacted.',
            '203.0.113.99': 'TEST-NET-3 address for public endpoint rejection; never contacted.',
        },
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    backup_module.atomic_json(receipt, evidence)
    print(json.dumps({'state': evidence['state'], 'tests': result.testsRun,
                      'receipt': receipt.relative_to(ROOT).as_posix()}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
