tvbase_fail() { printf 'ERROR: %s\n' "$1"; exit 9; }
tvbase_hex() { [ ${#1} = 64 ] || return 1; case "$1" in *[!0-9a-f]*) return 1;; esac; }
tvbase_sha() {
 t_raw=$(/system/bin/toybox sha256sum "$@") || return 1
 t_value=${t_raw%% *}; tvbase_hex "$t_value" || return 1; printf '%s' "$t_value"
}
tvbase_media() {
 [ -d "$tv_d" ] && [ -f "$tv_d/TVBASE-MEDIA.txt" ] && [ ! -L "$tv_d/TVBASE-MEDIA.txt" ] || tvbase_fail 'pendrive ausente'
 [ "$(cat "$tv_d/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || tvbase_fail 'marcador USB distinto'
}
tvbase_profile() {
 [ "$(id -u)" = 2000 ] || tvbase_fail 'UID distinto de shell'
 [ "$(getprop ro.build.version.sdk)" = 28 ] || tvbase_fail 'Android distinto'
 [ "$(tr -d '\000' < /proc/device-tree/amlogic-dt-id)" = gxlx2_p291_1g ] || tvbase_fail 'placa distinta'
}
tvbase_file() {
 [ -f "$1" ] && [ -r "$1" ] && [ ! -L "$1" ] || tvbase_fail 'archivo regular ausente'
 [ "$(stat -c %s "$1")" = "$2" ] || tvbase_fail 'tamano de archivo distinto'
 t_before=$(stat -c '%s:%Y:%i' "$1") || tvbase_fail 'stat fallo'
 t_sum=$(tvbase_sha "$1") || tvbase_fail 'lectura SHA fallo'
 tvbase_hex "$t_sum" || tvbase_fail 'SHA vacio o invalido'
 [ "$t_sum" = "$3" ] || tvbase_fail 'archivo SHA distinto'
 [ "$(stat -c '%s:%Y:%i' "$1")" = "$t_before" ] || tvbase_fail 'archivo cambio durante lectura'
}
tvbase_media
tvbase_profile
t_test=$(printf abc | tvbase_sha) || tvbase_fail 'autocontrol SHA fallo'
tvbase_hex "$t_test" || tvbase_fail 'autocontrol SHA vacio'
[ "$t_test" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad ] || tvbase_fail 'autocontrol incorrecto'
tvbase_file "$tv_d/TVBASE-P291-A9-0.1.1-RECOVERY.zip" 573089164 e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205
[ "$(/system/bin/pm path com.droidlogic.otaupgrade 2>&1)" = package:/product/app/OTAUpgrade/OTAUpgrade.apk ] || tvbase_fail 'ruta del actualizador distinta'
tvbase_file /product/app/OTAUpgrade/OTAUpgrade.apk 190988 9ffb822fc76974ee9df8c5493f0929638b69140f71506946cb410bab489a1d9c
tvbase_media
tvbase_profile
t_launch=$(/system/bin/am start -W -n com.droidlogic.otaupgrade/.MainActivity 2>&1) || { printf '%s\n' "$t_launch"; tvbase_fail 'apertura rechazada'; }
[ "$(printf '%s\n' "$t_launch" | grep -c '^Status: ok$')" = 1 ] || { printf '%s\n' "$t_launch"; tvbase_fail 'apertura sin confirmacion'; }
t_activity=$(printf '%s\n' "$t_launch" | sed -n 's/^Activity: //p')
case "$t_activity" in com.droidlogic.otaupgrade/.MainActivity|com.droidlogic.otaupgrade/com.droidlogic.otaupgrade.MainActivity) ;; *) printf '%s\n' "$t_launch"; tvbase_fail 'actividad inesperada';; esac
printf 'TVBASE_OPEN_OK:%s\n' "$tv_t"
