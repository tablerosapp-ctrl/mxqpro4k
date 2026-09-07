"""Resume marcas de cierre de un archivo local; no se conecta ni escribe al TV.

El resultado contiene identificadores de marcas, líneas y tiempos, nunca líneas
crudas. La atribución al intento la declara el operador; no se deduce del reloj.
Una marca alcanzada no demuestra retorno, reinicio físico ni instalación.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024
KERNEL_TIME = re.compile(r'^\[\s*(\d+\.\d+)(?:@\d+)?\]')
MARKERS = {
    'shutdown_broadcast': r'\bShutdownThread\b.*Sending shutdown broadcast',
    'activity_manager_enter': r'\bShutdownThread\b.*Shutting down activity manager',
    'activity_manager_timeout': r'\bActivityManager\b.*Activity manager shutdown timed out',
    'package_manager_enter': r'\bShutdownThread\b.*Shutting down package manager',
    'uncrypt_enter': r'\bShutdownThread\b.*Calling uncrypt and monitoring',
    'uncrypt_timeout': r'\bShutdownThread\b.*Timed out waiting for uncrypt',
    'uncrypt_error': r'\bShutdownThread\b.*Error uncrypting file',
    'framework_low_level_request': r'\bShutdownThread\b.*Rebooting, reason:',
    'init_reboot_enter': r'\binit\b.*Reboot start, reason:',
    'watchdog_started': r'\bwatchdogd: watchdogd started',
    'kernel_reboot_notifier': r'\bmeson_wdt\b.*reboot_notify: disable watchdog \(event = 1\)',
    'kernel_restart_message': r'\bRestarting system(?: with command|$)',
    'kernel_boot_banner': r'\bLinux version \d+\.',
    'sdio_cmd53': r'\bsdio: cmd:53\b',
}


def analyze(raw, origin, attempt):
    if origin not in ('pstore', 'logcat'):
        raise ValueError('Origen debe ser pstore o logcat.')
    if attempt not in ('previo-04', 'oem-07', 'no-atribuido'):
        raise ValueError('Intento debe ser previo-04, oem-07 o no-atribuido.')
    if not raw or len(raw) > MAX_BYTES or b'\0' in raw:
        raise ValueError('Entrada vacía, demasiado grande o con NUL: no clasificar como texto íntegro.')
    text = raw.decode('utf8', 'strict')
    events, times, resets = [], [], []
    compiled = {name: re.compile(pattern) for name, pattern in MARKERS.items()}
    # Console pstore is time ordered. Logcat can merge buffers; no durations there.
    for number, line in enumerate(text.splitlines(), 1):
        match = KERNEL_TIME.match(line)
        stamp = float(match[1]) if match else None
        if stamp is not None:
            if times and stamp < times[-1][1] - 0.001:
                resets.append(number)
            times.append((number, stamp))
        for marker, pattern in compiled.items():
            if pattern.search(line):
                events.append({'marker': marker, 'line': number, 'kernel_seconds': stamp})
    by_marker = {}
    for event in events:
        by_marker.setdefault(event['marker'], []).append(event)
    notify = by_marker.get('kernel_reboot_notifier', [])
    banners = by_marker.get('kernel_boot_banner', [])
    interval = None
    # Never combine multiple notifier cycles or a new boot into one duration.
    if origin == 'pstore' and len(notify) == 1 and not resets and not banners and times:
        t = notify[0]['kernel_seconds']
        if t is not None and times[-1][0] >= notify[0]['line']:
            interval = round(times[-1][1] - t, 6)
    warnings = []
    if resets or banners or len(notify) > 1:
        warnings.append('Posible mezcla de arranques/intentos; segmentar antes de inferir duración.')
    if attempt == 'no-atribuido':
        warnings.append('Sin vínculo acreditado con un intento físico.')
    if origin == 'pstore':
        warnings.append('Pstore puede conservar un arranque anterior; no usar su fecha como atribución.')
    # Absence is intentionally never promoted into a diagnosis.
    return {
        'schema_version': 1,
        'sha256': hashlib.sha256(raw).hexdigest(),
        'bytes': len(raw),
        'origin_declared': origin,
        'attempt_declared': attempt,
        'attempt_verified_by_parser': False,
        'events': events,
        'marker_counts': {key: len(value) for key, value in by_marker.items()},
        'kernel_time_regressions_at_lines': resets,
        'seconds_logged_after_single_notifier': interval,
        'warnings': warnings,
        'limits': [
            'El parser reconoce texto; no autentica el origen ni identifica la función bloqueada.',
            'Ausencia de marca no demuestra ausencia de ejecución.',
            'Restarting system precede machine_restart; no acredita reset físico.',
            'No se declara recovery, instalación, copia íntegra ni BCB/mapa correcto.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--origen', choices=('pstore', 'logcat'), required=True)
    parser.add_argument('--intento', choices=('previo-04', 'oem-07', 'no-atribuido'), default='no-atribuido')
    args = parser.parse_args()
    if args.input.is_symlink() or not args.input.is_file():
        parser.error('Se requiere un archivo regular local, sin enlace simbólico.')
    with args.input.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    print(json.dumps(analyze(raw, args.origen, args.intento), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
