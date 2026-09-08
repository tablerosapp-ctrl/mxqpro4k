"""Archiva respaldos existentes, cifra con age y verifica el descifrado en PC.

No accede al TV, USB ni red. No publica archivos. Las fuentes son inmutables.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'privado/backup-github-20260908'
AGE = ROOT / 'tools/age-1.3.2/age.exe'
KEYGEN = ROOT / 'tools/age-1.3.2/age-keygen.exe'
ACQ = ROOT / 'privado/instalacion022-adquisicion-20260908-124541-2bb0d2f7'
ORIG = [ROOT / 'privado/TVBASE-respaldo-P291-20260907-194104-0deb291b',
        ROOT / 'privado/TVBASE-respaldo-P291-20260907-194413-6d502965']
NAME = 'TVBASE-P291-RESPALDO-20260908.zip.age'
FLAGS = 0x08000000 if os.name == 'nt' else 0

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(p, data):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())

def digest(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def ordinary(p):
    assert p.resolve().is_relative_to(ROOT.resolve())
    for parent in [p, *p.parents]:
        if parent == ROOT.parent: break
        assert not parent.is_symlink() and not parent.is_junction(), 'Enlace no admitido'
    assert stat.S_ISREG(p.stat().st_mode), 'Archivo no regular'

def run(args, stdout=None):
    p = subprocess.run([str(a) for a in args], stdout=stdout or subprocess.PIPE,
                       stderr=subprocess.PIPE, creationflags=FLAGS)
    if p.returncode: raise RuntimeError('Herramienta local fallo, codigo '+str(p.returncode))
    return p.stdout

def main():
    DEST.mkdir(exist_ok=True)
    # A key-only interruption can resume; never replace an archive or receipt.
    assert not (DEST/'PREPARADO.json').exists() and not (DEST/'RESPALDO-PRIVADO.zip').exists()
    assets_dir = DEST / 'release-assets'; assets_dir.mkdir(exist_ok=True)
    assert not list(assets_dir.iterdir())
    assert load(ACQ / 'adquisicion.json')['state'] == 'verified'
    key = DEST / 'CLAVE-PRIVADA-RESPALDO-P291.txt'
    if not key.exists(): run([KEYGEN, '-o', key])
    ordinary(key)
    if os.name == 'nt':
        # Only the current account and SYSTEM; neither key nor SID is printed.
        quoted_path = "'"+str(key).replace("'", "''")+"'"
        ps = "$id=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value; & icacls "+quoted_path+" /inheritance:r /grant:r ('*'+$id+':F') '*S-1-5-18:F' | Out-Null; exit $LASTEXITCODE"
        run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps])
    recipient = run([KEYGEN, '-y', key]).decode().strip()
    assert re.fullmatch(r'age1[0-9a-z]+', recipient)
    with key.open('r+b') as f: f.flush(); os.fsync(f.fileno())
    sources = []
    original_images = {}
    expected = {}
    for folder in ORIG:
        m = load(folder / 'manifest.json')
        assert m['exit'] == 0
        for row in m['partitions']:
            path = folder / row['file']
            original_images[row['name']] = path
            expected[path] = (row['bytes'], row['sha256'])
        for p in sorted(folder.rglob('*')):
            if p.is_file(): sources.append((p, 'originales/'+folder.name+'/'+p.relative_to(folder).as_posix()))
    assert len(original_images) == 12
    archive_names = dict(sources)
    acq = load(ACQ / 'adquisicion.json')
    acq_files = {ACQ / r['relative_path']: (r['bytes'], r['sha256']) for r in acq['files']}
    expected.update(acq_files)
    aliases = []
    image_dir = ACQ / 'usb/TVBASE-respaldo-022-773306709'
    for p in sorted(ACQ.rglob('*')):
        if not p.is_file(): continue
        name = 'adquisicion022/'+p.relative_to(ACQ).as_posix()
        if p.parent == image_dir and p.suffix == '.img' and p.stem in original_images:
            original = original_images[p.stem]
            assert expected[p] == expected[original]
            aliases.append({'path':name, 'same_as':archive_names[original], 'bytes':expected[p][0], 'sha256':expected[p][1]})
        else: sources.append((p, name))
    assert len(aliases) == 5
    # Preserve the exact successful installer and matching five-image restorer.
    for rel in ['rom-simplificada/original-p291/instalacion-022/salida/TVBASE-P291-A9-0.2.2-VERIFICACION.json',
                'rom-simplificada/original-p291/restauracion-022/salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.2-VERIFICACION.json']:
        receipt = ROOT / rel; m = load(receipt); payload = ROOT / m['file']
        expected[payload] = (m['bytes'], m['sha256'])
        sources += [(receipt, 'paquetes/'+receipt.name), (payload, 'paquetes/'+payload.name)]
    assert len({name for _,name in sources}) == len(sources)
    plain = DEST / 'RESPALDO-PRIVADO.zip'
    index = {'format':1, 'scope':'Original P291 acquisitions, pre-install userdata, installation evidence and exact installer/restorer022. Not whole eMMC, not an atomic snapshot, no physical restoration proven.',
             'files':[], 'aliases':aliases, 'unique_partition_images':13, 'unique_partition_bytes':6157238272}
    print('Comprimiendo respaldo privado; originales intactos.', flush=True)
    total=0; last=time.monotonic()
    with zipfile.ZipFile(plain, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        for p,name in sources:
            ordinary(p); before=p.stat(); h=hashlib.sha256(); count=0
            with p.open('rb') as src,z.open(name,'w',force_zip64=True) as dst:
                while chunk:=src.read(4*1024*1024):
                    dst.write(chunk); h.update(chunk); count+=len(chunk); total+=len(chunk)
                    if time.monotonic()-last>20:
                        print(json.dumps({'stage':'compress','input_bytes':total}),flush=True); last=time.monotonic()
            after=p.stat()
            assert count==before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
            if p in expected: assert (count,h.hexdigest())==expected[p], 'Fuente difiere del respaldo verificado'
            index['files'].append({'path':name,'bytes':count,'sha256':h.hexdigest()})
        z.writestr('RESPALDO-INDICE.json',json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    save(DEST/'INDICE-PRIVADO.json',index)
    with plain.open('r+b') as f: f.flush(); os.fsync(f.fileno())
    archive_sha=digest(plain)
    encrypted=DEST/NAME
    run([AGE,'-r',recipient,'-o',encrypted,plain])
    with encrypted.open('r+b') as f: f.flush(); os.fsync(f.fileno())
    print(json.dumps({'stage':'encrypted','ciphertext_bytes':encrypted.stat().st_size}),flush=True)
    decrypted=DEST/'VERIFICACION-DESCIFRADA.zip'
    run([AGE,'-d','-i',key,'-o',decrypted,encrypted])
    assert decrypted.stat().st_size==plain.stat().st_size and digest(decrypted)==archive_sha
    with zipfile.ZipFile(decrypted) as z:
        assert len(z.namelist())==len(index['files'])+1
        assert json.loads(z.read('RESPALDO-INDICE.json'))==index
        for row in index['files']:
            h=hashlib.sha256(); count=0
            with z.open(row['path']) as f:
                while chunk:=f.read(4*1024*1024):h.update(chunk); count+=len(chunk)
            assert (count,h.hexdigest())==(row['bytes'],row['sha256'])
    print('Descifrado completo y todos los archivos verificados.',flush=True)
    parts=[]
    with encrypted.open('rb') as src:
        number=0
        while True:
            first=src.read(4*1024*1024)
            if not first:break
            number+=1; out=assets_dir/(NAME+f'.part{number:03d}'); count=0; h=hashlib.sha256()
            with out.open('xb') as f:
                block=first
                while block:
                    f.write(block); h.update(block); count+=len(block)
                    if count==512*1024*1024:break
                    block=src.read(min(4*1024*1024,512*1024*1024-count))
                f.flush(); os.fsync(f.fileno())
            assert digest(out)==h.hexdigest()
            parts.append({'name':out.name,'bytes':count,'sha256':h.hexdigest()})
    combined=hashlib.sha256()
    for part in parts:
        with (assets_dir/part['name']).open('rb') as f:
            while block:=f.read(4*1024*1024):combined.update(block)
    assert combined.hexdigest()==digest(encrypted)
    public={'format':1,'id':'P291-BACKUP-20260908','encryption':'age-v1-X25519','archive_format':'zip-deflate',
            'encrypted_file':NAME,'encrypted_bytes':encrypted.stat().st_size,'encrypted_sha256':combined.hexdigest(),
            'parts':parts,'unique_partition_images':13,'unique_partition_bytes':6157238272,
            'deduplicated_partition_aliases':5,'installer_and_restorer_022_included':True,
            'private_key_included':False,'roundtrip_verified':True,'device_restoration_tested':False,
            'whole_emmc_backup':False,'scope':'Original P291 images and pre-install userdata, related evidence, installer022 and OEM-restorer022. Files only; no automated flashing.'}
    public_file=assets_dir/'RESPALDO-CIFRADO.json';save(public_file,public)
    all_assets=[dict(row,path=str((assets_dir/row['name']).relative_to(ROOT)).replace('\\','/')) for row in parts]
    all_assets.append({'name':public_file.name,'path':public_file.relative_to(ROOT).as_posix(),'bytes':public_file.stat().st_size,'sha256':digest(public_file)})
    prepared={'state':'verified','encryption':'age-v1-X25519','roundtrip_verified':True,'assets':all_assets,'public_manifest':public,
              'private_key_path':key.relative_to(ROOT).as_posix(),'archive_files_verified':len(index['files']),
              'encrypted_sha256':combined.hexdigest(),'tool_origin':load(ROOT/'tools/age-1.3.2/ORIGEN.json')}
    save(DEST/'PREPARADO.json',prepared)
    print(json.dumps({'state':'verified','files_verified':len(index['files']),'assets':len(all_assets),'ciphertext_bytes':encrypted.stat().st_size,'receipt':(DEST/'PREPARADO.json').relative_to(ROOT).as_posix()}),flush=True)

if __name__=='__main__':main()
