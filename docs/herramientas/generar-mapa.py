"""Genera mapa, árbol e índice autónomo desde proyecto.json y archivos reales."""
from pathlib import Path
import json
import html
from collections import defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs'
data = json.loads((DOC / 'proyecto.json').read_text(encoding='utf8'))
derived = {'docs/index.html', 'docs/MAPA-ARCHIVOS.md', 'docs/ARBOL-ARCHIVOS.txt', 'docs/inventario.json', 'docs/evidencia/documentacion-verificada.json'}
private = 'rom-simplificada/claves-desarrollo'
private_captures = ('diagnostico/primer-tv-reportes-', 'diagnostico/primer-tv-evidencia-', 'diagnostico/primer-tv-complemento-', 'diagnostico/primer-tv-update-')
rows = []
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or p.is_symlink():
        continue
    rel = p.relative_to(ROOT).as_posix()
    if rel in derived or rel.startswith((private + '/', 'privado/', '.publicacion/')) or any(x in '/' + rel for x in ('/.git/', '/privado/', '/crudos/', '/originales/')):
        continue
    rows.append({'path': rel, 'bytes': p.stat().st_size})
stats = defaultdict(lambda: {'files': 0, 'bytes': 0})
for row in rows:
    group = row['path'].split('/')[0]
    stats[group]['files'] += 1
    stats[group]['bytes'] += row['bytes']
inventory = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'root': str(ROOT),
             'scope': 'Archivos reales salvo derivados documentales, .git y contenido/rutas interiores de claves privadas.',
             'protected_directories': [private], 'groups': dict(stats), 'files': rows}
