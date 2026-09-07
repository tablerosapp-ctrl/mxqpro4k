"""Comprueba enlaces locales, grafo, trazabilidad y artefactos sin tocar USB."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs'
data = json.loads((DOC / 'proyecto.json').read_text(encoding='utf8'))
errors = []
ids = {x['id'] for x in data['components']}
phases = {x['id'] for x in data['phases']}
assert len(ids) == len(data['components'])
for c in data['components']:
    for rel in c['files']:
        if not (ROOT / rel).is_file():
            errors.append('Archivo de componente ausente: ' + rel)
for e in data['edges']:
    if e['source'] not in ids or e['target'] not in ids:
        errors.append('Arista inválida: ' + str(e))
for q in data['requirements']:
    if not set(q['components']) <= ids:
        errors.append('Requisito apunta a componente inexistente: ' + q['id'])
    if q['id'] not in (DOC / 'ESPECIFICACION.md').read_text(encoding='utf8'):
        errors.append('Requisito sin especificación: ' + q['id'])
for p in data['phases']:
    if not set(p['depends_on']) <= phases or not set(p['components']) <= ids:
        errors.append('Etapa inválida: ' + p['id'])
def visit(n, pending, done):
    if n in pending:
        raise AssertionError('Ciclo en roadmap: ' + n)
    if n in done:
        return
    pending.add(n)
    for dep in next(x for x in data['phases'] if x['id'] == n)['depends_on']:
        visit(dep, pending, done)
    pending.remove(n)
    done.add(n)
for p in phases:
    visit(p, set(), set())

files = [ROOT / 'README.md', ROOT / 'AGENTS.md', ROOT / 'rom-simplificada/INSTALACION-USB.md', ROOT / 'rom-simplificada/instalador/README.md'] + list(DOC.glob('*.md')) + [DOC / 'historico/README.md']
count = 0
for p in files:
    text = p.read_text(encoding='utf8')
    for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        local = unquote(target.split('#')[0].strip('<>'))
        if not (p.parent / local).exists():
            errors.append(str(p.relative_to(ROOT)) + ' → ' + target)
        count += 1
page = (DOC / 'index.html').read_text(encoding='utf8')
embedded = re.search(r'<script id="project-data" type="application/json">(.*?)</script>', page, re.S)
assert embedded and json.loads(embedded[1]) == data
for placeholder in ['__PROJECT_DATA__', '__DELIVERY_LABEL__', '__STATE_LABEL__', '__DATE_LABEL__', '__NEXT_STEP_LABEL__']:
    if placeholder in page:
        errors.append('Plantilla sin resolver: ' + placeholder)
for target in re.findall(r'href="([^"]+)"', page):
    if '://' not in target and not target.startswith('#'):
        if not (DOC / unquote(target)).exists():
            errors.append('Enlace HTML ausente: ' + target)
        count += 1
artifacts = []
for a in data['artifacts']:
    path = ROOT / a['path']
    with path.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    if digest != a['sha256'] or path.stat().st_size != a['bytes']:
        errors.append('Entregable cambió: ' + a['name'])
    artifacts.append({'name': a['name'], 'sha256': digest, 'matched': digest == a['sha256']})
cleanup = json.loads((ROOT / data['cleanup_receipt']).read_text(encoding='utf-8-sig'))
assert cleanup['state'] == 'completed'
regenerated_caches = []
for row in cleanup['removed']:
    is_cache = Path(row['path']).name in {'.cache', '__pycache__'}
    if (ROOT / row['path']).exists() and is_cache:
        regenerated_caches.append(row['path'])
    elif (ROOT / row['path']).exists():
        errors.append('Retirado reapareció: ' + row['path'])
    for rel in row['retained']:
        if not (ROOT / rel).exists():
            errors.append('Fuente conservada ausente: ' + rel)
report = {'date_utc': datetime.now(timezone.utc).isoformat(), 'state': 'passed' if not errors else 'failed', 'links_checked': count,
          'component_paths_checked': sum(len(c['files']) for c in data['components']), 'graph_valid': True,
          'roadmap_acyclic': True, 'html_embedded_data_matches': True, 'artifacts': artifacts,
          'cleanup_bytes': cleanup['bytes_removed'], 'caches_regenerated_since_cleanup': regenerated_caches, 'errors': errors,
          'scope': 'Documentos vigentes y archivos locales; no prueba ejecución del TV ni enlaces web remotos.'}
(DOC / 'evidencia/documentacion-verificada.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
