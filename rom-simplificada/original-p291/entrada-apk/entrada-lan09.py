#!/usr/bin/env python3
"""One explicit LAN launch of the sealed USB helper; never reset or retry launch."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import uuid

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
PRIVATE = BASE / "privado"
SESSION = ROOT / "diagnostico/primer-tv-lan-20260907-184926/privado/session.json"
ADB = ROOT / "tools/platform-tools/adb.exe"
APK_SHA = "1d0f267e818acca5562048f9961c7c234f36b8cc81f827cb3eac9e3fcd2505a4"
APK_BYTES = 61843
PACKAGE = "local.tvbase.acceso"
ACTIVE = "/data/local/tmp/tvbase-entry-in-progress"
BUILD = "ampere-userdebug 9 PPR1.180610.011 20250226 test-keys"
MAX_OUTPUT = 131072


class ClientError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ClientError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Clave JSON duplicada")
        result[key] = value
    return result


def decode_json(data):
    def invalid(value):
        raise ClientError("Constante JSON no admitida: " + value)
    try:
        return json.loads(data, object_pairs_hook=unique_pairs, parse_constant=invalid)
    except (ValueError, UnicodeError) as error:
        raise ClientError("JSON inválido") from error


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def fsync_dir(directory):
    # Windows has no portable fsync-directory. Updates use MoveFileExW with
    # WRITE_THROUGH below; each file is also flushed with os.fsync and read back.
    if os.name != "nt":
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def durable_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    fsync_dir(path.parent)
    require(path.read_bytes() == data, "Lectura posterior PC diferente: " + path.name)


def durable_replace(path, data):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    durable_new(temporary, data)
    if os.name == "nt":
        move = ctypes.WinDLL("kernel32", use_last_error=True).MoveFileExW
        move.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        move.restype = ctypes.c_int
        if not move(str(temporary), str(path), 0x1 | 0x8):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        os.replace(temporary, path)
        fsync_dir(path.parent)
    require(path.read_bytes() == data, "No se confirmó persistencia PC: " + path.name)


@contextmanager
def client_lock(directory):
    path = directory / "client.lock"
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
            os.fsync(stream.fileno())
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ClientError("Otro cliente está observando este intento; no se inició nada") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def nonce_ok(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{32}", value), "Nonce inválido")
    return value


def apk_ok(value):
    require(isinstance(value, str) and len(value) <= 512
            and value.startswith("/data/app/") and value.endswith("/base.apk")
            and re.fullmatch(r"[A-Za-z0-9_./=+~\-]+", value)
            and "/../" not in value and "/./" not in value, "Ruta APK inválida")
    return value


def quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


def entry_command(apk, nonce, operation):
    apk_ok(apk)
    nonce_ok(nonce)
    require(operation in ("launch", "status"), "Operación no admitida")
    run = ("CLASSPATH=" + quote(apk) + " /system/bin/app_process /system/bin "
           "local.tvbase.acceso.PreparationHelper " + operation + " " + nonce)
    outer = ('if [ "$(/system/bin/id -u)" != 2000 ]; then exit 40; fi; '
             '/system/xbin/su 0 /system/bin/sh -c ' + quote(run)
             + "; tvbase_rc=$?; printf '\\nTVBASE_EXIT:" + nonce
             + ":%s\\n' \"$tvbase_rc\"; exit \"$tvbase_rc\"")
    command = "/system/bin/sh -c " + quote(outer)
    require(len(command.encode("utf-8")) + 6 <= 4096, "Comando ADB demasiado largo")
    return command


def check_command(command, nonce, label):
    nonce_ok(nonce)
    require(re.fullmatch(r"[a-z_]+", label), "Etiqueta inválida")
    outer = (command + "; tvbase_rc=$?; printf '\\nTVBASE_CHECK:" + nonce + ":" + label
             + ":%s\\n' \"$tvbase_rc\"; exit \"$tvbase_rc\"")
    return "/system/bin/sh -c " + quote(outer)


def check_output(raw, nonce, label, local_exit):
    require(local_exit == 0 and len(raw) <= MAX_OUTPUT, "Lectura ADB fallida o excesiva")
    marker = ("\nTVBASE_CHECK:" + nonce + ":" + label + ":0\n").encode("ascii")
    require(raw.endswith(marker) and raw.count(b"TVBASE_CHECK:") == 1,
            "Falta código remoto 0 exacto en " + label)
    return raw[:-len(marker)]


def parse_result(raw, nonce, operation, local_exit=0):
    nonce_ok(nonce)
    require(operation in ("launch", "status"), "Operación inválida")
    require(local_exit == 0 and 0 < len(raw) <= MAX_OUTPUT, "Transporte fallido o salida excesiva")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ClientError("Salida no UTF-8") from error
    require(text.endswith("\n") and "\r" not in text and "\x00" not in text, "Salida incompleta o alterada")
    lines = [line for line in text.split("\n") if line]
    require(len(lines) <= 128, "Demasiadas líneas")
    values = []
    exit_code = None
    terminal = False
    for line in lines:
        require(exit_code is None, "Contenido posterior al código remoto")
        if line.startswith("TVBASE_ENTRY:"):
            require(not terminal, "Más de un resultado terminal")
            value = decode_json(line[len("TVBASE_ENTRY:"):])
            require(isinstance(value, dict) and value.get("nonce") == nonce, "Nonce de respuesta distinto")
            state = value.get("state")
            require(state in ("stage", "launched", "prepared", "incomplete"), "Estado no admitido")
            require(state != "launched" or operation == "launch", "Launch recibido al consultar")
            require(state != "prepared" or operation == "status", "Prepared recibido antes de consultar")
            for key in ("reset_requested", "userdata_wiped", "firmware_images_written"):
                require(value.get(key) is False, "Efecto inesperado o campo ausente: " + key)
            if state == "prepared":
                require(value.get("env_readback_verified") is True
                        and value.get("bcb_readback_verified") is True, "Falta lectura final de ENV/BCB")
                require(isinstance(value.get("manifest_sha256"), str)
                        and re.fullmatch(r"[0-9a-f]{64}", value["manifest_sha256"]), "Hash final inválido")
                require(isinstance(value.get("report"), str)
                        and re.fullmatch(r"/mnt/media_rw/[A-Za-z0-9_-]+/TVBASE-entrada09-" + nonce,
                                         value["report"]), "Ruta de informe inesperada")
            terminal = state != "stage"
            values.append(value)
        elif line.startswith("TVBASE_EXIT:"):
            match = re.fullmatch(r"TVBASE_EXIT:" + nonce + r":(0|[1-9][0-9]{0,2})", line)
            require(match is not None and values, "Código remoto o nonce inválido")
            exit_code = int(match.group(1))
            require(exit_code <= 255, "Código remoto fuera de rango")
        else:
            raise ClientError("Línea no admitida en protocolo")
    require(exit_code is not None and values, "Falta resultado y código remoto")
    last = values[-1]
    require((last["state"] == "incomplete" and exit_code in (0, 1)) or exit_code == 0,
            "Código remoto diferente de cero")
    require(operation != "launch" or last["state"] in ("launched", "incomplete"),
            "No se confirmó el lanzamiento")
    return {"result": last, "remote_exit": exit_code, "events": values}


def load_session(path):
    data = decode_json(path.read_bytes())
    require(isinstance(data, dict) and isinstance(data.get("target"), str), "Sesión sin destino")
    match = re.fullmatch(r"([0-9.]+):5555", data["target"])
    require(match is not None, "Solo se admite el destino IPv4:5555 de la sesión privada")
    address = ipaddress.ip_address(match.group(1))
    require(any(address in ipaddress.ip_network(net) for net in
                ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")), "Destino fuera de LAN privada")
    return data["target"]


class Attempt:
    def __init__(self, path, data):
        self.path, self.data = path, data

    def save(self):
        self.data["updated_utc"] = now()
        durable_replace(self.path, json_bytes(self.data))

    def transition(self, state, **values):
        self.data.update(values)
        self.data["state"] = state
        self.save()


def bounded_process(args, timeout, creationflags):
    """Bound both pipes while reading; stop only the local ADB client on failure."""
    process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, creationflags=creationflags)
    overflow = threading.Event()
    buffers = [bytearray(), bytearray()]
    errors = []
    guard = threading.Lock()

    def consume(stream, index):
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    return
                with guard:
                    room = MAX_OUTPUT - len(buffers[index])
                    buffers[index].extend(chunk[:room])
                    if len(chunk) > room:
                        overflow.set()
                        return
        except OSError as error:
            with guard:
                errors.append(type(error).__name__)
        finally:
            stream.close()

    readers = [threading.Thread(target=consume, args=(stream, i), daemon=True)
               for i, stream in enumerate((process.stdout, process.stderr))]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while process.poll() is None:
            if overflow.is_set() or time.monotonic() >= deadline:
                timed_out = not overflow.is_set()
                process.kill()  # PC adb.exe only; never a command to the TV.
                break
            try:
                process.wait(timeout=min(0.1, max(0.001, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                pass
        process.wait(timeout=5)
    except BaseException:
        if process.poll() is None:
            process.kill()
        raise
    finally:
        for reader in readers:
            reader.join(timeout=2)
    with guard:
        return SimpleNamespace(stdout=bytes(buffers[0]), stderr=bytes(buffers[1]),
                               returncode=process.returncode, timed_out=timed_out,
                               output_limit=overflow.is_set(),
                               incomplete_pipe=bool(errors) or any(r.is_alive() for r in readers))


class Transport:
    def __init__(self, attempt, target, timeout=30, adb=ADB, runner=bounded_process):
        self.attempt, self.target, self.timeout, self.adb, self.runner = attempt, target, timeout, adb, runner

    def run(self, label, command):
        ident = label + "-" + uuid.uuid4().hex
        directory = self.attempt.path.parent
        request = {"created_utc": now(), "label": label, "command": command,
                   "target": self.target, "timeout_seconds": self.timeout}
        durable_new(directory / (ident + ".request.json"), json_bytes(request))
        try:
            completed = self.runner([str(self.adb), "-s", self.target, "exec-out", command],
                                    timeout=self.timeout,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
            timed_out = getattr(completed, "timed_out", False)
            output_limit = getattr(completed, "output_limit", False)
            incomplete_pipe = getattr(completed, "incomplete_pipe", False)
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
            output_limit, incomplete_pipe = False, True
        durable_new(directory / (ident + ".stdout"), stdout)
        durable_new(directory / (ident + ".stderr"), stderr)
        row = {"file_prefix": ident, "local_exit": code, "timeout": timed_out,
               "output_limit": output_limit, "incomplete_pipe": incomplete_pipe,
               "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
               "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
               "remote_cancel_requested": False}
        durable_new(directory / (ident + ".result.json"), json_bytes(row))
        self.attempt.data["observations"].append(row)
        self.attempt.save()
        require(not timed_out, "Terminó el plazo del cliente; el proceso remoto podría continuar")
        require(not output_limit and not incomplete_pipe, "Salida excesiva o incompleta; no acredita cancelación remota")
        return stdout, code


def checked(transport, nonce, label, command):
    raw, code = transport.run(label, check_command(command, nonce, label))
    return check_output(raw, nonce, label, code)


def preflight(transport, nonce, preparing):
    require(checked(transport, nonce, "shell_uid", "/system/bin/id -u") == b"2000\n", "ADB no es shell UID 2000")
    require(checked(transport, nonce, "root_uid", "/system/xbin/su 0 /system/bin/id -u") == b"0\n", "Root existente no disponible")
    require(checked(transport, nonce, "api", "/system/bin/getprop ro.build.version.sdk") == b"28\n", "API diferente")
    require(checked(transport, nonce, "dt", "/system/bin/cat /proc/device-tree/amlogic-dt-id") == b"gxlx2_p291_1g\0", "DT diferente")
    require(checked(transport, nonce, "build", "/system/bin/getprop ro.build.display.id") == (BUILD + "\n").encode(), "Build diferente")
    require(checked(transport, nonce, "kernel", "/system/bin/uname -r") == b"4.9.113\n", "Kernel diferente")
    raw = checked(transport, nonce, "apk_path", "/system/bin/pm path " + PACKAGE)
    require(raw.startswith(b"package:") and raw.endswith(b"\n") and raw.count(b"\n") == 1, "Ruta APK ausente o splits inesperados")
    apk = apk_ok(raw[8:-1].decode("ascii", "strict"))
    require(checked(transport, nonce, "apk_size", "/system/bin/toybox stat -c %s " + quote(apk)) == (str(APK_BYTES) + "\n").encode(), "Tamaño APK diferente")
    require(checked(transport, nonce, "apk_sha", "/system/bin/toybox sha256sum " + quote(apk)) == (APK_SHA + "  " + apk + "\n").encode(), "SHA256 de APK instalado diferente")
    if preparing:
        scan = "/system/bin/toybox find /data/local/tmp -maxdepth 1 -name tvbase-entry-in-progress -print"
        raw = checked(transport, nonce, "active", "/system/xbin/su 0 /system/bin/sh -c " + quote(scan))
        require(raw == b"", "Existe preparación interna; no se relanzará ni se eliminará")
    return apk


def new_attempt(private, session, target, authorization_note):
    private.mkdir(parents=True, exist_ok=True)
    pointer = private / "LAN09-ACTIVE.json"
    require(not pointer.exists(), "Ya existe LAN09-ACTIVE.json; revisar el intento conservado, no repetir prepare")
    nonce = uuid.uuid4().hex
    directory = private / ("lan09-" + nonce)
    directory.mkdir()
    fsync_dir(private)
    data = {"schema": "tvbase-entry-lan09-attempt-v1", "created_utc": now(), "nonce": nonce,
            "target": target, "session_path": str(session.resolve()), "apk_sha256": APK_SHA,
            "state": "preflight_pending", "launch_issued": False, "observations": [],
            "authorization_note": authorization_note, "flag_is_not_external_authorization": True,
            "automatic_reset": False, "automatic_retry": False}
    path = directory / "attempt.json"
    durable_new(path, json_bytes(data))
    # Exclusive creation arbitrates concurrent prepares. Never remove this pointer
    # automatically, even after preflight failure or a successful preparation.
    durable_new(pointer, json_bytes({"attempt": str(path.resolve()), "nonce": nonce}))
    return Attempt(path, data)


def load_attempt(path, private, target):
    path = path.resolve(strict=True)
    require(path.is_relative_to(private.resolve()) and path.name == "attempt.json", "El recibo debe estar en el directorio privado del cliente")
    data = decode_json(path.read_bytes())
    require(isinstance(data, dict) and data.get("schema") == "tvbase-entry-lan09-attempt-v1", "Esquema de intento distinto")
    nonce_ok(data.get("nonce"))
    require(data.get("target") == target and data.get("apk_sha256") == APK_SHA, "Destino o APK diferentes del intento")
    require(isinstance(data.get("observations"), list) and type(data.get("launch_issued")) is bool, "Recibo incompleto")
    return Attempt(path, data)


def prepare(session=SESSION, private=PRIVATE, accepted=False, authorization_note="", factory=Transport):
    require(accepted and authorization_note.strip(), "Falta aceptación explícita y referencia a la autorización conversacional")
    target = load_session(session)
    attempt = new_attempt(private, session, target, authorization_note.strip())
    print("Intento persistido en PC: " + str(attempt.path), flush=True)
    with client_lock(attempt.path.parent):
        try:
            transport = factory(attempt, target)
            apk = preflight(transport, attempt.data["nonce"], True)
            require(attempt.data["launch_issued"] is False, "El lanzamiento ya se emitió")
            # Persist BEFORE invoking ADB. Any exception or lost reply from here
            # is indeterminate; neither this function nor status can relaunch.
            attempt.transition("launch_in_flight", launch_issued=True, installed_apk=apk)
            raw, code = transport.run("launch", entry_command(apk, attempt.data["nonce"], "launch"))
            parsed = parse_result(raw, attempt.data["nonce"], "launch", code)
            attempt.transition(parsed["result"]["state"], last_result=parsed)
            return attempt
        except BaseException as error:
            attempt.transition("indeterminate" if attempt.data["launch_issued"] else "preflight_failed",
                               last_error=type(error).__name__ + ": " + str(error))
            raise


def status(path, session=SESSION, private=PRIVATE, factory=Transport):
    target = load_session(session)
    initial = load_attempt(path, private, target)
    with client_lock(initial.path.parent):
        attempt = load_attempt(initial.path, private, target)
        require(attempt.data["launch_issued"] is True, "Este intento no emitió launch; no se consultará un nonce inexistente")
        try:
            transport = factory(attempt, target)
            apk = preflight(transport, attempt.data["nonce"], False)
            raw, code = transport.run("status", entry_command(apk, attempt.data["nonce"], "status"))
            parsed = parse_result(raw, attempt.data["nonce"], "status", code)
            attempt.transition(parsed["result"]["state"], last_result=parsed, last_status_apk=apk)
            return attempt
        except BaseException as error:
            attempt.transition("indeterminate", last_error=type(error).__name__ + ": " + str(error))
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("prepare", help="Inicia UNA preparación real de ENV/BCB; requiere autorización previa")
    p.add_argument("--session", type=Path, default=SESSION)
    p.add_argument("--accept-env-bcb-risk", action="store_true")
    p.add_argument("--authorization-note", default="")
    s = sub.add_parser("status", help="Solo observa un intento existente; jamás relanza")
    s.add_argument("--session", type=Path, default=SESSION)
    s.add_argument("--attempt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.operation == "prepare":
            attempt = prepare(args.session, accepted=args.accept_env_bcb_risk,
                              authorization_note=args.authorization_note)
        else:
            attempt = status(args.attempt, args.session)
        print(json.dumps({"attempt": str(attempt.path), "state": attempt.data["state"],
                          "result": attempt.data.get("last_result"), "automatic_reset": False}, ensure_ascii=False, indent=2))
        if attempt.data["state"] == "launched":
            print("Lanzamiento confirmado; todavía no es preparación completa. Consultá status con este recibo.")
        elif attempt.data["state"] == "prepared":
            print("Preparación verificada; la ROM aún no está instalada. El ciclo físico se decide por separado.")
        return 2 if attempt.data["state"] == "incomplete" else 0
    except (ClientError, OSError, ValueError) as error:
        print("Sin confirmación: " + str(error), file=sys.stderr)
        print("No repetir prepare ni cortar alimentación. Consultar el recibo conservado; un plazo del cliente no cancela el helper.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