(DOC / 'inventario.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

# El árbol legible agrupa dependencias y extracciones; el JSON mantiene rutas completas.
collapse = {'rom-simplificada/inspeccion/apks', 'rom-simplificada/inspeccion/metadatos',
            'rom-simplificada/compilacion', 'rom-simplificada/instalador/host-classes',
            'rom-simplificada/fuentes-webview', private,
            'actualizacion-chrome/chrome-138-splits'}
for p in (ROOT / 'tools').iterdir():
    if p.is_dir():
        collapse.add(p.relative_to(ROOT).as_posix())
for p in (ROOT / 'diagnostico').iterdir():
    if p.is_dir() and p.name.startswith('android-'):
        collapse.add(p.relative_to(ROOT).as_posix())
for p in (ROOT / 'preparacion-usb').iterdir():
    if p.is_dir():
        collapse.add(p.relative_to(ROOT).as_posix())
for p in (ROOT / 'rom-simplificada/instalador').iterdir():
    if p.is_dir() and (p.name.startswith('host-classes') or p.name.startswith(('fixture-evidencia-', 'fixture-entrada-'))):
        collapse.add(p.relative_to(ROOT).as_posix())
for p in (ROOT / 'rom-simplificada/trabajo').rglob('*'):
    if p.is_dir() and p.name in ('go-cache', 'go-mod-cache', 'openjdk'):
        collapse.add(p.relative_to(ROOT).as_posix())
tree = {}
fold = defaultdict(lambda: [0, 0])
for row in rows:
    rel = row['path']
    if rel.startswith(private_captures) and not (rel.endswith('/HALLAZGOS.md') or rel.endswith('/resumen-saneado.json') or rel.endswith('/evidencia-saneada.json') or rel.endswith('/certificados-ota.json') or rel.endswith('/ANALISIS.md')):
        continue  # Los originales no se enumeran en el árbol público.
    prefix = next((c for c in sorted(collapse) if rel.startswith(c + '/')), None)
    shown = prefix or rel
    if prefix:
        fold[prefix][0] += 1
        fold[prefix][1] += row['bytes']
    node = tree
    for part in shown.split('/'):
        node = node.setdefault(part, {})
node = tree
for part in private.split('/'):
    node = node.setdefault(part, {})
lines = ['TV Base · árbol del proyecto después de la limpieza',
         'Rutas relativas a la raíz. Dependencias/extracciones agrupadas; detalle en docs/inventario.json.',
         'Los documentos derivados index.html/MAPA/ARBOL/inventario y recibo de validación se omiten del inventario.', '', 'mxqpro4k/']
def walk(node, prefix='', path=''):
    keys = sorted(node, key=lambda k: (not bool(node[k]), k.lower()))
    for i, key in enumerate(keys):
        last = i == len(keys) - 1
        rel = path + '/' + key if path else key
        label = key + ('/' if node[key] or rel in collapse else '')
        if rel == private:
            label += ' [protegido; no se enumera su contenido]'
        elif rel in fold:
            n, b = fold[rel]
            label += f' [{n} archivos; {b / 1e6:.1f} MB; agrupado]'
        lines.append(prefix + ('└── ' if last else '├── ') + label)
        walk(node[key], prefix + ('    ' if last else '│   '), rel)
walk(tree)
(DOC / 'ARBOL-ARCHIVOS.txt').write_text('\n'.join(lines) + '\n', encoding='utf8')

md = ['# Mapa de componentes y archivos', '',
      'Generado por `herramientas/generar-mapa.py` desde [proyecto.json](proyecto.json). [Grafo visual](index.html) · [Árbol](ARBOL-ARCHIVOS.txt) · [Inventario completo](inventario.json).', '',
      'La flecha expresa la relación indicada, no que se haya completado la prueba de destino. Los componentes propuestos aún no tienen archivos de implementación.', '', '```mermaid', 'flowchart LR']
for c in data['components']:
    md.append(f'    {c["id"].replace("-", "_")}["{c["label"]} · {c["state"]}"]')
for e in data['edges']:
    md.append(f'    {e["source"].replace("-", "_")} -->|"{e["relation"]}"| {e["target"].replace("-", "_")}')
md.extend(['```', '', '## Archivos por componente', ''])
for c in data['components']:
    md += [f'### {c["id"]} · {c["label"]}', '', f'**{c["state"]}**. {c["description"]}', '', 'Requisitos: ' + ', '.join(c['requirements']) + '.', '']
    if c['files']:
        md += [f'- [{p}](../{p})' for p in c['files']]
    else:
        md += ['Implementación pendiente; especificación en [ESPECIFICACION](ESPECIFICACION.md) y propuestas en [ROADMAP](ROADMAP.md).']
    md += ['']
md += ['## Directorios y cuidado', '', '| Ruta | Función | Regla |', '| --- | --- | --- |',
       '| `analisis-rom/` | Fuente community e inspección | Conservar original y manifiesto |',
       '| `rom-simplificada/componentes/` | Fuente de APK propias | Versionar cambios y conservar firma |',
       '| `rom-simplificada/trabajo/` | RAW activos y recetas aplicadas | No son respaldo original del TV |',
       '| `rom-simplificada/instalador/` | ZIP, recovery externo y pruebas | Revisar versión antes de reconstruir |',
       '| `rom-simplificada/salida/` | Releases históricas 0.1.x | Conservar; no repetir su instalación |',
       '| `rom-simplificada/original-p291/` | Plataforma0.2.0 inmutable, selección y gestor | Fuentes y recibos versionados; privados excluidos |',
       '| `rom-simplificada/original-p291/instalacion-021/` | Instalador0.2.1: seis respaldos y migración de datos | Release inmutable; preparación PC no acredita instalación |',
       '| `rom-simplificada/original-p291/restauracion-021/` | Restaurador0.2.1 de cinco imágenes OEM | Conserva userdata; no restaura su respaldo ni ofrece rollback |',
       '| `rom-simplificada/original-p291/entrada-apk/` | AccesoUSB0.9 y contrato ENV/BCB | Uso del método específico pendiente de decisión; no reset automático |',
       '| `rom-simplificada/original-p291/empaquetado/salida/` | Releases0.2.0 históricas | Conservar; ioctl ARM32 corregido en0.2.1 |',
       '| `privado/TVBASE-respaldo-*/` | Adquisiciones originales P291 | Inmutables; no publicar ni confundir con userdata |',
       '| `preparacion-usb/` | Preparadores y recibos de operaciones | Usar identidad estable; no repetir por rutina |',
       '| `diagnostico/` | Evidencia de ambos equipos | No mezclar perfiles P291 y P271 |',
       '| `actualizacion-chrome/` | Chrome fuente y firmas | Conservar APK integrado y evidencia |',
       '| `images/` | Armbian histórico comprimido | No es ROM Android ni ruta activa |',
       '| `tools/` | Compiladores e inspección locales | Dependencias; no están instaladas en USB |',
       '| `docs/` | Especificación, estado, grafo y roadmap | Regenerar mapa al cambiar relaciones |',
       '| `rom-simplificada/claves-desarrollo/` | Firma local de APK | Privado; no mostrar contenidos |', '',
       '## Inventario de tamaño', '', '| Grupo | Archivos | GB decimales |', '| --- | ---: | ---: |']
md += [f'| {k} | {v["files"]} | {v["bytes"] / 1e9:.3f} |' for k, v in sorted(stats.items())]
md += ['', 'El inventario excluye derivados documentales y contenido de claves; los tamaños son de archivos, no bloques físicos ocupados. Los temporales retirados se detallan en [LIMPIEZA](LIMPIEZA.md).', '']
(DOC / 'MAPA-ARCHIVOS.md').write_text('\n'.join(md), encoding='utf8')
template = (DOC / 'herramientas/mapa-template.html').read_text(encoding='utf8')
embedded = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
page = template.replace('__PROJECT_DATA__', embedded)
for key, placeholder in [('delivery_label', '__DELIVERY_LABEL__'), ('state', '__STATE_LABEL__'), ('date_label', '__DATE_LABEL__'), ('next_step_label', '__NEXT_STEP_LABEL__')]:
    page = page.replace(placeholder, html.escape(data.get(key, data['state'])))
(DOC / 'index.html').write_text(page, encoding='utf8')
print(json.dumps({'components': len(data['components']), 'requirements': len(data['requirements']), 'phases': len(data['phases']), 'inventoried_files': len(rows), 'tree_lines': len(lines)}, ensure_ascii=False))
