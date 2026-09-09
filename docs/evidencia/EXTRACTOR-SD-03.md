# RK3229-C: backup al final con variante RAM · 0.3 / RK3

**Extractor y guía copiados y releídos en la SD.** La captura anterior permanece en SD y en PC. [Fallo real y adquisición](ERROR-RK2-BACKUP-C.md), [contrato0.3](../../diagnostico/extractor-recovery-0.3/README.md), [construcción](../../diagnostico/extractor-recovery-rk3/COMPILACION.json), [revisión independiente](../../diagnostico/extractor-recovery-rk3/REVISION.json), [entregaSD](../../preparacion-usb/sd-rk3229-c-03-estado.json) y [lectura final independiente](SD-03-LECTURA-FINAL.json).

## Cambio solicitado

El usuario pidió intentar también los64MiB inestables, dejándolos para el final. El nuevo paquete copia primero las demás particiones elegibles en orden físico y difiere `backup` p10. No se excluye por la discrepancia anterior ni se acepta una copia con hashes distintos.

Solo para backup: lee64MiB a RAM, relee el origen antes de escribir esos datos en SD y compara ambos SHA. Si coinciden, guarda el buffer, sincroniza y relee SD; exige la misma huella. Comprueba memoria disponible o una estimación conservadora compatible con Linux3.10 y un margen adicional64MiB. Si falla memoria, lectura o hash, conserva el error y los resultados anteriores. Las lecturas usan la caché normal del kernel: no son acceso físico sin caché ni un snapshot atómico.

El resto conserva copia/SHA → sincronización y relecturaSD → relectura de origen. Cualquier fallo anterior sigue deteniendo el motor. Cache montada RW continúa omitida por el contrato previo; no se desmonta ni modifica para copiarla. Con el mapa observado se seleccionan14fuentes/7.679.770.624B, incluidas backup y userdata; reserva128MiB y espacio vuelven a comprobarse en recovery.

El paquete exige DT, CIDeMMC adquirido y mapa completo del recoveryC. El CID se incorpora solo en la construcción privada; no se publica. El mapa Android no se usa para fijar offsets. Esta variante no sirve todavía para A/B, P271 ni otro ejemplar con la misma carcasa.

## Entregable y conservación

Paquete `TVBASE-EXTRACTOR-0.3-RK3-ARM32-RECOVERY.zip`: 1463158B, SHA256 `ff9595f7a64a64df77f1c1d4904a896922e62a6be51d6a9e94247e79da985d01`. En SD se llama `update.zip`. Firma integral v3/SHA256 y CRC verificados en PC; no se cambia el recovery del TV.

Solo se sustituyeron `update.zip` y `LEEME-SD.txt`, después de archivar y verificar los anteriores. Otros siete archivos quedaron iguales: marcador, planC y los cinco de la captura fallida. SD8053063680B, FAT32TVBASESD, partición8052015104B desde1MiB; identidad comprobada sin elegir por letra. No hubo formato, reparación, escritura de bloques crudos ni modificación del Kingston. Espacio libre al entregar: 7962386432B. Flush de archivos y relectura comprobados; expulsión Windows y flush del volumen no observados.

El [lector completo](../../diagnostico/extractor-recovery-0.3/verificar-captura.py) exige cierre correcto de toda la selección. El [lector parcial](../../diagnostico/extractor-recovery-0.3/verificar-parcial.py) acepta únicamente los informes de fallo coherentes y vuelve a comprobar cada archivo; distingue los orígenes previamente verificados de los bytes fallidos. Su código0 significa revisión de archivos de una captura parcial, nunca respaldo completo. Ambos rechazan rutas no ordinarias o datos incoherentes y no abren los dispositivos descritos en JSON. [PruebasPC](../../diagnostico/extractor-recovery-0.3/PRUEBAS-LECTOR-PC.json).

## Prueba pendiente

[Guía copiada](LEEME-SD-RK3229-C-03.txt): expulsarSD de Windows, colocarla en el mismo C, entrar al recovery y elegir Apply update from SD card → update.zip. No hace falta Kingston. Esperar mensaje final; ante error conservarlo sin repetir automáticamente ni hacer wipe. Tras volver al menú, reiniciar Android y expulsar la SD antes de devolverla a PC.

0.2/RK2 sí ejecutó y dejó la captura parcial; **0.3/RK3 aún no fue ejecutado físicamente**. No hay nueva ROM ni restauración RK probada, ni certificación de limpieza del firmware. La próxima decisión depende de los archivos de esta prueba.
