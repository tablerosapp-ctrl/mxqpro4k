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
copy_one() {
 tv_s=$1; tv_n=$2; tv_max=$3
 printf '\nORIGEN %s\n' "$tv_s" >> "$tv_log" || fail 'registro fallo'
 tv_skip=
 if [ -L "$tv_s" ]; then tv_skip=ENLACE; elif [ ! -e "$tv_s" ]; then tv_skip=AUSENTE_O_NO_ACCESIBLE; elif [ ! -f "$tv_s" ]; then tv_skip=NO_REGULAR; elif [ ! -r "$tv_s" ]; then tv_skip=LECTURA_DENEGADA; fi
 if [ -n "$tv_skip" ]; then printf 'NO_COPIADO: %s\n' "$tv_skip" >> "$tv_log" || fail 'registro fallo'; return; fi
 tv_len=$(stat -c %s "$tv_s") || fail 'stat fallo'
 case "$tv_len" in ''|*[!0-9]*) fail 'longitud invalida';; esac
 if [ "$tv_len" -gt "$tv_max" ]; then printf 'NO_COPIADO: %s bytes exceden limite %s\n' "$tv_len" "$tv_max" >> "$tv_log" || fail 'registro fallo'; return; fi
 tv_before=$(hash "$tv_s") || fail 'SHA original fallo'
 head -c "$((tv_max+1))" "$tv_s" > "$tv_d/$tv_n" || fail 'copia binaria fallo'
 sync || fail 'sync copia fallo'
 tv_copylen=$(stat -c %s "$tv_d/$tv_n") || fail 'stat copia fallo'
 tv_after=$(hash "$tv_s") || fail 'SHA original fallo'
 tv_copyhash=$(hash "$tv_d/$tv_n") || fail 'SHA copia fallo'
 [ "$tv_len" = "$tv_copylen" ] && [ "$tv_before" = "$tv_after" ] && [ "$tv_before" = "$tv_copyhash" ] || fail 'copia distinta o fuente cambio'
 printf 'COPIADO %s\nbytes_original=%s\nbytes_copia=%s\nsha256_original=%s\nsha256_copia=%s\n' "$tv_n" "$tv_len" "$tv_copylen" "$tv_before" "$tv_copyhash" >> "$tv_log" || fail 'registro fallo'
 printf '%s  %s\n' "$tv_copyhash" "$tv_d/$tv_n" > "$tv_d/$tv_n.sha256" || fail 'registro SHA fallo'
}
tv_log="$tv_d/pstore.txt"
printf 'PSTORE: copias binarias completas; limite 2 MiB por archivo\n' > "$tv_log" || fail 'informe fallo'
tv_i=0
for tv_s in /sys/fs/pstore/console-ramoops* /sys/fs/pstore/ftrace-ramoops* /sys/fs/pstore/dmesg-ramoops*; do
 tv_i=$((tv_i+1)); [ "$tv_i" -le 16 ] || fail 'mas de 16 registros pstore'
 copy_one "$tv_s" "pstore-$tv_i.bin" 2097152
done
printf '\nFIN-%s\n' "$tv_t" >> "$tv_log" || fail 'pstore incompleto'
seal pstore.txt
done_step 2
