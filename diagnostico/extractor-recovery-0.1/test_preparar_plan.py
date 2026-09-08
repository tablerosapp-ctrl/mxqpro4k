"""Synthetic host-only plans and real ZIP-verifier integration; no TV or USB."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('prepare_recovery_plan', HERE / 'preparar-plan.py')
APP = importlib.util.module_from_spec(SPEC)
exec(compile((HERE / 'preparar-plan.py').read_bytes(), str(HERE / 'preparar-plan.py'), 'exec'), APP.__dict__)
DEVICE = '11111111-1111-4111-8111-111111111111'
CAPTURE = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
PLAN_FIELDS = {'schema', 'apk_capture_id', 'apk_device_id', 'apk_zip_sha256',
               'expected_dt', 'profile', 'display_name', 'operation'}


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def report(**changes):
    value = {'schema': 'tvbase-recognition-1', 'capture_id': CAPTURE, 'device_id': DEVICE,
             'suggested_profile': 'p291', 'profile_confidence': 'declared', 'display_name': 'Fixture P291',
             'dt_identity': 'fixture_p291', 'android': {'api': 28, 'abis': ['armeabi-v7a']},
             'hardware': {}, 'webview': {'observed': False}, 'export_limits': {'partial': True}}
    value.update(changes)
    return value


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(APP.PRIVATE.is_dir())
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-plan-', dir=APP.PRIVATE)
        self.folder = Path(self.temporary.name).resolve()
        # Verify the absolute cleanup target before TemporaryDirectory can
        # recursively delete the fixture it owns.
        self.assertTrue(self.folder.is_relative_to(APP.PRIVATE.resolve()))
        self.addCleanup(self.temporary.cleanup)
        self.output = self.folder / 'plan.json'

    def archive(self, *, data=None, bad_manifest=False, unsafe_member=False):
        data = report() if data is None else data
        entries = [('informe.json', encoded(data)), ('details/status.txt', b'fixture\n')]
        if unsafe_member:
            entries.append(('../outside.txt', b'not extracted'))
        manifest = {'schema': 'tvbase-recognition-files-1', 'capture_id': data['capture_id'],
                    'files': [{'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
                              for name, body in entries]}
        if bad_manifest:
            manifest['files'][0]['sha256'] = '0' * 64
        name = 'TVBASE-' + data['suggested_profile'] + '-' + data['device_id'][:8] + '-' + data['capture_id'][:8] + '.zip'
        path = self.folder / name
        with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_STORED) as archive:
            for name, body in entries:
                archive.writestr(name, body)
            archive.writestr('manifest.json', encoded(manifest))
        return path

    def item(self, **changes):
        return {'report': report(**changes), 'sha256': 'a' * 64}

    def test_make_plan_exact_contract_and_no_apk_instructions(self):
        item = self.item(dt_identity='vendor,board  soc,family', firmware='bad.zip', offsets=[1, 2],
                         operation='install', source='/dev/block/arbitrary', physical_identity_proven=True)
        before = copy.deepcopy(item)
        plan = APP.make_plan(item)
        self.assertEqual(set(plan), PLAN_FIELDS)
        self.assertEqual(plan['expected_dt'], 'vendor,board  soc,family')
        self.assertEqual(plan['operation'], 'capture_read_only')
        self.assertEqual(plan['apk_capture_id'], CAPTURE)
        self.assertEqual(plan['apk_device_id'], DEVICE)
        self.assertEqual(item, before)

    def test_dt_is_exact_not_normalized(self):
        for dt in ('gxlx2_p291_1g', 'vendor,board  soc,family', ' leading trailing ', 'x' * 4096):
            with self.subTest(dt_length=len(dt)):
                self.assertEqual(APP.make_plan(self.item(dt_identity=dt))['expected_dt'], dt)

    def test_reject_unknown_missing_control_or_excessive_dt(self):
        values = [None, '', '   ', 'unknown', ' UNKNOWN ', 'desconocido', 'n/a', 'null',
                  'x\x00y', 'x\ny', 'x\ty', 'x' * 4097, 'á' * 2049, '\ud800', {'dt': 'board'}]
        for dt in values:
            with self.subTest(kind=type(dt).__name__, length=len(dt) if isinstance(dt, str) else None):
                with self.assertRaises(APP.InvalidPlan):
                    APP.make_plan(self.item(dt_identity=dt))
        item = self.item()
        del item['report']['dt_identity']
        with self.assertRaises(APP.InvalidPlan):
            APP.make_plan(item)

    def test_profile_ascii_boundaries_and_rejections(self):
        for profile in ('p291', 'p271', 'rockchip-desconocido', 'a' * 80):
            with self.subTest(valid=profile):
                self.assertEqual(APP.make_plan(self.item(suggested_profile=profile))['profile'], profile)
        for profile in ('', 'p291_x', 'P291', 'p291/x', '../p291', 'á', 'a' * 81, 'p291\n', None):
            with self.subTest(kind=type(profile).__name__):
                with self.assertRaises(APP.InvalidPlan):
                    APP.make_plan(self.item(suggested_profile=profile))

    def test_uuid_digest_schema_and_display_validation(self):
        for field, value in [('capture_id', 'not-a-uuid'), ('device_id', '0' * 32),
                             ('capture_id', CAPTURE.upper()), ('device_id', '00000000-0000-0000-0000-000000000000'),
                             ('schema', 'other'), ('display_name', ''), ('display_name', 'x' * 257),
                             ('display_name', 'line\nbreak')]:
            with self.subTest(field=field):
                with self.assertRaises(APP.InvalidPlan):
                    APP.make_plan(self.item(**{field: value}))
        for digest in ('a' * 63, 'A' * 64, 'g' * 64, None):
            with self.subTest(digest_type=type(digest).__name__):
                item = self.item()
                item['sha256'] = digest
                with self.assertRaises(APP.InvalidPlan):
                    APP.make_plan(item)

    def test_real_zip_workflow_fsync_readback_and_source_preserved(self):
        archive = self.archive(data=report(dt_identity='vendor,board  soc,family'))
        before = archive.read_bytes()
        result = APP.prepare_plan(archive, self.output)
        self.assertEqual(result['state'], 'plan_verified_local')
        self.assertTrue(result['file_fsync'] and result['readback_verified'])
        self.assertFalse(result['usb_modified'] or result['physical_identity_proven'] or result['installation_authorized'])
        saved = self.output.read_bytes()
        plan = json.loads(saved)
        self.assertEqual(set(plan), PLAN_FIELDS)
        self.assertEqual(plan['apk_zip_sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(plan['expected_dt'], 'vendor,board  soc,family')
        self.assertEqual(result['sha256'], hashlib.sha256(saved).hexdigest())
        self.assertEqual(archive.read_bytes(), before)
        self.assertEqual(set(self.folder.iterdir()), {archive, self.output})
        self.assertEqual(self.output.stat().st_nlink, 1)

    def test_real_verifier_rejects_bad_manifest_before_output_creation(self):
        archive = self.archive(bad_manifest=True)
        with self.assertRaises(APP.InvalidPlan):
            APP.prepare_plan(archive, self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_name('plan.json.partial').exists())

    def test_real_verifier_rejects_unsafe_member_before_output_creation(self):
        archive = self.archive(unsafe_member=True)
        with self.assertRaises(APP.InvalidPlan):
            APP.prepare_plan(archive, self.output)
        self.assertEqual(set(self.folder.iterdir()), {archive})

    def test_real_verifier_rejects_tampered_payload_crc(self):
        archive = self.archive()
        raw = archive.read_bytes()
        self.assertIn(b'fixture\n', raw)
        archive.write_bytes(raw.replace(b'fixture\n', b'Fixture\n', 1))
        with self.assertRaises(APP.InvalidPlan):
            APP.prepare_plan(archive, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_final_and_partial_preserved(self):
        archive = self.archive()
        self.output.write_bytes(b'prior private plan')
        with self.assertRaises(APP.InvalidPlan):
            APP.prepare_plan(archive, self.output)
        self.assertEqual(self.output.read_bytes(), b'prior private plan')
        other = self.folder / 'other.json'
        partial = other.with_name(other.name + '.partial')
        partial.write_bytes(b'prior interrupted preparation')
        with self.assertRaises(FileExistsError):
            APP.prepare_plan(archive, other)
        self.assertEqual(partial.read_bytes(), b'prior interrupted preparation')
        self.assertFalse(other.exists())

    def test_reject_nonprivate_missing_parent_and_ambiguous_paths(self):
        verifier = APP.load_importer()
        for path in (APP.ROOT / 'plan-public.json', self.folder / 'missing' / 'plan.json',
                     self.folder / '..' / 'plan.json', self.folder / 'con.json',
                     self.folder / 'a.json:stream', self.folder / 'file.txt'):
            with self.subTest(case=path.name):
                with self.assertRaises(APP.InvalidPlan):
                    APP.output_path(path, verifier)

    def test_fsync_failure_preserves_partial_and_does_not_publish(self):
        archive = self.archive()
        with mock.patch.object(APP.os, 'fsync', side_effect=OSError('fixture EIO')):
            with self.assertRaises(OSError):
                APP.prepare_plan(archive, self.output)
        self.assertFalse(self.output.exists())
        self.assertTrue(self.output.with_name('plan.json.partial').is_file())

    def test_temporary_readback_failure_does_not_publish(self):
        archive = self.archive()
        with mock.patch.object(APP, '_readback', side_effect=APP.InvalidPlan('Fixture: relectura diferente.')):
            with self.assertRaises(APP.InvalidPlan):
                APP.prepare_plan(archive, self.output)
        self.assertFalse(self.output.exists())
        self.assertTrue(self.output.with_name('plan.json.partial').is_file())

    def test_atomic_publish_race_does_not_overwrite(self):
        archive = self.archive()
        real_link = os.link

        def race(temporary, final):
            Path(final).write_bytes(b'concurrent plan')
            return real_link(temporary, final)

        with mock.patch.object(APP.os, 'link', side_effect=race):
            with self.assertRaises(FileExistsError):
                APP.prepare_plan(archive, self.output)
        self.assertEqual(self.output.read_bytes(), b'concurrent plan')
        self.assertTrue(self.output.with_name('plan.json.partial').is_file())

    def test_cli_success_and_failure_do_not_print_private_identity(self):
        archive = self.archive(data=report(display_name='PRIVATE-NICKNAME'))
        stream = io.StringIO()
        with mock.patch('sys.stdout', stream):
            code = APP.main(['--apk-report', str(archive), '--output', str(self.output)])
        self.assertEqual(code, 0)
        shown = stream.getvalue()
        for private in (DEVICE, CAPTURE, 'PRIVATE-NICKNAME', str(archive), str(self.output)):
            self.assertNotIn(private, shown)
        self.assertEqual(json.loads(shown)['state'], 'plan_verified_local')
        stream = io.StringIO()
        with mock.patch('sys.stdout', stream):
            code = APP.main(['--apk-report', str(archive), '--output', str(self.output)])
        self.assertEqual(code, 1)
        for private in (DEVICE, CAPTURE, 'PRIVATE-NICKNAME', str(archive), str(self.output)):
            self.assertNotIn(private, stream.getvalue())
        self.assertEqual(json.loads(stream.getvalue())['state'], 'failed')


if __name__ == '__main__':
    unittest.main()
