# Preparación física de entrada al recovery P291 · Acceso USB0.9

El usuario respondió **«si ejecuta»** a la solicitud explícita de preparar ENV/BCB tras explicar el riesgo de impedir el arranque y la ausencia de rescate físico probado. Después confirmó el traslado del Kingston al primer P291 manteniendo alimentación y LAN. Esta decisión autoriza el método descrito; no debe pedirse nuevamente por rutina.

## Resultado observado

Se ejecutó una sola vez el [cliente LAN0.9](../../rom-simplificada/original-p291/entrada-apk/OPERACION-LAN-09.md) con la APK sellada ya instalada. El diálogo del sistema al2% no fue usado ni cancelado. Las comprobaciones previas confirmaron el P291 original, UID shell/root, API28, build/kernel y SHA de la APK, además de ausencia de intento interno anterior. El Kingston presentaba el marcador previsto y el ZIP0.2.1 del tamaño exacto.

La secuencia guardada fue `launched` → `stage` (ROM70%) → `prepared`. Hubo una sola emisión de lanzamiento y dos consultas; los31 registros de transporte pasaron códigos, tamaños y hashes, sin timeout o truncamiento. El helper confirmó preparación completa, lectura final ENV/BCB y dos órdenes de cache conservadas. No solicitó reinicio, borrado de userdata ni escritura de las imágenes Android.

El cierre demostró en este equipo la sesión independiente del helper y la sincronización de los archivos/directorios usados en el Kingston. Esa ejecución no demuestra resistencia a todo fallo de alimentación ni aceptación del cargador/recovery. La expulsión segura anterior de Windows no fue observada; no se modifica retrospectivamente el recibo de copia USB para afirmarla.

## Adquisición independiente después de preparar

Se adquirieron a PC el informe USB, sus21 archivos declarados con21 sidecars SHA, los recibos internos y las particiones ENV/misc actuales. Se verificaron bytes, hashes y coherencia. El último control terminó el7/9/2026 a las23:41:53ART.

| Elemento | Resultado |
| --- | --- |
| INFORME.json | 4383bytes, SHA256 `2b2715266a782072487c750c976f0f96e35a74d88c0e3664be501e37194ced7c`; estado `ready_to_commit`, coherente con el cierre interno `prepared`. |
| ENV original respaldado | SHA256 `49e48fddb963d1a4ebaf5889916bba8b59141bcc1eeef71ac1dad5c6425af775`. |
| ENV actual,8MiB completos | SHA256 `bbf9b6d51379a777576ffb96aa9776dc646c6300d70ee47dd2c475b747617b77`, idéntico al resultado previamente revisado. |
| misc original respaldado | SHA256 `c8b5991390836e2f03693d8a4f6f2f4ea2b223c20951a119155fba19cf542549`. |
| misc actual,8MiB completos | SHA256 `9793e0401880535b3a53d14436c3e59fb8d8e84cd96a649dca6a667d923648f2`, idéntico al resultado previamente revisado. |
| Órdenes activas de cache | command, uncrypt_file, zipinfo y block.map ausentes al control posterior. Las dos presentes antes de la preparación se respaldaron y preservaron con otro nombre. |
| Cierre | Recibos internos/USB y marcador coherentes; INCOMPLETO ausente en ambos lugares. |

Los registros crudos, respaldos, rutas del TV y nonce se conservan bajo directorios privados enPC. No publicar ese contenido. [Evidencia saneada y revisión independiente](../../rom-simplificada/original-p291/entrada-apk/EJECUCION-TV-09.json). La adquisición posterior es una observación adicional; no garantiza que ningún proceso ajeno cambie el estado en el futuro.

## Resultado físico posterior y siguiente paso

Después de indicar el ciclo de alimentación de10segundos con el Kingston conectado, el usuario confirmó **«Apareció un menú de recovery»** y pidió instrucciones. Es una observación comunicada por el usuario; no se dispone de una captura o hash que identifique exactamente la imagen de recovery ejecutada. El recibo `EJECUCION-TV-09.json` conserva el corte anterior al ciclo y no se reescribe para incorporar este resultado posterior.

Se indicó **«Apply update from EXT» → «Update from udisk» → `TVBASE-P291-A9-0.2.1-RECOVERY.zip`** y confirmar. Conservar el USB y la alimentación. No elegir wipe/factory reset por separado ni el ZIP de restauración. Esperar el mensaje final o error del instalador antes de reiniciar; si el menú difiere, identificarlo antes de seleccionar otra función. No repetir el actualizadorOEM, prepare ni otro ciclo de alimentación.

Todavía no se ha comunicado el resultado de aceptar o instalar elZIP. El menú visible no demuestra que la firma se haya aceptado o que se haya ejecutado el instalador. Este debe comprobar que bootcmd volvió al valor normal antes de respaldar/formatear y escribir Android.

**Se acredita el menú de recovery informado por el usuario; siguen pendientes la instalación deTVBase, el respaldo nuevo de userdata, la restauración y el arranque interno de la plataforma.** La preparación0.9 no borró los datos/Android originales. La ROM y sus pruebas de hardware, WebView, red y video siguen pendientes. La próxima actualización deROM desde Android simplificado tampoco está demostrada.
