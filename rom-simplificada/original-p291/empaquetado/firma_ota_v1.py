"""Whole-file OTA RSA/SHA-1 for the ORIGINAL recovery's unchanged v1 key.

No JAR signatures, no signed attributes and no digest label substitution. The
signed interval ends two bytes before the EOCD comment, exactly as AOSP9 uses.
This is a legacy compatibility format, not proof of executing the OEM verifier.
"""
import hashlib
import os
from pathlib import Path
import re
import struct

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.serialization import pkcs7

OID_SHA1 = bytes.fromhex('2b0e03021a')
OID_RSA = bytes.fromhex('2a864886f70d010101')
OID_DATA = bytes.fromhex('2a864886f70d010701')
OID_SIGNED_DATA = bytes.fromhex('2a864886f70d010702')
CERT_SHA256 = 'a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc'
RECOVERY_KEYS_SHA256 = 'cd0788004cfa998c7bbede4811b791187139504a01415b9d30df5609458398df'


def require(value, message):
    if not value:
        raise ValueError(message)


def node(tag, content):
    length = len(content)
    encoded = bytes([length]) if length < 128 else bytes([0x80+(length.bit_length()+7)//8])+length.to_bytes((length.bit_length()+7)//8, 'big')
    return bytes([tag])+encoded+content


def integer(value):
    raw = value.to_bytes(max(1, (value.bit_length()+7)//8), 'big')
    return node(2, (b'\0' if raw[0]&128 else b'')+raw)


def algorithm(oid):
    return node(0x30, node(6, oid)+b'\x05\x00')


def children(encoded):
    result = []
    offset = 0
    while offset < len(encoded):
        start = offset
        require(offset+2 <= len(encoded), 'Truncated DER header')
        tag, length = encoded[offset:offset+2]
        offset += 2
        if length&128:
            count = length&127
            require(0 < count <= 4 and offset+count <= len(encoded), 'Invalid DER length')
            length = int.from_bytes(encoded[offset:offset+count], 'big')
            offset += count
        end = offset+length
        require(end <= len(encoded), 'Truncated DER value')
        result.append((tag, encoded[offset:end], encoded[start:end]))
        offset = end
    return result


def hash_prefix(path, count, algorithm_name='sha1'):
    digest = hashlib.new(algorithm_name)
    with Path(path).open('rb') as stream:
        while count:
            block = stream.read(min(count, 4<<20))
            require(block, 'Truncated signed data')
            digest.update(block)
            count -= len(block)
    return digest.digest()


def trust_original_v1_key(keyfile, cert):
    data = Path(keyfile).read_bytes()
    require(hashlib.sha256(data).hexdigest() == RECOVERY_KEYS_SHA256, 'Original recovery key file changed')
    require(cert.fingerprint(hashes.SHA256()).hex() == CERT_SHA256, 'Unexpected OTA certificate')
    match = re.fullmatch(rb'\{64,(0x[0-9a-fA-F]+),\{([0-9,]+)\},\{([0-9,]+)\}\}', data.strip())
    require(match is not None, 'Expected exactly one unprefixed v1 RSA key')
    words = [int(value) for value in match[2].split(b',')]
    rr_words = [int(value) for value in match[3].split(b',')]
    require(len(words) == len(rr_words) == 64 and all(0 <= value < 2**32 for value in words+rr_words), 'Invalid RSA limbs')
    modulus = sum(value << (32*index) for index, value in enumerate(words))
    rr = sum(value << (32*index) for index, value in enumerate(rr_words))
    numbers = cert.public_key().public_numbers()
    require(numbers.e == 3 and modulus.bit_length() == 2048 and modulus == numbers.n, 'RSA key differs from original recovery')
    require(int(match[1],16) == (-pow(modulus,-1,2**32))%2**32 and rr == pow(2,4096,modulus), 'Invalid recovery RSA parameters')
    return {'key_version': 1, 'rsa_exponent': 3, 'rsa_bits': 2048, 'digest': 'SHA1',
            'keyfile_sha256': RECOVERY_KEYS_SHA256, 'certificate_sha256': CERT_SHA256}


def sign_zip(unsigned, final, cert, key):
    unsigned, final = Path(unsigned), Path(final)
    require(not final.exists(), 'Refusing to overwrite signed output')
    size = unsigned.stat().st_size
    with unsigned.open('rb') as stream:
        stream.seek(-22, 2)
        end = stream.read()
    require(size >= 22 and end[:4] == b'PK\x05\x06' and end[-2:] == b'\0\0', 'Expected unsigned classic ZIP with empty comment')
    require(key.public_key().public_numbers() == cert.public_key().public_numbers(), 'Signing key does not match certificate')
    signature = key.sign(hash_prefix(unsigned, size-2), padding.PKCS1v15(), utils.Prehashed(hashes.SHA1()))
    issuer_serial = node(0x30, cert.issuer.public_bytes()+integer(cert.serial_number))
    signer = node(0x30, integer(1)+issuer_serial+algorithm(OID_SHA1)+algorithm(OID_RSA)+node(4,signature))
    signed_data = node(0x30, integer(1)+node(0x31,algorithm(OID_SHA1))+node(0x30,node(6,OID_DATA))+
                       node(0xa0,cert.public_bytes(serialization.Encoding.DER))+node(0x31,signer))
    envelope = node(0x30, node(6,OID_SIGNED_DATA)+node(0xa0,signed_data))
    message = b'TVBASE P291 original recovery v1; experimental test key\0'
    length = len(message)+len(envelope)+6
    comment = message+envelope+struct.pack('<H2sH',len(envelope)+6,b'\xff\xff',length)
    require(length <= 65535 and b'PK\x05\x06' not in comment, 'Unsafe OTA comment')
    with unsigned.open('rb') as source, final.open('xb') as target:
        left = size-2
        while left:
            block = source.read(min(left,4<<20));require(block,'Source truncated while signing')
            target.write(block);left -= len(block)
        target.write(struct.pack('<H',length));target.write(comment)
        target.flush();os.fsync(target.fileno())
    result = verify_zip(final,cert)
    require(hash_prefix(unsigned,size-2,'sha256') == hash_prefix(final,size-2,'sha256'), 'ZIP signed bytes changed')
    return result


def verify_zip(path, cert):
    path = Path(path)
    size = path.stat().st_size
    with path.open('rb') as stream:
        require(size >= 28, 'ZIP too short')
        stream.seek(-6,2)
        start, marker, comment_size = struct.unpack('<H2sH',stream.read())
        require(marker == b'\xff\xff' and 6 < start <= comment_size <= 65535 and size >= comment_size+22, 'Bad OTA footer')
        stream.seek(-(comment_size+22),2)
        tail = stream.read()
        require(tail[:4] == b'PK\x05\x06' and tail.count(b'PK\x05\x06') == 1, 'Invalid or ambiguous EOCD')
        require(struct.unpack_from('<H',tail,20)[0] == comment_size, 'EOCD comment size mismatch')
        envelope = tail[-start:-6]
    outer = children(envelope)
    require(len(outer) == 1 and outer[0][0] == 0x30, 'Invalid PKCS7 ContentInfo')
    content = children(outer[0][1])
    require(len(content) == 2 and content[0][:2] == (6,OID_SIGNED_DATA) and content[1][0] == 0xa0, 'Expected SignedData')
    wrapped = children(content[1][1])
    require(len(wrapped) == 1 and wrapped[0][0] == 0x30, 'Invalid SignedData wrapper')
    data = children(wrapped[0][1])
    require(len(data) == 5 and data[1][2] == node(0x31,algorithm(OID_SHA1)), 'Digest set must contain only SHA1')
    require(data[2][2] == node(0x30,node(6,OID_DATA)) and data[3][0] == 0xa0 and data[4][0] == 0x31, 'Expected detached content and one certificate set')
    signers = children(data[4][1]);require(len(signers) == 1 and signers[0][0] == 0x30,'Expected one signer')
    info = children(signers[0][1])
    require(len(info) == 5 and info[2][2] == algorithm(OID_SHA1) and info[3][2] == algorithm(OID_RSA) and info[4][0] == 4, 'Signer must use direct RSA/SHA1 without attributes')
    require(info[1][2] == node(0x30,cert.issuer.public_bytes()+integer(cert.serial_number)), 'Signer identity mismatch')
    included = pkcs7.load_der_pkcs7_certificates(envelope)
    require(len(included) == 1 and included[0].fingerprint(hashes.SHA256()) == cert.fingerprint(hashes.SHA256()), 'Embedded certificate mismatch')
    signed_bytes = size-comment_size-2
    cert.public_key().verify(info[4][1],hash_prefix(path,signed_bytes),padding.PKCS1v15(),utils.Prehashed(hashes.SHA1()))
    return {'signature_algorithm':'RSA-PKCS1v1.5/SHA1','signed_bytes':signed_bytes,
            'signed_region_sha256':hash_prefix(path,signed_bytes,'sha256').hex(),
            'sha1_policy_replay_verified':True,'certificate_sha256':cert.fingerprint(hashes.SHA256()).hex(),
            'oem_recovery_executed':False}
