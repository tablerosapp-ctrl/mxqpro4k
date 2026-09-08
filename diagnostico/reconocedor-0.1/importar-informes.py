"""Verifica capturas del reconocedor y conserva copias privadas nuevas en PC.

No extrae el ZIP, modifica el origen ni determina aptitud para instalar una ROM.
--verify-only comprueba el origen sin crear archivos. Las capturas parciales son
válidas si su contenedor, manifiesto y datos cumplen este contrato de integridad.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import sys
import time
import unicodedata
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MAX_ENTRIES = 20_000
MAX_FILE = 128 * 1024 ** 2
MAX_JSON = 16 * 1024 ** 2
MAX_TOTAL = 5 * 1024 ** 3 // 2
MAX_ZIP = 3 * 1024 ** 3
MAX_CENTRAL = 64 * 1024 ** 2
MAX_BATCH = 1024
MAX_REPORTS_TOTAL = 64 * 1024 ** 2
COPY_MARGIN = 64 * 1024 ** 2
CHUNK = 1024 ** 2
SHA = re.compile(r'[0-9a-f]{64}')
PROFILE = re.compile(r'[a-z0-9][a-z0-9_-]{0,63}')
RESERVED = re.compile(r'(?:con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])', re.I)


class InvalidCapture(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise InvalidCapture(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def info_key(info):
    # Windows puede diferir en la semántica de ctime entre lstat y fstat.
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink


def ordinary(path, *, directory=False):
    need(path.is_absolute() and '..' not in path.parts, 'Ruta absoluta ambigua.')
    for item in (*reversed(path.parents), path):
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not (
            getattr(info, 'st_file_attributes', 0) & 0x400), 'Ruta con enlace o reparse point.')
        want_dir = item != path or directory
        need(stat.S_ISDIR(info.st_mode) if want_dir else stat.S_ISREG(info.st_mode),
             'Tipo de archivo o directorio no admitido.')
        if not want_dir:
            need(info.st_nlink == 1, 'Archivo con enlaces adicionales.')
    need(path.resolve(strict=True) == path, 'La ruta resuelta difiere del origen indicado.')
    return info


def open_readonly(path):
    before = ordinary(path)
    stream = path.open('rb')
    if info_key(before) != info_key(os.fstat(stream.fileno())):
        stream.close()
        raise InvalidCapture('El archivo cambió al abrirlo.')
    return stream, before


def unchanged(stream, path, before):
    need(info_key(before) == info_key(os.fstat(stream.fileno()))
         == info_key(ordinary(path)), 'El archivo cambió durante la lectura.')


class Progress:
    def __init__(self, label, emit=print):
        self.label, self.emit, self.last = label, emit, time.monotonic()

    def tick(self, count):
        if self.emit and time.monotonic() - self.last >= 15:
            self.emit(self.label + ': ' + str(count) + ' bytes', flush=True)
            self.last = time.monotonic()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Clave JSON duplicada.')
        result[key] = value
    return result


def invalid_constant(value):
    raise InvalidCapture('Número JSON no finito.')


def json_value(raw):
    need(0 < len(raw) <= MAX_JSON, 'JSON fuera del límite de tamaño.')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=no_duplicates,
                           parse_constant=invalid_constant)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, InvalidCapture):
            raise
        raise InvalidCapture('JSON UTF-8 inválido o demasiado profundo.') from None
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        need(depth <= 32 and nodes <= 300_000, 'Estructura JSON excesiva.')
        if isinstance(item, dict):
            pending.extend((x, depth + 1) for x in item.keys())
            pending.extend((x, depth + 1) for x in item.values())
        elif isinstance(item, list):
            pending.extend((x, depth + 1) for x in item)
        elif isinstance(item, float):
            need(math.isfinite(item), 'Número JSON no finito.')
        elif isinstance(item, str):
            need(not any(unicodedata.category(c) == 'Cs' for c in item), 'Unicode sustituto aislado en JSON.')
    return value


def canonical_member(name):
    need(isinstance(name, str) and 0 < len(name.encode('utf-8')) <= 1024,
         'Nombre ZIP vacío o demasiado largo.')
    need('\\' not in name and ':' not in name and not name.startswith('/'),
         'Ruta ZIP absoluta, Windows o con flujo alternativo.')
    need(not any(unicodedata.category(c) in ('Cc', 'Cs') for c in name),
         'Carácter de control en ruta ZIP.')
    parts = name.split('/')
    for part in parts:
        need(part not in ('', '.', '..') and not part.endswith((' ', '.')),
             'Componente ambiguo de ruta ZIP.')
        need(len(part.encode('utf-16-le')) // 2 <= 255, 'Componente de ruta demasiado largo.')
        need(not RESERVED.fullmatch(part.split('.', 1)[0]), 'Nombre reservado de Windows en ZIP.')
        need(not any(c in '<>"|?*' for c in part), 'Carácter no admitido por Windows en ZIP.')
    need(name in ('informe.json', 'manifest.json') or
         (len(parts) >= 2 and parts[0] in ('details', 'drivers')),
         'Ruta fuera de los espacios de nombres permitidos.')
    return unicodedata.normalize('NFC', name).casefold()


def central_directory(stream, size):
    """Acota el directorio antes de que zipfile lo cargue completo en memoria."""
    need(22 <= size <= MAX_ZIP, 'ZIP fuera del límite de tamaño.')
    amount = min(size, 65557)
    stream.seek(size - amount)
    tail = stream.read(amount)
    at = tail.rfind(b'PK\x05\x06')
    need(at >= 0 and len(tail) - at >= 22, 'ZIP sin fin de directorio válido.')
    row = struct.unpack_from('<4s4H2IH', tail, at)
    _, disk, central_disk, this_count, count, central_size, offset, comment = row
    need(at + 22 + comment == len(tail), 'Final de ZIP truncado o con bytes ajenos.')
    need(disk == central_disk == 0 and this_count == count, 'ZIP multidisco no admitido.')
    need(2 <= count <= MAX_ENTRIES and 0 < central_size <= MAX_CENTRAL,
         'Cantidad de entradas o directorio ZIP fuera del límite.')
    # Los límites del contrato quedan por debajo de los umbrales ZIP64 del
    # directorio final. No son necesarios contadores/offsets centinela ZIP64.
    need(offset != 0xffffffff and central_size != 0xffffffff,
         'Directorio ZIP64 fuera del contrato.')
    need(offset + central_size == size - amount + at, 'Ubicación del directorio ZIP incoherente.')
    stream.seek(0)
    need(stream.read(4) == b'PK\x03\x04', 'Prefijo ajeno a ZIP o archivo autoextraíble.')
    return count, offset


def inspect_members(archive, stream, expected_count, central_start):
    entries = archive.infolist()
    need(len(entries) == expected_count, 'Conteo de entradas ZIP incoherente.')
    known = {}
    exact = {}
    total = 0
    for entry in entries:
        need(entry.orig_filename == entry.filename, 'Nombre ZIP truncado por NUL.')
        key = canonical_member(entry.filename)
        need(key not in known, 'Ruta ZIP duplicada o equivalente en Windows.')
        mode = entry.external_attr >> 16
        kind = stat.S_IFMT(mode)
        need(not entry.is_dir() and not (entry.external_attr & 0x10)
             and kind in (0, stat.S_IFREG), 'ZIP contiene directorio, enlace o nodo especial.')
        need(not entry.flag_bits & 1 and entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
             'Entrada cifrada o compresión no admitida.')
        limit = MAX_JSON if entry.filename.lower().endswith('.json') else MAX_FILE
        need(0 <= entry.file_size <= limit and 0 <= entry.compress_size <= MAX_ZIP,
             'Entrada ZIP fuera del límite de tamaño.')
        total += entry.file_size
        need(total <= MAX_TOTAL, 'ZIP excede el límite descomprimido.')
        known[key] = entry.filename
        exact[entry.filename] = entry
    need('informe.json' in exact and 'manifest.json' in exact, 'Falta informe o manifiesto.')
    for key in known:
        parts = key.split('/')
        need(not any('/'.join(parts[:i]) in known for i in range(1, len(parts))),
             'Una ruta ZIP es archivo y también padre de otra.')
    ordered = sorted(entries, key=lambda x: x.header_offset)
    need(ordered[0].header_offset == 0, 'Prefijo ZIP no admitido.')
    for i, entry in enumerate(ordered):
        end = ordered[i + 1].header_offset if i + 1 < len(ordered) else central_start
        need(0 <= entry.header_offset < end <= central_start, 'Cabeceras ZIP superpuestas.')
        stream.seek(entry.header_offset)
        raw = stream.read(30)
        need(len(raw) == 30, 'Cabecera local ZIP truncada.')
        local = struct.unpack('<4s5H3I2H', raw)
        need(local[0] == b'PK\x03\x04' and local[2] == entry.flag_bits
             and local[3] == entry.compress_type, 'Cabecera ZIP local incoherente.')
        start = entry.header_offset + 30 + local[-2] + local[-1]
        need(start + entry.compress_size <= end, 'Datos ZIP superpuestos.')
    return exact, total


def read_member(archive, entry, progress, *, keep=False):
    digest = hashlib.sha256()
    count = 0
    chunks = []
    with archive.open(entry, 'r') as stream:
        while block := stream.read(CHUNK):
            count += len(block)
            need(count <= entry.file_size, 'Entrada ZIP excede el tamaño declarado.')
            digest.update(block)
            if keep:
                chunks.append(block)
            progress.tick(count)
    # zipfile comprueba CRC al consumir la entrada hasta el final.
    need(count == entry.file_size, 'Entrada ZIP incompleta.')
    return digest.hexdigest(), b''.join(chunks) if keep else None


def uuid_text(value):
    need(isinstance(value, str), 'UUID ausente o no textual.')
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        raise InvalidCapture('UUID inválido.') from None
    need(str(parsed) == value and parsed.int != 0, 'UUID no canónico o nulo.')
    return parsed


def validate_report(report, filename):
    required = {'schema', 'capture_id', 'device_id', 'suggested_profile', 'profile_confidence',
                'display_name', 'android', 'hardware', 'webview', 'export_limits'}
    need(isinstance(report, dict) and required <= set(report), 'Campos obligatorios de informe ausentes.')
    need(report['schema'] == 'tvbase-recognition-1', 'Schema de informe no admitido.')
    capture, device = uuid_text(report['capture_id']), uuid_text(report['device_id'])
    profile = report['suggested_profile']
    need(isinstance(profile, str) and PROFILE.fullmatch(profile), 'Perfil candidato inválido.')
    need(report['profile_confidence'] in ('declared', 'corroborated', 'unknown'), 'Confianza de perfil inválida.')
    need(isinstance(report['display_name'], str) and 0 < len(report['display_name']) <= 256,
         'Nombre visible ausente o excesivo.')
    for key in ('android', 'hardware', 'webview', 'export_limits'):
        need(isinstance(report[key], dict), 'Se esperaba un objeto de metadatos.')
    expected = 'TVBASE-' + profile + '-' + device.hex[:8] + '-' + capture.hex[:8] + '.zip'
    need(filename == expected, 'El nombre del ZIP no coincide con su informe.')


def verify_archive(path, *, emit=print):
    path = Path(path).absolute()
    progress = Progress('Verificando captura', emit)
    stream, before = open_readonly(path)
    try:
        with stream:
            count, central_start = central_directory(stream, before.st_size)
            with zipfile.ZipFile(stream, 'r') as archive:
                entries, total = inspect_members(archive, stream, count, central_start)
                manifest_sha, raw = read_member(archive, entries['manifest.json'], progress, keep=True)
                manifest = json_value(raw)
                need(isinstance(manifest, dict) and set(manifest) == {'schema', 'capture_id', 'files'}
                     and manifest['schema'] == 'tvbase-recognition-files-1', 'Manifiesto no admitido.')
                uuid_text(manifest['capture_id'])
                listed = manifest['files']
                need(isinstance(listed, list) and len(listed) == len(entries) - 1,
                     'El manifiesto no enumera exactamente las entradas.')
                expected = {}
                for row in listed:
                    need(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'},
                         'Entrada de manifiesto inválida.')
                    name = row['path']
                    canonical_member(name)
                    need(name != 'manifest.json' and name in entries and name not in expected,
                         'Entrada ausente, repetida o autorreferencia del manifiesto.')
                    need(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_FILE
                         and row['bytes'] == entries[name].file_size,
                         'Tamaño de manifiesto inválido o diferente del ZIP.')
                    need(isinstance(row['sha256'], str) and SHA.fullmatch(row['sha256']), 'SHA256 inválido.')
                    expected[name] = row
                need(set(expected) == set(entries) - {'manifest.json'}, 'Listado de manifiesto incompleto.')
                report = None
                for name, row in expected.items():
                    digest, data = read_member(archive, entries[name], progress, keep=name == 'informe.json')
                    need(digest == row['sha256'], 'SHA256 de contenido diferente del manifiesto.')
                    if data is not None:
                        report = json_value(data)
                validate_report(report, path.name)
                need(report['capture_id'] == manifest['capture_id'], 'Captura distinta entre informe y manifiesto.')
            unchanged(stream, path, before)
            stream.seek(0)
            digest = hashlib.sha256()
            while block := stream.read(CHUNK):
                digest.update(block)
                progress.tick(stream.tell())
            unchanged(stream, path, before)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, struct.error, OverflowError):
        raise InvalidCapture('ZIP inválido, CRC incorrecto o entrada no legible.') from None
    return {'source': path, 'source_snapshot': info_key(before), 'bytes': before.st_size,
            'sha256': digest.hexdigest(), 'manifest_sha256': manifest_sha,
            'member_count': count, 'uncompressed_bytes': total,
            'report_bytes': entries['informe.json'].file_size, 'report': report}


def sources(folder):
    folder = Path(folder).absolute()
    ordinary(folder, directory=True)
    all_files = list(folder.iterdir())
    archives = sorted((p for p in all_files if p.suffix.lower() == '.zip'), key=lambda p: p.name.casefold())
    need(0 < len(archives) <= MAX_BATCH, 'Se requieren entre 1 y 1024 ZIP en la carpeta de origen.')
    need(len({unicodedata.normalize('NFC', p.name).casefold() for p in archives}) == len(archives),
         'Nombres de ZIP equivalentes en el origen.')
    return folder, archives, len(all_files) - len(archives)


def verify_batch(folder, *, emit=print):
    source, archives, ignored = sources(folder)
    result = []
    captures = set()
    report_bytes = 0
    for number, path in enumerate(archives, 1):
        if emit:
            emit('Validando captura ' + str(number) + '/' + str(len(archives)), flush=True)
        item = verify_archive(path, emit=emit)
        capture_id = item['report']['capture_id']
        need(capture_id not in captures, 'capture_id repetido en el lote; requiere revisión.')
        captures.add(capture_id)
        report_bytes += item['report_bytes']
        need(report_bytes <= MAX_REPORTS_TOTAL, 'Metadatos acumulados excesivos; dividir la importación.')
        result.append(item)
    return source, result, ignored


def copy_verified(item, directory, *, emit=print):
    source = item['source']
    destination = directory / source.name
    temporary = directory / (source.name + '.parcial')
    stream, before = open_readonly(source)
    progress = Progress('Copiando captura', emit)
    digest, count = hashlib.sha256(), 0
    with stream, temporary.open('xb') as output:
        need(info_key(before) == item['source_snapshot'], 'El ZIP cambió después de validarlo.')
        while block := stream.read(CHUNK):
            need(output.write(block) == len(block), 'Escritura de copia incompleta.')
            digest.update(block)
            count += len(block)
            progress.tick(count)
        output.flush()
        os.fsync(output.fileno())
        unchanged(stream, source, before)
    need(count == item['bytes'] and digest.hexdigest() == item['sha256'], 'La copia difiere del ZIP validado.')
    digest, reread = hashlib.sha256(), 0
    with temporary.open('rb') as stored:
        while block := stored.read(CHUNK):
            digest.update(block)
            reread += len(block)
            progress.tick(reread)
    need(reread == count and digest.hexdigest() == item['sha256'], 'La relectura de la copia no coincide.')
    need(not destination.exists(), 'El destino de copia ya existe.')
    # El directorio es nuevo y exclusivo de esta importación. En Windows rename
    # tampoco reemplaza un destino existente. No se renombra ningún origen.
    os.link(temporary, destination)
    temporary.unlink()
    return {'path': 'zips/' + source.name, 'bytes': count, 'sha256': item['sha256'],
            'file_fsync': True, 'readback_verified': True}


def catalog(items, copies):
    devices = {}
    profiles = {}
    captures = []
    for item, copied in zip(items, copies):
        report = item['report']
        identity = report['device_id']
        profile = report['suggested_profile']
        device = devices.setdefault(identity, {'device_id': identity, 'identity_scope': 'app_installation',
                                               'capture_ids': [], 'reported_profiles': set(), 'display_names': set()})
        device['capture_ids'].append(report['capture_id'])
        device['reported_profiles'].add(profile)
        device['display_names'].add(report['display_name'])
        profiles.setdefault(profile, set()).add(identity)
        captures.append({'capture_id': report['capture_id'], 'device_id': identity,
                         'display_name': report['display_name'], 'suggested_profile': profile,
                         'reported_profile_confidence': report['profile_confidence'],
                         'reported_capture_status': report.get('capture_status', report.get('status', 'unspecified')),
                         'integrity': 'verified', 'profile_installation_approved': False,
                         'android': report['android'], 'hardware': report['hardware'],
                         'webview': report['webview'], 'export_limits': report['export_limits'],
                         'manifest_sha256': item['manifest_sha256'], 'archive': copied})
    for row in devices.values():
        row['reported_profiles'] = sorted(row['reported_profiles'])
        row['display_names'] = sorted(row['display_names'])
        row['profile_conflict_requires_review'] = len(set(row['reported_profiles']) - {'unknown'}) > 1
        row['physical_identity_proven'] = False
    return {'schema': 'tvbase-recognition-import-1', 'state': 'imported_verified', 'created_at_utc': now(),
            'private_data': True, 'capture_count': len(captures), 'app_installation_identity_count': len(devices),
            'captures': captures, 'devices': list(devices.values()),
            'candidate_profiles': [{'profile': name, 'app_installation_identity_count': len(ids),
                                    'installation_approved': False} for name, ids in sorted(profiles.items())],
            'limits': ['Manifiesto sin firma: integridad, no autenticidad ni identidad física acreditada.',
                       'device_id identifica una instalación de la APK; puede cambiar o duplicarse al reinstalar/clonar datos.',
                       'Capturas parciales o fallidas pueden tener integridad correcta; sus estados se conservan.',
                       'Ningún perfil candidato autoriza instalar una ROM.',
                       'El reloj del TV y el orden de archivos no acreditan cronología.',
                       'No se extrajeron ni ejecutaron drivers.']}


def durable_new_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with path.open('xb') as output:
        need(output.write(raw) == len(raw), 'Escritura de recibo incompleta.')
        output.flush()
        os.fsync(output.fileno())


def import_batch(source, output=None, *, verify_only=False, emit=print):
    source_path, items, ignored = verify_batch(source, emit=emit)
    if verify_only:
        return {'state': 'verified_only', 'capture_count': len(items),
                'app_installation_identity_count': len({x['report']['device_id'] for x in items}),
                'ignored_non_zip_entries': ignored, 'written_files': 0, 'installation_approved': False}
    need(output is not None, 'Falta --output para conservar copias.')
    output = Path(output).absolute()
    need(output.is_relative_to(ROOT) and output != ROOT and '..' not in output.parts,
         'El destino debe ser nuevo y estar dentro del proyecto.')
    need(not output.exists() and not output.is_symlink(), 'El destino ya existe; no se sobrescribe.')
    ordinary(output.parent, directory=True)
    need(not output.is_relative_to(source_path) and not source_path.is_relative_to(output),
         'Origen y destino no pueden contenerse entre sí.')
    need(shutil.disk_usage(output.parent).free >= sum(x['bytes'] for x in items)
         + 8 * sum(x['report_bytes'] for x in items) + COPY_MARGIN,
         'Espacio insuficiente para las copias y recibos.')
    output.mkdir()
    private = output / 'privado'
    private.mkdir()
    archives = private / 'zips'
    archives.mkdir()
    try:
        copies = [copy_verified(item, archives, emit=emit) for item in items]
        index = catalog(items, copies)
        index.update(ignored_non_zip_entries=ignored, source_directory=str(source_path),
                     source_modified=False, directory_fsync_verified=False)
        durable_new_json(private / 'catalogo.json', index)
        # Verificar que el índice es legible y conserva los mismos datos.
        need(json.loads((private / 'catalogo.json').read_text(encoding='utf-8')) == index,
             'Relectura del catálogo incorrecta.')
        return {'state': 'imported_verified', 'capture_count': len(items),
                'app_installation_identity_count': index['app_installation_identity_count'],
                'archive_bytes': sum(x['bytes'] for x in items), 'ignored_non_zip_entries': ignored,
                'installation_approved': False, 'source_modified': False}
    except Exception as error:
        # La carpeta nueva y los .parcial se conservan. No borrar ni reintentar
        # automáticamente; otra importación necesitará otro --output nuevo.
        durable_new_json(private / 'IMPORTACION-INCOMPLETA.json', {
            'schema': 'tvbase-recognition-import-failure-1', 'state': 'incomplete',
            'stopped_at_utc': now(), 'error_type': type(error).__name__, 'source_modified': False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Carpeta de ZIP; lectura sin recursión.')
    parser.add_argument('--output', help='Carpeta nueva dentro del proyecto; datos en privado/.')
    parser.add_argument('--verify-only', action='store_true', help='Validar sin copiar ni escribir archivos.')
    args = parser.parse_args()
    try:
        result = import_batch(args.source, args.output, verify_only=args.verify_only)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    except Exception as error:
        message = str(error) if isinstance(error, InvalidCapture) else 'Error de lectura/escritura (' + type(error).__name__ + ').'
        print(json.dumps({'state': 'failed', 'error': message, 'installation_approved': False}, ensure_ascii=False), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
