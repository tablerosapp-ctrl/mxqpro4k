import importlib.util
import tempfile
import hashlib
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('capture', Path(__file__).with_name('analizar-captura08.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.token = 'a' * 32
        self.folder = Path(self.temp.name)/('TVBASE-postintento-'+self.token)
        self.folder.mkdir()
        (self.folder/'INICIO.txt').write_text(self.token+'\n')
        for n in range(1, 11):
            (self.folder/f'etapa-{n}.ok').write_text(self.token+'\n')
        for n, data in [('autocontrol.bin', b'abc'), ('identidad.txt', b'identity'), ('pstore.txt', b'none'), ('COMPLETO.txt', b'TVBASE POSTINTENTO 0.8: recorrido terminado')]:
            self.seal(n, data)
        for n in m.QUERY_NAMES:
            self.seal(n+'.txt', b'reply')
            self.seal(n+'.rc', b'0\n')
            self.seal(n+'.estado', b'inicio_uptime=1 2\nfin_uptime=2 3\nexit=0\nbytes=5\ntruncado=no\n')

    def tearDown(self):
        self.temp.cleanup()

    def seal(self, n, data):
        (self.folder/n).write_bytes(data)
        (self.folder/(n+'.sha256')).write_text(hashlib.sha256(data).hexdigest()+'\n')

    def test_complete_fixture(self):
        self.assertEqual(m.analyze(self.folder)['capture_state'], 'complete')

    def test_empty_final_three_files_is_partial(self):
        for n in ('COMPLETO.txt', 'COMPLETO.txt.sha256', 'etapa-10.ok'):
            (self.folder/n).write_bytes(b'')
        r = m.analyze(self.folder)
        self.assertEqual(r['capture_state'], 'partial')
        self.assertEqual(r['valid_payload_seals'], 24)

    def test_changed_payload_not_trusted(self):
        (self.folder/'wifi.txt').write_bytes(b'changed')
        r = m.analyze(self.folder)
        self.assertEqual(r['queries']['wifi']['state'], 'unverified_files')
        self.assertEqual(r['capture_state'], 'partial')

    def test_rc_zero_with_service_timeout(self):
        r = m.classify_output(b"\0*** SERVICE 'batterystats' DUMP TIMEOUT (5000ms) EXPIRED ***\n", 0)
        self.assertEqual(r['state'], 'service_timeout')

    def test_empty_and_failed_are_not_success(self):
        self.assertEqual(m.classify_output(b'', 0)['state'], 'empty_output')
        self.assertEqual(m.classify_output(b'logcat read failure', 1)['state'], 'command_failed')

    def test_permission_denied_with_rc_zero(self):
        self.assertEqual(m.classify_output(b'Permission denied', 0)['state'], 'permission_denied')

    def test_output_does_not_export_mac_or_identity(self):
        self.seal('identidad.txt', b'PRIVATE_IDENTITY')
        self.seal('bluetooth.txt', b'PRIVATE_MAC')
        result = str(m.analyze(self.folder))
        self.assertNotIn('PRIVATE_', result)

    def test_metadata_contradiction_recorded(self):
        self.seal('wifi.rc', b'137\n')
        self.assertEqual(m.analyze(self.folder)['queries']['wifi']['state'], 'inconsistent_metadata')


if __name__ == '__main__':
    unittest.main()
