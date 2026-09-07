"""Read a previously collected proc/device-tree tar as data; no ADB/device access."""
import hashlib, json, re, struct, tarfile
from pathlib import Path, PurePosixPath
root=Path(__file__).resolve().parent
archive=root/'devicetree-del-segundo-tv.tar'
nodes={}
entries=0
with tarfile.open(archive,'r:') as tar:
    for entry in tar:
        entries+=1
        if not entry.isfile(): continue
        path=PurePosixPath(entry.name)
        assert '..' not in path.parts and not path.is_absolute() and entry.size<1024*1024
        value=tar.extractfile(entry).read()
        nodes.setdefault('/'+str(path.parent).removeprefix('.').strip('/'),{})[path.name]=value

def u32(value): return list(struct.unpack('>'+str(len(value)//4)+'I',value)) if value and len(value)%4==0 else []
def decode(value):
    result={'bytes':len(value),'hex':value.hex()}
    if value and all(c==0 or c in (9,10,13) or 32<=c<127 for c in value): result['texto']=value.rstrip(b'\0').decode('ascii')
    if len(value)%4==0: result['celdas_u32_be']=u32(value)
    return result

def regions(path,props):
    parent=str(PurePosixPath(path).parent)
    parentprops=nodes.get(parent,{})
    ac=u32(parentprops.get('#address-cells',nodes.get('/',{}).get('#address-cells',b'\x00\x00\x00\x02')))[0]
    sc=u32(parentprops.get('#size-cells',nodes.get('/',{}).get('#size-cells',b'\x00\x00\x00\x01')))[0]
    values=u32(props.get('reg',b'')); result=[]
    if not values or ac+sc<=0 or len(values)%(ac+sc): return result
    for i in range(0,len(values),ac+sc):
        addr=0; size=0
        for v in values[i:i+ac]: addr=(addr<<32)|v
        for v in values[i+ac:i+ac+sc]: size=(size<<32)|v
        result.append({'direccion':hex(addr),'bytes':size,'MiB':size/1048576})
    return result

selected={path:{key:decode(value) for key,value in props.items()} for path,props in nodes.items() if re.search(r'(^/$|memory|ddr|mali|vpu|vdec|codec_mm|amhdmitx|wifi|sdio|bt-dev|ethernet|emmc)',path)}
memory=[]
for path,props in nodes.items():
    if path.startswith('/reserved-memory/') or path.startswith('/memory'):
        info={'ruta':path,'regiones':regions(path,props),'propiedades':{k:decode(v) for k,v in props.items() if k in ['compatible','size','reg','reusable','no-map','linux,cma-default','alloc-ranges','status','alignment','device_type']}}
        for key in ('size','alignment'):
            cells=u32(props.get(key,b''))
            if cells:
                num=0
                for cell in cells:num=(num<<32)|cell
                info[key+'_bytes']=num
                info[key+'_MiB']=num/1048576
        memory.append(info)
properties={}
for line in (root/'propiedades.txt').read_text(encoding='utf-8-sig').splitlines():
    if line.startswith('ro.') and '=' in line:
        key,value=line.split('=',1);properties[key]=value
meminfo={}
for key,val in re.findall(r'^([A-Za-z_()]+):\s+(\d+) kB', (root/'memoria.txt').read_text(encoding='utf-8-sig'),re.M):
    meminfo[key]={'kB':int(val),'MiB':int(val)/1024}
report={'equipo':'Segundo TV box, conectado solo para diagnostico; no confundir con el original P291','origen_tar':archive.name,'sha256_tar':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'entradas_tar':entries,'nodos_con_propiedades':len(nodes),'dt_id':nodes['/']['amlogic-dt-id'].rstrip(b'\0').decode(),'propiedades_android':properties,'memoria_observada':meminfo,'memoria_dt':memory,'nodos_relevantes':selected,'kernel':(root/'kernel.txt').read_text(encoding='utf-8-sig'),'gpu':(root/'gpu.txt').read_text(encoding='utf-8-sig'),'limites':['Device tree es configuracion declarada del kernel; compatible WiFi no identifica por si solo el chip fisico.','CMA es memoria administrada por Linux; no restar CmaTotal entero de MemTotal como perdida adicional.','No se recolectaron /proc/modules ni enlaces driver del dispositivo WiFi en los archivos disponibles.','Un catalogo XML de codecs no prueba que VP9 este activo ni acelerado en una reproduccion real.']}
driverfile=root/'controladores-activos.txt'
if driverfile.exists():
    drivertext=driverfile.read_text(encoding='utf-8-sig')
    report['controladores_activos']={'fuente':driverfile.name,'modulos_cargados':re.findall(r'^(\S+) \d+ \d+ .* Live ',drivertext,re.M),'wifi':{'driver':'rtl88x2bs','modulo':'8822bs','vendor_sdio':'0x024c','device_sdio':'0xb822','modalias':'sdio:c07v024CdB822','evidencia_enlace_driver':'bus/sdio/drivers/rtl88x2bs'},'bibliotecas_vendor_relevantes':[name for name in ['libGLES_mali.so','gralloc.amlogic.so','hwcomposer.amlogic.so'] if name in drivertext],'limite':'Modulo cargado e identificador SDIO acreditan software enlazado; VP9/alpha efectivo en WebView exige una reproduccion instrumentada.'}
    report['limites']=[text for text in report['limites'] if not text.startswith('No se recolectaron')]
report['diferencias_candidato_p291']={'dt_id_segundo_tv':'gxlx_p271_1g','dt_id_candidato':'gxlx2_p291_1g','producto_segundo_tv':'Droidlogic/ampere','producto_candidato':'Fiberhome/p291_iptv','comun':['Android9/SDK28','armeabi-v7a','arm,mali-450'],'conclusion':'La coincidencia de Android y GPU no acredita que bootloader, DDR, DTB, WiFi ni HAL sean intercambiables.'}
report['memoria_observacion']='El nodo DT memory@00000000 declara896MiB, pero MemTotal observado983.42MiB es mayor. La captura no basta para explicar esa diferencia; no inferir capacidad fisica ni sumar reservas sobre MemTotal.'
(root/'perfil-segundo-tv.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
brief={'dt_id':report['dt_id'],'memoria_observada':{k:meminfo[k] for k in ['MemTotal','MemAvailable','CmaTotal','CmaFree','SwapTotal']},'memoria_dt':memory,'wifi_gpu_video':{k:v for k,v in selected.items() if re.search('wifi|mali|vpu|vdec|amhdmitx|bt-dev',k)}}
print(json.dumps(brief,ensure_ascii=True,indent=2))
