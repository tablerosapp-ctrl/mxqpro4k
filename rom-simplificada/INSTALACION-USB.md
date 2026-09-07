# Pendrive · instrucciones vigentes

Acceso USB0.5 produjo dos capturas parciales: el límite de APK detuvo la recopilación antes de OTAUpgrade y se encontró un defecto en la comprobación SHA de binarios. Ambas carpetas ya están conservadas en la PC. La versión **0.6** obtiene únicamente los archivos que faltan, **sin reiniciar**. La ROM sigue siendo0.1.1 y no está instalada.

**Copia0.6 verificada el7/9/2026 a las00:22 ART**, código0 y lectura SHA coincidente. [Recibo de entrega](../preparacion-usb/evidencia-06-estado.json) · [Estado](../docs/ESTADO.md).

## Pasos con Acceso USB0.6

1. Con Android iniciado en el **primer TV P291**, conectar el Kingston.
2. Instalar **AccesoUSB-0.6.apk**, actualizando la aplicación anterior.
3. Pulsar **«Guardar archivos que faltan (no reinicia)»**.
4. Esperar la confirmación de guardado. Android permanece encendido. Si hay un error, conservar el mensaje y los archivos parciales sin repetir la captura.
5. Conectar el Kingston a la PC para analizar la carpeta nueva **TVBASE-evidencia-…**.

El complemento comprueba primero un SHA conocido, copia los certificados OTA públicos y el APK **OTAUpgrade** identificado en este P291, y guarda la configuración de arranque accesible. No copia Servicios de Google ni repite pstore. El APK y los certificados son obligatorios para declarar completo el complemento; la configuración puede registrar permisos denegados.

No hay que abrir Update ni elegir el ZIP durante este paso. La recopilación no solicita reinicio ni instalación. El registro recuperado apunta a un atasco del cierre del sistema, pero aún no se ha identificado su causa exacta ni demostrado una vía de instalación.

## Archivos y conservación

```text
TVBASE/
├── AccesoUSB-0.6.apk
├── recovery.img
├── TVBASE-P291-A9-0.1.1-RECOVERY.zip
├── TVBASE-MEDIA.txt
├── LEEME-AHORA.txt
├── TVBASE-evidencia-…/        # conservar todas, incluidas parciales0.5
├── TVBASE-diagnostico-…txt
└── … versiones .no-usar y carpetas de Android
```

No se ha obtenido un respaldo original del TV. Conservar cualquier carpeta **TVBASE-respaldo-…** que llegue a generarse. El respaldo `usb-antes.img` de la PC corresponde al antiguo pendrive, no al TV.

Preparador vigente en PC: [preparar-evidencia-06.ps1](../preparacion-usb/preparar-evidencia-06.ps1). Copia por archivos, con identidad estable y lectura SHA; no formatea ni modifica particiones. No ejecutarlo otra vez por rutina.

[Hallazgos de las dos capturas](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md) · [Defecto SHA y reproducción](instalador/MKSH-HALLAZGO-0.5.md) · [Implementación de la ROM](instalador/README.md).
