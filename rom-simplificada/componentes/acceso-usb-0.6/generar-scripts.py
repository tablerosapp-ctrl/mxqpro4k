"""Fixed, complementary 0.6 capture; Android's updater is read, never launched."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
CREATE=r'''set -C
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
'''
COMMON=r'''set -C
tvbase_fail() { printf 'ERROR: %s\n' "$1"; exit 9; }
t_b=${tv_d%/*}
[ -d "$tv_d" ] && [ ! -L "$tv_d" ] || tvbase_fail 'carpeta original ausente'
[ "$(cat "$t_b/TVBASE-MEDIA.txt" 2>/dev/null)" = TVBASE-P291-20260906-4dc82786 ] || tvbase_fail 'cambio el USB'
[ "$(cat "$tv_d/INICIO.txt" 2>/dev/null)" = "$tv_t" ] || tvbase_fail 'carpeta incorrecta'
tvbase_hex() {
 [ ${#1} = 64 ] || return 1
 case "$1" in *[!0-9a-f]*) return 1;; esac
}
tvbase_sha() {
 t_raw=$(/system/bin/toybox sha256sum "$1") || return 1
 t_value=${t_raw%% *}
 tvbase_hex "$t_value" || return 1
 printf '%s' "$t_value"
}
tvbase_verify() {
 t_file="$tv_d/$1"
 t_line=$(cat "$t_file.sha256") || tvbase_fail 'falta registro SHA'
 t_expected=${t_line%% *}
 tvbase_hex "$t_expected" || tvbase_fail 'SHA guardado invalido'
 [ "${t_line#*  }" = "$t_file" ] || tvbase_fail 'ruta del SHA distinta'
 t_read=$(tvbase_sha "$t_file") || tvbase_fail 'SHA de lectura fallo'
 tvbase_hex "$t_read" || tvbase_fail 'SHA leido invalido'
 [ "$t_expected" = "$t_read" ] || tvbase_fail 'SHA de lectura distinto'
}
tvbase_rec() {
 tvbase_hex "$2" || tvbase_fail 'no se registra SHA invalido'
 printf '%s  %s\n' "$2" "$tv_d/$1" > "$tv_d/$1.sha256" || tvbase_fail 'registro SHA fallo'
 sync || tvbase_fail 'sync fallo'
 tvbase_verify "$1"
}
tvbase_seal() {
 [ "$(tail -n 1 "$tv_d/$1")" = "FIN-$tv_t" ] || tvbase_fail 'informe truncado'
 t_sum=$(tvbase_sha "$tv_d/$1") || tvbase_fail 'SHA informe fallo'
 tvbase_hex "$t_sum" || tvbase_fail 'SHA informe invalido'
 tvbase_rec "$1" "$t_sum"
}
tvbase_done() {
 printf '%s\n' "$tv_t" > "$tv_d/etapa-$1.ok" || tvbase_fail 'etapa incompleta'
 sync || tvbase_fail 'sync fallo'
 [ "$(cat "$tv_d/etapa-$1.ok")" = "$tv_t" ] || tvbase_fail 'etapa distinta'
 printf 'TVBASE_OK:%s:%s\n' "$1" "$tv_t"
}
'''
COPY=r'''tvbase_copy() {
 t_src=$1; t_name=$2; t_max=$3
 printf '\nORIGEN %s\n' "$t_src" >> "$t_log" || tvbase_fail 'registro fallo'
 [ -f "$t_src" ] && [ -r "$t_src" ] && [ ! -L "$t_src" ] || tvbase_fail 'original no legible'
 t_size=$(stat -c %s "$t_src") || tvbase_fail 'stat fallo'
 case "$t_size" in ''|*[!0-9]*) tvbase_fail 'longitud invalida';; esac
 [ "$t_size" -gt 0 ] && [ "$t_size" -le "$t_max" ] || tvbase_fail 'tamano fuera de limite'
 t_before=$(tvbase_sha "$t_src") || tvbase_fail 'SHA original fallo'
 tvbase_hex "$t_before" || tvbase_fail 'SHA original invalido'
 head -c "$((t_max+1))" "$t_src" > "$tv_d/$t_name" || tvbase_fail 'copia fallo'
 sync || tvbase_fail 'sync copia fallo'
 t_size2=$(stat -c %s "$tv_d/$t_name") || tvbase_fail 'stat copia fallo'
 t_after=$(tvbase_sha "$t_src") || tvbase_fail 'segunda lectura fallo'
 tvbase_hex "$t_after" || tvbase_fail 'SHA posterior invalido'
 [ "$t_size" = "$t_size2" ] && [ "$t_before" = "$t_after" ] || tvbase_fail 'fuente o tamano cambio'
 tvbase_rec "$t_name" "$t_before"
 printf 'COPIADO %s\nbytes_original=%s\nbytes_copia=%s\nsha256_original=%s\nsha256_copia=%s\n' "$t_name" "$t_size" "$t_size2" "$t_before" "$t_before" >> "$t_log" || tvbase_fail 'registro copia fallo'
}
'''
PREFLIGHT=r'''printf abc > "$tv_d/autocontrol.bin" || tvbase_fail 'autocontrol no escrito'
t_check=$(tvbase_sha "$tv_d/autocontrol.bin") || tvbase_fail 'autocontrol SHA fallo'
tvbase_hex "$t_check" || tvbase_fail 'autocontrol SHA vacio'
[ "$t_check" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad ] || tvbase_fail 'autocontrol incorrecto'
tvbase_rec autocontrol.bin "$t_check"
printf 'TVBASE COMPLEMENTO 0.6\nAutocontrol SHA256 de abc correcto.\nFIN-%s\n' "$tv_t" > "$tv_d/autocontrol.txt" || tvbase_fail 'informe fallo'
tvbase_seal autocontrol.txt
t_log="$tv_d/certificados.txt"
printf 'Certificados publicos OTA obligatorios\n' > "$t_log" || tvbase_fail 'informe fallo'
tvbase_copy /system/etc/security/otacerts.zip otacerts.zip 2097152
printf 'FIN-%s\n' "$tv_t" >> "$t_log" || tvbase_fail 'informe fallo'
tvbase_seal certificados.txt
tvbase_done 1
'''
APK=r'''t_pm=$(/system/bin/pm path com.droidlogic.otaupgrade 2>&1)
printf '%s\nFIN-%s\n' "$t_pm" "$tv_t" > "$tv_d/pm-path.txt" || tvbase_fail 'informe pm fallo'
tvbase_seal pm-path.txt
[ "$t_pm" = package:/product/app/OTAUpgrade/OTAUpgrade.apk ] || tvbase_fail 'OTA no coincide con ruta acreditada; ver pm-path.txt'
t_log="$tv_d/actualizador.txt"
printf 'Paquete com.droidlogic.otaupgrade, ruta acreditada P291. No se ejecuta.\n' > "$t_log" || tvbase_fail 'informe fallo'
tvbase_copy /product/app/OTAUpgrade/OTAUpgrade.apk OTAUpgrade.apk 33554432
printf 'FIN-%s\n' "$tv_t" >> "$t_log" || tvbase_fail 'informe fallo'
tvbase_seal actualizador.txt
tvbase_done 2
'''
CONFIG=r'''{
 printf 'TVBASE COMPLEMENTO 0.6; DATOS ACTUALES\n'; date; id
 cat /proc/device-tree/amlogic-dt-id; printf '\n'; cat /proc/sys/kernel/random/boot_id /proc/uptime
 for t_key in ro.build.display.id ro.build.version.sdk ro.boot.bootreason sys.boot.reason; do printf '%s=' "$t_key"; getprop "$t_key"; done
 printf 'FIN-%s\n' "$tv_t"
} > "$tv_d/identidad.txt" 2>&1 || tvbase_fail 'identidad incompleta'
tvbase_seal identidad.txt
{
 printf 'INIT/FSTAB LEGIBLES; NO SE MODIFICAN\n'
 t_i=0
 for t_src in /init*.rc /vendor/etc/init/*.rc /vendor/etc/init/hw/*.rc /system/etc/init/*.rc /odm/etc/init/*.rc /odm/etc/init/hw/*.rc /product/etc/init/*.rc; do
  [ -f "$t_src" ] || continue; t_i=$((t_i+1)); [ "$t_i" -le 120 ] || { printf '\nLIMITE: 120 init\n'; break; }
  printf '\nINIT %s; lineas pertinentes hasta8KiB\n' "$t_src"
  grep -n -i -E 'reboot|powerctl|bootmode|bootreason|boot_reason|recovery|otaupgrade|factory_reset|instaboot|boot_completed' "$t_src" 2>&1 | head -c 8192
 done
 t_i=0
 for t_src in /fstab.* /vendor/etc/fstab* /odm/etc/fstab* /system/etc/fstab*; do
  [ -f "$t_src" ] || continue; t_i=$((t_i+1)); [ "$t_i" -le 16 ] || { printf '\nLIMITE: 16 fstab\n'; break; }
  printf '\nFSTAB %s; hasta32KiB\n' "$t_src"; head -c 32768 "$t_src"
 done
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/init-y-fstab.txt" 2>&1 || tvbase_fail 'configuracion incompleta'
tvbase_seal init-y-fstab.txt
tvbase_done 3
'''
FINAL=r'''for t_i in 1 2 3; do [ "$(cat "$tv_d/etapa-$t_i.ok" 2>/dev/null)" = "$tv_t" ] || tvbase_fail 'falta etapa'; done
sync || tvbase_fail 'sync final fallo'
for t_n in autocontrol certificados pm-path actualizador identidad init-y-fstab; do
 [ -f "$tv_d/$t_n.txt" ] && [ -f "$tv_d/$t_n.txt.sha256" ] || tvbase_fail 'falta informe obligatorio'
 [ "$(tail -n 1 "$tv_d/$t_n.txt")" = "FIN-$tv_t" ] || tvbase_fail 'informe obligatorio incompleto'
 tvbase_verify "$t_n.txt"
done
for t_n in autocontrol.bin otacerts.zip OTAUpgrade.apk; do
 [ -s "$tv_d/$t_n" ] || tvbase_fail 'falta binario obligatorio'
 tvbase_verify "$t_n"
done
{
 printf 'TVBASE EVIDENCIA 0.6 COMPLETA\n'; date
 printf 'token=%s\ncarpeta=%s\n' "$tv_t" "$tv_d"
 printf 'Autocontrol SHA correcto; OTAUpgrade.apk y otacerts.zip con hash original/copia. Configuracion pertinente y lecturas denegadas conservadas. No se copio GMS ni se reinicio el TV.\n'
 printf '\nFIN-%s\n' "$tv_t"
} > "$tv_d/COMPLETO.txt" || tvbase_fail 'cierre incompleto'
tvbase_seal COMPLETO.txt
tvbase_done 4
'''
def main():
 pieces=[CREATE,COMMON+COPY+PREFLIGHT,COMMON+COPY+APK,COMMON+CONFIG,COMMON+FINAL]
 lines=['package local.tvbase.acceso;','/** Generated by generar-scripts.py; fixed 0.6 complementary stages. */','final class EvidenciaScripts {','  static final String[] STAGES = {']
 lines+=['    '+json.dumps(x,ensure_ascii=False)+',' for x in pieces]
 lines+=['  };','  static String command(int step,String directory,String token) throws java.io.IOException {','    if(!Evidencia.validToken(token)||step<0||step>=STAGES.length||(step>0&&!Evidencia.validDirectory(directory,token)))throw new java.io.IOException("Etapa o destino invalido");','    String command="tv_t=\\\'"+token+"\\\';tv_d=\\\'"+directory+"\\\';\\n"+STAGES[step];','    if(("shell:"+command+"\\0").getBytes(java.nio.charset.StandardCharsets.UTF_8).length>4096)throw new java.io.IOException("Etapa demasiado grande para ADB");','    return command;','  }','}']
 out=HERE/'scripts';out.mkdir(exist_ok=True)
 for i,piece in enumerate(pieces):
  size=len(("shell:tv_t='"+'a'*32+"';tv_d='"+'/mnt/media_rw/'+'A'*64+'/TVBASE-evidencia-'+'a'*32+"';\n"+piece+'\0').encode())
  print(f'stage {i}: modeled maximum OPEN {size} bytes');assert size<=4096,(i,size)
  (out/f'etapa-{i}.sh').write_text(piece,encoding='utf8',newline='\n')
 (HERE/'EvidenciaScripts.java').write_text('\n'.join(lines)+'\n',encoding='utf8')
if __name__=='__main__':main()
