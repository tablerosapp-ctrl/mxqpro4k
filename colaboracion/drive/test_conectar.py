"""La migración no amplía permisos ni expone el secreto en argumentos."""
from pathlib import Path
import configparser
import contextlib
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class ConnectionMigration(unittest.TestCase):
    def test_migration_preserves_prior_config_and_timeout_is_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            client = base / 'client.json'
            client.write_text(json.dumps({'installed': {
                'client_id': 'fixture.apps.googleusercontent.com', 'client_secret': 'private-fixture',
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token'}}), encoding='utf8')
            directory = base / 'TVBaseDrive'
            directory.mkdir()
            config = directory / 'rclone.conf'
            previous = b'[tvbase]\ntype=drive\nscope=drive.readonly\nroot_folder_id=example_folder_id\ntoken=old-fixture\n'
            config.write_bytes(previous)
            argv = ['conectar.py', '--folder-id', 'example_folder_id', '--rclone', str(base / 'rclone'),
                    '--client-json', str(client), '--replace-shared-client']
            def timeout(args, **kwargs):
                self.assertNotIn('private-fixture', ' '.join(args))
                self.assertNotIn('RCLONE_DRIVE_SCOPE', kwargs['env'])
                raise subprocess.TimeoutExpired(args, 900)
            output = io.StringIO()
            with patch.dict(os.environ, {'LOCALAPPDATA': temp, 'RCLONE_DRIVE_SCOPE': 'drive'}), \
                    patch.object(sys, 'argv', argv), patch('subprocess.run', side_effect=timeout), \
                    contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as caught:
                runpy.run_path(str(Path(__file__).with_name('conectar.py')), run_name='__main__')
            self.assertEqual(caught.exception.code, 124)
            self.assertNotIn('private-fixture', output.getvalue())
            self.assertEqual(next(directory.glob('config-anterior-*')).read_bytes(), previous)
            c = configparser.ConfigParser(interpolation=None)
            c.read(config)
            self.assertEqual(c['tvbase']['scope'], 'drive.readonly')
            self.assertNotIn('token', c['tvbase'])
            after = config.read_bytes()
            with patch.dict(os.environ, {'LOCALAPPDATA': temp}), patch.object(sys, 'argv', argv), \
                    patch('subprocess.run') as run, self.assertRaises(SystemExit):
                runpy.run_path(str(Path(__file__).with_name('conectar.py')), run_name='__main__')
            run.assert_not_called()
            self.assertEqual(config.read_bytes(), after)


if __name__ == '__main__':
    unittest.main()
