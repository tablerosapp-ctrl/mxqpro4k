"""Build a new recognition APK from sources; no device or USB access."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
TOOLS=ROOT/'tools/verificacion-apk/build-tools-37/android-37.0'
SDK=ROOT/'tools/compilar-android/android-28.jar'
ECJ=ROOT/'tools/compilar-android/ecj-3.39.0.jar'
KEY=ROOT/'rom-simplificada/claves-desarrollo/componentes.jks'
PASSWORD=KEY.with_name('password.txt')
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=HERE/'privado'/('build-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    out.mkdir(parents=True,exist_ok=False)
    sources={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((HERE/'src').glob('*')) if p.is_file()}
    signing={p.name:sha(p) for p in (KEY,PASSWORD)}
    def run(args):
        p=subprocess.run([str(a) for a in args],capture_output=True,creationflags=0x08000000)
        with (out/'build.log').open('ab') as f:f.write(p.stdout+p.stderr)
        if p.returncode:raise RuntimeError('Build error; inspect '+str(out/'build.log'))
        return p.stdout
    classes=out/'classes';classes.mkdir()
    run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-bootclasspath',SDK,'-d',classes,*sorted((HERE/'src').glob('*.java'))])
    dex=out/'dex';dex.mkdir()
    run([JAVA,'-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','21','--lib',SDK,'--output',dex,*sorted(classes.rglob('*.class'))])
    unsigned=out/'unsigned.apk'
    run([TOOLS/'aapt2.exe','link','-I',SDK,'--manifest',HERE/'src/AndroidManifest.xml','-o',unsigned,'--min-sdk-version','21','--target-sdk-version','28'])
    with zipfile.ZipFile(unsigned,'a') as z:z.write(dex/'classes.dex','classes.dex')
    aligned=out/'aligned.apk';run([TOOLS/'zipalign.exe','-f','4',unsigned,aligned])
    final=out/'Reconocimiento-TVBase-0.1.apk'
    run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','sign','--ks',KEY,'--ks-key-alias','tvbase-development','--ks-pass','file:'+str(PASSWORD),'--out',final,aligned])
    proof=run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','verify','--verbose','--print-certs','--min-sdk-version','21',final]);(out/'signature.txt').write_bytes(proof)
    signer='d2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613'
    assert signer.encode() in proof
    badging=run([TOOLS/'aapt2.exe','dump','badging',final]);(out/'badging.txt').write_bytes(badging)
    assert b"name='com.tvbase.reconocimiento'" in badging and b"versionName='0.1'" in badging and b"minSdkVersion:'21'" in badging
    xml=run([TOOLS/'aapt2.exe','dump','xmltree',final,'--file','AndroidManifest.xml']);(out/'manifest.txt').write_bytes(xml)
    for forbidden in [b'android.permission.INTERNET',b'android.permission.REBOOT',b'android.permission.RECOVERY',b'android.permission.INSTALL_PACKAGES',b'android:sharedUserId']:
        assert forbidden not in xml,forbidden
    assert signing=={p.name:sha(p) for p in (KEY,PASSWORD)}
    assert sources=={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((HERE/'src').glob('*')) if p.is_file()}
    with zipfile.ZipFile(final) as z:assert z.testzip() is None
    result={'state':'built_verified_pc','version':'0.1','package':'com.tvbase.reconocimiento','min_api':21,'target_api':28,'apk':final.relative_to(ROOT).as_posix(),'bytes':final.stat().st_size,'sha256':sha(final),'source_sha256':sources,'signer_sha256':signer,'signing_inputs_unchanged':True,'network_permission':False,'root_or_adb':False,'tv_tested':False,'usb_export_on_android_tested':False,'created_at':datetime.now(timezone.utc).isoformat()}
    (out/'receipt.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (HERE/'COMPILACION.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
