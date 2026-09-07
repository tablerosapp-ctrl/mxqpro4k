"""Audita temporales concretos; no borra ni accede a discos externos."""
from pathlib import Path
import gzip
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidencia'
OUT.mkdir(parents=True, exist_ok=True)

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

rows = []

def item(rel, reason, retained):
    p = ROOT / rel
    if not p.exists():
        return
    assert p.resolve().is_relative_to(ROOT) and not p.is_symlink()
    files = sorted(x for x in p.rglob('*') if x.is_file()) if p.is_dir() else [p]
    assert all(x.resolve().is_relative_to(ROOT) and not x.is_symlink() for x in files)
    rows.append({'path': rel, 'bytes': sum(x.stat().st_size for x in files),
                 'files': len(files), 'sha256': sha(p) if p.is_file() else None,
                 'reason': reason, 'retained': retained})

meta = json.loads((ROOT / 'preparacion-usb/imagen.json').read_text(encoding='utf-8-sig'))
raw = ROOT / 'images' / meta['archivo']
gz = raw.with_suffix('.img.gz')
if raw.exists():
    assert sha(gz) == meta['sha256_gz_publicado_y_verificado']
    assert sha(raw) == meta['sha256_img_calculado']
    with gzip.open(gz, 'rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == meta['sha256_img_calculado']
    item(raw.relative_to(ROOT).as_posix(), 'Imagen Armbian expandida regenerable; gzip descomprimido y hash comprobados.', [gz.relative_to(ROOT).as_posix(), 'preparacion-usb/imagen.json'])

for unsigned, signed in [('unsigned.zip', 'TVBASE-P291-A9-0.1-RECOVERY.zip'), ('unsigned-0.1.1.zip', 'TVBASE-P291-A9-0.1.1-RECOVERY.zip')]:
    p = ROOT / 'rom-simplificada/instalador' / unsigned
    target = ROOT / 'rom-simplificada/salida' / signed
    if p.exists():
        # La firma agrega un comentario ZIP y cambia solo sus ultimos dos bytes.
        left = p.stat().st_size - 2
        with p.open('rb') as a, target.open('rb') as b:
            while left:
                n = min(left, 4 << 20)
                assert a.read(n) == b.read(n)
                left -= n
        item(p.relative_to(ROOT).as_posix(), 'Intermedio sin firma; contenido comparado byte a byte con el ZIP firmado conservado.', [target.relative_to(ROOT).as_posix(), 'rom-simplificada/instalador/empaquetar.py'])

manifest = json.loads((ROOT / 'rom-simplificada/instalador/manifest-0.1.1.json').read_text())
for name in ['product', 'odm', 'boot']:
    rel = 'rom-simplificada/instalador/payload/' + name + '.img'
    p = ROOT / rel
    if p.exists():
        expected = next(x for x in manifest['images'] if x['name'] == name)
        assert sha(p) == expected['sha256'] and p.stat().st_size == expected['size']
        item(rel, 'Extraccion intermedia regenerada por empaquetar.py; coincide con manifiesto de ROM firmada.', ['analisis-rom/candidato-android9.img', 'rom-simplificada/salida/TVBASE-P291-A9-0.1.1-RECOVERY.zip'])

item('rom-simplificada/trabajo/fallo-debugfs-ruta-absoluta/system.raw.img', 'Copia defectuosa de trabajo descartada antes de empaquetar; conservar causa, comandos y fsck.', ['rom-simplificada/trabajo/fallo-debugfs-ruta-absoluta/CAUSA.txt', 'rom-simplificada/trabajo/fallo-debugfs-ruta-absoluta/system-fsck.log', 'rom-simplificada/trabajo/system.raw.img'])
for rel in ['rom-simplificada/instalador/.cache', 'rom-simplificada/instalador/__pycache__', 'rom-simplificada/inspeccion/__pycache__']:
    item(rel, 'Cache de compilacion/importacion regenerable; fuentes y binarios finales conservados.', ['rom-simplificada/instalador', 'rom-simplificada/inspeccion'])

record = {'created_utc': datetime.now(timezone.utc).isoformat(), 'root': str(ROOT), 'state': 'audited_not_deleted', 'entries': rows, 'bytes': sum(x['bytes'] for x in rows)}
(OUT / 'limpieza-plan.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'files_or_directories': len(rows), 'bytes': record['bytes'], 'plan': str(OUT / 'limpieza-plan.json')}))
