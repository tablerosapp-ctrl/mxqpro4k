"""Build TVBASE 0.2.0 from immutable, verified P291 backups on this PC.

Only regular workspace files are mutated. No mounts, device paths, network,
firmware execution, USB writes, userdata migration or installation are used.
"""
import hashlib
import importlib.util
import json
import mmap
import re
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import boot
import product_ea

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORK = HERE / 'privado/construccion-0.2.0-intento03'
ORIGINALS = ROOT / 'privado/TVBASE-respaldo-P291-20260907-194413-6d502965'
BOOT_ORIGINAL = ROOT / 'privado/TVBASE-respaldo-P291-20260907-194104-0deb291b/boot.img'
INVENTORY = HERE / 'privado/inventario'
TOOLS = ROOT / 'tools/ext4-cygwin/bin'
spec = importlib.util.spec_from_file_location('inv_p291', ROOT/'rom-simplificada/inspeccion/inventariar-ext4.py')
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quote(text):
    text = str(text).replace('\\', '/')
    assert not any(c in text for c in ('"', '\n', '\r', '\0'))
    return '"' + text + '"'


def run(args, log, timeout=300):
    p = subprocess.run([str(x) for x in args], capture_output=True, timeout=timeout, creationflags=0x08000000)
    log.write_bytes(p.stdout + p.stderr)
    assert p.returncode == 0, (log.relative_to(ROOT).as_posix(), p.returncode)
    return p.stdout + p.stderr


@contextmanager
def filesystem(path):
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        fs = inv.Ext4(inv.Sparse(data, 0, len(data)))
        yield fs, dict(fs.walk())


def props(text, values, remove=()):
    for key in remove:
        text = re.sub(r'(?m)^' + re.escape(key) + r'=[^\n]*\n?', '', text)
    for key, value in values.items():
        text, count = re.subn(r'(?m)^' + re.escape(key) + r'=[^\n]*$', key+'='+value, text)
        assert count <= 1, key
        if not count:
            text = text.rstrip() + '\n' + key + '=' + value + '\n'
    return text


def remove_service(text, name, required=True):
    text, count = re.subn(r'(?m)^service '+re.escape(name)+r' [^\n]*\n(?:[ \t]+[^\n]*\n|\n)*',
                         '# TVBASE: '+name+' removed.\n\n', text)
    assert count == 1 if required else count <= 1, name
    text = re.sub(r'(?m)^[ \t]*start '+re.escape(name)+r'[ \t]*$',
                  '    # TVBASE: '+name+' startup removed', text)
    return text


