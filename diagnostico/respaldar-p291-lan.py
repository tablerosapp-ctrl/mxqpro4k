"""Read selected original P291 partitions to this PC; never restore or write the TV.

Usage: python diagnostico/respaldar-p291-lan.py --stage critical
       python diagnostico/respaldar-p291-lan.py --stage system

Requires the existing, explicitly authorized `su 0` and ADB shell_v2. Each run
creates a new PRIVATE folder. No retries, resume, USB writes, remount or reboot.
`tee` is mounted RW: matching reads are evidence, not an atomic filesystem backup.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import queue
import re
import shlex
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / 'diagnostico/primer-tv-lan-20260907-184926/privado/session.json'
ADB = ROOT / 'tools/platform-tools/adb.exe'
MIB = 1024 * 1024
# name: (major, minor, bytes). These are the first P291's observed block aliases.
PARTITIONS = {
    'bootloader': (179, 1, 4*MIB), 'recovery': (179, 6, 24*MIB),
    'boot': (179, 11, 16*MIB), 'misc': (179, 7, 8*MIB),
    'env': (179, 4, 8*MIB), 'dtbo': (179, 8, 8*MIB),
    'vbmeta': (179, 14, 2*MIB), 'tee': (179, 15, 32*MIB),
    'system': (179, 18, 1280*MIB), 'vendor': (179, 16, 900*MIB),
    'product': (179, 19, 128*MIB), 'odm': (179, 17, 128*MIB),
}
STAGES = {'critical': tuple(PARTITIONS)[:8], 'system': tuple(PARTITIONS)[8:]}
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def stamp():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def demand(condition, message):
    if not condition:
        raise RuntimeError(message)


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def parse_target(target):
    host, separator, port = target.partition(':')
    address = ipaddress.IPv4Address(host)
    allowed = any(address in ipaddress.ip_network(net) for net in
                  ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
    demand(separator == ':' and port == '5555' and allowed, 'Expected a private IPv4 endpoint on 5555')
    return target


def parse_alias(text, name):
    # Reject symlinks, unexpected extra lines and anything except the known block node.
    match = re.fullmatch(r'b\S+\s+\d+\s+\S+\s+\S+\s+(\d+),\s+(\d+)\s+[^\r\n]+\s+'
                         + re.escape('/dev/block/'+name), text.strip())
    demand(match is not None, 'Unexpected block alias: '+name)
    return tuple(int(value) for value in match.groups())


def parse_mounts(text, name, require_ro):
    rows = [line.split() for line in text.splitlines()]
    rows = [row for row in rows if len(row) == 6 and row[0] == '/dev/block/'+name]
    if require_ro:
        demand(len(rows) == 1 and rows[0][1] == '/'+name and
               'ro' in rows[0][3].split(',') and 'rw' not in rows[0][3].split(','),
               'Partition is not mounted read-only at its expected path: '+name)
    return [{'mountpoint': row[1], 'filesystem': row[2], 'options': row[3]} for row in rows]


class Backup:
    def __init__(self, stage):
        demand(os.name == 'nt' and ROOT.drive.upper() == 'C:', 'Destination must be this Windows C: workspace')
        private = (ROOT / 'privado').resolve()
        demand(private.is_relative_to(ROOT) and private != ROOT, 'Private destination escapes the workspace')
        demand(ADB.is_file() and SESSION.is_file(), 'Missing local ADB or private session record')
        session = json.loads(SESSION.read_text(encoding='utf-8-sig'))
        demand(session['profile']['dt'] == 'gxlx2_p291_1g' and session['profile']['api'] == '28', 'Session profile mismatch')
        self.target = parse_target(session['target'])
        self.expected_build = session['profile']['build']
        self.stage = stage
        self.names = STAGES[stage]
        private.mkdir(exist_ok=True)
        required = sum(PARTITIONS[name][2] for name in self.names) + 1024*MIB
        demand(shutil.disk_usage(private).free >= required, 'Insufficient local disk space')
        self.output = private / ('TVBASE-respaldo-P291-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
        self.output.mkdir()  # New directory only; no existing backup is modified.
        self.receipt = self.output / 'manifest.json'
        self.state = {
            'format': 1, 'state': 'checking', 'started': stamp(), 'stage': stage,
            'profile': 'P291/gxlx2_p291_1g/API28', 'target': self.target,
            'session_sha256': hashlib.sha256(SESSION.read_bytes()).hexdigest(),
            'selection': list(self.names), 'commands': [], 'partitions': [],
            'tv_write_requested': False, 'reboot_requested': False,
            'usb_accessed': False, 'complete_restore_backup': False,
            'limitations': [
                'Selected partitions only; userdata, cache and other unlisted partitions are excluded.',
                'No restore path or restored boot has been tested.',
                'Live device: matching hashes do not make a filesystem snapshot atomic.',
                'tee may be mounted read-write; this script does not freeze or remount it.',
                'A process in uninterruptible kernel sleep may outlive its requested timeout.',
            ],
        }
        self.save()
        print(json.dumps({'output': str(self.output), 'stage': stage}), flush=True)

    def save(self):
        atomic_json(self.receipt, self.state)

    def argv(self, arguments):
        return [str(ADB), '-s', self.target, *arguments]

    def command(self, label, words, timeout=15, root=True):
        # All remote words are constants or selected allowlist values. No shell
        # substitutions, output redirection, aliases or arbitrary user commands.
        if root:
            seconds = max(1, int(timeout)-2)
            args = ['shell', '-T', '/system/xbin/su', '0', '/system/bin/toybox',
                    'timeout', '-s', 'KILL', str(seconds), *words]
        else:
            args = words
        start = time.monotonic()
        row = {'label': label, 'arguments': args, 'timeout_seconds': timeout, 'exit': None}
        self.state['commands'].append(row)
        process = None
        try:
            process = subprocess.Popen(self.argv(args), stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       creationflags=FLAGS)
            while True:
                left = timeout-(time.monotonic()-start)
                if left <= 0:
                    raise subprocess.TimeoutExpired(self.argv(args), timeout)
                try:
                    stdout, stderr = process.communicate(timeout=min(15, left))
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic()-start >= timeout:
                        raise
                    print(f'{label}: verificando, {time.monotonic()-start:.0f} s', flush=True)
                    row['elapsed_seconds'] = round(time.monotonic()-start, 1)
                    self.save()
            row.update(exit=process.returncode, seconds=round(time.monotonic()-start, 3),
                       stdout_bytes=len(stdout), stderr_bytes=len(stderr),
                       stdout_sha256=hashlib.sha256(stdout).hexdigest())
            (self.output / (label+'.stdout.txt')).write_bytes(stdout)
            (self.output / (label+'.stderr.txt')).write_bytes(stderr)
            demand(process.returncode == 0, f'{label}: exit {process.returncode}')
            demand(len(stdout) <= 128*1024 and len(stderr) <= 64*1024,
                   label+': output limit exceeded')
            return stdout.decode('utf-8', errors='strict').rstrip('\r\n\x00')
        except subprocess.TimeoutExpired as error:
            row.update(timed_out=True, seconds=round(time.monotonic()-start, 3))
            (self.output / (label+'.stdout.txt')).write_bytes(error.stdout or b'')
            (self.output / (label+'.stderr.txt')).write_bytes(error.stderr or b'')
            raise RuntimeError(label+': timeout; no automatic retry') from error
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    pass
            self.save()

    def profile(self):
        features = self.command('transport-features', ['features'], root=False)
        demand('shell_v2' in features.replace('\n', ',').split(','), 'ADB shell_v2 is required for remote exit status')
        uid = self.command('root-uid', ['/system/bin/toybox', 'id', '-u'])
        dt = self.command('profile-dt', ['/system/bin/toybox', 'cat', '/proc/device-tree/amlogic-dt-id'])
        api = self.command('profile-api', ['/system/bin/getprop', 'ro.build.version.sdk'])
        build = self.command('profile-build', ['/system/bin/getprop', 'ro.build.display.id'])
        demand(uid == '0' and dt == 'gxlx2_p291_1g' and api == '28' and build == self.expected_build,
               'Live root/profile/build differs from the authorized first P291')
        self.boot_id = self.command('profile-boot-id', ['/system/bin/toybox', 'cat', '/proc/sys/kernel/random/boot_id'])
        demand(re.fullmatch(r'[0-9a-f-]{36}', self.boot_id), 'Invalid boot identifier')
        self.state.update(root_uid=0, build=build, boot_id=self.boot_id, state='reading')
        self.save()

    def metadata(self, name, suffix, timeout):
        major, minor, size = PARTITIONS[name]
        prefix = name+'-'+suffix
        listing = self.command(prefix+'-alias', ['/system/bin/toybox', 'ls', '-ld', '/dev/block/'+name], timeout())
        demand(parse_alias(listing, name) == (major, minor), 'Block major/minor changed: '+name)
        length = self.command(prefix+'-size', ['/system/bin/toybox', 'blockdev', '--getsize64', '/dev/block/'+name], timeout())
        demand(length.isdecimal() and int(length) == size, 'Block size changed: '+name)
        mounts = self.command(prefix+'-mounts', ['/system/bin/toybox', 'cat', '/proc/mounts'], timeout())
        mounts = parse_mounts(mounts, name, name in STAGES['system'])
        boot_id = self.command(prefix+'-boot-id', ['/system/bin/toybox', 'cat', '/proc/sys/kernel/random/boot_id'], timeout())
        demand(boot_id == self.boot_id, 'TV restarted during backup; stop without retry')
        return {'major': major, 'minor': minor, 'bytes': size, 'mounts': mounts}

    def partition(self, name):
        size = PARTITIONS[name][2]
        maximum = 900 if name in STAGES['system'] else 180
        began = time.monotonic()
        deadline = began + maximum

        def remaining(cap=None):
            seconds = deadline-time.monotonic()
            demand(seconds > 3, name+': partition deadline expired')
            return min(seconds, cap) if cap is not None else seconds

        row = {'name': name, 'expected_bytes': size, 'state': 'checking',
               'started': stamp(), 'deadline_seconds': maximum, 'copy_exit': None}
        self.state['partitions'].append(row)
        self.save()
        row['before'] = self.metadata(name, 'before', lambda: remaining(15))
        partial = self.output / (name+'.img.parcial')
        final = self.output / (name+'.img')
        read_seconds = max(1, math.floor(remaining())-2)
        nonce = uuid.uuid4().hex
        footer_prefix = ('\nTVBASE_RAW_'+nonce+'_EXIT=').encode('ascii')
        footer_limit = len(footer_prefix)+4  # decimal status 0..255 and newline
        # shell -T altered binary line endings on this actual Windows/ADB path.
        # exec-out preserves bytes but does not itself prove remote exit status.
        # A fresh, exact-offset footer reports cat/timeout's real status instead.
        script = (f'/system/bin/toybox timeout -s KILL {read_seconds} '
                  f'/system/bin/toybox cat /dev/block/{name}; tvbase_rc=$?; '
                  f'/system/bin/toybox printf "\\nTVBASE_RAW_{nonce}_EXIT=%d\\n" "$tvbase_rc"')
        arguments = ['exec-out', '/system/xbin/su 0 /system/bin/sh -c '+shlex.quote(script)]
        row.update(state='copying', read_arguments=arguments, read_bytes=0)
        self.save()
        print(f'{name}: iniciando lectura de {size//MIB} MiB', flush=True)
        blocks = queue.Queue(maxsize=4)
        stopping = threading.Event()
        reader_errors = []
        count = 0
        last_report = time.monotonic()
        streaming_hash = hashlib.sha256()

        with (self.output/(name+'-copy.stderr.txt')).open('xb') as errors, partial.open('xb') as image:
            process = subprocess.Popen(self.argv(arguments), stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=errors, creationflags=FLAGS)

            def reader():
                try:
                    while not stopping.is_set():
                        block = process.stdout.read(1024*1024)
                        while not stopping.is_set():
                            try:
                                blocks.put(block, timeout=0.25)
                                break
                            except queue.Full:
                                continue
                        if not block:
                            return
                except Exception as error:
                    reader_errors.append(repr(error))

            worker = threading.Thread(target=reader, daemon=True, name='adb-binary-reader')
            worker.start()
            try:
                while True:
                    remaining()
                    demand(not reader_errors, 'ADB reader failed: '+repr(reader_errors))
                    try:
                        block = blocks.get(timeout=0.25)
                    except queue.Empty:
                        block = None
                    if block == b'':
                        break
                    if block:
                        before = count
                        count += len(block)
                        demand(count <= size+footer_limit, name+': output exceeds partition plus footer')
                        image.write(block)
                        if before < size:
                            streaming_hash.update(block[:size-before])
                    if time.monotonic()-last_report >= 15:
                        image.flush()
                        os.fsync(image.fileno())
                        row.update(read_bytes=count, elapsed_seconds=round(time.monotonic()-began, 1))
                        self.save()
                        print(f'{name}: {count//MIB}/{size//MIB} MiB, {row["elapsed_seconds"]} s', flush=True)
                        last_report = time.monotonic()
                row['transport_exit'] = process.wait(timeout=remaining())
                demand(row['transport_exit'] == 0, f'{name}: ADB transport exit {row["transport_exit"]}')
                demand(size < count <= size+footer_limit, name+': missing data or status footer')
                image.flush()
                os.fsync(image.fileno())
            finally:
                stopping.set()
                if process.poll() is None:
                    process.kill()  # PC adb client only; remote timeout bounds its reader.
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    pass
                row['transport_exit'] = process.returncode
                worker.join(timeout=2)
                process.stdout.close()
                image.flush()
                os.fsync(image.fileno())
                errors.flush()
                os.fsync(errors.fileno())
                row['raw_bytes_with_footer'] = count
                row['read_bytes'] = min(count, size)
                self.save()

        row['state'] = 'verifying'
        self.save()
        with partial.open('rb') as image:
            image.seek(size)
            footer = image.read(footer_limit+1)
        footer_match = re.fullmatch(re.escape(footer_prefix)+rb'(0|[1-9][0-9]{0,2})\n', footer)
        demand(footer_match is not None and int(footer_match.group(1)) <= 255,
               name+': missing/invalid exact-offset remote exit footer')
        row['copy_exit'] = int(footer_match.group(1))
        row['footer_verified'] = True
        demand(row['copy_exit'] == 0, f'{name}: remote read exit {row["copy_exit"]}')
        disk_hash = hashlib.sha256()
        with partial.open('rb') as image:
            left = size
            while left:
                block = image.read(min(left, 1024*1024))
                demand(bool(block), name+': truncated local image')
                remaining()
                disk_hash.update(block)
                left -= len(block)
        demand(partial.stat().st_size == count and disk_hash.hexdigest() == streaming_hash.hexdigest(),
               name+': local reread differs')
        remote = self.command(name+'-sha256-after', ['/system/bin/toybox', 'sha256sum', '/dev/block/'+name], remaining())
        match = re.fullmatch(r'([0-9a-f]{64})  '+re.escape('/dev/block/'+name), remote)
        demand(match is not None, name+': invalid remote SHA256 response')
        row.update(pc_sha256=disk_hash.hexdigest(), remote_sha256_after=match.group(1))
        demand(row['pc_sha256'] == row['remote_sha256_after'], name+': remote partition changed or copy differs')
        row['after'] = self.metadata(name, 'after', lambda: remaining(15))
        demand(row['before'] == row['after'], name+': block/mount identity changed')
        demand(not final.exists(), 'Refusing to overwrite a previous image')
        # Remove ONLY the validated protocol footer from this PC's private copy.
        # On every earlier failure the original .parcial including footer stays.
        with partial.open('r+b') as image:
            image.truncate(size)
            image.flush()
            os.fsync(image.fileno())
        demand(partial.stat().st_size == size, 'Final local length differs')
        partial.rename(final)
        row.update(state='verified', file=final.name, bytes=size, sha256=disk_hash.hexdigest(),
                   completed=stamp(), seconds=round(time.monotonic()-began, 3),
                   atomic_snapshot=False)
        self.save()
        print(f'{name}: verificada, {size//MIB} MiB, SHA256 {row["sha256"]}', flush=True)

    def run(self):
        try:
            self.profile()
            for name in self.names:
                self.partition(name)
            self.state.update(state='verified_selected_partitions', completed=stamp(), exit=0)
            self.save()
            print(json.dumps({'state': self.state['state'], 'manifest': str(self.receipt),
                              'complete_restore_backup': False}), flush=True)
            return 0
        except BaseException as error:
            for row in self.state['partitions']:
                if row['state'] != 'verified':
                    row.update(state='failed', error=repr(error))
            self.state.update(state='failed', error=repr(error), completed=stamp(), exit=1)
            self.save()
            print(json.dumps({'state': 'failed', 'error': repr(error),
                              'manifest': str(self.receipt), 'retry': False}), flush=True)
            return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=tuple(STAGES), required=True)
    args = parser.parse_args()
    return Backup(args.stage).run()


if __name__ == '__main__':
    raise SystemExit(main())
