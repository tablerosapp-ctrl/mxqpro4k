# Entrada USB de la ROM original P291

**Estado vigente y archivos:** [Acceso USB 0.9](ESTADO-ENTRADA-09.md). El APK se compiló y firmó contra API 28 con el ZIP 0.2.1 exacto, y su cotejo independiente está aprobado en la [liberación offline](LIBERACION-09.json). El [RootProbe físico](PROBE-FISICO.json) ya fue aprobado en almacenamiento interno. El desacoplamiento del nuevo worker, fsync USB, entrada a recovery y escrituras ENV/BCB todavía no se probaron físicamente.

## Contrato previo conservado como antecedente

El texto que sigue es el diseño inicial anterior a esa implementación. Sus menciones a pasos pendientes describen aquel momento; prevalece el documento de estado enlazado arriba. La ROM 0.2.0 y sus recibos no se modificaron para desarrollar esta entrada.

Se compiló por separado un **helper mínimo, sin APK ni entrada a recovery**, para probar UID/API/DT y fsync de un archivo temporal dentro de `/data/local/tmp`. [Artefacto, comando único y límites](PROBE-EJECUCION.md). Sus 17 controles host no prueban la ejecución Android; la ejecución física corresponde al coordinador y queda pendiente en este recibo.

## Resultado que debe ofrecer

Una actualización de la aplicación `local.tvbase.acceso`, firmada con la misma clave local existente y con `versionCode` superior a 8, que pueda trabajar sin LAN ni Internet. El transporte queda restringido a `127.0.0.1:5555`, ya disponible en el Android original. Una respuesta ADB `AUTH` debe detener la operación: no habilitar servicios, reiniciar adbd, alterar autenticación ni instalar otro mecanismo de root.

El acceso root ya comprobado por LAN fue `/system/xbin/su 0 /system/bin/id`. La sintaxis propuesta para el cliente local es `/system/xbin/su 0 /system/bin/sh` con un programa fijo revisado. Que el comando `id` haya funcionado no acredita todavía la ejecución de ese programa desde la aplicación.

El TV continúa en la espera del actualizador OEM al 2 %. No se reutilizan el botón OEM, `ShutdownThread`, consultas a BatteryStats/WiFi/Bluetooth ni el reinicio normal que ya dejó el equipo sin señal. La secuencia de preparación persistente y la acción de entrada se definirán mediante la revisión del recovery y del kernel originales. Un diagnóstico completo no habilita por sí solo esos pasos.

## Componentes y límites

| Componente previsto | Responsabilidad | Límite |
| --- | --- | --- |
| `Acceso.java` | Pantalla compatible con control remoto; progreso y resultado de una operación iniciada por el usuario. | No disparadores automáticos al abrir, volver del fondo o recrear la actividad. |
| `AdbLocal.java` | Cliente de un flujo, solo loopback; paquetes fragmentados, checksum, canal y límites comprobados. | No aceptar servicios o comandos suministrados desde USB ni argumentos de un intent. |
| `RootProbe.java` | Programa propio ejecutado temporalmente con el `su` existente; identidad, lecturas y SHA. | Sin comandos arbitrarios, sin listener, sin `setprop`, `uncrypt`, BCB write, wipe, flash ni reset en esta etapa. |
| `InformePersistente.java` | Nueva carpeta de informe, copias limitadas, hashes, sincronización y cierre verificable. | Un error de lectura, escritura, fsync o plazo deja el resultado incompleto; nunca convertir timeout en éxito. |
| `Contrato.java` | Perfil P291, receta aprobada, nombres y tamaños esperados, estados terminales. | Los argumentos de entrada a recovery deben venir de una revisión explícita posterior. |

La alternativa preferida para `RootProbe` es una clase `main` dentro de la misma APK, cargada con el `app_process` ya existente. Permite usar SHA de Java y `android.system.Os.fsync` para archivos y directorios sin instalar un binario auxiliar ni invocar un `sync` global que podría quedar esperando otros dispositivos. **Esta alternativa necesita primero una prueba acotada de ejecución e identidad; no está confirmada en este TV.** El proceso ART puede generar caché de ejecución; no describirlo como cero escrituras internas.

Si esa ejecución falla, conservar el error y revisar la alternativa; no iniciar una sucesión automática de comandos root. La APK no se firma con la clave de plataforma ni adquiere UID de sistema: solicita al `su` local la ejecución temporal del programa concreto.

## Comprobaciones antes de preparar nada