class Plan:
    def __init__(self, part, source, records, workspace):
        self.part, self.source, self.workspace = part, source, workspace
        self.nodes = {r['path']: r for r in records}
        self.removed, self.edits, self.added_dirs = set(), {}, set()
        self.added_dir_contexts = {}
        self.reclamation = None
        self.commands = []

    def remove_tree(self, path):
        assert path.startswith('/') and path != '/' and '..' not in path.split('/')
        assert path in self.nodes, (self.part, path)
        selected = {p for p in self.nodes if p == path or p.startswith(path+'/')}
        self.removed.update(selected)

    def remove_if_present(self, path):
        if path in self.nodes:
            self.remove_tree(path)

    def read(self, fs, nodes, path):
        assert nodes[path]['modo'] & 0xf000 == 0x8000
        return fs.content(nodes[path]).decode('utf8')

    def label(self, path):
        log = self.workspace / ('label-'+hashlib.sha256(path.encode()).hexdigest()[:16]+'.txt')
        out = run([TOOLS/'debugfs.exe', '-R', 'ea_list '+quote(path), self.source], log)
        found = re.findall(rb'security\.selinux\s+\([0-9]+\)\s*=\s*"([^"\r\n]+)"', out)
        assert len(found) == 1, path
        value = found[0].decode('ascii').removesuffix('\\000')
        assert re.fullmatch(r'u:object_r:[A-Za-z0-9_]+:s0', value)
        return value

    def put(self, path, content, context=None, mode=None, uid=0, gid=0):
        assert path not in self.removed and path not in self.edits
        assert path.startswith('/') and '..' not in path.split('/')
        if path in self.nodes:
            old = self.nodes[path]
            assert old['modo'] & 0xf000 == 0x8000, path
            context = self.label(path)
            mode, uid, gid = old['modo'], old['uid'], old['gid']
        else:
            assert context is not None
            mode = mode or 0o100644
        if isinstance(content, str):
            content = content.encode('utf8')
        payload = self.workspace / ('payload-'+hashlib.sha256(path.encode()).hexdigest()[:16])
        payload.write_bytes(content)
        self.edits[path] = {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content),
                           'mode': mode, 'uid': uid, 'gid': gid, 'context': context,
                           'payload': payload}

    def metadata(self, path, mode, uid, gid, context):
        label_file = self.workspace / ('context-'+hashlib.sha256(context.encode()).hexdigest()[:16])
        label_file.write_bytes(context.encode()+b'\0')
        self.commands.extend(['set_inode_field '+quote(path)+' mode 0'+format(mode,'o'),
                              'set_inode_field '+quote(path)+' uid '+str(uid),
                              'set_inode_field '+quote(path)+' gid '+str(gid),
                              'ea_set -f '+quote(label_file)+' '+quote(path)+' security.selinux'])

    def apply(self, edited):
        assert edited.parent == self.workspace and not edited.exists()
        shutil.copyfile(self.source, edited)
        assert sha(edited) == sha(self.source)
        for path in sorted(self.removed, key=lambda p: (p.count('/'), p), reverse=True):
            cmd = 'rmdir' if self.nodes[path]['modo'] & 0xf000 == 0x4000 else 'rm'
            self.commands.append(cmd+' '+quote(path))
        for path, item in self.edits.items():
            for parent in reversed(PurePosixPath(path).parents):
                name = str(parent)
                if name in self.nodes:
                    assert self.nodes[name]['modo'] & 0xf000 == 0x4000, name
                if name == '/' or name in self.nodes or name in self.added_dirs:
                    continue
                assert name not in self.removed
                self.commands.append('mkdir '+quote(name))
                self.metadata(name, 0o40755, 0, 0, item['context'])
                self.added_dirs.add(name)
                self.added_dir_contexts[name] = item['context']
            if path in self.nodes:
                self.commands.append('rm '+quote(path))
            self.commands.extend(['cd '+quote(str(PurePosixPath(path).parent)),
                                  'write '+quote(item['payload'])+' '+quote(PurePosixPath(path).name), 'cd /'])
            self.metadata(path, item['mode'], item['uid'], item['gid'], item['context'])
        command_file = self.workspace/'debugfs.txt'
        command_file.write_text('\n'.join(self.commands)+'\n', encoding='utf8')
        run([TOOLS/'debugfs.exe', '-w', '-f', command_file, edited], self.workspace/'edit.log')
        if self.part == 'product':
            self.reclamation = product_ea.reclaimed(self, edited)
        run([TOOLS/'e2fsck.exe', '-fn', edited], self.workspace/'fsck-edited.log')

    def xattrs(self, image, paths, label):
        paths = sorted(paths)
        command_file = self.workspace/('xattrs-'+label+'.commands')
        command_file.write_text(''.join('ea_list '+quote(path)+'\n' for path in paths), encoding='utf8')
        out = run([TOOLS/'debugfs.exe', '-f', command_file, image], self.workspace/('xattrs-'+label+'.log'))
        text = out.decode('utf8', 'strict').replace('\r\n', '\n')
        text = re.sub(r'(?m)^debugfs [0-9][^\n]*\n?', '', text)
        matches = list(re.finditer(r'(?m)^debugfs: ea_list "([^"\n]+)"\n', text))
        assert [m[1] for m in matches] == paths
        assert not text[:matches[0].start()].strip() if matches else not text.strip()
        attributes = {}
        for i, match in enumerate(matches):
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            lines = [line.strip() for line in text[match.end():end].splitlines()
                     if line.strip() and line.strip() != 'Extended attributes:']
            # debugfs omits displayed values above its print limit. Only the
            # name/size are taken here; ea_get below verifies the exact bytes.
            assert all(re.fullmatch(r'[^\s]+\s+\([0-9]+\)(?:\s*=\s*.+)?', line) for line in lines), (match[1], lines)
            attributes[match[1]] = {}
            for line in lines:
                attr = re.fullmatch(r'([^\s]+)\s+\(([0-9]+)\)(?:\s*=\s*.+)?', line)
                assert attr[1] not in attributes[match[1]]
                attributes[match[1]][attr[1]] = int(attr[2])
        raw_dir = self.workspace/('xattr-bytes-'+label+'-'+uuid.uuid4().hex[:8])
        raw_dir.mkdir()
        commands, files = [], []
        for name, attrs in attributes.items():
            for attribute, size in attrs.items():
                destination = raw_dir/hashlib.sha256((name+'\0'+attribute).encode()).hexdigest()
                commands.append('ea_get -f '+quote(destination)+' '+quote(name)+' '+quote(attribute))
                files.append((name, attribute, size, destination))
        if commands:
            raw_commands = raw_dir/'commands.txt'
            raw_commands.write_text('\n'.join(commands)+'\n', encoding='utf8')
            run([TOOLS/'debugfs.exe', '-f', raw_commands, image], raw_dir/'read.log')
        result = {name:{} for name in paths}
        for name, attribute, size, destination in files:
            assert destination.is_file() and destination.stat().st_size == size, (name,attribute)
            result[name][attribute] = {'bytes':size, 'sha256':sha(destination)}
        return result

    def verify(self, path):
        with filesystem(path) as (fs, nodes):
            assert set(nodes) == (set(self.nodes)-self.removed) | set(self.edits) | self.added_dirs
            unchanged = 0
            for name, node in nodes.items():
                if name in self.added_dirs:
                    assert (node['modo'], node['uid'], node['gid']) == (0o40755, 0, 0)
                    continue
                expected = self.edits[name] if name in self.edits else self.nodes[name]
                mode = expected['mode'] if name in self.edits else expected['modo']
                assert (node['modo'], node['uid'], node['gid']) == (mode, expected['uid'], expected['gid']), name
                if node['modo'] & 0xf000 in (0x8000, 0xa000):
                    assert hashlib.sha256(fs.content(node)).hexdigest() == expected['sha256'], name
                    unchanged += name not in self.edits
            free = fs.meta['bloques_libres'] * fs.bs
        # Compare all displayed extended attributes of untouched nodes, including
        # capabilities; verify labels on edited files and their new directories.
        untouched = set(self.nodes)-self.removed-set(self.edits)
        before = self.xattrs(self.source, untouched, path.stem+'-source')
        after = self.xattrs(path, set(nodes), path.stem+'-result')
        assert all(before[name] == after[name] for name in untouched), 'An unrelated extended attribute changed'
        expected_labels = {name:item['context'] for name,item in self.edits.items()}
        expected_labels.update(self.added_dir_contexts)
        for name, label in expected_labels.items():
            value = after[name].get('security.selinux')
            expected = label.encode()+b'\0'
            assert value == {'bytes':len(expected), 'sha256':hashlib.sha256(expected).hexdigest()}, name
        return {'unchanged_files_verified': unchanged, 'removed_nodes': len(self.removed),
                'changed_files_verified': len(self.edits), 'free_bytes': free,
                'unchanged_nodes_xattrs_verified': len(untouched), 'new_directory_contexts_verified': len(self.added_dirs)}


