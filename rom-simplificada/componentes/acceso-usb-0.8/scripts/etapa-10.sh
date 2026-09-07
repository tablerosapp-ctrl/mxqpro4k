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
for t_i in 1 2 3 4 5 6 7 8 9; do [ "$(cat "$tv_d/etapa-$t_i.ok")" = "$tv_t" ] || tvbase_fail 'etapa ausente'; done
for t_n in autocontrol.bin identidad.txt pstore.txt espacio.txt espacio.rc espacio.estado webview.txt webview.rc webview.estado; do tvbase_verify "$t_n"; done
for t_n in log-anterior log-actual wifi bluetooth bateria; do for t_s in txt rc estado; do tvbase_verify "$t_n.$t_s"; done; done
for t_f in "$tv_d"/console-ramoops*.bin "$tv_d"/pmsg-ramoops*.bin; do [ ! -f "$t_f" ] || tvbase_verify "${t_f##*/}"; done
printf 'TVBASE POSTINTENTO 0.8: recorrido terminado y archivos comprobados.\nLas salidas pueden indicar denegacion, timeout o truncamiento; esto no acredita respuesta de todos los servicios ni causa del fallo.\nNo se reinicio ni se cambio WiFi/BT.\n' > "$tv_d/COMPLETO.txt" || tvbase_fail 'cierre'
tvbase_seal COMPLETO.txt; tvbase_done 10
