package local.tvbase.acceso;

/** Fixed read-only inspection; its only output file is on a USB bearing our marker. */
final class Diagnostico {
  static final String COMMAND =
    "tvbase_out=; " +
    "for tvbase_base in /storage/* /mnt/media_rw/*; do " +
    "[ -d \"$tvbase_base\" ] || continue; " +
    "[ \"$(cat \"$tvbase_base/TVBASE-MEDIA.txt\" 2>/dev/null)\" = TVBASE-P291-20260906-4dc82786 ] || continue; " +
    "tvbase_candidate=\"$tvbase_base/TVBASE-diagnostico-$(date +%Y%m%d-%H%M%S)-$$.txt\"; " +
    "if (set -C; : > \"$tvbase_candidate\") 2>/dev/null; then tvbase_out=$tvbase_candidate; break; fi; done; " +
    "if [ -z \"$tvbase_out\" ]; then printf 'ERROR: no se pudo guardar en el pendrive TVBASE. No se reinicio ni se cambio Android.\\n'; exit 2; fi; " +
    "{ " +
    "printf 'TVBASE DIAGNOSTICO 0.4 - SOLO LECTURA\\n'; date; " +
    "printf '\\nIDENTIDAD\\n'; id; cat /proc/device-tree/amlogic-dt-id; printf '\\n'; " +
    "for tvbase_key in ro.build.display.id ro.build.version.sdk ro.product.device ro.product.board ro.bootloader ro.hardware ro.debuggable ro.secure ro.adb.secure service.adb.tcp.port persist.adb.tcp.port ro.bootmode ro.boot.bootreason sys.boot.reason ro.boot.reboot_mode ro.boot.verifiedbootstate init.svc.adbd; do printf '%s=' \"$tvbase_key\"; getprop \"$tvbase_key\"; done; " +
    "printf '\\nKERNEL Y ARRANQUE\\n'; cat /proc/version; cat /proc/cmdline; " +
    "printf '\\nPARTICIONES\\n'; cat /proc/partitions; " +
    "printf '\\nDESTINOS Y PERMISOS\\n'; ls -ld /cache /cache/recovery /sys/fs/pstore; " +
    "ls -l /dev/block/boot /dev/block/recovery /dev/block/misc /dev/block/system /dev/block/vendor /dev/block/vbmeta; " +
    "ls -l /dev/block/by-name /dev/block/platform/*/by-name 2>&1 | head -c 10000; " +
    "printf '\\nCABECERA RECOVERY (solo lectura, 64 bytes)\\n'; od -An -tx1 -N64 /dev/block/recovery; " +
    "printf '\\nORDEN RECOVERY PENDIENTE (solo lectura)\\n'; head -c 4096 /cache/recovery/command; " +
    "printf '\\nREGISTRO RECOVERY\\n'; tail -c 10000 /cache/recovery/last_log; " +
    "printf '\\nREGISTRO ANTERIOR RECOVERY\\n'; tail -c 6000 /cache/recovery/last_log.1; " +
    "printf '\\nREGISTROS PERSISTENTES\\n'; ls -l /sys/fs/pstore; " +
    "for tvbase_log in /sys/fs/pstore/console-ramoops-0 /sys/fs/pstore/console-ramoops /proc/last_kmsg; do printf '\\n%s\\n' \"$tvbase_log\"; tail -c 6000 \"$tvbase_log\"; done; " +
    "printf '\\nLOG DE ARRANQUE ACTUAL\\n'; logcat -b all -d -v brief -t 160 2>&1 | grep -iE 'reboot|recovery|shutdown|powerctl|bootreason|boot_reason|watchdog' | head -c 8000; " +
    "printf '\\nMONTAJES\\n'; head -c 10000 /proc/mounts; " +
    "printf '\\nFIN TVBASE DIAGNOSTICO 0.4\\n'; " +
    "} >> \"$tvbase_out\" 2>&1; " +
    "if [ \"$(tail -n 1 \"$tvbase_out\")\" != 'FIN TVBASE DIAGNOSTICO 0.4' ]; then printf 'ERROR: informe incompleto; no retirar ni reiniciar.\\n'; exit 3; fi; " +
    "sync; printf 'Informe guardado en el pendrive:\\n%s\\n' \"$tvbase_out\"; " +
    "printf 'Se registraron tambien los permisos denegados. No se reinicio ni se instalo Android.\\n';";

  static final String VERIFY_USB =
    "tvbase_found=; for tvbase_base in /storage/* /mnt/media_rw/*; do " +
    "[ \"$(cat \"$tvbase_base/TVBASE-MEDIA.txt\" 2>/dev/null)\" = TVBASE-P291-20260906-4dc82786 ] || continue; " +
    "tvbase_found=$tvbase_base; break; done; " +
    "if [ -z \"$tvbase_found\" ]; then printf 'ERROR: pendrive TVBASE ausente\\n'; exit 2; fi; " +
    "for tvbase_forbidden in aml_autoscript aml_sdc_burn.ini factory_update_param.aml update.zip dtb.img; do " +
    "if [ -e \"$tvbase_found/$tvbase_forbidden\" ]; then printf 'ERROR: archivo de arranque inesperado: %s\\n' \"$tvbase_forbidden\"; exit 3; fi; done; " +
    "set -- $(sha256sum \"$tvbase_found/TVBASE-P291-A9-0.1.1-RECOVERY.zip\" 2>/dev/null); " +
    "if [ \"$1\" != e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205 ]; then printf 'ERROR: ROM ausente o lectura distinta\\n'; exit 4; fi; " +
    "set -- $(sha256sum \"$tvbase_found/recovery.img\" 2>/dev/null); " +
    "if [ \"$1\" != e59ef077378f8b1ba644bcfbef2a0f55e9914258696f203e813392e0a9fed01b ]; then printf 'ERROR: recovery USB ausente o lectura distinta\\n'; exit 5; fi; " +
    "printf 'TVBASE_USB_OK\\n';";

  private Diagnostico() {}
}
