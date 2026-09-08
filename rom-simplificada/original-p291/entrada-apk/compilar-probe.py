"""Build an unsigned app_process DEX/JAR locally; no TV, USB, keys or APK install."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JAVA = ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
TOOLS = ROOT/'tools/verificacion-apk/build-tools-37/android-37.0'
SDK = ROOT/'tools/compilar-android/android-28.jar'
ECJ = ROOT/'tools/compilar-android/ecj-3.39.0.jar'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    out = HERE/'privado'/('probe-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    out.mkdir(parents=True, exist_ok=False)

    def run(args):
        result = subprocess.run([str(x) for x in args], capture_output=True, creationflags=0x08000000)
        with (out/'build.log').open('ab') as stream:
            stream.write(result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError('Build/check failed: '+str(out/'build.log'))
        return result.stdout.decode('utf8', 'replace')

    source = [HERE/'RootProbe.java', HERE/'ProbeContract.java']
    classes = out/'classes'; classes.mkdir()
    run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-bootclasspath',SDK,'-d',classes,*source])
    dex = out/'dex'; dex.mkdir()
    run([JAVA,'-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',SDK,
         '--output',dex,*sorted(classes.rglob('*.class'))])
    jar = out/'tvbase-root-probe-0.1.jar'
    with zipfile.ZipFile(jar, 'x', compression=zipfile.ZIP_STORED) as archive:
        archive.write(dex/'classes.dex', 'classes.dex')
    host = out/'host-classes'; host.mkdir()
    run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-d',host,HERE/'ProbeContract.java',HERE/'ProbeContractTest.java'])
    tests = run([JAVA,'-cp',host,'local.tvbase.acceso.ProbeContractTest'])
    assert '17 host checks passed' in tests, tests
    with zipfile.ZipFile(jar) as archive:
        assert archive.namelist() == ['classes.dex'] and archive.read('classes.dex') == (dex/'classes.dex').read_bytes()
    receipt = {'state':'compiled_host_checked','date_utc':datetime.now(timezone.utc).isoformat(),
               'jar':jar.relative_to(ROOT).as_posix(),'jar_bytes':jar.stat().st_size,'jar_sha256':sha(jar),
               'dex':(dex/'classes.dex').relative_to(ROOT).as_posix(),'dex_sha256':sha(dex/'classes.dex'),
               'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in source},
               'test_source_sha256':sha(HERE/'ProbeContractTest.java'),'compiler_sha256':sha(Path(__file__)),
               'min_api':28,'javac_source_target':'8','host_contract_checks':17,'host_result':tests.strip(),
               'android_apis_tested_on_host':False,'root_app_process_tested':False,'fsync_tested_on_device':False,
               'tv_accessed':False,'usb_accessed':False,'firmware_written':False,
               'allowed_destination':'/data/local/tmp/tvbase-entry-probe-<32 lowercase hex nonce>/probe.bin',
               'repeat_policy':'one explicit execution; an existing directory is rejected; never retry automatically'}
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (HERE/'PROBE-COMPILADO.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
