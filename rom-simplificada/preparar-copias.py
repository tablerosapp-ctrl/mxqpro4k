"""Expand selected partitions from the immutable ROM into regular workspace files."""
import hashlib, importlib.util, json, mmap
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
module=ROOT/'rom-simplificada/inspeccion/inventariar-ext4.py'
spec=importlib.util.spec_from_file_location('inventory',module)
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)
source=ROOT/'analisis-rom/candidato-android9.img'
assert hashlib.file_digest(source.open('rb'),'sha256').hexdigest()==inventory.EXPECTED
parts=json.loads((ROOT/'analisis-rom/integridad-interna.json').read_text(encoding='utf8'))['registros']
out=ROOT/'rom-simplificada/trabajo';out.mkdir(exist_ok=True)
records=[]
with source.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
 for p in parts:
  if p['tipo']!='PARTITION' or p['nombre'] not in ('system','vendor','product'):continue
  dest=out/(p['nombre']+'.raw.img')
  if dest.exists():raise FileExistsError('Work image already exists; do not discard changes: '+str(dest))
  reader=inventory.Sparse(data,p['offset'],p['bytes'])
  digest=hashlib.sha256()
  with dest.open('xb') as target:
   for pos in range(0,reader.logical_size,4*1024*1024):
    chunk=reader.read(pos,min(4*1024*1024,reader.logical_size-pos));target.write(chunk);digest.update(chunk)
  records.append({'particion':p['nombre'],'bytes':reader.logical_size,'sha256':digest.hexdigest()})
  print(json.dumps(records[-1]),flush=True)
(out/'copias-originales.json').write_text(json.dumps(records,indent=2),encoding='utf8')
