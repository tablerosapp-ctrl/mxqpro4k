for t_c in /storage/* /mnt/media_rw/*; do
 [ -d "$t_c" ] || continue
 t_part=${t_c##*/}; case "$t_part" in ''|emulated|self|*[!A-Za-z0-9_-]*) continue;; esac
 [ ${#t_part} -le 64 ] || continue
 [ -f "$t_c/TVBASE-MEDIA.txt" ] && [ ! -L "$t_c/TVBASE-MEDIA.txt" ] || continue
 [ "$(cat "$t_c/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || continue
 printf 'TVBASE_MEDIA:%s\n' "$t_c"; exit 0
done
printf 'ERROR: pendrive TVBASE ausente\n'; exit 2
