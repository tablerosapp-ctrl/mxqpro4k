# Investigacion de escritura del Kingston

Identidad: Kingston DataTraveler 3.0, 30943995904 bytes, identificador USB terminado en `KINGSTON_SERIAL_LOCAL`. Las letras D: y E: no identifican el dispositivo fisico.

## Evidencia anterior

Dos grabaciones con Imager 1.8.5 fallaron aproximadamente despues de 2 GB. Una tercera, con Imager 2.0.11.1, fallo el 4/9/2026 a las 23:41 antes de verificar. El registro contiene errores Win32 5, 433 y 55, escrituras pendientes durante segundos, evento Windows disk 153 y nueva llegada del dispositivo. La ruta era USB(3)/HS03.

El 5/9 a las 00:01 se recupero el volumen con DiskPart y formato exFAT. Antes de recuperar, Windows identificaba el dispositivo completo pero mostraba una pseudoparticion en offset 0 y NTFS de aproximadamente 3 GB, sin letra. La cabecera guardada confirma NTFS directamente en sector 0. La recuperacion y una comprobacion de 1 MiB pasaron; no acreditan la memoria completa ni escrituras largas.

## Consulta de fuentes del 5/9/2026

- Las [notas oficiales de Imager 2.0.11](https://github.com/raspberrypi/rpi-imager/releases/tag/v2.0.11) describen cambios en los bloqueos de volumen, sincronizacion y manejo del tamano de dispositivos en Windows. La version utilizada, 2.0.11.1, los incluye. La [actualizacion 2.0.11.1](https://github.com/raspberrypi/rpi-imager/releases/tag/v2.0.11.1) no anuncia otro arreglo de nuestro error concreto.
- La consulta de incidencias oficiales encontro un [reporte de verificacion intermitente en 2.0.11.1](https://github.com/raspberrypi/rpi-imager/issues/1721). No reproduce nuestra evidencia: nuestro fallo ocurrio durante escritura y antes de verificar. No se puede atribuir nuestra averia a ese reporte.
- El registro local muestra escritura asincrona y limites informados por el dispositivo. Que existan varias escrituras pendientes no demuestra por si solo un defecto del grabador.

## Prueba con la nueva conexion

El usuario cambio fisicamente el puerto. Windows confirmo a las 00:04:45 una nueva llegada en USB(16)/SS04. El Kingston seguia vacio en E:, exFAT. Se mantuvieron imagen, hash y grabador 2.0.11.1, con verificacion habilitada. La ruta USB queda guardada por intento.

Intento iniciado a las 00:06:59. Directorio: `grabacion-20260905-000644-562f503b`. El limite de transferencia anunciado paso de 65536 a 524288 bytes; profundidad de cola efectiva 6 en ambos intentos. Es una diferencia concreta entre conexiones, no una demostracion de causa raiz.

El resultado definitivo de este intento se registra en `estado-grabacion.json` y en el `resultado.json` de ese directorio. No confundir `verificacion: true` (opcion habilitada) con `verificacion_completada: true` (proceso terminado correctamente).

## Resultado

Exito a las 00:11:26 del 5/9/2026: codigo de salida 0, escritura 230 segundos, verificacion 35.103 segundos, ciclo `succeeded` y expulsion solicitada. El hash leido coincide con el original: `4479b09374d92ffe4be625b5dded96c5d7d7a0e8c6bcb0a7d2894a839214a2f8`. No hubo que cambiar de imagen, herramienta o desactivar la verificacion.

El resultado es compatible con un problema de la conexion/ruta USB anterior o de su interaccion con la escritura; no permite aislar contacto, alimentacion, controlador o software como causa precisa. Ya hay una imagen verificada: corresponde avanzar a la prueba en el TV box y evitar mas regrabaciones por rutina.
