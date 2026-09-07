#!/bin/sh
# Inventario para un arranque Linux temporal. No instala ni modifica la eMMC.
# Solo escribe el informe y su archivo comprimido en /tmp.

set -u
umask 077
report_dir="/tmp/tvbox-hardware-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir "$report_dir" || exit 1

capture() {
    report_file=$1
    shift
    {
        printf 'Orden:'
        printf ' %s' "$@"
        printf '\n\n'
        if command -v "$1" >/dev/null 2>&1; then
            if command -v timeout >/dev/null 2>&1; then
                timeout 20 "$@"
            else
                "$@"
            fi
            report_status=$?
            printf '\nEstado de salida: %s\n' "$report_status"
        else
            printf 'Herramienta no disponible: %s\n' "$1"
        fi
    } > "$report_dir/$report_file" 2>&1
}

cat > "$report_dir/LEEME.txt" <<'INFO'
Inventario del Linux que esta ejecutandose, para preparar una base Android.
No demuestra que los componentes propietarios de Android sean compatibles.
El DTB describe la configuracion de arranque elegida; no certifica por si solo
el modelo del silicio. Contrastar con identificadores y datos fisicos de placa.
Este script no instala paquetes, no monta particiones ni modifica el arranque.
No lee el contenido del Android instalado. El informe permanece en /tmp y se
perdera al apagar; copiarlo a la PC antes. Puede incluir IP, MAC e identificadores
de hardware; no se envia automaticamente a ningun servidor.
INFO

capture sistema.txt uname -a
capture cpu.txt cat /proc/cpuinfo
capture memoria.txt cat /proc/meminfo
capture arranque-linux.txt cat /proc/cmdline
capture distribucion.txt cat /etc/os-release
capture bloques.txt lsblk -o NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,RO
capture montajes.txt findmnt -r
capture modulos.txt lsmod
capture red-direcciones.txt ip -brief address
capture red-enlaces.txt ip -details link
capture usb.txt lsusb
capture usb-topologia.txt lsusb -t
capture dispositivos-entrada.txt cat /proc/bus/input/devices
capture audio.txt cat /proc/asound/cards
capture kernel-linux.txt dmesg
capture codecs-linux.txt v4l2-ctl --list-devices

{
    for dt_root in /sys/firmware/devicetree/base /proc/device-tree; do
        [ -d "$dt_root" ] || continue
        printf 'Arbol utilizado: %s\n' "$dt_root"
        for field in model compatible amlogic-dt-id; do
            [ -r "$dt_root/$field" ] || continue
            printf '\n%s:\n' "$field"
            tr '\000' '\n' < "$dt_root/$field"
        done
        break
    done
    for soc in /sys/devices/soc0 /sys/devices/system/soc/soc0; do
        [ -d "$soc" ] || continue
        for field in family machine soc_id revision; do
            [ -r "$soc/$field" ] || continue
            printf '\n%s: ' "$soc/$field"
            cat "$soc/$field"
        done
    done
} > "$report_dir/identidad.txt" 2>&1

{
    for bus in platform mmc sdio usb i2c spi; do
        printf '\nBus %s\n' "$bus"
        for dev in /sys/bus/"$bus"/devices/*; do
            [ -e "$dev" ] || continue
            printf '\nDispositivo: %s\n' "$dev"
            if [ -L "$dev/driver" ]; then
                printf 'Driver: '
                readlink "$dev/driver"
            fi
            for field in modalias vendor device idVendor idProduct name type manfid oemid; do
                [ -r "$dev/$field" ] || continue
                printf '%s: ' "$field"
                cat "$dev/$field"
                printf '\n'
            done
        done
    done
} > "$report_dir/dispositivos-y-drivers.txt" 2>&1

{
    ls -l /dev/dri /dev/video* /dev/am* /dev/codec* 2>/dev/null
    for connector in /sys/class/drm/card*-*; do
        [ -d "$connector" ] || continue
        printf '\nConector: %s\n' "$connector"
        for field in status enabled modes; do
            [ -r "$connector/$field" ] || continue
            printf '%s:\n' "$field"
            cat "$connector/$field"
        done
    done
} > "$report_dir/video-linux.txt" 2>&1

{
    for zone in /sys/class/thermal/thermal_zone*; do
        [ -d "$zone" ] || continue
        printf '\n%s\n' "$zone"
        for field in type temp; do
            [ -r "$zone/$field" ] || continue
            printf '%s: ' "$field"
            cat "$zone/$field"
        done
    done
} > "$report_dir/temperatura.txt" 2>&1

if command -v dtc >/dev/null 2>&1 && [ -d /sys/firmware/devicetree/base ]; then
    capture arbol-linux.txt dtc -I fs -O dts /sys/firmware/devicetree/base
fi

printf 'Informe guardado en: %s\n' "$report_dir"
if command -v tar >/dev/null 2>&1; then
    if tar -czf "$report_dir.tar.gz" -C /tmp "${report_dir##*/}"; then
        printf 'Archivo para copiar a la PC: %s.tar.gz\n' "$report_dir"
    fi
fi
printf 'Copiar el informe antes de apagar: /tmp puede estar en RAM.\n'
