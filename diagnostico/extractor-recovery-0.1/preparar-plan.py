"""Prepara en PC un plan privado de extracción a partir de un ZIP APK verificado.

Uso: preparar-plan.py --apk-report <captura.zip> --output <proyecto/privado/plan.json>
La carpeta de salida debe existir. No copia al USB, extrae archivos del ZIP ni
produce instrucciones de instalación. DT/perfil asocian una captura candidata;
el UUID de la APK identifica su instalación, no demuestra identidad física.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / 'privado'
IMPORTER_PATH = ROOT / 'diagnostico' / 'reconocedor-0.1' / 'importar-informes.py'
PROFILE = re.compile(r'[a-z0-9-]{1,80}', re.ASCII)
SHA256 = re.compile(r'[0-9a-f]{64}', re.ASCII)
OUTPUT_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.json', re.ASCII)
RESERVED = re.compile(r'con|prn|aux|nul|com[1-9]|lpt[1-9]', re.I | re.ASCII)
UNKNOWN_DT = frozenset(('unknown', 'desconocido', 'unavailable', 'not available', 'null', 'none', 'n/a'))


class InvalidPlan(ValueError):
    """Error whose message is fixed and safe to present without private values."""


def need(condition, message):
    if not condition:
        raise InvalidPlan(message)


def load_importer():
    """Use the sealed recognizer's actual verifier without creating bytecode."""
    spec = importlib.util.spec_from_file_location('tvbase_recognition_verifier', IMPORTER_PATH)
    need(spec is not None, 'No se pudo cargar el verificador del reconocedor.')
    module = importlib.util.module_from_spec(spec)
    # Loading source this way avoids modifying the released recognizer directory
    # with __pycache__ files. The path is fixed; no input controls executable code.
    exec(compile(IMPORTER_PATH.read_bytes(), str(IMPORTER_PATH), 'exec'), module.__dict__)
    return module


def canonical_uuid(value):
    need(isinstance(value, str), 'Falta un UUID textual de la captura APK.')
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        raise InvalidPlan('UUID de captura APK inválido.') from None
    need(str(parsed) == value and parsed.int != 0, 'UUID de captura APK no canónico o nulo.')
    return value


def make_plan(verified_item):
    """Return the exact eight-field ProfilePlan contract from verified metadata.

    This pure helper does not verify a ZIP by itself; prepare_plan always invokes
    the real archive verifier first. No offsets, source paths, firmware choices,
    instructions or other metadata from the APK can enter the plan.
    """
    need(isinstance(verified_item, dict), 'Resultado de verificación ausente.')
    report = verified_item.get('report')
    need(isinstance(report, dict) and report.get('schema') == 'tvbase-recognition-1',
         'Informe del reconocedor ausente o incompatible.')
    digest = verified_item.get('sha256')
    need(isinstance(digest, str) and SHA256.fullmatch(digest), 'SHA256 del ZIP verificado inválido.')
    dt = report.get('dt_identity')
    need(isinstance(dt, str) and dt.strip() and dt.strip().casefold() not in UNKNOWN_DT,
         'La captura no contiene una identidad DT conocida.')
    try:
        dt_bytes = dt.encode('utf-8')
    except UnicodeError:
        raise InvalidPlan('La identidad DT no es UTF-8 válida.') from None
    need(len(dt_bytes) <= 4096, 'La identidad DT excede el límite de recovery.')
    need(not any(unicodedata.category(c) in ('Cc', 'Cs') for c in dt),
         'La identidad DT contiene caracteres de control.')
    profile = report.get('suggested_profile')
    need(isinstance(profile, str) and PROFILE.fullmatch(profile),
         'El perfil candidato debe contener solo letras ASCII minúsculas, números o guiones.')
    name = report.get('display_name')
    need(isinstance(name, str) and 0 < len(name) <= 256 and
         not any(unicodedata.category(c) in ('Cc', 'Cs') for c in name),
         'Nombre visible de la captura ausente o inválido.')
    return {
        'schema': 'tvbase-recovery-plan-1',
        'apk_capture_id': canonical_uuid(report.get('capture_id')),
        'apk_device_id': canonical_uuid(report.get('device_id')),
        'apk_zip_sha256': digest,
        'expected_dt': dt,
        'profile': profile,
        'display_name': name,
        'operation': 'capture_read_only',
    }


