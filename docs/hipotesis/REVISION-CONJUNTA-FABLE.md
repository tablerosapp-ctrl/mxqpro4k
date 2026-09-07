# Revisión de los aportes de Fable · 7/9/2026

**Actualización posterior:** [captura física0.8](../../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md). Se observaron los problemas de servicios que se buscaban;25archivos de datos sellados son válidos, pero el cierre llegó vacío. Android original activo. No se demuestra todavía qué bloqueó Update; LAN del primerP291 ofrecida para observación en vivo. Las decisiones de abajo documentan la revisión previa a esa captura.

Se recibieron tres documentos en `mxqpro4kpropuestasastra.zip` del Kingston: entrega a Astra, PROP-08 y PROP-12. El ZIP tiene 19.663 bytes, SHA256 `49f9c62ebbc462fd6e52a799dac2d72aab1d1823704aef452ba34538b262b0e8`; CRC y copia USB→PC comprobados. Los originales quedan privados, íntegros. [Adquisición y fuentes](../../diagnostico/fable-20260907/resumen-saneado.json).

**Conclusión de Codex:** el aporte más útil es observar el intento ya ocurrido y acotar los servicios implicados. La espera de BatteryStats es un candidato concreto, no una causa identificada. No hay una vía nueva de flasheo probada. La coincidencia entre nuestras hipótesis no reemplaza una captura del mismo intento.

## Qué adoptamos

| Aporte recibido | Decisión y avance |
| --- | --- |
| Separar el cierre Java del OEM y la petición directa ADB | Adoptado; coincide con [H1](H1-RESULTADO-CODEX.md). El pstore anterior solo describe la segunda vía. |
| PROP-09: registros del arranque anterior, pstore y espacio | Implementado en Acceso USB0.8. Intenta leer `logcat -L`, console/pmsg y df; conserva permisos denegados y límites. Resultado físico pendiente. |
| PROP-13 fase1: consultas WiFi, Bluetooth y BatteryStats con plazo | Implementado en0.8. Un timeout indica que esa consulta no terminó; no identifica por sí solo la espera del apagado. |
| PROP-13 fases2/3: apagar radios y ensayar otro reinicio | Diferidas. Primero leer0.8 y justificar una intervención específica. No cambiar radios ni reiniciar en esta captura. |
| PROP-12: actualización propia, manifiestos firmados y canales separados | Adoptado como dirección de C-GESTION/M6; necesita las correcciones de abajo. No resuelve el acceso inicial al recovery. |
| PROP-08: vía Amlogic fuera del cierre de Android | Mantener como investigación alternativa. No se entregó una herramienta ni imagen de rescate y no está validado el modo USB/lectura del P291. Pendrive y cable hacia PC son vías diferentes. |
| PROP-10: medir multimedia | Se mantiene para M3. El usuario ya probó dos VP9, alfa y canvas en el sistema actual; una suite comparable servirá al instalar nuestra base. |
| PROP-11: ZIP pequeño sin cambios para repetir Update | No se adopta ahora. El ZIP vacío y la ROM completa ya llegaron al mismo2%; otro paquete no instrumenta el cierre por sí solo. |

## Qué corregimos al contrastarlo con las fuentes

