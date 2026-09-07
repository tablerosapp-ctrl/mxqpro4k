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
for tv_i in 1 2 3 4 5; do [ "$(cat "$tv_d/etapa-$tv_i.ok" 2>/dev/null)" = "$tv_t" ] || fail 'falta una etapa'; done
for tv_n in arranque pstore resolucion paquetes actualizador pm-path apk-y-certificados init-y-fstab; do
 [ -f "$tv_d/$tv_n.txt" ] && [ -f "$tv_d/$tv_n.txt.sha256" ] || fail 'falta informe obligatorio'
 [ "$(tail -n 1 "$tv_d/$tv_n.txt")" = "FIN-$tv_t" ] || fail 'informe obligatorio incompleto'
done
sync || fail 'sync final fallo'
tv_i=0
for tv_s in "$tv_d"/*.sha256; do
 [ -f "$tv_s" ] || fail 'faltan hashes'; tv_i=$((tv_i+1))
 sha256sum -c "$tv_s" >/dev/null 2>&1 || fail 'verificacion SHA256 fallo'
done
[ "$tv_i" -ge 8 ] || fail 'faltan informes'
{
 printf 'TVBASE EVIDENCIA 0.5 COMPLETA\n'; date
 printf 'token=%s\ncarpeta=%s\narchivos_con_SHA256=%s\n' "$tv_t" "$tv_d" "$tv_i"
 printf 'Lecturas del TV; salidas en este USB. Sin reiniciar ni iniciar actualizador. Las denegaciones quedan registradas.\n'
 printf '\nINVENTARIO\n'; ls -l "$tv_d"
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/COMPLETO.txt" 2>&1 || fail 'resumen incompleto'
seal COMPLETO.txt
done_step 6
