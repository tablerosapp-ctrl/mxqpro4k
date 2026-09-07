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
 cmd package resolve-activity --brief -a android.settings.SYSTEM_UPDATE_SETTINGS
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/resolucion.txt" 2>&1 || fail 'resolucion incompleta'
seal resolucion.txt
package_ok() {
 case "$1" in ''|*[!A-Za-z0-9_.]*|.*|*.|*..*|[0-9]*) return 1;; esac
}
tv_count=0; tv_pkg=; tv_component=; tv_rejected=0
while IFS= read -r tv_line; do
 case "$tv_line" in */*) ;; *) continue;; esac
 tv_p=${tv_line%%/*}; tv_c=${tv_line#*/}
 if ! package_ok "$tv_p"; then tv_rejected=$((tv_rejected+1)); continue; fi
 case "$tv_c" in ''|*[!A-Za-z0-9_.$]*|*..*) tv_rejected=$((tv_rejected+1)); continue;; esac
 tv_count=$((tv_count+1)); tv_pkg=$tv_p; tv_component=$tv_line
done < "$tv_d/resolucion.txt"
tv_selected=
if [ "$tv_count" = 1 ] && [ "$tv_rejected" = 0 ] && [ "$tv_pkg" != android ]; then tv_selected=$tv_pkg; fi
{
 [ -z "$tv_selected" ] || printf '%s\n' "$tv_selected"
 [ "$tv_selected" = com.droidlogic.otaupgrade ] || printf 'com.droidlogic.otaupgrade\n'
 printf 'FIN-%s\n' "$tv_t"
} > "$tv_d/paquetes.txt" || fail 'lista de paquetes fallo'
seal paquetes.txt
{
 printf 'CANDIDATOS; NO SE EJECUTAN. La Activity resuelta puede ser solo una pantalla de Ajustes, no el flasheador.\n'
 printf 'componentes_validos=%s\nlineas_rechazadas=%s\ncomponente=%s\npaquete_resuelto_seleccionado=%s\n' "$tv_count" "$tv_rejected" "$tv_component" "$tv_selected"
 if [ -z "$tv_selected" ]; then printf 'SIN_RESOLUCION_UNIVOCA: ausente, ambigua, invalida o resolver android; se conserva candidato fijo.\n'; fi
 while IFS= read -r tv_p; do
  [ "$tv_p" = "FIN-$tv_t" ] && continue
  package_ok "$tv_p" || fail 'paquete invalido'
  printf '\nPAQUETE %s; DUMPSYS HASTA 96 KIB\n' "$tv_p"
  dumpsys -t 10 package "$tv_p" 2>&1 | head -c 98304
 done < "$tv_d/paquetes.txt"
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/actualizador.txt" 2>&1 || fail 'informe actualizador fallo'
seal actualizador.txt
{
 while IFS= read -r tv_p; do
  [ "$tv_p" = "FIN-$tv_t" ] && continue
  package_ok "$tv_p" || fail 'paquete invalido'
  pm path "$tv_p"
 done < "$tv_d/paquetes.txt"
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/pm-path.txt" 2>&1 || fail 'pm path incompleto'
seal pm-path.txt
done_step 3
