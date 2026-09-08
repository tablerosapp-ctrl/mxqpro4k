"""Pure offline codec for the original P291 ENV/BCB. No I/O or device access.

This does not authorize applying its output or prove that the installed bootloader
implements the reference source. The integration must check the live partition
identity, full backup, unchanged snapshot, durable receipts and explicit approval.
"""
import hashlib
import re
import struct
import zlib

ENV_SIZE = 65536
PARTITION_SIZE = 8388608
ENV_NORMAL = 'run storeboot'
# The reference shell only enters recovery after restoring normal bootcmd AND
# saveenv returning success. A returned recovery_from_flash falls back to Android.
# saveenv has no readback/transaction guarantee: this is not an atomic rollback.
ENV_MENU_ONCE = ("if setenv bootcmd 'run storeboot'; then if saveenv; then "
                 "run recovery_from_flash; run storeboot; else run storeboot; fi; "
                 "else run storeboot; fi")
MENU_ARGS = b'recovery\n--show_text\n'
CACHE_PENDING = ('command', 'uncrypt_file', 'zipinfo', 'block.map')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def snapshot(data, expected_sha256, length):
    require(type(data) is bytes and len(data) == length, 'Exact byte length required')
    require(isinstance(expected_sha256, str) and re.fullmatch('[0-9a-f]{64}', expected_sha256),
            'Explicit lowercase SHA256 required')
    require(sha(data) == expected_sha256, 'Snapshot changed')


def parse_env(record):
    require(type(record) is bytes and len(record) == ENV_SIZE, 'ENV must be exactly64KiB')
    expected = struct.unpack_from('<I', record)[0]
    require(zlib.crc32(record[4:]) & 0xffffffff == expected, 'Invalid ENV CRC32')
    end = record.find(b'\0\0', 4)
    require(end > 4, 'Missing ENV double terminator')
    require(not any(record[end+2:]), 'Nonzero ENV padding: unknown layout')
    pairs = []
    names = set()
    for entry in record[4:end].split(b'\0'):
        key, marker, value = entry.partition(b'=')
        require(marker == b'=' and re.fullmatch(rb'[A-Za-z0-9_]+', key), 'Invalid ENV key')
        require(key not in names, 'Duplicate ENV key')
        # Original irremote_update has one LF; preserve it exactly. The new
        # bootcmd itself deliberately contains no LF (reference Hush copies it).
        require(all(32 <= c <= 126 or c == 10 for c in value), 'Non-ASCII/control ENV value')
        names.add(key)
        pairs.append((key.decode('ascii'), value.decode('ascii')))
    return pairs


def pack_env(pairs):
    body = b'\0'.join((key+'='+value).encode('ascii') for key, value in pairs) + b'\0\0'
    require(len(body) <= ENV_SIZE-4, 'ENV capacity exceeded')
    body = body.ljust(ENV_SIZE-4, b'\0')
    record = struct.pack('<I', zlib.crc32(body) & 0xffffffff) + body
    require(parse_env(record) == pairs, 'ENV roundtrip mismatch')
    return record


def env_menu(record, expected_sha256):
    snapshot(record, expected_sha256, ENV_SIZE)
    pairs = parse_env(record)
    values = dict(pairs)
    require(values.get('bootcmd') == ENV_NORMAL, 'Unexpected or already armed bootcmd')
    require(values.get('recovery_part') == 'recovery' and values.get('recovery_offset') == '0',
            'Unexpected recovery source')
    require(values.get('upgrade_step') == '2', 'Upgrade state would alter preboot')
    require(values.get('wipe_data') == 'successful' and values.get('wipe_cache') == 'successful',
            'Pending OEM wipe state')
    require('recovery_from_flash' in values and 'storeboot' in values and 'preboot' in values,
            'Missing boot flow definition')
    updated = [(k, ENV_MENU_ONCE if k == 'bootcmd' else v) for k,v in pairs]
    result = pack_env(updated)
    require([(k,v) for k,v in parse_env(result) if k != 'bootcmd'] ==
            [(k,v) for k,v in pairs if k != 'bootcmd'], 'Unexpected environment change')
    return result


def env_disarm(record, expected_sha256):
    """Only disarm this exact command; do not overwrite an unknown current ENV."""
    snapshot(record, expected_sha256, ENV_SIZE)
    pairs = parse_env(record)
    require(dict(pairs).get('bootcmd') == ENV_MENU_ONCE, 'Unknown armed bootcmd')
    return pack_env([(k, ENV_NORMAL if k == 'bootcmd' else v) for k,v in pairs])


def env_partition(before, expected_sha256):
    """Return a full comparison image in memory; write scope remains first64KiB."""
    snapshot(before, expected_sha256, PARTITION_SIZE)
    # Exact original layout: no second environment record inferred from padding.
    require(not any(before[ENV_SIZE:]), 'Unexpected data outside ENV record')
    record = env_menu(before[:ENV_SIZE], sha(before[:ENV_SIZE]))
    return record + before[ENV_SIZE:]


def bcb_menu(misc, expected_sha256):
    snapshot(misc, expected_sha256, PARTITION_SIZE)
    result = bytearray(misc)
    result[0:32] = b'boot-recovery\0'.ljust(32,b'\0')
    result[64:832] = MENU_ARGS.ljust(768,b'\0')
    result = bytes(result)
    require(result[32:64] == misc[32:64] and result[832:] == misc[832:],
            'BCB unrelated fields changed')
    return result


def bcb_disarm(misc, expected_sha256):
    """Clear only this exact menu request, retaining all other partition bytes."""
    snapshot(misc, expected_sha256, PARTITION_SIZE)
    require(misc[:32] == b'boot-recovery\0'.ljust(32,b'\0') and
            misc[64:832] == MENU_ARGS.ljust(768,b'\0'), 'Unknown pending BCB request')
    result = bytearray(misc)
    result[:32] = bytes(32)
    result[64:832] = bytes(768)
    return bytes(result)
