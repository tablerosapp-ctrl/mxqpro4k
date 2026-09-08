"""Reproduce HardwareCollector/0.2 worker/byte-bound tests on the host JVM.

Run with Python 3.10+ from any directory. Each run keeps a new private directory
containing compiled host classes and an exclusive, fsynced, reread result.json.
The APK sources are compiled unchanged; no Android/TV/USB operation is invoked.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
ANDROID = ROOT / 'tools/compilar-android/android-28.jar'
JSON = ROOT / 'tools/pruebas-reconocedor-json/json-20240303.jar'
SOURCE = HERE / 'src/HardwareCollector.java'
HARNESS = HERE / 'tests/HardwareCollectorHarness.java'
RUNNER = Path(__file__).resolve()
EXPECTED = re.compile(r'PASS HardwareCollector/0\.2 host worker and byte-bound cases=(\d+)\s*')
CASES = [
    {'id': 'successful_and_exceptional_actions',
     'checks': '100 consecutive memory-only actions return values and release their slot; an IOException propagates and the slot recovers.'},
    {'id': 'timeout_does_not_release_stuck_worker',
     'checks': 'A latch-controlled action ignores interruption; client timeout returns while the slot remains occupied, 20 new actions are rejected without executing, and real completion releases the slot.'},
    {'id': 'caller_interruption_does_not_release_worker',
     'checks': 'Interrupting the waiting caller preserves its interrupt flag and does not release a still-running underlying action.'},
    {'id': 'bounded_bytes_and_no_progress',
     'checks': 'Input sizes 0/1/6/7/8/20 with cap 7 retain at most cap+1, zero-progress streams fail, and an interrupted reader fails.'},
    {'id': 'invalid_limits_never_start_actions',
     'checks': 'Timeouts -1/0/30001 and byte caps -1/0/1048577 are rejected without occupying the worker slot.'},
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(path):
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError('A required input is not a regular file')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    after = path.stat()
    if (info.st_size, info.st_mtime_ns, info.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise RuntimeError('A required input changed while hashing it')
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': info.st_size, 'sha256': digest.hexdigest()}


def input_hashes(paths):
    return {path.relative_to(ROOT).as_posix(): fingerprint(path) for path in paths}


def run(arguments, commands):
    arguments = [str(value) for value in arguments]
    row = {'argv': arguments, 'cwd': str(ROOT), 'timeout_seconds': 30, 'started_at_utc': utc_now()}
    commands.append(row)
    try:
        completed = subprocess.run(arguments, cwd=ROOT, capture_output=True, timeout=30,
                                   creationflags=0x08000000 if os.name == 'nt' else 0)
    except subprocess.TimeoutExpired as error:
        row.update({'state': 'timeout', 'stdout': (error.stdout or b'').decode('utf-8', 'replace'),
                    'stderr': (error.stderr or b'').decode('utf-8', 'replace'), 'finished_at_utc': utc_now()})
        raise RuntimeError('Host command exceeded its client timeout') from None
    row.update({'state': 'finished', 'exit_code': completed.returncode,
                'stdout': completed.stdout.decode('utf-8', 'replace'),
                'stderr': completed.stderr.decode('utf-8', 'replace'), 'finished_at_utc': utc_now()})
    if completed.returncode != 0:
        raise RuntimeError('Host command returned a nonzero exit code; see the private command log')
    return row['stdout']


def write_receipt(path, result):
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        if stream.write(raw) != len(raw):
            raise RuntimeError('Receipt write was incomplete')
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise RuntimeError('Receipt reread differs from written bytes')
    return hashlib.sha256(raw).hexdigest()


def main():
    private = HERE / 'privado'
    private.mkdir(exist_ok=True)
    if private.resolve() != private.absolute() or getattr(private.lstat(), 'st_file_attributes', 0) & 0x400:
        raise RuntimeError('Private output directory must not be redirected')
    output = Path(tempfile.mkdtemp(prefix='test-hardware-collector-', dir=private)).resolve()
    if not output.is_relative_to(private.resolve()):
        raise RuntimeError('Output directory escaped its private root')
    classes = output / 'classes'
    classes.mkdir()
    result = {
        'schema': 'tvbase-hardware-collector-host-tests-1', 'state': 'failed', 'started_at_utc': utc_now(),
        'clock_source': 'host_PC_UTC_not_device_clock', 'case_count_unit': 'five scenario groups with multiple assertions',
        'expected_cases': CASES, 'commands': [], 'scope': 'host worker bookkeeping and bounded in-memory reads',
        'adapters': [
            'Production HardwareCollector.java is compiled unchanged with ECJ -8 against the Android API 28 compile stubs.',
            'The host JVM executes production readBounded, hasPendingReads and readBytes; java.util.concurrent threads and latches are real host implementations.',
            'Latches simulate an operation that ignores interruption; ByteArrayInputStream and a zero-progress InputStream simulate bounded data reads.',
            'android-28.jar supplies compile/runtime type resolution only. Android Context, SystemClock, Binder, PackageManager, Os, sysfs and codec methods are not invoked by this harness.',
            'json-20240303.jar is available before the Android stub JAR on the runtime classpath; no production Java source is rewritten or replaced.',
        ],
        'not_tested': ['Android UI or lifecycle', 'Android Binder and native kernel interruption',
                       'getprop/uname/id process exit and cleanup on the TV', 'actual sysfs directory traversal or driver binding',
                       'physical byte budget over a full hardware inventory', 'APK installation or device capture',
                       'USB/SAF export, fsync or safe removal', 'MX9 failure reproduction or recovery'],
        'android_tested': False, 'tv_tested': False, 'usb_tested': False,
        'source_rewritten_for_host': False, 'signature_or_independent_attestation': False,
        'receipt_persistence': 'On successful return: O_EXCL creation, file fsync and exact reread; directory fsync is not claimed.',
    }
    try:
        sources = [SOURCE, HARNESS, RUNNER]
        tools = [JAVA, ECJ, ANDROID, JSON]
        before = input_hashes(sources)
        tools_before = input_hashes(tools)
        result['source_files'] = before
        result['tool_files'] = tools_before
        run([JAVA, '-version'], result['commands'])
        run([JAVA, '-jar', ECJ, '-8', '-encoding', 'UTF-8', '-classpath', ANDROID,
             '-d', classes, SOURCE, HARNESS], result['commands'])
        classpath = os.pathsep.join(str(path) for path in (classes, JSON, ANDROID))
        shown = run([JAVA, '-cp', classpath, 'com.tvbase.reconocimiento.HardwareCollectorHarness'], result['commands'])
        matched = EXPECTED.fullmatch(shown)
        if not matched or int(matched.group(1)) != len(CASES):
            raise RuntimeError('Harness output did not confirm all expected scenario groups')
        result['cases'] = int(matched.group(1))
        result['source_unchanged'] = before == input_hashes(sources)
        result['tools_unchanged'] = tools_before == input_hashes(tools)
        if not result['source_unchanged'] or not result['tools_unchanged']:
            raise RuntimeError('Inputs changed during the host test')
        result['class_files'] = [fingerprint(path) for path in sorted(classes.rglob('*.class'))]
        result['state'] = 'passed'
    except Exception as error:
        result['error_type'] = type(error).__name__
        result['error'] = str(error)
    result['finished_at_utc'] = utc_now()
    receipt = output / 'result.json'
    digest = write_receipt(receipt, result)
    print(json.dumps({'state': result['state'], 'cases': result.get('cases', 0), 'receipt': str(receipt),
                      'receipt_sha256': digest, 'scope': result['scope']}, ensure_ascii=False, indent=2))
    return 0 if result['state'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
