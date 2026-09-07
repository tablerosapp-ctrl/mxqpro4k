"""Build the P291 Bluetooth-free revision in new local ext4 image copies.

Never opens a device, executes firmware or mutates an earlier release. Android
features, applications, HAL startup and the MTK Bluetooth module are removed
independently; WiFi files and the candidate boot remain unchanged. Physical WiFi
operation and Android startup are not established by these offline checks.
"""
import hashlib
import importlib.util
import json
import mmap
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'rom-simplificada'
WORK = HERE / 'trabajo/revision-0.1.2'
REPORT = WORK / 'revision.json'
SOURCES = {
    'system': (HERE / 'trabajo/revision-0.1.1/system.raw.img',
               'bc2179940754382e5461aa0d65049559b52c1837421c59e651804504010e95d5'),
    'vendor': (HERE / 'trabajo/vendor.raw.img',
               '02d4e8b4cfa01feabf7be61edc8ff7f48129cb3fa5ba1a51f15aba61c687b976'),
}
BOOT = HERE / 'inspeccion/boot-original.img'
BOOT_SHA = 'd7cfafa9b4978e72e63851a8f8f3b9eaf346bc4fb24b8bdb50ed02fcedf100ba'
DEBUGFS = ROOT / 'tools/ext4-cygwin/bin/debugfs.exe'
FSCK = ROOT / 'tools/ext4-cygwin/bin/e2fsck.exe'
FEATURES = ('android.hardware.bluetooth', 'android.hardware.bluetooth_le')
SPEC = importlib.util.spec_from_file_location('tvbase_ext4', HERE / 'inspeccion/inventariar-ext4.py')
inv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inv)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def quote(value):
    value = str(value).replace('\\', '/')
    assert not any(char in value for char in ('"', '\n', '\r', '\0'))
    return '"' + value + '"'


def run(args, timeout=120):
    process = subprocess.run([str(arg) for arg in args], capture_output=True,
                             timeout=timeout, creationflags=0x08000000)
    return process.returncode, process.stdout + process.stderr


@contextmanager
def filesystem(path):
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        fs = inv.Ext4(inv.Sparse(data, 0, len(data)))
        yield fs, dict(fs.walk())


def context(path, image):
    code, output = run([DEBUGFS, '-R', 'ea_list ' + quote(path), image])
    assert code == 0, (path, output)
    found = re.findall(rb'security\.selinux\s+\([0-9]+\)\s*=\s*"([^"\r\n]+)"', output)
    assert len(found) == 1, (path, output)
    label = found[0].decode('ascii').removesuffix('\\000')
    assert re.fullmatch(r'u:object_r:[a-zA-Z0-9_]+:s0', label), (path, label)
    return label, output


