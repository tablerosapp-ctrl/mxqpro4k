# SD para extraer el último Rockchip

El usuario aportó una SD grabada, autorizó borrarla y confirmó que el Kingston estaba en otro puerto USB. La foto del último RK3229-C ofrece **Apply update from SD card** y declara `CNV8b.20230725`. El reconocimiento Android de ese mismo equipo ya está adquirido; no se repite.

## Decisión y correspondencia con el recovery

Se usan dos medios: SD de 8 GB para cargar el extractor y Kingston de 32 GB para las copias. La SD tenía `sdupdate.img`, un marcador Rockchip y `sd_boot_config.config` con `fw_update=1`, además de una partición que empezaba a 96 MiB. Por tanto no bastaba con agregar un ZIP a esa tarjeta: conservaba un mecanismo de actualización automática. No se ejecuta el programa Rockchip ni se instala su imagen.

La imagen de la SD, de 907.946.456 bytes, se comparó íntegra con la imagen aportada en PC: SHA256 `8728cf503b79f22000110c41a1d7b1f3b10a975bc15e8256461f6ef72285c89e`. El [inspector local](../../diagnostico/rockchip-sd-20260908/inspeccionar-paquete.py) verifica rangos RKFW/RKAF y conserva por separado el recovery y otros componentes seleccionados. No certifica autenticidad de firmware ni ejecuta sus binarios. [Revisión de la herramienta aportada](HERRAMIENTA-SD-ROCKCHIP.md).

El recovery de esa imagen coincide en fingerprint con C, pero no se ha leído el hash del recovery instalado. Su análisis acredita clave v3 Rockchip/SHA256, ruta fija SD/update.zip y montaje USB inicial. [Análisis directo y límites](RECOVERY-CNV8B-SD.md). Se preparó **RK1**, que conserva idéntico el ejecutable ARM32 0.1 y cambia firma, certificado y metadatos de empaquetado. [Receta y contrato](../../diagnostico/extractor-recovery-rk1/README.md), [construcción](../../diagnostico/extractor-recovery-rk1/COMPILACION.json), [revisión independiente](../../diagnostico/extractor-recovery-rk1/REVISION.json).

| Entregable | Bytes | SHA256 |
| --- | ---: | --- |
| `TVBASE-EXTRACTOR-0.1-RK1-ARM32-RECOVERY.zip` | 1.380.273 | `0f7fe7a5f609290f69597c599ac8c72954b4fc7e04957cd27b279a368f060c38` |
| Ejecutable incluido, idéntico a 0.1 | 3.276.960 | `05221a82892e3aa6958d128d497c81645f8fdeae5cd494f320385f1e6d060e48` |

La variante tiene cuatro entradas, sin imágenes ni clave privada. Se verificaron CRC/contenido, firma Python y OpenJDK; la revisión independiente usó DER propio y exponenciación RSA con el módulo de res/keys. Los casos de clave incorrecta, digest anterior, contenido alterado y footer corrupto fueron rechazados. La clave pública de desarrollo compartida sólo resuelve esta compatibilidad de laboratorio, no la confianza de las futuras actualizaciones de producción.

## Preparación y conservación

El [preparador](../../preparacion-usb/preparar-sd-rk3229-c.ps1) exige la identidad completa del lector/tarjeta, tamaño 8.053.063.680 bytes, bus USB, disco ajeno al sistema, geometría inicial y los tres archivos esperados con la imagen idéntica a PC. Antes del borrado conserva en privado los primeros 96 MiB y los dos auxiliares; exige fsync y relectura de origen/copia. No es un respaldo de toda la SD ni del TV. Los metadatos internos de Windows no se copian.

