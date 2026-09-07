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
tvbase_copy() {
 t_src=$1; t_name=$2; t_max=$3
 printf '\nORIGEN %s\n' "$t_src" >> "$t_log" || tvbase_fail 'registro fallo'
 [ -f "$t_src" ] && [ -r "$t_src" ] && [ ! -L "$t_src" ] || tvbase_fail 'original no legible'
 t_size=$(stat -c %s "$t_src") || tvbase_fail 'stat fallo'
 case "$t_size" in ''|*[!0-9]*) tvbase_fail 'longitud invalida';; esac
 [ "$t_size" -gt 0 ] && [ "$t_size" -le "$t_max" ] || tvbase_fail 'tamano fuera de limite'
 t_before=$(tvbase_sha "$t_src") || tvbase_fail 'SHA original fallo'
 tvbase_hex "$t_before" || tvbase_fail 'SHA original invalido'
 head -c "$((t_max+1))" "$t_src" > "$tv_d/$t_name" || tvbase_fail 'copia fallo'
 sync || tvbase_fail 'sync copia fallo'
 t_size2=$(stat -c %s "$tv_d/$t_name") || tvbase_fail 'stat copia fallo'
 t_after=$(tvbase_sha "$t_src") || tvbase_fail 'segunda lectura fallo'
 tvbase_hex "$t_after" || tvbase_fail 'SHA posterior invalido'
 [ "$t_size" = "$t_size2" ] && [ "$t_before" = "$t_after" ] || tvbase_fail 'fuente o tamano cambio'
 tvbase_rec "$t_name" "$t_before"
 printf 'COPIADO %s\nbytes_original=%s\nbytes_copia=%s\nsha256_original=%s\nsha256_copia=%s\n' "$t_name" "$t_size" "$t_size2" "$t_before" "$t_before" >> "$t_log" || tvbase_fail 'registro copia fallo'
}
t_pm=$(/system/bin/pm path com.droidlogic.otaupgrade 2>&1)
printf '%s\nFIN-%s\n' "$t_pm" "$tv_t" > "$tv_d/pm-path.txt" || tvbase_fail 'informe pm fallo'
tvbase_seal pm-path.txt
[ "$t_pm" = package:/product/app/OTAUpgrade/OTAUpgrade.apk ] || tvbase_fail 'OTA no coincide con ruta acreditada; ver pm-path.txt'
t_log="$tv_d/actualizador.txt"
printf 'Paquete com.droidlogic.otaupgrade, ruta acreditada P291. No se ejecuta.\n' > "$t_log" || tvbase_fail 'informe fallo'
tvbase_copy /product/app/OTAUpgrade/OTAUpgrade.apk OTAUpgrade.apk 33554432
printf 'FIN-%s\n' "$tv_t" >> "$t_log" || tvbase_fail 'informe fallo'
tvbase_seal actualizador.txt
tvbase_done 2
