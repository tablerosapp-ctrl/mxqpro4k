"""Revisión independiente, solo PC, del cierre físico 0.2.2 y su adquisición.

No conecta dispositivos, no ejecuta imágenes y nunca escribe en la adquisición.
El argumento debe estar dentro de privado/ de este proyecto. Solo emite el
resumen público si pasan todos los controles; un archivo de salida existente
no se sobrescribe. --self-test-only valida casos de metadatos sin leer .img.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'rom-simplificada/original-p291/instalacion-022/salida/TVBASE-P291-A9-0.2.2-VERIFICACION.json'
RELEASE_SHA = '55177ba801abab5c2c32391ac3ddc3139cd39bcff50b88e06e3ddcff9b39fbba'
PACKAGE = 'TVBASE-P291-A9-0.2.2'
NAMES = ['system', 'vendor', 'product', 'odm', 'boot']
PROFILE = {'system': (1342177280, 18), 'vendor': (943718400, 16),
           'product': (134217728, 19), 'odm': (134217728, 17),
           'boot': (16777216, 11), 'data': (3495952384, 20), 'env': (8388608, 4)}
TOTAL = 6067060736
FS_BYTES = 3495936000
DISK_BYTES = 7650410496
JSON_FILES = ['00-backup-verified.json', '10-format-started.json',
              '11-format-result.json', '20-userdata-prepared.json',
              '90-installed-verified.json']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Clave JSON duplicada: ' + key)
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Constante JSON inválida')))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_file(base, relative):
    normalized = relative.replace('\\', '/')
    parts = PurePosixPath(normalized)
    require(not parts.is_absolute() and all(p not in ('..', '.') and ':' not in p for p in parts.parts), 'Ruta no relativa')
    target = base.joinpath(*parts.parts)
    require(target.resolve().is_relative_to(base.resolve()), 'Ruta fuera de adquisición')
    for item in [target, *target.parents]:
        if item == base:
            break
        require(not item.is_symlink() and not item.is_junction(), 'Enlace no admitido')
    require(stat.S_ISREG(target.stat().st_mode), 'No es archivo regular')
    return target


def integer(value, expected, label):
    require(type(value) is int and value == expected, label)


def utc(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value), 'Hora no UTC RFC3339')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def metadata(documents, log, manifest):
    backup, started, formatted, prepared, finished = [documents[n] for n in JSON_FILES]
    require(backup['state'] == 'backup_verified' and backup['package_id'] == PACKAGE, 'Cierre de respaldo distinto')
    require(backup['dt_id'] == manifest['dt_id'] and backup['media_id'] == manifest['media_id'], 'Perfil/medio distinto')
    integer(backup['format'], 1, 'Formato de recibo distinto')
    integer(backup['data_bytes'], PROFILE['data'][0], 'Tamaño userdata distinto')
    require(backup['data_major_minor'] == '179:20', 'Dispositivo userdata distinto')
    require(backup['start_offsets_originally_captured'] is False, 'Origen de offsets incorrecto')
    records = backup['records']
    require([r['name'] for r in records] == NAMES + ['data'], 'Seis respaldos únicos y ordenados requeridos')
    images = {i['name']: i for i in manifest['images']}
    require(list(images) == NAMES, 'Orden de payloads distinto')
    for row in records:
        name = row['name']
        integer(row['bytes'], PROFILE[name][0], 'Tamaño respaldo incorrecto: ' + name)
        require(row['file'] == name + '.img' and row['state'] == 'verified', 'Archivo/estado de respaldo incorrecto')
        digest = row['sha256']
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'SHA respaldo inválido')
        require(row['usb_read_sha256'] == row['source_after_sha256'] == digest, 'Tres SHA de respaldo no coinciden')
        if name != 'data':
            require(digest == images[name]['original_sha256'], 'Respaldo difiere del original P291')
    require(sum(r['bytes'] for r in records) == TOTAL, 'Total respaldo incorrecto')
    layouts = backup['layouts_observed']
    require(set(layouts) == set(PROFILE), 'Faltan siete layouts observados')
    ranges, parent = [], None
    public_layouts = []
    for name, (size, minor) in PROFILE.items():
        row = layouts[name]
        require(row['Name'] == name and row['MajorMinor'] == f'179:{minor}', 'Identidad layout incorrecta')
        for key, expected in [('Bytes', size), ('Device', (179 << 8) + minor), ('Partition', minor),
                              ('ParentBytes', DISK_BYTES), ('ParentDevice', 179 << 8), ('Sectors', size // 512)]:
            integer(row[key], expected, 'Layout incorrecto: ' + key)
        require(type(row['Start']) is int and 0 < row['Start'] < DISK_BYTES // 512, 'Inicio fuera de rango')
        require(row['Sectors'] <= DISK_BYTES // 512 - row['Start'], 'Fin fuera de disco')
        p = PurePosixPath(row['PartitionPath'])
        require(str(p) == row['PartitionPath'] and str(p).startswith('/sys/devices/'), 'Ruta sysfs no canónica')
        require(not any(x == 'virtual' or x.lower().startswith('usb') for x in p.parts), 'Ruta sysfs no eMMC')
        require(p.parent.as_posix() == row['ParentPath'] and p.parent.parent.name == 'block', 'Padre no directo')
        require(row['DiskName'] == p.parent.name and re.fullmatch('mmcblk[0-9]+', row['DiskName']), 'Nombre disco inválido')
        require(p.name in (name, f"{row['DiskName']}p{minor}"), 'Nombre de partición no admitido')
        parent = parent or row['ParentPath']
        require(parent == row['ParentPath'], 'Padres diferentes')
        ranges.append((row['Start'], row['Start'] + row['Sectors'], name))
        public_layouts.append({'name': name, 'major_minor': row['MajorMinor'], 'bytes': size,
                               'start_sector': row['Start'], 'sectors': row['Sectors'], 'sysfs_basename': p.name})
    ranges.sort()
    require(all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])), 'Particiones solapadas')
    require(started == {'bytes': PROFILE['data'][0], 'device': '179:20', 'filesystem_bytes': FS_BYTES, 'state': 'format_started'}, 'Inicio formato incorrecto')
    integer(formatted['exit'], 0, 'Formateador falló')
    require(formatted['timeout'] is False and formatted['output_truncated'] is False, 'Formateador incompleto')
    require(isinstance(formatted['output'], str) and 'Creating filesystem with 853500 4k blocks' in formatted['output'], 'Salida formateador incompatible')
    require(prepared['state'] == 'userdata_prepared' and prepared['filesystem_bytes'] == FS_BYTES, 'Preparación data incorrecta')
    require(all(prepared[k] is True for k in ('footer_zero', 'empty_readonly_mount_verified', 'unmounted_after_check')), 'Preparación data incompleta')
    require(finished == {'state': 'installed_verified', 'package_id': PACKAGE, 'platform_version': '0.2.0'}, 'Falta cierre completo022')
    lines = log.splitlines()
    require(len(lines) == 10, 'Log debe tener cinco pares exactos')
    times = []
    for index, name in enumerate(NAMES):
        words = lines[2 * index].split(' ')
        require(len(words) == 3 and words[:2] == ['INICIO', name], 'Inicio/orden de flash incorrecto')
        times.append(utc(words[2]))
        require(lines[2 * index + 1] == f"VERIFICADO {name} {images[name]['sha256']}", 'SHA/orden de relectura incorrecto')
    declared = utc(backup['created_utc'])
    require(all(a <= b for a, b in zip([declared] + times, times)), 'Reloj retrocede en recibos')
    return records, public_layouts, {'clock_trusted_as_real_date': False, 'backup_receipt_declared_utc': backup['created_utc'],
        'flash_start_declared_utc': {n: t.strftime('%Y-%m-%dT%H:%M:%SZ') for n, t in zip(NAMES, times)},
        'backup_receipt_to_first_flash_start_seconds': int((times[0] - declared).total_seconds()),
        'successive_flash_start_intervals_seconds': [int((b - a).total_seconds()) for a, b in zip(times, times[1:])],
        'exact_total_or_per_image_duration_known': False}


def self_tests(documents, log, manifest):
    metadata(documents, log, manifest)
    tests = [('duplicate_json', lambda: decode(b'{"x":1,"x":2}'))]
    changes = [
        ('nonzero_formatter', lambda d: d[JSON_FILES[2]].update(exit=1)),
        ('formatter_timeout', lambda d: d[JSON_FILES[2]].update(timeout=True)),
        ('output_truncated', lambda d: d[JSON_FILES[2]].update(output_truncated=True)),
        ('missing_footer', lambda d: d[JSON_FILES[3]].update(footer_zero=False)),
        ('wrong_package', lambda d: d[JSON_FILES[4]].update(package_id='TVBASE-P291-A9-0.2.1')),
        ('wrong_size', lambda d: d[JSON_FILES[0]]['records'][0].update(bytes=1)),
        ('hash_disagreement', lambda d: d[JSON_FILES[0]]['records'][0].update(usb_read_sha256='0' * 64)),
        ('duplicate_backup', lambda d: d[JSON_FILES[0]]['records'].__setitem__(1, d[JSON_FILES[0]]['records'][0])),
        ('wrong_parent', lambda d: d[JSON_FILES[0]]['layouts_observed']['data'].update(ParentDevice=0)),
        ('out_of_disk', lambda d: d[JSON_FILES[0]]['layouts_observed']['data'].update(Start=DISK_BYTES // 512)),
        ('overlap', lambda d: d[JSON_FILES[0]]['layouts_observed']['data'].update(Start=5197824)),
    ]
    for label, change in changes:
        candidate = copy.deepcopy(documents)
        change(candidate)
        tests.append((label, lambda d=candidate: metadata(d, log, manifest)))
    tests += [('wrong_flash_hash', lambda: metadata(documents, log.replace(manifest['images'][0]['sha256'], '0' * 64), manifest)),
              ('extra_flash_line', lambda: metadata(documents, log + 'ERROR extra\n', manifest)),
              ('invalid_clock', lambda: metadata(documents, log.replace('T01:', 'T99:'), manifest))]
    for label, action in tests:
        try:
            action()
        except (ValueError, KeyError, TypeError):
            continue
        raise ValueError('Regresión no rechazada: ' + label)
    return {'valid_metadata_case_passed': True, 'rejected_cases': [name for name, _ in tests], 'scope': 'PC metadata only; no device calls'}


def run(directory, output=None, self_test_only=False):
    directory = directory.resolve()
    require(directory.is_relative_to((ROOT / 'privado').resolve()), 'Solo adquisición local dentro de privado/')
    acquisition_path = safe_file(directory, 'adquisicion.json')
    raw = acquisition_path.read_bytes()
    acquisition = decode(raw)
    require(acquisition['state'] == 'verified' and type(acquisition['exit_code']) is int and acquisition['exit_code'] == 0, 'Adquisición no terminada/verificada')
    require(acquisition['usb_written'] is False and acquisition['tv_contacted'] is False, 'Alcance de adquisición diferente')
    integer(acquisition['backup_images_verified'], 6, 'Faltan imágenes en adquisición')
    integer(acquisition['backup_bytes_verified'], TOTAL, 'Total adquisición distinto')
    require(sha(RELEASE) == RELEASE_SHA, 'Recibo de release022 cambió')
    release = decode(RELEASE.read_bytes())
    manifest = release['manifest']
    require(manifest['id'] == PACKAGE and release['version'] == '0.2.2', 'Release incorrecto')
    rows = {}
    for row in acquisition['files']:
        relative = row['relative_path'].replace('\\', '/')
        require(relative not in rows, 'Ruta de adquisición duplicada')
        require(row['verified'] is True and row['sha256'] == row['pc_read_sha256'] and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'Registro adquisición inválido')
        require(type(row['bytes']) is int and row['bytes'] >= 0, 'Tamaño adquisición inválido')
        rows[relative] = row
    integer(acquisition['bytes_copied'], sum(r['bytes'] for r in rows.values()), 'Total de todos los archivos no coincide')
    prefixes = {str(PurePosixPath(p).parent) for p in rows if p.endswith('/00-backup-verified.json') and PurePosixPath(p).parent.name.startswith('TVBASE-respaldo-022-')}
    require(len(prefixes) == 1, 'Se requiere una sola transacción022')
    prefix = prefixes.pop()
    expected = JSON_FILES + ['instalacion.log'] + [n + '.img' for n in NAMES + ['data']]
    require({p for p in rows if p.startswith(prefix + '/')} == {prefix + '/' + n for n in expected}, 'Archivos de cierre faltantes/extraños')
    def verify_file(relative, image=False):
        row = rows[relative]
        path = safe_file(directory, relative)
        integer(path.stat().st_size, row['bytes'], 'Tamaño físico diferente')
        if image:
            print('Verificando copia PC: ' + path.name, file=sys.stderr, flush=True)
        require(sha(path) == row['sha256'], 'SHA físico PC distinto: ' + path.name)
        return path
    documents = {}
    for name in JSON_FILES:
        documents[name] = decode(verify_file(prefix + '/' + name).read_bytes())
    log = verify_file(prefix + '/instalacion.log').read_text(encoding='utf-8')
    records, layouts, clock = metadata(documents, log, manifest)
    tests = self_tests(documents, log, manifest)
    if self_test_only:
        return {'state': 'metadata_tests_passed', 'tests': tests}
    public_backups = []
    for row in records:
        relative = prefix + '/' + row['file']
        acquired = rows[relative]
        require(acquired['matches_tv_receipt'] is True, 'Imagen no cotejada al adquirir')
        require(acquired['bytes'] == row['bytes'] and acquired['sha256'] == row['sha256'], 'Imagen no coincide con reciboTV')
        verify_file(relative, image=True)
        public_backups.append({'name': row['name'], 'bytes': row['bytes'], 'sha256': row['sha256'],
                               'original_p291_hash_matches': True if row['name'] != 'data' else None,
                               'independent_pc_read_matches_tv_three_hashes': True})
    photo = verify_file('foto-inicio-tvbase.png')
    require(acquisition_path.read_bytes() == raw, 'Adquisición cambió durante revisión')
    summary = {'schema_version': 1, 'state': 'physical_installation_022_evidence_independently_verified',
        'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'reviewer_script_sha256': sha(Path(__file__)),
        'scope': 'Read existing PC acquisition only; no TV, USB, network, install, restore or configuration operation',
        'acquisition': {'state': 'verified', 'exit_code': 0, 'receipt_sha256': hashlib.sha256(raw).hexdigest(),
                        'declared_files': len(rows), 'declared_bytes': acquisition['bytes_copied'],
                        'independently_rehashed_files': len(expected) + 1, 'scope_note': '12 transaction files plus launcher photo; historical acquisitions not rehashed'},
        'release': {'package_id': PACKAGE, 'platform_version': '0.2.0', 'receipt_sha256': RELEASE_SHA,
                    'sealed_pc_zip_sha256': release['sha256'], 'executed_zip_whole_hash_recorded_by_installer': False},
        'installer_result': {'physical_installation_verified_by_persisted_receipts': True,
             'userdata_backup_confirmed': True, 'userdata_format_completed': True, 'formatter_exit': 0,
             'formatter_timeout': False, 'formatter_output_truncated': False, 'filesystem_bytes': FS_BYTES,
             'footer_zero_readback': True, 'empty_readonly_mount_and_unmount_verified': True,
             'five_image_fsync_and_readback_completed': True, 'flash_order': NAMES,
             'installed_image_sha256': {i['name']: i['sha256'] for i in manifest['images']},
             'terminal_state': 'installed_verified'},
        'backups': {'count': 6, 'bytes': TOTAL, 'records': public_backups, 'restoration_tested': False},
        'layouts': {'source': 'Physical recovery receipt00, initial observations; later guard executions inferred from completed sealed installer',
                    'start_offsets_now_observed': True, 'parent_bytes': DISK_BYTES, 'parent_major_minor': '179:0',
                    'parent_type_raw_field_recorded': False, 'records': layouts},
        'receipt_sha256': {n: rows[prefix + '/' + n]['sha256'] for n in JSON_FILES + ['instalacion.log']},
        'timing': clock, 'parser_tests': tests,
        'separate_user_observations': {'launcher_visible': {'source': 'User photo', 'photo_sha256': sha(photo), 'bytes': photo.stat().st_size},
            'wifi_reconnected': {'source': 'User statement, not measured by this verifier'},
            'home_key_does_not_return_to_launcher': {'source': 'User statement', 'issue': 'ISSUE-HOME-01'}},
        'limits': ['Receipts and log are unsigned; PC acquisition hashes preserve received evidence, not cryptographic attestation from the TV.',
                  'Installer receipts pin package_id and five payload hashes; they do not record the whole executed ZIP hash or executed recovery hash.',
                  'TV clock says January 2020. Intervals between starts include intervening checks; exact backup, format and total installation durations are unknown.',
                  'No post-boot partition rehash was performed. Current running Android identity is supported by user observations, separately from recovery readback.',
                  'Cold boot with USB absent, reentry into recovery, five-image restore and raw userdata restore remain untested.',
                  'WiFi reconnection does not establish Internet access, stability, throughput, WebView provider or multimedia performance.',
                  'HOME issue remains open; no fixes or new product tests are authorized before user OK.']}
    if output:
        with output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(summary, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('acquisition', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test-only', action='store_true')
    args = parser.parse_args()
    try:
        result = run(args.acquisition, args.output, args.self_test_only)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('Verificación rechazada: ' + str(exc), file=sys.stderr)
        sys.exit(1)
