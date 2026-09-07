"""Read-only firmware-data inspection; writes reports/extracted data only beside this script.
Container layout reference: https://github.com/7Ji/ampack/blob/master/src/image.rs
Does not execute firmware or access any device.
"""
import hashlib, json, mmap, re, shutil, struct, tarfile, zlib
from pathlib import Path

root = Path(__file__).resolve().parent
metadata = json.loads((root / 'origen-github.json').read_text(encoding='utf-8-sig'))
archive = root / metadata['name']
sha = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
assert 'sha256:' + sha == metadata['digest'], 'Archive SHA-256 differs from GitHub'
report = {'origen': metadata, 'sha256_verificado': sha, 'compatibilidad': 'NO CONFIRMADA', 'metodo': 'Analisis estatico de bytes; no ejecuta componentes ni escribe dispositivos', 'contenido_tar': []}
imagepath = root / 'candidato-android9.img'
with tarfile.open(archive, 'r:xz', encoding='utf-8', errors='replace') as tar:
    for entry in tar:
        report['contenido_tar'].append({'nombre': entry.name, 'bytes': entry.size, 'archivo_regular': entry.isfile()})
        if entry.isfile() and entry.name.lower().endswith('.img'):
            if not imagepath.exists():
                with tar.extractfile(entry) as inp, imagepath.open('xb') as out:
                    shutil.copyfileobj(inp, out, 4 * 1024 * 1024)
            else:
                assert imagepath.stat().st_size == entry.size, 'Existing image size mismatch'
            report['img_nombre_original'] = entry.name
print('Archive SHA verified and image extracted', flush=True)
with imagepath.open('rb') as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
    crc, version, magic, total, align, count = struct.unpack_from('<IIIQII', data)
    assert magic == 0x27b51956 and version in (1, 2) and total == len(data) and count < 1024
    width = 32 if version == 1 else 256
    recordsize = 64 + 2 * width
    assert 64 + recordsize * count <= len(data)
    report['contenedor'] = {'version': version, 'magic': hex(magic), 'bytes': total, 'items': count, 'alineacion': align, 'crc_declarado_no_verificado': hex(crc)}
    report['partes'] = []
    dtb_blobs = []
    for index in range(count):
        base = 64 + index * recordsize
        itemid, filetype, current, offset, size = struct.unpack_from('<IIQQQ', data, base)
        main = data[base+32:base+32+width].split(b'\0',1)[0].decode('ascii','replace')
        sub = data[base+32+width:base+32+2*width].split(b'\0',1)[0].decode('ascii','replace')
        assert offset <= len(data) and size <= len(data) - offset
        info = {'id': itemid, 'tipo': main, 'nombre': sub, 'offset': offset, 'bytes': size, 'formato_archivo': filetype}
        report['partes'].append(info)
        if 'dtb' in sub.lower() and main != 'VERIFY' and size < 16*1024*1024:
            blob = data[offset:offset+size]
            if blob.startswith(b'\x1f\x8b'):
                decoder = zlib.decompressobj(31)
                blob = decoder.decompress(blob, 32*1024*1024)
                assert len(blob) < 32*1024*1024
                info['gzip_fin_verificado'] = decoder.eof
                if not decoder.eof:
                    info['nota_gzip'] = 'El elemento entrega datos descomprimidos pero no contiene un fin gzip completo; no se acredita integridad gzip interna.'
            (root / ('datos-dtb-' + str(index) + '.bin')).write_bytes(blob)
            dtb_blobs.append((sub, blob))
    report['propiedades_texto_en_img'] = []
    for pattern in [rb'ro\.(?:build|vendor\.build|system\.build)\.version\.(?:release|sdk|security_patch)=[^\r\n\x00]{1,100}', rb'ro\.product\.(?:board|device|model|cpu\.abi|cpu\.abilist|name)=[^\r\n\x00]{1,120}', rb'ro\.treble\.enabled=[^\r\n\x00]{1,20}', rb'ro\.build\.fingerprint=[^\r\n\x00]{1,200}']:
        for hit in re.finditer(pattern, data):
            report['propiedades_texto_en_img'].append({'offset': hit.start(), 'texto': hit.group().decode('ascii','replace')})
    report['identificadores_en_img'] = {}
    for marker in [b'gxlx2_p291_1g', b'P05L', b'5V300A1', b'1C11H16M', b'MT7668', b'MT7661']:
        offsets = []; pos = data.find(marker)
        while pos >= 0 and len(offsets) < 50:
            offsets.append(pos); pos = data.find(marker, pos+len(marker))
        report['identificadores_en_img'][marker.decode()] = offsets
    report['dtb_propiedades'] = []
    for label, blob in dtb_blobs:
        pos = blob.find(b'\xd0\x0d\xfe\xed')
        while pos >= 0:
            if pos + 40 > len(blob): break
            hdr = struct.unpack_from('>10I', blob, pos)
            _, dtlen, offstruct, offstrings, _, ver, _, _, sizestrings, sizestruct = hdr
            if dtlen < 40 or pos+dtlen > len(blob) or offstrings+sizestrings > dtlen or offstruct+sizestruct > dtlen:
                pos = blob.find(b'\xd0\x0d\xfe\xed', pos+4); continue
            strings = blob[pos+offstrings:pos+offstrings+sizestrings]
            p = pos+offstruct; end = p+sizestruct; stack=[]; props=[]
            while p+4 <= end:
                token = struct.unpack_from('>I',blob,p)[0]; p+=4
                if token == 1:
                    stop=blob.find(b'\0',p,end); assert stop >= 0
                    stack.append(blob[p:stop].decode('ascii','replace')); p=(stop+4)&~3
                elif token == 2:
                    if stack: stack.pop()
                elif token == 3:
                    length, nameoff = struct.unpack_from('>II',blob,p); p+=8
                    assert p+length<=end and nameoff<len(strings)
                    name=strings[nameoff:].split(b'\0',1)[0].decode('ascii','replace')
                    value=blob[p:p+length]; p=(p+length+3)&~3
                    if re.search(r'amlogic-dt-id|compatible|model|memory|ddr|reg|status',name) and (len(stack)<3 or re.search(r'memory|ddr', '/'.join(stack),re.I)):
                        text=value.rstrip(b'\0').decode('ascii','replace') if all(c in (0,9,10,13) or 32<=c<127 for c in value) else 'hex:'+value.hex()
                        props.append({'ruta':'/'.join(stack) or '/', 'propiedad':name, 'valor':text})
                elif token == 4: continue
                elif token == 9: break
                else: break
            report['dtb_propiedades'].append({'item':label,'offset':pos,'bytes':dtlen,'version':ver,'propiedades':props})
            pos=blob.find(b'\xd0\x0d\xfe\xed',pos+dtlen)
report['limites'] = ['La coincidencia del DTB no acredita compatibilidad de placa, RAM, bootloader ni todos los perifericos.', 'Las propiedades de Android se localizaron como texto sin montar el sistema; pueden existir copias para recovery o valores configurados por el fabricante.', 'CRC interno, configuracion DDR y funcionamiento de drivers no verificados; no se ha flasheado.']
(root/'informe-inspeccion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps({key: report[key] for key in ['contenedor','partes','propiedades_texto_en_img','identificadores_en_img','dtb_propiedades']},ensure_ascii=True,indent=2))
