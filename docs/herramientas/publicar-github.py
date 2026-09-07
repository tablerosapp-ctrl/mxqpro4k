"""Publica un espejo de main con identificadores locales anonimizados.

No modifica el Git operativo ni sus artefactos. Configuración en privado/.
Los tokens se obtienen del gestor de credenciales y nunca se guardan o imprimen.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.publicacion'
MIRROR = WORK / 'repositorio'
CONFIG = ROOT / 'privado/publicacion-redacciones.json'
GIT = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
ENV = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
FLAGS = 0x08000000 if os.name == 'nt' else 0
SECRET = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}')


def git(*args, cwd=ROOT, data=None):
    p = subprocess.run([str(GIT), *args], cwd=cwd, input=data, capture_output=True,
                       env=ENV, creationflags=FLAGS, timeout=120)
    if p.returncode:
        raise RuntimeError('Git falló: ' + ' '.join(args[:3]) + ': ' + p.stderr.decode('utf8', 'replace')[-1200:])
    return p.stdout


def load_config():
    d = json.loads(CONFIG.read_text(encoding='utf8'))
    assert re.fullmatch(r'[A-Za-z0-9_.-]+', d['owner'])
    assert re.fullmatch(r'[A-Za-z0-9_.-]+', d['repo'])
    assert d['redactions'] and all(k and v and k != v for k, v in d['redactions'].items())
    return d


def scrub(raw, config):
    for old, new in config['redactions'].items():
        raw = raw.replace(old.encode(), new.encode())
    # Slash and JSON-escaped Windows paths; operational files stay unchanged.
    raw = re.sub(rb'(Users[\\/]+)' + re.escape(config['local_user'].encode()) + rb'(?=[\\/])',
                 rb'\1usuario-local', raw)
    return raw


def prepare(config):
    assert not git('status', '--porcelain'), 'Commit local pendiente; no publicar archivos sin registrar.'
    assert MIRROR.resolve().is_relative_to(ROOT.resolve())
    source_head = git('rev-parse', 'main').decode().strip()
    raw = git('fast-export', '--signed-tags=strip', 'refs/heads/main')
    incoming, outgoing = io.BytesIO(raw), io.BytesIO()
    changed = payloads = 0
    while line := incoming.readline():
        if line.startswith(b'data '):
            count = int(line[5:]); body = incoming.read(count)
            assert len(body) == count and b'\0' not in body, 'Binario inesperado en historial publicable.'
            assert not SECRET.search(body), 'Patrón de secreto en historial: revisar localmente antes de publicar.'
            clean = scrub(body, config)
            changed += clean != body; payloads += 1
            outgoing.write(b'data ' + str(len(clean)).encode() + b'\n' + clean)
        else:
            outgoing.write(scrub(line, config))
    stream = outgoing.getvalue()
    assert all(x.encode() not in stream for x in config['redactions']), 'Identificador privado restante.'
    WORK.mkdir(exist_ok=True)
    if not (MIRROR / '.git').exists():
        MIRROR.mkdir(exist_ok=True)
        git('init', '--initial-branch=main', str(MIRROR))
    git('fast-import', '--quiet', cwd=MIRROR, data=stream)
    # Update only this generated worktree. No reset/clean of the operator repo.
    git('read-tree', '--reset', '-u', 'main', cwd=MIRROR)
    public_head = git('rev-parse', 'main', cwd=MIRROR).decode().strip()
    source_commits = git('rev-list', '--reverse', 'main').decode().splitlines()
    public_commits = git('rev-list', '--reverse', 'main', cwd=MIRROR).decode().splitlines()
    assert len(source_commits) == len(public_commits), 'Se perdió historia al exportar.'
    audit(config)
    state = {'prepared_at': datetime.now(timezone.utc).isoformat(), 'source_head': source_head,
             'public_head': public_head, 'owner': config['owner'], 'repo': config['repo'],
             'payloads_checked': payloads, 'payloads_anonymized': changed,
             'redaction_config_sha256': hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
             'commit_map': dict(zip(source_commits, public_commits)), 'pushed': False}
    (WORK / 'estado.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf8')
    return state


def audit(config):
    rows = git('rev-list', '--objects', 'main', cwd=MIRROR).decode().splitlines()
    for row in rows:
        oid, _, name = row.partition(' ')
        kind = git('cat-file', '-t', oid, cwd=MIRROR).strip()
        if kind != b'blob':
            continue
        assert not re.search(r'\.(?:apk|img|zip|jks|pk8|pem|key|exe|dll|bin|dex|class|png)$', name, re.I), 'Binario/clave/foto en historial: ' + name
        assert not name.startswith(('privado/', '.publicacion/')) and 'claves-desarrollo/' not in name
        body = git('cat-file', 'blob', oid, cwd=MIRROR)
        assert b'\0' not in body and not SECRET.search(body), 'Contenido no publicable: ' + name
        assert all(x.encode() not in body for x in config['redactions']), 'Identificador pendiente: ' + name


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def api(path, token=None, payload=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'TVBase-publication'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode()
    req = urllib.request.Request('https://api.github.com' + path, data=data, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise RuntimeError('GitHub respondió HTTP ' + str(e.code) + ' en ' + path) from None


def publish(config):
    state = json.loads((WORK / 'estado.json').read_text(encoding='utf8'))
    assert not git('status', '--porcelain'), 'Cambios locales sin commit.'
    assert state['source_head'] == git('rev-parse', 'main').decode().strip(), 'Preparación desactualizada.'
    assert state['public_head'] == git('rev-parse', 'main', cwd=MIRROR).decode().strip()
    assert state['redaction_config_sha256'] == hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    assert not git('status', '--porcelain', cwd=MIRROR), 'Espejo generado con cambios ajenos.'
    audit(config)
    credential = git('credential', 'fill', data=b'protocol=https\nhost=github.com\n\n')
    fields = dict(x.split('=', 1) for x in credential.decode().splitlines() if '=' in x)
    token = fields.get('password'); assert token, 'Falta autenticación GitHub.'
    assert api('/user', token)['login'] == config['owner'], 'Cuenta distinta de la autorizada.'
    path = '/repos/' + config['owner'] + '/' + config['repo']
    repo = api(path, token)
    if repo is None:
        repo = api('/user/repos', token, {'name': config['repo'], 'private': False,
                   'description': 'TV Base: Android interno para P291, evidencia, fuentes y revisión colaborativa.',
                   'auto_init': False, 'has_issues': True})
        state['created_repository_id'] = repo['id']
    assert repo['private'] is False and repo['owner']['login'] == config['owner']
    url = 'https://github.com/' + config['owner'] + '/' + config['repo'] + '.git'
    remotes = git('remote', cwd=MIRROR).decode().splitlines()
    if 'origin' not in remotes:
        git('remote', 'add', 'origin', url, cwd=MIRROR)
    assert git('remote', 'get-url', 'origin', cwd=MIRROR).decode().strip() == url
    heads = git('ls-remote', '--heads', 'origin', cwd=MIRROR).decode().splitlines()
    assert all(x.endswith('\trefs/heads/main') for x in heads), 'Ramas remotas inesperadas: revisar antes de continuar.'
    if heads:
        git('fetch', 'origin', 'main', cwd=MIRROR)
        git('merge-base', '--is-ancestor', 'FETCH_HEAD', 'main', cwd=MIRROR)
    git('push', '--set-upstream', 'origin', 'main:main', cwd=MIRROR)
    remote_sha = git('ls-remote', 'origin', 'refs/heads/main', cwd=MIRROR).decode().split()[0]
    assert remote_sha == state['public_head'], 'SHA remoto diferente.'
    # Anonymous API proves it is actually public, independently of our token.
    public_repo = api(path)
    assert public_repo and public_repo['private'] is False
    state.update(pushed=True, verified_at=datetime.now(timezone.utc).isoformat(),
                 url=public_repo['html_url'], remote_head=remote_sha,
                 anonymous_public_verified=True)
    (WORK / 'estado.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf8')
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    assert args.prepare != args.publish, 'Elegir solamente --prepare o --publish.'
    config = load_config()
    result = prepare(config) if args.prepare else publish(config)
    print(json.dumps({k: v for k, v in result.items() if k != 'commit_map'}, indent=2))
