"""Conecta una cuenta propia a una carpeta compartida, solo lectura, sin subir archivos."""
from pathlib import Path
import argparse
import os
import re
import subprocess
import uuid
import json

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--folder-id', required=True, help='ID privado de la carpeta compartida')
p.add_argument('--rclone', type=Path, required=True)
a = p.parse_args()
if not re.fullmatch('[A-Za-z0-9_-]{10,}', a.folder_id):
    raise SystemExit('ID de carpeta invalido')
directory = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.config'))) / 'TVBaseDrive'
directory.mkdir(parents=True, exist_ok=True)
config = directory / 'rclone.conf'
if config.exists():
    raise SystemExit('Configuracion existente: no se reemplaza. Verificar conexion primero.')
env = {k: v for k, v in os.environ.items() if not k.upper().startswith('RCLONE_')}
with (directory / ('conexion-' + uuid.uuid4().hex + '.log')).open('xb') as log:
    proc = subprocess.run([str(a.rclone.resolve()), 'config', 'create', 'tvbase', 'drive',
        'scope', 'drive.readonly', 'root_folder_id', a.folder_id, 'config_is_local', 'true',
        'config_change_team_drive', 'false', '--config', str(config)],
        stdout=log, stderr=log, env=env, timeout=900,
        creationflags=0x08000000 if os.name == 'nt' else 0)
print(json.dumps({'exit_code': proc.returncode, 'config_exists': config.exists(),
                  'scope': 'drive.readonly', 'uploads': 0}))
raise SystemExit(proc.returncode)
