"""Inventario y descarga selectiva de Drive. No contiene operaciones de subida/borrado."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import configparser
import hashlib
import json
import os
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'privado' / 'drive-compartido'
CFG = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.config'))) / 'TVBaseDrive' / 'rclone.conf'
EXE = ROOT / 'tools' / 'rclone-1.75.1' / ('rclone.exe' if os.name == 'nt' else 'rclone')
FLAGS = 0x08000000 if os.name == 'nt' else 0


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def load(path):
    return json.loads(path.read_text(encoding='utf8'))


def safe_path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Ruta vacia o no portable')
    parts = value.split('/')
    if any(p in ('', '.', '..') or p[-1:] in (' ', '.') or
           re.search(r'[\x00-\x1f<>:"|?*]', p) or
           re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?', p)
           for p in parts):
        raise ValueError('Ruta no portable o insegura')
    return PurePosixPath(value)


def connection():
    # Nunca imprimir ni copiar el token; tampoco heredar overrides del backend.
    c = configparser.ConfigParser(interpolation=None)
    c.read(CFG, encoding='utf8')
    if 'tvbase' not in c or c['tvbase'].get('type') != 'drive':
        raise ValueError('Conectar primero la cuenta propia de Google')
    cfg = c['tvbase']
    if cfg.get('scope') != 'drive.readonly' or not cfg.get('token'):
        raise ValueError('Se exige conexion de solo lectura')
    folder = cfg.get('root_folder_id', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{10,}', folder):
        raise ValueError('Falta ID de carpeta compartida')
    if cfg.get('team_drive'):
        raise ValueError('Esta receta requiere carpeta compartida, no Shared Drive')
    return folder


def run(*args, output=None):
    if args[0] not in ('lsjson', 'copyto'):
        raise ValueError('Operacion no permitida')
    if len(args) < 2 or not args[1].startswith('tvbase:'):
        raise ValueError('Solo se admite Drive como origen')
    if args[0] == 'copyto':
        destination = Path(args[2]).resolve()
        if not destination.is_relative_to((STATE / 'objetos').resolve()):
            raise ValueError('Solo se descarga al almacen local de objetos')
    connection()
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('RCLONE_')}
    proc = subprocess.run([str(EXE), *args, '--config', str(CFG),
                           '--drive-skip-shortcuts', '--drive-skip-gdocs',
                           '--retries', '1', '--low-level-retries', '3'],
                          stdout=output or subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, creationflags=FLAGS, timeout=3600)
    if proc.returncode:
        # Salida detallada privada; no enviar nombres/IDs ni logs a GitHub.
        save(STATE / 'errores' / (uuid.uuid4().hex + '.json'),
             {'utc': utc(), 'exit_code': proc.returncode,
              'stderr': proc.stderr.decode('utf8', 'replace')})
        raise RuntimeError('Drive fallo; revisar registro privado, sin reintento automatico')
    return proc.stdout


def validate_items(items):
    names, ids, out = set(), set(), []
    for item in items:
        safe_path(item['Path'])
        folded = item['Path'].casefold()
        if folded in names or item.get('ID') in ids or not item.get('ID'):
            raise ValueError('Nombre ambiguo o ID duplicado en Drive')
        names.add(folded)
        ids.add(item['ID'])
        if item.get('IsDir'):
            continue
        sha = item.get('Hashes', {}).get('sha256', '')
        if item.get('Size', -1) < 0 or not re.fullmatch('[a-fA-F0-9]{64}', sha):
            raise ValueError('Archivo sin tamano/SHA256: no autorizar transferencias')
        out.append({'path': item['Path'], 'id': item['ID'], 'bytes': item['Size'],
                    'sha256': sha.lower(), 'modified': item.get('ModTime')})
    return out


def inventory():
    folder = connection()
    name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    raw = STATE / 'inventarios' / (name + '-proveedor.json')
    raw.parent.mkdir(parents=True, exist_ok=True)
    with raw.open('xb') as f:
        run('lsjson', 'tvbase:', '--recursive', '--hash-type', 'sha256', '--fast-list', output=f)
        f.flush()
        os.fsync(f.fileno())
    files = validate_items(load(raw))
    result = {'schema': 1, 'utc': utc(), 'root_id': folder,
              'scope': 'native files; shortcuts and Google editor files excluded',
              'files': files, 'bytes': sum(f['bytes'] for f in files)}
    target = raw.with_name(name + '.json')
    save(target, result)
    baseline = STATE / 'BASELINE.json'
    if not baseline.exists():
        save(baseline, result)
    else:
        if load(baseline)['root_id'] != folder:
            raise ValueError('La cuenta apunta a otra carpeta; baseline conservada')
    return {'manifest': str(target), 'files': len(files), 'bytes': result['bytes']}


def compare(manifest):
    remote = load(manifest)
    if remote['root_id'] != connection():
        raise ValueError('Inventario de otra carpeta')
    results = []
    for f in remote['files']:
        parts = safe_path(f['path']).parts
        local = ROOT / 'privado'
        linked = local.is_symlink() or (hasattr(local, 'is_junction') and local.is_junction())
        for part in parts:
            local = local / part
            linked |= local.is_symlink() or (hasattr(local, 'is_junction') and local.is_junction())
        if linked:
            state = 'link_rejected'
        elif not local.is_file():
            state = 'remote_only'
        elif local.stat().st_size != f['bytes']:
            state = 'size_differs'
        else:
            before = local.stat()
            with local.open('rb') as stream:
                sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = local.stat()
            state = 'equal_sha256' if sha == f['sha256'] else 'hash_differs'
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                state = 'local_changed_during_read'
        results.append({'path': f['path'], 'state': state})
    counts = {s: sum(x['state'] == s for x in results) for s in sorted({x['state'] for x in results})}
    out = STATE / 'comparaciones' / (uuid.uuid4().hex + '.json')
    save(out, {'utc': utc(), 'manifest': str(manifest), 'counts': counts, 'files': results})
    return {'report': str(out), 'counts': counts}


def selected_download(entry):
    folder = connection()
    if load(STATE / 'BASELINE.json')['root_id'] != folder:
        raise ValueError('La conexion no coincide con el alcance congelado')
    safe_path(entry['path'])
    source = 'tvbase:' + entry['path']
    current = json.loads(run('lsjson', source, '--stat', '--hash-type', 'sha256'))
    current['Path'] = entry['path']
    files = validate_items([current])
    if len(files) != 1 or files[0]['id'] != entry['id']:
        raise ValueError('ID cambiado: conservar y revisar; no incorporar otra identidad')
    f = files[0]
    # Objetos locales inmutables; nunca sobrescribir originales bajo privado/.
    object_id = hashlib.sha256((entry['id'] + ':' + f['sha256']).encode()).hexdigest()
    target = STATE / 'objetos' / object_id / safe_path(entry['path']).name
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.partial')
    if not target.exists():
        if partial.exists():
            raise ValueError('Descarga parcial previa: conservar y revisar antes de repetir')
        run('copyto', source, str(partial), '--immutable', '--no-update-modtime')
        with partial.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        if sha != f['sha256'] or partial.stat().st_size != f['bytes']:
            raise ValueError('Descarga no coincide; parcial conservado')
        end = json.loads(run('lsjson', source, '--stat', '--hash-type', 'sha256'))
        if end.get('ID') != f['id'] or end.get('Hashes', {}).get('sha256', '').lower() != sha:
            raise ValueError('Origen cambio durante descarga; parcial conservado')
        partial.rename(target)
    else:
        with target.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != f['sha256']:
                raise ValueError('Objeto local alterado; no reemplazar')
    return {'path': entry['path'], 'object': str(target), 'sha256': f['sha256'],
            'changed_since_baseline': f['sha256'] != entry['sha256']}


def select(path):
    safe_path(path)
    baseline = load(STATE / 'BASELINE.json')
    entries = [x for x in baseline['files'] if x['path'] == path]
    if len(entries) != 1:
        raise ValueError('Ruta fuera de la lista inicial; ampliar alcance requiere revision')
    result = selected_download(entries[0])
    key = hashlib.sha256(path.encode()).hexdigest()
    dest = STATE / 'seleccion' / (key + '.json')
    if not dest.exists():
        save(dest, entries[0])
    return result


def refresh():
    results, errors = [], []
    baseline = load(STATE / 'BASELINE.json')
    allowed = {x['path']: x for x in baseline['files']}
    for path in sorted((STATE / 'seleccion').glob('*.json')):
        entry = load(path)
        if allowed.get(entry['path']) != entry:
            raise ValueError('Seleccion modificada o fuera del alcance')
        try:
            results.append(selected_download(entry))
        except Exception as e:
            errors.append({'path': entry['path'], 'error': str(e)})
    receipt = {'utc': utc(), 'files': results, 'errors': errors, 'upload_count': 0,
               'delete_count': 0, 'scope': 'selected existing IDs only; local original files untouched'}
    save(STATE / 'refrescos' / (uuid.uuid4().hex + '.json'), receipt)
    return receipt


def main():
    global EXE
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rclone', type=Path, default=EXE)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('inventory')
    sub.add_parser('compare').add_argument('--manifest', type=Path, required=True)
    sub.add_parser('select').add_argument('--path', required=True)
    sub.add_parser('refresh')
    a = p.parse_args()
    EXE = a.rclone.resolve()
    for path in (ROOT / 'privado', STATE):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('No usar enlaces para el estado privado')
    STATE.mkdir(parents=True, exist_ok=True)
    lock = STATE / 'operacion.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit('Otra operacion o cierre incompleto; revisar lock antes de continuar')
    try:
        os.write(fd, str(os.getpid()).encode())
        result = {'inventory': inventory, 'compare': lambda: compare(a.manifest),
                  'select': lambda: select(a.path), 'refresh': refresh}[a.command]()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if isinstance(result, dict) and result.get('errors') else 0
    finally:
        os.close(fd)
        lock.unlink()


if __name__ == '__main__':
    raise SystemExit(main())
