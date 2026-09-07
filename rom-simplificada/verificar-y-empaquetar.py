"""Validate every retained file and build an experimental Amlogic container.
Only regular workspace files are accessed. This script never flashes any device.
"""
import hashlib,importlib.util,json,mmap,struct,subprocess,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;HERE=ROOT/'rom-simplificada';WORK=HERE/'trabajo'
OUT=HERE/'salida';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'analisis-rom/candidato-android9.img'
spec=importlib.util.spec_from_file_location('inv',HERE/'inspeccion/inventariar-ext4.py')
inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
changes=json.loads((WORK/'cambios.json').read_text(encoding='utf8'))
original=json.loads((ROOT/'analisis-rom/integridad-interna.json').read_text(encoding='utf8'))['registros']
assert hashlib.file_digest(SOURCE.open('rb'),'sha256').hexdigest()==inv.EXPECTED
result={'status':'experimental_no_flasheada','source_sha256':inv.EXPECTED,'static_verification':{},
 'hardware_compatibility_confirmed':False,'usb_install_entry_confirmed':False,'runtime_webview_confirmed':False}
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True,creationflags=0x08000000)
 return p.returncode,p.stdout+p.stderr
def zero_free(image):
 # Honor allocation bitmaps; skip uninitialized block groups. No allocated block is changed.
 with image.open('r+b') as f,mmap.mmap(f.fileno(),0) as m:
  sb=m[1024:2048];bs=1024<<struct.unpack_from('<I',sb,24)[0]
  total=struct.unpack_from('<I',sb,4)[0];first=struct.unpack_from('<I',sb,20)[0]
  bpg=struct.unpack_from('<I',sb,32)[0];assert not struct.unpack_from('<I',sb,96)[0]&0x80
  zero=bytes(bs);cleared=0;skipped=[]
  for group,start in enumerate(range(first,total,bpg)):
   gd=m[(first+1)*bs+group*32:(first+1)*bs+(group+1)*32]
   if struct.unpack_from('<H',gd,18)[0]&2:skipped.append(group);continue
   block=struct.unpack_from('<I',gd,0)[0];bitmap=bytes(m[block*bs:(block+1)*bs]);count=0
   for local in range(min(bpg,total-start)):
    if not bitmap[local//8]&(1<<(local%8)):
     off=(start+local)*bs;m[off:off+bs]=zero;cleared+=1;count+=1
   assert count==struct.unpack_from('<H',gd,12)[0],('free block count mismatch',group)
  m.flush()
 return {'zeroed_free_blocks':cleared,'skipped_uninitialized_groups':skipped}

with SOURCE.open('rb') as src,mmap.mmap(src.fileno(),0,access=mmap.ACCESS_READ) as data:
 for name in ('system','vendor'):
  image=WORK/(name+'.raw.img');free_info=zero_free(image)
  code,output=run([ROOT/'tools/ext4-cygwin/bin/e2fsck.exe','-fn',image])
  (OUT/(name+'-fsck.txt')).write_bytes(output);assert code==0,output.decode('utf8','replace')
  part=next(p for p in original if p['tipo']=='PARTITION' and p['nombre']==name)
  before=inv.Ext4(inv.Sparse(data,part['offset'],part['bytes']))
  old={p:n for p,n in before.walk()}
  dropped=set(changes['removed_paths'][name]);replaced={p['path']:p for p in changes['added_or_replaced'][name]}
  with image.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as edited:
   after=inv.Ext4(inv.Sparse(edited,0,len(edited)));new={p:n for p,n in after.walk()};verified=0
   assert not dropped&set(new)
   for path,node in old.items():
    if path in dropped or path in replaced:continue
    assert path in new,('missing unchanged path',path)
    for key in ('modo','uid','gid'):assert node[key]==new[path][key],('metadata changed',path,key)
    typ=node['modo']&0xf000
    if typ in (0x8000,0xa000):
     assert hashlib.sha256(before.content(node)).digest()==hashlib.sha256(after.content(new[path])).digest(),('content changed',path)
     verified+=1
   for path,item in replaced.items():
    assert hashlib.sha256(after.content(new[path])).hexdigest()==item['sha256'],path
    code,ea=run([ROOT/'tools/ext4-cygwin/bin/debugfs.exe','-R','ea_list '+path,image]);assert code==0
    assert item['context'].encode() in ea,(path,ea)
   # Any unexpected extra regular file would invalidate the recipe.
   for path,node in new.items():
    if path not in old and node['modo']&0xf000==0x8000:assert path in replaced,path
   result['static_verification'][name]={'untouched_files_identical':verified,'changed_files_verified':len(replaced),
      'fsck_exit':code,'sha256':hashlib.sha256(edited).hexdigest(),'free_bytes':after.meta['bloques_libres']*after.bs,**free_info}
   print(name,verified,'unchanged files verified',flush=True)

def sparse_pack(image,dest):
 bs=4096;chunks=0;blocks=image.stat().st_size//bs
 with image.open('rb') as f,dest.open('w+b') as out:
  out.write(bytes(28));kind=None;start=0;count=0;payload=bytearray()
  def emit():
   nonlocal chunks
   if count==0:return
   if kind=='zero':out.write(struct.pack('<HHII',0xcac2,0,count,16));out.write(bytes(4))
   else:out.write(struct.pack('<HHII',0xcac1,0,count,12+len(payload)));out.write(payload)
   chunks+=1
  for i in range(blocks):
   b=f.read(bs);assert len(b)==bs
   now='zero' if b==bytes(bs) else 'raw'
   if kind!=now or (kind=='raw' and count>=1024):emit();payload=bytearray();count=0;kind=now
   if now=='raw':payload.extend(b)
   count+=1
  emit();out.seek(0);out.write(struct.pack('<IHHHHIIII',0xed26ff3a,1,0,28,12,bs,blocks,chunks,0))
 # Compare the complete expanded stream to the filesystem copy.
 digest=hashlib.sha256()
 with dest.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as d:
  reader=inv.Sparse(d,0,len(d))
  for p in range(0,reader.logical_size,4*1024*1024):digest.update(reader.read(p,min(4*1024*1024,reader.logical_size-p)))
 assert digest.hexdigest()==hashlib.file_digest(image.open('rb'),'sha256').hexdigest()
 return dest

replacements={n:sparse_pack(WORK/(n+'.raw.img'),OUT/(n+'.sparse.img')) for n in ('system','vendor')}
final=OUT/'TVBASE-P291-A9-0.1-EXPERIMENTAL.img'
if final.exists():raise FileExistsError('Keep the existing complete container; do not overwrite it implicitly')
with SOURCE.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as d,final.open('w+b') as out:
 count=len(original);header=bytearray(d[:64+count*576]);out.write(header);cache={};emitted=[]
 for i,p in enumerate(original):
  key=(p['offset'],p['bytes']);content=None
  if p['tipo']=='PARTITION' and p['nombre'] in replacements:content=replacements[p['nombre']].read_bytes();key=('new',p['nombre'])
  elif p['tipo']=='VERIFY' and p['nombre'] in replacements:
   content=b'sha1sum '+hashlib.file_digest(replacements[p['nombre']].open('rb'),'sha1').hexdigest().encode();key=('verify',p['nombre'])
  if key in cache:offset,length=cache[key]
  else:
   # Maintain original alignment; duplicated payloads keep a shared offset.
   padding=(-out.tell())%4;out.write(bytes(padding));offset=out.tell()
   if content is None:content=d[p['offset']:p['offset']+p['bytes']]
   out.write(content);length=len(content);cache[key]=(offset,length)
  base=64+i*576;struct.pack_into('<QQ',header,base+16,offset,length)
  emitted.append({**p,'offset':offset,'bytes':length})
 size=out.tell();struct.pack_into('<Q',header,12,size);out.seek(0);out.write(header);out.flush()
 out.seek(4);crc=0
 while True:
  b=out.read(4*1024*1024)
  if not b:break
  crc=zlib.crc32(b,crc)
 out.seek(0);out.write(struct.pack('<I',crc^0xffffffff));out.flush()

checks=[]
with SOURCE.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as orig,final.open('rb') as g,mmap.mmap(g.fileno(),0,access=mmap.ACCESS_READ) as d:
 assert struct.unpack_from('<Q',d,12)[0]==len(d)
 crc=0
 for pos in range(4,len(d),4*1024*1024):crc=zlib.crc32(d[pos:pos+4*1024*1024],crc)
 assert struct.unpack_from('<I',d,0)[0]==crc^0xffffffff
 for i,p in enumerate(emitted):
  payload=d[p['offset']:p['offset']+p['bytes']]
  if p['nombre'] not in replacements or p['tipo'] not in ('PARTITION','VERIFY'):
   old=original[i];assert payload==orig[old['offset']:old['offset']+old['bytes']],('unexpected container change',p)
  if p['tipo']=='PARTITION':
   v=emitted[i+1];assert v['tipo']=='VERIFY' and v['nombre']==p['nombre']
   declared=d[v['offset']:v['offset']+v['bytes']];calculated=b'sha1sum '+hashlib.sha1(payload).hexdigest().encode()
   assert declared==calculated,p['nombre'];checks.append(p['nombre'])
result.update({'file':str(final.relative_to(ROOT)),'bytes':final.stat().st_size,'sha256':hashlib.file_digest(final.open('rb'),'sha256').hexdigest(),
 'container_crc32':hex(crc^0xffffffff),'verified_partition_sha1':checks,'unchanged_other_container_items':True,'records':emitted})
assert hashlib.file_digest(SOURCE.open('rb'),'sha256').hexdigest()==inv.EXPECTED
(OUT/'VERIFICACION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:result[k] for k in ('file','bytes','sha256','container_crc32','verified_partition_sha1')},indent=2))
