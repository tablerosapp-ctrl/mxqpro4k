# Update 0.1.2: cierre de Android y código real de BatteryStats

7/9/2026, actualizado con la pila obtenida a las 19:36. **El cierre está esperando al worker de BatteryStats, que espera una respuesta de WifiStateMachine; este último hilo está detenido esperando que retorne la llamada de arranque del HAL WiFi.** La dependencia se observa en una misma captura Java y nativa de `system_server` del primer P291.

Esta nota no acredita instalación, respaldo ni arranque de recovery. El análisis se realizó sobre archivos locales; la adquisición y la solicitud única de pilas las realizó el agente principal. Las trazas, identificadores, binarios extraídos y el lector acotado permanecen en `privado/`.

## Secuencia observada

`privado/update012-log-20260907-222712.txt`: 34349 bytes, 333 líneas, SHA256 `7b01ed835e85a730df67b2dd04540797ff41b688e9abf2f71a57bc5428d99a3f`.

| Hora del registro | Línea | Hecho |
| --- | --- | --- |
| 19:25:28.925 | 171 | El actualizador anuncia copia del ZIP 0.1.2 desde USB a `/data/cache/update.zip`. No equivale a verificar su hash interno. |
| 19:25:37.683–.727 | 174–175 | Entra en `updateWithBCB`. |
| 19:25:38.857–.858 | 177–179 | El ayudante recibe una orden que referencia `@/cache/recovery/block.map`. |
| 19:25:38.968 | 181 | `RecoverySystemService` informa que `setup bcb` terminó correctamente. |
| 19:25:39.281 | 184 | Comienza el broadcast de cierre. |
| 19:25:40.310 | 212 | Comienza el cierre de ActivityManager. |
| 19:25:40.510 | 239 | BatteryStats anuncia su escritura previa al apagado, en el mismo hilo de cierre que la línea anterior. |
| Hasta 19:26:56.399 | 240, 258, 308 | El mismo proceso del sistema sigue generando registros de recolección de memoria: 75,889 segundos después de la entrada en BatteryStats. |
| Hasta 19:27:12.374 | 333 | Siguen apareciendo registros de Android: ventana de 91,864 segundos desde esa entrada. |

En esta ventana no aparecen los siguientes anuncios de cierre de PackageManager, radios o preparación del contenido mediante uncrypt. El log por sí solo no distinguía entre la espera del worker, un bloqueo de estadísticas o una escritura posterior. La pila obtenida después resuelve esa duda para el instante capturado.

El `received 0` de la línea 180 es el acuse que el cliente entrega al ayudante; no es una observación de su código de salida. En AOSP 9, `setup-bcb` escribe la orden de arranque y devuelve estado 100; la creación de `block.map` mediante `uncrypt` es otra operación. Por ello el reconocimiento de BCB no demuestra un mapa válido ni la integridad de la copia interna. Referencias: [RecoverySystemService](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/RecoverySystemService.java) y [uncrypt](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/uncrypt/uncrypt.cpp).

La lectura posterior con el acceso root ya existente despejó también esos dos puntos: `/data/cache/update.zip` tiene **573082917 bytes y SHA256 `6c0c4307208c8d0e1a958a3fc6c790fa94021a850599985b0a41b340b821bb99`**, igual al ZIP 0.1.2 verificado; `uncrypt_file` referencia ese archivo, pero **`/cache/recovery/block.map` no existe**. Evidencia local: `privado/root-preparacion.txt`, `root-cache-contenido.txt` y `root-zip-interno-sha.txt`. La copia del ZIP está acreditada; su preparación como mapa para la orden BCB observada está incompleta.

## Pila contemporánea: cadena de espera confirmada

`privado/root-system-server-trace-20260907-193623-raw.txt`: 107301 bytes, SHA256 `af90d91809cf26af69b54dde9e91f455e999f9e00cb461ad2d8bb71ed7f9f94c`. La cabecera del TV marca 19:36:22; el recibo de la PC registra una SIGQUIT a las 19:36:23. No se invocó BatteryStats mediante Binder ni se solicitó un reinicio. La adquisición aceptada empleó salida binaria, marcador único de finalización y comprobación de hash/códigos. La transferencia anterior mediante shell añadió retornos de carro y se conserva separada como **no aceptada**.

