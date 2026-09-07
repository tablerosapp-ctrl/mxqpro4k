# Primer P291: observación por LAN

**Actualización final de esta revisión:** root incorporado confirmado y12particiones originales verificadas. Elbloqueo actual tiene trazaJava, elZIP se preservó fuera de su rutaactiva y0.1.2 queda enrevisión por diferencias dearranque/firma. [Resultado de root](ROOT-RESULTADO.md) · [Respaldo](RESPALDO-resumen-saneado.json) · [Recoveryoriginal](RECOVERY-ORIGINAL.md). Los apartados siguientes conservan la secuencia de descubrimiento.

7/9/2026. La conexión ofrecida por el usuario permitió leer el **primer P291**, con DT `gxlx2_p291_1g`, API28 y UID2000. Android conserva la build original de febrero2025. La interfaz de esta conexión es `eth0`. La IP, identificadores y registros completos permanecen en `privado/`, fuera del repositorio público.

No hay instalación de TVBASE ni respaldo original confirmado. La instalación final continúa prevista desde pendrive; esta conexión sirve para diagnosticar el bloqueo.

## Lo nuevo observado

El pstore contiene una excepción fatal del kernel en la ruta que coordina el reinicio de Bluetooth con WiFi. No es solamente un timeout de una consulta:

| Referencia en `privado/pstore-lan.txt` | Uptime | Resultado |
| --- | --- | --- |
| L257–270 | 18560,005–18560,101s | SDIO CMD53, lectura `ret:-110`, registros `0xffffffff` y fallo de adquisición del controlador. |
| L271 | 18560,108022s | `btmtk_sdio_start_reset_dongle_progress`, solicitud de reset. El texto «user mode» del driver no identifica al usuario humano ni una orden de Codex. |
| L288–305 | 18560,280–18560,370s | Notificación BT→WiFi; PC en `glResetTrigger.part.1+0xe8/0x1e8 [wlan_mt7663_sdio]`. |
| L366–374 | 18560,371–18560,409s | Cadena del hilo `btmtk_main_serv` y `Kernel panic - not syncing: Fatal exception`. |
| L416–417 | 18561,220–18566,224s | Reinicio automático anunciado a cinco segundos; razón12. |

La cadena registrada es `btmtk_service_main_thread` → `btmtk_sdio_start_reset_dongle_progress` → `btmtk_sdio_notify_wlan_remove_start` → `BT_rst_L0_notify_WF_step1` → `glResetTrigger.part.1`.

Esto es compatible con el reinicio espontáneo que comunicó el usuario. La ventana guardada no permite vincular su hora inequívocamente con ese evento. Antes de ese aviso, Codex solo había realizado descubrimiento TCP en la LAN y operaciones del conector ADB de la PC: **no envió una orden de reinicio al TV**. La propiedad `sys.boot.reason=reboot,update` no invalida el panic explícito ni acredita un nuevo Update.

El archivo tiene32756B y SHA `ba9d21a64e7e1c6e088745365ac6c14fd71f9acb62c386d6c311c73e077d2e13`. Su primera línea está truncada. Es distinto del pstore0.8, que no contenía un panic ni el intervalo de cierre. Los conteos de SDIO entre ventanas de distinta duración no miden una mejora.

## Esperas Bluetooth del arranque actual

La entrada ya existente de DropBox `system_app_anr`, 7/9 a18:49:00, corresponde a `com.android.bluetooth`, PID5797. Se leyó una sola entrada mediante una consulta con plazo; no se generó una traza nueva. Sus73173B tienen SHA `18ce5aafb44877aaa7468479ac8a0e44b298d8266a0b18e6cf02623aabfadefa`.

- Hilo principal, L173–195: `AdapterService.onUnbind` → `cleanupNative` → `clean_up_stack` → `semaphore_wait`/`eventfd_read`.
- `stack_manager`, L460–473: `event_start_up_stack` esperando `future_await`.
- `hci_thread`, L516–540: inicialización del HALBluetooth mediante HIDL, esperando respuesta Binder.

Se observan tres ANR sucesivos a380,937s,408,824s y436,626s. El manager intenta reiniciar el servicio aunque su estado visible seaOFF: registra `mEnabled is true; restarting`, timeouts de enlace y nuevas aperturas. A18:53 la preferencia `bluetooth_on` seguía en1; el dump mostrabaOFF y servicio desconectado. Esto explica por qué **OFF en esa pantalla no demostraba que la radio estuviera desactivada por configuración**.

La instantánea de procesos muestra WiFiHAL y `btmtk_main_serv` enD; también un hilo HDMI-CEC. BatteryStatsWorker estáS. WCHAN0 no revela el lugar de espera de esos procesos; no demuestra normalidad ni una espera concreta. La traza ANR de Bluetooth no incluye una pila útil de system_server/BatteryStats. No se volvieron a pedir los dumpsWiFi/BatteryStats que habían agotado su plazo.

## Intervención dirigida

