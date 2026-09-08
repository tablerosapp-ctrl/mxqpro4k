"""Emit reproducible public evidence from local tests/builds; no device/ROM build."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives import serialization
import empaquetar_original as package
import test_firma_ota_v1 as signature_tests
from firma_ota_v1 import sign_zip, trust_original_v1_key


def main():
    compiled=[]
    for operation in ('install','restore'):
        directory=package.BUILD_ROOT/package.package_id(operation)
        receipt=directory/'compilacion.json';data=json.loads(receipt.read_text())
        package.require(all(package.sha(package.HERE/name)==value for name,value in data['go_sources'].items()),'Compiled source changed')
        package.require(package.sha(directory/'update-binary')==data['installer_sha256'] and package.sha(directory/'verify-package.exe')==data['validator_sha256'],'Compiled binary changed')
        compiled.append({'operation':operation,'receipt_sha256':package.sha(receipt),**data})
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(signature_tests))
    package.require(result.wasSuccessful(),'Signature tests failed: '+stream.getvalue())
    private=(package.ROOT/'privado').resolve();package.require(private.is_relative_to(package.ROOT),'Fixture directory escapes workspace')
    with tempfile.TemporaryDirectory(prefix='fixture-empaquetado-v1-',dir=private) as generated:
        directory=Path(generated).resolve();package.require(directory.is_relative_to(private),'Unsafe fixture location')
        cert=x509.load_pem_x509_certificate((package.SIGNING/'testkey.x509.pem').read_bytes())
        key=serialization.load_der_private_key((package.SIGNING/'testkey.pk8').read_bytes(),password=None)
        trust=trust_original_v1_key(package.KEYFILE,cert)
        with zipfile.ZipFile(directory/'unsigned.zip','x') as archive:
            info=zipfile.ZipInfo('fixture.bin',(2026,9,7,0,0,0))
            archive.writestr(info,bytes(range(256))*32)
        signed=directory/'signed.zip';proof=sign_zip(directory/'unsigned.zip',signed,cert,key)
        classes=package.BUILD_ROOT/package.package_id('install')/'openjdk'
        args=[package.JAVA,'--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED',
              '--add-exports=java.base/sun.security.x509=ALL-UNNAMED','-cp',classes,'VerifyWholeZip',signed]
        verified=subprocess.run(list(map(str,args)),capture_output=True,creationflags=0x08000000)
        package.require(verified.returncode==0,'Independent PKCS7 check failed: '+verified.stderr.decode(errors='replace'))
        proof.update(openjdk_exit=verified.returncode,openjdk_stdout=verified.stdout.decode().strip(),
                     fixture_bytes=signed.stat().st_size,fixture_sha256=package.sha(signed))
    evidence={'state':'passed','recorded_at':datetime.now().astimezone().isoformat(timespec='seconds'),
              'signature_tests_run':result.testsRun,'signature_tests_output':stream.getvalue(),
              'signature_fixture':proof,'recovery_trust':trust,'compiled_installers':compiled,
              'sources':{path.name:package.sha(path) for path in package.HERE.iterdir() if path.suffix in ('.py','.go','.java') or path.name=='go.mod'},
              'tv_accessed':False,'usb_accessed':False,'rom_package_built_by_validation':False,
              'oem_verifier_executed':False,'data_wiped':False,'restoration_tested':False,
              'limits':['PC fixture and source compilation only','No acceptance by OEM recovery inferred',
                        'Small Go payload fixtures temporarily reduce geometry; original constants tested separately']}
    target=package.HERE/'EVIDENCIA-TESTS.json'
    temporary=target.with_suffix('.json.tmp')
    with temporary.open('x',encoding='utf-8') as output:
        json.dump(evidence,output,ensure_ascii=False,indent=2);output.write('\n');output.flush();os.fsync(output.fileno())
    os.replace(temporary,target)
    print(json.dumps({'state':'passed','signature_tests':result.testsRun,
                      'go_pass_events_per_operation':[len(row['go_tests_passed']) for row in compiled],
                      'receipt':target.relative_to(package.ROOT).as_posix()},indent=2))


if __name__=='__main__':main()