| Hilo y líneas de la captura | Espera observada | Alcance |
| --- | --- | --- |
| Hilo de cierre, L1612–1624 | `ShutdownThread.run` → `ActivityManagerService.shutdown` → `BatteryStatsService.shutdown` → `syncStats` → `awaitUninterruptibly` → `FutureTask.get`/`awaitDone` → aparcamiento del hilo. | El cierre aún espera el Future; no llegó a la escritura final de estadísticas que sigue a `syncStats`. |
| `batterystats-worker`, L325–346 | `updateExternalStatsLocked` → `WifiServiceImpl.requestActivityInfo` → `reportActivityInfo` → `getSupportedFeatures` → `WifiStateMachine.syncGetSupportedFeatures` → `WifiAsyncChannel`/`AsyncChannel.sendMessageSynchronously` → `Object.wait`. | El worker está esperando una consulta síncrona al hilo WiFi antes de poder terminar su trabajo. |
| `WifiStateMachine`, L807–829 | Configuración de interfaz cliente → `WifiNative.startHal` → `WifiVendorHal.startVendorHal` → `HalDeviceManager.startWifi` → `IWifi$Proxy.start` → `HwRemoteBinder.transact` → `IPCThreadState.waitForResponse`/`ioctl`. | Su bucle de mensajes está ocupado esperando el retorno del HAL, por lo que no despacha la consulta que espera BatteryStats. Mantiene los bloqueos de HalDeviceManager, WifiVendorHal y WifiNative que la captura muestra adquiridos. |
| `WifiService`, L791–799; `WifiScanningService`, L837–845; `WifiP2pService`, L853–861 | Sus respectivos bucles esperan mensajes mediante `epoll`/Looper. | No todos los hilos llamados WiFi están en la misma espera. Su estado no demuestra que la radio funcione. |

El worker está ejecutando `WifiServiceImpl` **en su propio hilo**, como muestra la pila. Por eso la declaración AIDL `oneway` no garantiza aquí un retorno inmediato: la llamada local entra en una consulta síncrona. Todavía no llegó a los `awaitControllerInfo()` de 2000 milisegundos. Esos plazos no limitan esta espera anterior.

```mermaid
flowchart LR
  cierre[Hilo de cierre] -->|Future sin plazo| stats[BatteryStats worker]
  stats -->|consulta síncrona de capacidades| wifi[WifiStateMachine]
  wifi -->|HIDL start: espera respuesta| hal[HAL WiFi remoto]
  hal -. punto interno aún sin pila .-> driver[HAL / driver]
```

La causa inmediata del atasco de cierre queda observada. **El punto exacto dentro del proceso HAL o del driver sigue sin identificarse:** esta captura pertenece a `system_server`, no al servidor HAL remoto. Tampoco prueba por sí sola cuánto tiempo lleva esa llamada concreta, ni que su causa sea idéntica al panic de Bluetooth/WiFi de otro arranque. No corresponde denominarla un deadlock circular demostrado: la evidencia muestra una cadena de esperas.

## Confirmación en el código adquirido del P291

La adquisición de `/system/framework/oat/arm/services.vdex` tiene 9680428 bytes y SHA256 `b051439a45d8e7d12839df445a43b0b97c4a9db267a2158a5fd8a5e2aa741649`; el responsable de la adquisición confirmó coincidencia entre lectura previa, copia en PC y lectura posterior. El análisis local volvió a calcular el mismo hash.

Es VDEX 019 con sección DEX 002 y un **CompactDex 001**, cuyo comienzo está en el byte 40. No es un DEX estándar. `dexdump` 37 rechazó la copia derivada con código 1. Se leyó su estructura CompactDex siguiendo los formatos oficiales, sin cambiar su cabecera, ejecutar sus binarios ni inventar referencias para instrucciones optimizadas.

El lector acotado resolvió 11 métodos, sus instrucciones y manejadores de excepciones. Dentro de esos métodos no quedaron referencias optimizadas sin resolver; esto no significa que se haya descompilado o validado todo el archivo. Los desplazamientos siguientes son bytes desde el comienzo del VDEX:

