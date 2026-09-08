"""Publica exclusivamente el respaldo age ya verificado, como Release pública.

La clave y los originales nunca son entradas de carga. --check valida solamente
archivos locales; sin esa opción se publica o retoma la Release fija. Un fallo
conserva el borrador y sus assets: no hay reemplazos, borrados ni reintentos
automáticos. Cada ejecución de publicación deja un recibo privado independiente.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import runpy
import ssl
import stat
import sys
import time
from urllib.parse import quote
import uuid


ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / 'privado/backup-github-20260908'
ASSET_DIR = PRIVATE / 'release-assets'
OWNER = 'tablerosapp-ctrl'
REPO = 'mxqpro4k'
REPO_PATH = '/repos/' + OWNER + '/' + REPO
TAG = 'respaldo-p291-20260908'
TITLE = 'Respaldo cifrado P291 · 8 septiembre 2026'
PART_PREFIX = 'TVBASE-P291-RESPALDO-20260908.zip.age.part'
MANIFEST = 'RESPALDO-CIFRADO.json'
MAX_ASSET = 1024 ** 3  # Cada archivo debe ser estrictamente menor que 1 GiB.
MAX_JSON = 2 * 1024 ** 2
CHUNK = 1024 ** 2
TIMEOUT = 60
HEX256 = re.compile(r'[0-9a-f]{64}')
PART_NAME = re.compile(re.escape(PART_PREFIX) + r'([0-9]{3})')
RELEASE_URL = 'https://github.com/' + OWNER + '/' + REPO + '/releases/tag/' + TAG
BODY = (
    'Respaldo cifrado de las particiones originales del primer P291 y de '
    'userdata. No es firmware instalable ni una restauración ensayada. '
    'La clave privada se conserva fuera de GitHub.\n\n'
    '[Contenido, verificación y límites del respaldo]('
    'https://github.com/' + OWNER + '/' + REPO + '/blob/main/docs/RESPALDO-GITHUB.md).'
)


class PublicationError(RuntimeError):
    """Mensaje controlado: nunca contiene respuestas HTTP ni credenciales."""


def require(condition, message):
    if not condition:
        raise PublicationError(message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def ordinary(path: Path, *, directory=False):
    """Rechaza symlinks, junctions/reparse points y hardlinks de archivos."""
    require(path.is_absolute(), 'Se requiere una ruta absoluta local.')
    require('..' not in path.parts, 'No se admiten componentes .. en rutas.')
    require(path.is_relative_to(ROOT), 'Ruta fuera del proyecto.')
    current = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            current /= part
        try:
            info = current.lstat()
        except OSError:
            raise PublicationError('Falta una ruta local requerida.') from None
        require(not stat.S_ISLNK(info.st_mode) and not (
            getattr(info, 'st_file_attributes', 0) & 0x400),
            'No se admiten enlaces ni puntos de reanálisis.')
        want_dir = current != path or directory
        require(stat.S_ISDIR(info.st_mode) if want_dir else stat.S_ISREG(info.st_mode),
                'Tipo de archivo o directorio inesperado.')
        if not want_dir:
            require(info.st_nlink == 1, 'No se admiten archivos con enlaces adicionales.')
    require(path.resolve(strict=True) == path, 'Ruta canónica diferente de la autorizada.')
    return info


def fingerprint(info):
    # En el Python de esta PC, lstat y fstat devuelven semánticas distintas de
    # ctime en Windows. Identidad, tamaño, mtime y enlaces sí son comparables;
    # la integridad de los bytes se comprueba además con SHA256.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink)


def checked_open(path):
    info = ordinary(path)
    try:
        stream = path.open('rb')
    except OSError:
        raise PublicationError('No se pudo abrir un archivo requerido.') from None
    if fingerprint(info) != fingerprint(os.fstat(stream.fileno())):
        stream.close()
        raise PublicationError('El archivo cambió al abrirlo.')
    return stream, info


def stable(stream, path, info):
    require(fingerprint(os.fstat(stream.fileno())) == fingerprint(info)
            and fingerprint(ordinary(path)) == fingerprint(info),
            'Un archivo local cambió durante su lectura.')


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'JSON contiene una clave duplicada.')
        result[key] = value
    return result


def parse_json(raw):
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=no_duplicate_keys)
    except (ValueError, UnicodeError):
        raise PublicationError('JSON inválido.') from None


def read_json(path):
    stream, info = checked_open(path)
    with stream:
        require(0 < info.st_size <= MAX_JSON, 'Tamaño JSON fuera del límite.')
        raw = stream.read(MAX_JSON + 1)
        require(len(raw) == info.st_size, 'Lectura JSON incompleta.')
        stable(stream, path, info)
    return parse_json(raw), hashlib.sha256(raw).hexdigest()


def hash_file(path):
    stream, info = checked_open(path)
    digest = hashlib.sha256()
    total = 0
    last = time.monotonic()
    with stream:
        while block := stream.read(CHUNK):
            digest.update(block)
            total += len(block)
            if time.monotonic() - last >= 15:
                print('Verificando ' + path.name + ': ' + str(total) + ' bytes', flush=True)
                last = time.monotonic()
        require(total == info.st_size, 'Lectura binaria incompleta.')
        stable(stream, path, info)
    return total, digest.hexdigest(), fingerprint(info)


def asset_names(assets):
    require(isinstance(assets, list) and 2 <= len(assets) <= 100,
            'Se requiere un manifiesto y entre 1 y 99 partes cifradas.')
    names = []
    numbers = []
    for asset in assets:
        require(isinstance(asset, dict), 'Entrada de asset inválida.')
        name = asset.get('name')
        require(isinstance(name, str), 'Nombre de asset inválido.')
        match = PART_NAME.fullmatch(name)
        require(name == MANIFEST or match is not None, 'Nombre no permitido para publicación.')
        if match:
            numbers.append(int(match.group(1)))
        require(type(asset.get('bytes')) is int and 0 < asset['bytes'] < MAX_ASSET,
                'Un asset no cumple el límite de tamaño menor que 1 GiB.')
        require(isinstance(asset.get('sha256'), str) and HEX256.fullmatch(asset['sha256']),
                'SHA256 de asset inválido.')
        names.append(name)
    require(len(set(names)) == len(names) and names.count(MANIFEST) == 1,
            'Nombres repetidos o manifiesto ausente.')
    require(sorted(numbers) == list(range(1, len(numbers) + 1)),
            'Las partes deben ser consecutivas desde part001.')
    return set(names)


def load_inputs(receipt_path):
    path = Path(receipt_path)
    if not path.is_absolute():
        path = ROOT / path
    require(path == PRIVATE / 'PREPARADO.json', 'Recibo fuera de la ubicación autorizada.')
    receipt, receipt_sha = read_json(path)
    require(isinstance(receipt, dict) and receipt.get('state') == 'verified'
            and receipt.get('encryption') == 'age-v1-X25519'
            and receipt.get('roundtrip_verified') is True,
            'Falta un respaldo age con descifrado íntegro verificado.')
    names = asset_names(receipt.get('assets'))
    require(isinstance(receipt.get('public_manifest'), dict), 'Falta el manifiesto público.')
    ordinary(ASSET_DIR, directory=True)
    assets = []
    for entry in receipt['assets']:
        raw_path = entry.get('path')
        require(isinstance(raw_path, str), 'Ruta de asset inválida.')
        local = Path(raw_path)
        if not local.is_absolute():
            local = ROOT / local
        require(local == ASSET_DIR / entry['name'], 'Asset fuera del directorio autorizado.')
        count, digest, snapshot = hash_file(local)
        require(count == entry['bytes'] and digest == entry['sha256'],
                'Tamaño o SHA256 local no coincide: ' + entry['name'])
        assets.append(dict(entry, local_path=local, snapshot=snapshot))
    manifest, _ = read_json(ASSET_DIR / MANIFEST)
    require(manifest == receipt['public_manifest'], 'El manifiesto público difiere del recibido.')
    public_bytes = json.dumps(manifest, ensure_ascii=False).encode('utf-8')
    require(not re.search(rb'AGE-SECRET-KEY-|PRIVATE KEY|github_pat_|gh[pousr]_[A-Za-z0-9]{30,}',
                          public_bytes), 'Patrón de clave privada o token en manifiesto público.')
    # La cabecera de age pertenece únicamente a la primera parte, nunca a la clave.
    first = next(x for x in assets if x['name'] == PART_PREFIX + '001')
    stream, info = checked_open(first['local_path'])
    with stream:
        header = b'age-encryption.org/v1\n'
        require(stream.read(len(header)) == header, 'Cabecera binaria age v1 ausente.')
        stable(stream, first['local_path'], info)
    state, state_sha = read_json(ROOT / '.publicacion/estado.json')
    require(isinstance(state, dict) and state.get('pushed') is True
            and state.get('owner') == OWNER and state.get('repo') == REPO
            and isinstance(state.get('public_head'), str)
            and re.fullmatch(r'[0-9a-f]{40}', state['public_head'])
            and state.get('remote_head') == state['public_head'],
            'El espejo público no tiene un HEAD publicado y verificado.')
    return dict(receipt_path=path, receipt_sha256=receipt_sha, assets=assets,
                names=names, public_head=state['public_head'], state_sha256=state_sha)


def request_json(host, method, path, token=None, payload=None, missing_ok=False):
    require(host == 'api.github.com' and path.startswith('/'), 'Destino HTTP no autorizado.')
    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'TVBase-encrypted-backup', 'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    if data is not None:
        headers['Content-Type'] = 'application/json'
    connection = http.client.HTTPSConnection(host, timeout=TIMEOUT, context=ssl.create_default_context())
    try:
        connection.request(method, path, body=data, headers=headers)
        response = connection.getresponse()
        if response.status == 404 and missing_ok:
            return None
        require(200 <= response.status < 300,
                'GitHub respondió HTTP ' + str(response.status) + ' en ' + method + '.')
        raw = response.read(MAX_JSON + 1)
        require(len(raw) <= MAX_JSON, 'Respuesta JSON demasiado grande.')
        return parse_json(raw)
    finally:
        connection.close()


def api(method, path, token=None, payload=None, missing_ok=False):
    return request_json('api.github.com', method, path, token, payload, missing_ok)


def credential():
    # Reutiliza el acceso al gestor de credenciales del publicador del espejo.
    # Su resultado se mantiene únicamente en memoria; se ocultan incluso errores.
    helper = runpy.run_path(str(ROOT / 'docs/herramientas/publicar-github.py'))
    try:
        raw = helper['git']('credential', 'fill', data=b'protocol=https\nhost=github.com\n\n')
        fields = dict(line.split('=', 1) for line in raw.decode('utf-8').splitlines() if '=' in line)
        token = fields.get('password')
        require(isinstance(token, str) and bool(token) and '\n' not in token and '\r' not in token,
                'No hay credencial GitHub utilizable.')
        return token
    except Exception:
        raise PublicationError('No se pudo obtener la credencial GitHub autorizada.') from None


def assert_repository(token, public_head):
    account = api('GET', '/user', token)
    require(isinstance(account, dict) and account.get('login') == OWNER,
            'La cuenta autenticada no es la dueña autorizada.')
    repo = api('GET', REPO_PATH, token)
    require(isinstance(repo, dict) and repo.get('private') is False
            and repo.get('full_name') == OWNER + '/' + REPO
            and repo.get('owner', {}).get('login') == OWNER,
            'El repositorio no es el público autorizado.')
    anonymous = api('GET', REPO_PATH)
    require(isinstance(anonymous, dict) and anonymous.get('private') is False
            and anonymous.get('full_name') == OWNER + '/' + REPO,
            'El repositorio no se puede comprobar como público sin credenciales.')
    head = api('GET', REPO_PATH + '/git/ref/heads/main')
    require(isinstance(head, dict) and head.get('object', {}).get('sha') == public_head,
            'El HEAD remoto de main difiere del espejo publicado.')


def release_metadata(release, public_head, *, published=None):
    require(isinstance(release, dict) and type(release.get('id')) is int and release['id'] > 0,
            'Identificador de Release inválido.')
    require(release.get('tag_name') == TAG and release.get('target_commitish') == public_head
            and release.get('name') == TITLE and release.get('body') == BODY
            and release.get('prerelease') is True
            and type(release.get('draft')) is bool,
            'La Release existente no corresponde exactamente a este respaldo.')
    # GitHub puede asignar una URL provisional a un borrador sin tag creado.
    # No se usa esa URL para cargar ni para redirigir credenciales.
    if not release['draft']:
        require(release.get('html_url') == RELEASE_URL, 'URL pública de Release inesperada.')
    if published is not None:
        require(release['draft'] == (not published), 'Estado de publicación inesperado.')


def find_release(token):
    # El listado autenticado incluye borradores. No crear un duplicado si la
    # búsqueda queda incompleta: máximo explícito de 1000 Releases.
    found = []
    for page in range(1, 11):
        rows = api('GET', REPO_PATH + '/releases?per_page=100&page=' + str(page), token)
        require(isinstance(rows, list), 'Listado de Releases inválido.')
        found.extend(row for row in rows if isinstance(row, dict) and row.get('tag_name') == TAG)
        if len(rows) < 100:
            require(len(found) <= 1, 'Hay más de una Release con la etiqueta prevista.')
            return found[0] if found else None
    raise PublicationError('No se pudo completar el listado de Releases; no se crea otra.')


def list_assets(release_id, token=None):
    rows = []
    for page in (1, 2):
        batch = api('GET', REPO_PATH + '/releases/' + str(release_id)
                    + '/assets?per_page=100&page=' + str(page), token)
        require(isinstance(batch, list), 'Listado de assets inválido.')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise PublicationError('Demasiados assets en la Release prevista.')


def check_assets(rows, expected, *, complete=False, draft=False):
    require(isinstance(rows, list), 'Listado remoto inválido.')
    local = {x['name']: x for x in expected}
    seen = {}
    for row in rows:
        require(isinstance(row, dict), 'Asset remoto inválido.')
        name = row.get('name')
        require(isinstance(name, str) and name in local and name not in seen,
                'Asset remoto ajeno o duplicado; no se modifica la Release.')
        asset = local[name]
        require(type(row.get('id')) is int and row['id'] > 0
                and row.get('state') == 'uploaded' and type(row.get('size')) is int
                and row['size'] == asset['bytes']
                and row.get('digest') == 'sha256:' + asset['sha256'],
                'Asset remoto incompleto o diferente; no se reemplaza: ' + name)
        expected_url = 'https://github.com/' + OWNER + '/' + REPO + '/releases/download/' + TAG + '/' + name
        download_url = row.get('browser_download_url')
        if draft:
            # Las URL provisionales de borrador no se usan para ninguna petición.
            draft_pattern = (re.escape('https://github.com/' + OWNER + '/' + REPO)
                             + r'/releases/download/[^/?#]+/' + re.escape(name))
            require(isinstance(download_url, str) and re.fullmatch(draft_pattern, download_url),
                    'URL provisional de asset fuera del repositorio autorizado.')
        else:
            require(download_url == expected_url, 'URL de descarga remota inesperada.')
        seen[name] = dict(name=name, id=row['id'], bytes=row['size'], sha256=asset['sha256'],
                          url=row['browser_download_url'])
    if complete:
        require(set(seen) == set(local), 'La Release no contiene todos los assets verificados.')
    return seen


def upload_asset(release_id, asset, token):
    path = asset['local_path']
    stream, info = checked_open(path)
    connection = http.client.HTTPSConnection('uploads.github.com', timeout=TIMEOUT,
                                              context=ssl.create_default_context())
    try:
        require(fingerprint(info) == asset['snapshot'], 'El asset cambió después de verificarlo.')
        route = REPO_PATH + '/releases/' + str(release_id) + '/assets?name=' + quote(asset['name'], safe='')
        connection.putrequest('POST', route)
        connection.putheader('Authorization', 'Bearer ' + token)
        connection.putheader('Accept', 'application/vnd.github+json')
        connection.putheader('User-Agent', 'TVBase-encrypted-backup')
        connection.putheader('X-GitHub-Api-Version', '2022-11-28')
        connection.putheader('Content-Type', 'application/json' if asset['name'] == MANIFEST else 'application/octet-stream')
        connection.putheader('Content-Length', str(asset['bytes']))
        connection.endheaders()
        digest = hashlib.sha256()
        sent = 0
        last = time.monotonic()
        while sent < asset['bytes']:
            block = stream.read(min(CHUNK, asset['bytes'] - sent))
            require(bool(block), 'El asset se truncó durante la carga.')
            connection.send(block)
            digest.update(block)
            sent += len(block)
            if time.monotonic() - last >= 15:
                print('Subiendo ' + asset['name'] + ': ' + str(sent) + '/' + str(asset['bytes']), flush=True)
                last = time.monotonic()
        require(not stream.read(1) and digest.hexdigest() == asset['sha256'],
                'El contenido cambió durante la carga; se conserva el borrador.')
        stable(stream, path, info)
        response = connection.getresponse()
        require(response.status == 201, 'La carga respondió HTTP ' + str(response.status) + '.')
        raw = response.read(MAX_JSON + 1)
        require(len(raw) <= MAX_JSON, 'Respuesta de carga demasiado grande.')
        uploaded = parse_json(raw)
        check_assets([uploaded], [asset], complete=True, draft=True)
        return uploaded
    finally:
        stream.close()
        connection.close()


def write_receipt(result):
    ordinary(PRIVATE, directory=True)
    name = 'PUBLICACION-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
    temporary = PRIVATE / (name + '.parcial')
    destination = PRIVATE / (name + '.json')
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with temporary.open('xb') as output:
        require(output.write(raw) == len(raw), 'Recibo escrito parcialmente.')
        output.flush()
        os.fsync(output.fileno())
    # El enlace crea el destino de forma atómica y falla si ya existía. No
    # sobrescribe PREPARADO ni otro recibo; al retirar el temporal queda un link.
    os.link(temporary, destination)
    temporary.unlink()
    return destination


def publish(inputs, result):
    result.update(stage='authentication', public_head=inputs['public_head'],
                  prepared_receipt_sha256=inputs['receipt_sha256'],
                  publication_state_sha256=inputs['state_sha256'])
    token = credential()
    assert_repository(token, inputs['public_head'])
    result['stage'] = 'draft'
    release = find_release(token)
    if release is None:
        existing_tag = api('GET', REPO_PATH + '/git/ref/tags/' + TAG, token, missing_ok=True)
        if existing_tag is not None:
            require(isinstance(existing_tag, dict) and existing_tag.get('object', {}).get('type') == 'commit'
                    and existing_tag['object'].get('sha') == inputs['public_head'],
                    'La etiqueta existente apunta a otro commit; no se crea una Release.')
        release = api('POST', REPO_PATH + '/releases', token, {
            'tag_name': TAG, 'target_commitish': inputs['public_head'], 'name': TITLE,
            'body': BODY, 'draft': True, 'prerelease': True, 'make_latest': 'false'})
    release_metadata(release, inputs['public_head'])
    result.update(release_id=release['id'], url=RELEASE_URL)
    uploaded = check_assets(list_assets(release['id'], token), inputs['assets'],
                            complete=not release['draft'], draft=release['draft'])
    result['stage'] = 'upload'
    for asset in sorted(inputs['assets'], key=lambda item: item['name']):
        if asset['name'] in uploaded:
            print('Ya verificado en GitHub: ' + asset['name'], flush=True)
            continue
        require(release['draft'] is True, 'No se agregan archivos a una Release publicada.')
        upload_asset(release['id'], asset, token)
    # Lista completa independiente de las respuestas individuales de carga.
    result['stage'] = 'verify_draft'
    check_assets(list_assets(release['id'], token), inputs['assets'], complete=True, draft=release['draft'])
    assert_repository(token, inputs['public_head'])
    tag = api('GET', REPO_PATH + '/git/ref/tags/' + TAG, token, missing_ok=True)
    if tag is not None:
        require(tag.get('object', {}).get('type') == 'commit'
                and tag['object'].get('sha') == inputs['public_head'],
                'La etiqueta existente apunta a otro commit; no se modifica.')
    result['stage'] = 'publish'
    if release['draft']:
        result['publication_requested'] = True
        release = api('PATCH', REPO_PATH + '/releases/' + str(release['id']), token,
                      {'draft': False, 'prerelease': True, 'make_latest': 'false'})
        release_metadata(release, inputs['public_head'], published=True)
    result['stage'] = 'anonymous_verification'
    public_release = api('GET', REPO_PATH + '/releases/tags/' + TAG)
    release_metadata(public_release, inputs['public_head'], published=True)
    require(public_release['id'] == release['id'], 'La Release pública tiene otra identidad.')
    public_assets = check_assets(list_assets(release['id']), inputs['assets'], complete=True)
    tag = api('GET', REPO_PATH + '/git/ref/tags/' + TAG)
    require(isinstance(tag, dict) and tag.get('object', {}).get('type') == 'commit'
            and tag['object'].get('sha') == inputs['public_head'], 'Etiqueta pública distinta del commit previsto.')
    result.update(state='published_verified', stage='complete', anonymous_public_verified=True,
                  assets=[public_assets[name] for name in sorted(public_assets)],
                  verification='GitHub asset digest SHA256 y tamaño consultados sin autenticación; '
                               'no se descargaron de nuevo todos los bytes.',
                  completed_at=utc_now())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', required=True, help='Recibo privado PREPARADO.json verificado.')
    parser.add_argument('--check', action='store_true', help='Solo comprobar archivos locales; sin red ni autenticación.')
    args = parser.parse_args()
    result = dict(started_at=utc_now(), state='unverified', stage='local_validation',
                  repository=OWNER + '/' + REPO, tag=TAG, publication_requested=False)
    receipt_out = None
    code = 0
    try:
        inputs = load_inputs(args.receipt)
        if args.check:
            print(json.dumps({'state': 'local_verified', 'assets': len(inputs['assets']),
                              'bytes': sum(x['bytes'] for x in inputs['assets']),
                              'public_head': inputs['public_head'], 'network_used': False}))
            return 0
        publish(inputs, result)
    except Exception as error:
        code = 1
        result.update(error=str(error) if isinstance(error, PublicationError)
                      else 'Fallo local o de transporte (' + type(error).__name__ + ').',
                      stopped_at=utc_now())
    if not args.check:
        try:
            receipt_out = write_receipt(result)
        except Exception:
            code = 1
            print('No se pudo guardar el recibo privado. Consultar el estado remoto antes de repetir.', file=sys.stderr)
    print(json.dumps({'state': result['state'], 'stage': result['stage'],
                      'url': result.get('url'), 'private_receipt_written': receipt_out is not None,
                      'error': result.get('error')}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
