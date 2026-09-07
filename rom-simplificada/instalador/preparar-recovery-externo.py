"""Build a USB-bootable P291 recovery copy with our ZIP signing key.
Only the RAM disk's trusted-key list and identifying properties change.
The kernel, recovery executable, device trees and every other CPIO entry are preserved.
This does not write a device or disable signature verification.
"""
import gzip, hashlib, importlib.util, json, re, struct
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE/'recovery-externo'
SOURCE=ROOT/'rom-simplificada/inspeccion/recovery-original.img'
FINAL=OUT/'recovery.img'
EXPECTED='736c6fa50d1957b6f0c1b5b986b19e1216659cc51210719e9ed269173a95adc0'
def sha(b):return hashlib.sha256(b).hexdigest()
def entries(data):
    pos=0;rows=[]
    while True:
        header=data[pos:pos+110];assert header[:6] in (b'070701',b'070702')
        values=[int(header[6+i*8:14+i*8],16) for i in range(13)]
        size,nlen=values[6],values[11]
        name=data[pos+110:pos+110+nlen-1].decode('utf8')
        start=(pos+110+nlen+3)//4*4;end=(start+size+3)//4*4
        rows.append((name,header,data[pos+110:start],data[start:start+size],data[pos:end]))
        pos=end
        if name=='TRAILER!!!':return rows,data[pos:]

def key(version,n,e):
    assert n.bit_length()==2048 and (version,e) in ((3,3),(4,65537))
    words=lambda value:','.join(str((value>>(32*i))&0xffffffff) for i in range(64))
    return ('v%d {64,0x%08x,{%s},{%s}}'%(version,(-pow(n,-1,1<<32))%(1<<32),words(n),words(pow(2,4096,n)))).encode()

