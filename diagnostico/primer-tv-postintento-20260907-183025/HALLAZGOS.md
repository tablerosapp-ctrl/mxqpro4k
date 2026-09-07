# Captura física0.8 · servicios bloqueados y cierre USB incompleto

Adquirida el7/9/2026 a las18:30 ART del Kingston identificado, sin modificarlo. Carpeta `TVBASE-postintento-ecd4e0799a9d47f2a0eec3a0300bc6fd`;63archivos copiados a almacenamiento privado de esta PC y comparados con una segunda lectura del USB. [Manifiesto y análisis saneados](resumen-saneado.json). La fecha2020 del TV no es una referencia cronológica fiable.

**Resultado:** los25archivos de datos exigidos presentes tienen SHA válido; etapas1–9 y autocontrol `abc` válidos. Los tres archivos finales existen pero tienen0bytes: `COMPLETO.txt`, su `.sha256` y `etapa-10.ok`. La captura se clasifica **parcial por cierre**, aunque los informes útiles pueden analizarse por su verificación individual. No convertir la existencia del nombre COMPLETO en éxito.

El usuario confirmó que la APK indicó finalización antes de retirar el USB. No atribuirlo a que interrumpió la captura. 0.8 comprobaba lectura, pero no exigía sincronización del almacenamiento ni desmontaje antes de anunciar éxito. Eso deja una brecha real de persistencia: lectura de caché y lectura después de mover el USB son garantías distintas. No se demostró el mecanismo exacto que dejó esos tres archivos vacíos. Se conservan sin rellenarlos ni reconstruir un supuesto cierre original. No repetir0.8 para obtener los mismos datos.

## Observaciones del primer P291

| Dato | Resultado observado | Qué permite concluir |
| --- | --- | --- |
| Android/identidad | API28, UID2000shell, build `ampere-userdebug 9 PPR1.180610.011 20250226 test-keys`; uptime17761,63s | Android está activo y conserva el sistema original. El instante/ciclo exacto que lo devolvió no queda identificado. |
| WebView | `com.android.chrome`70.0.3538.80, multiproceso desactivado | No se está usando Chrome138 de nuestra ROM. |
| WiFi | Estado «enabling», interfaz nula, `mIfaceIsUp=false`; dump parcial con timeout5000ms | La inicialización no llegó a una interfaz operativa y la consulta no terminó. |
| BatteryStats | Solo aviso de timeout5000ms, sin estadísticas | No completó el dump; no equivale a estadísticas vacías normales. |
| Bluetooth | EstadoOFF, servicio no conectado,21entradas recientes de RESTARTED | El estado OFF no basta para afirmar que la actividad de Bluetooth haya cesado. |
| Log actual | Seis ANR de `com.android.bluetooth/.btservice.AdapterService` en140,477s, seguidos por terminaciones y nuevos procesos | Hay un ciclo de servicio que no responde y se reinicia durante Android normal. Empieza antes de instalar/abrir0.8. |
| Log anterior | `logcat read failure`, retorno1 | No se obtuvo ese registro; no hay evidencia del punto exacto de cierre Java del intento OEM. |
| Espacio | /data1.294.228KiB libres; /cache1.066.800KiB libres | No están llenos en esta captura. No verifica tamaño/hash del ZIP interno ni espacio durante el intento previo. |

