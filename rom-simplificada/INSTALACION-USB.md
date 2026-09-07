# Pendrive · instrucciones vigentes

La entrada de Acceso USB **0.4** también dejó el primer P291 sin señal. No se vio recovery ni se instaló el ZIP. La revisión **0.5** recoge evidencia del último intento **sin reiniciar**. La ROM preparada sigue siendo **0.1.1**; esta revisión cambia la herramienta de acceso, no la ROM.

**Entrega verificada el7/9/2026 a las00:00 ART:** APK0.5 y guía copiadas y leídas; ROM/recovery conservados. [Recibo](../preparacion-usb/evidencia-05-estado.json) · [Estado operativo](../docs/ESTADO.md).

## Pasos con Acceso USB 0.5

1. Con Android ya iniciado en el **primer TV P291**, conectar el Kingston.
2. Abrir el pendrive e instalar **AccesoUSB-0.5.apk**, actualizando la aplicación anterior.
3. Abrir Acceso USB y pulsar **«Guardar evidencia del último intento (no reinicia)»**.
4. Esperar el resultado en pantalla. Debe indicar que la evidencia quedó guardada; Android permanece encendido. Si aparece un error, conservar el texto y los archivos parciales.
5. Volver a conectar el Kingston a la PC para analizar la nueva carpeta **TVBASE-evidencia-…**. No borrar los informes anteriores.

Este paso obtiene el registro persistente completo, los datos del arranque actual, el APK del actualizador original y sus certificados públicos cuando Android permite leerlos. Cada lectura denegada queda registrada. Una carpeta parcial no equivale a una recopilación completa: la marca `COMPLETO.txt` solo se escribe tras verificar la secuencia y los archivos guardados.

Instalar esta APK no instala la ROM. No hay que pulsar Update, elegir el ZIP ni repetir los botones de reinicio de las versiones anteriores. La vía del actualizador original se decidirá después de analizar su implementación en **este P291**; el APK del segundo TV P271 no acredita el mismo comportamiento.

## Archivos conservados

```text
TVBASE/
├── AccesoUSB-0.5.apk           # recopilación sin reinicio
├── recovery.img               # preparado, arranque aún no demostrado
├── TVBASE-P291-A9-0.1.1-RECOVERY.zip
├── TVBASE-MEDIA.txt
├── LEEME-AHORA.txt
├── TVBASE-diagnostico-…txt     # informes anteriores
├── TVBASE-evidencia-…/         # aparecerá al ejecutar 0.5
└── … versiones .no-usar y carpetas de Android
```

No hay un respaldo original del TV confirmado. Si llega a crearse una carpeta **TVBASE-respaldo-…**, conservarla íntegra. El archivo `usb-antes.img` guardado en la PC respalda el antiguo pendrive, no el TV.

La preparación es una copia por archivos, sin formato ni cambios de partición. La herramienta vigente en PC es [preparar-evidencia-05.ps1](../preparacion-usb/preparar-evidencia-05.ps1): identifica el Kingston de forma estable, comprueba firma y pruebas, copia y lee para verificar. No elige por letra solamente y no debe ejecutarse de nuevo por rutina.

[Hallazgos que motivan el cambio](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md) · [Implementación y límites de la ROM](instalador/README.md).