def main():
    assert not FINAL.exists(), 'Preserve an existing prepared recovery'
    data=SOURCE.read_bytes();assert sha(data)==EXPECTED and data[:8]==b'ANDROID!'
    ks,ka,rs,ra,ss,sa,tags,page,version=struct.unpack_from('<9I',data,8)
    assert version==1 and page==2048
    align=lambda n:(n+page-1)//page*page
    ds,do,hs=struct.unpack_from('<IQI',data,1632);assert hs==1648
    kernel=data[page:page+ks];ram=data[page+align(ks):page+align(ks)+rs]
    second=data[page+align(ks)+align(rs):page+align(ks)+align(rs)+ss];dtbo=data[do:do+ds]
    assert not any(data[align(do+ds):])
    digest=hashlib.sha1()
    for content in (kernel,ram,second,dtbo):digest.update(content);digest.update(struct.pack('<I',len(content)))
    assert digest.digest()==data[576:596], 'Original Android v1 ID must verify before repacking'
    rows,tail=entries(gzip.decompress(ram));original={name:content for name,_,_,content,_ in rows}
    cert=x509.load_pem_x509_certificate((ROOT/'tools/firmar-ota/testkey.x509.pem').read_bytes())
    public=cert.public_key().public_numbers();trusted=key(3,public.n,public.e)
    oldkeys=original['res/keys'].strip()
    assert re.fullmatch(rb'\{64,0x[0-9a-fA-F]+,\{[0-9,]+\},\{[0-9,]+\}\}',oldkeys)
    words=[int(v) for v in re.search(rb'\{64,0x[0-9a-fA-F]+,\{([0-9,]+)\}',oldkeys)[1].split(b',')]
    assert sum(v<<(32*i) for i,v in enumerate(words))!=public.n
    newkeys=oldkeys+b',\n'+trusted+b'\n'
    props=original['prop.default'].decode('utf8')
    for k,v in {'ro.build.display.id':'TVBASE-Recovery-P291-0.1',
                'ro.build.fingerprint':'tvbase/ampere/ampere:9/PPR1.180610.011/recovery-0.1:userdebug/test-keys',
                'ro.product.device':'ampere'}.items():
        pattern=r'^'+re.escape(k)+r'=.*$';props,count=re.subn(pattern,k+'='+v,props,flags=re.M)
        assert count<=1
        if not count:props+='\n'+k+'='+v+'\n'
    changed={'res/keys':newkeys,'prop.default':props.encode()}
    cpio=bytearray()
    for name,header,namedata,content,raw in rows:
        if name not in changed:cpio.extend(raw);continue
        content=changed[name];header=bytearray(header);header[54:62]=('%08x'%len(content)).encode()
        if header[:6]==b'070702':header[102:110]=('%08x'%(sum(content)&0xffffffff)).encode()
        cpio.extend(header);cpio.extend(namedata);cpio.extend(content);cpio.extend(bytes((-len(cpio))%4))
    cpio.extend(tail);newram=gzip.compress(bytes(cpio),compresslevel=9,mtime=0)
    newdo=page+align(ks)+align(len(newram))+align(ss)
    assert newdo+align(ds)<=len(data)
    result=bytearray(len(data));result[:page]=data[:page]
    struct.pack_into('<I',result,16,len(newram));struct.pack_into('<Q',result,1636,newdo)
    off=page
    for content in (kernel,newram,second):result[off:off+len(content)]=content;off+=align(len(content))
    assert off==newdo;result[newdo:newdo+ds]=dtbo
    digest=hashlib.sha1()
    for content in (kernel,newram,second,dtbo):digest.update(content);digest.update(struct.pack('<I',len(content)))
    result[576:608]=digest.digest()+bytes(12)
    reread,_=entries(gzip.decompress(newram));after={name:content for name,_,_,content,_ in reread}
    assert original.keys()==after.keys()
    for name,header,namedata,content,raw in rows:
        if name in changed:assert after[name]==changed[name]
        else:assert next(x[4] for x in reread if x[0]==name)==raw,name
    assert result[page:page+ks]==kernel and result[newdo:newdo+ds]==dtbo
    assert result[page+align(ks)+align(len(newram)):page+align(ks)+align(len(newram))+ss]==second
    # Roundtrip the added C-key numbers rather than treating a textual key as proof.
    parsed=re.fullmatch(rb'v3 \{64,(0x[0-9a-f]+),\{([0-9,]+)\},\{([0-9,]+)\}\}',trusted);assert parsed
    n=sum(int(v)<<(32*i) for i,v in enumerate(parsed[2].split(b',')))
    assert n==public.n and int(parsed[1],16)==(-pow(n,-1,1<<32))%(1<<32)
    assert sum(int(v)<<(32*i) for i,v in enumerate(parsed[3].split(b',')))==pow(2,4096,n)
    # Verify the actual existing ROM ZIP against the public key now embedded in recovery.
    spec=importlib.util.spec_from_file_location('pack',HERE/'empaquetar.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
    cert_hash=pack.verify_signature(ROOT/'rom-simplificada/salida/TVBASE-P291-A9-0.1.1-RECOVERY.zip',cert)
    with FINAL.open('xb') as f:f.write(result)
    assert sha(FINAL.read_bytes())==sha(result) and sha(SOURCE.read_bytes())==EXPECTED
    report={'file':str(FINAL.relative_to(ROOT)),'bytes':len(result),'sha256':sha(result),'source_sha256':EXPECTED,
            'kernel_sha256':sha(kernel),'secondary_sha256':sha(second),'dtbo_sha256':sha(dtbo),
            'unchanged_cpio_entries':len(rows)-len(changed),'changed_cpio_entries':list(changed),
            'original_key_retained':True,'added_key_version':3,'added_key_certificate_sha256':cert_hash,
            'signature_verification_disabled':False,'rom_zip_signature_verified_with_added_key':True,
            'android_v1_id_verified':True,'external_boot_hardware_confirmed':False,
            'intended_use':'load recovery.img from USB into RAM through Amlogic update; not flash the recovery partition',
            'limitations':['Installed P291 bootloader USB boot behavior is unverified.','Amlogic reference may clear instaboot header; recovery may process existing commands/logs.','Bootloader authentication of this modified RAM disk is unverified.']}
    (OUT/'PREPARADO.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (OUT/'keys-prepared.txt').write_bytes(newkeys)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
