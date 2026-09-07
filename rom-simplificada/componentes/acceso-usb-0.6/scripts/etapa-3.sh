set -C
tvbase_fail() { printf 'ERROR: %s\n' "$1"; exit 9; }
t_b=${tv_d%/*}
[ -d "$tv_d" ] && [ ! -L "$tv_d" ] || tvbase_fail 'carpeta original ausente'
[ "$(cat "$t_b/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || tvbase_fail 'cambio el USB'
[ "$(cat "$tv_d/INICIO.txt" 2>/dev/null)" = "$tv_t" ] || tvbase_fail 'carpeta incorrecta'
tvbase_hex() {
 [ ${#1} = 64 ] || return 1
 case "$1" in *[!0-9a-f]*) return 1;; esac
}
tvbase_sha() {
 t_raw=$(/system/bin/toybox sha256sum "$1") || return 1
 t_value=${t_raw%% *}
 tvbase_hex "$t_value" || return 1
 printf '%s' "$t_value"
}
tvbase_verify() {
 t_file="$tv_d/$1"
 t_line=$(cat "$t_file.sha256") || tvbase_fail 'falta registro SHA'
 t_expected=${t_line%% *}
 tvbase_hex "$t_expected" || tvbase_fail 'SHA guardado invalido'
 [ "${t_line#*  }" = "$t_file" ] || tvbase_fail 'ruta del SHA distinta'
 t_read=$(tvbase_sha "$t_file") || tvbase_fail 'SHA de lectura fallo'
 tvbase_hex "$t_read" || tvbase_fail 'SHA leido invalido'
 [ "$t_expected" = "$t_read" ] || tvbase_fail 'SHA de lectura distinto'
}
tvbase_rec() {
 tvbase_hex "$2" || tvbase_fail 'no se registra SHA invalido'
 printf '%s  %s\n' "$2" "$tv_d/$1" > "$tv_d/$1.sha256" || tvbase_fail 'registro SHA fallo'
 sync || tvbase_fail 'sync fallo'
 tvbase_verify "$1"
}
tvbase_seal() {
 [ "$(tail -n 1 "$tv_d/$1")" = "FIN-$tv_t" ] || tvbase_fail 'informe truncado'
 t_sum=$(tvbase_sha "$tv_d/$1") || tvbase_fail 'SHA informe fallo'
 tvbase_hex "$t_sum" || tvbase_fail 'SHA informe invalido'
 tvbase_rec "$1" "$t_sum"
}
tvbase_done() {
 printf '%s\n' "$tv_t" > "$tv_d/etapa-$1.ok" || tvbase_fail 'etapa incompleta'
 sync || tvbase_fail 'sync fallo'
 [ "$(cat "$tv_d/etapa-$1.ok")" = "$tv_t" ] || tvbase_fail 'etapa distinta'
 printf 'TVBASE_OK:%s:%s\n' "$1" "$tv_t"
}
{
 printf 'TVBASE COMPLEMENTO 0.6; DATOS ACTUALES\n'; date; id
 cat /proc/device-tree/amlogic-dt-id; printf '\n'; cat /proc/sys/kernel/random/boot_id /proc/uptime
 for t_key in ro.build.display.id ro.build.version.sdk ro.boot.bootreason sys.boot.reason; do printf '%s=' "$t_key"; getprop "$t_key"; done
 printf 'FIN-%s\n' "$tv_t"
} > "$tv_d/identidad.txt" 2>&1 || tvbase_fail 'identidad incompleta'
tvbase_seal identidad.txt
{
 printf 'INIT/FSTAB LEGIBLES; NO SE MODIFICAN\n'
 t_i=0
 for t_src in /init*.rc /vendor/etc/init/*.rc /vendor/etc/init/hw/*.rc /system/etc/init/*.rc /odm/etc/init/*.rc /odm/etc/init/hw/*.rc /product/etc/init/*.rc; do
  [ -f "$t_src" ] || continue; t_i=$((t_i+1)); [ "$t_i" -le 120 ] || { printf '\nLIMITE: 120 init\n'; break; }
  printf '\nINIT %s; lineas pertinentes hasta8KiB\n' "$t_src"
  grep -n -i -E 'reboot|powerctl|bootmode|bootreason|boot_reason|recovery|otaupgrade|factory_reset|instaboot|boot_completed' "$t_src" 2>&1 | head -c 8192
 done
 t_i=0
 for t_src in /fstab.* /vendor/etc/fstab* /odm/etc/fstab* /system/etc/fstab*; do
  [ -f "$t_src" ] || continue; t_i=$((t_i+1)); [ "$t_i" -le 16 ] || { printf '\nLIMITE: 16 fstab\n'; break; }
  printf '\nFSTAB %s; hasta32KiB\n' "$t_src"; head -c 32768 "$t_src"
 done
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/init-y-fstab.txt" 2>&1 || tvbase_fail 'configuracion incompleta'
tvbase_seal init-y-fstab.txt
tvbase_done 3