Se realizó una sola desactivación Bluetooth mediante la API normal de Android, independiente de Update, a19:01:29ART. El ajuste original era1 y pasó a0. La API devolviótrue; el manager registró `APPLICATION_REQUEST` del auxiliar. La solicitud y el cierre se guardaron; el TV conservó el mismo arranque y la conexiónEthernet. A los45s no aparecen nuevos reiniciosBluetooth en el registro del manager. Falta una ventana mayor: esto no afirma que el driver o recovery quedaron reparados.

En el P291, `svc help` ofreceBluetooth, pero `com.android.shell` carece de `BLUETOOTH_ADMIN`. Por ello no se modifica el permiso del shell ni se llama a transacciones Binder por número. Una APK corriente puede declarar los permisos normalesBluetooth y ejecutar `BluetoothAdapter.disable()`. La aceptación de la solicitud, el estadoOFF y el cese del ciclo son comprobaciones distintas.

Fuentes de referencia Android9: [orden svc](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/cmds/svc/src/com/android/commands/svc/BluetoothCommand.java), [API del adaptador](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/core/java/android/bluetooth/BluetoothAdapter.java), [manager y persistencia del ajuste](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/BluetoothManagerService.java). Son referencias; la respuesta física se registra por separado.

Auxiliar instalado: [ControlBluetooth0.1](../../rom-simplificada/componentes/control-bluetooth-0.1/README.md),24979B,SHA `6d7c866478c859ac3948a1132aa75ceebc13d059c32098aaecc0cbb82dbf031f`. Se revalidó P291 antes de instalarlo. Solo declara los dos permisos normales deBluetooth, sin red, root ni comandos de reinicio. No se restaurará Bluetooth automáticamente: el usuario acaba de pedir prescindir deél.

El cambio de alcance queda en REQ-13/PROP-14/ADR-21: varianteROM nueva sin pila/HAL/móduloBluetooth operativo, manteniendoWiFi y sin modificar0.1.1. Esto no implica retirar todos los auxiliaresBluetooth compilados dentro del kernel ni alterar pines compartidos delDT.

La [comparación de radios del TV y las ROM](COMPARACION-RADIOS.md) reúne hashes, compilaciones de kernel y versiones de firmware. Los cuatro binarios leídos del TV difieren del candidato; 0.1.2 retira el módulo Bluetooth y conserva WiFi y boot del candidato. Estas diferencias no demuestran una reparación ni compatibilidad física.

## Límites y siguiente decisión

El panic acota una avería real al controlador combinado de radios; **no demuestra todavía que sea la causa del2% OEM**. Tampoco prueba BCB, block.map, ejecución de recovery, integridad de la copia interna delZIP o compatibilidad física del candidato. Una ROM con menos aplicaciones no acredita reparar ese controlador.

Conservar esta evidencia y observar la intervención antes de elegir otro intento. No repetir Update/recovery en bucle, no habilitar root y no confundir los datos delP271 con los delP291. La herramienta temporal de identificación LAN de la PC recibió la dirección delTV y terminó; no cambió reglas de firewall.

## Resultado posterior: el ajuste solo no alcanzó

A los164s de desactivar Bluetooth apareció otro ANR y Android inició un proceso de reemplazo. El manager mantuvo la preferenciaOFF y pidió apagarlo, pero aún había trabajo anterior pendiente. A19:06:50ART se ejecutó una vez `pm disable-user --user 0 com.android.bluetooth`: devolvió `disabled-user` y una lectura posterior confirmó el paquete en la lista de inhabilitados. Su proceso dejó de aparecer. La operación no cambia el permiso del shell ni modifica WiFi; para revertirla haría falta habilitar expresamente ese paquete, además de la preferencia, algo que no se hará automáticamente.

El usuario realizó un apagado físico de10s y confirmó el menú Android. La lectura de19:09:50 muestra otro bootID y63,60s de actividad; preferenciaBluetooth0 y paquete inhabilitado persistieron. No aparece el proceso `com.android.bluetooth`, pero sí el HAL de fábrica, `btmtksdio` cargado y `wlan_mt7663_sdio` en estadoLoading. El hilo `btmtk_main_serv` y WiFiHAL siguen enD. Por tanto, no se declara reparado el cierre ni recuperadoWiFi. Los tiempos negativos de algunas líneas tempranas del log reflejan el cambio del reloj durante el arranque; no se usan como duración de la prueba.

Una reconsultaBatteryStats fue rechazada por la revisión automática porque podía dejar más trabajo bloqueado. No llegó a ejecutarse. Se usaron los registros existentes, lista de procesos y estado persistido; no se intentó eludir ese rechazo mediante otra herramienta.

## ROM sin Bluetooth y ruta de entrada

La [ROM0.1.2](../../rom-simplificada/SIN-BLUETOOTH-0.1.2.md) ya está construida, firmada y [copiada/leída enKingston](../../preparacion-usb/rom-012-estado.json). El usuario pasó el pendrive alTV. No equivale a una instalación; el intento posterior y su resultado se registran abajo.

