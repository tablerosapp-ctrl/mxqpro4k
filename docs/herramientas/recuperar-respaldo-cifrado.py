"""Recover this project's encrypted backup to a NEW private PC directory.

Python 3.9+ and a separately obtained age executable are required. Offline only:
  python recuperar-respaldo-cifrado.py --manifest RESPALDO-CIFRADO.json \
      --key CLAVE-PRIVADA.txt --age /path/to/age --output /private/new-directory

Keep the parts next to the public manifest; keep the private key elsewhere.
No downloads, mounts, flashing, device access, shell commands or automatic cleanup.
On failure preserve the output and INCOMPLETO.json; choose another NEW directory
for a later attempt. A verified file recovery does not prove TV restoration.
The plaintext ZIP and extracted files are private. On Windows files are fsynced;
Python's portable directory-fsync interface is unavailable and is not claimed.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

NAME = 'TVBASE-P291-RESPALDO-20260908.zip.age'
INDEX = 'RESPALDO-INDICE.json'
PART_BYTES = 512 * 1024 * 1024
CHUNK = 4 * 1024 * 1024
MAX_JSON = 16 * 1024 * 1024
MAX_FILES = 100000
MAX_PLAIN_BYTES = 128 * 1024 ** 3
FLAGS = 0x08000000 if os.name == 'nt' else 0


class RecoveryError(Exception):
    pass


def need(condition, message):
    if not condition:
        raise RecoveryError(message)


def no_links(path):
    """Reject POSIX symlinks and all Windows reparse points, including junctions."""
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        st = item.lstat()
        need(not stat.S_ISLNK(st.st_mode) and
             not getattr(st, 'st_file_attributes', 0) & 0x400,
             'Enlace o reparse point no admitido.')
    return path


def ordinary(path):
    path = no_links(path)
    need(stat.S_ISREG(path.stat().st_mode), 'Se requiere un archivo regular.')
    return path


def open_read(path):
    path = ordinary(path)
    before = path.stat()
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_BINARY', 0) |
                 getattr(os, 'O_NOFOLLOW', 0))
    try:
        current = os.fstat(fd)
        need(stat.S_ISREG(current.st_mode) and
             (before.st_dev, before.st_ino) == (current.st_dev, current.st_ino),
             'Archivo cambiado durante la apertura.')
        return os.fdopen(fd, 'rb')
    except BaseException:
        os.close(fd)
        raise


def new_file(path):
    no_links(path.parent)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    return os.fdopen(fd, 'wb')


def sync_dir(path):
    if os.name == 'nt':
        return False
    fd = os.open(str(no_links(path)), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


def write_new(path, raw):
    with new_file(path) as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    sync_dir(path.parent)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Clave JSON duplicada.')
        result[key] = value
    return result


def decode_json(raw):
    need(len(raw) <= MAX_JSON, 'JSON supera el límite permitido.')
    try:
        value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs_unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               RecoveryError('Constante JSON no admitida.')))
    except (UnicodeError, ValueError) as exc:
        raise RecoveryError('JSON inválido.') from exc
    need(isinstance(value, dict), 'Se requiere un objeto JSON.')
    return value


def read_json(path):
    with open_read(path) as f:
        return decode_json(f.read(MAX_JSON + 1))


def size_hash(row, allow_empty=True):
    need(isinstance(row, dict), 'Fila de índice inválida.')
    count, digest = row.get('bytes'), row.get('sha256')
    need(type(count) is int and (0 if allow_empty else 1) <= count <= MAX_PLAIN_BYTES,
         'Tamaño inválido.')
    need(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest),
         'SHA256 inválido.')
    return count, digest


def safe_relative(name):
    need(isinstance(name, str) and 0 < len(name) <= 2048, 'Ruta inválida.')
    need(not any(ord(c) < 32 or ord(c) == 127 or c in '\\:<>"|?*' for c in name),
         'Ruta incompatible o insegura.')
    pieces = name.split('/')
    for piece in pieces:
        need(piece not in ('', '.', '..') and len(piece) <= 240 and
             not piece.endswith(('.', ' ')), 'Componente de ruta inseguro.')
        normalized = unicodedata.normalize('NFKC', piece).casefold()
        need(not re.fullmatch(r'(con|conin\$|conout\$|prn|aux|nul|com[1-9]|lpt[1-9])',
                              normalized.split('.')[0]), 'Nombre reservado de Windows.')
    need(pieces[0] in ('originales', 'adquisicion022', 'paquetes') or name == INDEX,
         'Ruta fuera de las raíces del respaldo.')
    return name


def collision_key(name):
    return '/'.join(unicodedata.normalize('NFKC', x).casefold() for x in name.split('/'))


def check_names(names):
    seen = set()
    prefixes = {}
    for name in names:
        safe_relative(name)
        key = collision_key(name)
        need(key not in seen, 'Ruta duplicada o colisión de nombres.')
        seen.add(key)
        pieces = name.split('/')
        for i in range(1, len(pieces) + 1):
            exact = '/'.join(pieces[:i])
            normalized = collision_key(exact)
            need(normalized not in prefixes or prefixes[normalized] == exact,
                 'Colisión de directorios o nombres entre plataformas.')
            prefixes[normalized] = exact
    for key in seen:
        pieces = key.split('/')
        need(not any('/'.join(pieces[:i]) in seen for i in range(1, len(pieces))),
             'Colisión entre archivo y directorio.')


def parse_manifest(value):
    need(type(value.get('format')) is int and value['format'] == 1 and
         value.get('encryption') == 'age-v1-X25519' and
         value.get('archive_format') == 'zip-deflate' and
         value.get('encrypted_file') == NAME, 'Formato de manifiesto no admitido.')
    encrypted = {'bytes': value.get('encrypted_bytes'), 'sha256': value.get('encrypted_sha256')}
    size_hash(encrypted, False)
    parts = value.get('parts')
    need(isinstance(parts, list) and 1 <= len(parts) <= 999, 'Lista de partes inválida.')
    for number, row in enumerate(parts, 1):
        count, _ = size_hash(row, False)
        need(row.get('name') == NAME + '.part%03d' % number, 'Partes no contiguas o mal nombradas.')
        need(count == PART_BYTES if number < len(parts) else count <= PART_BYTES,
             'Tamaño de parte incorrecto.')
    need(sum(row['bytes'] for row in parts) == encrypted['bytes'], 'Suma de partes incorrecta.')
    return parts, encrypted


def transfer_checked(source, destination, expected, combined=None):
    count, h = 0, hashlib.sha256()
    while True:
        block = source.read(min(CHUNK, expected['bytes'] - count + 1))
        if not block:
            break
        count += len(block)
        need(count <= expected['bytes'], 'Archivo supera el tamaño indexado.')
        destination.write(block)
        h.update(block)
        if combined is not None:
            combined.update(block)
    need((count, h.hexdigest()) == (expected['bytes'], expected['sha256']),
         'Tamaño o SHA256 no coincide.')


class HashSink:
    def write(self, block):
        return len(block)


def verify_file(path, row):
    with open_read(path) as src:
        transfer_checked(src, HashSink(), row)


def target_file(base, name):
    safe_relative(name)
    parent = base
    for component in name.split('/')[:-1]:
        child = parent / component
        if not child.exists():
            child.mkdir(mode=0o700)
            sync_dir(parent)
        no_links(child)
        need(child.is_dir(), 'El directorio de extracción no es seguro.')
        parent = child
    result = parent / name.split('/')[-1]
    need(not os.path.lexists(result), 'El archivo de salida ya existe.')
    return result


def validate_zip(z):
    infos = z.infolist()
    need(1 <= len(infos) <= MAX_FILES + 1, 'Cantidad de entradas ZIP inválida.')
    names = [i.filename for i in infos]
    check_names(names)
    need(names.count(INDEX) == 1, 'Falta el índice interno.')
    for info in infos:
        mode = info.external_attr >> 16
        kind = stat.S_IFMT(mode)
        need(info.orig_filename == info.filename and not info.is_dir() and
             kind in (0, stat.S_IFREG) and not info.flag_bits & 1 and
             not info.external_attr & 0x10 and info.compress_type == zipfile.ZIP_DEFLATED,
             'Entrada ZIP no regular, cifrada o de formato no admitido.')
    need(z.getinfo(INDEX).file_size <= MAX_JSON, 'Índice interno demasiado grande.')
    raw = z.read(INDEX)
    index = decode_json(raw)
    need(type(index.get('format')) is int and index['format'] == 1 and
         type(index.get('unique_partition_images')) is int and
         index['unique_partition_images'] == 13, 'Formato de índice no admitido.')
    files, aliases = index.get('files'), index.get('aliases')
    need(isinstance(files, list) and 1 <= len(files) <= MAX_FILES and
         isinstance(aliases, list) and len(aliases) == 5, 'Archivos o aliases inválidos.')
    all_names = [INDEX]
    by_name = {}
    for row in files:
        size_hash(row)
        path = safe_relative(row.get('path'))
        need(path != INDEX, 'El índice no puede incluirse a sí mismo.')
        all_names.append(path)
        by_name[path] = row
    for row in aliases:
        size_hash(row)
        all_names.append(safe_relative(row.get('path')))
        source = safe_relative(row.get('same_as'))
        need(source in by_name and (row['bytes'], row['sha256']) ==
             (by_name[source]['bytes'], by_name[source]['sha256']),
             'Alias fuera del índice, encadenado o inconsistente.')
    check_names(all_names)
    need(set(names) == set(by_name) | {INDEX}, 'El ZIP tiene entradas extra o faltantes.')
    need(sum(row['bytes'] for row in files + aliases) <= MAX_PLAIN_BYTES,
         'Tamaño de extracción excesivo.')
    for path, row in by_name.items():
        need(z.getinfo(path).file_size == row['bytes'], 'Tamaño ZIP difiere del índice.')
    return raw, files, aliases


def validate_key(path):
    # Do not accept plugin identities, encrypted identity files or prompt workflows.
    with open_read(path) as f:
        raw = f.read(16385)
    need(len(raw) <= 16384, 'Archivo de identidad no admitido.')
    try:
        lines = [s.strip() for s in raw.decode('ascii').splitlines()
                 if s.strip() and not s.lstrip().startswith('#')]
    except UnicodeError as exc:
        raise RecoveryError('Se requiere una identidad X25519 local.') from exc
    need(len(lines) == 1 and re.fullmatch(r'AGE-SECRET-KEY-1[0-9A-Z]{20,100}', lines[0]),
         'Se requiere una única identidad X25519 local.')


def recover(manifest, key, age, output):
    output = Path(os.path.abspath(output))
    no_links(output.parent)
    need(not os.path.lexists(output), 'La salida debe ser un directorio NUEVO.')
    manifest, key, age = ordinary(manifest), ordinary(key), ordinary(age)
    validate_key(key)
    output.mkdir(mode=0o700)
    sync_dir(output.parent)
    marker = output / 'INCOMPLETO.json'
    stage = 'manifest'
    write_new(marker, json_bytes({'state': 'incomplete', 'stage': stage,
                                  'rule': 'Conservar archivos. No reutilizar este destino.'}))
    try:
        parts, encrypted = parse_manifest(read_json(manifest))
        ciphertext = output / NAME
        stage = 'verify_parts'
        combined = hashlib.sha256()
        with new_file(ciphertext) as dst:
            for part in parts:
                with open_read(manifest.parent / part['name']) as src:
                    transfer_checked(src, dst, part, combined)
            dst.flush()
            os.fsync(dst.fileno())
        need(combined.hexdigest() == encrypted['sha256'], 'SHA256 concatenado incorrecto.')
        verify_file(ciphertext, encrypted)
        sync_dir(output)
        stage = 'decrypt'
        plain = output / 'RESPALDO-PRIVADO.zip'
        need(not os.path.lexists(plain), 'El ZIP de salida ya existe.')
        code = subprocess.run([str(age), '-d', '-i', str(key), '-o', str(plain), str(ciphertext)],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, creationflags=FLAGS, check=False).returncode
        need(code == 0, 'age no pudo autenticar y descifrar el respaldo. Verificar clave y partes.')
        ordinary(plain)
        if os.name != 'nt':
            plain.chmod(0o600)
        with plain.open('r+b') as f:
            f.flush()
            os.fsync(f.fileno())
        sync_dir(output)
        stage = 'validate_index'
        with open_read(plain) as raw_zip, zipfile.ZipFile(raw_zip) as z:
            index_raw, files, aliases = validate_zip(z)
            base = output / 'archivos'
            base.mkdir(mode=0o700)
            sync_dir(output)
            write_new(base / INDEX, index_raw)
            stage = 'extract'
            for row in files:
                dest = target_file(base, row['path'])
                with z.open(row['path']) as src, new_file(dest) as dst:
                    transfer_checked(src, dst, row)
                    dst.flush()
                    os.fsync(dst.fileno())
                verify_file(dest, row)
                sync_dir(dest.parent)
        stage = 'copy_aliases'
        for row in aliases:
            dest = target_file(base, row['path'])
            with open_read(base / row['same_as']) as src, new_file(dest) as dst:
                transfer_checked(src, dst, row)
                dst.flush()
                os.fsync(dst.fileno())
            verify_file(dest, row)
            sync_dir(dest.parent)
        result = {'state': 'verified_files_only', 'files_verified': len(files),
                  'alias_copies_verified': len(aliases), 'encrypted_sha256': encrypted['sha256'],
                  'index_sha256': hashlib.sha256(index_raw).hexdigest(), 'file_fsync': True,
                  'directory_fsync': os.name != 'nt', 'device_restoration_tested': False}
        stage = 'finish'
        write_new(output / 'RECUPERACION-VERIFICADA.json', json_bytes(result))
        # Retain the initial receipt under a historical name, rather than delete data.
        marker.rename(output / 'OPERACION-INICIADA.json')
        sync_dir(output)
        return result
    except BaseException as exc:
        failure = {'state': 'incomplete', 'stage': stage,
                   'error': str(exc) if isinstance(exc, RecoveryError) else type(exc).__name__,
                   'rule': 'No asumir recuperación completa. Conservar archivos; usar otra salida nueva.'}
        try:
            # A separate receipt never overwrites a successful/failed data file.
            write_new(output / 'ERROR-RECUPERACION.json', json_bytes(failure))
            if not marker.exists():
                write_new(marker, json_bytes(failure))
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'key', 'age', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        result = recover(args.manifest, args.key, args.age, args.output)
    except (Exception, KeyboardInterrupt) as exc:
        detail = str(exc) if isinstance(exc, RecoveryError) else type(exc).__name__
        print('Recuperación incompleta: ' + detail +
              ' No se limpió ni reutilizó la salida.', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
