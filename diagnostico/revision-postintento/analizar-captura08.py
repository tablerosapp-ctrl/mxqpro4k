"""Lectura offline: distingue integridad del transporte, cierre y éxito de dumpsys.

No modifica la carpeta de entrada ni exporta líneas crudas, MAC o boot_id.
Un código 0 no convierte un DUMP TIMEOUT en respuesta satisfactoria.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

QUERY_NAMES = ('log-anterior', 'log-actual', 'wifi', 'bluetooth', 'bateria', 'espacio', 'webview')


def classify_output(raw, return_code):
    text = raw.decode('utf8', 'replace')
    timeout = bool(re.search(r"\*\*\* SERVICE '[^']+' DUMP TIMEOUT \(\d+(?:ms|s)\) EXPIRED", text))
    if timeout:
        state = 'service_timeout'
    elif 'Permission denied' in text or 'Permission Denial' in text:
        state = 'permission_denied'
    elif return_code != 0:
        state = 'command_failed'
    elif not raw:
        state = 'empty_output'
    else:
        state = 'output_received'
    return {'state': state, 'exit': return_code, 'bytes': len(raw), 'contains_nul': b'\0' in raw}


def analyze(folder):
    folder = Path(folder)
    match = re.fullmatch(r'TVBASE-postintento-([0-9a-f]{32})', folder.name)
    if not match or folder.is_symlink() or not folder.is_dir():
        raise ValueError('Carpeta de captura inválida')
    paths = list(folder.iterdir())
    if len(paths) > 256 or any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError('Contenido de carpeta no admitido')
    if sum(p.stat().st_size for p in paths) > 32 * 1024 * 1024:
        raise ValueError('Captura demasiado grande')
    files = {p.name: p.read_bytes() for p in paths}
    def sealed(name):
        digest = files.get(name + '.sha256', b'').strip()
        return name in files and bool(re.fullmatch(b'[0-9a-f]{64}', digest)) and hashlib.sha256(files[name]).hexdigest().encode() == digest
    required = ['autocontrol.bin', 'identidad.txt', 'pstore.txt']
    required += [name+'.'+suffix for name in QUERY_NAMES for suffix in ('txt', 'rc', 'estado')]
    required += [name for name in files if re.fullmatch(r'(console|pmsg)-ramoops[^/]*\.bin', name)]
    integrity = {name: sealed(name) for name in required}
    token = match[1].encode()
    stages = {str(n): files.get(f'etapa-{n}.ok', b'').strip() == token for n in range(1, 11)}
    initial = files.get('INICIO.txt', b'').strip() == token and files.get('autocontrol.bin') == b'abc'
    closure = sealed('COMPLETO.txt') and files.get('COMPLETO.txt', b'').startswith(b'TVBASE POSTINTENTO 0.8: recorrido terminado')
    queries = {}
    for name in QUERY_NAMES:
        if not all(integrity[name+'.'+s] for s in ('txt', 'rc', 'estado')):
            queries[name] = {'state': 'unverified_files'}
            continue
        meta = dict(line.split('=', 1) for line in files[name+'.estado'].decode('ascii').splitlines() if '=' in line)
        rc = int(files[name+'.rc'].strip())
        data = files[name+'.txt']
        if int(meta['exit']) != rc or int(meta['bytes']) != len(data):
            queries[name] = {'state': 'inconsistent_metadata'}
            continue
        row = classify_output(data, rc)
        row.update(seconds=round(float(meta['fin_uptime'].split()[0])-float(meta['inicio_uptime'].split()[0]), 3), truncated=meta['truncado']=='si')
        queries[name] = row
    complete = initial and all(integrity.values()) and all(stages.values()) and closure and all(q['state'] not in ('unverified_files', 'inconsistent_metadata') for q in queries.values())
    log = files.get('log-actual.txt', b'').decode('utf8', 'replace') if sealed('log-actual.txt') else ''
    anrs = re.findall(r'^\s*(\d+\.\d+)\s+\d+\s+\d+\s+E ActivityManager: ANR in com\.android\.bluetooth\s*$', log, re.M)
    return {
        'scope': 'Offline; no autentica causa del bloqueo ni ejecución de recovery',
        'capture_state': 'complete' if complete else 'partial',
        'files_acquired': len(files), 'required_payload_seals': integrity,
        'valid_payload_seals': sum(integrity.values()), 'initial_valid': initial,
        'stages': stages, 'closure_valid': closure,
        'zero_byte_files': sorted(name for name, raw in files.items() if not raw),
        'queries': queries,
        'bluetooth_anr_count': len(anrs),
        'bluetooth_anr_uptime_seconds': [float(t) for t in anrs],
        'bluetooth_anr_span_seconds': round(float(anrs[-1])-float(anrs[0]), 3) if len(anrs)>1 else None,
        'physical_cause_confirmed': False,
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    print(json.dumps(analyze(p.parse_args().folder), ensure_ascii=False, indent=2))
