# Primera extracción RK3229-C: pendrive preparado

El 8 de septiembre de 2026 se recibió y verificó la copia manual del último Rockchip. El usuario confirmó que puede abrir su menú recovery. Se preparó el Kingston para ejecutar allí **el extractor ARM32 0.1 existente**, sin reconstruir el ejecutable ni instalar otra ROM. [Hallazgos del equipo](../../diagnostico/reconocimiento-20260908-rk3229-manual/HALLAZGOS.md) · [Matriz y selección](../MATRIZ-PERFILES.md).

## Entrega comprobada en PC

[Recibo de preparación](../../preparacion-usb/extraccion-rk3229-c-estado.json): `state=verified`, código nativo 0, cierre a las 18:14:42 ART. Se ejecutó una sola preparación de escritura. Añadió exactamente dos archivos, con sincronización de archivo y relectura SHA correctas:

| Destino bajo TVBASE-EXTRACCION | Bytes | SHA256 |
| --- | ---: | --- |
| PLANES/RK3229-C.json | 401 | `f5f15963b2d8d98eb81e17b45f824f541ef2b47f7d511ac0b29e12d5a7b67311` |
| LEEME-RK3229-C.txt | 4677 | `34ff377070de11d0c59b5fae6306107c38468c549fc7b83529ce19189c39c6cc` |

Se conservaron 222 archivos anteriores comprobados por SHA y ocho grandes por metadatos. Los ocho grandes no se volvieron a leer íntegramente en esta preparación. Los bytes de archivos pasaron de 7.650.774.964 a 7.650.780.042, una diferencia de 5078 B. Quedaron 23.270.916.096 B libres. No hubo borrados, sustituciones, formato, reparación, contacto al TV ni escritura de particiones.

El plan P271 permanece con su SHA original y DT diferente. No existía ningún plan RK; después hay únicamente C. La selección se hace por DT, por lo que esta entrega se usa **solo en el último aparato MBOX/CNV8b.20230725**, no en A/B. El plan es una asociación candidata al informe, no una prueba de identidad física. Regresar a PC antes de cambiar de equipo.

El paquete USB ARM32 existente fue releído: 1.380.373 B, SHA `1f45405d22193b1e09cc694bc5328be6e8aa7f071e0d77323cacc15611063f08`. La [compilación sellada](../../diagnostico/extractor-recovery-0.1/COMPILACION.json) y sus nueve fuentes coinciden. Ambos ZIP locales de esa compilación y sus recibos fueron comprobados; no se copiaron otra vez al USB. `CAPTURAS` seguía vacío al cierre.

El recibo conserva expulsión pendiente y sincronización del volumen no acreditada. La sincronización de los dos archivos y su relectura no se convierten en una observación de expulsión física. Expulsar desde Windows antes del traslado.

## Verificación del preparador y lección de esta ejecución

El [preparador nuevo](../../preparacion-usb/preparar-extraccion-rk3229-c.ps1) verifica identidad exacta del Kingston, tamaño, tipo USB, ausencia de disco de sistema/arranque, FAT32 y marcadores. Rechaza archivos de destino existentes y cualquier plan inesperado. Usa creación exclusiva y conserva un recibo privado separado del resumen público. No repetirlo después de la entrega; no modifica los preparadores ni recibos anteriores.

La primera comprobación sin escritura en Windows PowerShell5 falló antes de acceder al USB: el paso de código Python mediante argumento `-c` perdió comillas y produjo `NameError`. Se corrigió únicamente ese transporte para enviar el código por entrada estándar, conservando argumentos de rutas separados y comprobación de código nativo. El helper pasó en PowerShell5.1; la siguiente comprobación completa `CheckOnly` terminó código0, sin escribir. Después se realizó la única `Prepare`, código0. No fue un fallo físico del Kingston ni una repetición de una escritura fallida.

Hubo revisión independiente del script, sus destinos y la guía; el cambio final de transporte también fue revisado. La guía recibió además una aclaración sobre montajes USB ambiguos. No se agregaron pruebas que simulen una instalación ni se atribuyen estos controles PC a ejecución física del extractor.

## Paso físico preparado y límites

La [guía copiada](LEEME-EXTRACCION-RK3229-C.txt) indica entrar al recovery que el usuario ya sabe abrir, seleccionar almacenamiento externo/USB y abrir:

`TVBASE-EXTRACCION/TVBASE-EXTRACTOR-0.1-ARM32-RECOVERY.zip`

No utilizar Update desde Android, AccesoUSB del P291, el instalador/restaurador P291 ni opciones de wipe. El ZIP extractor no contiene imágenes de ROM y abre los bloques solo en lectura. El recovery anfitrión puede escribir registros o metadatos propios.

**Faltan aceptación de firma, ejecución e imágenes C.** Las firmas de APK observadas no demuestran confianza de recovery. C declara ARM32, Linux3.10.104 y MMC no removible con topología compatible con las comprobaciones del extractor; recovery debe volver a verificarlo. El ioctl ARM32 del extractor es `0x80041272`, no el literal64 que falló en el instalador histórico. Los inicios no están en esta ficha y se obtienen en el dispositivo.

El USB debe estar montado y ser un destino físico válido con escritura. Un rechazo de firma, ruta, montaje, sysfs o ioctl se conserva como evidencia, sin forzar, renombrar paquetes o reiterar automáticamente. Algunas comprobaciones fallan antes de guardar inventario: el texto o foto puede ser la única evidencia nueva.

El resultado esperado de copia es «COPIA Y RELECTURA TERMINADAS». Se vuelve a verificar en PC con [verificar-captura.py](../../diagnostico/extractor-recovery-0.1/verificar-captura.py). Inventario solamente no equivale a respaldo. Puede omitir áreas RW, ocupadas o no admitidas; no desmonta ni copia RPMB. Ni un hash de CID futuro ni la geometría capturada se presentan retrospectivamente como identidad medida por la APK. No se promete duración, copia de todos los chips o restauración ensayada.
