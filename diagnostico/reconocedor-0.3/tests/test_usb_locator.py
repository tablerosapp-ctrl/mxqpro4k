"""Compile unchanged UsbLocator/0.3 and run its virtual-filesystem host tests.

Run with Python 3.10+ from any directory. Each run preserves a new private
classes directory and an exclusive, fsynced, reread result.json. No Android or
real USB probe is invoked; source and tool hashes are recorded before/after.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
ANDROID = ROOT / 'tools/compilar-android/android-28.jar'
JSON = ROOT / 'tools/pruebas-reconocedor-json/json-20240303.jar'
SOURCE = HERE / 'src/UsbLocator.java'
HARNESS = HERE / 'tests/UsbLocatorHarness.java'
RUNNER = Path(__file__).resolve()
CASES = [
    'nested_oem_path', 'mount_parsers_environment_and_spaces', 'volume_hint_and_usb_root_wildcard',
    'same_marker_different_volumes_not_merged', 'dev_inode_and_canonical_alias_rules',
    'strict_marker_schema_id_size_and_duplicates', 'depth_three_and_no_user_data_tree',
    'canonical_escape_and_identity_change_rejected', 'denials_directory_arrays_entries_and_diagnostics_bounded',
    'timeout_retains_single_worker_and_snapshot_is_immutable', 'bounded_reads_and_malformed_mounts',
]


def now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(path):
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise RuntimeError('Input changed while hashing')
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': after.st_size, 'sha256': digest.hexdigest()}


def fingerprints(paths):
    return {path.relative_to(ROOT).as_posix(): fingerprint(path) for path in paths}


def execute(argv, commands):
    row = {'argv': [str(value) for value in argv], 'cwd': str(ROOT), 'timeout_seconds': 30, 'started_at_utc': now()}
    commands.append(row)
    try:
        process = subprocess.run(row['argv'], cwd=ROOT, capture_output=True, timeout=30,
                                 creationflags=0x08000000 if os.name == 'nt' else 0)
    except subprocess.TimeoutExpired as error:
        row.update({'state': 'timeout', 'stdout': (error.stdout or b'').decode('utf-8', 'replace'),
                    'stderr': (error.stderr or b'').decode('utf-8', 'replace'), 'finished_at_utc': now()})
        raise RuntimeError('Host command exceeded its client timeout') from None
    row.update({'state': 'finished', 'exit_code': process.returncode,
                'stdout': process.stdout.decode('utf-8', 'replace'),
                'stderr': process.stderr.decode('utf-8', 'replace'), 'finished_at_utc': now()})
    if process.returncode:
        raise RuntimeError('Host command failed; see the private command log')
    return row['stdout']


def main():
    private = HERE / 'privado'
    private.mkdir(exist_ok=True)
    if private.resolve() != private.absolute() or getattr(private.lstat(), 'st_file_attributes', 0) & 0x400:
        raise RuntimeError('Private output directory must not be redirected')
    output = Path(tempfile.mkdtemp(prefix='test-usb-locator-', dir=private)).resolve()
    if not output.is_relative_to(private.resolve()):
        raise RuntimeError('Output escaped private directory')
    classes = output / 'classes'
    classes.mkdir()
    result = {
        'schema': 'tvbase-usb-locator-host-tests-1', 'state': 'failed', 'started_at_utc': now(),
        'clock_source': 'host_PC_UTC_not_device_clock', 'commands': [], 'expected_case_ids': CASES,
        'scope': 'virtual filesystem discovery policy and real host Java worker gate',
        'adapters': [
            'Production UsbLocator.java is compiled unchanged with ECJ -8 against Android API 28 stubs.',
            'Fake Probe uses in-memory maps for directories, canonical paths, marker bytes and filesystem dev/inode; it never calls FileProbe or real Android/USB paths.',
            'Host JVM threads and latches exercise the actual separate UsbLocator worker, including an operation that ignores interruption.',
            'The host JSON implementation json-20240303.jar replaces Android org.json at runtime; the strict marker matcher and path policy remain production code.',
            'Fake dev/inode values test alias policy only; they do not validate Android Os.stat or prove physical USB identity.',
        ],
        'not_tested': ['physical MX9/OEM storage layout', 'Android Os.stat adapter or permissions',
                       'actual native directory-read interruption', 'StorageVolume APIs',
                       'real marker reads, write permission, USB/SAF export or fsync',
                       'APK installation, UI chooser, fallback app-specific storage or physical USB removal'],
        'tv_tested': False, 'usb_tested': False, 'android_tested': False, 'source_rewritten_for_host': False,
        'signature_or_independent_attestation': False,
        'receipt_persistence': 'Successful runner return requires exclusive creation, file fsync and exact reread; directory fsync is not claimed.',
    }
    try:
        sources, tools = [SOURCE, HARNESS, RUNNER], [JAVA, ECJ, ANDROID, JSON]
        before, tools_before = fingerprints(sources), fingerprints(tools)
        result['source_files'], result['tool_files'] = before, tools_before
        execute([JAVA, '-version'], result['commands'])
        execute([JAVA, '-jar', ECJ, '-8', '-encoding', 'UTF-8', '-classpath', ANDROID,
                 '-d', classes, SOURCE, HARNESS], result['commands'])
        text = execute([JAVA, '-cp', os.pathsep.join(str(path) for path in (classes, JSON)),
                        'com.tvbase.reconocimiento.UsbLocatorHarness'], result['commands'])
        outcome = json.loads(text)
        if outcome.get('state') != 'passed' or outcome.get('cases') != len(CASES) or outcome.get('case_ids') != CASES:
            raise RuntimeError('Harness did not confirm every expected scenario')
        result['harness_result'] = outcome
        result['cases'] = outcome['cases']
        result['source_unchanged'] = fingerprints(sources) == before
        result['tools_unchanged'] = fingerprints(tools) == tools_before
        if not result['source_unchanged'] or not result['tools_unchanged']:
            raise RuntimeError('Inputs changed during host tests')
        result['class_files'] = [fingerprint(path) for path in sorted(classes.rglob('*.class'))]
        result['state'] = 'passed'
    except Exception as error:
        result['error_type'], result['error'] = type(error).__name__, str(error)
    result['finished_at_utc'] = now()
    receipt = output / 'result.json'
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with receipt.open('xb') as stream:
        if stream.write(raw) != len(raw):
            raise RuntimeError('Incomplete receipt write')
        stream.flush()
        os.fsync(stream.fileno())
    if receipt.read_bytes() != raw:
        raise RuntimeError('Receipt reread mismatch')
    print(json.dumps({'state': result['state'], 'cases': result.get('cases', 0), 'receipt': str(receipt),
                      'receipt_sha256': hashlib.sha256(raw).hexdigest()}, ensure_ascii=False, indent=2))
    return 0 if result['state'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
