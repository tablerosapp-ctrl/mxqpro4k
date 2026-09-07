set -C
tvbase_fail(){ printf 'ERROR: %s\n' "$1"; exit 9; }
tvbase_hex(){ [ ${#1} = 64 ] || return 1; case "$1" in *[!0-9a-f]*) return 1;; esac; }
tvbase_sha(){ t_h=$(/system/bin/toybox timeout -s KILL 8 /system/bin/toybox sha256sum "$1") || return 1; t_h=${t_h%% *}; tvbase_hex "$t_h" || return 1; printf %s "$t_h"; }
tvbase_verify(){ t_e=$(cat "$tv_d/$1.sha256") || tvbase_fail 'falta SHA'; tvbase_hex "$t_e" || tvbase_fail 'SHA guardado invalido'; t_h=$(tvbase_sha "$tv_d/$1") || tvbase_fail 'lectura SHA'; tvbase_hex "$t_h" && [ "$t_e" = "$t_h" ] || tvbase_fail 'SHA distinto'; }
tvbase_seal(){ t_h=$(tvbase_sha "$tv_d/$1") || tvbase_fail 'SHA fallo'; tvbase_hex "$t_h" || tvbase_fail 'SHA vacio'; printf '%s\n' "$t_h" > "$tv_d/$1.sha256" || tvbase_fail 'escritura SHA'; tvbase_verify "$1"; }
[ "$(id -u)" = 2000 ] && [ "$(getprop ro.build.version.sdk)" = 28 ] && [ "$(tr -d '\000' < /proc/device-tree/amlogic-dt-id)" = gxlx2_p291_1g ] || tvbase_fail 'perfil distinto'
t_b=${tv_d%/*}
[ -d "$tv_d" ] && [ ! -L "$tv_d" ] && [ ! -L "$tv_d/INICIO.txt" ] && [ ! -L "$t_b/TVBASE-MEDIA.txt" ] && [ "$(cat "$tv_d/INICIO.txt")" = "$tv_t" ] && [ "$(cat "$t_b/TVBASE-MEDIA.txt")" = TVBASE-P291-20260906-4dc82786 ] || tvbase_fail 'USB/carpeta distinto'
tvbase_done(){ printf '%s\n' "$tv_t" > "$tv_d/etapa-$1.ok" || tvbase_fail 'etapa'; [ "$(cat "$tv_d/etapa-$1.ok")" = "$tv_t" ] || tvbase_fail 'lectura etapa'; printf 'TVBASE_OK:%s:%s\n' "$1" "$tv_t"; }
t_i=0
printf 'PSTORE; solo console/pmsg; hasta cuatro archivos, 2MiB cada uno\n' > "$tv_d/pstore.txt" || tvbase_fail 'informe'
for t_src in /sys/fs/pstore/console-ramoops* /sys/fs/pstore/pmsg-ramoops*; do
 [ -e "$t_src" ] || continue
 t_i=$((t_i+1)); [ "$t_i" -le 4 ] || { printf 'LIMITE_ARCHIVOS\n' >> "$tv_d/pstore.txt"; break; }
 t_n=${t_src##*/}; case "$t_n" in *[!A-Za-z0-9_-]*) tvbase_fail 'nombre pstore';; esac
 printf 'ORIGEN %s\n' "$t_src" >> "$tv_d/pstore.txt" || tvbase_fail 'informe'
 if [ ! -r "$t_src" ] || [ ! -f "$t_src" ] || [ -L "$t_src" ]; then printf 'NO_LEGIBLE\n' >> "$tv_d/pstore.txt"; continue; fi
 t_sz=$(stat -c %s "$t_src") || tvbase_fail 'stat pstore'
 case "$t_sz" in ''|*[!0-9]*) tvbase_fail 'tamano pstore';; esac
 if [ "$t_sz" -le 0 ] || [ "$t_sz" -gt 2097152 ]; then printf 'TAMANO_NO_ADMITIDO %s\n' "$t_sz" >> "$tv_d/pstore.txt"; continue; fi
 t_before=$(tvbase_sha "$t_src") || tvbase_fail 'SHA origen pstore'; tvbase_hex "$t_before" || tvbase_fail 'SHA origen vacio'
 /system/bin/toybox timeout -s KILL 8 /system/bin/toybox head -c 2097153 "$t_src" > "$tv_d/$t_n.bin" || tvbase_fail 'copia pstore'
 t_after=$(tvbase_sha "$t_src") || tvbase_fail 'SHA posterior pstore'; tvbase_hex "$t_after" || tvbase_fail 'SHA posterior vacio'
 [ "$t_before" = "$t_after" ] && [ "$(stat -c %s "$tv_d/$t_n.bin")" = "$t_sz" ] || tvbase_fail 'origen cambio'
 tvbase_seal "$t_n.bin"
 [ "$(cat "$tv_d/$t_n.bin.sha256")" = "$t_before" ] || tvbase_fail 'copia pstore distinta'
 printf 'COPIADO %s bytes=%s sha256=%s\n' "$t_n.bin" "$t_sz" "$t_before" >> "$tv_d/pstore.txt" || tvbase_fail 'informe'
done
printf 'entradas_encontradas=%s\n' "$t_i" >> "$tv_d/pstore.txt" || tvbase_fail 'informe final'
tvbase_seal pstore.txt; tvbase_done 2
