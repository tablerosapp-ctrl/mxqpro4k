"""Read verified P291 backup files, without mounting or executing their contents."""
import hashlib
import importlib.util
import json
import mmap
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'privado/inventario'
ORIGINAL = ROOT / 'privado/TVBASE-respaldo-P291-20260907-194413-6d502965'
SOURCES = {
    'system': '249611912b7b1fa277d169f8612f9a719df3abf99dc98ed8e817657e2c9beb2c',
    'vendor': 'd542fc091469a7c1223c1d5091f8ec6b3456f38dd1218b779d18d1942190d2a7',
    'product': 'ef2c71f6208e25fa1cc9d5c12cb04972ac20d772e2c11a76972859403b530075',
    'odm': '97836d5a1b016b64d3875c82cb5f3b4daee0f56d8eea3675b4231086429cbe67',
}
spec = importlib.util.spec_from_file_location('ext4_inventory', ROOT / 'rom-simplificada/inspeccion/inventariar-ext4.py')
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)
AAPT = ROOT / 'tools/verificacion-apk/build-tools-37/android-37.0/aapt.exe'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve the existing inventory, inspect its receipt before another run')
    OUT.mkdir(parents=True)
    report = {'scope': 'Verified original P291 files; offline read only', 'partitions': {}, 'apks': []}
    for part, expected in SOURCES.items():
        source = ORIGINAL / (part + '.img')
        with source.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert actual == expected, part
        inventory = []
        with source.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            fs = inv.Ext4(inv.Sparse(data, 0, len(data)))
            for path, node in fs.walk():
                row = {k: v for k, v in node.items() if k != 'raw'}
                row['path'] = path
                kind = node['modo'] & 0xf000
                if kind in (0x8000, 0xa000):
                    content = fs.content(node)
                    row['sha256'] = hashlib.sha256(content).hexdigest()
                    if kind == 0xa000:
                        row['symlink'] = content.decode('utf8', 'strict')
                    elif path.endswith('.apk') or (len(content) < 4 * 1024 * 1024 and
                            (path.endswith(('.prop', '.rc', '.xml', '.conf', '.sh')) or
                             any(x in path for x in ('fstab', 'file_contexts', 'seapp_contexts')))):
                        relative = Path(*path.lstrip('/').split('/'))
                        dest = OUT / ('apks' if path.endswith('.apk') else 'metadata') / part / relative
                        assert dest.resolve().is_relative_to(OUT.resolve())
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(content)
                        if path.endswith('.apk'):
                            item = {'part': part, 'path': path, 'bytes': len(content), 'sha256': row['sha256']}
                            for label, args in [('badging', ['dump', 'badging']),
                                                ('manifest', ['dump', 'xmltree'])]:
                                cmd = [str(AAPT), *args, str(dest)]
                                if label == 'manifest':
                                    cmd.append('AndroidManifest.xml')
                                p = subprocess.run(cmd, capture_output=True, timeout=30, creationflags=0x08000000)
                                dest.with_suffix('.' + label + '.txt').write_bytes(p.stdout + p.stderr)
                                item[label + '_exit'] = p.returncode
                                assert p.returncode == 0, (part, path, label)
                                if label == 'badging':
                                    text = p.stdout.decode('utf8', 'replace')
                                    for key, pattern in [('package', r"package: name='([^']+)'"),
                                            ('version', r"versionName='([^']*)'"),
                                            ('version_code', r"versionCode='([^']*)'"),
                                            ('min_sdk', r"sdkVersion:'([^']*)'"),
                                            ('label', r"application-label:'([^']*)'")]:
                                        match = re.search(pattern, text)
                                        item[key] = match.group(1) if match else None
                            report['apks'].append(item)
                inventory.append(row)
            report['partitions'][part] = {'source_sha256': actual, 'bytes': len(data),
                    'filesystem': fs.meta, 'nodes': len(inventory)}
        (OUT / (part + '.json')).write_text(json.dumps(inventory, indent=2), encoding='utf8')
        print(json.dumps({'partition': part, 'nodes': len(inventory),
              'apks': len([a for a in report['apks'] if a['part'] == part])}), flush=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'state': 'completed', 'apks': len(report['apks'])}), flush=True)


if __name__ == '__main__':
    main()
