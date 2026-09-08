# Acceso USB 0.9: preparación explícita y proceso independiente

## Observación posterior · ejecución autorizada

La [preparación física del primer P291](../../../docs/evidencia/PREPARACION-ENTRADA-P291-09.md) terminó con resultado verificado tras la autorización «si ejecuta». Los cambios previstos de ENV/BCB están escritos y releídos; el usuario informó posteriormente un menú de recovery tras el ciclo físico. La aceptación del ZIP y la ROM instalada todavía no se acreditan. No repetir launch. El contenido siguiente conserva el análisis previo de esta compilación.

Estado del trabajo: APK 0.9 compilado, firmado contra API 28 y revisado de forma independiente, con el ZIP 0.2.1 exacto fijado. [Liberación offline](LIBERACION-09.json), [compilación](COMPILACION-09.json) y [cotejo independiente del artefacto](../entrada/REVISION-APK09-ARTEFACTO.json). El revisor obtuvo un DEX idéntico al recompilar las mismas fuentes y política. Este cierre no acredita entrega USB ni ejecución física: la preparación no se ejecutó en el TV ni se escribió su ENV/BCB durante el desarrollo.

El APK mide 61843 bytes y tiene SHA256 `1d0f267e818acca5562048f9961c7c234f36b8cc81f827cb3eac9e3fcd2505a4`. Su ZIP admitido mide 573688933 bytes y tiene SHA256 `dcb152c77e55cb067d6e88a8144990a3edb5d06568ea8cdfdc414a0fa21aac58`. El archivo binario permanece en la salida privada identificada por el recibo.

El [RootProbe físico aprobado](PROBE-FISICO.json) acredita UID 0, API 28, DT P291 y fsync de archivo/directorios en una carpeta nueva de `/data/local/tmp`. No acredita fsync de FAT32, desacoplamiento del proceso, modificación de ENV/BCB ni entrada real a recovery.

## Comportamiento implementado

La APK conserva el paquete `local.tvbase.acceso`, versión 9/0.9 y la firma local habitual. Presenta «Preparar entrada a recovery» con una confirmación concreta sobre la modificación del arranque y sus riesgos. La operación se inicia una sola vez; cerrar o volver a abrir la pantalla no la repite. «Ver estado de esta preparación» permite volver a observar el mismo nonce sin relanzar el trabajo.

El cliente solo conecta a `127.0.0.1:5555` y rechaza `AUTH`. Usa el `su` existente sin cambiar adbd, autenticación, radios o propiedades. El lanzador ejecuta el helper de la misma APK mediante `app_process`, con `setsid` y `nohup`, entrada desde `/dev/null` y salida a un registro interno. No existe un timeout KILL alrededor del mutador. Antes de operar, el hijo exige PID=grupo=sesión, ningún terminal, SIGHUP ignorada y sus tres descriptores desligados del transporte.

La APK consulta estados mediante conexiones ADB separadas y breves. Perder la conexión, cerrar la pantalla o terminar el plazo de observación **no es una orden de cancelación**. El cliente exige nonce y código remoto exactos; el cierre de ADB por sí solo no acredita resultado.

| Fase | Comprobación y efecto |
| --- | --- |
| Perfil | UID 0, API 28, DT `gxlx2_p291_1g`, build original exacto y kernel 4.9.113. |
| USB | Un solo montaje físico FAT32 con el marcador aprobado; dispositivo y nodo coincidentes, ruta sysfs USB y montaje de escritura. Rechaza MMC y volúmenes ambiguos. |
| Persistencia previa | Crea carpeta nueva de informe, archivos exclusivos y comprobación fsync de archivos, directorio y padre. Cualquier fallo aquí impide llegar a ENV/BCB. |
| ROM | Nombre, tamaño y SHA256 exactos de 0.2.1 fijados al compilar desde su recibo verificado; lectura estable y completa. No usa hashes arbitrarios del USB. |
| Respaldo | Copia íntegra de ENV y misc, 8 MiB cada una, y archivos concretos de cache. Hash, lectura posterior y persistencia en USB antes de modificar. |
| Cache | Preserva `command`, `uncrypt_file`, `zipinfo` y `block.map` que existan mediante renombrado acotado y verifica la ausencia de sus nombres activos. No los restaura automáticamente. |
| BCB | Solo permite escribir los primeros 2048 bytes de misc. Solicita `recovery` con `--show_text`, conserva campos ajenos y compara los 8 MiB posteriores con el resultado esperado. |
| ENV | Solo permite escribir el registro inicial de 65536 bytes; conserva claves/orden y cola, recalcula CRC, exige resultado exacto revisado y vuelve a comparar los 8 MiB. |
| Cierre | Manifiesto USB, marcador y recibos internos coherentes; lectura de hashes y sincronización. No dispara reinicio ni instala el ZIP. |

