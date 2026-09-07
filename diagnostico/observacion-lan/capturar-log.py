"""Capture one bounded Android logcat stream; never request an update/reboot.

The target comes from the locally verified private session. Output and its
receipt stay in that same ignored directory. A disconnect is not proof of a
successful reboot, recovery entry or installation.
"""
import argparse
import datetime
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--since', help='TV log timestamp MM-DD HH:MM:SS.mmm; includes buffered messages from that point')
    args = parser.parse_args()
    if args.since is not None:
        if not re.fullmatch(r'\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', args.since):
            parser.error('--since requires MM-DD HH:MM:SS.mmm in the TV clock')
        try:
            datetime.datetime.strptime('2000-' + args.since, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            parser.error('--since is not a valid calendar time')
    source = args.session.resolve()
    assert source.is_relative_to(ROOT / 'diagnostico') and source.parent.name == 'privado'
    assert 10 <= args.seconds <= 600
    session = json.loads(source.read_text(encoding='utf-8-sig'))
    target = session['target']
    host, port = target.split(':')
    address = ipaddress.ip_address(host)
    assert address.version == 4 and address.is_private and not address.is_loopback
    assert port == '5555'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')
    output = source.parent / ('cierre-en-vivo-' + stamp + '.txt')
    receipt = output.with_suffix('.json')
    command = (
        '/system/bin/toybox timeout -s KILL ' + str(args.seconds) +
        ' /system/bin/logcat -b main -b system -b crash -v threadtime -T ' +
        ('"' + args.since + '"' if args.since else '1') +
        ' ShutdownThread:V RecoverySystem:V RecoverySystemService:V uncrypt:V'
        ' ActivityManager:I BatteryStats:W AppOps:W BluetoothManagerService:I WifiNative:E init:I "*:S"'
    )
    record = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'target': target, 'command': command, 'limit_seconds': args.seconds,
              'buffer_since_tv_clock': args.since,
              'max_bytes': 8 * 1024 * 1024, 'update_requested': False,
              'reboot_requested': False, 'state': 'running'}
    start = time.monotonic()
    with output.open('xb') as log:
        child = subprocess.Popen([str(ROOT / 'tools/platform-tools/adb.exe'), '-s', target,
                                  'exec-out', command], stdout=log, stderr=subprocess.STDOUT,
                                 creationflags=0x08000000)
        record['host_pid'] = child.pid
        receipt.write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
        print(json.dumps({'capture_started': True, 'receipt': str(receipt.relative_to(ROOT))}), flush=True)
        reason = 'stream_ended'
        try:
            while child.poll() is None:
                if time.monotonic() - start > args.seconds + 5:
                    reason = 'host_deadline'; break
                if output.stat().st_size >= record['max_bytes']:
                    reason = 'size_limit'; break
                time.sleep(0.5)
        finally:
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait(timeout=3)
            log.flush(); os.fsync(log.fileno())
    record.update(state='finished', reason=reason, exit_code=child.returncode,
                  elapsed_seconds=round(time.monotonic() - start, 3),
                  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  bytes=output.stat().st_size,
                  sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  physical_result='not_inferred_from_stream_exit')
    with receipt.open('w', encoding='utf8') as target_file:
        json.dump(record, target_file, indent=2); target_file.write('\n')
        target_file.flush(); os.fsync(target_file.fileno())
    print(json.dumps({'capture_finished': True, 'reason': reason,
                      'exit_code': child.returncode, 'bytes': record['bytes']}), flush=True)


if __name__ == '__main__':
    main()
