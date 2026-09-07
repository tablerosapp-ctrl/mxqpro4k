"""Static verification only; no firmware code execution or device access.
References: 7Ji/ampack src/image.rs, src/crc32.rs, src/sha1sum.rs.
"""
import hashlib, json, mmap, struct, zlib
from pathlib import Path

root = Path(__file__).resolve().parent
report = {'referencias': ['https://github.com/7Ji/ampack/blob/master/src/image.rs', 'https://github.com/7Ji/ampack/blob/master/src/crc32.rs', 'https://github.com/7Ji/ampack/blob/master/src/sha1sum.rs']}
with (root/'candidato-android9.img').open('rb') as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
    recorded, version, magic, size, align, count = struct.unpack_from('<IIIQII', data)
    assert version == 2 and magic == 0x27b51956 and size == len(data)
    crc = 0
    imagehash = hashlib.sha256()
    imagehash.update(data[:4])
    for pos in range(4,len(data),4*1024*1024):
        chunk=data[pos:pos+4*1024*1024]; crc=zlib.crc32(chunk,crc); imagehash.update(chunk)
    # AMpack starts with all bits set and does not apply the final XOR.
    calculated = crc ^ 0xffffffff
    report['img_sha256'] = imagehash.hexdigest()
    report['crc32_contenedor'] = {'declarado':hex(recorded),'calculado':hex(calculated),'coincide':recorded==calculated,'rango':'Desde byte 4 al final; polinomio 0xedb88320, inicio ffffffff, sin XOR final'}
    records=[]
    for i in range(count):
        base=64+i*576
        id_,type_,current,offset,length=struct.unpack_from('<IIQQQ',data,base)
        main=data[base+32:base+288].split(b'\0',1)[0].decode('ascii')
        sub=data[base+288:base+544].split(b'\0',1)[0].decode('ascii')
        verify,backup,backup_id=struct.unpack_from('<IHH',data,base+544)
        assert offset+length<=len(data)
        records.append({'id':id_,'tipo':main,'nombre':sub,'offset':offset,'bytes':length,'verify_flag':verify,'backup':backup,'backup_id':backup_id})
    report['registros'] = records
    report['sha1_particiones'] = []
    for i, part in enumerate(records):
        if part['tipo']!='PARTITION': continue
        assert part['verify_flag']==1
        verify=records[i+1]
        assert verify['tipo']=='VERIFY' and verify['nombre']==part['nombre'] and verify['bytes']==48 and verify['verify_flag']==0
        value=data[verify['offset']:verify['offset']+48]
        assert value.startswith(b'sha1sum ')
        declared=value[8:].decode('ascii')
        sha=hashlib.sha1()
        for pos in range(part['offset'],part['offset']+part['bytes'],4*1024*1024):
            sha.update(data[pos:min(pos+4*1024*1024,part['offset']+part['bytes'])])
        report['sha1_particiones'].append({'nombre':part['nombre'],'declarado':declared,'calculado':sha.hexdigest(),'coincide':declared==sha.hexdigest()})
    part=next(p for p in records if p['tipo']=='PARTITION' and p['nombre']=='_aml_dtb')
    raw=data[part['offset']:part['offset']+part['bytes']]
    decomp=zlib.decompressobj(31)
    expanded=decomp.decompress(raw,32*1024*1024)
    report['dtb_gzip']={'offset':part['offset'],'bytes_declarados':part['bytes'],'primeros32_hex':raw[:32].hex(),'ultimos32_hex':raw[-32:].hex(),'bytes_descomprimidos':len(expanded),'eof':decomp.eof,'datos_sin_consumir':len(decomp.unconsumed_tail),'datos_sobrantes':len(decomp.unused_data),'sha256_descomprimido':hashlib.sha256(expanded).hexdigest()}
    try:
        zlib.decompress(raw,31)
        report['dtb_gzip']['comprobacion_zlib_completa']='correcta'
    except zlib.error as error:
        report['dtb_gzip']['comprobacion_zlib_completa']=str(error)
    expected_trailer=struct.pack('<II',zlib.crc32(expanded),len(expanded)&0xffffffff)
    report['dtb_gzip']['trailer_gzip_esperado_hex']=expected_trailer.hex()
    report['dtb_gzip']['termina_en_primeros7_bytes_trailer']=raw.endswith(expected_trailer[:7])
    # A diagnostic on a temporary in-memory buffer only: never alter the firmware.
    try:
        completed=zlib.decompress(raw+b'\x00',31)
        report['dtb_gzip']['prueba_un_cero_solo_en_memoria']={'gzip_valido':True,'datos_identicos':completed==expanded,'nota':'Se agrego un byte 00 a un buffer temporal para localizar el truncamiento. La IMG y el gzip original no se modificaron.'}
    except zlib.error as error:
        report['dtb_gzip']['prueba_un_cero_solo_en_memoria']={'gzip_valido':False,'error':str(error)}
    expected_next=next(p for p in records if p['id']==3)
    report['dtb_gzip']['siguiente_elemento'] = expected_next
    report['dtb_gzip']['offset_siguiente_coincide_fin_dtb']=expected_next['offset']==part['offset']+part['bytes']
    (root/'dtb-comprimido-original.gz').write_bytes(raw)
    report['configuracion_plataforma'] = []
    for part in records:
        if part['tipo'] in ('conf','ini') and part['bytes'] < 4096:
            report['configuracion_plataforma'].append({'tipo':part['tipo'],'nombre':part['nombre'],'contenido':data[part['offset']:part['offset']+part['bytes']].decode('utf-8','replace')})
report['conclusion'] = 'Los resultados distinguen identidad del archivo, integridad del contenedor y completitud gzip. Ninguna comprobacion acredita compatibilidad de hardware.'
(root/'integridad-interna.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:report[key] for key in ['crc32_contenedor','sha1_particiones','dtb_gzip','configuracion_plataforma']},ensure_ascii=True,indent=2))
