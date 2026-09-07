# Pendrive · intento detenido, no repetir Update

**Resultado vigente:** el intento con la ROM completa quedó al 2 % más de diez minutos después de Copying. Los pasos de instalación de abajo son el registro de lo ya probado, **no una indicación de repetirlos**. [Estado y acción actual](../docs/ESTADO.md) · [Fotos y análisis](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md).

La captura 0.6 terminó correctamente y ya se analizó. Se verificó la firma completa de la ROM con el certificado OTA del primer P291. **La ROM aún no está instalada; su aceptación por el recovery interno no está demostrada.**

Acceso USB 0.7 quedó copiado y leído en el Kingston el 7/9/2026 a las 12:34 ART, con código 0 y SHA coincidente. [Recibo de entrega](../preparacion-usb/entrada-oem-07-estado.json). Solo comprueba el pendrive y abre el menú de actualización original. El primer ensayo usó un ZIP vacío y el siguiente usó la ROM completa; ambos quedaron en la preparación al 2 %. No hay otro recopilador general ni una solución demostrada al atasco del reinicio.

## Pasos ya ejecutados con Acceso USB 0.7

1. Con Android iniciado en el **primer TV P291**, conectar el Kingston.
2. Instalar **AccesoUSB-0.7.apk**, actualizando Acceso USB.
3. Pulsar **«Abrir actualización local»**. Esperar la comprobación: lee el ZIP completo y puede tardar varios minutos.
4. En el menú original, pulsar **Select**, elegir **TVBASE-P291-A9-0.1.1-RECOVERY.zip**, pulsar **Update** y confirmar **Update**.
5. Mantener conectados la alimentación y el pendrive durante la instalación y el respaldo. Si se detiene o queda sin señal, conservar fase, mensaje y tiempo; avisar antes de repetir o cortar la corriente.

La APK 0.7 no instala la ROM ni pulsa Update. El actualizador original prepara el paquete y solicita recovery al confirmar. No activar opciones de borrado si aparecen; el fabricante oculta algunas preferencias y no se garantiza conservar sus datos. El primer Update puede escribir una orden en cache antes de mostrar la confirmación.

El flujo OEM solicita recovery interno. `recovery.img` externo permanece guardado; no se afirma que esta vía lo cargue. La barra de progreso o el apagado no prueban que se haya escrito la ROM. No se requiere WiFi, internet ni Ethernet.

## Archivos y conservación

```text
TVBASE/
├── AccesoUSB-0.7.apk
├── TVBASE-P291-A9-0.1.1-RECOVERY.zip
├── recovery.img
├── TVBASE-MEDIA.txt
├── LEEME-AHORA.txt
├── TVBASE-evidencia-…/        # conservar todas, incluidas parciales
├── TVBASE-diagnostico-…txt
└── … versiones .no-usar y carpetas de Android
```

No se ha obtenido un respaldo original del TV. Conservar cualquier carpeta **TVBASE-respaldo-…** que aparezca. `usb-antes.img` de la PC corresponde al antiguo pendrive.

Preparador en PC: [preparar-entrada-oem-07.ps1](../preparacion-usb/preparar-entrada-oem-07.ps1). Copia por archivos con identidad estable, firma y SHA; no formatea ni cambia particiones. Su ejecución requiere las pruebas finales y el recibo propio para acreditar la entrega.

[Estado completo](../docs/ESTADO.md) · [Captura 0.6](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md) · [Firma contra el P291](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json) · [Receta de la ROM](instalador/README.md).