def plan(part, source):
    """Resolve every expected source path and transformation before any copy."""
    with filesystem(source) as (fs, nodes):
        trees = ['/app/Bluetooth', '/app/BluetoothSettings'] if part == 'system' else ['/app/BluetoothRemote']
        removed = set()
        for tree in trees:
            assert tree in nodes and nodes[tree]['modo'] & 0xf000 == 0x4000, tree
            removed.update(path for path in nodes if path == tree or path.startswith(tree + '/'))
        for feature in FEATURES:
            path = '/etc/permissions/' + feature + '.xml'
            assert path in nodes and ET.fromstring(fs.content(nodes[path])).find('feature').get('name') == feature
            removed.add(path)

        replaced = {}
        added = {}
        if part == 'system':
            props = fs.content(nodes['/build.prop'])
            assert props.count(b'TVBASE-P291-A9-0.1.1-experimental') == 1
            replaced['/build.prop'] = props.replace(b'TVBASE-P291-A9-0.1.1-experimental', b'TVBASE-P291-A9-0.1.2-experimental')
            info = json.loads(fs.content(nodes['/etc/tvbase.json']))
            assert info['version'] == '0.1.1-experimental' and info['inherited_recovery_replacement_disabled'] is True
            info.update(version='0.1.2-experimental', bluetooth_disabled=True,
                        bluetooth_hardware_tested=False)
            replaced['/etc/tvbase.json'] = (json.dumps(info, indent=2) + '\n').encode()
            added['/etc/permissions/tvbase-no-bluetooth.xml'] = (
                '<?xml version="1.0" encoding="utf-8"?>\n<permissions>\n'
                + ''.join('    <unavailable-feature name="' + feature + '" />\n' for feature in FEATURES)
                + '</permissions>\n').encode()
            for path in ('/bin/install-recovery.sh', '/etc/install-recovery.sh'):
                assert b'applypatch' not in fs.content(nodes[path]) and b'exit 0' in fs.content(nodes[path])
            assert fs.content(nodes['/etc/init/tvbase.rc']).count(b'    stop flash_recovery\n') == 2
        else:
            module = '/lib/modules/btmtksdio.ko'
            assert module in nodes and digest(fs.content(nodes[module])) == '7828aa5b4fa94b27db0f6070b77b0dffe45ba36f52546dde0ae9cde560e6771c'
            removed.add(module)
            init_path = '/etc/init/hw/init.amlogic.rc'
            init_text = fs.content(nodes[init_path]).decode()
            for module_name, commands in (
                ('btmtksdio', ['    insmod /vendor/lib/modules/btmtksdio.ko']),
                ('rtk_btusb', ['    insmod /vendor/lib/modules/rtk_btusb.ko']),
                ('sprdbt_tty', ['    insmod /vendor/lib/modules/uwe5621_bsp_sdio.ko',
                               '    insmod /vendor/lib/modules/sprdbt_tty.ko']),
            ):
                block = 'on property:persist.vendor.bt_module=' + module_name + '\n' + '\n'.join(commands) + '\n'
                assert init_text.count(block) == 1, module_name
                init_text = init_text.replace(block, '# TVBASE 0.1.2: Bluetooth module startup removed (' + module_name + ').\n')
            replaced[init_path] = init_text.encode()
            hal_path = '/etc/init/android.hardware.bluetooth@1.0-service.rc'
            old_hal = fs.content(nodes[hal_path])
            assert old_hal.count(b'service vendor.bluetooth-1-0 ') == 1 and old_hal.count(b'    start vendor.bluetooth-1-0') == 2
            replaced[hal_path] = b'# TVBASE 0.1.2: Bluetooth HAL and all explicit restart triggers disabled.\n'
            manifest_path = '/etc/vintf/manifest.xml'
            manifest = fs.content(nodes[manifest_path]).decode()
            old_root = ET.fromstring(manifest)
            assert len([hal for hal in old_root.findall('hal') if hal.findtext('name') == 'android.hardware.bluetooth']) == 1
            expression = r'    <hal format="hidl">\r?\n        <name>android\.hardware\.bluetooth</name>\r?\n(?:(?!    </hal>).)*    </hal>\r?\n'
            new_manifest, count = re.subn(expression, '', manifest, flags=re.S)
            assert count == 1
            new_root = ET.fromstring(new_manifest)
            expected = [ET.tostring(hal) for hal in old_root if hal.findtext('name') != 'android.hardware.bluetooth']
            assert [ET.tostring(hal) for hal in new_root] == expected
            replaced[manifest_path] = new_manifest.encode()

        assert not (set(replaced) & removed) and not (set(added) & set(nodes))
        metadata = {}
        for path in replaced:
            assert path in nodes and nodes[path]['modo'] & 0xf000 == 0x8000
            label, output = context(path, source)
            metadata[path] = {key: nodes[path][key] for key in ('modo', 'uid', 'gid')}
            metadata[path].update(context=label, context_before=output.decode('utf8', 'replace'))
        for path in added:
            template = '/etc/permissions/android.hardware.bluetooth.xml'
            label, output = context(template, source)
            metadata[path] = {key: nodes[template][key] for key in ('modo', 'uid', 'gid')}
            metadata[path].update(context=label, context_before=output.decode('utf8', 'replace'))
        removed_details = {}
        for path in sorted(removed):
            node = nodes[path]
            removed_details[path] = {key: node[key] for key in ('modo', 'uid', 'gid', 'bytes')}
            if node['modo'] & 0xf000 in (0x8000, 0xa000):
                removed_details[path]['sha256'] = digest(fs.content(node))
        return {'removed': removed_details, 'replaced': replaced, 'added': added, 'metadata': metadata}


