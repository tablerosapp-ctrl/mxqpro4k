# Reconocimiento 0.1: entrega secuencial por USB

8/9/2026. El usuario dio OK para construir el reconocedor y preparar el Kingston conectado para varios TV box. Se implementó una aplicación Android normal que conserva una ficha por equipo y una captura distinta por pasada. El nombre P291/P271/Rockchip es candidato; no habilita instalar una ROM ni demuestra todos los chips físicos.

## Entregable

`TVBASE-RECONOCIMIENTO/Reconocimiento-TVBase-0.1.apk`: 106899 bytes, SHA256 **f631d5a16fa26266276f3be6f7f1e9f924ff95ea26dd922ff18f105022e1d813**. Paquete `com.tvbase.reconocimiento`, versión0.1, API21+/target28. [Compilación vinculada a fuentes](../../diagnostico/reconocedor-0.1/COMPILACION.json).

La APK no tiene permisos de Internet, root, ADB, reinicio o instalación de paquetes/ROM. Lee APIs y archivos accesibles; genera índices, copias seleccionadas y errores de acceso/límites. Inicializa WebView y EGL locales para identificar implementaciones, sin probar rendimiento. [Alcance](../../diagnostico/reconocedor-0.1/README.md) · [Guía](../../diagnostico/reconocedor-0.1/LEEME-USB.txt).

## Pruebas PC

- Compilación de las seis fuentes Java/XML, dex, alineación, firma con la clave existente y metadatos/CRC APK verificados. Las fuentes y hashes quedan ligados al recibo de compilación. Se corrigieron antes de entregar errores de sintaxis/SDK y una comprobación del nombre de campo de aapt2; las salidas previas se conservan en privado.
- Diecinueve métodos de prueba del [importador](../../diagnostico/reconocedor-0.1/test_importar_informes.py), con subcasos: ZIP/JSON malformado, CRC/hash, rutas/Unicode, límites, perfiles y varias unidades, captura parcial, corrupción de copia antes de relectura y DEFLATE con descriptor.
- [Escritor Java real](../../diagnostico/reconocedor-0.1/tests/test_archive.py) produjo un ZIP con archivo binario de4MiB y JSON UTF8; el importador Python independiente lo aceptó. Se rechazaron seis nombres inseguros y una repetición que sobrescribiría la captura. Prueba host con org.json; no equivale a filesystem/proveedor Android.
- Revisión independiente de colectores y exportación: datos tardíos de tareas acotadas no escriben al cerrar; DT prioritario, presupuesto por espacio, nombres de copia portables; relectura de ZIP y distinción entre fsync no soportado y error real. Se resolvieron colisión de reintentos y sincronización local antes de registrar la última captura. Los límites de recibo parcial/proveedor se documentan.

## Copia al Kingston

[Preparador](../../preparacion-usb/preparar-reconocimiento-01.ps1) validó identidad/tamaño exactos del Kingston, FAT32/TVBASE y marcador anterior; comprobó fuentes y APK. `-CheckOnly` terminó sin escribir. Una ejecución `-Prepare` terminó **verified, código0**. [Recibo saneado](../../preparacion-usb/reconocimiento-01-estado.json).

Se agregaron APK, guía y marcador en una carpeta nueva, con flush de archivos y SHA de relectura; `INFORMES` quedó vacío, sin datos de prueba ficticios. Se preservó el inventario anterior: 197 archivos de hasta64MiB por SHA y siete archivos grandes por ruta/tamaño/fecha, sin volver a leer toda userdata. No hubo borrado, traslado, formato o reparación. La verificación de metadatos de los grandes no equivale a una nueva verificación completa de sus hashes; los respaldos adquiridos anteriormente conservan su evidencia propia.

La expulsión segura se indicó al usuario. No se observó su ejecución ni se acredita flush de volumen Windows. No repetir el preparador sobre la carpeta/recibo existentes.

## Pendiente físico

Primera instalación/ejecución de la APK y escritura desde Android aún no probadas al entregar. Se propone empezar por P291 conocido y después acumular P271/otros; cada TV requiere poder instalar la APK. Cuando vuelva el USB, verificar/importar sin borrar origen. Solo entonces se podrá declarar captura física y determinar qué información protegida necesita un acceso específico.

Ni esta entrega ni el espacio disponible de casi30GB convierten el informe en copia completa de la ROM, prueba de aceleración de video o certificación antimalware. Las copias crudas y sus identidades son privadas; GitHub recibe únicamente código y documentación saneados.
