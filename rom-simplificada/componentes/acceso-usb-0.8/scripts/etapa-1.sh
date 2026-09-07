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
printf abc > "$tv_d/autocontrol.bin" || tvbase_fail 'autocontrol'
t_h=$(tvbase_sha "$tv_d/autocontrol.bin") || tvbase_fail 'SHA autocontrol'
tvbase_hex "$t_h" && [ "$t_h" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad ] || tvbase_fail 'SHA autocontrol incorrecto'
tvbase_seal autocontrol.bin
{
 printf 'TVBASE POSTINTENTO 0.8; no reinicia; consultas con plazo\n'; id; cat /proc/uptime; cat /proc/sys/kernel/random/boot_id
 for t_p in ro.build.version.sdk ro.build.display.id ro.boot.bootreason sys.boot.reason persist.sys.boot.reason sys.shutdown.requested init.svc.uncrypt init.svc.adbd init.svc.logd; do printf '%s=' "$t_p"; getprop "$t_p"; done
} > "$tv_d/identidad.txt" 2>&1 || tvbase_fail 'identidad'
tvbase_seal identidad.txt
tvbase_done 1
