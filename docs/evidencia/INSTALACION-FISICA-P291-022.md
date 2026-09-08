# Primera instalación física de TV Base en P291

## Resultado del 8 de septiembre de 2026

**La instalación terminó y TV Base arrancó.** El usuario aportó una foto del menú propio y confirmó que puede conectarse nuevamente por WiFi. El Kingston volvió a la PC con los seis respaldos, los recibos de preparación de datos y el cierre `installed_verified` de 0.2.2. La revisión de esos archivos confirma las cinco escrituras y sus hashes de lectura. [Hallazgos y alcance](../../diagnostico/primer-tv-instalado-20260908/HALLAZGOS.md) · [Resumen verificable](../../diagnostico/primer-tv-instalado-20260908/resumen-saneado.json).

Hay una incidencia abierta: **la casita/Home del control no vuelve al menú principal**. Se registra en [ISSUE-HOME-01](../INCIDENCIAS.md). El usuario sigue probando su APK y, por ahora, informa que el resto funciona; eso no sustituye una aceptación completa de todas las funciones.

## Evidencias separadas

| Evidencia | Qué permite afirmar |
| --- | --- |
| Seis imágenes y `00-backup-verified.json` | system, vendor, product, odm, boot y userdata previos a la instalación están respaldados. Copias USB→PC cotejadas por tamaño y SHA. |
| `10`, `11` y `20` | Formato terminado con código 0, sin timeout ni salida truncada; footer limpio, contenido vacío comprobado en montaje de solo lectura y desmontaje final registrados. |
| `instalacion.log` y `90-installed-verified.json` | Cinco imágenes de plataforma 0.2.0 escritas y releídas, con boot al final; cierre del instalador 0.2.2 registrado. |
| Foto del launcher y reporte del usuario | TV Base ejecutándose y WiFi conectable en este ejemplar. No prueban el proveedor WebView efectivo ni estabilidad/rendimiento prolongados. |

Los recibos del TV no están firmados y no guardan el hash integral del ZIP ejecutado. La coherencia se contrasta con el identificador del paquete, los cinco hashes de plataforma y los entregables sellados conservados. No se atribuye a la foto una comprobación de versión de Chrome o de todos los drivers.

## Qué se conservó

Adquisición en PC terminada: **199 archivos, 6091261673 bytes**; seis imágenes suman **6067060736 bytes**. Se conservaron también los informes anteriores del USB y la fotografía. Destino privado local: `privado/instalacion022-adquisicion-20260908-124541-2bb0d2f7`. El contenido de userdata no se montó ni se inspeccionó; los originales y datos privados no se publican en GitHub. El pendrive no recibió escrituras del recopilador.

Foto: 271722 bytes, SHA256 `bab991620b84b3b574c994daa8ea8a23a7e5fde603e7b17e758cc9fbb5eac6bd`. El original permanece local. Los doce respaldos originales anteriores siguen conservados; este nuevo conjunto agrega una copia de userdata inmediatamente anterior al borrado. Ninguno de los dos conjuntos se presenta como copia de toda la eMMC ni como restauración ensayada.

## Lo aprendido

Ahora hay topología y starts reales registrados por recovery: las particiones están bajo `…/block/mmcblk0/<nombre lógico>`, con padre MMC 179:0 de 7650410496 B. Esto valida en el equipo el caso que había rechazado 0.2.1. La corrección 0.2.2 funcionó conservando las comprobaciones de identidad y las mismas imágenes de Android. [Error anterior](ERROR-INSTALADOR-P291-021.md) · [Fuente y contrato](PARTICIONES-AMLOGIC-P291-022.md).

El reloj del TV seguía fechado en 2020. El registro declara 13 min 54 s desde el cierre del respaldo hasta el inicio de system, y 16 min 22 s entre el inicio de system y el inicio de boot. No son la duración total ni tiempos puros de escritura: incluyen comprobaciones, sincronización y otras operaciones, y no hay reloj monotónico por fase. Por eso reducir respaldos no permite prometer por sí solo una instalación corta.

## Pendientes y autorización

Home del control, resultado de la APK y proveedor WebView, dos VP9/alfa/canvas, almacenamiento, estabilidad de red y arranque en frío sin pendrive siguen por comprobar. El pendrive está ahora en PC, pero no se registró un encendido desde cero sin USB. La conexión WiFi informada no demuestra todavía estabilidad de larga duración o funcionamiento en otros aparatos.

No se probó reentrada a recovery desde el Android nuevo ni restauración; no hay rollback automático. El gestor propio sigue incluido pero desactivado, sin servidor configurado ni ensayo remoto.

**El usuario pidió documentar y proponer antes de actuar.** Se realizó únicamente adquisición/lectura del USB, revisión local, documentación y publicación. Nuevas pruebas en TV, corrección de Home, capa de producto, instalador rápido y actualizaciones requieren su OK posterior. [Propuesta de dos recorridos](../PROPUESTA-LOTES-Y-ACTUALIZACIONES.md).
