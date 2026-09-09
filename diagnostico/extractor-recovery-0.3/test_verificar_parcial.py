"""Failed capture fixtures: ordinary small files inside the workspace only."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


F = module('complete_fixture', 'test_verificar_captura.py')
P = module('partial_verifier', 'verificar-parcial.py')


class PartialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fixture-partial-', dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'capture'
        self.inv, self.report, self.result = F.fixture(self.root)
        for name in ('report.json', 'resultado.json'):
            (self.root / name).unlink()
        self.report.update(status='failed', error='source changed during reread')
        self.report['sources'][1].update(status='failed', reread_sha256='f' * 64,
                                         error=self.report['error'])
        for part in self.report['sources'][1]['parts']:
            part['status'] = 'destination_verified'
        self.save()

    def save(self):
        F.write_json(self.root / 'failed-report.json', self.report)
        F.write_json(self.root / 'resultado-error.json', {
            'schema': 'tvbase-recovery-result-1', 'status': 'failed',
            'capture_id': F.CAPTURE_ID, 'error': self.report['error']})

    def reject(self, code):
        with self.assertRaisesRegex(P.V.InvalidCapture, code):
            P.verify_failed(self.root)

    def test_counts_only_sources_with_both_origin_hashes(self):
        answer = P.verify_failed(self.root)
        self.assertEqual(answer['verified_source_bytes'], self.report['sources'][0]['source']['bytes'])
        self.assertFalse(answer['capture_complete'])
        self.assertFalse(answer['all_device_storage_copied'])
        self.assertEqual(answer['sources'][1]['verified_source_bytes'], 0)
        with self.assertRaisesRegex(P.V.InvalidCapture, 'capture_marked_failed'):
            P.V.verify_capture(self.root)

    def test_rejects_corrupted_verified_and_failed_parts(self):
        for source in self.report['sources']:
            path = self.root / source['parts'][0]['name']
            original = path.read_bytes()
            path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            self.reject('part_sha256_mismatch')
            path.write_bytes(original)

    def test_does_not_promote_mismatch_to_verified(self):
        self.report['sources'][1]['status'] = 'verified'
        self.save()
        self.reject('claimed_verified_source_invalid')

    def test_part_errors_and_unknown_states_rejected(self):
        part = self.report['sources'][0]['parts'][0]
        for change, error in [({'error': 'read failed'}, 'claimed_verified_source_invalid'),
                              ({'error': 7}, 'invalid_text'),
                              ({'status': 'invented'}, 'unknown_partial_part_state')]:
            original = copy.deepcopy(part)
            part.update(change)
            self.save()
            self.reject(error)
            part.clear(); part.update(original)

    def test_conflicting_markers_unexpected_files_and_path_rejected(self):
        for name, code in [('resultado.json', 'conflicting_success_records'),
                           ('unexpected.txt', 'unexpected_or_missing_files')]:
            path = self.root / name
            path.write_bytes(b'fixture')
            self.reject(code)
            path.unlink()
        self.report['sources'][0]['parts'][0]['name'] = '../outside.img.partial'
        self.save()
        self.reject('unsafe_basename')

    def test_failed_without_parts_preserves_preceding_verified_source(self):
        row = self.report['sources'][1]
        for part in row.pop('parts'):
            (self.root / part['name']).unlink()
        self.save()
        result = P.verify_failed(self.root)
        self.assertEqual(result['sources'][1]['copied_bytes_checked'], 0)
        self.assertGreater(result['verified_source_bytes'], 0)

    def test_preflight_failure_with_only_omitted_sources_is_not_complete(self):
        for row in self.report['sources']:
            for part in row.pop('parts'):
                (self.root / part['name']).unlink()
            row.pop('sha256'); row.pop('reread_sha256')
            row.update(status='omitted', error='not attempted')
        self.save()
        answer = P.verify_failed(self.root)
        self.assertEqual(answer['verified_source_bytes'], 0)
        self.assertFalse(answer['capture_complete'])

    def test_deferred_order_absent_only_before_attempt(self):
        inv = {'source_policy': {}}
        source = {'name': 'mmcblk0p10', 'major_minor': '179:10', 'kind': 'partition'}
        for state in ('omitted', 'failed'):
            P.V.validate_policy_source(inv, source, {'status': state}, 13, 14)
        for state in ('verified', 'failed'):
            with self.assertRaisesRegex(P.V.InvalidCapture, 'backup_verification_order_mismatch'):
                P.V.validate_policy_source(inv, source, {'status': state, 'sha256': 'a' * 64}, 13, 14)
        P.V.validate_policy_source(inv, source, {'status': 'failed', 'verification_order': 'source_source_destination'}, 13, 14)


if __name__ == '__main__':
    unittest.main()
