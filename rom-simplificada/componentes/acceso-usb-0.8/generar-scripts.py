"""Post-intento 0.8: lectura acotada, sin Update, reinicio ni cambio de radios."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
COMMON=r'''set -C
tvbase_fail(){ printf 'ERROR: %s\n' "$1"; exit 9; }
tvbase_hex(){ [ ${#1} = 64 ] || return 1; case "$1" in *[!0-9a-f]*) return 1;; esac; }
tvbase_sha(){ t_h=$(/system/bin/toybox timeout -s KILL 8 /system/bin/toybox sha256sum "$1") || return 1; t_h=${t_h%% *}; tvbase_hex "$t_h" || return 1; printf %s "$t_h"; }
tvbase_verify(){ t_e=$(cat "$tv_d/$1.sha256") || tvbase_fail 'falta SHA'; tvbase_hex "$t_e" || tvbase_fail 'SHA guardado invalido'; t_h=$(tvbase_sha "$tv_d/$1") || tvbase_fail 'lectura SHA'; tvbase_hex "$t_h" && [ "$t_e" = "$t_h" ] || tvbase_fail 'SHA distinto'; }
tvbase_seal(){ t_h=$(tvbase_sha "$tv_d/$1") || tvbase_fail 'SHA fallo'; tvbase_hex "$t_h" || tvbase_fail 'SHA vacio'; printf '%s\n' "$t_h" > "$tv_d/$1.sha256" || tvbase_fail 'escritura SHA'; tvbase_verify "$1"; }
[ "$(id -u)" = 2000 ] && [ "$(getprop ro.build.version.sdk)" = 28 ] && [ "$(tr -d '\000' < /proc/device-tree/amlogic-dt-id)" = gxlx2_p291_1g ] || tvbase_fail 'perfil distinto'
t_b=${tv_d%/*}
[ -d "$tv_d" ] && [ ! -L "$tv_d" ] && [ ! -L "$tv_d/INICIO.txt" ] && [ ! -L "$t_b/TVBASE-MEDIA.txt" ] && [ "$(cat "$tv_d/INICIO.txt")" = "$tv_t" ] && [ "$(cat "$t_b/TVBASE-MEDIA.txt")" = TVBASE-P291-20260906-4dc82786 ] || tvbase_fail 'USB/carpeta distinto'
tvbase_done(){ printf '%s\n' "$tv_t" > "$tv_d/etapa-$1.ok" || tvbase_fail 'etapa'; [ "$(cat "$tv_d/etapa-$1.ok")" = "$tv_t" ] || tvbase_fail 'lectura etapa'; printf 'TVBASE_OK:%s:%s\n' "$1" "$tv_t"; }
'''
RUN=r'''tvbase_run(){
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
'''
CREATE=r'''set -C
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
'''
SETUP=r'''printf abc > "$tv_d/autocontrol.bin" || tvbase_fail 'autocontrol'
t_h=$(tvbase_sha "$tv_d/autocontrol.bin") || tvbase_fail 'SHA autocontrol'
tvbase_hex "$t_h" && [ "$t_h" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad ] || tvbase_fail 'SHA autocontrol incorrecto'
tvbase_seal autocontrol.bin
{
 printf 'TVBASE POSTINTENTO 0.8; no reinicia; consultas con plazo\n'; id; cat /proc/uptime; cat /proc/sys/kernel/random/boot_id
 for t_p in ro.build.version.sdk ro.build.display.id ro.boot.bootreason sys.boot.reason persist.sys.boot.reason sys.shutdown.requested init.svc.uncrypt init.svc.adbd init.svc.logd; do printf '%s=' "$t_p"; getprop "$t_p"; done
} > "$tv_d/identidad.txt" 2>&1 || tvbase_fail 'identidad'
tvbase_seal identidad.txt
tvbase_done 1
'''
PSTORE=r'''t_i=0
printf 'PSTORE; solo console/pmsg; hasta cuatro archivos, 2MiB cada uno\n' > "$tv_d/pstore.txt" || tvbase_fail 'informe'
for t_src in /sys/fs/pstore/console-ramoops* /sys/fs/pstore/pmsg-ramoops*; do
 [ -e "$t_src" ] || continue
 t_i=$((t_i+1)); [ "$t_i" -le 4 ] || { printf 'LIMITE_ARCHIVOS\n' >> "$tv_d/pstore.txt"; break; }
 t_n=${t_src##*/}; case "$t_n" in *[!A-Za-z0-9_-]*) tvbase_fail 'nombre pstore';; esac
 printf 'ORIGEN %s\n' "$t_src" >> "$tv_d/pstore.txt" || tvbase_fail 'informe'
 if [ ! -r "$t_src" ] || [ ! -f "$t_src" ] || [ -L "$t_src" ]; then printf 'NO_LEGIBLE\n' >> "$tv_d/pstore.txt"; continue; fi
 t_sz=$(stat -c %s "$t_src") || tvbase_fail 'stat pstore'
 case "$t_sz" in ''|*[!0-9]*) tvbase_fail 'tamano pstore';; esac
 if [ "$t_sz" -le 0 ] || [ "$t_sz" -gt 2097152 ]; then printf 'TAMANO_NO_ADMITIDO %s\n' "$t_sz" >> "$tv_d/pstore.txt"; continue; fi
 t_before=$(tvbase_sha "$t_src") || tvbase_fail 'SHA origen pstore'; tvbase_hex "$t_before" || tvbase_fail 'SHA origen vacio'
 /system/bin/toybox timeout -s KILL 8 /system/bin/toybox head -c 2097153 "$t_src" > "$tv_d/$t_n.bin" || tvbase_fail 'copia pstore'
 t_after=$(tvbase_sha "$t_src") || tvbase_fail 'SHA posterior pstore'; tvbase_hex "$t_after" || tvbase_fail 'SHA posterior vacio'
 [ "$t_before" = "$t_after" ] && [ "$(stat -c %s "$tv_d/$t_n.bin")" = "$t_sz" ] || tvbase_fail 'origen cambio'
 tvbase_seal "$t_n.bin"
 [ "$(cat "$tv_d/$t_n.bin.sha256")" = "$t_before" ] || tvbase_fail 'copia pstore distinta'
 printf 'COPIADO %s bytes=%s sha256=%s\n' "$t_n.bin" "$t_sz" "$t_before" >> "$tv_d/pstore.txt" || tvbase_fail 'informe'
done
printf 'entradas_encontradas=%s\n' "$t_i" >> "$tv_d/pstore.txt" || tvbase_fail 'informe final'
tvbase_seal pstore.txt; tvbase_done 2
'''
FINAL=r'''for t_i in 1 2 3 4 5 6 7 8 9; do [ "$(cat "$tv_d/etapa-$t_i.ok")" = "$tv_t" ] || tvbase_fail 'etapa ausente'; done
for t_n in autocontrol.bin identidad.txt pstore.txt espacio.txt espacio.rc espacio.estado webview.txt webview.rc webview.estado; do tvbase_verify "$t_n"; done
for t_n in log-anterior log-actual wifi bluetooth bateria; do for t_s in txt rc estado; do tvbase_verify "$t_n.$t_s"; done; done
for t_f in "$tv_d"/console-ramoops*.bin "$tv_d"/pmsg-ramoops*.bin; do [ ! -f "$t_f" ] || tvbase_verify "${t_f##*/}"; done
printf 'TVBASE POSTINTENTO 0.8: recorrido terminado y archivos comprobados.\nLas salidas pueden indicar denegacion, timeout o truncamiento; esto no acredita respuesta de todos los servicios ni causa del fallo.\nNo se reinicio ni se cambio WiFi/BT.\n' > "$tv_d/COMPLETO.txt" || tvbase_fail 'cierre'
tvbase_seal COMPLETO.txt; tvbase_done 10
'''
def main():
 pieces=[CREATE,COMMON+SETUP,COMMON+PSTORE]
 queries=[('log-anterior',12,1048576,'/system/bin/logcat -L -b all -d'),('log-actual',12,524288,"/system/bin/logcat -b main -b system -d -v monotonic ShutdownThread:V BatteryStats:V BatteryExternalStatsWorker:V ActivityManager:I PowerManagerService:V RecoverySystem:V uncrypt:V '*:S'"),('wifi',8,262144,'/system/bin/dumpsys -t 5 wifi'),('bluetooth',8,262144,'/system/bin/dumpsys -t 5 bluetooth_manager'),('bateria',8,524288,'/system/bin/dumpsys -t 5 batterystats'),('espacio',8,32768,'/system/bin/toybox df /data /cache'),('webview',8,32768,'/system/bin/dumpsys -t 5 webviewupdate')]
 for i,(name,seconds,cap,command) in enumerate(queries,3):pieces.append(COMMON+RUN+f'tvbase_run {name} {seconds} {cap} {command}\ntvbase_done {i}\n')
 pieces.append(COMMON+FINAL)
 out=HERE/'scripts';out.mkdir(exist_ok=True)
 for i,body in enumerate(pieces):
  size=len(("shell:tv_t='"+'a'*32+"';tv_d='"+'/mnt/media_rw/'+'A'*64+'/TVBASE-postintento-'+'a'*32+"';\n"+body+'\0').encode())
  assert size<=4096,(i,size)
  (out/f'etapa-{i}.sh').write_text(body,encoding='utf8',newline='\n')
  print('stage',i,'max OPEN bytes',size)
 text='package local.tvbase.acceso;\nfinal class EvidenciaScripts {\n static final String[] STAGES={\n'+',\n'.join(json.dumps(x,ensure_ascii=False) for x in pieces)+'\n};\n'
 text+=' static String command(int step,String directory,String token)throws java.io.IOException {\n if(!Evidencia.validToken(token)||step<0||step>=STAGES.length||(step==0&&!"".equals(directory))||(step>0&&!Evidencia.validDirectory(directory,token)))throw new java.io.IOException("Etapa o destino invalido");\n String c="tv_t=\'"+token+"\';tv_d=\'"+directory+"\';\\n"+STAGES[step];\n if(c.getBytes("UTF-8").length+7>4096)throw new java.io.IOException("OPEN excedido"); return c;\n }\n}\n'
 (HERE/'EvidenciaScripts.java').write_text(text,encoding='utf8')
if __name__=='__main__':main()
