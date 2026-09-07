# Evidencia del primer P291 después del intento 0.4

Análisis del 7/9/2026. Este documento y `resumen-saneado.json` contienen el resumen publicable. Las capturas originales y los recibos de adquisición permanecen locales y privados. Se distingue el resultado físico de las inferencias basadas en código de referencia.

**Resultado principal:** ahora hay evidencia de que el sistema anterior entró en la preparación del reinicio y continuó ejecutando su kernel durante más de ocho minutos. Esto favorece un atasco al cerrar el sistema, antes del reinicio físico, frente a la explicación de que simplemente estuviera funcionando un recovery sin HDMI. Todavía no se identificó la función que se bloquea ni se acreditó que el cargador intentara leer el recovery externo.

## Capturas e integridad

Se adquirieron dos carpetas generadas por Acceso USB 0.5:

- `TVBASE-evidencia-d5cec3a75764497890668bd1e2f085dd`.
- `TVBASE-evidencia-e315690ee54f4639abe422fbd9cc46b4`.

Ambas son **capturas parciales**: el recorrido se detuvo en la copia de APK. No existe una adquisición completa del actualizador y sus certificados. El identificador de arranque coincide entre ambas; sus lecturas de uptime son 1367,49 y 1481,36 segundos, una diferencia de 113,87 segundos. Son dos consultas del mismo arranque, no dos reinicios registrados. El reloj del TV no tiene una fecha confiable; se conserva como referencia temporal la adquisición en la PC.

Los dos `pstore-1.bin` tienen 32.756 bytes y el mismo SHA-256 calculado en PC:

```text
708cae6320f0de63ab764269003d3bfb1a52a45815cc2d6da85849210f4331b8
```

Los recibos de adquisición registran los hashes de las copias en PC. Además, `verificacion-local-privada.json` confirma por captura seis informes de texto cuyos hashes coinciden con los registrados en el USB: `arranque.txt`, `pstore.txt`, `resolucion.txt`, `paquetes.txt`, `actualizador.txt` y `pm-path.txt`.

**Defecto observado de 0.5:** los campos de SHA del origen y la copia de los binarios quedaron vacíos, y sus archivos de comprobación no contienen una verificación válida. Afecta al pstore y a los tres APK divididos copiados. Por ello no se acredita la comprobación de esos binarios en el TV; el hash de adquisición en PC no sustituye esa comprobación.

**Causa reproducida:** una prueba con mksh R56 real en PC confirmó que el alias de Android 9 `hash='\builtin alias -t'` toma precedencia sobre la función del recopilador también llamada `hash`. La llamada no ejecuta la función que debía calcular y validar SHA; devuelve salida vacía y código 0. Después, las tres cadenas vacías del origen previo, origen posterior y copia comparan iguales. Las pruebas previas con Bash no reprodujeron esa particularidad de mksh. Esta reproducción explica el defecto del recopilador; no diagnostica daño del pendrive. Las dos copias binarias idénticas en PC siguen sin sustituir una verificación válida del origen en el TV.

La [auditoría de mksh y sus seis casos de regresión](../../rom-simplificada/instalador/MKSH-HALLAZGO-0.5.md) documenta las fuentes exactas de Android 9, la reproducción y la corrección de la colisión de nombres.

## Qué cambió respecto de 0.4

El TV conserva el perfil `gxlx2_p291_1g`, Android 9/API 28, la compilación original `ampere-userdebug 9 PPR1.180610.011 20250226 test-keys` y el kernel 4.9.113. `sys.boot_completed=1` confirma que el Android actual completó su arranque. Las 24 filas eMMC de `/proc/partitions` coinciden exactamente con las del informe 0.4. No hay evidencia de instalación ni respaldo original del TV.

