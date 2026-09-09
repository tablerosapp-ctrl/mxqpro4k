# RK3229-C: extracción en la misma SD · 0.2 / RK2

## Motivo y alcance

RK1 fue aceptado y ejecutado por el recovery real, pero no encontró un pendrive montado que cumpliera sus controles. [Foto, orden de ejecución y conservación](ERROR-RK1-DESTINO-USB.md). El usuario pidió guardar en SD y autorizó completar la preparación mientras estaba ausente.

La nueva variante usa exclusivamente la SD de carga como destino. El Kingston no hace falta para esta prueba y conserva sus respaldos. No se instala una ROM, cambia el recovery ni repite el formateo de la tarjeta. Los archivos anteriores se archivaron y comprobaron en PC antes de sustituirlos; las versiones selladas0.1/RK1 siguen intactas.

## Controles

- Montaje raíz `/mnt/external_sd`, FAT32/vfat RW, correspondiente al archivo `update.zip` ejecutado. Sin elegir cualquier ruta por nombre ni usar almacenamiento interno como alternativa.
- Topología sysfs física MMC con `type=SD`, CID válido, partición directa número1, tamaño8053063680B y partición8052015104B desde1MiB. No se equipara el serial del lector Windows al CID de la SD. CID, nodos, tamaños por ioctl, montaje y paquete se revalidan durante la copia.
- Separación del destino respecto de todas las fuentes eMMC por sysfs y major:minor. Orígenes abiertos exclusivamente para lectura; áreas ocupadas por consumidores RW o desconocidas se omiten con motivo. No se desmonta ni remonta para forzar la copia.
- Plan C derivado de su captura Android, marcador de esta entrega y carpetas nuevas por ejecución. Los otros Rockchip comparten DT y requieren seleccionar otro plan después de revisar esta captura.
- Partes de hasta1GiB, reserva128MiB y espacio recalculado con todas las fuentes elegidas. No se reduce el respaldo para hacerlo caber. Faltante de espacio deja inventario y error antes de copiar imágenes.
- SHA durante copia, relectura del destino y segunda lectura del origen; fsync de archivos/directorios y cierre verificable. Las extensiones `.partial` permanecen: el manifiesto acredita el estado, no el nombre.

## Capacidad y limitaciones

La SD volvió a PC con8033837056B libres. La eMMC declarada por Android mide7818182656B. Más128MiB de reserva y una estimación conservadora adicional de8MiB para áreas boot dejan margen para esta primera captura. Los tamaños y el espacio efectivo se comprueban otra vez en recovery; la captura puede omitir áreas montadas RW y no incluye RPMB ni todos los chips. No hay restauración Rockchip ensayada.

La fotografía acredita ejecución de0.1/RK1, no la de0.2/RK2. La coincidencia del firmware aportado con la compilación del TV tampoco demuestra igualdad binaria de su recovery. Las pruebas PC no sustituyen el primer respaldo físico y su importación/relectura en PC.

## Entrega

**Completada y verificada en PC.** [Construcción](../../diagnostico/extractor-recovery-rk2/COMPILACION.json), [revisión independiente](../../diagnostico/extractor-recovery-rk2/REVISION.json), [reciboSD](../../preparacion-usb/sd-rk3229-c-02-estado.json) y [lectura final independiente](SD-02-LECTURA-FINAL.json).

Paquete `TVBASE-EXTRACTOR-0.2-RK2-ARM32-RECOVERY.zip`: 1387097B, SHA256 `3d9e6a18c023ccc4a355aab738537655049016634dcf855990b307aa619486cd`. Se copió idéntico como `update.zip`, junto con guía, marcador y planC. Carpetas de captura vacías al entregar. Archivos con flush y relectura comprobados; no se observó flush de volumen ni expulsión segura. El Kingston no fue modificado y la SD no se formateó. [Guía0.2](LEEME-SD-RK3229-C-02.txt). Esta SD se utiliza primero en RK3229-C; no se pasa al siguiente TV antes de devolver y verificar sus archivos.
