"""Read and compare candidate Android boot/recovery; never access devices."""
import gzip, hashlib, json, re, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE/'recovery-externo'
OUT.mkdir(exist_ok=True)

def sha(b):return hashlib.sha256(b).hexdigest()

def parse(path):
    data=path.read_bytes()
    assert data[:8]==b'ANDROID!'
    ks,ka,rs,ra,ss,sa,tags,page,version=struct.unpack_from('<9I',data,8)
    assert page in (2048,4096,8192,16384) and version in (0,1)
    align=lambda n:(n+page-1)//page*page
    k=data[page:page+ks];r=data[page+align(ks):page+align(ks)+rs]
    second=data[page+align(ks)+align(rs):page+align(ks)+align(rs)+ss]
    assert len(k)==ks and len(r)==rs and len(second)==ss
    info={'file':str(path.relative_to(ROOT)),'bytes':len(data),'sha256':sha(data),
          'kernel_size':ks,'kernel_sha256':sha(k),'ramdisk_size':rs,
          'second_size':ss,'second_sha256':sha(second),'page':page,'header_version':version,
          'name':data[48:64].split(b'\0')[0].decode('ascii','replace'),
          'cmdline':data[64:576].split(b'\0')[0].decode('ascii','replace')}
    if version==1:
        ds,do,hs=struct.unpack_from('<IQI',data,1632)
        if (ds,do,hs)==(0,0,0):
            info['v1_extension']='all zero; inherited nonstandard candidate boot header, not normalized'
        else:
            assert 1648<=hs<=page and do+ds<=len(data)
            info['recovery_dtbo']={'size':ds,'offset':do,'sha256':sha(data[do:do+ds])}
    return info,r,second

def cpio(data):
    pos=0;result={}
    while True:
        assert data[pos:pos+6] in (b'070701',b'070702'),pos
        vals=[int(data[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
        mode,size,namesize=vals[1],vals[6],vals[11]
        name=data[pos+110:pos+110+namesize-1].decode('utf8')
        start=(pos+110+namesize+3)//4*4;content=data[start:start+size]
        assert len(content)==size
        pos=(start+size+3)//4*4
        if name=='TRAILER!!!':break
        assert name not in result
        result[name]=(mode,content)
    return result

boot,_,bootdt=parse(ROOT/'rom-simplificada/inspeccion/boot-original.img')
rec,ram,dt=parse(ROOT/'rom-simplificada/inspeccion/recovery-original.img')
assert ram[:2]==b'\x1f\x8b'
files=cpio(gzip.decompress(ram))
selected={}
for name,(mode,data) in files.items():
    if mode&0xf000!=0x8000:continue
    if name.endswith(('.rc','.prop','.fstab','.sh')) or name in ('default.prop','etc/recovery.fstab','res/keys'):
        assert len(data)<200000
        safe=OUT/name
        assert safe.resolve().is_relative_to(OUT.resolve())
        safe.parent.mkdir(parents=True,exist_ok=True);safe.write_bytes(data)
        selected[name]=sha(data)
binary=files.get('sbin/recovery',files.get('system/bin/recovery'))
assert binary
strings=[b.decode('ascii') for b in re.findall(rb'[\x20-\x7e]{8,}',binary[1])
         if any(k in b.lower() for k in (b'update_package',b'/udisk',b'/usb',b'/cache/recovery',b'autoupdate',b'aml_autoscript',b'apply update',b'gxlx',b'p291',b'/res/keys'))]
(OUT/'recovery-strings.json').write_text(json.dumps(strings,indent=2),encoding='utf8')
report={'source':'community candidate, not installed recovery','boot':boot,'recovery':rec,
        'same_kernel_as_candidate_boot':boot['kernel_sha256']==rec['kernel_sha256'],
        'same_secondary_as_candidate_boot':bootdt==dt,'ramdisk_files':len(files),
        'metadata':selected,'selected_recovery_strings':strings,
        'hardware_boot_confirmed':False}
(OUT/'informe.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('metadata',)},indent=2))
