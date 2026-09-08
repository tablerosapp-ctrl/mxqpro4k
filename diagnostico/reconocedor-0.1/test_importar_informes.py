"""Fixtures sintéticos locales: sin TV, USB, red, credenciales ni drivers reales."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('recognition_import', HERE / 'importar-informes.py')
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)
DEVICE_A = '11111111-1111-4111-8111-111111111111'
DEVICE_B = '22222222-2222-4222-8222-222222222222'
CAPTURE_A = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
CAPTURE_B = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def report(**changes):
    value = {'schema': 'tvbase-recognition-1', 'capture_id': CAPTURE_A, 'device_id': DEVICE_A,
             'suggested_profile': 'p291', 'profile_confidence': 'declared', 'display_name': 'Fixture P291',
             'android': {'api': 28, 'abis': ['armeabi-v7a']}, 'hardware': {'dt_id': 'fixture_p291'},
             'webview': {'observed': False}, 'export_limits': {'partial': True}, 'capture_status': 'partial'}
    value.update(changes)
    return value


class ImportTests(unittest.TestCase):
    def setUp(self):
        private = APP.ROOT / 'privado'
        private.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-reconocedor-', dir=private)
        self.folder = Path(self.temporary.name).resolve()
        # Antes del borrado recursivo automático de TemporaryDirectory se fija
        # y comprueba que el único destino queda dentro del privado del proyecto.
        self.assertTrue(self.folder.is_relative_to(private.resolve()))
        self.addCleanup(self.temporary.cleanup)
        self.source = self.folder / 'source'
        self.source.mkdir()

    def archive(self, *, data=None, raw_report=None, extra=(), edit_manifest=None, mode=None):
        data = report() if data is None else data
        entries = [('informe.json', encoded(data) if raw_report is None else raw_report),
                   ('details/estado.txt', b'Fixture: parcial\n'), ('drivers/fixture.ko', b'\x00\xfffixture')]
        entries.extend(extra)
        manifest = {'schema': 'tvbase-recognition-files-1', 'capture_id': data['capture_id'],
                    'files': [{'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
                              for name, body in entries]}
        if edit_manifest:
            edit_manifest(manifest)
        name = 'TVBASE-' + data['suggested_profile'] + '-' + data['device_id'][:8] + '-' + data['capture_id'][:8] + '.zip'
        path = self.source / name
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as archive:
                for name, body in entries:
                    if mode is not None and name == 'drivers/fixture.ko':
                        info = zipfile.ZipInfo(name)
                        info.create_system = 3
                        info.external_attr = mode << 16
                        archive.writestr(info, body)
                    else:
                        archive.writestr(name, body)
                archive.writestr('manifest.json', encoded(manifest))
        return path

    def reject(self, path):
        with self.assertRaises(APP.InvalidCapture):
            APP.verify_archive(path, emit=None)

    def test_partial_valid_and_verify_only_writes_nothing(self):
        path = self.archive()
        before = path.read_bytes()
        names = set(self.folder.rglob('*'))
        result = APP.import_batch(self.source, verify_only=True, emit=None)
        self.assertEqual(result['state'], 'verified_only')
        self.assertEqual(result['written_files'], 0)
        self.assertEqual(set(self.folder.rglob('*')), names)
        self.assertEqual(path.read_bytes(), before)

    def test_failed_capture_is_not_corrupt_archive(self):
        path = self.archive(data=report(capture_status='failed', export_limits={'denied': ['fixture']}))
        value = APP.verify_archive(path, emit=None)
        self.assertEqual(value['report']['capture_status'], 'failed')

    def test_deflate_with_streaming_data_descriptors(self):
        path = self.archive()
        with zipfile.ZipFile(path) as existing:
            members = [(x.filename, existing.read(x)) for x in existing.infolist()]

        class NonSeekable(io.BytesIO):
            def seek(self, *args):
                raise OSError('Fixture de salida sin seek')

            def seekable(self):
                return False

        buffer = NonSeekable()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in members:
                archive.writestr(name, data)
        path.write_bytes(buffer.getvalue())
        with zipfile.ZipFile(path) as archive:
            self.assertTrue(all(x.flag_bits & 8 for x in archive.infolist()))
        result = APP.verify_archive(path, emit=None)
        self.assertEqual(result['member_count'], 4)

    def test_import_two_installation_identities_and_candidate_profiles(self):
        one = self.archive()
        two = self.archive(data=report(device_id=DEVICE_B, capture_id=CAPTURE_B,
                                       suggested_profile='p271', display_name='Fixture P271'))
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (one, two)}
        output = self.folder / 'imported'
        result = APP.import_batch(self.source, output, emit=None)
        self.assertEqual(result['app_installation_identity_count'], 2)
        index = json.loads((output / 'privado/catalogo.json').read_text(encoding='utf-8'))
        self.assertEqual({x['profile'] for x in index['candidate_profiles']}, {'p291', 'p271'})
        self.assertTrue(all(x['installation_approved'] is False for x in index['candidate_profiles']))
        self.assertTrue(all(x['identity_scope'] == 'app_installation' for x in index['devices']))
        for p in (one, two):
            saved = output / 'privado/zips' / p.name
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), hashes[p.name])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), hashes[p.name])
        self.assertEqual(set(p.name for p in output.iterdir()), {'privado'})
        self.assertFalse((output / 'privado/drivers').exists())
        self.assertTrue(all(x['archive']['readback_verified'] for x in index['captures']))

    def test_same_identity_different_profile_is_review_not_new_device(self):
        self.archive()
        self.archive(data=report(capture_id=CAPTURE_B, suggested_profile='p271'))
        output = self.folder / 'conflict'
        APP.import_batch(self.source, output, emit=None)
        index = json.loads((output / 'privado/catalogo.json').read_text(encoding='utf-8'))
        self.assertEqual(index['app_installation_identity_count'], 1)
        self.assertTrue(index['devices'][0]['profile_conflict_requires_review'])

    def test_existing_output_is_preserved(self):
        self.archive()
        output = self.folder / 'existing'
        output.mkdir()
        marker = output / 'existing.txt'
        marker.write_bytes(b'keep')
        with self.assertRaises(APP.InvalidCapture):
            APP.import_batch(self.source, output, emit=None)
        self.assertEqual(marker.read_bytes(), b'keep')
        self.assertEqual(list(output.iterdir()), [marker])

    def test_copy_failure_keeps_new_directory_and_source(self):
        path = self.archive()
        before = path.read_bytes()
        output = self.folder / 'failure'
        with mock.patch.object(APP, 'copy_verified', side_effect=OSError('fixture failure')):
            with self.assertRaises(OSError):
                APP.import_batch(self.source, output, emit=None)
        failure = json.loads((output / 'privado/IMPORTACION-INCOMPLETA.json').read_text())
        self.assertEqual(failure['state'], 'incomplete')
        self.assertEqual(path.read_bytes(), before)

    def test_local_copy_corruption_rejected_by_readback(self):
        path = self.archive()
        before = path.read_bytes()
        output = self.folder / 'readback-failure'
        actual_fsync = os.fsync
        calls = 0

        def corrupt_first_copy(fd):
            nonlocal calls
            actual_fsync(fd)
            calls += 1
            if calls == 1:
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, b'X')
                actual_fsync(fd)

        with mock.patch.object(APP.os, 'fsync', side_effect=corrupt_first_copy):
            with self.assertRaisesRegex(APP.InvalidCapture, 'relectura'):
                APP.import_batch(self.source, output, emit=None)
        self.assertTrue((output / 'privado/zips' / (path.name + '.parcial')).exists())
        self.assertFalse((output / 'privado/zips' / path.name).exists())
        self.assertTrue((output / 'privado/IMPORTACION-INCOMPLETA.json').exists())
        self.assertEqual(path.read_bytes(), before)

    def test_manifest_exact_listing_and_strict_sizes(self):
        changes = [lambda m: m['files'].pop(),
                   lambda m: m['files'].append(copy.deepcopy(m['files'][0])),
                   lambda m: m['files'][0].update(path='manifest.json'),
                   lambda m: m['files'][0].update(path='details/absent.txt'),
                   lambda m: m['files'][0].update(bytes=True),
                   lambda m: m['files'][0].update(bytes=-1),
                   lambda m: m['files'][0].update(bytes=2 ** 100),
                   lambda m: m['files'][0].update(bytes=3.14),
                   lambda m: m['files'][0].update(sha256=''),
                   lambda m: m['files'][0].update(sha256='0' * 64),
                   lambda m: m.update(capture_id=CAPTURE_B),
                   lambda m: m.update(schema='unknown')]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                self.reject(self.archive(edit_manifest=change))

    def test_json_malformed_duplicates_nonfinite_and_surrogates(self):
        for value in (b'\xff', b'{', b'{"schema":"a","schema":"b"}', b'[]',
                      b'{"x":NaN}', b'{"x":1e999}', b'{"x":"\\ud800"}'):
            with self.subTest(value=value):
                self.reject(self.archive(raw_report=value))

    def test_report_required_metadata_and_filename(self):
        for changes in ({'schema': 'unknown'}, {'android': []}, {'hardware': None},
                        {'webview': False}, {'export_limits': []}, {'display_name': ''},
                        {'profile_confidence': 'approved'}, {'device_id': DEVICE_A.upper()}):
            with self.subTest(changes=changes):
                data = report(**changes)
                # DEVICE_A solo contiene números; usar un UUID con letras para
                # que la variante de mayúsculas realmente sea no canónica.
                if 'device_id' in changes:
                    data['device_id'] = CAPTURE_A.upper()
                self.reject(self.archive(data=data))
        path = self.archive()
        renamed = path.with_name('unrelated.zip')
        path.rename(renamed)
        self.reject(renamed)

    def test_windows_names_and_path_traversal(self):
        invalid = ('/informe.json', '../informe.json', 'details/../a', 'details/./a', 'details//a',
                   'details\\a', 'C:/drivers/a', 'drivers/a:stream', 'details/a.', 'details/a ',
                   'details/CON', 'details/NUL.txt', 'details/COM1.ko', 'details/LPT².txt',
                   'details/a\x00b', 'details/a?b', 'details/', 'other/file', 'DETAILS/a')
        for name in invalid:
            with self.subTest(name=name):
                with self.assertRaises(APP.InvalidCapture):
                    APP.canonical_member(name)

    def test_duplicate_case_unicode_and_file_parent_conflicts(self):
        for extra in ([('details/estado.txt', b'other')],
                      [('details/ESTADO.txt', b'other')],
                      [('details/caf\u00e9', b'a'), ('details/cafe\u0301', b'b')],
                      [('details/tree', b'a'), ('details/tree/leaf', b'b')]):
            with self.subTest(extra=extra):
                self.reject(self.archive(extra=extra))

    def test_symlink_special_node_and_explicit_directory_rejected(self):
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFDIR | 0o755, stat.S_IFIFO | 0o600):
            with self.subTest(mode=mode):
                self.reject(self.archive(mode=mode))
        self.reject(self.archive(extra=[('details/', b'')]))

    def test_source_hardlink_rejected(self):
        path = self.archive()
        other = self.folder / 'hardlink.zip'
        os.link(path, other)
        self.reject(path)

    def test_crc_tamper_is_rejected_without_extraction(self):
        path = self.archive()
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo('drivers/fixture.ko')
        raw = bytearray(path.read_bytes())
        local = struct.unpack_from('<4s5H3I2H', raw, info.header_offset)
        at = info.header_offset + 30 + local[-2] + local[-1]
        raw[at] ^= 1
        path.write_bytes(raw)
        self.reject(path)

    def test_central_overflow_and_trailing_data(self):
        for field in ('entries', 'size', 'offset', 'member_size', 'trailing'):
            with self.subTest(field=field):
                path = self.archive()
                raw = bytearray(path.read_bytes())
                end = raw.rfind(b'PK\x05\x06')
                if field == 'entries':
                    struct.pack_into('<HH', raw, end + 8, APP.MAX_ENTRIES + 1, APP.MAX_ENTRIES + 1)
                elif field == 'size':
                    struct.pack_into('<I', raw, end + 12, 0xffffffff)
                elif field == 'offset':
                    struct.pack_into('<I', raw, end + 16, 0xffffffff)
                elif field == 'member_size':
                    central = raw.find(b'PK\x01\x02')
                    struct.pack_into('<I', raw, central + 24, 0xffffffff)
                else:
                    raw.extend(b'outside')
                path.write_bytes(raw)
                self.reject(path)

    def test_uncompressed_budget_enforced_before_read(self):
        path = self.archive()
        with mock.patch.object(APP, 'MAX_TOTAL', 1):
            self.reject(path)
        with mock.patch.object(APP, 'MAX_JSON', 1):
            self.reject(path)

    def test_duplicate_capture_id_across_installations_rejected(self):
        self.archive()
        self.archive(data=report(device_id=DEVICE_B))
        with self.assertRaises(APP.InvalidCapture):
            APP.verify_batch(self.source, emit=None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
