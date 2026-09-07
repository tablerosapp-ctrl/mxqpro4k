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
 printf 'CONFIGURACION LEGIBLE; NO SE MODIFICA\n'
 tv_i=0
 for tv_s in /init*.rc /vendor/etc/init/*.rc /vendor/etc/init/hw/*.rc /system/etc/init/*.rc /odm/etc/init/*.rc /odm/etc/init/hw/*.rc /product/etc/init/*.rc; do
  [ -f "$tv_s" ] || continue; tv_i=$((tv_i+1)); [ "$tv_i" -le 120 ] || { printf '\nLIMITE: 120 archivos init\n'; break; }
  printf '\nINIT %s (lineas pertinentes, hasta 8 KiB)\n' "$tv_s"
  grep -n -i -E 'reboot|powerctl|bootmode|bootreason|boot_reason|recovery|otaupgrade|factory_reset|instaboot|boot_completed' "$tv_s" 2>&1 | head -c 8192
 done
 tv_i=0
 for tv_s in /fstab.* /vendor/etc/fstab* /odm/etc/fstab* /system/etc/fstab*; do
  [ -f "$tv_s" ] || continue; tv_i=$((tv_i+1)); [ "$tv_i" -le 16 ] || { printf '\nLIMITE: 16 fstab\n'; break; }
  printf '\nFSTAB %s (hasta 32 KiB)\n' "$tv_s"; head -c 32768 "$tv_s"
 done
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/init-y-fstab.txt" 2>&1 || fail 'informe configuracion fallo'
seal init-y-fstab.txt
done_step 5
