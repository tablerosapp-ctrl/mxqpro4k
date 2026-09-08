"""Inspección local RKFW/RKAF. No ejecuta imágenes ni accede a dispositivos.

Referencia estructural: rockchip-linux/rkdeveloptool/RKImage.h y
rockchip-android/bootable-recovery/rk3399-box-7.1/rkimage.h.
Conserva sólo miembros seleccionados, a nombres propios en una carpeta nueva.
SHA comprueba adquisición; no autentica al fabricante ni valida compatibilidad.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import struct

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / 'privado'
SELECT = {'package-file', 'parameter', 'boot', 'recovery'}


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    src = Path(args.image).absolute()
    out = Path(args.output).absolute()
    assert src.is_file() and src.resolve() == src and src.is_relative_to(ROOT)
    assert out.is_relative_to(PRIVATE) and out != PRIVATE and not out.exists()
    assert out.parent.is_dir() and out.parent.resolve() == out.parent
    before = src.stat()
    sha = digest(src)
    with src.open('rb') as f:
        head = f.read(102)
        assert head[:4] == b'RKFW' and struct.unpack_from('<H', head, 4)[0] == 102
        boot_offset, boot_size, fw_offset, fw_size = struct.unpack_from('<4I', head, 25)
        assert boot_offset >= 102 and boot_size > 0 and fw_size > 2048
        assert boot_offset + boot_size <= fw_offset and fw_offset + fw_size <= before.st_size
        f.seek(fw_offset)
        af = f.read(2048)
        assert af[:4] == b'RKAF'
        af_size = struct.unpack_from('<I', af, 4)[0]
        assert af_size + 4 == fw_size
        count = struct.unpack_from('<I', af, 136)[0]
        assert 0 < count <= 16 and 140 + count * 112 <= len(af)
        rows = []
        seen = set()
        ranges = []
        for i in range(count):
            item = af[140+i*112:140+(i+1)*112]
            name = item[:32].split(b'\0', 1)[0].decode('ascii')
            declared_path = item[32:96].split(b'\0', 1)[0].decode('ascii')
            offset, flash_offset, sectors, size = struct.unpack_from('<4I', item, 96)
            assert name not in seen
            seen.add(name)
            assert offset <= af_size and size <= af_size and offset + size <= af_size
            if size:
                assert offset >= 2048
                ranges.append((offset, offset+size))
            rows.append(dict(name=name, declared_path=declared_path,
                             package_offset=offset, declared_flash_offset=flash_offset,
                             declared_sectors=sectors, bytes=size, extracted=False))
        ranges.sort()
        assert all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:]))
        out.mkdir()
        for row in rows:
            if row['name'] not in SELECT or not row['bytes']:
                continue
            assert row['bytes'] <= 64*1024*1024
            f.seek(fw_offset + row['package_offset'])
            data = f.read(row['bytes'])
            assert len(data) == row['bytes']
            dst = out / (row['name'] + '.payload')
            with dst.open('xb') as w:
                assert w.write(data) == len(data)
                w.flush()
                os.fsync(w.fileno())
            h = hashlib.sha256(data).hexdigest()
            assert digest(dst) == h
            row.update(extracted=True, output_file=dst.name, sha256=h)
    after = src.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    assert digest(src) == sha
    result = dict(schema='tvbase-rkfw-static-inspection-1', state='selected_members_readback_verified',
                  created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_file=str(src), source_bytes=before.st_size, source_sha256=sha,
                  firmware_offset=fw_offset, firmware_bytes=fw_size, entries=rows,
                  source_unchanged=True, firmware_executed=False, tv_or_media_contacted=False,
                  package_authenticity_verified=False, physical_compatibility_verified=False,
                  directory_sync_verified=False)
    with (out/'INSPECCION.json').open('x', encoding='utf-8', newline='\n') as w:
        json.dump(result, w, ensure_ascii=False, indent=2)
        w.write('\n'); w.flush(); os.fsync(w.fileno())
    print(json.dumps(dict(state=result['state'], entries=count, extracted=[r['name'] for r in rows if r['extracted']],
                          source_sha256=sha), ensure_ascii=False))


if __name__ == '__main__':
    main()