def edit(part, image, recipe):
    commands = []
    for path in sorted(recipe['removed'], key=lambda value: (value.count('/'), value), reverse=True):
        action = 'rmdir' if recipe['removed'][path]['modo'] & 0xf000 == 0x4000 else 'rm'
        commands.append(action + ' ' + quote(path))
    for number, (path, content) in enumerate({**recipe['replaced'], **recipe['added']}.items()):
        meta = recipe['metadata'][path]
        payload = WORK / ('file-' + part + '-' + str(number))
        label = WORK / ('context-' + part + '-' + str(number))
        payload.write_bytes(content)
        label.write_bytes(meta['context'].encode() + b'\0')
        (WORK / ('context-before-' + part + '-' + str(number) + '.txt')).write_text(meta['context_before'], encoding='utf8')
        if path in recipe['replaced']:
            commands.append('rm ' + quote(path))
        parent, basename = path.rsplit('/', 1)
        # Cygwin debugfs write must receive a basename after cd; never a full destination.
        commands.extend(['cd ' + quote(parent or '/'), 'write ' + quote(payload) + ' ' + quote(basename), 'cd /',
                         'set_inode_field ' + quote(path) + ' mode ' + oct(meta['modo']).replace('0o', '0'),
                         'set_inode_field ' + quote(path) + ' uid ' + str(meta['uid']),
                         'set_inode_field ' + quote(path) + ' gid ' + str(meta['gid']),
                         'ea_set -f ' + quote(label) + ' ' + quote(path) + ' security.selinux'])
    command_file = WORK / (part + '-debugfs.txt')
    command_file.write_text('\n'.join(commands) + '\n', encoding='utf8')
    code, output = run([DEBUGFS, '-w', '-f', command_file, image])
    (WORK / (part + '-debugfs.log')).write_bytes(output)
    assert code == 0, output.decode('utf8', 'replace')
    code, output = run([FSCK, '-fn', image])
    (WORK / (part + '-fsck.txt')).write_bytes(output)
    assert code == 0, output.decode('utf8', 'replace')


def verify(part, source, image, recipe):
    unchanged = {}
    changes = {**recipe['replaced'], **recipe['added']}
    with filesystem(source) as (oldfs, before), filesystem(image) as (newfs, after):
        assert set(after) == (set(before) - set(recipe['removed'])) | set(recipe['added']), part
        for path, node in after.items():
            expected_meta = recipe['metadata'][path] if path in changes else before[path]
            for key in ('modo', 'uid', 'gid'):
                assert node[key] == expected_meta[key], (part, path, key)
            if node['modo'] & 0xf000 not in (0x8000, 0xa000):
                continue
            content = newfs.content(node)
            if path in changes:
                assert content == changes[path], (part, path)
                label, output = context(path, image)
                assert label == expected_meta['context'], (part, path, label)
                (WORK / ('context-after-' + part + '-' + str(list(changes).index(path)) + '.txt')).write_bytes(output)
            else:
                assert digest(oldfs.content(before[path])) == digest(content), (part, path)
                unchanged[path] = digest(content)
            if path.endswith('.xml') and path.startswith(('/etc/permissions/', '/etc/sysconfig/')):
                root = ET.fromstring(content)
                assert not any(child.tag == 'feature' and child.get('name') in FEATURES for child in root), path
            if path.endswith('.rc') and path.startswith('/etc/init/'):
                active = '\n'.join(line for line in content.decode('utf8', 'replace').splitlines() if not line.lstrip().startswith('#'))
                assert not re.search(r'\b(?:start|service)\s+vendor\.bluetooth-1-0\b', active), path
                assert 'insmod /vendor/lib/modules/btmtksdio.ko' not in active, path
        if part == 'system':
            xml = ET.fromstring(newfs.content(after['/etc/permissions/tvbase-no-bluetooth.xml']))
            assert {element.get('name') for element in xml.findall('unavailable-feature')} == set(FEATURES)
        else:
            xml = ET.fromstring(newfs.content(after['/etc/vintf/manifest.xml']))
            assert not any(hal.findtext('name') == 'android.hardware.bluetooth' for hal in xml.findall('hal'))
        wifi = {path: value for path, value in unchanged.items()
                if any(token in path.lower() for token in ('wifi', 'wlan', 'wpa_supplicant', 'hostapd', 'mt7663'))}
        return {
            'image': str(image.relative_to(ROOT)), 'bytes': image.stat().st_size, 'sha256': sha(image),
            'fsck_exit': 0, 'unchanged_files_verified': len(unchanged),
            'unchanged_metadata_nodes_verified': len(after) - len(changes),
            'removed_paths': recipe['removed'],
            'changed_files': {path: {'sha256': digest(content), **{key: value for key, value in recipe['metadata'][path].items() if key != 'context_before'}} for path, content in changes.items()},
            'wifi_files_preserved': wifi,
        }