| Método real | Desplazamiento | Resultado de la lectura |
| --- | --- | --- |
| `ActivityManagerService.shutdown(int)` | 2304202 | El plazo recibido se entrega a `ActivityStackSupervisor`; después se llama a BatteryStats y posteriormente a ProcessStats. No existe aquí un plazo global que envuelva todas esas operaciones. |
| `BatteryStatsService.shutdown()` | 2619270 | Registra el mensaje observado, llama a `syncStats("shutdown", 31)`, entra al bloqueo de estadísticas y llama a `shutdownLocked()`. Finalmente cierra el worker. |
| `BatteryStatsService.syncStats()` | 2619360 | Obtiene el Future de `scheduleSync()` y lo entrega a `awaitUninterruptibly()`. |
| `BatteryStatsService.awaitUninterruptibly()` | 2610864 | Invoca `Future.get()` sin plazo. El manejador de `InterruptedException` vuelve a esa llamada; el de `ExecutionException` retorna. |
| `BatteryExternalStatsWorker.awaitControllerInfo()` | 2605608 | Pasa 2000 milisegundos a `awaitResult()` y captura `TimeoutException`. Ese plazo corresponde a la respuesta del controlador, no a todo el trabajo ni al Future exterior. |
| `BatteryExternalStatsWorker.updateExternalStatsLocked()` | 2607426 | Además de pedir datos de radios, llama a actualizaciones de CPU, wakelocks, ancho de banda del kernel, RPM y estadísticas de red. La espera no puede atribuirse solamente a Bluetooth o WiFi con este código estático. |

Queda confirmada la espera sin límite en el código de este P291, antes inferida por comparación con AOSP. La pila contemporánea acredita además que el cierre está detenido en esa ruta y que el worker espera la consulta WiFi descrita arriba. La presencia de otras llamadas en el código no demuestra que se estén ejecutando en este instante.

Referencias del formato: [CompactDex](https://android.googlesource.com/platform/art/+/android-9.0.0_r1/libdexfile/dex/compact_dex_file.h), [direcciones de datos](https://android.googlesource.com/platform/art/+/android-9.0.0_r1/libdexfile/dex/dex_file.h) y [tabla de instrucciones](https://android.googlesource.com/platform/art/+/android-9.0.0_r1/libdexfile/dex/dex_instruction_list.h). Comparación de comportamiento: [BatteryStatsService](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/am/BatteryStatsService.java) y [BatteryExternalStatsWorker](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/am/BatteryExternalStatsWorker.java).

La evidencia reproducible privada es `leer-cdex-acotado.py`, SHA256 `e5d0577f6a682f88e030f00890e44d8807382962656d717d7b92f0694307cdb8`, y `services-p291-metodos-acotados.json`, 99630 bytes, SHA256 `409359741533989156bbd86e14368fcd39e1dda6b539a4b6d2454c0d43a07a04`. El JSON conserva llamadas, instrucciones y excepciones; no es una reconstrucción de fuentes Java ni un verificador integral de VDEX.

## Implicaciones para continuar

La única solicitud de pilas mediante [ART SignalCatcher](https://android.googlesource.com/platform/art/+/android-9.0.0_r1/runtime/signal_catcher.cc) ya dio el resultado buscado: no hace falta repetirla ni consultar BatteryStats para confirmar esta cadena. Los ANR antiguos de Bluetooth quedan como antecedentes de otro intervalo.

1. Si se necesita localizar el bloqueo más abajo, la siguiente evidencia relevante es la pila del servidor HAL WiFi y de sus hilos de kernel, con la identidad del proceso comprobada y una lectura acotada. La pila Java obtenida no contiene esa información. La CLI [debuggerd de AOSP 9](https://android.googlesource.com/platform/system/core/+/android-9.0.0_r1/debuggerd/debuggerd.cpp) no ofrece `-j` y su solicitud nativa usa plazo interno cero; no debe tratarse como una lectura garantizada de duración corta.
2. Antes de una vía que escriba memoria interna, aprovechar el acceso existente para comprobar particiones y obtener los respaldos críticos. Este análisis no los considera realizados.
3. Para conservar la ruta BCB que referencia `block.map`, falta preparar y verificar ese mapa. Tener el ZIP correcto y `uncrypt_file` no sustituye ese paso. Un reinicio directo de ADB omite el cierre Java en AOSP 9, pero realiza `sync()`, no crea el mapa y conserva las posibles esperas del kernel; por ello no resuelve por sí solo los dos problemas observados. Referencia: [servicio de reinicio ADB](https://android.googlesource.com/platform/system/core/+/android-9.0.0_r1/adb/services.cpp).

No se propone aquí matar hilos, reiniciar a la fuerza ni escribir una orden BCB distinta. Terminar un cliente tampoco garantiza cancelar el trabajo de BatteryStats o del HAL. El objetivo de conservar WiFi en la plataforma debe tratarse separadamente de resolver este bloqueo concreto de su implementación actual.
