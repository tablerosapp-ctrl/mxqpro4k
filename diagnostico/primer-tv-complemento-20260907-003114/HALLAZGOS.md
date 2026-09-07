# Complemento 0.6 del primer P291: captura y análisis

Análisis del 7 de septiembre de 2026. Este documento y [resumen-saneado.json](resumen-saneado.json) son publicables; los informes originales, el APK original y la adquisición detallada permanecen privados. El reloj del TV no es confiable: la fecha corresponde a la adquisición en PC.

**Resultado:** se completó la captura de los archivos que faltaban. El ZIP TVBASE 0.1.1 tiene una firma integral válida con el certificado OTA obtenido de este P291. El actualizador original prepara una orden persistente antes de solicitar reinicio; por ello ofrece una ruta distinta de los reinicios directos anteriores. Todavía no se demostró la escritura real de esa orden, la preparación del mapa de bloques, el arranque de recovery ni la instalación.

## Captura e integridad

Acceso USB 0.6 produjo `TVBASE-evidencia-690a4d7ced1f49f9916ac18cfe6106a2`: **25 archivos adquiridos, diez SHA-256 comprobados, los cuatro marcadores posteriores a la creación y cierre COMPLETO**. El autocontrol del contenido `abc` coincide con su SHA-256 conocido. La captura corresponde al primer TV `gxlx2_p291_1g`, Android 9/API 28, con acceso shell UID2000. No reinició ni instaló una ROM.

| Archivo útil | Tamaño | SHA-256 |
| --- | ---: | --- |
| `OTAUpgrade.apk` | 190.988 bytes | `9ffb822fc76974ee9df8c5493f0929638b69140f71506946cb410bab489a1d9c` |
| `otacerts.zip` | 1.073 bytes | `7dd077650421772a3114c9132cd3da989b65f073459b7d8023e7138f2323a6c8` |
| `init-y-fstab.txt` | 10.408 bytes | `2b596d66bbbaf530ea637f1b2d25a5b062acb4c06c3f2b72e9d074bff1ef03b4` |

El APK es idéntico por SHA-256 al obtenido anteriormente del P271. Esa coincidencia permite reutilizar el análisis de ese código; **no equipara hardware, firmware, particiones ni recovery** de los equipos. El origen ahora está acreditado directamente en el P291.

## Confianza del ZIP existente

La [auditoría de certificados](certificados-ota.json) comprobó la firma integral de `TVBASE-P291-A9-0.1.1-RECOVERY.zip` con el certificado capturado del P291. Se verificó la región firmada completa mediante la implementación local Python y, de forma independiente, OpenJDK PKCS7. El archivo conserva 573.089.164 bytes y SHA-256 `e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205`.

El almacén del P291 contiene una clave pública que coincide con la del firmante del ZIP; **no hace falta volver a firmar para coincidir con ese almacén**. La aceptación por `RecoverySystem.verifyPackage` es una inferencia basada en AOSP Android 9 y en la criptografía comprobada en PC; no se ejecutó ese método en el framework del fabricante. Las claves `/res/keys` del recovery interno siguen desconocidas, por lo que la comprobación no acredita su aceptación ni la compatibilidad de la ROM. [RecoverySystem de AOSP Android 9](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/core/java/android/os/RecoverySystem.java).

La firma de `OTAUpgrade.apk` es válida para API28 y usa una clave diferente de la del almacén OTA; son mecanismos distintos. El almacén del candidato original también usa una clave diferente: su nombre `testkey.x509.pem` no demuestra igualdad. Esa diferencia debe considerarse al definir futuras actualizaciones del sistema final; no invalida el resultado del ZIP actual frente al Android actual del P291.

## Flujo real del actualizador

El análisis estático identifica `com.droidlogic.otaupgrade`, versionCode 2, versionName `2.0201411271418`, con identidad de sistema y permisos de actualización. El componente concreto del menú es `com.droidlogic.otaupgrade/.MainActivity`.