La identidad de bloques se limita a los nodos originales `env` 179:4 y `misc` 179:7, ambos de 8388608 bytes. Los hashes completos actuales deben coincidir con las capturas aprobadas: no basta encontrar un CRC válido. La receta inicial está vinculada al estado de este primer TV; no se debe aplicar sin adaptación a cualquier P291 del mismo nombre comercial.

## Qué significa el cambio de ENV

El `bootcmd` temporal intenta restaurar `run storeboot` y guardarlo **si el flujo de preboot llega a ejecutar ese bootcmd**. Solo después intenta `recovery_from_flash`; si esa ejecución retorna, continúa con `storeboot`. La semántica se contrastó contra fuentes Amlogic/Hush de referencia y el codec con los bytes originales, pero no se ejecutó en el bootloader físico.

La escritura de ENV y `saveenv` no son una transacción con rollback comprobado. Un corte o una escritura incompleta puede producir CRC inválido, activar valores por defecto o impedir el arranque. Un retorno exitoso de `saveenv` no acredita lectura posterior del bootloader. El respaldo en USB no prueba que exista una vía de restauración desde un TV que no arranque.

La APK explica estos riesgos antes de preparar. Solo tras una preparación confirmada solicita al usuario un ciclo de alimentación, manteniendo el USB. Ese ciclo es una acción física posterior; no se envía SysRq, `reboot`, `do_kernel_restart`, `uncrypt` ni una llamada al actualizador OEM. La selección del ZIP en recovery sigue siendo manual y la respuesta del control remoto no está comprobada; la guía contempla teclado USB.

## Resultado, fallo y persistencia

El directorio interno fijo `tvbase-entry-in-progress` bloquea reintentos automáticos. Guarda nonce, log, PID y comprobaciones de aislamiento, checkpoints antes de cada mutación y un fallo interno aunque el pendrive desaparezca. Los archivos crudos del informe USB quedan en una carpeta nueva `TVBASE-entrada09-<nonce>` y deben tratarse como privados.

`COMPLETO.txt` en USB **no basta por sí solo**. La consulta final exige estado y recibo internos `prepared` del mismo nonce, ausencia de `INCOMPLETO`, lock del mutador disponible, hash del manifiesto y texto del marcador correctos, además de sincronización dirigida. Un fallo tiene prioridad sobre un marcador de cierre antiguo o parcial. Las consultas no toman el lock durante el arranque del worker; si el proceso termina mientras se consulta, vuelven a leer el estado antes de declarar un fallo.

Ante un resultado incompleto o desconocido, la interfaz indica no cortar la alimentación ni repetir la preparación hasta revisar los informes. No restaura cache, BCB o ENV automáticamente. Las operaciones ya iniciadas quedan diferenciadas de las lecturas posteriores verificadas. `userdata_wiped=false` describe este helper; no significa ausencia de escrituras en `/data`, donde crea sus archivos internos. La instalación posterior del ZIP 0.2.1 tiene su propia política de respaldo y borrado de datos.

## Archivos e integración

- [PreparationHelper.java](src/PreparationHelper.java): lanzamiento, aislamiento, fases, checkpoints y consulta del commit.
- [EntryIO.java](src/EntryIO.java): identidad USB/bloques, copias, fsync y escrituras de prefijos limitadas.
- [EntryCodec.java](src/EntryCodec.java): transformación pura de ENV/BCB, contrastada con [el codec independiente](../entrada/codec_entrada.py).
- [EntryContract.java](src/EntryContract.java): perfil, rutas permitidas y comandos ADB generados.
- [AdbLocal.java](src/AdbLocal.java), [Acceso.java](src/Acceso.java) y [manifiesto](src/AndroidManifest.xml): transporte, interfaz y permisos.
- [compilar-entrada09.py](compilar-entrada09.py): salida nueva por intento, política generada desde la ROM real y firma existente. `--check-only` compila tipos con la modificación deshabilitada y **no genera APK**.

El builder final exige un recibo `reviewed_offline` con los hashes de todos los archivos de `src`, aprobación del método desacoplado, ausencia de reset y hashes de los resultados ENV/BCB esperados. Después de firmar se deben cotejar APK, política generada, certificado y pruebas con esos mismos archivos. Las herramientas, claves, bytecode y evidencia cruda permanecen locales bajo las exclusiones existentes; este directorio no publica sus contenidos privados.

## Verificación cerrada en PC

La revisión independiente aprobó 13 regresiones del codec Python, 11 comprobaciones negativas del codec Java y 12 casos de transporte con un servidor ADB simulado. Los codecs produjeron los mismos bytes esperados a partir de los respaldos originales. El cotejo final verificó firma para API 28, certificado habitual, paquete/versión/SDK, CRC del APK, hashes de las siete fuentes, política generada y ZIP real; una recompilación independiente produjo el mismo `classes.dex`. Los recibos conservan las identidades exactas para reproducir el cotejo.

Son pruebas de código, protocolo y artefacto en PC. Permanecen pendientes el desacoplamiento real del worker, fsync del pendrive, preparación de ENV/BCB, entrada a recovery e instalación. La liberación no transforma esos límites en resultados físicos.