def main():
    assert WORK.resolve().is_relative_to((HERE / 'trabajo').resolve())
    # The independent packager may create only its isolated compiler directory.
    # Any image, recipe, log or receipt means this image build already started.
    if WORK.exists():
        assert WORK.is_dir() and all(child.name == 'instalador' and child.is_dir() for child in WORK.iterdir()), \
            'Preserve an existing image revision; inspect it instead of retrying blindly'
    assert DEBUGFS.is_file() and FSCK.is_file()
    for source, expected in SOURCES.values():
        assert source.resolve().is_relative_to(ROOT.resolve()) and source.is_file()
        assert sha(source) == expected, str(source)
    assert sha(BOOT) == BOOT_SHA
    recipes = {part: plan(part, source) for part, (source, _) in SOURCES.items()}
    WORK.mkdir(exist_ok=True)
    print('Source hashes, paths and all planned changes validated; creating isolated copies.', flush=True)
    results = {}
    for part, (source, expected) in SOURCES.items():
        image = WORK / (part + '.raw.img')
        assert image.resolve().is_relative_to(WORK.resolve()) and not image.exists()
        shutil.copyfile(source, image)
        assert sha(image) == expected
        edit(part, image, recipes[part])
        results[part] = verify(part, source, image, recipes[part])
        assert sha(source) == expected
        print(part + ': fsck, content, metadata and unchanged files verified.', flush=True)
    assert sha(BOOT) == BOOT_SHA
    report = {
        'version': '0.1.2', 'package_id': 'TVBASE-P291-A9-0.1.2',
        'system_image': results['system']['image'], 'system_sha256': results['system']['sha256'],
        'vendor_image': results['vendor']['image'], 'vendor_sha256': results['vendor']['sha256'],
        'source_system_sha256': SOURCES['system'][1], 'source_vendor_sha256': SOURCES['vendor'][1],
        'boot_image': str(BOOT.relative_to(ROOT)), 'boot_sha256': BOOT_SHA, 'boot_unchanged': True,
        'fsck_exit': 0, 'bluetooth_disabled': True, 'inherited_recovery_replacement_disabled': True,
        'hardware_tested': False, 'physically_installed': False, 'wifi_recovery_confirmed': False,
        'unchanged_files_verified': sum(item['unchanged_files_verified'] for item in results.values()),
        'partitions': results, 'script_sha256': sha(Path(__file__).resolve()),
        'limits': [
            'Offline image checks do not establish first boot, WiFi recovery or hardware compatibility.',
            'Boot, DT nodes and built-in bt_device/input_btrcu helpers are unchanged; Bluetooth app/HAL startup and the MTK Bluetooth module are removed.',
            'WiFi shares physical radio hardware; preserving its files does not guarantee independence from Bluetooth on this board.',
            'No userdata edits or settings-provider calls; unavailable-feature prevents the AOSP9 Bluetooth service from starting despite inherited Bluetooth preferences.',
            'No ZIP packaging, device access, flashing or USB operation is performed by this script.',
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in report.items() if key != 'partitions'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