Después quita las particiones de esa SD, pone a cero solamente el prefijo respaldado para retirar el loader previo, relee los ceros y crea MBR con una partición máxima desde 1 MiB, FAT32 `TVBASESD`. Todas las operaciones vuelven a comprobar identidad y geometría; el handle raw también comprueba número, tamaño y serial mediante IOCTL. [Pruebas locales](SD-PREPARADOR-PRUEBAS-PC.json): 31 casos y sintaxis PowerShell 5.1 correctos; los fixtures PC no equivalen a ejecutar formato físico.

El [entregador](../../preparacion-usb/entregar-sd-rk3229-c.ps1) sólo actúa tras el recibo de formato completo y con ambos medios identificados. Copia el ZIP como `update.zip` y la [guía](LEEME-SD-RK3229-C.txt), con creación exclusiva, flush de archivos y relectura SHA256. Comprueba el plan C existente y que Kingston no contiene `update.zip` ni `update.img` en raíz, porque ese recovery busca esos nombres automáticamente al inicio. No cambia Kingston, sus respaldos ni sus planes.

**Resultado operativo: pendiente.** Windows canceló la solicitud de elevación del continuador; no arrancó el proceso y la SD sigue sin particiones. El paquete está listo en PC y el Kingston se conserva; los archivos todavía no fueron copiados a la SD. Hace falta volver a mostrar la solicitud cuando el usuario pueda aceptarla. No se sabe si la cancelación fue manual o por tiempo de espera. No hay extracción ni instalación en el TV.

## Errores de preparación investigados antes de cualquier escritura

La primera comprobación tenía `REV_` en la identidad del lector; la consulta real mostró `REV__`. Se corrigió exactamente ese carácter, manteniendo todos los demás controles. El siguiente CheckOnly comparó los archivos pero Windows denegó abrir PhysicalDrive con el token no administrativo. Ninguno creó recibo de preparación ni modificó la SD.

El primer proceso administrativo no llegó a ejecutar el script porque Windows PowerShell tenía deshabilitada la ejecución de scripts. Se confirmó con un script local inocuo, sin acceso a dispositivos. La ejecución corregida permite el script sólo en ese proceso; no cambia la política persistente de Windows. No son errores físicos de la SD y no se vuelve a grabar una imagen por tanteo.

## Detención tras Clear-Disk y continuación acotada

El proceso administrativo obtuvo y verificó el respaldo del prefijo (SHA256 `25b1107c216ef0c489e6075bd8bb08be5ccf454d9b99cca9285d2b5616a0e068`). Clear-Disk terminó sin error, pero la consulta posterior mostró MBR con cero particiones. El preparador exigía RAW y abortó **antes de poner a cero el prefijo, crear la partición o formatear**. Se conserva su [recibo de fallo](../../preparacion-usb/sd-rk3229-c-formato-estado.json) sin convertirlo en éxito ni repetir ese preparador.

La continuación nueva parte de la identidad exacta y cero particiones, vuelve a validar los respaldos ya existentes y realiza sólo lo que falta. [Update-Disk](https://learn.microsoft.com/en-us/powershell/module/storage/update-disk?view=windowsserver2025-ps) permite refrescar la información de Windows después de la escritura del prefijo. Se comprueban nuevamente geometría, formato y el área previa a la nueva partición. Una discrepancia detiene el proceso conservando el nuevo recibo; no se prueba otra imagen ni se selecciona otro disco.

## Prueba física siguiente

Sólo en RK3229-C, conectar **SD y Kingston antes de entrar al recovery**, elegir **Apply update from SD card → update.zip** y dejar terminar la copia/verificación. No usar Wipe, Recovery System ni los instaladores P291 del Kingston. Ante error, conservar el texto sin repetir automáticamente. Devolver Kingston a PC después de finalizar y expulsarlo correctamente desde Android, antes de cambiar de equipo.

Esta entrega todavía no acredita firma aceptada por el recovery real, copia de eMMC ni restauración. El extractor abre fuentes internas para lectura, omite áreas ocupadas y exige sus propios controles; el recovery anfitrión puede escribir registros o metadatos. A/B comparten DT con C y necesitan otro plan después de revisar la primera captura.
