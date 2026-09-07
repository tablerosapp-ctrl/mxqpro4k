set -C
[ "$(id -u)" = 2000 ] && [ "$(getprop ro.build.version.sdk)" = 28 ] && [ "$(tr -d '\000' < /proc/device-tree/amlogic-dt-id)" = gxlx2_p291_1g ] || exit 2
/system/bin/toybox timeout -s KILL 2 /system/bin/toybox true || exit 3
/system/bin/toybox timeout -s KILL 1 /system/bin/toybox sleep 3 >/dev/null 2>&1
[ "$?" -ge 128 ] || { printf 'ERROR: timeout no comprobado\n'; exit 3; }
t_b=
for t_c in /storage/* /mnt/media_rw/*; do
 [ -d "$t_c" ] || continue
 t_part=${t_c##*/}; case "$t_part" in ''|emulated|self|*[!A-Za-z0-9_-]*) continue;; esac
 [ ${#t_part} -le 64 ] && [ ! -L "$t_c/TVBASE-MEDIA.txt" ] || continue
 [ "$(cat "$t_c/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || continue
 t_b=$t_c; break
done
[ -n "$t_b" ] || { printf 'ERROR: USB TVBASE ausente\n'; exit 2; }
tv_d="$t_b/TVBASE-postintento-$tv_t"
mkdir "$tv_d" || exit 3
printf '%s\n' "$tv_t" > "$tv_d/INICIO.txt" || exit 4
[ "$(cat "$tv_d/INICIO.txt")" = "$tv_t" ] || exit 5
printf 'TVBASE_READY:%s\n' "$tv_d"
