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
for kind in ('components', 'phases'):
    positions = [(n['x'], n['y']) for n in data[kind]]
    if len(positions) != len(set(positions)):
        errors.append('Nodos superpuestos en el grafo: ' + kind)
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
files += [p for p in (ROOT / 'rom-simplificada/original-p291').rglob('*.md')
          if 'privado' not in p.relative_to(ROOT).parts]
files += list((ROOT / 'rom-simplificada/componentes/gestion-tvbase').glob('*.md'))
files += [DOC / 'hipotesis/HOME-P291.md']
files += [DOC / 'evidencia/REINICIOS-P291-SIN-USB.md']
files += [DOC / 'evidencia/RECONOCEDOR-USB-01.md']
files += list((ROOT / 'diagnostico/reconocedor-0.1').glob('*.md'))
files += list((ROOT / 'diagnostico/extractor-recovery-0.1').glob('*.md'))
files += list((ROOT / 'diagnostico/extractor-recovery-rk1').glob('*.md'))
files += list((ROOT / 'diagnostico/extractor-recovery-0.2').glob('*.md'))
files += list((ROOT / 'diagnostico/extractor-recovery-rk2').glob('*.md'))
files += list((ROOT / 'diagnostico/extractor-recovery-0.3').glob('*.md'))
files += list((ROOT / 'diagnostico/extractor-recovery-rk3').glob('*.md'))
files += [DOC / 'evidencia/ERROR-RK2-BACKUP-C.md', DOC / 'evidencia/EXTRACTOR-SD-03.md']
files += [DOC / 'evidencia/ERROR-RK1-DESTINO-USB.md', DOC / 'evidencia/EXTRACTOR-SD-02.md']
files += [DOC / 'evidencia' / name for name in ('RECOVERY-CNV8B-SD.md', 'HERRAMIENTA-SD-ROCKCHIP.md', 'SD-RK3229-C.md')]
files += [DOC / 'evidencia/RECOVERY-P271-ALCANCE.md', DOC / 'evidencia/EXTRACTOR-RECOVERY-01.md']
files += [DOC / 'evidencia/ROM-ORIGINAL-P291-020.md', DOC / 'evidencia/ENTRADA-ORIGINAL-P291-021.md', DOC / 'evidencia/PREPARACION-ENTRADA-P291-09.md', DOC / 'evidencia/ERROR-INSTALADOR-P291-021.md', DOC / 'evidencia/PARTICIONES-AMLOGIC-P291-022.md', DOC / 'evidencia/INSTALADOR-P291-022.md', DOC / 'evidencia/INSTALACION-FISICA-P291-022.md', ROOT / 'diagnostico/primer-tv-instalado-20260908/HALLAZGOS.md']
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
