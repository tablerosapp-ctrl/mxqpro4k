"""Repackage the sealed extractor 0.1 ARM32 for the supplied CNV8b recovery.

Only PC files are accessed. New output directory required. This does not build
or change the extractor, execute recovery, or authorize a ROM installation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import serialization
import firma_ota_v3 as signer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'diagnostico/extractor-recovery-0.1/privado/release-20260908-154731-69ecb368/TVBASE-EXTRACTOR-0.1-ARM32-RECOVERY.zip'
PRIOR_SHA = '1f45405d22193b1e09cc694bc5328be6e8aa7f071e0d77323cacc15611063f08'
MATERIAL = ROOT / 'privado/rockchip-cnv8b-20260908/firma-rk-publica'
KEYFILE = ROOT / 'privado/rockchip-cnv8b-20260908/recovery-files/res--keys'
JAVA = ROOT / 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ = ROOT / 'tools/compilar-android/ecj-3.39.0.jar'
BINARY = 'META-INF/com/google/android/update-binary'
META = 'tvbase/extractor.json'
CERT = 'META-INF/com/android/otacert'
SCRIPT = 'META-INF/com/google/android/updater-script'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    with path.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    signer.require(path.read_bytes() == data, 'PC readback differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    signer.require(output.is_relative_to(ROOT / 'privado') and not output.exists(), 'Use a new private output directory')
    signer.require(sha(PRIOR) == PRIOR_SHA, 'Sealed extractor package changed')
    certfile, pk8 = MATERIAL / 'testkey.x509.pem', MATERIAL / 'testkey.pk8'
    signer.require(sha(certfile) == '10a7b524d14750a12b44472524340df6b300f1b648fb63c3b17a161bde1e08d7', 'RK certificate changed')
    signer.require(sha(pk8) == '6062eea9d9d0c993906564ca644ef7b1ada2d2038bffb7343ac78b7714c955e7', 'RK development key changed')
    cert = x509.load_pem_x509_certificate(certfile.read_bytes())
    trust = signer.trust_cnv8b_v3_key(KEYFILE, cert)
    sources = {p.relative_to(ROOT).as_posix(): sha(p) for p in HERE.iterdir() if p.suffix in ('.py', '.java')}
    with zipfile.ZipFile(PRIOR) as archive:
        signer.require(len(archive.infolist()) == 4 and set(archive.namelist()) == {BINARY,META,CERT,SCRIPT}, 'Unexpected original members')
        signer.require(archive.testzip() is None, 'Original CRC failed')
        entries = {name: archive.read(name) for name in archive.namelist()}
        metadata = json.loads(entries[META])
        binary_sha = hashlib.sha256(entries[BINARY]).hexdigest()
        signer.require(metadata['extractor_sha256'] == binary_sha and metadata['architecture'] == 'ARM32', 'Wrong binary metadata')
    metadata.update(package_id='TVBASE-EXTRACTOR-0.1-RK1-ARM32', package_variant='RK1',
                    signature_scope='Supplied CNV8b.20230725 recovery v3 public development key; physical acceptance pending',
                    package_source_sha256=PRIOR_SHA, extractor_binary_unchanged=True)
    entries[META] = (json.dumps(metadata, ensure_ascii=False, indent=2)+'\n').encode()
    entries[CERT] = cert.public_bytes(serialization.Encoding.PEM)
    output.mkdir()
    try:
        unsigned = output / 'unsigned.zip'
        with zipfile.ZipFile(unsigned, 'x', compression=zipfile.ZIP_DEFLATED, allowZip64=False) as archive:
            for name, data in entries.items():
                info = zipfile.ZipInfo(name, (2026,9,8,0,0,0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if name == BINARY else 0o100644) << 16
                archive.writestr(info, data)
        final = output / 'TVBASE-EXTRACTOR-0.1-RK1-ARM32-RECOVERY.zip'
        key = serialization.load_der_private_key(pk8.read_bytes(), password=None)
        signature = signer.sign_zip(unsigned, final, cert, key)
        del key
        with zipfile.ZipFile(final) as archive:
            signer.require(len(archive.infolist()) == 4 and set(archive.namelist()) == set(entries) and archive.testzip() is None, 'Final CRC/members failed')
            for name, data in entries.items():
                signer.require(archive.read(name) == data, 'Changed member: '+name)
            signer.require(archive.getinfo(BINARY).external_attr >> 16 == 0o100755, 'Executable mode differs')
        javaout = output / 'java'; javaout.mkdir()
        logs = []
        def run(args, name, expect_success=True):
            result = subprocess.run([str(a) for a in args], cwd=HERE, capture_output=True, creationflags=0x08000000)
            save(output / name, result.stdout+result.stderr)
            logs.append(dict(file=name, exit=result.returncode, sha256=sha(output/name)))
            signer.require((result.returncode == 0) == expect_success, 'Unexpected result: '+name)
        run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-d',javaout,HERE/'VerifyWholeZip.java'], 'java-compile.log')
        javaargs=[JAVA,'-Xmx128m','--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED',
                  '--add-exports=java.base/sun.security.x509=ALL-UNNAMED','-cp',javaout,'VerifyWholeZip']
        run(javaargs+[final,certfile], 'java-positive.log')
        negatives=[]
        def reject(name, action):
            try: action()
            except Exception as exc:
                negatives.append(dict(name=name, rejected=True, exception=type(exc).__name__))
            else: raise ValueError('Negative case incorrectly accepted: '+name)
        oldcert=x509.load_pem_x509_certificate((ROOT/'tools/firmar-ota/testkey.x509.pem').read_bytes())
        reject('wrong P291 certificate against recovery key', lambda: signer.trust_cnv8b_v3_key(KEYFILE,oldcert))
        reject('original SHA1 package with RK cert', lambda: signer.verify_zip(PRIOR,cert))
        reject('RK package with P291 cert', lambda: signer.verify_zip(final,oldcert))
        broken=bytearray(final.read_bytes()); broken[64]^=1
        tampered=output/'negative-tampered.zip'; save(tampered,broken)
        reject('signed content corruption', lambda: signer.verify_zip(tampered,cert))
        run(javaargs+[tampered,certfile], 'java-negative-content.log', False)
        run(javaargs+[final,ROOT/'tools/firmar-ota/testkey.x509.pem'], 'java-negative-trust.log', False)
        broken=bytearray(final.read_bytes()); broken[-3]^=1
        footer=output/'negative-footer.zip'; save(footer,broken)
        reject('OTA footer corruption', lambda: signer.verify_zip(footer,cert))
        signer.require(sources == {p.relative_to(ROOT).as_posix():sha(p) for p in HERE.iterdir() if p.suffix in ('.py','.java')}, 'Recipe changed during build')
        signer.require(sha(PRIOR) == PRIOR_SHA, 'Original package changed during repackaging')
        receipt=dict(schema='tvbase-extractor-rk1-build-1',state='verified_pc',created_utc=datetime.now(timezone.utc).isoformat(),
                     package=final.name,bytes=final.stat().st_size,sha256=sha(final),sources=sources,
                     original_package_sha256=PRIOR_SHA,extractor_version='0.1',extractor_sha256=binary_sha,
                     extractor_unchanged=True,trust=trust,signature=signature,negative_tests=negatives,command_logs=logs,
                     members=[dict(name=k,bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in entries.items()],
                     python_verified=True,openjdk_verified=True,crc_verified=True,physical_acceptance=False,
                     sd_written=False,usb_written=False,tv_contacted=False,
                     limitations=['Public development key is not production update security',
                                  'Recovery host may write its own metadata; extractor opens internal sources read-only',
                                  'Binary 0.1 unchanged; no new physical extraction or restoration validation'])
        save(output/'COMPILACION.json',(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
        print(json.dumps({k:receipt[k] for k in ('state','package','bytes','sha256','extractor_sha256','physical_acceptance')},indent=2))
    except Exception as exc:
        save(output/'FALLO.json',(json.dumps(dict(state='failed_preserved',error_type=type(exc).__name__,error=str(exc)))+'\n').encode())
        raise


if __name__ == '__main__':
    main()
