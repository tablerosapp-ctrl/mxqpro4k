"""Host fixtures for explicit Downloads export; never touches physical media."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
JSON = ROOT / 'tools/pruebas-reconocedor-json/json-20240303.jar'


def run(arguments):
    process = subprocess.run([str(value) for value in arguments], capture_output=True,
                             timeout=60, creationflags=0x08000000)
    if process.returncode:
        raise RuntimeError((process.stdout + process.stderr).decode('utf-8', 'replace'))
    return process.stdout


def main():
    sources = [HERE / 'src/LocalExport.java', HERE / 'src/ReportArchive.java',
               HERE / 'tests/LocalExportHarness.java', Path(__file__).resolve()]
    def hashes():
        return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sources}
    before = hashes()
    private = HERE / 'privado'
    private.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='test-local-export-', dir=private))
    classes = output / 'classes'
    classes.mkdir()
    run([JAVA, '-jar', ECJ, '-8', '-encoding', 'UTF-8', '-cp', JSON, '-d', classes, *sources[:3]])
    result = json.loads(run([JAVA, '-cp', str(classes) + ';' + str(JSON),
                             'com.tvbase.reconocimiento.LocalExportHarness', output / 'fixture']))
    if before != hashes():
        raise RuntimeError('Source changed during host tests')
    result.update(source_sha256=before, source_unchanged=True, android_tested=False,
                  usb_tested=False, directory_persistence_verified=False)
    with (output / 'result.json').open('x', encoding='utf-8') as receipt:
        json.dump(result, receipt, ensure_ascii=False, indent=2)
        receipt.write('\n')
    print(json.dumps({'state': result['state'], 'cases': result['cases'],
                      'symlink_skipped': result['symlink_skipped'],
                      'receipt': str(output / 'result.json'), 'scope': result['scope']}, indent=2))


if __name__ == '__main__':
    main()
