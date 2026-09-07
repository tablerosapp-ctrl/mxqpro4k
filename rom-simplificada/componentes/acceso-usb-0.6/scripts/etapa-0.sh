set -C
t_b=
for t_c in /storage/* /mnt/media_rw/*; do
 [ -d "$t_c" ] || continue
 [ "$(cat "$t_c/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || continue
 t_part=${t_c##*/}
 case "$t_part" in ''|*[!A-Za-z0-9_-]*) continue;; esac
 t_b=$t_c; break
done
[ -n "$t_b" ] || { printf 'ERROR: pendrive TVBASE ausente\n'; exit 2; }
tv_d="$t_b/TVBASE-evidencia-$tv_t"
mkdir "$tv_d" || { printf 'ERROR: carpeta nueva no creada; no se cambia destino\n'; exit 3; }
printf '%s\n' "$tv_t" > "$tv_d/INICIO.txt" || exit 4
sync || exit 5
[ "$(cat "$tv_d/INICIO.txt")" = "$tv_t" ] || exit 6
printf 'TVBASE_READY:%s\n' "$tv_d"
