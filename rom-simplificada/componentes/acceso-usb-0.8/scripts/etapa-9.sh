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
tvbase_run(){
 tv_n=$1; tv_s=$2; tv_m=$3; shift 3
 printf 'inicio_uptime=%s\n' "$(cat /proc/uptime)" > "$tv_d/$tv_n.estado" || tvbase_fail 'estado'
 ( /system/bin/toybox timeout -s KILL "$tv_s" "$@"; printf '%s\n' "$?" > "$tv_d/$tv_n.rc" ) 2>&1 | /system/bin/toybox head -c "$((tv_m+1))" > "$tv_d/$tv_n.txt" || tvbase_fail 'salida'
 t_rc=$(cat "$tv_d/$tv_n.rc") || tvbase_fail 'sin codigo de salida'
 case "$t_rc" in ''|*[!0-9]*) tvbase_fail 'codigo invalido';; esac
 t_sz=$(stat -c %s "$tv_d/$tv_n.txt") || tvbase_fail 'tamano'
 t_cut=no; [ "$t_sz" -le "$tv_m" ] || t_cut=si
 printf 'fin_uptime=%s\nexit=%s\nbytes=%s\ntruncado=%s\n' "$(cat /proc/uptime)" "$t_rc" "$t_sz" "$t_cut" >> "$tv_d/$tv_n.estado" || tvbase_fail 'estado final'
 tvbase_seal "$tv_n.txt"; tvbase_seal "$tv_n.rc"; tvbase_seal "$tv_n.estado"
}
tvbase_run webview 8 32768 /system/bin/dumpsys -t 5 webviewupdate
tvbase_done 9