El motivo de arranque pasó de `recovery` a `reboot,update`. En las nuevas capturas coinciden `ro.boot.bootreason`, `sys.boot.reason` y `persist.sys.boot.reason`. Esa coincidencia registra el motivo comunicado o conservado; no es una prueba independiente de ejecución de recovery. Android documenta que el motivo procede del cargador y puede ser refinado por el sistema. [AOSP: motivos de arranque](https://source.android.com/docs/core/architecture/bootloader/boot-reason).

La partición recovery de 24 MiB sigue presente. `/proc/cmdline` y `/cache/recovery/command` continúan denegados a UID2000. No se obtuvo el contenido del recovery interno ni el comando que pueda tener pendiente.

El pstore nuevo es legible: 32.756 bytes ASCII, sin bytes nulos ni bytes superiores a 127. Contiene el registro conservado de otro arranque, con tiempos de kernel entre 13397,710 y 13922,076 segundos, muy superiores al uptime actual. No es el antiguo fragmento corrupto de 0.4. Los patrones de ftrace y dmesg de ramoops figuran como ausentes o no accesibles.

## Secuencia que conserva el pstore

| Tiempo del kernel anterior | Observación |
| --- | --- |
| 13400,165 s | Se inicia watchdogd; empiezan mensajes de cierre de procesos y recursos de video. |
| 13400,618 s | Queda un proceso del grupo UID0 sin terminar tras el intento de cierre. |
| 13403,361 s | Queda un proceso del grupo UID1010 sin terminar. El UID no identifica por sí solo la función bloqueada. |
| 13404,739 s | HDMI recibe `avmute`. |
| 13404,840 s | El watchdog registra `reboot_notify: disable watchdog (event = 1)`. |
| 13428,886 s | Se registra una desconexión USB. No se identifica su causa ni se atribuye al Kingston por esa línea solamente. |
| Hasta 13922,076 s | El mismo registro continúa con timeouts SDIO CMD53: 517,24 segundos después del aviso de reinicio. |

No aparecen `Restarting system`, un nuevo inicio de kernel, una traza de panic ni la ejecución de recovery dentro del contenido conservado.

En el código público Amlogic/Khadas 4.9, el mensaje del watchdog se emite desde un callback registrado en la cadena de avisos de reinicio. `event=1` corresponde a `SYS_RESTART`, alias de `SYS_DOWN`. Esa cadena precede a `device_shutdown()` y al reinicio físico en `kernel_restart()`. La correspondencia ubica la fase alcanzada; el código de referencia no es una extracción del kernel instalado. [Controlador watchdog](https://github.com/khadas/linux/blob/khadas-vims-4.9.y/drivers/amlogic/watchdog/meson_wdt.c), [constantes de reinicio](https://github.com/khadas/linux/blob/khadas-vims-4.9.y/include/linux/reboot.h), [secuencia de reinicio](https://github.com/khadas/linux/blob/khadas-vims-4.9.y/kernel/reboot.c).

**Inferencia:** un bloqueo durante la preparación o el cierre del sistema es ahora la explicación favorecida. No se puede distinguir aún entre otro callback, cierre de un dispositivo u otra operación posterior. La ausencia de la siguiente marca de log no identifica por sí sola la instrucción exacta que falló.

Los timeouts SDIO y los intentos fallidos de abrir Bluetooth MediaTek también aparecen en los últimos 64 KiB del dmesg **actual**, mientras Android sigue funcionando. Son una pista relevante y no una demostración de causalidad. No acreditan falla de eMMC ni del pendrive, ni habilitan a afirmar que actualizar o desactivar el WiFi resolverá el reinicio.

## Fallo de recopilación de APK en 0.5

La actividad genérica de actualización se resolvió a Google Play Services. La selección también añadió el candidato conocido `com.droidlogic.otaupgrade`. `pm-path.txt` enumeró, en este orden:

1. El APK base de Google Play Services: **73.834.539 bytes**, omitido por exceder el límite individual de 33.554.432 bytes.
2. Tres APK divididos de ese mismo paquete, que sí se copiaron como `actualizador-2.apk`, `actualizador-3.apk` y `actualizador-4.apk`.
3. `/product/app/OTAUpgrade/OTAUpgrade.apk`, como quinta entrada.

El límite de cuatro entradas se contabilizó antes de decidir si cada archivo podía copiarse. Por eso la base de Google omitida también consumió una posición. Al alcanzar la quinta entrada se detuvo la etapa: **el APK de OTAUpgrade no llegó a copiarse**. Los tres APK divididos obtenidos no contienen el binario útil del actualizador local buscado. Tampoco se alcanzaron la copia de `otacerts.zip`, la recopilación posterior de configuración ni el cierre completo de la captura. Este fallo de alcance y orden pertenece al recopilador; no es una denegación del TV contra OTAUpgrade.

Sí se obtuvo del gestor de paquetes del **primer P291**, sin extrapolar el segundo TV:

| Campo | Resultado observado |
| --- | --- |
| Paquete | `com.droidlogic.otaupgrade` |
| Ruta | `/product/app/OTAUpgrade/OTAUpgrade.apk` |
| Versión | versionCode 2; versionName `2.0201411271418` |
| Identidad | UID1000, componente del sistema |
| Permisos | `android.permission.REBOOT` y `android.permission.RECOVERY`: `granted=true` |

Esto identifica un actualizador privilegiado real en el P291, pero no prueba cómo prepara el ZIP, qué certificados acepta ni si su ruta evita el atasco del reinicio. Para resolverlo falta su APK y el almacén público de certificados OTA de esta unidad. [AOSP: RecoverySystem Android 9](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-9.0.0_r1/core/java/android/os/RecoverySystem.java).

## Siguiente avance y límites

Al cerrar este análisis se está construyendo **Acceso USB 0.6**, un complemento de lectura para obtener el APK específico, los certificados y la configuración faltantes, y corregir la verificación de binarios evitando la colisión con el alias de mksh. **Todavía no fue entregado ni probado en el TV.** Su existencia como trabajo en curso no acredita una solución del reinicio ni autoriza a marcar completa la instalación.

No repetir el botón de reinicio 0.4, el ZIP vacío ni el formato del USB a partir de estos informes. El resultado útil siguiente es analizar los archivos concretos del actualizador del P291; después se podrá elegir una ruta sustentada. Permanecen pendientes el acceso efectivo a recovery, el respaldo original, la instalación interna y el primer arranque de TVBASE.

Actualización posterior: complemento0.6 copiado y verificado en el Kingston el7/9 a las00:22 ART. [Recibo](../../preparacion-usb/evidencia-06-estado.json). Esta entrega no altera los resultados de las dos capturas0.5 ni acredita la ejecución0.6 enTV.