El usuario informa un switch interno que conserva su posición y probó ambas posiciones tanto al conectar alimentación como con Android funcionando, sin efecto visible. No se dará por confirmado que sea un botónrecovery ni se repetirá ese procedimiento. La documentación de [CoreELEC sobre entradas Amlogic](https://wiki.coreelec.org/coreelec:ceboot) describe botones y otros métodos dependientes del equipo; no identifica este switch ni prueba que el P291 implemente esa vía.

Se preparó una captura pasiva con [capturar-log.py](../observacion-lan/capturar-log.py): un solo flujo de mensajes, máximo600s/8MiB, sin ordenarUpdate, reinicio o consultaBatteryStats. El intento OEM posterior tuvo Bluetooth inhabilitado desde el arranque y observación por LAN. Es una condición nueva que permite contrastar la hipótesis, no una garantía de superar2%. Una desconexiónADB no se clasificará como instalación ni entrada a recovery.

## Intento OEM0.1.2 observado por LAN

El usuario confirmó que ve2% tras seleccionar la ROM0.1.2. El registro completo recuperado del búfer a19:27:12ART contiene la transición real, aunque ocurrió entre el fin de la primera captura en vivo y el inicio de la segunda. Esa discontinuidad se conserva: la evidencia de la transición procede de la lectura del búfer, no de un flujo continuo.

| Hora ART, 7/9 | Observado en el registro del P291 |
| --- | --- |
| 19:25:38.857 | uncrypt recibe `--update_package=@/cache/recovery/block.map` y locale. |
| 19:25:38.968 | RecoverySystemService informa éxito de setupBCB. |
| 19:25:39.281 | ShutdownThread envía el broadcast de cierre. |
| 19:25:40.310 | El hilo de cierre entra a ActivityManager. |
| 19:25:40.359 | Ese mismo hilo registra el cierre de AppOps. |
| 19:25:40.510 | Ese mismo hilo registra «Writing battery stats before shutdown...». |

Luego siguen mensajes de Android hasta19:27:12.374,91,864s después, sin marcas de cierre de PackageManager ni del procesamiento del paquete. El usuario ve2%; no se ha instalado la ROM. La preferencia y la aplicaciónBluetooth estaban inhabilitadas desde el apagado físico anterior, pero el módulo del kernel seguía cargándose. **Este cambio en Androidoriginal no evitó el2%; la varianteROM sin móduloBluetooth todavía no se ejecutó.**

Una instantánea posterior encuentra el hilo de cierre en estadoS y el mismo bootID. Su stack está denegado; WCHAN0 no identifica dónde espera. Los metadatos del ZIP interno, block.map y cache/recovery también están denegados. El transporte ADB devuelve0 aun con esos textos: se registran como denegaciones, no lecturas válidas. No se consultó BatteryStats otra vez ni se alteraron permisos.

El acuse de setupBCB **no verifica la copia interna del ZIP, el mapa de bloques, su persistencia ni la aceptación del cargador**. Ese uncrypt corresponde a prepararBCB; no debe confundirse con el procesamiento del paquete que genera el mapa. No saltar directamente a reinicio suponiendo que esa preparación terminó.

Se obtuvo únicamente el VDEX de servicios instalado,9680428B,SHA `b051439a45d8e7d12839df445a43b0b97c4a9db267a2158a5fd8a5e2aa741649`, con hashes antes/PC/después iguales. Permite contrastar el framework real; no es un respaldo delTV. Su formatoVDEX019 contiene CompactDex001, por lo que no basta tratarlo como unDEX ordinario. Los binarios y recibos originales permanecen privados.

La herramienta de captura incorpora ahora una fecha inicial opcional para recuperar mensajes del búfer al renovar una ventana y añade los tags BatteryStats/AppOps. El cambio solo afecta capturas futuras; no rellena retrospectivamente los flujos originales.


## Actualización con root autorizado

Elusuario pidió explorarroot y el su existente devolvióUID0. Las nuevaslecturas pruebanZIPinterno correcto ymapa ausente. La trazaJavaactual localiza lacadena de espera hastaIWifi.start. [Resultado de root y respaldo](ROOT-RESULTADO.md) · [Análisis detallado](ANALISIS-UPDATE-012.md). Esto reemplaza laslimitaciones deacceso y lacausalidad pendiente de losapartadosprevios; no equivale ainstalación nirespaldo finalizado.

## Copia interna retirada del intento pendiente

Después de detectar las diferencias dearranque/firma y del pedido delusuario de decidirantesdeforzar, se preservó elZIP como `/data/cache/TVBASE-0.1.2-preservada-no-instalar.zip`. Se comprobó antes que noexistíanblock.map ni un proceso uncrypt activo y que eltamaño/hash eran loscorrectos. Elrenombrado terminó con código0; la rutaactiva `/data/cache/update.zip` quedó ausente y elarchivo conservado volvió a verificarse por SHA. No se borró elZIP, no seescribieronboot/system/vendor ni sepidióreinicio.

Esto retira elarchivo que consumiría elintento OEM si laespera se liberara. **No cancela elhiloJava ni limpiaBCB**: laordende boot-recovery y uncrypt_file siguenreferenciando lapreparación anterior. ElTVpuede seguirmostrando2%; no presentarlo como cancelacióncompletadelarranque ni indicaruncorte asumiendoBCBlimpio. Elpendrive yla releaseenPC permanecenintactos.
