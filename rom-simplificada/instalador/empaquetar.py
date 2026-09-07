"""Produce a real non-A/B recovery ZIP, then verify every payload and its whole-file signature.
The AOSP public test key is used only for this experimental stock-recovery candidate.
Acceptance by the first TV's recovery is NOT implied by signing successfully.
"""
import argparse,hashlib,importlib.util,json,mmap,struct,sys,zipfile
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding,utils
from cryptography.hazmat.primitives.serialization import pkcs7

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'rom-simplificada/salida';WORK=HERE/'payload';WORK.mkdir(exist_ok=True)
TOOLS=ROOT/'tools/firmar-ota';FINAL=OUT/'TVBASE-P291-A9-0.1-RECOVERY.zip'
spec=importlib.util.spec_from_file_location('ext4',ROOT/'rom-simplificada/inspeccion/inventariar-ext4.py');ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def der(data,offset=0):
 start=offset;tag=data[offset];offset+=1;n=data[offset];offset+=1
 if n&128:k=n&127;assert 0<k<=4;n=int.from_bytes(data[offset:offset+k],'big');offset+=k
 end=offset+n;assert end<=len(data)
 return tag,data[offset:end],data[start:end],end
def children(data):
 nodes=[];offset=0
 while offset<len(data):t,v,full,offset=der(data,offset);nodes.append((t,v,full))
 return nodes
def verify_signature(path,cert):
 with path.open('rb') as f:
  f.seek(-6,2);footer=f.read();start,mark,comment=struct.unpack('<H2sH',footer);assert mark==b'\xff\xff' and 6<start<=comment
  size=f.tell();f.seek(-(22+comment),2);tail=f.read();assert tail[:4]==b'PK\x05\x06' and tail.count(b'PK\x05\x06')==1
  assert struct.unpack_from('<H',tail,20)[0]==comment
  f.seek(size-start);signature=f.read(start-6)
  outer=children(der(signature)[1]);assert outer[0][1].hex()=='2a864886f70d010702';sd=children(der(outer[1][1])[1]);assert sd[-1][0]==0x31
  signers=children(sd[-1][1]);assert len(signers)==1;info=children(signers[0][1]);assert len(info)==5 # No signed attributes: same direct digest as recovery.
  assert children(info[2][1])[0][1].hex()=='608648016503040201'
  assert children(info[3][1])[0][1].hex()=='2a864886f70d010101'
  assert info[4][0]==4
  included=pkcs7.load_der_pkcs7_certificates(signature);assert len(included)==1 and included[0].fingerprint(hashes.SHA256())==cert.fingerprint(hashes.SHA256())
  digest=hashlib.sha256();left=size-comment-2;f.seek(0)
  while left:b=f.read(min(left,4<<20));assert b;digest.update(b);left-=len(b)
  cert.public_key().verify(info[4][1],digest.digest(),padding.PKCS1v15(),utils.Prehashed(hashes.SHA256()))
 return cert.fingerprint(hashes.SHA256()).hex()