1. Exigir API 28, DT `gxlx2_p291_1g`, identidad inicial de shell y UID 0 dentro del helper. Registrar kernel y compilación, sin inferir compatibilidad por el nombre comercial del equipo.
2. Descubrir un único volumen físico cuyo marcador sea el aprobado. Verificar el montaje, el directorio canónico y los enlaces; evitar confundir `/storage` y `/mnt/media_rw` como dos pendrives diferentes. No elegir el primer volumen encontrado.
3. Abrir una sola vez el ZIP aprobado de la ROM y comprobar tipo regular, tamaño, SHA256 y estabilidad de inode/dispositivo/tamaño durante la lectura. Los valores se fijan durante la compilación contra [el recibo verificado](../empaquetado/salida/TVBASE-P291-A9-0.2.0-VERIFICACION.json); no confiar en un hash arbitrario del pendrive.
4. Leer el alias original de `misc`, resolver el dispositivo y exigir `179:7`, tamaño 8388608 bytes, antes de copiarlo. Conservar una copia exacta de la partición seleccionada y sus hashes; no llamarla respaldo completo del TV. La copia inicial sirve también para conservar BCB antes de cualquier preparación posterior.
5. Conservar la existencia, tipo, tamaño, contenido exacto o motivo de lectura incompleta de los archivos concretos de `/cache/recovery`: `command`, `uncrypt_file`, `block.map` y los registros acotados que determine la revisión. No recorrer ni publicar todo `/data` o cache. Un archivo ausente es un resultado distinto de un archivo vacío o denegado.
6. Comparar el estado inicial y final de las fuentes mutables. Si cambian durante la captura, registrar la variación y detener cualquier transición posterior; Android sigue activo y no existe un snapshot atómico.

Los campos y prioridades exactos de BCB, `command` y argumentos del recovery corresponden a la revisión independiente de sus fuentes/binario. No se introducen aquí una orden `--update_package`, un argumento de reset ni una limpieza automática de órdenes antiguas.

## Persistencia que faltó en 0.8

La captura 0.8 devolvió cierre correcto al cliente, pero varios archivos finales quedaron vacíos al volver a la PC. Leer un archivo recién escrito desde la caché del mismo sistema no acredita persistencia. La entrada nueva debe exigir esta secuencia:

1. Crear exclusivamente una carpeta nueva con identificador aleatorio, bajo el volumen ya validado; sincronizar su directorio padre.
2. Escribir cada archivo con creación exclusiva y rechazo de enlaces; comprobar cantidad de bytes y SHA; sincronizar el descriptor, cerrarlo y volver a leer/hash. Conservar archivos parciales ante cualquier fallo.
3. Crear y sincronizar los sidecars de SHA y el inventario de archivos exactos, incluyendo resultados ausentes/denegados/timeout; sincronizar el directorio del informe.
4. Escribir el marcador terminal después de completar las verificaciones, sincronizar el marcador y finalmente su directorio. Solo entonces devolver al cliente un resultado terminal con nonce, hash del inventario y código real de la operación.

La API [Os.fsync](https://developer.android.com/reference/android/system/Os#fsync(java.io.FileDescriptor)) está disponible antes de API 28. Se debe verificar su funcionamiento real con archivos y directorios del volumen USB de este TV. Si el sistema devuelve error o no termina, la interfaz debe mostrar captura incompleta; no degradar silenciosamente a `flush()` ni a una espera fija. La sincronización solicitada al sistema tampoco prueba que un dispositivo defectuoso respete sus garantías eléctricas.

El transporte debe conservar bytes. Se propone `exec:` de ADB, con prueba de disponibilidad y marcador final ligado al nonce; el cierre `CLSE` no prueba por sí solo el código de salida. La ruta histórica `shell:` sigue siendo válida solo para texto controlado: en la adquisición LAN una lectura `shell -T` cambió saltos de línea. La aplicación no debe transportar imágenes binarias por un decodificador UTF-8.

## Estados e integración posteriores

- `LECTURA_INICIADA`: carpeta nueva creada; aún puede quedar incompleta.
- `DIAGNOSTICO_PERSISTIDO`: todas las lecturas exigidas y el cierre de archivo/directorio concluyeron; no equivale a preparación de recovery.
- `INCOMPLETO`: error, timeout, cambio de origen o falta de prueba de persistencia; no reintentar automáticamente.
- La preparación persistente, su reversión y la acción de entrada tendrán estados diferentes y una revisión específica. Ninguno está habilitado en esta etapa.

Los plazos del cliente no garantizan terminar un proceso bloqueado dentro del kernel. El helper debe tener límites por fase y un identificador registrable; si no responde, la interfaz no puede prometer que haya sido cancelado. Un proceso que siguiera escribiendo invalida una nueva captura o preparación hasta resolver su estado.

La compilación usará el SDK 28 y las herramientas existentes en PC, salida privada nueva por intento, paquete y certificado de Acceso USB conservados. Las pruebas host deben cubrir ADB fragmentado/AUTH/canales, salida sin marcador, comando excesivo, identidad distinta, dos volúmenes válidos, enlaces/rutas hostiles, SHA/tamaño incorrectos, archivo cambiado y fallo en cada punto de sincronización. Los resultados host no sustituyen la prueba del helper, `fsync`, recovery o entrada en el TV.

## Referencias locales

- [Cliente ADB de 0.8](../../componentes/acceso-usb-0.8/AdbLocal.java).
- [Captura 0.8](../../componentes/acceso-usb-0.8/Evidencia.java).
- [Compilación histórica de 0.8](../../instalador/compilar-evidencia08.py).
- [Root y adquisición binaria confirmados](../../../diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md).
- [Recovery original y BCB observados](../../../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md).

No se accedió al TV o al pendrive para escribir este contrato. Los informes crudos y APK compiladas futuras quedan bajo `privado/`, fuera del repositorio público.
