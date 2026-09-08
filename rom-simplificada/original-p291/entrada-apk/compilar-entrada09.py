"""Build USB entry 0.9 offline. Final signing requires exact ROM and reviewed source hashes."""
import argparse
from datetime import datetime,timezone
import hashlib,json,subprocess,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SRC=HERE/'src'
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
TOOLS=ROOT/'tools/verificacion-apk/build-tools-37/android-37.0'
SDK=ROOT/'tools/compilar-android/android-28.jar'
ECJ=ROOT/'tools/compilar-android/ecj-3.39.0.jar'
KEY=ROOT/'rom-simplificada/claves-desarrollo/componentes.jks'
PASSWORD=KEY.with_name('password.txt')
ENV_SHA='4a769455ff8fdfd7a84d65c781259e34ca94657a833d8d55222b16acac2c31f6'
BCB_SHA='60e06b0f4afd4db33faef964133a5aa08991e42932b11302c72a36881a834e1b'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check-only',action='store_true',help='Compile API28 classes only, without a ZIP hash, APK or signing')
    parser.add_argument('--rom-receipt',type=Path)
    parser.add_argument('--method-review',type=Path)
    args=parser.parse_args()
    sources={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(SRC.iterdir()) if p.is_file()}
    zip_name='TVBASE-P291-A9-0.2.1-RECOVERY.zip';zip_sha='';zip_bytes=0;review=None
    if not args.check_only:
        assert args.rom_receipt and args.method_review,'Final build requires ROM receipt and independent method review'
        rom=json.loads(args.rom_receipt.read_text(encoding='utf8'))
        assert rom['package_id']=='TVBASE-P291-A9-0.2.1' and rom['operation']=='install_reviewed_with_userdata_migration'
        assert rom['data_policy']=='backup_raw_userdata_then_format_ext4'
        zip_path=(ROOT/rom['file']).resolve()
        assert zip_path.is_relative_to(ROOT) and zip_path.name==zip_name
        assert zip_path.stat().st_size==rom['bytes'] and sha(zip_path)==rom['sha256']
        assert rom['payload_sha256_verified'] and rom['zip_crc_verified'] and rom['openjdk_signature_verified']
        zip_sha=rom['sha256'];zip_bytes=rom['bytes']
        review=json.loads(args.method_review.read_text(encoding='utf8'))
        assert review['state']=='reviewed_offline' and review['approved'] is True
        assert review['source_sha256']==sources,'Reviewed sources changed'
        assert review['env_record_sha256']==ENV_SHA and review['bcb_prefix_sha256']==BCB_SHA
        assert review['detached_method_reviewed'] is True and review['no_automatic_reset'] is True
        rom_receipt_sha=sha(args.rom_receipt);review_receipt_sha=sha(args.method_review)
    out=HERE/'privado'/('entrada09-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    out.mkdir(parents=True,exist_ok=False)
    def run(command):
        result=subprocess.run([str(x) for x in command],capture_output=True,creationflags=0x08000000)
        with (out/'build.log').open('ab') as stream:stream.write(result.stdout+result.stderr)
        if result.returncode:raise RuntimeError('Build failed: '+str(out/'build.log'))
        return result.stdout
    policy=out/'EntryPolicy.java'
    policy.write_text('package local.tvbase.acceso;\nfinal class EntryPolicy {\n'
        +' static final boolean METHOD_REVIEWED='+('false' if args.check_only else 'true')+';\n'
        +' static final String ZIP_NAME='+json.dumps(zip_name)+';\n'
        +' static final String ZIP_SHA='+json.dumps(zip_sha)+';\n'
        +' static final long ZIP_BYTES='+str(zip_bytes)+'L;\n'
        +' static final String ENV_RECORD_SHA="'+ENV_SHA+'";\n'
        +' static final String BCB_PREFIX_SHA="'+BCB_SHA+'";\n}\n',encoding='utf8')
    classes=out/'classes';classes.mkdir()
    run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-bootclasspath',SDK,'-d',classes,*sorted(SRC.glob('*.java')),policy])
    record={'state':'api28_compilation_checked' if args.check_only else 'compiled_reviewed',
            'date_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':sources,
            'generated_policy_sha256':sha(policy),'builder_sha256':sha(Path(__file__)),
            'method_reviewed':not args.check_only,'apk_built':not args.check_only,
            'physical_preparation_tested':False,'usb_fsync_tested':False,'automatic_reset':False}
    if args.check_only:
        (out/'check-result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
        print(json.dumps({'state':record['state'],'output':out.relative_to(ROOT).as_posix()},indent=2));return
    key_before={str(p):sha(p) for p in (KEY,PASSWORD)}
    dex=out/'dex';dex.mkdir()
    run([JAVA,'-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',SDK,'--output',dex,*sorted(classes.rglob('*.class'))])
    unsigned=out/'unsigned.apk'
    run([TOOLS/'aapt2.exe','link','-I',SDK,'--manifest',SRC/'AndroidManifest.xml','-o',unsigned,'--min-sdk-version','28','--target-sdk-version','28'])
    with zipfile.ZipFile(unsigned,'a') as archive:archive.write(dex/'classes.dex','classes.dex')
    aligned=out/'aligned.apk';run([TOOLS/'zipalign.exe','-f','4',unsigned,aligned])
    final=out/'AccesoUSB-0.9.apk'
    run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','sign','--ks',KEY,'--ks-key-alias','tvbase-development','--ks-pass','file:'+str(PASSWORD),'--out',final,aligned])
    proof=run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','verify','--verbose','--print-certs','--min-sdk-version','28','--max-sdk-version','28',final])
    assert b'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613' in proof
    (out/'signature.txt').write_bytes(proof)
    badging=run([TOOLS/'aapt2.exe','dump','badging',final]);(out/'badging.txt').write_bytes(badging)
    assert b"name='local.tvbase.acceso'" in badging and b"versionCode='9'" in badging and b"versionName='0.9'" in badging
    assert key_before=={str(p):sha(p) for p in (KEY,PASSWORD)}
    assert sources=={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(SRC.iterdir()) if p.is_file()},'Sources changed during build'
    assert rom_receipt_sha==sha(args.rom_receipt) and review_receipt_sha==sha(args.method_review),'Reviewed receipt changed during build'
    record.update({'package':'local.tvbase.acceso','version':'0.9','version_code':9,'apk':final.relative_to(ROOT).as_posix(),
                   'bytes':final.stat().st_size,'sha256':sha(final),'dex_sha256':sha(dex/'classes.dex'),
                   'policy':{'zip_name':zip_name,'zip_bytes':zip_bytes,'zip_sha256':zip_sha,'env_record_sha256':ENV_SHA,'bcb_prefix_sha256':BCB_SHA},
                   'rom_receipt_sha256':rom_receipt_sha,'method_review_sha256':review_receipt_sha,
                   'signature_verification_api28_exit':0,'signing_inputs_unchanged':True,
                   'limitations':['ENV/BCB preparation changes boot metadata; no recovery or rollback physical proof.',
                                  'No automatic reset; a user power cycle is a separate physical action.',
                                  'A failed or lost observation never cancels the detached helper.']})
    (out/'receipt.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    (HERE/'COMPILACION-09.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps(record,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