def output_path(value, verifier):
    path = Path(value).absolute()
    need('..' not in path.parts and path.is_relative_to(PRIVATE) and path != PRIVATE,
         'La salida debe ser un archivo nuevo dentro de privado del proyecto.')
    need(OUTPUT_NAME.fullmatch(path.name) and not RESERVED.fullmatch(path.name.split('.')[0]),
         'El nombre de salida debe ser un nombre simple terminado en .json.')
    try:
        verifier.ordinary(path.parent, directory=True)
    except (OSError, verifier.InvalidCapture):
        raise InvalidPlan('La carpeta de salida debe existir y no contener enlaces.') from None
    need(not os.path.lexists(path), 'El archivo de salida ya existe; no se sobrescribe.')
    return path


def _readback(path, expected, verifier):
    stream, before = verifier.open_readonly(path)
    with stream:
        raw = stream.read(len(expected) + 1)
        verifier.unchanged(stream, path, before)
    need(raw == expected, 'La relectura del plan no coincide con los bytes escritos.')


def write_new_plan(path, plan, verifier):
    """Exclusive temporary file, fsync/readback, then atomic no-replace link.

    Only the private local project filesystem is used. Failure retains the
    temporary file; the final name is never published before the temporary
    payload has passed file fsync and readback. Directory fsync is not claimed.
    """
    raw = (json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    need(len(raw) <= 16384, 'El plan excede el límite de lectura de recovery.')
    temporary = path.with_name(path.name + '.partial')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    parent_before = verifier.ordinary(path.parent, directory=True)
    # Exclusive creation also rejects a previously interrupted preparation.
    descriptor = os.open(temporary, flags, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'La salida temporal no es un archivo regular exclusivo.')
        need(stream.write(raw) == len(raw), 'Escritura de plan incompleta.')
        stream.flush()
        os.fsync(stream.fileno())
        written = os.fstat(stream.fileno())
    need(verifier.info_key(written) == verifier.info_key(verifier.ordinary(temporary)),
         'El temporal cambió después de escribirlo.')
    _readback(temporary, raw, verifier)
    parent_after = verifier.ordinary(path.parent, directory=True)
    need((parent_before.st_dev, parent_before.st_ino) == (parent_after.st_dev, parent_after.st_ino),
         'La carpeta de salida cambió durante la preparación.')
    # os.link publishes a complete inode atomically and fails if the final path
    # already exists. There is no replace/rename fallback on unsupported volumes.
    os.link(temporary, path)
    # Only this invocation's exclusive temporary name is removed, after checking
    # both paths still refer to the same inode and contain the verified bytes.
    temp_info, final_info = temporary.lstat(), path.lstat()
    need(stat.S_ISREG(temp_info.st_mode) and stat.S_ISREG(final_info.st_mode) and
         (temp_info.st_dev, temp_info.st_ino) == (final_info.st_dev, final_info.st_ino) ==
         (written.st_dev, written.st_ino), 'La publicación del plan cambió de identidad.')
    temporary.unlink()
    _readback(path, raw, verifier)
    return hashlib.sha256(raw).hexdigest()


def prepare_plan(apk_report, output):
    verifier = load_importer()
    try:
        item = verifier.verify_archive(apk_report, emit=None)
    except verifier.InvalidCapture:
        raise InvalidPlan('El ZIP de la APK no superó la verificación completa de integridad.') from None
    plan = make_plan(item)
    path = output_path(output, verifier)
    need(verifier.info_key(verifier.ordinary(item['source'])) == item['source_snapshot'],
         'El ZIP cambió después de su verificación; no se creó el plan.')
    digest = write_new_plan(path, plan, verifier)
    # No UUID, DT, nickname, input path or output path is printed by the CLI.
    return {'state': 'plan_verified_local', 'sha256': digest, 'file_fsync': True,
            'readback_verified': True, 'usb_modified': False,
            'physical_identity_proven': False, 'installation_authorized': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk-report', required=True, help='ZIP del reconocedor 0.1; lectura y verificación completas.')
    parser.add_argument('--output', required=True, help='Archivo .json nuevo dentro del privado del proyecto; carpeta existente.')
    args = parser.parse_args(argv)
    try:
        result = prepare_plan(args.apk_report, args.output)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    except Exception as error:
        message = str(error) if isinstance(error, InvalidPlan) else 'La preparación falló por un error de lectura o escritura.'
        print(json.dumps({'state': 'failed', 'error': message, 'installation_authorized': False}, ensure_ascii=False), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
