# P291: resultado de Acceso USB 0.4

Adquisición en PC: **6/9/2026, 23:38 ART**. El usuario informa que «Guardar informe y abrir instalador USB (reinicia)» deja el TV sin señal y nunca aparece recovery. No se observó instalación del ZIP ni respaldo de particiones originales.

## Evidencia nueva

Se identificó el mismo Kingston de 30.943.995.904 bytes, no perteneciente al sistema, con marcador TVBASE correcto. Se copiaron dos informes de 14.891 bytes cada uno, comprobando SHA-256 de origen y copia. Los originales y adquisición detallada se conservan solo localmente; [resumen-saneado.json](resumen-saneado.json) registra hashes, observaciones y límites para Git.

Los informes se denominan `TVBASE-diagnostico-20200101-004250-25473.txt` y `TVBASE-diagnostico-20200101-004256-25565.txt`. El reloj del TV estaba en 2020: sus nombres no son fechas fiables del experimento. Son idénticos salvo la línea de hora, separada por seis segundos. Contienen el marcador de fin correcto y corresponden a la recopilación **anterior a solicitar update**. No son dos registros del fallo posterior.

| Dato observado | Resultado | Lo que permite concluir |
| --- | --- | --- |
| Perfil | `gxlx2_p291_1g`, Android9/API28, build20250226 | Es el primer equipo esperado |
| Identidad del acceso | UID/GID2000 shell, contexto `u:r:shell:s0` | ADB local funciona; no es root |
| eMMC | `mmcblk0`, 7.650.410.496 bytes | Capacidad expuesta por este kernel, sin extrapolar el segundo TV |
| recovery | Bloque179:6, 25.165.824 bytes =24MiB | La partición existe; su contenido no pudo leerse |
| boot | Bloque179:11, 16.777.216 bytes | Tamaño observado; no valida contenido o compatibilidad |
| system | Bloque179:18, 1.342.177.280 bytes | Coincide en capacidad con la imagen system preparada |
| vendor | Bloque179:16, 943.718.400 bytes | Tiene capacidad para el payload actual; el instalador debe revalidar |
| Motivos de arranque | `ro.boot.bootreason=recovery`, `sys.boot.reason=recovery` | Motivo comunicado al Android que arrancó; no prueba ejecución de recovery |
| Lectura de bloques/cache | Permission denied en recovery, command y last_log | No conocemos la imagen instalada ni las órdenes pendientes |
| pstore | console-ramoops de32.756 bytes; ftrace de131.072 bytes visibles | El informe solo guardó los últimos6000 bytes de console; faltó evidencia completa |

Los tamaños se derivan de `/proc/partitions` y de los números de bloque expuestos por los aliases. No se asignan product/odm a números de partición por simple semejanza con otro equipo.

## Interpretación acotada

**No está demostrado que falte recovery.** Existe su partición, pero UID2000 no pudo leer la cabecera. Puede haber contenido inválido, un fallo de carga, un problema de salida HDMI o un reinicio que no llegue al cargador; estos informes no distinguen esas hipótesis.

`ro.boot.bootreason` es el motivo comunicado por el cargador. `sys.boot.reason` puede derivarse del mismo dato, por lo que su coincidencia no es una segunda confirmación independiente. No demuestra qué imagen se ejecutó ni que `update` haya llegado a U-Boot. [Motivos de arranque AOSP](https://source.android.com/docs/core/architecture/bootloader/boot-reason).

El fragmento persistente contiene timeouts SDIO CMD53 y bytes corruptos. Es idéntico en ambas capturas anteriores al reinicio. No demuestra un fallo del Kingston o de la eMMC, ni que ese driver haya bloqueado el apagado. El driver Amlogic de referencia trata ese timeout como error de petición; hacen falta las fases posteriores para ubicar el bloqueo. [Driver SDIO](https://github.com/khadas/linux/blob/khadas-vims-4.9.y/drivers/amlogic/mmc/aml_sd_emmc_v3.c).

Linux ejecuta `device_shutdown()` antes del reinicio de máquina: un problema de apagado de un driver podría impedir llegar al cargador. Es una hipótesis, no la causa demostrada en esta unidad. Los datos no contienen el tramo posterior al botón que permitiría comprobarlo. [Linux4.9, secuencia de reinicio](https://github.com/torvalds/linux/blob/v4.9/kernel/reboot.c), [init Android9](https://github.com/aosp-mirror/platform_system_core/blob/android-9.0.0_r1/init/reboot.cpp).

Ramoops usa RAM persistente entre reinicios; una captura corrupta después de cortar alimentación no permite diagnosticar por sí sola RAM averiada. Conservar los bytes originales evita empeorar la evidencia mediante decodificación de texto. [Ramoops del kernel](https://docs.kernel.org/admin-guide/ramoops.html).

## Medio y archivos

La lectura completa posterior de ROM0.1.1, recovery externo y APK0.4 coincide con los hashes de entrega. No se modificó el USB al adquirir los informes. Windows mostraba `HealthStatus=Warning`; la comprobación FAT32 de solo lectura terminó con código0 y declaró no encontrar problemas, aunque emitió también «Acceso denegado» al principio. No se reparó, formateó ni tomó ese aviso como explicación del fallo del TV. La lectura de los archivos no acredita toda la capacidad física del pendrive, pero sí descarta cambios de esos tres artefactos respecto de la entrega.

## Decisión siguiente · ADR-13

Retirar el intento0.4 como instrucción a repetir. Preparar Acceso USB0.5 para recopilar sin reiniciar: pstore completo, boot_id/uptime y motivos actuales/anteriores; APK y permisos del actualizador de **este** P291; certificados OTA públicos y configuración de arranque legible. Si algo está denegado, registrarlo sin alterar permisos ni pedir root.

El actualizador inicial solo se probó con un ZIP vacío. Su vía no está descartada, pero no se justifican otro intento o una firma distinta basándose en el APK del P271. Revisar el APK real permite determinar si prepara una orden persistente y cómo llega al reinicio. `otacerts.zip` documenta la confianza de Android; no demuestra por sí solo la lista de claves interna del recovery. [RecoverySystem Android9](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-9.0.0_r1/core/java/android/os/RecoverySystem.java).

No cambiar la ROM ni reflashear el pendrive para corregir una entrada aún no demostrada. La próxima observación útil es la evidencia posterior al último intento, sin provocar otro apagado para obtenerla.
