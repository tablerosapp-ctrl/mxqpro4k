"""Small offline fixtures; existing signing files are read-only, no ROM/device action."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from firma_ota_v1 import hash_prefix, sign_zip, trust_original_v1_key, verify_zip

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SIGNING=ROOT/'tools/firmar-ota'
KEYFILE=ROOT/'diagnostico/primer-tv-lan-20260907-184926/privado/recovery-original-analisis/res--keys'


class SignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert=x509.load_pem_x509_certificate((SIGNING/'testkey.x509.pem').read_bytes())
        cls.key=serialization.load_der_private_key((SIGNING/'testkey.pk8').read_bytes(),password=None)

    def setUp(self):
        private=(ROOT/'privado').resolve();self.assertTrue(private.is_relative_to(ROOT))
        self.temporary=tempfile.TemporaryDirectory(prefix='fixture-ota-sha1-',dir=private)
        self.directory=Path(self.temporary.name).resolve();self.assertTrue(self.directory.is_relative_to(private))
        self.addCleanup(self.temporary.cleanup)
        self.unsigned=self.directory/'unsigned.zip';self.signed=self.directory/'signed.zip'
        with zipfile.ZipFile(self.unsigned,'x') as archive:archive.writestr('fixture.bin',bytes(range(256))*32)

    def test_original_key_v1_trust(self):
        self.assertEqual(trust_original_v1_key(KEYFILE,self.cert)['digest'],'SHA1')

    def test_sign_verify_preserves_signed_bytes_and_payload(self):
        original=self.unsigned.read_bytes();result=sign_zip(self.unsigned,self.signed,self.cert,self.key)
        self.assertEqual(self.unsigned.read_bytes(),original)
        self.assertEqual(self.signed.read_bytes()[:len(original)-2],original[:-2])
        self.assertEqual(result['signed_bytes'],len(original)-2)
        self.assertTrue(verify_zip(self.signed,self.cert)['sha1_policy_replay_verified'])
        with zipfile.ZipFile(self.signed) as archive:self.assertEqual(archive.read('fixture.bin'),bytes(range(256))*32)

    def test_changed_signed_byte_rejected(self):
        sign_zip(self.unsigned,self.signed,self.cert,self.key)
        data=bytearray(self.signed.read_bytes());data[50]^=1;self.signed.write_bytes(data)
        with self.assertRaises(InvalidSignature):verify_zip(self.signed,self.cert)

    def test_footer_corruption_rejected(self):
        sign_zip(self.unsigned,self.signed,self.cert,self.key)
        data=bytearray(self.signed.read_bytes());data[-4]=0;self.signed.write_bytes(data)
        with self.assertRaises(ValueError):verify_zip(self.signed,self.cert)

    def test_existing_signed_output_preserved(self):
        self.signed.write_bytes(b'preserve existing')
        with self.assertRaises(ValueError):sign_zip(self.unsigned,self.signed,self.cert,self.key)
        self.assertEqual(self.signed.read_bytes(),b'preserve existing')

    def test_untrusted_keyfile_rejected(self):
        other=self.directory/'keys';other.write_bytes(KEYFILE.read_bytes()+b'changed')
        with self.assertRaises(ValueError):trust_original_v1_key(other,self.cert)


if __name__=='__main__':unittest.main(verbosity=2)
