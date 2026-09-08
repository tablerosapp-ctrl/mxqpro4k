"""Importador 0.2: regresiones heredadas, fichas ligadas y ZIP P271 real.

El ZIP real y su catálogo original se leen solamente. Los casos sintéticos se
crean bajo un temporal privado del proyecto cuya ruta se comprueba antes de
limpiarlo. No se accede a TV, pendrive, red ni fuentes de la APK.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


APP = module_from_path('recognition_import_02', HERE.parent / 'importar-informes.py')
LEGACY = module_from_path('recognition_legacy_fixtures', ROOT / 'diagnostico/reconocedor-0.1/test_importar_informes.py')
# The original tests and fixture helpers now exercise the new importer. Their
# source files remain unchanged; no tests are copied out of the 0.1 release.
LEGACY.APP = APP
REAL_DIRECTORY = ROOT / 'diagnostico/reconocimiento-20260908-p271-mx9/privado'
REAL_ZIP = REAL_DIRECTORY / 'zips/TVBASE-p271-5cdc0e26-4da32653.zip'
REAL_CATALOG = REAL_DIRECTORY / 'catalogo.json'
REAL_SHA = '3824c4355ec7f75d25dd09a5ca406c90cc017ceab3d45b14732c94f62a7e073f'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def capture_report(**changes):
    value = LEGACY.report()
    value.pop('capture_status')
    value.update(changes)
    return value


def catalog_entry(item):
    result = APP.catalog([item], [{'path': 'zips/' + item['source'].name,
                                  'bytes': item['bytes'], 'sha256': item['sha256']}])
    return result['captures'][0]


class NewImporterTests(LEGACY.ImportTests):
    """Includes all 19 original integrity/overwrite/path regressions."""

    @unittest.skipUnless(REAL_ZIP.is_file() and REAL_CATALOG.is_file(), 'Captura P271 privada no disponible en este entorno')
    def test_real_p271_capture_state_is_not_unspecified(self):
        original_catalog_sha = sha(REAL_CATALOG)
        original_zip_sha = sha(REAL_ZIP)
        original_zip_info = APP.info_key(REAL_ZIP.stat())
        checked = APP.verify_archive(REAL_ZIP, emit=None)
        entry = catalog_entry(checked)
        self.assertEqual(checked['sha256'], REAL_SHA)
        self.assertEqual(checked['bytes'], 69460957)
        self.assertEqual(checked['member_count'], 2464)
        self.assertEqual(checked['report']['dt_identity'], 'gxlx_p271_1g')
        self.assertEqual(entry['reported_capture_status'], 'inventory_with_explicit_limits')
        self.assertEqual(entry['reported_capture_status_source'], 'capture_state')
        self.assertEqual(entry['integrity'], 'verified')
        self.assertFalse(entry['profile_installation_approved'])
        self.assertIsNone(entry['parent_capture_id'])
        self.assertEqual(sha(REAL_ZIP), original_zip_sha)
        self.assertEqual(APP.info_key(REAL_ZIP.stat()), original_zip_info)
        self.assertEqual(sha(REAL_CATALOG), original_catalog_sha)
        original = json.loads(REAL_CATALOG.read_text(encoding='utf-8'))
        self.assertEqual(original['captures'][0]['reported_capture_status'], 'unspecified')

    def test_basic_checkpoint_and_secondary_keep_same_schema_and_separate_ids(self):
        initial = capture_report(capture_state='basic_checkpoint')
        secondary = capture_report(capture_id=LEGACY.CAPTURE_B,
                                   capture_state='inventory_with_explicit_limits',
                                   parent_capture_id=LEGACY.CAPTURE_A)
        one, two = self.archive(data=initial), self.archive(data=secondary)
        original = {p.name: sha(p) for p in (one, two)}
        destination = self.folder / 'linked-import'
        APP.import_batch(self.source, destination, emit=None)
        index = json.loads((destination / 'privado/catalogo.json').read_text(encoding='utf-8'))
        self.assertEqual(index['schema'], 'tvbase-recognition-import-1')
        self.assertEqual(index['importer_version'], '0.2')
        self.assertEqual(index['capture_count'], 2)
        self.assertEqual(index['app_installation_identity_count'], 1)
        captures = {row['capture_id']: row for row in index['captures']}
        self.assertEqual(captures[LEGACY.CAPTURE_A]['reported_capture_status'], 'basic_checkpoint')
        self.assertIsNone(captures[LEGACY.CAPTURE_A]['parent_capture_id'])
        self.assertEqual(captures[LEGACY.CAPTURE_B]['parent_capture_id'], LEGACY.CAPTURE_A)
        self.assertEqual(captures[LEGACY.CAPTURE_B]['reported_capture_status'], 'inventory_with_explicit_limits')
        self.assertTrue(all(row['integrity'] == 'verified' for row in captures.values()))
        self.assertFalse(index['devices'][0]['physical_identity_proven'])
        self.assertEqual({p.name: sha(p) for p in (one, two)}, original)

    def test_partial_failed_and_checkpoint_states_are_not_promoted_to_complete(self):
        for state in ('partial', 'failed', 'basic_checkpoint', 'inventory_with_explicit_limits'):
            with self.subTest(state=state):
                path = self.archive(data=capture_report(capture_state=state))
                entry = catalog_entry(APP.verify_archive(path, emit=None))
                self.assertEqual(entry['reported_capture_status'], state)
                self.assertEqual(entry['reported_capture_status_source'], 'capture_state')
                self.assertEqual(entry['integrity'], 'verified')
                self.assertFalse(entry['profile_installation_approved'])

    def test_legacy_capture_status_and_status_are_preserved_with_provenance(self):
        for field, state in (('capture_status', 'partial'), ('status', 'failed')):
            with self.subTest(field=field):
                path = self.archive(data=capture_report(**{field: state}))
                entry = catalog_entry(APP.verify_archive(path, emit=None))
                self.assertEqual(entry['reported_capture_status'], state)
                self.assertEqual(entry['reported_capture_status_source'], field)

    def test_canonical_state_takes_precedence_without_mutating_report(self):
        data = capture_report(capture_state='partial', capture_status='complete', status='failed')
        path = self.archive(data=data)
        checked = APP.verify_archive(path, emit=None)
        before = copy.deepcopy(checked['report'])
        entry = catalog_entry(checked)
        self.assertEqual(entry['reported_capture_status'], 'partial')
        self.assertEqual(entry['reported_capture_status_source'], 'capture_state')
        self.assertEqual(checked['report'], before)
        self.assertEqual(checked['report']['capture_status'], 'complete')

    def test_missing_state_stays_unspecified(self):
        checked = APP.verify_archive(self.archive(data=capture_report()), emit=None)
        entry = catalog_entry(checked)
        self.assertEqual(entry['reported_capture_status'], 'unspecified')
        self.assertIsNone(entry['reported_capture_status_source'])

    def test_unknown_textual_state_is_kept_as_reported(self):
        state = 'future_partial_observation'
        checked = APP.verify_archive(self.archive(data=capture_report(capture_state=state)), emit=None)
        self.assertEqual(catalog_entry(checked)['reported_capture_status'], state)

    def test_malformed_present_state_rejected_without_silent_legacy_fallback(self):
        for state in (None, True, 7, [], {}, '', 'x' * 129, 'partial\ncomplete', 'partial\x00'):
            with self.subTest(state=state):
                path = self.archive(data=capture_report(capture_state=state, capture_status='partial'))
                self.reject(path)

    def test_malformed_legacy_state_is_still_rejected_when_canonical_exists(self):
        path = self.archive(data=capture_report(capture_state='basic_checkpoint', capture_status=[]))
        self.reject(path)

    def test_secondary_reference_can_arrive_without_its_parent_in_this_batch(self):
        data = capture_report(capture_state='partial', capture_id=LEGACY.CAPTURE_B,
                              parent_capture_id=LEGACY.CAPTURE_A)
        self.archive(data=data)
        _, items, _ = APP.verify_batch(self.source, emit=None)
        self.assertEqual(len(items), 1)
        entry = catalog_entry(items[0])
        self.assertEqual(entry['parent_capture_id'], LEGACY.CAPTURE_A)
        self.assertEqual(entry['capture_id'], LEGACY.CAPTURE_B)
        self.assertFalse(entry['profile_installation_approved'])

    def test_invalid_and_self_parent_references_rejected(self):
        for parent in (None, False, 5, '', 'not-a-uuid', '00000000-0000-0000-0000-000000000000',
                       LEGACY.CAPTURE_A, LEGACY.CAPTURE_B.upper()):
            with self.subTest(parent=parent):
                path = self.archive(data=capture_report(capture_state='partial', parent_capture_id=parent))
                self.reject(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
