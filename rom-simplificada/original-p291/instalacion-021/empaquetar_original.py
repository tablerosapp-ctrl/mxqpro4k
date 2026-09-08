"""Build new P291-original recovery packages; PC only, never install them.

First: --operation install --build-only.
Then: --operation install --revision-report <reviewed JSON>.
This package backs up six partitions and migrates userdata; no restore mode.
All release/build outputs are new; existing outputs cause an error.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from firma_ota_v1 import CERT_SHA256, require, sign_zip, trust_original_v1_key, verify_zip

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VERSION = '0.2.1'
PLATFORM_VERSION = '0.2.0'
MEDIA = 'TVBASE-P291-20260906-4dc82786'
GEOMETRY = {'system':(1342177280,'179:18'), 'vendor':(943718400,'179:16'),
            'product':(134217728,'179:19'), 'odm':(134217728,'179:17'), 'boot':(16777216,'179:11')}
ORIGINAL_HASHES = {
    'system':'249611912b7b1fa277d169f8612f9a719df3abf99dc98ed8e817657e2c9beb2c',
    'vendor':'d542fc091469a7c1223c1d5091f8ec6b3456f38dd1218b779d18d1942190d2a7',
    'product':'ef2c71f6208e25fa1cc9d5c12cb04972ac20d772e2c11a76972859403b530075',
    'odm':'97836d5a1b016b64d3875c82cb5f3b4daee0f56d8eea3675b4231086429cbe67',
    'boot':'13e027a3aae1af232d1d700421486f32b7958a9fa0a157d8cbd3c47243ab697d',
}
KERNEL_SHA = '9968c75f691f67dcb805ef8105e1ca534f73430bcf8b3920a066580e326b791a'
DTB_SHA = '13e54b5f1bba959e398da74b9d0859d08ba1747840ed3866eca1f3461c550d01'
BACKUPS = (
    ROOT/'privado/TVBASE-respaldo-P291-20260907-194104-0deb291b/manifest.json',
    ROOT/'privado/TVBASE-respaldo-P291-20260907-194413-6d502965/manifest.json',
)
KEYFILE = ROOT/'diagnostico/primer-tv-lan-20260907-184926/privado/recovery-original-analisis/res--keys'
SIGNING = ROOT/'tools/firmar-ota'
GO = ROOT/'tools/instalador-go/go/bin/go.exe'
JAVA = ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ = ROOT/'tools/compilar-android/ecj-3.39.0.jar'
BUILD_ROOT = ROOT/'privado/original-p291-empaquetado'
OUTPUT = HERE/'salida'
GO_SOURCES = ('go.mod','package.go','data_policy.go','package_test.go','main_linux.go','main_windows.go','backup_verified.go','backup_verified_test.go','userdata_linux.go','transaction_linux.go','env_guard.go','env_guard_test.go','block_abi.go','block_abi_test.go')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def local_path(relative):
    require(isinstance(relative,str) and not Path(relative).is_absolute(),'Expected a relative workspace path')
    path = (ROOT/relative).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(),'Input escapes workspace or is absent')
    return path


def json_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def platform_proof(report):
    prior=HERE.parent/'empaquetado/salida/TVBASE-P291-A9-0.2.0-VERIFICACION.json'
    data=json.loads(prior.read_text())
    require(data['version']=='0.2.0' and data['package_id']=='TVBASE-P291-A9-0.2.0','Wrong immutable platform release')
    require(data['payload_sha256_verified'] and data['zip_crc_verified'] and data['windows_package_verifier_passed'] and data['openjdk_signature_verified'],'Incomplete platform verification')
    previous_zip=local_path(data['file'])
    require(previous_zip.stat().st_size==573492264 and sha(previous_zip)=='bd4a8dd7df8d61580c5b450867bda2ef2b214b400b4cafcce5a26baa5c48a614','Immutable platform ZIP changed')
    require(data['review_report_sha256']==sha(report),'Immutable image report changed')
    composition=HERE.parent/'COMPOSICION-VERIFICADA.json'
    checked=json.loads(composition.read_text())
    require(checked['state']=='passed' and checked['image_report_sha256']==sha(report) and checked['apk_count']==39,'Composition verification does not match')
    return {'platform_version':'0.2.0','release_receipt_sha256':sha(prior),'release_zip_sha256':data['sha256'],
            'image_report_sha256':sha(report),'composition_receipt_sha256':sha(composition)}


def runtime_probe_proof():
    formatter_path=ROOT/'privado/mke2fs-prueba-fisica-20260907-224337/receipt.json'
    formatter=json.loads(formatter_path.read_text())
    require(formatter['state']=='passed' and formatter['target_kind']=='exclusive_regular_file' and formatter['logical_bytes']==3495936000,'Native formatter fixture failed')
    require(formatter['partition_format_requested'] is False and formatter['mounted'] is False and formatter['temporary_files_removed'] is True,'Formatter fixture scope differs')
    require(formatter['tools_sha256']==['2b1799d99503493f46f130f861889e0f03eb00d39cc633212890823bf1f86525','dcd4750293852e9b06f6de4c51c24d3d3941e67f221872965c6f02251509cd02'],'Formatter/config fixture differs')
    require(all(row['remote_exit']==0 and row['transport_exit']==0 for row in formatter['commands']),'Formatter fixture command failed')
    sb=formatter['superblock']
    require(sb['magic']==0xef53 and sb['blocks']==853500 and sb['block_size']==4096 and sb['inode_size']==256 and sb['state']==1 and sb['features']==[0x3c,0x242,0x7b],'Unexpected native superblock')
    abi_path=ROOT/'privado/abi-probe-fisico-20260907-224633/receipt.json'
    abi=json.loads(abi_path.read_text())
    require(abi['state']=='passed' and abi['result']['state']=='passed' and abi['result']['pointer_bytes']==4 and abi['temporary_executable_removed'] is True,'Native ABI probe failed')
    require(abi['source_sha256']=='b92fd6cf1a85e8f99a0711b5ec0196121e045e2287d1d001642fdd87339490f2' and all(row['exit']==0 for row in abi['stages']),'Native ABI executable/exit differs')
    require([(row['path'],row['bytes'],row['ioctl'],row['errno'],row['opened_readonly']) for row in abi['result']['partitions']]==[
        ('/dev/block/env',8388608,'0x80041272',0,True),('/dev/block/data',3495952384,'0x80041272',0,True)],'Native ABI target/geometry differs')
    return {'formatter_regular_file_receipt_sha256':sha(formatter_path),'block_ioctl_readonly_receipt_sha256':sha(abi_path),
            'formatter_regular_file_native_passed':True,'arm32_block_ioctl_native_passed':True,
            'partition_format_in_recovery_tested':False,'recovery_mount_tested':False}


def package_id(operation):
    return 'TVBASE-P291-A9-0.2.1' if operation=='install' else 'TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1'


def inspect_boot(path):
    data = Path(path).read_bytes()
    require(len(data)==GEOMETRY['boot'][0] and data[:8]==b'ANDROID!','Boot must have original full partition size and Android header')
    kernel_size,ramdisk_size,second_size = (struct.unpack_from('<I',data,at)[0] for at in (8,16,24))
    page,version = struct.unpack_from('<II',data,36)
    dtbo_size,dtbo_offset,header_size = struct.unpack_from('<IQI',data,1632)
    require(page==2048 and version==1 and header_size==1648 and dtbo_size==0 and dtbo_offset==0,'Original P291 boot header geometry changed')
    require(kernel_size==9914832 and second_size==174080 and 0<ramdisk_size<4<<20,'Unexpected boot component sizes')
    align=lambda n: (n+page-1)//page*page
    ramdisk_offset=page+align(kernel_size);second_offset=ramdisk_offset+align(ramdisk_size)
    require(second_offset+second_size<=len(data),'Boot component outside partition')
    kernel=data[page:page+kernel_size];ramdisk=data[ramdisk_offset:ramdisk_offset+ramdisk_size];dtb=data[second_offset:second_offset+second_size]
    require(hashlib.sha256(kernel).hexdigest()==KERNEL_SHA and hashlib.sha256(dtb).hexdigest()==DTB_SHA,'Kernel or multi-DTB differs from the original P291')
    digest=hashlib.sha1()
    for part in (kernel,ramdisk,dtb,b''):
        digest.update(part);digest.update(struct.pack('<I',len(part)))
    require(digest.digest()==data[576:596],'Boot v1 identifier mismatch')
    return {'kernel_sha256':KERNEL_SHA,'dtb_sha256':DTB_SHA,'ramdisk_sha256':hashlib.sha256(ramdisk).hexdigest(),
            'header_version':1,'header_size':1648,'header_id_verified':True,'bytes':len(data)}


def verified_originals():
    originals={};receipts=[]
    for receipt in BACKUPS:
        data=json.loads(receipt.read_text(encoding='utf-8'))
        require(data['state']=='verified_selected_partitions' and data['exit']==0 and data['root_uid']==0,'Original backup is not verified')
        require(data['profile']=='P291/gxlx2_p291_1g/API28','Wrong original profile')
        receipts.append({'path':receipt.relative_to(ROOT).as_posix(),'sha256':sha(receipt)})
        for row in data['partitions']:
            name=row['name']
            if name not in GEOMETRY:continue
            require(name not in originals,'Duplicate original partition')
            require(row['state']=='verified' and row['copy_exit']==0 and row['transport_exit']==0 and row['footer_verified'] is True,'Unverified original partition')
            size,mm=GEOMETRY[name]
            require(row['bytes']==size and row['sha256']==row['pc_sha256']==row['remote_sha256_after']==ORIGINAL_HASHES[name],'Original hash/size differs')
            path=(receipt.parent/row['file']).resolve()
            require(path.parent==receipt.parent.resolve() and path.stat().st_size==size and sha(path)==row['sha256'],'Original file differs from acquisition')
            originals[name]=path
    require(set(originals)==set(GEOMETRY),'Missing original partitions')
    inspect_boot(originals['boot'])
    return originals,receipts


def reviewed_images(report, originals):
    review=json.loads(Path(report).read_text(encoding='utf-8'))
    require(review['version']==PLATFORM_VERSION and review['package_id']=='TVBASE-P291-A9-0.2.0' and review['dt_id']=='gxlx2_p291_1g','Wrong reviewed revision')
    require(review['reviewed'] is True and review['bluetooth_disabled'] is True,'Review/Bluetooth removal not approved in report')
    require(set(review['images'])==set(GEOMETRY),'Expected all five image descriptions')
    paths={}
    for name,(size,_) in GEOMETRY.items():
        row=review['images'][name];path=local_path(row['path'])
        require(row['bytes']==size and re.fullmatch('[0-9a-f]{64}',row['sha256']) and path.stat().st_size==size and sha(path)==row['sha256'],'Reviewed image mismatch: '+name)
        require(row['source_sha256']==ORIGINAL_HASHES[name],'Image does not cite the original P291 source')
        require(path==originals[name] or path.is_relative_to(ROOT/'rom-simplificada/original-p291'),'Modified image outside original-P291 workspace')
        if name!='boot':require(type(row['fsck_exit']) is int and row['fsck_exit']==0,'ext4 validation failed/absent: '+name)
        paths[name]=path
    boot=inspect_boot(paths['boot'])
    require(review['boot_review']['approved'] is True and review['boot_review']['kernel_sha256']==KERNEL_SHA and review['boot_review']['dtb_sha256']==DTB_SHA,'Missing reviewed boot provenance')
    require(review['boot_review']['ramdisk_sha256']==boot['ramdisk_sha256'],'Boot ramdisk differs from reviewed result')
    return paths,review,boot


def run_command(args,log,env=None):
    process=subprocess.run(list(map(str,args)),cwd=HERE,env=env,capture_output=True,creationflags=0x08000000)
    with log.open('xb') as stream:stream.write(process.stdout+process.stderr)
    require(process.returncode==0,'Command failed; inspect '+log.name)
    return process


def verify_elf(path):
    data=Path(path).read_bytes()
    require(data[:7]==b'\x7fELF\x01\x01\x01' and struct.unpack_from('<H',data,18)[0]==40,'Expected ARM32 ELF')
    offset=struct.unpack_from('<I',data,28)[0];stride,count=struct.unpack_from('<HH',data,42)
    require(all(struct.unpack_from('<I',data,offset+i*stride)[0]!=3 for i in range(count)),'Installer must not have PT_INTERP')


def build(operation):
    require(operation=='install','Installation build only')
    ident=package_id(operation);directory=BUILD_ROOT/ident
    require(not directory.exists(),'Build exists; review/version instead of overwriting')
    directory.mkdir(parents=True)
    env=os.environ.copy();env.update(GOROOT=str(GO.parents[1]),GOCACHE=str(directory/'go-cache'),GOMODCACHE=str(directory/'go-mod-cache'),
                                    GOPROXY='off',GOTOOLCHAIN='local',CGO_ENABLED='0',GOOS='windows',GOARCH='amd64')
    operation_id='install_reviewed_with_userdata_migration' if operation=='install' else 'restore_original'
    ldflags=f'-s -w -X main.allowedPackageID={ident} -X main.allowedOperation={operation_id}'
    run_command([GO,'test','-count=1','-json','-ldflags',ldflags,'.'],directory/'go-tests.jsonl',env)
    run_command([GO,'build','-trimpath','-buildvcs=false','-ldflags',ldflags,'-o',directory/'verify-package.exe','.'],directory/'go-windows.log',env)
    env.update(GOOS='linux',GOARCH='arm',GOARM='7')
    run_command([GO,'build','-trimpath','-buildvcs=false','-ldflags',ldflags,'-o',directory/'update-binary','.'],directory/'go-arm.log',env)
    verify_elf(directory/'update-binary')
    java_out=directory/'openjdk';java_out.mkdir()
    run_command([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-d',java_out,HERE/'VerifyWholeZip.java'],directory/'openjdk-compile.log')
    events=[json.loads(line) for line in (directory/'go-tests.jsonl').read_text().splitlines() if line.startswith('{')]
    receipt={'package_id':ident,'operation':operation_id,'version':VERSION,'go_sources':{name:sha(HERE/name) for name in GO_SOURCES},
             'go_tests_passed':[row['Test'] for row in events if row.get('Action')=='pass' and 'Test' in row],
             'installer_sha256':sha(directory/'update-binary'),'validator_sha256':sha(directory/'verify-package.exe'),
             'java_source_sha256':sha(HERE/'VerifyWholeZip.java'),'java_class_sha256':sha(java_out/'VerifyWholeZip.class'),
             'physically_tested':False}
    json_new(directory/'compilacion.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)


def package(operation,report):
    require(operation=='install','This release only builds installation; exact-data restoration requires its own reviewed manifest')
    ident=package_id(operation);directory=BUILD_ROOT/ident
    proof=json.loads((directory/'compilacion.json').read_text())
    require(proof['package_id']==ident and all(sha(HERE/name)==value for name,value in proof['go_sources'].items()),'Installer sources changed after tests/build')
    require(sha(directory/'update-binary')==proof['installer_sha256'] and sha(directory/'verify-package.exe')==proof['validator_sha256'],'Installer binary changed')
    require(sha(HERE/'VerifyWholeZip.java')==proof['java_source_sha256'] and sha(directory/'openjdk/VerifyWholeZip.class')==proof['java_class_sha256'],'Independent verifier changed')
    verify_elf(directory/'update-binary')
    original,receipts=verified_originals()
    if operation=='install':
        require(report is not None,'Reviewed images report required')
        immutable_platform=platform_proof(report)
        runtime_probes=runtime_probe_proof()
        paths,review,boot=reviewed_images(report,original)
    else:
        require(report is None,'Restoration always uses the exact original acquisitions')
        paths=original;review=None;boot=inspect_boot(paths['boot'])
    operation_id='install_reviewed_with_userdata_migration' if operation=='install' else 'restore_original'
    manifest={'format':3,'id':ident,'dt_id':'gxlx2_p291_1g','media_id':MEDIA,'operation':operation_id,
              'data_policy':'backup_raw_userdata_then_format_ext4','platform_version':PLATFORM_VERSION,
              'data_bytes':3495952384,'data_major_minor':'179:20','filesystem_bytes':3495936000,'images':[]}
    for name,(size,mm) in GEOMETRY.items():
        manifest['images'].append({'name':name,'entry':'tvbase/'+name+'.img','size':size,'sha256':sha(paths[name]),
                                   'major_minor':mm,'original_sha256':ORIGINAL_HASHES[name]})
    cert=x509.load_pem_x509_certificate((SIGNING/'testkey.x509.pem').read_bytes())
    trust=trust_original_v1_key(KEYFILE,cert)
    final=OUTPUT/(ident+'-RECOVERY.zip');receipt=OUTPUT/(ident+'-VERIFICACION.json')
    unsigned=directory/'unsigned.zip'
    require(not any(path.exists() for path in (final,receipt,unsigned)),'Refusing to overwrite any build/release')
    OUTPUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(unsigned,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as archive:
        for image in manifest['images']:
            print('Empaquetando',image['name'],image['size'],flush=True)
            archive.write(paths[image['name']],image['entry'])
        binary_info=zipfile.ZipInfo('META-INF/com/google/android/update-binary',(2026,9,7,0,0,0));binary_info.external_attr=0o100755<<16
        archive.writestr(binary_info,(directory/'update-binary').read_bytes())
        archive.writestr('tvbase/manifest.json',json.dumps(manifest,indent=2))
        archive.writestr('META-INF/com/android/metadata','ota-type=BLOCK\npre-device=ampere\nota-wipe=no\npost-sdk-level=28\n')
        archive.writestr('META-INF/com/android/otacert',cert.public_bytes(serialization.Encoding.PEM))
    key=serialization.load_der_private_key((SIGNING/'testkey.pk8').read_bytes(),password=None)
    signature=sign_zip(unsigned,final,cert,key)
    verify_zip(final,cert)
    with zipfile.ZipFile(final) as archive:
        require(archive.testzip() is None,'ZIP CRC failure')
        require(json.loads(archive.read('tvbase/manifest.json'))==manifest,'Manifest changed')
        for image in manifest['images']:
            with archive.open(image['entry']) as stream:require(hashlib.file_digest(stream,'sha256').hexdigest()==image['sha256'],'Payload SHA mismatch')
            require(archive.getinfo(image['entry']).file_size==image['size'],'Payload length mismatch')
    run_command([directory/'verify-package.exe',final],directory/'package-accepted.log')
    run_command([JAVA,'-Xmx3g','--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED',
                 '--add-exports=java.base/sun.security.x509=ALL-UNNAMED','-cp',directory/'openjdk','VerifyWholeZip',final],directory/'openjdk-signature.log')
    require(all(sha(path)==ORIGINAL_HASHES[name] for name,path in original.items()),'An original changed during packaging')
    result={'version':VERSION,'package_id':ident,'operation':operation_id,'file':final.relative_to(ROOT).as_posix(),
            'bytes':final.stat().st_size,'sha256':sha(final),'manifest':manifest,'original_backup_manifests':receipts,
            'review_report':None if report is None else Path(report).resolve().relative_to(ROOT).as_posix(),
            'review_report_sha256':None if report is None else sha(report),'boot_validation':boot,
            'signature':signature,'recovery_v1_trust':trust,'openjdk_signature_verified':True,
            'payload_sha256_verified':True,'zip_crc_verified':True,'windows_package_verifier_passed':True,
            'installer_sha256':proof['installer_sha256'],'builder_sha256':sha(Path(__file__)),
            'signature_helper_sha256':sha(HERE/'firma_ota_v1.py'),'originals_unchanged':True,
            'data_policy':manifest['data_policy'],'userdata_format_after_verified_backup':True,
            'formatter_sha256':'2b1799d99503493f46f130f861889e0f03eb00d39cc633212890823bf1f86525',
            'platform_images_version':PLATFORM_VERSION,
            'immutable_platform_proof':immutable_platform,
            'native_runtime_probes':runtime_probes,
            'physically_installed':False,'oem_recovery_acceptance_confirmed':False,'restore_path_tested':False,
            'pending_before_install':['physical_recovery_entry_with_direct_USB_package'],
            'limits':['Non-A/B; no automatic rollback','Test key and legacy SHA1 are compatibility measures, not production update security',
                      'Full userdata backup is created in recovery before formatting; restoring that backup requires an exact-backup restore operation, not the old five-partition restore ZIP']}
    json_new(receipt,result);json_new(OUTPUT/(ident+'-manifest.json'),manifest)
    print(json.dumps(result,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation',choices=('install',),required=True)
    parser.add_argument('--build-only',action='store_true')
    parser.add_argument('--revision-report',type=Path)
    args=parser.parse_args()
    if args.build_only:
        require(args.revision_report is None,'Build-only does not consume image reports');build(args.operation)
    else:package(args.operation,args.revision_report)


if __name__=='__main__':main()
