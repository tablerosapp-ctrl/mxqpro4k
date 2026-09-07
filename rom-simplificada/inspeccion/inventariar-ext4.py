"""Read-only Android sparse/ext4 inventory from the verified Amlogic container.
No mounts, firmware execution, devices or source-image mutations.
References: kernel.org/doc/html/latest/filesystems/ext4/{super,inodes,ifork,group_descr}.html
Android sparse header: android.googlesource.com/platform/system/core/+/main/libsparse/sparse_format.h
"""
import bisect, hashlib, json, mmap, re, struct, subprocess, uuid
from pathlib import Path, PurePosixPath

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
IMAGE=ROOT/'analisis-rom/candidato-android9.img'
EXPECTED='bd8a8d9c02f6aa1119e5ea7708f2b49a1e4c7fef6169d30bbd1604981eb042e5'

def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]

class Sparse:
    def __init__(self,data,offset,size):
        self.data=data;self.offset=offset;self.size=size;self.chunks=[]
        raw=data[offset:offset+28]
        self.is_sparse=u32(raw)==0xed26ff3a
        if not self.is_sparse:
            self.logical_size=size;self.chunks=[(0,size,0xcac1,offset)];self.starts=[0];self.meta={'sparse':False,'bytes_logicos':size};return
        magic,major,minor,fhs,chs,bs,blocks,nchunks,checksum=struct.unpack('<IHHHHIIII',raw)
        assert major==1 and 28<=fhs<=4096 and 12<=chs<=4096 and bs in (1024,2048,4096,8192) and nchunks<1000000
        pos=offset+fhs;logical=0;types={}
        for _ in range(nchunks):
            ctype,reserved,nblocks,total=struct.unpack_from('<HHII',data,pos)
            assert chs<=total and pos+total<=offset+size
            clen=nblocks*bs;payload=pos+chs
            if ctype==0xcac1: assert total-chs==clen
            elif ctype==0xcac2: assert total-chs==4
            elif ctype==0xcac3: assert total==chs
            elif ctype==0xcac4: assert total-chs==4 and nblocks==0
            else: raise ValueError('Unknown sparse chunk '+hex(ctype))
            if clen:self.chunks.append((logical,clen,ctype,payload))
            types[hex(ctype)]=types.get(hex(ctype),0)+1
            pos+=total;logical+=clen
        assert logical==blocks*bs and pos==offset+size
        self.logical_size=logical;self.starts=[c[0] for c in self.chunks]
        self.meta={'sparse':True,'version':[major,minor],'bloque':bs,'chunks':nchunks,'tipos_chunks':types,'bytes_logicos':logical,'checksum_declarado':checksum}
    def read(self,pos,size):
        assert pos>=0 and size>=0 and pos+size<=self.logical_size
        out=bytearray()
        while size:
            index=bisect.bisect_right(self.starts,pos)-1
            start,length,ctype,payload=self.chunks[index]
            rel=pos-start;n=min(size,length-rel);assert n>0
            if ctype==0xcac1:out.extend(self.data[payload+rel:payload+rel+n])
            elif ctype==0xcac2:
                fill=self.data[payload:payload+4];out.extend((fill*((n+7)//4))[rel%4:rel%4+n])
            elif ctype==0xcac3:out.extend(b'\0'*n)
            else:raise ValueError('Unsupported data chunk')
            pos+=n;size-=n
        return bytes(out)

class Ext4:
    def __init__(self,reader):
        self.r=reader;sb=reader.read(1024,1024)
        assert u16(sb,56)==0xef53
        self.bs=1024<<u32(sb,24);self.ipg=u32(sb,40);self.isize=u16(sb,88);self.first=u32(sb,20)
        self.incompat=u32(sb,96);self.ro=u32(sb,100);self.descsize=max(32,u16(sb,254)) if self.incompat&0x80 else 32
        assert self.bs in (1024,2048,4096) and self.isize>=128 and not self.incompat&(0x10|0x8000|0x10000) and not self.ro&0x200
        blocks=u32(sb,4)+(u32(sb,336)<<32 if self.incompat&0x80 else 0)
        self.meta={'tipo':'ext4','bloque':self.bs,'bytes_fs':blocks*self.bs,'inodos':u32(sb),'inode_size':self.isize,'descriptor_size':self.descsize,'feature_compat':hex(u32(sb,92)),'feature_incompat':hex(self.incompat),'feature_ro_compat':hex(self.ro),'uuid':str(uuid.UUID(bytes=sb[104:120])),'etiqueta':sb[120:136].split(b'\0',1)[0].decode('utf-8','replace'),'ultimo_montaje':sb[136:200].split(b'\0',1)[0].decode('utf-8','replace'),'inodos_libres':u32(sb,16),'bloques_libres':u32(sb,12)}
        assert blocks*self.bs<=reader.logical_size
    def inode(self,num):
        assert 1<=num<=self.meta['inodos'];group=(num-1)//self.ipg;index=(num-1)%self.ipg
        gd=self.r.read((self.first+1)*self.bs+group*self.descsize,self.descsize)
        table=u32(gd,8)+(u32(gd,40)<<32 if self.descsize>=64 else 0)
        raw=self.r.read(table*self.bs+index*self.isize,self.isize)
        return {'inode':num,'modo':u16(raw),'uid':u16(raw,2)+(u16(raw,120)<<16),'gid':u16(raw,24)+(u16(raw,122)<<16),'bytes':u32(raw,4)+(u32(raw,108)<<32),'flags':u32(raw,32),'raw':raw,'acl_block':u32(raw,104)+(u16(raw,118)<<32)}
    def extents(self,node,depth=0):
        magic,entries,maximum,level,generation=struct.unpack_from('<HHHHI',node)
        assert magic==0xf30a and level<=5 and depth<=5 and entries<=maximum and 12+entries*12<=len(node)
        for i in range(entries):
            b=12+i*12
            if level:
                logical,low,high,unused=struct.unpack_from('<IIHH',node,b)
                yield from self.extents(self.r.read((low+(high<<32))*self.bs,self.bs),depth+1)
            else:
                logical,length,high,low=struct.unpack_from('<IHHI',node,b)
                unwritten=length>32768
                yield (logical*self.bs,(length-32768 if unwritten else length)*self.bs,(low+(high<<32))*self.bs,unwritten)
    def content(self,inode,limit=256*1024*1024):
        size=inode['bytes'];assert size<=limit
        if inode['modo']&0xf000==0xa000 and size<=60:return inode['raw'][40:40+size]
        if not size:return b''
        if not inode['flags']&0x80000:
            assert size<=12*self.bs, 'Indirect block data not supported in bounded reader'
            out=bytearray()
            for index in range((size+self.bs-1)//self.bs):
                block=u32(inode['raw'],40+index*4)
                out.extend(self.r.read(block*self.bs,self.bs) if block else b'\0'*self.bs)
            return bytes(out[:size])
        result=bytearray(size)
        for logical,length,physical,unwritten in self.extents(inode['raw'][40:100]):
            n=min(length,max(0,size-logical))
            if n and not unwritten:result[logical:logical+n]=self.r.read(physical,n)
        return bytes(result)
    def entries(self,inode):
        data=self.content(inode,16*1024*1024);pos=0
        while pos+8<=len(data):
            ino,length,nlen,typ=struct.unpack_from('<IHBB',data,pos)
            assert length>=8 and length%4==0 and pos+length<=len(data) and nlen<=length-8
            if ino:
                name=data[pos+8:pos+8+nlen].decode('utf-8','strict')
                if name not in ('.','..'):
                    assert '/' not in name and '\\' not in name and '\0' not in name
                    yield name,ino,typ
            pos+=length
    def walk(self):
        seen=set();stack=[('',self.inode(2),0)]
        while stack:
            path,node,depth=stack.pop();assert depth<64 and len(seen)<200000
            if path:yield path,node
            if node['modo']&0xf000!=0x4000:continue
            assert node['inode'] not in seen;seen.add(node['inode'])
            for name,ino,typ in self.entries(node):stack.append((path+'/'+name,self.inode(ino),depth+1))

def main():
    assert hashlib.file_digest(IMAGE.open('rb'),'sha256').hexdigest()==EXPECTED
    table=json.loads((ROOT/'analisis-rom/integridad-interna.json').read_text(encoding='utf-8-sig'))['registros']
    aapt=ROOT/'tools/verificacion-apk/build-tools-37/android-37.0/aapt.exe'
    report={'fuente':str(IMAGE),'sha256_fuente':EXPECTED,'solo_lectura':True,'particiones':{},'apks':[],'limites':['Lector de inventario, no fsck: no valida checksums ext4 ni reconstruye xattrs/SELinux. No usarlo como escritor de sistemas de archivos.','APK analizadas por aapt como datos; ninguna se instalo ni ejecuto.']}
    with IMAGE.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
        for part in table:
            if part['tipo']!='PARTITION' or part['nombre'] not in ['system','vendor','product','odm','vbmeta','boot','recovery']:continue
            name=part['nombre'];reader=Sparse(data,part['offset'],part['bytes'])
            if name in ['vbmeta','boot','recovery']:
                dest=HERE/(name+'-original.img');dest.write_bytes(reader.read(0,reader.logical_size))
                report['particiones'][name]={'contenedor':part,'imagen':reader.meta,'extraida':str(dest)};continue
            fs=Ext4(reader);inventory=[];metadata_count=0;apks_count=0
            for path,node in fs.walk():
                item={k:v for k,v in node.items() if k!='raw'};item['ruta']=path;item['modo']=oct(item['modo']);inventory.append(item)
                if node['modo']&0xf000==0xa000:
                    item['enlace']=fs.content(node).decode('utf-8','replace');continue
                if node['modo']&0xf000!=0x8000:continue
                is_apk=path.lower().endswith('.apk')
                is_meta=(node['bytes']<4*1024*1024 and (path.endswith(('build.prop','.rc','.xml','.conf','.sh')) or any(x in path for x in ['fstab','file_contexts','fs_config','permissions','selinux'])))
                if not is_apk and not is_meta:continue
                relative=PurePosixPath(path.lstrip('/'));assert '..' not in relative.parts
                dest=HERE/('apks' if is_apk else 'metadatos')/name/Path(*relative.parts)
                assert dest.resolve().is_relative_to(HERE.resolve());dest.parent.mkdir(parents=True,exist_ok=True)
                content=fs.content(node);dest.write_bytes(content)
                if is_apk:
                    apk={'particion':name,'ruta':path,'archivo_local':str(dest),'bytes':node['bytes'],'sha256':hashlib.sha256(content).hexdigest()}
                    if aapt.exists():
                        proc=subprocess.run([str(aapt),'dump','badging',str(dest)],capture_output=True,timeout=30,creationflags=0x08000000)
                        output=proc.stdout.decode('utf-8','replace');dest.with_suffix('.badging.txt').write_text(output,encoding='utf-8')
                        apk['aapt_exit']=proc.returncode
                        for key,pattern in [('paquete',r"package: name='([^']+)'"),('version',r"versionName='([^']*)'"),('min_sdk',r"sdkVersion:'([^']*)'"),('etiqueta',r"application-label:'([^']*)'")]:
                            match=re.search(pattern,output);apk[key]=match.group(1) if match else None
                    report['apks'].append(apk);apks_count+=1
                else:metadata_count+=1
            (HERE/(name+'-inventario.json')).write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
            report['particiones'][name]={'contenedor':part,'imagen':reader.meta,'fs':fs.meta,'entradas':len(inventory),'apks':apks_count,'metadatos_extraidos':metadata_count}
            print(name, len(inventory),'entries',apks_count,'APK',flush=True)
    (HERE/'inventario-rom.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'particiones':report['particiones'],'apks':[{k:v for k,v in apk.items() if k not in ['sha256','archivo_local']} for apk in report['apks']]},ensure_ascii=True,indent=2))

if __name__=='__main__':main()