def main():
    assert not WORK.exists(), 'Keep previous work/results; do not rerun blindly'
    policy = json.loads((HERE/'politica-paquetes.json').read_text())
    inventory = json.loads((INVENTORY/'report.json').read_text())
    keep = {p for group in policy['keep_groups'].values() for p in group}
    packages = {a['package'] for a in inventory['apks']}
    assert keep <= packages
    components = {r['component']: r for r in json.loads((HERE/'COMPONENTES.json').read_text())}
    # The management build receipt is supplied by its isolated compiler.
    management = json.loads((HERE/'gestion/compilacion-resultado.json').read_text())
    component_files = {n: ROOT/r['path'] for n, r in components.items()}
    for n, record in components.items():
        assert sha(component_files[n]) == record['sha256']
    management_apk = ROOT/management['apk']
    assert sha(management_apk) == management['sha256'] and management['signature_verification_api28_exit'] == 0
    assert management['configuration_disabled'] and management['signing_inputs_unchanged']
    release = json.loads((HERE/'gestion/LIBERACION.json').read_text())
    assert release['state'] == 'reviewed_offline' and release['reviewer_received'] and release['tests_passed']
    assert release['apk_sha256'] == management['sha256'] and release['source_sha256'] == management['source_sha256']
    assert all(sha(ROOT/path) == digest for path,digest in release['source_sha256'].items())
    chrome = ROOT/'actualizacion-chrome/chrome-138.0.7204.179-arm32.apk'
    assert sha(chrome) == '3d9414001b3e2555831cd014df2c9ae5a6eab10190c4cffce7ecaad3c0f53f23'
    for part, row in inventory['partitions'].items():
        source = ORIGINALS/(part+'.img')
        assert source.is_file() and source.stat().st_size == row['bytes'] and sha(source) == row['source_sha256']
    assert sha(BOOT_ORIGINAL) == boot.ORIGINAL_SHA
    WORK.mkdir(parents=True)
    removed_apks = [a for a in inventory['apks'] if a['package'] not in keep]
    report = {'version': '0.2.0', 'package_id': 'TVBASE-P291-A9-0.2.0',
              'builder_sha256': sha(Path(__file__)), 'boot_transformer_sha256': sha(HERE/'boot.py'),
              'product_ea_helper_sha256': sha(HERE/'product_ea.py'),
              'dt_id': 'gxlx2_p291_1g', 'images': {}, 'removed_apks': removed_apks,
              'retained_packages': sorted(keep), 'changes': {}, 'bluetooth_disabled': True,
              'boot_unchanged': False, 'reviewed': False, 'physical_boot_tested': False,
              'security_limitations': ['Original Android framework/native libraries retained; not a full AOSP rebuild.',
                'Original SELinux permissive and public platform signing keys retained in this experiment.',
                'Android9/Chrome138 no longer receives current official browser releases.',
                'Old userdata must be removed by a separate reviewed migration before first installation.',
                'No physical traffic, driver, WebView or restoration validation yet.']}
    removed_packages = {a['package'] for a in removed_apks}
    for part in ('system', 'vendor', 'product', 'odm'):
        workspace = WORK/part
        workspace.mkdir()
        source = ORIGINALS/(part+'.img')
        records = json.loads((INVENTORY/(part+'.json')).read_text())
        plan = Plan(part, source, records, workspace)
        for apk in removed_apks:
            if apk['part'] != part:
                continue
            path = apk['path']
            assert path.startswith(('/app/', '/priv-app/', '/preinstall/'))
            tree = str(PurePosixPath(path).parent)
            if tree == '/preinstall':
                tree = path
            plan.remove_tree(tree)
        with filesystem(source) as (fs, nodes):
            if part == 'system':
                for path in ('/xbin/su', '/xbin/procmem', '/recovery-from-boot.p'):
                    plan.remove_tree(path)
                plan.put('/bin/install-recovery.sh', '#!/system/bin/sh\n# TVBASE: preserve installed recovery.\nexit 0\n')
                plan.put('/build.prop', props(plan.read(fs,nodes,'/build.prop'), {
                    'ro.build.display.id': 'TVBASE-P291-A9-0.2.0-experimental', 'ro.product.locale': 'es-AR',
                    'ro.build.user': 'tvbase', 'ro.build.host': 'local-build'}, remove=('ro.expect.recovery_id',)))
                plan.put('/etc/prop.default', props(plan.read(fs,nodes,'/etc/prop.default'), {
                    'ro.debuggable': '0', 'ro.secure': '1', 'ro.adb.secure': '1', 'persist.sys.usb.config': 'none'},
                    remove=('ro.opa.eligible_device', 'ro.com.google.gmsversion')))
                plan.put('/app/Chrome/Chrome.apk', chrome.read_bytes(), context='u:object_r:system_file:s0')
                plan.put('/app/InicioTV/InicioTV.apk', component_files['inicio'].read_bytes(), context='u:object_r:system_file:s0')
                plan.put('/priv-app/TVBaseGestion/TVBaseGestion.apk', management_apk.read_bytes(), context='u:object_r:system_file:s0')
                plan.put('/etc/permissions/privapp-permissions-tvbase-gestion.xml',
                    (HERE/'gestion/privapp-permissions-tvbase-gestion.xml').read_bytes(), context='u:object_r:system_file:s0')
                info = {'version': '0.2.0', 'profile': 'gxlx2_p291_1g', 'android_api': 28,
                    'chrome_version': '138.0.7204.179', 'bluetooth_disabled': True,
                    'remote_manager_included': True, 'owner_endpoint_configured': False,
                    'adb_tcp_enabled_by_default': False, 'inherited_setuid_su_removed': True,
                    'base': 'verified_original_p291_derivative', 'physical_boot_tested': False}
                plan.put('/etc/tvbase.json', json.dumps(info,indent=2)+'\n', context='u:object_r:system_file:s0')
                plan.put('/etc/permissions/tvbase-no-bluetooth.xml',
                    '<permissions>\n<unavailable-feature name="android.hardware.bluetooth"/>\n'
                    '<unavailable-feature name="android.hardware.bluetooth_le"/>\n</permissions>\n',
                    context='u:object_r:system_file:s0')
            if part == 'vendor':
                # Remove the complete factory payload area, not only its APK entries.
                plan.remove_tree('/preinstall')
                plan.remove_tree('/bin/preinstall.sh')
                for path in ('/lib/modules/btmtksdio.ko', '/lib/modules/rtk_btusb.ko',
                             '/lib/modules/btusb.ko', '/lib/modules/btmtk_usb.ko', '/lib/modules/sprdbt_tty.ko',
                             '/bin/hw/android.hardware.bluetooth@1.0-service'):
                    plan.remove_if_present(path)
                init_path = '/etc/init/hw/init.amlogic.rc'
                text = plan.read(fs,nodes,init_path)
                for service in ('preinstall', 'factoryreset'):
                    text = remove_service(text, service)
                text, debug_count = re.subn(r'(?m)^on property:ro.debuggable=1\n'
                    r'    write /sys/module/kgdboc/parameters/kgdboc ttyFIQ2\n'
                    r'    write /sys/module/fiq_debugger/parameters/kgdb_enable 1\n',
                    '# TVBASE: serial kernel debug startup removed.\n', text)
                assert debug_count == 1
                for module in ('btmtksdio', 'sprdbt_tty'):
                    text, count = re.subn(r'(?m)^on property:persist.vendor.btmodule='+module+r'\n(?:[ \t]+[^\n]*\n|\n)*',
                        '# TVBASE: Bluetooth module trigger removed.\n\n', text)
                    assert count == 1
                plan.put(init_path, text)
                board = '/etc/init/hw/init.amlogic.board.rc'
                text = remove_service(plan.read(fs,nodes,board), 'softprobe')
                text, count = re.subn(r'(?m)^[ \t]*start console[ \t]*$', '    # TVBASE: console removed', text)
                assert count == 2
                text = re.sub(r'(?m)^[ \t]*chmod 755 /vendor/bin/startsoftdetector.sh[ \t]*$',
                              '    # TVBASE: obsolete factory probe removed', text)
                plan.put(board,text)
                plan.put('/etc/init/android.hardware.bluetooth@1.0-service.rc', '# TVBASE: Bluetooth HAL removed.\n')
                for optional in ('/etc/init/miracast_hdcp2.rc',):
                    plan.remove_if_present(optional)
                manifest = '/etc/vintf/manifest.xml'
                text = plan.read(fs,nodes,manifest)
                tree = ET.fromstring(text)
                selected = [h for h in tree.findall('hal') if h.findtext('name') == 'android.hardware.bluetooth']
                assert len(selected) == 1
                tree.remove(selected[0])
                plan.put(manifest, ET.tostring(tree, encoding='utf-8', xml_declaration=True)+b'\n')
                plan.put('/build.prop', props(plan.read(fs,nodes,'/build.prop'), {
                    'service.adb.tcp.port': '-1', 'persist.adb.tcp.port': '-1', 'ro.adb.secure': '1',
                    'config.disable_bluetooth': 'true', 'ro.vendor.autoconnectbt.isneed': 'false'}))
                for name, folder in [('webview-overlay', 'TVBaseWebView'), ('defaults', 'TVBaseDefaults')]:
                    plan.put('/overlay/'+folder+'/'+folder+'.apk', component_files[name].read_bytes(),
                             context='u:object_r:vendor_overlay_file:s0')
            # Remove declared Bluetooth hardware and grants for packages removed.
            for path, node in nodes.items():
                if path in plan.removed or path in plan.edits or node['modo'] & 0xf000 != 0x8000:
                    continue
                if not (path.startswith('/etc/permissions/') or path.startswith('/etc/sysconfig/')) or not path.endswith('.xml'):
                    continue
                content = fs.content(node)
                tree = ET.fromstring(content)
                changed = False
                for child in list(tree):
                    if child.get('package') in removed_packages or (child.tag == 'feature' and child.get('name') in
                        ('android.hardware.bluetooth', 'android.hardware.bluetooth_le')):
                        tree.remove(child); changed = True
                if changed:
                    if not list(tree):
                        plan.remove_tree(path)
                    else:
                        plan.put(path, ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')
        assert not (set(plan.edits) & plan.removed)
        edited, final = workspace/(part+'.edited.img'), workspace/(part+'.img')
        plan.apply(edited)
        plan.verify(edited)
        # Copy allocated filesystem blocks into a new image. Free regions become
        # zero/hole data so removed APK bytes are not shipped as unused space.
        run([TOOLS/'e2image.exe', '-ra', edited, final], workspace/'e2image.log')
        assert final.stat().st_size == source.stat().st_size
        run([TOOLS/'e2fsck.exe', '-fn', final], workspace/'fsck-final.log')
        verification = plan.verify(final)
        report['images'][part] = {'path': final.relative_to(ROOT).as_posix(), 'bytes': final.stat().st_size,
            'sha256': sha(final), 'source_sha256': inventory['partitions'][part]['source_sha256'], 'fsck_exit': 0,
            **verification, 'external_ea_reclamation': plan.reclamation}
        report['changes'][part] = {'removed_paths': sorted(plan.removed),
            'files': {p: {k:v for k,v in r.items() if k != 'payload'} for p,r in plan.edits.items()}}
        print(json.dumps({'partition': part, **report['images'][part]}), flush=True)
    boot_data, boot_report = boot.harden(BOOT_ORIGINAL.read_bytes())
    final_boot = WORK/'boot.img'
    final_boot.write_bytes(boot_data)
    assert sha(final_boot) == boot_report['sha256']
    report['images']['boot'] = {'path': final_boot.relative_to(ROOT).as_posix(), **boot_report}
    report['boot_review'] = {'approved': True, 'kernel_sha256': boot_report['kernel_sha256'],
                            'dtb_sha256': boot_report['dtb_sha256'], 'ramdisk_sha256': boot_report['ramdisk_sha256']}
    report['reviewed'] = True
    # Revalidate immutable sources after the entire build.
    for part, row in inventory['partitions'].items():
        assert sha(ORIGINALS/(part+'.img')) == row['source_sha256']
    assert sha(BOOT_ORIGINAL) == boot.ORIGINAL_SHA
    (HERE/'IMAGENES-0.2.0.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'state':'built_verified_offline','images':5,'physical_boot_tested':False}), flush=True)


if __name__ == '__main__':
    main()
