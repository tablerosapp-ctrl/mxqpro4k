"""Build revision 0.1.2 installer, then package reviewed system/vendor images.

All outputs are new. No device/USB access. Original signing helpers are loaded
by AST so importing the older packager cannot recreate its retired payload dir.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.serialization import pkcs7

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REV = ROOT / 'rom-simplificada/trabajo/revision-0.1.2'
BUILD = REV / 'instalador'
WORK = REV / 'paquete'
OUT = ROOT / 'rom-simplificada/salida'
VERSION = '0.1.2'
PACKAGE_ID = 'TVBASE-P291-A9-0.1.2'
BASE = OUT / 'TVBASE-P291-A9-0.1.1-RECOVERY.zip'
BASE_SHA = 'e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205'
FINAL = OUT / (PACKAGE_ID + '-RECOVERY.zip')
REPORT = OUT / 'RECOVERY-VERIFICACION-0.1.2.json'
MANIFEST = HERE / 'manifest-0.1.2.json'
GO = ROOT / 'tools/instalador-go/go/bin/go.exe'
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
SIGNING = ROOT / 'tools/firmar-ota'
CERT_SHA = 'a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc'
GO_SOURCES = ('go.mod', 'package.go', 'package_test.go', 'main_linux.go', 'main_windows.go')
NAMES = ('system', 'vendor', 'product', 'odm', 'boot')


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def json_new(path, data):
    with path.open('x', encoding='utf8', newline='\n') as target:
        json.dump(data, target, ensure_ascii=False, indent=2)
        target.write('\n')
        target.flush()
        os.fsync(target.fileno())


def run(args, log_name, env=None, expected=0):
    proc = subprocess.run(list(map(str, args)), cwd=HERE, env=env,
                          capture_output=True, creationflags=0x08000000)
    with (BUILD / log_name).open('xb') as log:
        log.write(proc.stdout + proc.stderr)
    if expected is None:
        assert proc.returncode != 0, 'Unexpected acceptance of the previous package'
    else:
        assert proc.returncode == expected, proc.stderr.decode('utf8', 'replace')[:2000]
    return proc


def signature_helper():
    source = (HERE / 'empaquetar.py').read_text(encoding='utf8')
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('der', 'children', 'verify_signature')]
    assert {node.name for node in functions} == {'der', 'children', 'verify_signature'}
    scope = dict(struct=struct, hashlib=hashlib, pkcs7=pkcs7, hashes=hashes,
                 padding=padding, utils=utils)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(HERE / 'empaquetar.py'), 'exec'), scope)
    return scope['verify_signature']


def verify_elf(path):
    data = path.read_bytes()
    assert data[:7] == b'\x7fELF\x01\x01\x01' and struct.unpack_from('<H', data, 18)[0] == 40
    offset = struct.unpack_from('<I', data, 28)[0]
    stride, count = struct.unpack_from('<HH', data, 42)
    assert all(struct.unpack_from('<I', data, offset + n * stride)[0] != 3 for n in range(count))


def build_installers():
    assert not BUILD.exists(), 'Installer output already exists; review it rather than overwriting.'
    BUILD.mkdir(parents=True)
    env = os.environ.copy()
    env.update(GOROOT=str(GO.parents[1]), GOCACHE=str(BUILD / 'go-cache'),
               GOMODCACHE=str(BUILD / 'go-mod-cache'), GOPROXY='off',
               GOTOOLCHAIN='local', CGO_ENABLED='0', GOOS='windows', GOARCH='amd64')
    ldflags = '-s -w -X main.allowedPackageID=' + PACKAGE_ID
    print('Compilando instaladores y ejecutando pruebas Go existentes', flush=True)
    run([GO, 'test', '-count=1', '-json', '-ldflags', ldflags, '.'], 'go-tests.jsonl', env)
    test_events = [json.loads(line) for line in (BUILD / 'go-tests.jsonl').read_text(encoding='utf8').splitlines() if line.startswith('{')]
    passed = [event['Test'] for event in test_events if event.get('Action') == 'pass' and 'Test' in event]
    assert 'TestPackageChecks' in passed and 'TestExactCopy' in passed
    run([GO, 'build', '-trimpath', '-buildvcs=false', '-ldflags', ldflags, '-o', BUILD / 'verify-package.exe', '.'], 'go-windows.log', env)
    env.update(GOOS='linux', GOARCH='arm', GOARM='7')
    run([GO, 'build', '-trimpath', '-buildvcs=false', '-ldflags', ldflags, '-o', BUILD / 'update-binary', '.'], 'go-arm.log', env)
    verify_elf(BUILD / 'update-binary')
    assert sha(BASE) == BASE_SHA
    rejected = run([BUILD / 'verify-package.exe', BASE], 'old-package-rejected.log', expected=None)
    assert b'perfil de paquete no permitido' in rejected.stderr
    host = BUILD / 'openjdk'; host.mkdir()
    run([JAVA, '-jar', ECJ, '-8', '-encoding', 'UTF-8', '-d', host, HERE / 'VerifyWholeZip.java'], 'openjdk-compile.log')
    receipt = {
        'version': VERSION, 'package_id': PACKAGE_ID, 'ldflags': ldflags,
        'go_version': (GO.parents[1] / 'VERSION').read_text().splitlines()[0],
        'linux_arch': 'arm', 'goarm': '7', 'cgo_enabled': False,
        'installer_binary': (BUILD / 'update-binary').relative_to(ROOT).as_posix(),
        'installer_sha256': sha(BUILD / 'update-binary'),
        'validator': (BUILD / 'verify-package.exe').relative_to(ROOT).as_posix(),
        'validator_sha256': sha(BUILD / 'verify-package.exe'),
        'go_tests_passed': passed, 'previous_package_rejected': True,
        'previous_package_sha256': BASE_SHA, 'previous_package_rejection_exit': rejected.returncode,
        'go_sources': {name: sha(HERE / name) for name in GO_SOURCES},
        'openjdk_verifier_source_sha256': sha(HERE / 'VerifyWholeZip.java'),
        'openjdk_verifier_class_sha256': sha(host / 'VerifyWholeZip.class'),
        'physically_tested': False,
    }
    json_new(BUILD / 'compilacion.json', receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def read_review(path):
    assert path.resolve() == (REV / 'revision.json').resolve()
    revision = json.loads(path.read_text(encoding='utf8'))
    assert revision['version'] == VERSION and revision['package_id'] == PACKAGE_ID
    assert revision['fsck_exit'] == 0
    assert revision['bluetooth_disabled'] is True
    assert revision['inherited_recovery_replacement_disabled'] is True
    paths = {}
    for name in ('system', 'vendor'):
        raw_path = Path(revision[name + '_image'])
        assert not raw_path.is_absolute(), 'Image paths must be workspace-relative'
        image = (ROOT / raw_path).resolve()
        assert image.is_relative_to(REV.resolve()) and image.is_file() and not image.is_symlink()
        expected = revision[name + '_sha256']
        assert re.fullmatch('[0-9a-f]{64}', expected) and sha(image) == expected
        paths[name] = image
    receipt = json.loads((BUILD / 'compilacion.json').read_text(encoding='utf8'))
    assert receipt['package_id'] == PACKAGE_ID and receipt['previous_package_rejected'] is True
    for name, expected in receipt['go_sources'].items():
        assert sha(HERE / name) == expected, 'Go sources changed since build'
    assert sha(BUILD / 'update-binary') == receipt['installer_sha256']
    assert sha(BUILD / 'verify-package.exe') == receipt['validator_sha256']
    assert sha(BUILD / 'openjdk/VerifyWholeZip.class') == receipt['openjdk_verifier_class_sha256']
    verify_elf(BUILD / 'update-binary')
    return revision, paths, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--revision-report', type=Path)
    args = parser.parse_args()
    if args.build_only:
        assert args.revision_report is None
        build_installers()
        return
    assert args.revision_report is not None, '--revision-report required after images are reviewed'
    assert not any(p.exists() for p in (FINAL, REPORT, MANIFEST, WORK)), 'New output required; no verified releases are overwritten'
    revision, paths, build_receipt = read_review(args.revision_report)
    assert sha(BASE) == BASE_SHA
    cert = x509.load_pem_x509_certificate((SIGNING / 'testkey.x509.pem').read_bytes())
    assert cert.fingerprint(hashes.SHA256()).hex() == CERT_SHA
    verify_signature = signature_helper()
    assert verify_signature(BASE, cert) == CERT_SHA
    with zipfile.ZipFile(BASE) as base:
        assert len(base.namelist()) == len(set(base.namelist()))
        old = json.loads(base.read('tvbase/manifest.json'))
        assert old['id'] == 'TVBASE-P291-A9-0.1.1'
        assert tuple(image['name'] for image in old['images']) == NAMES
        assert old['format'] == 1 and old['dt_id'] == 'gxlx2_p291_1g'
        assert old['media_id'] == 'TVBASE-P291-20260906-4dc82786'
        manifest = dict(old, id=PACKAGE_ID, images=[])
        for previous in old['images']:
            image = dict(previous)
            assert image['entry'] == 'tvbase/' + image['name'] + '.img'
            if image['name'] in paths:
                current = paths[image['name']]
                assert current.stat().st_size == previous['size'], 'Partition image size changed'
                image['sha256'] = revision[image['name'] + '_sha256']
                assert image['sha256'] != previous['sha256'], 'Expected reviewed Bluetooth change missing'
            manifest['images'].append(image)
        WORK.mkdir()
        unsigned = WORK / ('unsigned-' + VERSION + '.zip')
        with zipfile.ZipFile(unsigned, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=False) as package:
            for image in manifest['images']:
                print('Empaquetando', image['name'], image['size'], flush=True)
                digest = hashlib.sha256(); total = 0
                src = paths[image['name']].open('rb') if image['name'] in paths else base.open(image['entry'])
                with src, package.open(image['entry'], 'w') as target:
                    while chunk := src.read(4 << 20):
                        target.write(chunk); digest.update(chunk); total += len(chunk)
                assert total == image['size'] and digest.hexdigest() == image['sha256']
            binary_info = zipfile.ZipInfo('META-INF/com/google/android/update-binary', (2026, 9, 7, 0, 0, 0))
            binary_info.external_attr = 0o100755 << 16
            package.writestr(binary_info, (BUILD / 'update-binary').read_bytes())
            package.writestr('tvbase/manifest.json', json.dumps(manifest, indent=2))
            for unchanged in ('META-INF/com/android/metadata', 'META-INF/com/android/otacert'):
                package.writestr(unchanged, base.read(unchanged))
    print('Firmando ZIP completo 0.1.2 con la clave AOSP existente', flush=True)
    raw = unsigned.read_bytes()
    assert raw[-22:-18] == b'PK\x05\x06' and raw[-2:] == b'\0\0'
    key = serialization.load_der_private_key((SIGNING / 'testkey.pk8').read_bytes(), password=None)
    signature = pkcs7.PKCS7SignatureBuilder().set_data(raw[:-2]).add_signer(cert, key, hashes.SHA256()).sign(
        serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary, pkcs7.PKCS7Options.NoAttributes])
    message = b'TVBASE experimental AOSP testkey\0'
    length = len(message) + len(signature) + 6
    comment = message + signature + struct.pack('<H2sH', len(signature) + 6, b'\xff\xff', length)
    assert length <= 65535 and b'PK\x05\x06' not in comment
    with FINAL.open('xb') as final:
        final.write(raw[:-2]); final.write(struct.pack('<H', length)); final.write(comment)
        final.flush(); os.fsync(final.fileno())
    del raw, key
    assert verify_signature(FINAL, cert) == CERT_SHA
    with zipfile.ZipFile(FINAL) as package:
        assert package.testzip() is None
        for image in manifest['images']:
            with package.open(image['entry']) as source:
                assert hashlib.file_digest(source, 'sha256').hexdigest() == image['sha256']
            assert package.getinfo(image['entry']).file_size == image['size']
        assert hashlib.sha256(package.read('META-INF/com/google/android/update-binary')).hexdigest() == build_receipt['installer_sha256']
        assert json.loads(package.read('tvbase/manifest.json')) == manifest
    run([BUILD / 'verify-package.exe', FINAL], 'new-package-accepted.log')
    run([JAVA, '-Xmx3g', '--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED', '-cp', BUILD / 'openjdk', 'VerifyWholeZip', FINAL], 'openjdk-signature-verified.log')
    assert sha(BASE) == BASE_SHA, 'Base ZIP changed during packaging'
    result = {
        'file': FINAL.relative_to(ROOT).as_posix(), 'version': VERSION, 'package_id': PACKAGE_ID,
        'bytes': FINAL.stat().st_size, 'sha256': sha(FINAL), 'manifest': manifest,
        'base_zip_sha256': BASE_SHA, 'base_zip_unchanged_after': True,
        'inherited_payloads_byte_identical': ['product', 'odm', 'boot'],
        'bluetooth_disabled': True, 'inherited_recovery_replacement_disabled': True,
        'whole_file_signature_verified': True, 'openjdk_whole_file_signature_verified': True,
        'certificate_sha256': CERT_SHA, 'payload_sha256_verified': True,
        'windows_installer_accepts_new_payload': True, 'windows_installer_rejects_previous_package': True,
        'installer_elf': 'ARM32 static, no PT_INTERP',
        'installer_binary': build_receipt['installer_binary'], 'installer_sha256': build_receipt['installer_sha256'],
        'preserved_partitions': ['bootloader', 'recovery', 'dtb', 'dtbo', 'vbmeta', 'data', 'keys', 'env', 'misc'],
        'original_partition_backup_required': True, 'hardware_compatibility_confirmed': False,
        'first_tv_recovery_accepts_signature': False, 'physically_installed': False,
        'revision_report': args.revision_report.resolve().relative_to(ROOT).as_posix(),
        'revision_report_sha256': sha(args.revision_report), 'reviewed_revision': revision,
        'builder_sha256': sha(Path(__file__)), 'signature_helper_source_sha256': sha(HERE / 'empaquetar.py'),
        'installer_build_receipt_sha256': sha(BUILD / 'compilacion.json'),
        'signature_helper_loading': 'AST functions der/children/verify_signature only; original main and module side effects not executed',
    }
    json_new(MANIFEST, manifest)
    json_new(REPORT, result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