1. Abrir explícitamente ese menú construye la interfaz. No selecciona un ZIP ni dispara Update. No se encontró una entrada pública para preparar un ZIP local sin reiniciar.
2. `Select` acepta archivos por su sufijo `.zip`; no verifica firma. **El primer Update ya intenta escribir `/cache/recovery/command`, antes de mostrar la confirmación. Cancelar solo cierra el diálogo y no limpia esa orden.** La aparición del diálogo tampoco prueba que la escritura haya tenido éxito.
3. El Update de la confirmación inicia la preparación. En API28, el flujo intenta copiar el ZIP a `/data/cache/update.zip`.
4. `installPackage` intenta primero el método privado `updateWithBCB`. Este escribe `/cache/recovery/uncrypt_file`, elimina el mapa anterior y solicita `setupBcb` por reflexión, con `--update_package=@/cache/recovery/block.map` y locale. Después pide `PowerManager.reboot("recovery-update")`. Si devuelve false, existe una alternativa mediante `RecoverySystem.installPackage`.
5. La APK no llama a `processPackage` ni ejecuta `uncrypt`: **crear el nuevo block.map depende del framework**. El ZIP copiado y `uncrypt_file` no bastan para acreditar una actualización preparada.

El código original tiene límites relevantes: no verifica la firma del ZIP; su comprobación de copia no acredita integridad; puede llegar a pedir reinicio aunque no encuentre el método `setupBcb`; y no lee de vuelta la orden de cache. También contiene preferencias privadas de borrado cuyo valor actual no se obtuvo. Estos defectos no prueban que la próxima operación vaya a fallar, pero impiden presentar una pantalla de progreso o el apagado como confirmación de preparación correcta.

## Parámetros reales y alcance del arranque en frío

La configuración legible del P291 establece `/dev/block/misc /misc emmc`, y `/dev/block/cache` y `/dev/block/data` como ext4. La captura anterior identifica misc como179:7, de8MiB, y cache como179:3, de1.120MiB. Son capacidades de partición, no espacio libre. El nodo misc es root:root0600; `/cache` es system:cache0770. Shell UID2000 no puede preparar directamente esas ubicaciones.

El init legible copia `ro.boot.bootreason` a `sys.boot.reason`; su coincidencia en `reboot,update` no es evidencia independiente de ejecución de recovery. Los init de raíz tienen lectura denegada. La sección vacía de `/system/etc/init/uncrypt.rc` **no demuestra que falten servicios**: el filtro de la captura no incluye los términos `uncrypt`, `setup-bcb` ni `clear-bcb`.

El [pstore anterior](../primer-tv-evidencia-20260907-000948/HALLAZGOS.md) muestra preparación del reinicio y actividad del mismo kernel durante más de ocho minutos después. Favorece un atasco al cerrar el sistema; no identifica la función bloqueada ni demuestra que SDIO sea la causa. La captura 0.6 no contiene un intento nuevo de instalación.

En AOSP, BCB guarda la orden en misc y la escritura incluye sincronización. El código Amlogic de referencia procesa `boot-recovery` mediante `recovery_from_flash`. La configuración P271 de referencia consulta BCB antes de elegir el modo de arranque; por eso una orden persistente podría servir tras cortar y restablecer alimentación. **No se extrajo el cargador P291 y no se acreditó esa secuencia en él.** Tampoco equivale a cargar el recovery externo del pendrive. No trasladar índices físicos ni variables del P271 al P291. [BCB de AOSP](https://android.googlesource.com/platform/bootable/recovery/+/refs/heads/main/bootloader_message/bootloader_message.cpp), [BCB de Amlogic](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/common/cmd_bcb.c).

El arranque en frío solo podría continuar esa instalación si antes quedaron correctos el ZIP interno, block.map y BCB, y el cargador y recovery los aceptan. No se comprobó ninguna de esas condiciones durante una ejecución real. Para el actualizador futuro, AOSP Android 9 separa `processPackage` y `scheduleUpdateOnBoot`; permiten diseñar preparación y comprobación antes del reinicio, pero requieren RECOVERY y no constituyen una entrada disponible para la APK auxiliar actual. [API y secuencia de AOSP Android 9](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/core/java/android/os/RecoverySystem.java).

## Siguiente entregable

**Acceso USB 0.7 está en preparación; aún no se acredita entrega ni prueba física.** Su alcance previsto es comprobar el perfil P291, el USB marcado, el ZIP exacto y el APK original, y abrir únicamente el menú OEM explícito. No iniciará Update, no solicitará reinicio por su cuenta ni repetirá la captura general. El primer Update ya tiene efectos de preparación: no debe describirse como una consulta inocua.

Los archivos necesarios para decidir esta ruta ya fueron obtenidos y analizados. Siguen pendientes la ejecución comprobada del flujo OEM, la preparación persistente real, recovery funcional, respaldo original del TV, instalación interna y primer arranque de TVBASE. El éxito de captura y firma no sustituye esos resultados.
