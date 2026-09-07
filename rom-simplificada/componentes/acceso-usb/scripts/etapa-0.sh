set -C
tv_b=
for tv_c in /storage/* /mnt/media_rw/*; do
 [ -d "$tv_c" ] || continue
 [ "$(cat "$tv_c/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || continue
 tv_part=${tv_c##*/}
 case "$tv_part" in ''|*[!A-Za-z0-9_-]*) continue;; esac
 tv_b=$tv_c; break
done
[ -n "$tv_b" ] || { printf 'ERROR: pendrive TVBASE ausente\n'; exit 2; }
tv_d="$tv_b/TVBASE-evidencia-$tv_t"
mkdir "$tv_d" || { printf 'ERROR: no se creo carpeta nueva; no se busco otro destino\n'; exit 3; }
printf '%s\n' "$tv_t" > "$tv_d/INICIO.txt" || exit 4
sync || { printf 'ERROR: sync inicial fallo\n'; exit 5; }
[ "$(cat "$tv_d/INICIO.txt")" = "$tv_t" ] || exit 6
printf 'TVBASE_READY:%s\n' "$tv_d"