def main():
 global FINAL
 parser=argparse.ArgumentParser()
 parser.add_argument('--revision-report',type=Path)
 args=parser.parse_args()
 revision=None;version='0.1';binary=HERE/'update-binary'
 if args.revision_report:
  revision=json.loads(args.revision_report.read_text(encoding='utf8'))
  assert revision['version']=='0.1.1' and revision['package_id']=='TVBASE-P291-A9-0.1.1'
  assert revision['inherited_recovery_replacement_disabled'] and revision['fsck_exit']==0
  version=revision['version'];binary=ROOT/revision['installer_binary']
  assert binary.resolve().is_relative_to(ROOT/'rom-simplificada/trabajo/revision-0.1.1')
  FINAL=OUT/f'TVBASE-P291-A9-{version}-RECOVERY.zip'
 if FINAL.exists():raise RuntimeError('La salida ya existe; no se sobrescribe sin revisar la version')
 original=ROOT/'analisis-rom/candidato-android9.img';assert sha(original)=='bd8a8d9c02f6aa1119e5ea7708f2b49a1e4c7fef6169d30bbd1604981eb042e5'
 existing=json.loads((OUT/'VERIFICACION.json').read_text(encoding='utf8'));paths={}
 for name in ('system','vendor'):
  p=ROOT/'rom-simplificada/trabajo'/f'{name}.raw.img';assert sha(p)==existing['static_verification'][name]['sha256'];paths[name]=p
 if revision:
  p=ROOT/revision['system_image'];assert p.resolve().is_relative_to(ROOT/'rom-simplificada/trabajo/revision-0.1.1')
  assert sha(p)==revision['system_sha256'];paths['system']=p
 parts=json.loads((ROOT/'analisis-rom/informe-inspeccion.json').read_text(encoding='utf8'))['partes']
 with original.open('rb') as source,mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as data:
  for name in ('product','odm','boot'):
   part=next(x for x in parts if x['tipo']=='PARTITION' and x['nombre']==name);r=ext.Sparse(data,part['offset'],part['bytes']);p=WORK/f'{name}.img'
   with p.open('wb') as f:
    for off in range(0,r.logical_size,4<<20):f.write(r.read(off,min(4<<20,r.logical_size-off)))
   paths[name]=p
 b=binary.read_bytes();assert b[:7]==b'\x7fELF\x01\x01\x01' and struct.unpack_from('<H',b,18)[0]==40
 phoff=struct.unpack_from('<I',b,28)[0];phsize,phnum=struct.unpack_from('<HH',b,42)
 assert all(struct.unpack_from('<I',b,phoff+i*phsize)[0]!=3 for i in range(phnum)), 'El instalador no debe depender de un interprete externo'
 manifest={'format':1,'id':f'TVBASE-P291-A9-{version}','dt_id':'gxlx2_p291_1g','media_id':'TVBASE-P291-20260906-4dc82786','images':[]}
 for name,p in paths.items():manifest['images'].append({'name':name,'entry':f'tvbase/{name}.img','size':p.stat().st_size,'sha256':sha(p)})
 unsigned=HERE/f'unsigned-{version}.zip'
 with zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as z:
  for im in manifest['images']:
   print('Empaquetando',im['name'],im['size'],flush=True);z.write(paths[im['name']],im['entry'])
  info=zipfile.ZipInfo('META-INF/com/google/android/update-binary',(2026,9,6,0,0,0));info.external_attr=0o100755<<16;z.writestr(info,b)
  z.writestr('tvbase/manifest.json',json.dumps(manifest,indent=2))
  z.writestr('META-INF/com/android/metadata','ota-type=BLOCK\npre-device=ampere\nota-wipe=no\npost-sdk-level=28\n')
  z.writestr('META-INF/com/android/otacert',(TOOLS/'testkey.x509.pem').read_bytes())
 print('Firmando el paquete completo',flush=True)
 raw=unsigned.read_bytes();assert raw[-22:-18]==b'PK\x05\x06' and raw[-2:]==b'\0\0'
 cert=x509.load_pem_x509_certificate((TOOLS/'testkey.x509.pem').read_bytes());key=serialization.load_der_private_key((TOOLS/'testkey.pk8').read_bytes(),password=None)
 signature=pkcs7.PKCS7SignatureBuilder().set_data(raw[:-2]).add_signer(cert,key,hashes.SHA256()).sign(serialization.Encoding.DER,[pkcs7.PKCS7Options.DetachedSignature,pkcs7.PKCS7Options.Binary,pkcs7.PKCS7Options.NoAttributes])
 msg=b'TVBASE experimental AOSP testkey\0';total=len(msg)+len(signature)+6;comment=msg+signature+struct.pack('<H2sH',len(signature)+6,b'\xff\xff',total)
 assert total<=65535 and b'PK\x05\x06' not in comment
 with FINAL.open('xb') as f:f.write(raw[:-2]);f.write(struct.pack('<H',total));f.write(comment)
 del raw
 cert_hash=verify_signature(FINAL,cert)
 with zipfile.ZipFile(FINAL) as z:
  for im in manifest['images']:
   with z.open(im['entry']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==im['sha256']
   assert z.getinfo(im['entry']).file_size==im['size']
  assert hashlib.sha256(z.read('META-INF/com/google/android/update-binary')).hexdigest()==sha(binary)
 result={'file':str(FINAL.relative_to(ROOT)),'bytes':FINAL.stat().st_size,'sha256':sha(FINAL),'manifest':manifest,'whole_file_signature_verified':True,'certificate_sha256':cert_hash,'payload_sha256_verified':True,'installer_elf':'ARM32 static, no PT_INTERP','installer_sha256':sha(binary),'preserved_partitions':['bootloader','recovery','dtb','dtbo','vbmeta','data','keys','env','misc'],'original_partition_backup_required':True,'hardware_compatibility_confirmed':False,'first_tv_recovery_accepts_signature':False,'physically_installed':False}
 if revision:result['recovery_preservation_revision']=revision
 report_name='RECOVERY-VERIFICACION.json' if version=='0.1' else f'RECOVERY-VERIFICACION-{version}.json'
 (OUT/report_name).write_text(json.dumps(result,indent=2),encoding='utf8');(HERE/f'manifest-{version}.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
