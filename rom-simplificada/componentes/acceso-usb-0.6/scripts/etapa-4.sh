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
for t_i in 1 2 3; do [ "$(cat "$tv_d/etapa-$t_i.ok" 2>/dev/null)" = "$tv_t" ] || tvbase_fail 'falta etapa'; done
sync || tvbase_fail 'sync final fallo'
for t_n in autocontrol certificados pm-path actualizador identidad init-y-fstab; do
 [ -f "$tv_d/$t_n.txt" ] && [ -f "$tv_d/$t_n.txt.sha256" ] || tvbase_fail 'falta informe obligatorio'
 [ "$(tail -n 1 "$tv_d/$t_n.txt")" = "FIN-$tv_t" ] || tvbase_fail 'informe obligatorio incompleto'
 tvbase_verify "$t_n.txt"
done
for t_n in autocontrol.bin otacerts.zip OTAUpgrade.apk; do
 [ -s "$tv_d/$t_n" ] || tvbase_fail 'falta binario obligatorio'
 tvbase_verify "$t_n"
done
{
 printf 'TVBASE EVIDENCIA 0.6 COMPLETA\n'; date
 printf 'token=%s\ncarpeta=%s\n' "$tv_t" "$tv_d"
 printf 'Autocontrol SHA correcto; OTAUpgrade.apk y otacerts.zip con hash original/copia. Configuracion pertinente y lecturas denegadas conservadas. No se copio GMS ni se reinicio el TV.\n'
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/COMPLETO.txt" || tvbase_fail 'cierre incompleto'
tvbase_seal COMPLETO.txt
tvbase_done 4
