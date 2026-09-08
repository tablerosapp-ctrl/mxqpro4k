"""Strict P291 Android v1 boot transformation on local files only.

Preserves kernel, multi-DTB and every unrelated ramdisk entry. The original
vendor SELinux permissive setting remains an explicit experimental limitation.
"""
import gzip
import hashlib
import struct

ORIGINAL_SHA = '13e027a3aae1af232d1d700421486f32b7958a9fa0a157d8cbd3c47243ab697d'
KERNEL_SHA = '9968c75f691f67dcb805ef8105e1ca534f73430bcf8b3920a066580e326b791a'
DTB_SHA = '13e54b5f1bba959e398da74b9d0859d08ba1747840ed3866eca1f3461c550d01'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def entries(data):
    pos, result, names = 0, [], set()
    while True:
        header = data[pos:pos + 110]
        assert len(header) == 110 and header[:6] in (b'070701', b'070702')
        values = [int(header[6 + i * 8:14 + i * 8], 16) for i in range(13)]
        size, nlen = values[6], values[11]
        assert 1 <= nlen <= 4096
        namebytes = data[pos + 110:pos + 110 + nlen]
        assert namebytes[-1:] == b'\0'
        name = namebytes[:-1].decode('utf8')
        assert name not in names and not name.startswith('/') and '..' not in name.split('/')
        names.add(name)
        start = (pos + 110 + nlen + 3) // 4 * 4
        end = (start + size + 3) // 4 * 4
        assert end <= len(data)
        content = data[start:start + size]
        if header[:6] == b'070702':
            assert values[12] == sum(content) & 0xffffffff
        result.append((name, header, data[pos + 110:start], content, data[pos:end]))
        pos = end
        if name == 'TRAILER!!!':
            assert not any(data[pos:])
            return result, data[pos:]


def parse(data):
    assert len(data) == 16777216 and data[:8] == b'ANDROID!'
    ks, ka, rs, ra, ss, sa, tags, page, version = struct.unpack_from('<9I', data, 8)
    ds, do, hs = struct.unpack_from('<IQI', data, 1632)
    assert page == 2048 and version == 1 and hs == 1648 and ds == 0 and do == 0
    align = lambda n: (n + page - 1) // page * page
    kernel = data[page:page + ks]
    ram = data[page + align(ks):page + align(ks) + rs]
    second = data[page + align(ks) + align(rs):page + align(ks) + align(rs) + ss]
    assert sha(kernel) == KERNEL_SHA and sha(second) == DTB_SHA
    end = page + align(ks) + align(rs) + align(ss)
    assert end <= len(data) and not any(data[end:])
    digest = hashlib.sha1()
    for part in (kernel, ram, second, b''):
        digest.update(part)
        digest.update(struct.pack('<I', len(part)))
    assert digest.digest() == data[576:596]
    return kernel, ram, second, page


def harden(data):
    assert sha(data) == ORIGINAL_SHA
    kernel, ram, second, page = parse(data)
    rows, tail = entries(gzip.decompress(ram))
    old = {n: c for n, h, nd, c, raw in rows}
    assert old['default.prop'] == b'system/etc/prop.default'
    # Drop the serial console service entirely; vendor explicit starts are also
    # removed by the filesystem recipe. Keep physical USB ADB auth capability.
    text = old['init.rc'].decode('utf8')
    import re
    text, count = re.subn(r'(?m)^service console [^\n]*\n(?:[ \t]+[^\n]*\n|\n)*',
                         '# TVBASE: interactive root console removed.\n\n', text)
    assert count == 1
    text = re.sub(r'(?m)^[ \t]+start console\s*$', '    # TVBASE: console removed', text)
    usb = old['init.usb.rc']
    assert usb.count(b' --root_seclabel=u:r:su:s0') == 1
    usb = usb.replace(b' --root_seclabel=u:r:su:s0', b'')
    changed = {'init.rc': text.encode(), 'init.usb.rc': usb}
    cpio = bytearray()
    for name, header, namedata, content, raw in rows:
        if name not in changed:
            cpio.extend(raw)
            continue
        content = changed[name]
        header = bytearray(header)
        header[54:62] = ('%08x' % len(content)).encode()
        if header[:6] == b'070702':
            header[102:110] = ('%08x' % (sum(content) & 0xffffffff)).encode()
        cpio.extend(header + namedata + content)
        cpio.extend(bytes((-len(cpio)) % 4))
    cpio.extend(tail)
    newram = gzip.compress(bytes(cpio), compresslevel=9, mtime=0)
    align = lambda n: (n + page - 1) // page * page
    result = bytearray(len(data))
    result[:page] = data[:page]
    struct.pack_into('<I', result, 16, len(newram))
    off = page
    for part in (kernel, newram, second):
        result[off:off + len(part)] = part
        off += align(len(part))
    assert off <= len(result)
    digest = hashlib.sha1()
    for part in (kernel, newram, second, b''):
        digest.update(part)
        digest.update(struct.pack('<I', len(part)))
    result[576:608] = digest.digest() + bytes(12)
    newkernel, newram2, newsecond, _ = parse(result)
    after, _ = entries(gzip.decompress(newram2))
    assert [r[0] for r in rows] == [r[0] for r in after]
    for before, later in zip(rows, after):
        assert later[3] == changed[before[0]] if before[0] in changed else later[4] == before[4]
    assert kernel == newkernel and second == newsecond
    # Command line and addresses remain original; security properties are in
    # system/etc/prop.default and vendor/build.prop, validated separately.
    allowed = set(range(16, 20)) | set(range(576, 608))
    assert all(result[i] == data[i] for i in range(page) if i not in allowed)
    proof = {'source_sha256': ORIGINAL_SHA, 'bytes': len(result), 'sha256': sha(result),
             'kernel_sha256': sha(kernel), 'dtb_sha256': sha(second),
             'ramdisk_sha256': sha(newram),
             'kernel_dtb_unchanged': True, 'changed_cpio_entries': list(changed),
             'unchanged_cpio_entries': len(rows) - len(changed),
             'header_id_verified': True, 'selinux_mode': 'inherited_permissive',
             'physical_boot_tested': False}
    return bytes(result), proof
