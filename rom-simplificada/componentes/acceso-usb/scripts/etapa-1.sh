set -C
fail() { printf 'ERROR: %s\n' "$1"; exit 9; }
tv_b=${tv_d%/*}
[ -d "$tv_d" ] && [ ! -L "$tv_d" ] || fail 'carpeta original ausente'
[ "$(cat "$tv_b/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || fail 'cambio el USB'
[ "$(cat "$tv_d/INICIO.txt" 2>/dev/null)" = "$tv_t" ] || fail 'carpeta incorrecta'
hash() {
 tv_h=$(sha256sum "$1") || fail 'SHA256 fallo'
 tv_h=${tv_h%% *}
 [ ${#tv_h} = 64 ] || fail 'SHA256 incompleto'
 case "$tv_h" in *[!0-9a-f]*) fail 'SHA256 invalido';; esac
 printf '%s' "$tv_h"
}
seal() {
 tv_f="$tv_d/$1"
 [ "$(tail -n 1 "$tv_f")" = "FIN-$tv_t" ] || fail 'informe truncado'
 sha256sum "$tv_f" > "$tv_f.sha256" || fail 'registro SHA fallo'
 sync || fail 'sync fallo'
 sha256sum -c "$tv_f.sha256" >/dev/null 2>&1 || fail 'lectura SHA distinta'
}
done_step() {
 printf '%s\n' "$tv_t" > "$tv_d/etapa-$1.ok" || fail 'etapa incompleta'
 sync || fail 'sync fallo'
 [ "$(cat "$tv_d/etapa-$1.ok")" = "$tv_t" ] || fail 'lectura etapa distinta'
 printf 'TVBASE_OK:%s:%s\n' "$1" "$tv_t"
}
{
 printf 'TVBASE EVIDENCIA 0.5 - ARRANQUE ACTUAL\n'; date; id
 printf '\nBOOT_ID Y UPTIME\n'; cat /proc/sys/kernel/random/boot_id /proc/uptime
 printf '\nPLACA/KERNEL/CMDLINE\n'; cat /proc/device-tree/amlogic-dt-id; printf '\n'; cat /proc/version /proc/cmdline
 printf '\nPROPIEDADES CONCRETAS DE ARRANQUE\n'
 for tv_k in ro.build.display.id ro.build.version.sdk ro.product.device ro.product.board ro.bootloader ro.hardware ro.bootmode ro.boot.bootreason ro.boot.reboot_mode sys.boot.reason sys.boot.reason.last persist.sys.boot.reason persist.sys.boot.reason.history sys.shutdown.requested sys.powerctl sys.boot_completed ro.runtime.firstboot ro.boot.verifiedbootstate init.svc.adbd; do printf '%s=' "$tv_k"; getprop "$tv_k"; done
 printf '\nPARTICIONES\n'; cat /proc/partitions
 printf '\nTABLA DE ALIASES, HASTA 64 KIB POR DIRECTORIO\n'
 for tv_p in /dev/block /dev/block/by-name /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name; do [ -d "$tv_p" ] || continue; printf '\n%s\n' "$tv_p"; ls -l "$tv_p" 2>&1 | head -c 65536; printf '\n'; done
 printf '\nMONTAJES, HASTA 32 KIB\n'; head -c 32768 /proc/mounts
 printf '\nPERMISOS RECOVERY Y PSTORE\n'; ls -ld /cache /cache/recovery /sys/fs/pstore; ls -l /sys/fs/pstore
 printf '\nCOMANDO RECOVERY, SI ES LEGIBLE\n'; head -c 4096 /cache/recovery/command
 printf '\nDMESG ACTUAL, ULTIMOS 64 KIB; DENEGACION PERMITIDA\n'; dmesg 2>&1 | tail -c 65536
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/arranque.txt" 2>&1 || fail 'escritura arranque fallo'
seal arranque.txt
done_step 1
