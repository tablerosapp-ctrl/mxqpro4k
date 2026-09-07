"""Build isolated ordinary-permission Bluetooth control APK; never contact a TV."""
from pathlib import Path
import hashlib, json, subprocess, zipfile, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'rom-simplificada/componentes/control-bluetooth-0.1'
OUT = ROOT / 'rom-simplificada/compilacion/control-bluetooth-0.1'
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
TOOLS = ROOT / 'tools/verificacion-apk/build-tools-37/android-37.0'
SDK = ROOT / 'tools/compilar-android/android-28.jar'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
KEYS = ROOT / 'rom-simplificada/claves-desarrollo'
SIGNER = 'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613'
ANDROID = '{http://schemas.android.com/apk/res/android}'

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def run(args):
    p = subprocess.run(list(map(str, args)), capture_output=True, creationflags=0x08000000)
    with (OUT / 'compilacion.log').open('ab') as f:
        f.write(p.stdout + p.stderr)
    if p.returncode:
        raise RuntimeError(p.stderr.decode('utf8', 'replace'))
    return p.stdout

assert (KEYS / 'componentes.jks').is_file() and (KEYS / 'password.txt').is_file()
manifest = ET.parse(SRC / 'AndroidManifest.xml').getroot()
permissions = sorted(e.get(ANDROID + 'name') for e in manifest.findall('uses-permission'))
assert permissions == ['android.permission.BLUETOOTH', 'android.permission.BLUETOOTH_ADMIN']
assert manifest.get('package') == 'com.tvbase.bluetoothcontrol'
assert manifest.get(ANDROID + 'versionCode') == '1'
assert not manifest.findall('.//service') and not manifest.findall('.//provider')
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'classes').exists(), 'Fresh output required; do not replace a verified build.'
classes = OUT / 'classes'; classes.mkdir()
sources = sorted(SRC.glob('*.java'))
run([JAVA, '-jar', ECJ, '-8', '-encoding', 'UTF-8', '-bootclasspath', SDK, '-d', classes, *sources])
dex = OUT / 'dex'; dex.mkdir()
run([JAVA, '-cp', TOOLS / 'lib/d8.jar', 'com.android.tools.r8.D8', '--min-api', '28', '--lib', SDK, '--output', dex, *sorted(classes.rglob('*.class'))])
unsigned = OUT / 'unsigned.apk'
run([TOOLS / 'aapt2.exe', 'link', '-I', SDK, '--manifest', SRC / 'AndroidManifest.xml', '-o', unsigned, '--min-sdk-version', '28', '--target-sdk-version', '28'])
with zipfile.ZipFile(unsigned, 'a') as archive:
    archive.write(dex / 'classes.dex', 'classes.dex')
aligned = OUT / 'aligned.apk'
run([TOOLS / 'zipalign.exe', '-f', '4', unsigned, aligned])
final = OUT / 'ControlBluetooth-0.1.apk'
run([JAVA, '-jar', TOOLS / 'lib/apksigner.jar', 'sign', '--ks', KEYS / 'componentes.jks', '--ks-key-alias', 'tvbase-development', '--ks-pass', 'file:' + str(KEYS / 'password.txt'), '--out', final, aligned])
signature = run([JAVA, '-jar', TOOLS / 'lib/apksigner.jar', 'verify', '--verbose', '--print-certs', '--min-sdk-version', '28', '--max-sdk-version', '28', final])
assert SIGNER.encode() in signature
(OUT / 'firma.txt').write_bytes(signature)
badging = run([TOOLS / 'aapt2.exe', 'dump', 'badging', final])
assert b"package: name='com.tvbase.bluetoothcontrol' versionCode='1' versionName='0.1'" in badging
assert b"minSdkVersion:'28'" in badging and b"targetSdkVersion:'28'" in badging
actual_permissions = sorted(line.split(b"'")[1].decode() for line in badging.splitlines() if line.startswith(b'uses-permission:'))
assert actual_permissions == permissions
(OUT / 'badging.txt').write_bytes(badging)
run([TOOLS / 'zipalign.exe', '-c', '4', final])
with zipfile.ZipFile(final) as archive:
    assert archive.testzip() is None
    dex_bytes = archive.read('classes.dex')
    for prohibited in (b'Ljava/net/', b'Ljava/lang/ProcessBuilder;', b'Ljava/lang/Runtime;', b'reboot:', b'127.0.0.1', b'setprop', b'Landroid/os/IBinder;'):
        assert prohibited not in dex_bytes, prohibited
proof = {
    'component': 'control-bluetooth', 'version': '0.1',
    'package': 'com.tvbase.bluetoothcontrol', 'version_code': 1,
    'path': final.relative_to(ROOT).as_posix(), 'bytes': final.stat().st_size,
    'sha256': digest(final), 'signer_sha256': SIGNER,
    'permissions': permissions, 'min_sdk': 28, 'target_sdk': 28,
    'purpose': 'explicit_normal_bluetooth_api_control', 'tv_tested': False,
    'validation': {'compiled_api28': True, 'signed_verified_api28': True, 'permissions_exact': True, 'zipalign': True, 'zip_crc': True, 'bounded_static_dex_scan': True},
    'limits': ['No physical validation', '8s is a visual deadline, not server cancellation', 'API acceptance and observed OFF do not prove driver quiescence', 'One in-flight call per process; persisted unfinished request blocks replay after process loss'],
    'sources': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(SRC.iterdir()) if p.is_file()},
    'builder_sha256': digest(Path(__file__)),
}
(OUT / 'componente.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(proof, ensure_ascii=False, indent=2))
