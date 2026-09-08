"""Compile isolated P291 components; no TV or earlier build outputs are changed."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'privado/componentes'
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
TOOLS = ROOT / 'tools/verificacion-apk/build-tools-37/android-37.0'
SDK = ROOT / 'tools/compilar-android/android-28.jar'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
KEYS = ROOT / 'rom-simplificada/claves-desarrollo'


def run(args, log):
    p = subprocess.run([str(x) for x in args], capture_output=True, timeout=120, creationflags=0x08000000)
    with log.open('ab') as stream:
        stream.write(p.stdout + p.stderr)
    if p.returncode:
        raise RuntimeError('Local compiler failed; inspect private build log')
    return p.stdout


def main():
    assert not OUT.exists(), 'Preserve existing component outputs'
    assert (KEYS / 'componentes.jks').is_file() and (KEYS / 'password.txt').is_file()
    OUT.mkdir(parents=True)
    records = []
    for name in ('inicio', 'webview-overlay', 'defaults'):
        src, dest = HERE / 'componentes' / name, OUT / name
        dest.mkdir()
        log = dest / 'build.log'
        unsigned = dest / 'unsigned.apk'
        args = [TOOLS/'aapt2.exe', 'link', '-I', SDK, '--manifest', src/'AndroidManifest.xml',
                '-o', unsigned, '--min-sdk-version', '28', '--target-sdk-version', '28',
                '--no-resource-deduping', '--no-resource-removal']
        if (src / 'res').exists():
            run([TOOLS/'aapt2.exe', 'compile', '--dir', src/'res', '-o', dest/'resources.zip'], log)
            args.append(dest/'resources.zip')
        run(args, log)
        if name == 'inicio':
            classes, dex = dest/'classes', dest/'dex'
            classes.mkdir(); dex.mkdir()
            run([JAVA, '-jar', ECJ, '-8', '-encoding', 'UTF-8', '-bootclasspath', SDK,
                 '-d', classes, *sorted(src.glob('*.java'))], log)
            run([JAVA, '-cp', TOOLS/'lib/d8.jar', 'com.android.tools.r8.D8', '--min-api', '28',
                 '--lib', SDK, '--output', dex, *sorted(classes.rglob('*.class'))], log)
            with zipfile.ZipFile(unsigned, 'a') as archive:
                archive.write(dex/'classes.dex', 'classes.dex')
        run([TOOLS/'zipalign.exe', '-f', '4', unsigned, dest/'aligned.apk'], log)
        final = dest/(name+'.apk')
        run([JAVA, '-jar', TOOLS/'lib/apksigner.jar', 'sign', '--ks', KEYS/'componentes.jks',
             '--ks-key-alias', 'tvbase-development', '--ks-pass', 'file:'+str(KEYS/'password.txt'),
             '--out', final, dest/'aligned.apk'], log)
        verify = run([JAVA, '-jar', TOOLS/'lib/apksigner.jar', 'verify', '--verbose', '--print-certs',
                      '--min-sdk-version', '28', '--max-sdk-version', '28', final], log)
        (dest/'firma.txt').write_bytes(verify)
        with final.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        records.append({'component': name, 'path': final.relative_to(ROOT).as_posix(),
                        'bytes': final.stat().st_size, 'sha256': digest, 'signature_verified_api28': True})
    (HERE/'COMPONENTES.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf8')
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
