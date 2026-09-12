"""Pruebas de barreras: rutas, alcance, identidad y descarga sin sobreescritura."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json
import hashlib

spec = importlib.util.spec_from_file_location('drive', Path(__file__).with_name('drive.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class Guards(unittest.TestCase):
    def test_connection_requires_own_readonly_client(self):
        with tempfile.TemporaryDirectory(dir=d.ROOT / 'privado') as temp:
            cfg = Path(temp) / 'test.conf'
            base = '[tvbase]\ntype = drive\nscope = drive.readonly\nroot_folder_id = example_folder_id\ntoken = fixture\n'
            with patch.object(d, 'CFG', cfg):
                cfg.write_text(base, encoding='utf8')
                with self.assertRaises(ValueError):
                    d.connection()
                own = base + 'client_id = fixture\nclient_secret = fixture\n'
                cfg.write_text(own, encoding='utf8')
                self.assertEqual(d.connection(), 'example_folder_id')
                cfg.write_text(own.replace('drive.readonly', 'drive'), encoding='utf8')
                with self.assertRaises(ValueError):
                    d.connection()

    def test_paths(self):
        for path in ('../secret', '/secret', 'a/../b', 'a\\b', 'C:/data',
                     'a//b', 'a\nfile', 'a/NUL.txt', 'a/end.', 'a/end ', ''):
            with self.subTest(path=path), self.assertRaises(ValueError):
                d.safe_path(path)
        self.assertEqual(str(d.safe_path('captura/área.img.partial')), 'captura/área.img.partial')

    def item(self, path='a.bin', id='file-id', data=b'original'):
        return {'Path': path, 'ID': id, 'Size': len(data), 'IsDir': False,
                'Hashes': {'sha256': hashlib.sha256(data).hexdigest()}}

    def test_duplicates_and_no_hash(self):
        for items in ([self.item(), self.item(id='other')],
                      [self.item(), self.item(path='A.bin', id='other')],
                      [self.item(), self.item(path='b.bin')],
                      [dict(self.item(), Hashes={})]):
            with self.subTest(items=items), self.assertRaises(ValueError):
                d.validate_items(items)

    def test_no_write_commands(self):
        for command in ('sync', 'bisync', 'delete', 'copy', 'move', 'purge'):
            with self.assertRaises(ValueError):
                d.run(command)
        with self.assertRaises(ValueError):
            d.run('copyto', '/local/secret', 'tvbase:secret')
        with self.assertRaises(ValueError):
            d.run('copyto', 'tvbase:report', 'another-drive:report')

    def test_separate_versions_and_id_change(self):
        with tempfile.TemporaryDirectory(dir=d.ROOT / 'privado') as temp:
            state = Path(temp)
            entry = d.validate_items([self.item()])[0]
            d.save(state / 'BASELINE.json', {'root_id': 'folder', 'files': [entry]})
            payload = b'original'
            id = 'file-id'
            def fake(*args, **kwargs):
                if args[0] == 'lsjson':
                    return json.dumps(self.item(id=id, data=payload)).encode()
                self.assertEqual(args[0], 'copyto')
                self.assertEqual(args[1], 'tvbase:a.bin')
                Path(args[2]).write_bytes(payload)
                return b''
            with patch.object(d, 'STATE', state), patch.object(d, 'connection', return_value='folder'), patch.object(d, 'run', side_effect=fake):
                first = d.select('a.bin')
                self.assertEqual(Path(first['object']).read_bytes(), b'original')
                with self.assertRaises(ValueError):
                    d.select('omitted.bin')
                payload = b'new revision'
                second = d.refresh()['files'][0]
                self.assertNotEqual(first['object'], second['object'])
                self.assertEqual(Path(first['object']).read_bytes(), b'original')
                self.assertEqual(Path(second['object']).read_bytes(), payload)
                id = 'different-file'
                self.assertEqual(len(d.refresh()['errors']), 1)

    def test_bad_download_preserved(self):
        with tempfile.TemporaryDirectory(dir=d.ROOT / 'privado') as temp:
            state = Path(temp)
            entry = d.validate_items([self.item()])[0]
            d.save(state / 'BASELINE.json', {'root_id': 'folder', 'files': [entry]})
            def fake(*args, **kwargs):
                if args[0] == 'lsjson':
                    return json.dumps(self.item()).encode()
                Path(args[2]).write_bytes(b'corrupt')
                return b''
            with patch.object(d, 'STATE', state), patch.object(d, 'connection', return_value='folder'), patch.object(d, 'run', side_effect=fake):
                with self.assertRaises(ValueError):
                    d.select('a.bin')
                self.assertEqual(len(list(state.rglob('*.partial'))), 1)
                self.assertFalse((state / 'seleccion').exists())


if __name__ == '__main__':
    unittest.main()
