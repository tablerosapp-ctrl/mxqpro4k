"""Read-only final composition and free-block verification of local P291 images."""
import hashlib
import io
import json
import struct
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import construir as builder

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sparse_super_group(group):
    """The supported sparse_super profile uses groups 0, 1 and powers of 3/5/7."""
    if group in (0, 1):
        return True
    for base in (3, 5, 7):
        value = group
        while value > 1 and value % base == 0:
            value //= base
        if value == 1:
            return True
    return False


def effective_free_groups(fs):
    """Reconstruct BLOCK_UNINIT metadata for the exact supported P291 profile.

    On-disk bitmaps in an uninitialized group are not authoritative. All bitmap
    and inode-table locations come from the complete descriptor table, including
    metadata moved across groups by flex_bg. Backup superblocks, GDT copies and
    reserved GDT blocks are added separately. No whole group is skipped.
    References: kernel.org/doc/html/latest/filesystems/ext4/{bitmaps,group_descr}.html
    """
    sb = fs.r.read(1024, 1024)
    u16 = lambda data, offset: struct.unpack_from('<H', data, offset)[0]
    u32 = lambda data, offset: struct.unpack_from('<I', data, offset)[0]
    assert not fs.r.is_sparse, 'Zero-byte guarantee requires a raw image'
    assert fs.bs == 4096 and fs.first == 0 and fs.descsize == 32
    assert (u32(sb, 92), u32(sb, 96), u32(sb, 100)) == (0x38, 0x242, 0x7b), 'Unsupported ext4 features'
    assert u16(sb, 56) == 0xef53 and u32(sb, 24) == 2
    assert u32(sb, 20) == 0 and u16(sb, 88) == fs.isize and fs.isize in (128, 256)
    per_group, count = u32(sb, 32), u32(sb, 4)
    assert per_group == fs.bs * 8 and 0 < count <= 0xffffffff
    assert count * fs.bs == fs.meta['bytes_fs'] == fs.r.logical_size
    assert u32(sb, 40) == fs.ipg and fs.ipg > 0
    groups = (count - fs.first + per_group - 1) // per_group
    gdt_blocks = (groups * fs.descsize + fs.bs - 1) // fs.bs
    reserved_gdt = u16(sb, 206)
    inode_blocks = (fs.ipg * fs.isize + fs.bs - 1) // fs.bs
    metadata, descriptors = set(), []
    for group in range(groups):
        raw = fs.r.read((fs.first + 1) * fs.bs + group * fs.descsize, fs.descsize)
        block_bitmap, inode_bitmap, inode_table = (u32(raw, offset) for offset in (0, 4, 8))
        flags, declared_free = u16(raw, 18), u16(raw, 12)
        assert not flags & ~0x7, ('Unsupported group flags', group, flags)
        assert 0 < block_bitmap < count and 0 < inode_bitmap < count
        assert 0 < inode_table < count and inode_table + inode_blocks <= count
        metadata.update((block_bitmap, inode_bitmap))
        metadata.update(range(inode_table, inode_table + inode_blocks))
        start = fs.first + group * per_group
        end = min(start + per_group, count)
        if sparse_super_group(group):
            reserved_end = start + 1 + gdt_blocks + reserved_gdt
            assert reserved_end <= end, ('Metadata exceeds group', group)
            metadata.update(range(start, reserved_end))
        assert declared_free <= end - start
        descriptors.append((group, start, end, block_bitmap, flags, declared_free))
    assert sum(row[-1] for row in descriptors) == u32(sb, 12) == fs.meta['bloques_libres']
    for group, start, end, bitmap_block, flags, declared_free in descriptors:
        reserved = metadata.intersection(range(start, end))
        if flags & 0x2:  # EXT4_BG_BLOCK_UNINIT: synthesize, never trust raw bitmap.
            free = [number for number in range(start, end) if number not in reserved]
        else:
            bitmap = fs.r.read(bitmap_block * fs.bs, fs.bs)
            free = [number for number in range(start, end)
                    if not bitmap[(number-start)//8] & (1 << ((number-start) % 8))]
            assert not reserved.intersection(free), ('Metadata marked free', group)
        assert len(free) == declared_free, ('Group free-count mismatch', group, len(free), declared_free)
        yield group, free, flags, len(reserved)


def verify_zero_blocks(reader, block_size, numbers, part, group):
    for number in numbers:
        assert not any(reader.read(number * block_size, block_size)), ('Nonzero free block', part, group, number)


def self_test():
    """Synthetic vendor geometry; no image or receipt is opened or changed."""
    from types import SimpleNamespace
    bs, count, per_group, groups = 4096, 230400, 32768, 8
    data = bytearray(75 * bs)
    put32 = lambda offset, value: struct.pack_into('<I', data, offset, value)
    put16 = lambda offset, value: struct.pack_into('<H', data, offset, value)
    for offset, value in {4: count, 12: 178848, 20: 0, 24: 2, 32: per_group,
                          40: 7200, 92: 0x38, 96: 0x242, 100: 0x7b}.items():
        put32(1024 + offset, value)
    for offset, value in {56: 0xef53, 88: 256, 206: 56}.items():
        put16(1024 + offset, value)
    flags = (0, 1, 1, 1, 3, 3, 3, 1)
    declared = (870, 13290, 32768, 32708, 32768, 32710, 32768, 966)
    metadata = set(range(0, 58)) | set(range(58, 74)) | set(range(74, 3674))
    for group in (1, 3, 5, 7):
        metadata.update(range(group * per_group, group * per_group + 58))
    for group in range(groups):
        descriptor = bs + group * 32
        for offset, value in ((0, 58+group), (4, 66+group), (8, 74+450*group)):
            put32(descriptor + offset, value)
        put16(descriptor + 12, declared[group])
        put16(descriptor + 18, flags[group])
        if flags[group] & 2:
            continue
        bitmap = bytearray(b'\xff' * bs)
        start, end = group * per_group, min((group+1) * per_group, count)
        free = [number for number in range(start, end) if number not in metadata][-declared[group]:]
        for number in free:
            index = number - start
            bitmap[index//8] &= ~(1 << (index % 8))
        data[(58+group)*bs:(59+group)*bs] = bitmap

    class FixtureReader:
        is_sparse = False
        logical_size = count * bs
        dirty = None

        def read(self, offset, size):
            assert 0 <= offset <= offset + size <= self.logical_size
            if offset < len(data):
                return bytes(data[offset:offset+size]).ljust(size, b'\0')
            if self.dirty is not None and offset <= self.dirty * bs < offset + size:
                result = bytearray(size)
                result[self.dirty * bs-offset] = 1
                return bytes(result)
            return b'\0' * size

    reader = FixtureReader()
    fs = SimpleNamespace(r=reader, bs=bs, first=0, descsize=32, isize=256, ipg=7200,
                         meta={'bytes_fs':count*bs, 'bloques_libres':178848})
    effective = list(effective_free_groups(fs))
    fifth = effective[5]
    assert fifth[0] == 5 and fifth[2] & 2 and fifth[3] == 58
    assert len(fifth[1]) == 32710 and fifth[1][0] == 163898
    assert sum(len(row[1]) for row in effective) == 178848
    raw_free = sum(not data[63*bs+i//8] & (1 << (i % 8)) for i in range(per_group))
    assert raw_free - len(fifth[1]) == 58
    verify_zero_blocks(reader, bs, fifth[1], 'fixture', 5)
    reader.dirty = 163840  # allocated backup metadata must not be classified free.
    verify_zero_blocks(reader, bs, fifth[1], 'fixture', 5)
    reader.dirty = 163898  # first real free block: the verifier must reject it.
    try:
        verify_zero_blocks(reader, bs, fifth[1], 'fixture', 5)
    except AssertionError as error:
        assert error.args[0] == ('Nonzero free block', 'fixture', 5, 163898)
    else:
        raise AssertionError('Nonzero free-block fixture was accepted')
    print('Self-test passed: exact 58-block UNINIT difference; nonzero free block rejected')


def main():
    result_path = HERE/'COMPOSICION-VERIFICADA.json'
    assert not result_path.exists(), 'Preserve previous verification receipts'
    report = json.loads((HERE/'IMAGENES-0.2.0.json').read_text())
    inventory = json.loads((HERE/'privado/inventario/report.json').read_text())
    policy = json.loads((HERE/'politica-paquetes.json').read_text())
    keep = {p for group in policy['keep_groups'].values() for p in group}
    expected = {(a['part'], a['path']): a['sha256'] for a in inventory['apks'] if a['package'] in keep}
    components = json.loads((HERE/'COMPONENTES.json').read_text())
    component_paths = {'inicio': ('system','/app/InicioTV/InicioTV.apk'),
                       'webview-overlay': ('vendor','/overlay/TVBaseWebView/TVBaseWebView.apk'),
                       'defaults': ('vendor','/overlay/TVBaseDefaults/TVBaseDefaults.apk')}
    expected.update({component_paths[r['component']]: r['sha256'] for r in components})
    expected['system','/app/Chrome/Chrome.apk'] = '3d9414001b3e2555831cd014df2c9ae5a6eab10190c4cffce7ecaad3c0f53f23'
    manager = json.loads((HERE/'gestion/LIBERACION.json').read_text())
    expected['system','/priv-app/TVBaseGestion/TVBaseGestion.apk'] = manager['apk_sha256']
    found, free_checks, files = {}, {}, {}
    for part in ('system','vendor','product','odm'):
        row = report['images'][part]
        image = ROOT/row['path']
        assert image.stat().st_size == row['bytes'] and builder.sha(image) == row['sha256']
        with builder.filesystem(image) as (fs,nodes):
            files[part] = set(nodes)
            for path,node in nodes.items():
                if path.endswith('.apk') and node['modo'] & 0xf000 == 0x8000:
                    content = fs.content(node)
                    found[part,path] = hashlib.sha256(content).hexdigest()
                    if (part,path) == ('system','/priv-app/TVBaseGestion/TVBaseGestion.apk'):
                        with zipfile.ZipFile(io.BytesIO(content)) as apk:
                            assert apk.read('assets/owner.conf') == b'TVBASE-OWNER-1\nenabled=false\n'
            # Check every unallocated block, not a sample. Contents of allocated
            # inode slack are outside this specific free-block guarantee.
            checked = 0
            uninitialized = []
            for group, free, flags, metadata_count in effective_free_groups(fs):
                verify_zero_blocks(fs.r, fs.bs, free, part, group)
                checked += len(free)
                if flags & 0x2:
                    uninitialized.append({'group':group,'metadata_blocks':metadata_count,'free_blocks':len(free)})
            assert checked*fs.bs == row['free_bytes']
            free_checks[part] = {'zero_free_blocks':checked,'zero_free_bytes':checked*fs.bs,
                                 'uninitialized_groups_reconstructed':uninitialized}
            print(json.dumps({'part':part,**free_checks[part]}),flush=True)
    assert found == expected, {'unexpected':sorted(set(found)-set(expected)), 'missing':sorted(set(expected)-set(found))}
    assert len(found) == 39 and len(keep) == 34
    assert not {'/xbin/su','/xbin/procmem','/recovery-from-boot.p'} & files['system']
    assert not any(path.startswith('/preinstall') for path in files['vendor'])
    assert not any(path.startswith('/app/OTAUpgrade') for path in files['product'])
    boot_row = report['images']['boot']
    assert builder.sha(ROOT/boot_row['path']) == boot_row['sha256']
    kernel,ramdisk,dtb,page = builder.boot.parse((ROOT/boot_row['path']).read_bytes())
    assert hashlib.sha256(kernel).hexdigest() == builder.boot.KERNEL_SHA
    assert hashlib.sha256(dtb).hexdigest() == builder.boot.DTB_SHA
    result = {'state':'passed','date_utc':datetime.now(timezone.utc).isoformat(),
              'image_report_sha256':builder.sha(HERE/'IMAGENES-0.2.0.json'),
              'verifier_sha256':builder.sha(Path(__file__)),
              'apk_count':len(found),'retained_original_packages':len(keep),'added_apks':5,
              'apks':[{'partition':part,'path':path,'sha256':digest} for (part,path),digest in sorted(found.items())],
              'free_blocks':free_checks,'manager_configuration_disabled':True,
              'kernel_sha256':builder.boot.KERNEL_SHA,'dtb_sha256':builder.boot.DTB_SHA,
              'elevated_legacy_su_and_procmem_absent':True,'vendor_preinstall_absent':True,
              'physical_boot_tested':False,'traffic_audited_on_device':False,
              'limits':'Exact APK inventory and all free blocks checked; not a full code security or allocated-slack audit.'}
    result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Composition verified offline: 39 APKs; all free blocks zero')


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Verification requires Python without optimization')
    if sys.argv[1:] == ['--self-test']:
        self_test()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit('Usage: verificar-composicion.py [--self-test]')
