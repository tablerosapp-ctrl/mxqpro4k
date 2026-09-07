"""Disable inherited recovery replacement in an isolated local system image.
Never opens devices; preserves the original 0.1 image and all other partitions.
"""
import hashlib, importlib.util, json, mmap, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'rom-simplificada'
WORK = HERE / 'trabajo/revision-0.1.1'
SOURCE = HERE / 'trabajo/system.raw.img'
IMAGE = WORK / 'system.raw.img'
REPORT = WORK / 'revision.json'
spec = importlib.util.spec_from_file_location('inv', HERE / 'inspeccion/inventariar-ext4.py')
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def run(args):
    p = subprocess.run([str(x) for x in args], capture_output=True, creationflags=0x08000000)
    return p.returncode, p.stdout + p.stderr

def main():
    expected = '1b388c1366a4a77e0c7e24ee935be187d25a051ab90ea6cbb518e0e486b7c2fb'
    assert sha(SOURCE) == expected
    assert not IMAGE.exists() and not REPORT.exists(), 'Preserve the existing revision; do not retry blindly'
    WORK.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, IMAGE)
    print('Copied original system image; editing isolated revision', flush=True)
    with SOURCE.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        fs = inv.Ext4(inv.Sparse(data, 0, len(data)))
        nodes = dict(fs.walk())
        noop = b'#!/system/bin/sh\n# TVBASE: preserve the existing recovery for future updates and restoration.\nexit 0\n'
        replacements = {'/bin/install-recovery.sh': noop, '/etc/install-recovery.sh': noop}
        for path in replacements:
            assert b'applypatch' in fs.content(nodes[path]), path
        rc = fs.content(nodes['/etc/init/tvbase.rc'])
        assert rc.count(b'    stop bootvideo\n') == 2
        replacements['/etc/init/tvbase.rc'] = rc.replace(b'    stop bootvideo\n', b'    stop bootvideo\n    stop flash_recovery\n')
        props = fs.content(nodes['/build.prop'])
        assert props.count(b'TVBASE-P291-A9-0.1-experimental') == 1
        replacements['/build.prop'] = props.replace(b'TVBASE-P291-A9-0.1-experimental', b'TVBASE-P291-A9-0.1.1-experimental')
        info = json.loads(fs.content(nodes['/etc/tvbase.json']))
        info['version'] = '0.1.1-experimental'
        info['inherited_recovery_replacement_disabled'] = True
        replacements['/etc/tvbase.json'] = (json.dumps(info, indent=2) + '\n').encode()
        commands = []
        contexts = {}
        for i, (path, content) in enumerate(replacements.items()):
            node = nodes[path]
            assert node['modo'] & 0xf000 == 0x8000
            code, ea = run([ROOT / 'tools/ext4-cygwin/bin/debugfs.exe', '-R', 'ea_list ' + path, SOURCE])
            assert code == 0
            (WORK / ('context-before-' + str(i) + '.txt')).write_bytes(ea)
            context = 'u:object_r:install_recovery_exec:s0' if path == '/bin/install-recovery.sh' else 'u:object_r:system_file:s0'
            assert context.encode() in ea, (path, ea)
            contexts[path] = context
            payload = WORK / ('file-' + str(i))
            payload.write_bytes(content)
            label = WORK / ('context-' + str(i))
            label.write_bytes(context.encode() + b'\0')
            parent, name = path.rsplit('/', 1)
            commands.extend(['rm "' + path + '"', 'cd "' + (parent or '/') + '"',
                             'write "' + payload.as_posix() + '" "' + name + '"', 'cd /',
                             'set_inode_field "' + path + '" mode ' + oct(node['modo']).replace('0o', '0'),
                             'set_inode_field "' + path + '" uid ' + str(node['uid']),
                             'set_inode_field "' + path + '" gid ' + str(node['gid']),
                             'ea_set -f "' + label.as_posix() + '" "' + path + '" security.selinux'])
    cmdfile = WORK / 'debugfs.txt'
    cmdfile.write_text('\n'.join(commands) + '\n', encoding='utf8')
    code, output = run([ROOT / 'tools/ext4-cygwin/bin/debugfs.exe', '-w', '-f', cmdfile, IMAGE])
    (WORK / 'debugfs.log').write_bytes(output)
    assert code == 0
    code, output = run([ROOT / 'tools/ext4-cygwin/bin/e2fsck.exe', '-fn', IMAGE])
    (WORK / 'fsck.txt').write_bytes(output)
    assert code == 0, output.decode('utf8', 'replace')
    verified = 0
    with SOURCE.open('rb') as a, IMAGE.open('rb') as b, mmap.mmap(a.fileno(), 0, access=mmap.ACCESS_READ) as olddata, mmap.mmap(b.fileno(), 0, access=mmap.ACCESS_READ) as newdata:
        oldfs = inv.Ext4(inv.Sparse(olddata, 0, len(olddata)))
        newfs = inv.Ext4(inv.Sparse(newdata, 0, len(newdata)))
        before, after = dict(oldfs.walk()), dict(newfs.walk())
        assert set(before) == set(after)
        for path, node in before.items():
            for key in ('modo', 'uid', 'gid'):
                assert node[key] == after[path][key], (path, key)
            if node['modo'] & 0xf000 not in (0x8000, 0xa000):
                continue
            content = newfs.content(after[path])
            if path in replacements:
                assert content == replacements[path]
                code, ea = run([ROOT / 'tools/ext4-cygwin/bin/debugfs.exe', '-R', 'ea_list ' + path, IMAGE])
                assert code == 0 and contexts[path].encode() in ea
            else:
                assert hashlib.sha256(oldfs.content(node)).digest() == hashlib.sha256(content).digest(), path
                verified += 1
    report = {'version': '0.1.1', 'package_id': 'TVBASE-P291-A9-0.1.1',
              'system_image': str(IMAGE.relative_to(ROOT)), 'source_system_sha256': expected,
              'system_sha256': sha(IMAGE), 'fsck_exit': 0, 'unchanged_files_verified': verified,
              'changed_files': {path: hashlib.sha256(content).hexdigest() for path, content in replacements.items()},
              'inherited_recovery_replacement_disabled': True, 'hardware_tested': False,
              'installer_binary': str((WORK / 'update-binary').relative_to(ROOT))}
    assert sha(SOURCE) == expected
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2), flush=True)

if __name__ == '__main__':
    main()
