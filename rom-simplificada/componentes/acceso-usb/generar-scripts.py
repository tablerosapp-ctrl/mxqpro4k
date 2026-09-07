"""Embed fixed shell stages; no TV access."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
CREATE=r'''set -C
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
'''
COMMON=r'''set -C
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
'''
BOOT=r'''{
 printf 'TVBASE EVIDENCIA 0.5 - ARRANQUE ACTUAL\n'; date; id
 printf '\nBOOT_ID Y UPTIME\n'; cat /proc/sys/kernel/random/boot_id /proc/uptime
 printf '\nPLACA/KERNEL/CMDLINE\n'; cat /proc/device-tree/amlogic-dt-id; printf '\n'; cat /proc/version /proc/cmdline
 printf '\nPROPIEDADES CONCRETAS DE ARRANQUE\n'
 for tv_k in ro.build.display.id ro.build.version.sdk ro.product.device ro.product.board ro.bootloader ro.hardware ro.bootmode ro.boot.bootreason ro.boot.reboot_mode sys.boot.reason sys.boot.reason.last persist.sys.boot.reason persist.sys.boot.reason.history sys.shutdown.requested sys.powerctl sys.boot_completed ro.runtime.firstboot ro.boot.verifiedbootstate init.svc.adbd; do printf '%s=' "$tv_k"; getprop "$tv_k"; done
 printf '\nPARTICIONES\n'; cat /proc/partitions
 printf '\nTABLA DE ALIASES, HASTA 64 KIB POR DIRECTORIO\n'
 for tv_p in /dev/block /dev/block/by-name /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name; do [ -d "$tv_p" ] || continue; printf '\n%s\n' "$tv_p"; ls -l "$tv_p" 2>&1 | head -c 65536; printf '\n'; done
 printf '\nMONTAJES, HASTA 32 KIB\n'; head -c 32768 /proc/mounts
 printf '\nPERMISOS RECOVERY Y PSTORE\n'; ls -ld /cache /cache/recovery /sys/fs/pstore; ls -l /sys/fs/pstore
 printf '\nCOMANDO RECOVERY, SI ES LEGIBLE\n'; head -c 4096 /cache/recovery/command
 printf '\nDMESG ACTUAL, ULTIMOS 64 KIB; DENEGACION PERMITIDA\n'; dmesg 2>&1 | tail -c 65536
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/arranque.txt" 2>&1 || fail 'escritura arranque fallo'
seal arranque.txt
done_step 1
'''
COPY=r'''copy_one() {
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
'''
PSTORE=r'''tv_log="$tv_d/pstore.txt"
printf 'PSTORE: copias binarias completas; limite 2 MiB por archivo\n' > "$tv_log" || fail 'informe fallo'
tv_i=0
for tv_s in /sys/fs/pstore/console-ramoops* /sys/fs/pstore/ftrace-ramoops* /sys/fs/pstore/dmesg-ramoops*; do
 tv_i=$((tv_i+1)); [ "$tv_i" -le 16 ] || fail 'mas de 16 registros pstore'
 copy_one "$tv_s" "pstore-$tv_i.bin" 2097152
done
printf '\nFIN-%s\n' "$tv_t" >> "$tv_log" || fail 'pstore incompleto'
seal pstore.txt
done_step 2
'''
SELECT=r'''package_ok() {
 case "$1" in ''|*[!A-Za-z0-9_.]*|.*|*.|*..*|[0-9]*) return 1;; esac
}
tv_count=0; tv_pkg=; tv_component=; tv_rejected=0
while IFS= read -r tv_line; do
 case "$tv_line" in */*) ;; *) continue;; esac
 tv_p=${tv_line%%/*}; tv_c=${tv_line#*/}
 if ! package_ok "$tv_p"; then tv_rejected=$((tv_rejected+1)); continue; fi
 case "$tv_c" in ''|*[!A-Za-z0-9_.$]*|*..*) tv_rejected=$((tv_rejected+1)); continue;; esac
 tv_count=$((tv_count+1)); tv_pkg=$tv_p; tv_component=$tv_line
done < "$tv_d/resolucion.txt"
tv_selected=
if [ "$tv_count" = 1 ] && [ "$tv_rejected" = 0 ] && [ "$tv_pkg" != android ]; then tv_selected=$tv_pkg; fi
{
 [ -z "$tv_selected" ] || printf '%s\n' "$tv_selected"
 [ "$tv_selected" = com.droidlogic.otaupgrade ] || printf 'com.droidlogic.otaupgrade\n'
 printf 'FIN-%s\n' "$tv_t"
} > "$tv_d/paquetes.txt" || fail 'lista de paquetes fallo'
seal paquetes.txt
'''
QUERY=r'''{
 cmd package resolve-activity --brief -a android.settings.SYSTEM_UPDATE_SETTINGS
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/resolucion.txt" 2>&1 || fail 'resolucion incompleta'
seal resolucion.txt
'''
DETAIL=r'''{
 printf 'CANDIDATOS; NO SE EJECUTAN. La Activity resuelta puede ser solo una pantalla de Ajustes, no el flasheador.\n'
 printf 'componentes_validos=%s\nlineas_rechazadas=%s\ncomponente=%s\npaquete_resuelto_seleccionado=%s\n' "$tv_count" "$tv_rejected" "$tv_component" "$tv_selected"
 if [ -z "$tv_selected" ]; then printf 'SIN_RESOLUCION_UNIVOCA: ausente, ambigua, invalida o resolver android; se conserva candidato fijo.\n'; fi
 while IFS= read -r tv_p; do
  [ "$tv_p" = "FIN-$tv_t" ] && continue
  package_ok "$tv_p" || fail 'paquete invalido'
  printf '\nPAQUETE %s; DUMPSYS HASTA 96 KIB\n' "$tv_p"
  dumpsys -t 10 package "$tv_p" 2>&1 | head -c 98304
 done < "$tv_d/paquetes.txt"
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/actualizador.txt" 2>&1 || fail 'informe actualizador fallo'
seal actualizador.txt
{
 while IFS= read -r tv_p; do
  [ "$tv_p" = "FIN-$tv_t" ] && continue
  package_ok "$tv_p" || fail 'paquete invalido'
  pm path "$tv_p"
 done < "$tv_d/paquetes.txt"
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/pm-path.txt" 2>&1 || fail 'pm path incompleto'
seal pm-path.txt
done_step 3
'''
UPDATER=r'''tv_log="$tv_d/apk-y-certificados.txt"
printf 'APK de candidatos registrados y certificados publicos OTA; cuatro APK globales como maximo\n' > "$tv_log" || fail 'informe fallo'
tv_i=0
while IFS= read -r tv_line; do
 case "$tv_line" in package:*) tv_s=${tv_line#package:};; *) continue;; esac
 case "$tv_s" in *'/../'*|*'/./'*) fail 'ruta APK inesperada';; /system/*.apk|/vendor/*.apk|/product/*.apk|/odm/*.apk|/data/app/*.apk) ;; *) fail 'origen APK no permitido';; esac
 tv_i=$((tv_i+1)); [ "$tv_i" -le 4 ] || fail 'mas de cuatro APK'
 copy_one "$tv_s" "actualizador-$tv_i.apk" 33554432
done < "$tv_d/pm-path.txt"
printf 'rutas_APK_devuelvas=%s\n' "$tv_i" >> "$tv_log" || fail 'registro APK fallo'
copy_one /system/etc/security/otacerts.zip otacerts.zip 2097152
printf '\nFIN-%s\n' "$tv_t" >> "$tv_log" || fail 'informe incompleto'
seal apk-y-certificados.txt
done_step 4
'''
CONFIG=r'''{
 printf 'CONFIGURACION LEGIBLE; NO SE MODIFICA\n'
 tv_i=0
 for tv_s in /init*.rc /vendor/etc/init/*.rc /vendor/etc/init/hw/*.rc /system/etc/init/*.rc /odm/etc/init/*.rc /odm/etc/init/hw/*.rc /product/etc/init/*.rc; do
  [ -f "$tv_s" ] || continue; tv_i=$((tv_i+1)); [ "$tv_i" -le 120 ] || { printf '\nLIMITE: 120 archivos init\n'; break; }
  printf '\nINIT %s (lineas pertinentes, hasta 8 KiB)\n' "$tv_s"
  grep -n -i -E 'reboot|powerctl|bootmode|bootreason|boot_reason|recovery|otaupgrade|factory_reset|instaboot|boot_completed' "$tv_s" 2>&1 | head -c 8192
 done
 tv_i=0
 for tv_s in /fstab.* /vendor/etc/fstab* /odm/etc/fstab* /system/etc/fstab*; do
  [ -f "$tv_s" ] || continue; tv_i=$((tv_i+1)); [ "$tv_i" -le 16 ] || { printf '\nLIMITE: 16 fstab\n'; break; }
  printf '\nFSTAB %s (hasta 32 KiB)\n' "$tv_s"; head -c 32768 "$tv_s"
 done
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/init-y-fstab.txt" 2>&1 || fail 'informe configuracion fallo'
seal init-y-fstab.txt
done_step 5
'''
FINAL=r'''for tv_i in 1 2 3 4 5; do [ "$(cat "$tv_d/etapa-$tv_i.ok" 2>/dev/null)" = "$tv_t" ] || fail 'falta una etapa'; done
for tv_n in arranque pstore resolucion paquetes actualizador pm-path apk-y-certificados init-y-fstab; do
 [ -f "$tv_d/$tv_n.txt" ] && [ -f "$tv_d/$tv_n.txt.sha256" ] || fail 'falta informe obligatorio'
 [ "$(tail -n 1 "$tv_d/$tv_n.txt")" = "FIN-$tv_t" ] || fail 'informe obligatorio incompleto'
done
sync || fail 'sync final fallo'
tv_i=0
for tv_s in "$tv_d"/*.sha256; do
 [ -f "$tv_s" ] || fail 'faltan hashes'; tv_i=$((tv_i+1))
 sha256sum -c "$tv_s" >/dev/null 2>&1 || fail 'verificacion SHA256 fallo'
done
[ "$tv_i" -ge 8 ] || fail 'faltan informes'
{
 printf 'TVBASE EVIDENCIA 0.5 COMPLETA\n'; date
 printf 'token=%s\ncarpeta=%s\narchivos_con_SHA256=%s\n' "$tv_t" "$tv_d" "$tv_i"
 printf 'Lecturas del TV; salidas en este USB. Sin reiniciar ni iniciar actualizador. Las denegaciones quedan registradas.\n'
 printf '\nINVENTARIO\n'; ls -l "$tv_d"
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/COMPLETO.txt" 2>&1 || fail 'resumen incompleto'
seal COMPLETO.txt
done_step 6
'''
def main():
 pieces=[CREATE,COMMON+BOOT,COMMON+COPY+PSTORE,COMMON+QUERY+SELECT+DETAIL,COMMON+COPY+UPDATER,COMMON+CONFIG,COMMON+FINAL]
 lines=['package local.tvbase.acceso;','/** Generated by generar-scripts.py; fixed diagnostic stages only. */','final class EvidenciaScripts {','  static final String[] STAGES = {']
 lines+=['    '+json.dumps(x,ensure_ascii=False)+',' for x in pieces]
 lines+=['  };','  static String command(int step,String directory,String token) throws java.io.IOException {','    if(!Evidencia.validToken(token)||step<0||step>=STAGES.length||(step>0&&!Evidencia.validDirectory(directory,token)))throw new java.io.IOException("Etapa o destino inválido");','    String command="tv_t=\\\'"+token+"\\\';tv_d=\\\'"+directory+"\\\';\\n"+STAGES[step];','    if(("shell:"+command+"\\0").getBytes(java.nio.charset.StandardCharsets.UTF_8).length>4096)throw new java.io.IOException("Etapa demasiado grande para ADB");','    return command;','  }','}']
 (HERE/'EvidenciaScripts.java').write_text('\n'.join(lines)+'\n',encoding='utf8')
 out=HERE/'scripts';out.mkdir(exist_ok=True)
 for i,piece in enumerate(pieces):
  size=len(("shell:tv_t='"+'a'*32+"';tv_d='"+'/mnt/media_rw/'+'A'*64+'/TVBASE-evidencia-'+'a'*32+"';\n"+piece+'\0').encode())
  print(f'stage {i}: modeled maximum OPEN {size} bytes')
  assert size<=4096,(i,size)
  (out/f'etapa-{i}.sh').write_text(piece,encoding='utf8',newline='\n')
if __name__=='__main__':main()