**BatteryStats tiene una espera sin límite, pero falta localizar qué la retiene.** En Android9, `shutdown()` llama a `syncStats()` y termina esperando un Future con `get()` sin timeout. El trabajador puede estar ocupado o bloqueado antes de completar la tarea. Sin embargo, las solicitudes de estadísticas WiFi y Bluetooth están declaradas `oneway`, y la espera explícita de sus respuestas en el trabajador tiene timeout de2s. La posibilidad de un bloqueo no queda eliminada; tampoco se demuestra el mecanismo síncrono descrito en el aporte. Fuentes: [BatteryStatsService](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/am/BatteryStatsService.java), [BatteryExternalStatsWorker](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/am/BatteryExternalStatsWorker.java), [IWifiManager](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/wifi/java/android/net/wifi/IWifiManager.aidl), [IBluetooth](https://android.googlesource.com/platform/system/bt/+/android-9.0.0_r1/binder/android/bluetooth/IBluetooth.aidl). Son referencias AOSP; no se extrajo el framework del TV.

**El2% no confirma archivos persistentes.** La llamada Java de referencia favorece una espera en el cierre de ActivityManager, pero la actualización del diálogo es asíncrona y puede quedar congelada. No leímos `uncrypt_file`, `block.map` o BCB de este intento. La ejecución observada de Copying tampoco verifica la copia interna. La secuencia del APK conocido permite inferir intención, no acreditar bytes persistidos. Se mantiene [H2](H2-PREPARACION-RECOVERY.md) abierta.

**Un servicio lento no basta para probar causalidad.** `dumpsys batterystats` puede esperar locks distintos a los que afectan el cierre; una lectura rápida después de arrancar no descarta el bloqueo anterior. Un timeout de WiFi/BT es evidencia auxiliar. La ausencia de registros anteriores también puede deberse a permisos, rotación o soporte de pstore. `COMPLETO.txt` significa recorrido y archivos comprobados, no que todos los servicios respondieron.

**Cambiar `ota-type` no repara la entrada.** El paquete0.1.1 ya contiene imágenes completas y un `update-binary` propio. En recovery tradicional AOSP9 se extrae y ejecuta ese binario; renombrar metadatos no hace que el TV entre en recovery ni prueba que pueda leer el USB. No fabricamos otra variante del ZIP sin un rechazo concreto. [Instalador AOSP9](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/install.cpp).

**Burning Tool no es aún un respaldo acreditado.** No se aportó una lectura de esta unidad ni una prueba de restauración. Reconocer el dispositivo en modo quemado, leer particiones y restaurarlas son tres capacidades que deben comprobarse separadamente. Tampoco se debe combinar bootloader/DTB/vbmeta propios y cinco particiones candidatas suponiendo compatibilidad automática. La capacidad de arrancar por USB directo depende del cargador instalado, no del nombre de un archivo.

## Contrato implementado en0.8

- Solo primer P291, API28 y UID2000; conexión existente a localhost. Ningún root ni cambio de autenticación.
- Una carpeta nueva por ejecución: `TVBASE-postintento-...`; no sobrescribe reportes.
- Once etapas: creación y comprobación de timeout, identidad/autocontrol SHA, pstore, log anterior, log actual filtrado, WiFi, Bluetooth, batería, espacio, WebView y comprobación final.
- Cada consulta conserva salida, código de retorno, uptime inicial/final, bytes y marca de truncamiento. Los archivos se sellan y se vuelven a leer con SHA64hex y autocontrol `abc`.
- Pstore: hasta cuatro archivos console/pmsg de2MiB cada uno, tamaño y SHA de origen antes/después y de copia. Los no legibles o de tamaño no admitido se declaran.
- Límites de8–12s para consultas directas y90s para la espera del cliente por etapa. No se lanza otra consulta tras un error del protocolo.
- `toybox timeout -s KILL` limita al proceso hijo directo; no garantiza interrumpir una espera de kernel no interrumpible. Cerrar el socket tampoco garantiza terminar ese proceso remoto. El preflight comprueba el comando en el propio TV antes de crear el informe. [Fuente timeout de Android9](https://android.googlesource.com/platform/external/toybox/+/android-9.0.0_r1/toys/other/timeout.c).
- No se pulsa Update, no se solicita reinicio, no se cambia WiFi/BT y no se escribe BCB/particiones. La lectura y los hashes no acreditan persistencia frente a corte eléctrico. Los servicios consultados pueden realizar trabajo ordinario de diagnóstico.

[Fuentes propias](../../rom-simplificada/componentes/acceso-usb-0.8/generar-scripts.py) · [Pruebas PC](../../rom-simplificada/instalador/EVIDENCIA-TESTS-0.8.json) · [Entrega y limpieza USB](../../preparacion-usb/postintento-08-estado.json) · [Pasos de uso](../../rom-simplificada/INSTALACION-USB.md).

## Condiciones del actualizador futuro

Se aceptan cuatro canales separados: ROM, motor web, APK y contenido, con autenticación del manifiesto, compatibilidad por placa, hashes, bitácora y recuperación prevista. Antes de implementarlo hay que ajustar PROP-12:

1. `/system` y otras particiones del sistema están montadas durante Android. La exigencia de desmontaje corresponde al entorno que realmente las escribe; no puede ser un preflight general del Android en uso.
2. Preparar block.map mediante el flujo AOSP usa `uncrypt_file`. No puede prometerse que ese archivo solo exista después de la preparación. Deben documentarse el orden, BCB y los efectos persistentes de cada estado.
3. Conservar una APK anterior no garantiza downgrade: intervienen firma, versionCode, privilegios y migraciones de datos. Rollback de APK, motor y ROM requiere mecanismos y ensayos distintos.
4. Sin A/B, “PREPARED” no basta para concluir que no queda una orden de arranque persistente. Tras una interrupción se debe reconciliar el estado real antes de reintentar.

## Cómo cambia la siguiente decisión

Si0.8 aporta registros del intento reciente con una espera identificable, se podrá plantear una intervención dirigida y su control. Si conserva el mismo pstore viejo o accesos denegados, se registrará ese límite; no se presentará como nueva evidencia ni se pedirá repetir Update sin instrumentación. Un dump normal de servicios solo describe el arranque actual. La entrada física Amlogic queda como alternativa que necesita evidencia específica del P291 y un procedimiento verificable de lectura/restauración.

El retorno a Android tras el último2% todavía no fue confirmado por el usuario. La captura0.8 se ejecuta únicamente cuando Android está disponible. No hay ROM instalada ni respaldo del TV confirmado.
