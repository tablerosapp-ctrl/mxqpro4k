"""Read a failed capture without promoting it to a completed backup.

Only regular files in one local directory are read. Reuse the strict inventory,
path, part-name and SHA validators; failure markers remain authoritative.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tvbase_complete_verifier', HERE / 'verificar-captura.py')
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


class FailedReader(V.CaptureReader):
    def __init__(self, capture):
        raw = Path(capture)
        V.need('..' not in raw.parts, 'ambiguous_capture_path')
        self.root = raw.absolute()
        self.root_info = V.info_key(V.ordinary(self.root, directory=True))
        self.files = self.scan()
        V.need(V.FAILURES <= self.files.keys(), 'missing_failure_records')
        V.need('resultado.json' not in self.files and 'report.json' not in self.files,
               'conflicting_success_records')


def verify_failed(capture):
    reader = FailedReader(capture)
    result, _ = reader.json('resultado-error.json', 65536)
    V.obj(result, {'schema', 'status', 'capture_id', 'error'})
    V.need(result['schema'] == V.RESULT_SCHEMA and result['status'] == 'failed', 'not_failed_result')
    cid = result['capture_id']
    V.need(type(cid) is str and V.CAPTURE_ID.fullmatch(cid) is not None, 'invalid_capture_id')
    V.text(result['error'])
    inv, _ = reader.json('inventario.json', 8 << 20)
    blocks, _, _ = V.validate_inventory(inv, cid, inventory_only=False)
    report, report_hash = reader.json('failed-report.json')
    V.obj(report, {'format', 'status', 'expected_bytes', 'required_bytes', 'free_bytes_at_preflight',
                   'part_bytes', 'sources', 'limit', 'error'}, {'omitted'})
    V.need(report['format'] == 'tvbase-recovery-capture-0.1' and report['status'] == 'failed', 'not_failed_report')
    V.need(report['error'] == result['error'], 'failure_reason_mismatch')
    V.text(report['limit'], 4096)
    V.omissions(report.get('omitted'))
    part_bytes = V.integer(report['part_bytes'], 1, V.MAX_PART_BYTES)
    sources = V.array(report['sources'], V.MAX_SOURCES)
    V.need(bool(sources), 'missing_sources')
    expected = V.integer(report['expected_bytes'], 1, V.MAX_SOURCES * V.MAX_SOURCE_BYTES)
    required = V.integer(report['required_bytes'], 1, (1 << 64) - 1)
    V.need(required == expected + V.SPACE_RESERVE, 'invalid_preflight_sizes')
    V.integer(report['free_bytes_at_preflight'], 0, (1 << 64) - 1)
    allowed = {'inventario.json', 'failed-report.json', 'resultado-error.json'}
    seen = set()
    verified_bytes = 0
    total = 0
    checked = []
    for position, row in enumerate(sources):
        V.obj(row, {'source', 'id', 'status'}, {'sha256', 'reread_sha256', 'parts', 'error', 'verification_order'})
        source = V.validate_source(row['source'])
        V.validate_policy_source(inv, source, row, position, len(sources))
        ident = V.digest(row['id'])
        V.need(ident == V.source_id(source) and source['name'] in blocks
               and ident == V.source_id(blocks[source['name']]), 'source_inventory_mismatch')
        V.need(ident not in seen, 'duplicate_source')
        seen.add(ident)
        total += source['bytes']
        status = row['status']
        V.need(status in {'verified', 'failed', 'omitted'}, 'unknown_partial_source_state')
        for key in ('sha256', 'reread_sha256'):
            if key in row:
                V.digest(row[key])
        if 'error' in row:
            V.text(row['error'])
        parts = V.array(row.get('parts'), V.MAX_PARTS, nullable=True)
        whole = hashlib.sha256()
        copied = 0
        all_parts_verified = True
        for index, part in enumerate(parts):
            V.obj(part, {'index', 'name', 'expected_bytes', 'copied_bytes', 'status'}, {'sha256', 'error'})
            name = V.basename(part['name'])
            V.need(part['index'] == index and type(part['index']) is int
                   and name == f'{ident}.part-{index:06d}.img.partial' and name not in allowed, 'part_identity_mismatch')
            allowed.add(name)
            V.need(part['status'] in {'incomplete', 'copied_synced', 'destination_verified', 'verified'},
                   'unknown_partial_part_state')
            if 'error' in part:
                V.text(part['error'])
            exp = min(part_bytes, source['bytes'] - index * part_bytes)
            V.need(V.integer(part['expected_bytes'], 1, part_bytes) == exp, 'part_declared_size_mismatch')
            size = V.integer(part['copied_bytes'], 0, exp)
            digest = reader.hash_part(name, size, whole)
            if 'sha256' in part:
                V.need(V.digest(part['sha256']) == digest, 'part_sha256_mismatch')
            copied += size
            all_parts_verified &= (part['status'] == 'verified' and size == exp
                                   and 'sha256' in part and 'error' not in part)
        if status == 'verified':
            V.need('error' not in row and copied == source['bytes'] and all_parts_verified
                   and whole.hexdigest() == row.get('sha256') == row.get('reread_sha256'),
                   'claimed_verified_source_invalid')
            verified_bytes += copied
        elif status == 'omitted':
            V.need(not parts and 'sha256' not in row and 'reread_sha256' not in row, 'omitted_source_has_data')
        if copied == source['bytes'] and 'sha256' in row:
            V.need(whole.hexdigest() == row['sha256'], 'aggregate_sha256_mismatch')
        checked.append({'name': source['name'], 'state': status, 'copied_bytes_checked': copied,
                        'verified_source_bytes': copied if status == 'verified' else 0})
    V.need(total == expected, 'invalid_failed_capture_scope')
    reader.finish(allowed)
    return {'schema': 'tvbase-partial-capture-verification-1', 'status': 'failed_capture_files_verified_pc',
            'capture_complete': False, 'capture_modified': False, 'verified_source_bytes': verified_bytes,
            'sources': checked, 'failed_report_sha256': report_hash, 'all_device_storage_copied': False,
            'restore_tested': False, 'scope': 'Previously verified sources only; failed source bytes are not a stable original.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify_failed(args.capture)
    except (V.InvalidCapture, OSError, UnicodeError, OverflowError, RecursionError):
        print(json.dumps({'status': 'invalid_partial_capture', 'verified_source_bytes': 0, 'capture_complete': False}))
        return 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
