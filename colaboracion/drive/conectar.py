"""Conecta una cuenta propia a una carpeta compartida, solo lectura, sin subir archivos."""
from pathlib import Path
import argparse
import os
import re
import subprocess
import uuid
import json
import configparser

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--folder-id', required=True, help='ID privado de la carpeta compartida')
p.add_argument('--rclone', type=Path, required=True)
p.add_argument('--client-json', type=Path, required=True)
p.add_argument('--replace-shared-client', action='store_true')
p.add_argument('--reconnect', action='store_true')
a = p.parse_args()
if not re.fullmatch('[A-Za-z0-9_-]{10,}', a.folder_id):
    raise SystemExit('ID de carpeta invalido')
directory = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.config'))) / 'TVBaseDrive'
directory.mkdir(parents=True, exist_ok=True)
config = directory / 'rclone.conf'
client_path = a.client_json.resolve(strict=True)
if client_path.is_relative_to(Path(__file__).resolve().parents[2]):
    raise SystemExit('Guardar credenciales fuera del proyecto')
try:
    client = json.loads(client_path.read_text(encoding='utf8'))['installed']
    assert client['client_id'].endswith('.apps.googleusercontent.com') and client['client_secret']
    assert client['auth_uri'] == 'https://accounts.google.com/o/oauth2/auth'
    assert client['token_uri'] == 'https://oauth2.googleapis.com/token'
except (KeyError, ValueError, AssertionError):
    raise SystemExit('Se exige JSON de cliente de escritorio de Google') from None
if a.reconnect and a.replace_shared_client:
    raise SystemExit('Elegir reconexion o migracion')
c = configparser.ConfigParser(interpolation=None)
if config.exists():
    c.read(config, encoding='utf8')
    if c.sections() != ['tvbase']:
        raise SystemExit('Configuracion ajena: conservar y revisar')
    old = c['tvbase']
    if (old.get('type') != 'drive' or old.get('scope') != 'drive.readonly' or
            old.get('root_folder_id') != a.folder_id or old.get('team_drive')):
        raise SystemExit('Alcance anterior distinto: conservar y revisar')
    if a.reconnect:
        if old.get('client_id') != client['client_id'] or old.get('client_secret') != client['client_secret']:
            raise SystemExit('Cliente distinto: no reconectar')
    elif not a.replace_shared_client or old.get('client_id') or old.get('client_secret'):
        raise SystemExit('Configuracion existente: no reemplazar')
    if not a.reconnect:
        with (directory / ('config-anterior-' + uuid.uuid4().hex + '.conf')).open('xb') as f:
            f.write(config.read_bytes())
            f.flush()
            os.fsync(f.fileno())
elif a.reconnect or a.replace_shared_client:
    raise SystemExit('No existe configuracion para esa operacion')
if not a.reconnect:
    c = configparser.ConfigParser(interpolation=None)
    c['tvbase'] = {'type': 'drive', 'scope': 'drive.readonly', 'root_folder_id': a.folder_id,
                   'client_id': client['client_id'], 'client_secret': client['client_secret']}
    temporary = directory / ('config-nueva-' + uuid.uuid4().hex + '.conf')
    with temporary.open('x', encoding='utf8') as f:
        c.write(f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, config)

env = {k: v for k, v in os.environ.items() if not k.upper().startswith('RCLONE_')}
with (directory / ('conexion-' + uuid.uuid4().hex + '.log')).open('xb') as log:
    try:
        proc = subprocess.run([str(a.rclone.resolve()), 'config', 'reconnect', 'tvbase:',
            '--auto-confirm', '--config', str(config)], stdout=log, stderr=log,
            env=env, timeout=900, creationflags=0x08000000 if os.name == 'nt' else 0)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = 124
c.read(config, encoding='utf8')
print(json.dumps({'exit_code': code, 'token_present': bool(c['tvbase'].get('token')),
                  'own_client': True, 'scope': 'drive.readonly', 'uploads': 0}))
raise SystemExit(code)