WiFi y BatteryStats tardaron5,31s y5,30s respectivamente; ambos devolvieron **código de proceso0 pero texto DUMP TIMEOUT**. AOSP9 permite esta combinación: imprime el error y `Dumpsys::main()` retorna0. Por eso el analizador offline clasifica el contenido además del código. La duplicación del mensaje/NUL coincide con las dos rutas de impresión del timeout en esa referencia y no invalida por sí sola los SHA. [Fuente AOSP9](https://android.googlesource.com/platform/frameworks/native/+/android-9.0.0_r1/cmds/dumpsys/dumpsys.cpp), SHA `234299baccbebf19372a46176b2094d28ec29c7bee6760bf31dd5e5a7c2aa7aa`.

El dump de Bluetooth indica0crashes mientras el log contiene6ANR. Son contadores de fenómenos distintos; no borrar ni ignorar ninguno. El análisis no exporta MAC, boot_id ni líneas crudas con procesos ajenos.

## Pstore nuevo

32756B, SHA `498a57cc784ce32b2cd47951fc090779e4ef5af9da6bf5af6d0ff896ec3765fa`, distinto al pstore0.5. Primera línea truncada; marcas completas12064,380099–12592,770914s,129líneas de SDIOCMD53. Contiene aperturas del driver **Mediatek Bluetooth SDIO v0.0.1.13_2020092401** y `mode is 2`. Esto identifica texto del controlador presente; no determina por sí solo el modelo físico del chip.

No contiene una marca de reboot_notify ni el intervalo de apagado. Puede ser una ventana posterior de un anillo que perdió el comienzo; la ausencia no demuestra que nunca se solicitara reinicio. No se atribuye inequívocamente al último Update ni se mezcla con los517,24s del pstore anterior. `ro.boot.bootreason=reboot,update` tampoco acredita ejecución de recovery.

## Efecto sobre H1/H2 y Fable

La rama de Fable sobre WiFi/Bluetooth/BatteryStats gana evidencia concreta de problemas **durante Android**. En AOSP9, tanto `dump()` sin argumentos como `shutdown()` de BatteryStats pasan por `syncStats(UPDATE_ALL)`; esa coincidencia vuelve útil observar el trabajador y sus esperas. No prueba que el dump ni el apagado estén detenidos en la misma línea. El trabajador pide WiFi/BT de forma asíncrona y limita la espera explícita de respuestas a2s; faltan las pilas o el registro del intervalo para identificar el bloqueo real. [BatteryStatsService](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/am/BatteryStatsService.java).

Los dumps pueden programar trabajo interno; matar el cliente al vencer el plazo no garantiza cancelar la operación del servicio. No repetir BatteryStats en bucle ni acumular consultas bloqueadas. Los ANR anteriores a la captura acreditan que el problema de Bluetooth ya existía.

H2 permanece abierta: no hay lectura de copia interna/mapa/BCB ni identificación del recovery. No se modifica la ROM ni se prepara otro ZIP a partir de estos timeouts. No hay instalación ni respaldo del TV confirmados.

## Próximo paso acotado

El usuario ofreció acceso por LAN. Conectar **este primer P291** al mismo router que la PC, que puede seguir por WiFi. Usar la IP que informe el usuario y comprobar primero DT/API/UID y acceso existente; no sustituirlo por el segundo P271. LAN no aporta alimentación/HDMI ni eleva privilegios. No habilitar root ni cambiar autenticación.

Primero, lectura en vivo acotada: estado de procesos, errores Bluetooth y registros/pilas ya existentes que sean legibles. No repetir dumps BatteryStats atascados. Si el acceso y las observaciones lo permiten, preparar una comparación antes/después de desactivar radios mediante controles normales, registrando el estado inicial y el resultado real de cada orden. OFF, retorno0 o aceptación de la solicitud no demuestran que haya cesado el ciclo. No combinar esa intervención con otro Update ni reiniciar automáticamente.

Antes de otra captura USB, exigir sincronización dirigida de archivos y directorio, tratar su ausencia/error/plazo vencido como fallo y comprobar el cierre después. AOSP9 dispone de `toybox fsync`, pero su disponibilidad/permisos en el TV deben probarse; no sustituirlo por `sync` global a ciegas. [Fuente fsync](https://android.googlesource.com/platform/external/toybox/+/android-9.0.0_r1/toys/other/fsync.c), SHA `cc337d59c44e2d19e1af7008a7f93bd96c1fd185cdf30fae87b0c0cfc01dfc3e`. La corrección no se ha desplegado y no garantiza inmunidad a fallos físicos del medio.

## Reproducibilidad

[Analizador offline](../revision-postintento/analizar-captura08.py),8regresiones en [test_captura08.py](../revision-postintento/test_captura08.py): timeout con retorno0, mensajes con NUL, tres cierres vacíos, datos alterados, metadatos inconsistentes, permisos, éxito válido y salida sin contenido privado. Pruebas PC aprobadas, sin tocar el TV ni cambiar archivos del USB. Los hashes de estos scripts están en el resumen. La revisión física0.8 se registra aparte de los resultados locales de compilación de esa APK.
