# Pendrive · diagnóstico del último intento con Acceso USB0.8

**Entrega vigente:0.8, copiada y leída el7/9/2026 a las15:54 ART.** [Recibo](../preparacion-usb/postintento-08-estado.json). La ROM completa quedó detenida al2% con el actualizador OEM; todavía no hay instalación ni respaldo del TV confirmados. Esta captura aplica las partes de la [revisión de Fable](../docs/hipotesis/REVISION-CONJUNTA-FABLE.md) que permiten observar el fallo sin otro reinicio.

1. Cuando el **primer TV P291** muestre Android normalmente, conectar el Kingston.
2. Instalar **AccesoUSB-0.8.apk**, actualizando Acceso USB, y abrirla.
3. Pulsar una vez **«Guardar diagnóstico del último intento»**. Esperar el resultado; puede tardar unos minutos.
4. Al terminar, o si muestra un error, devolver el pendrive a esta PC. No repetirlo; conservar el mensaje de error.

No pulsar Update ni los botones de reinicio anteriores. Si Android sigue detenido en actualización, la captura aún no puede ejecutarse: comunicar ese estado. El resultado del último ciclo de alimentación sigue sin confirmar.

La APK busca registros anteriores y consulta WiFi, Bluetooth, batería, espacio y WebView. No cambia radios ni solicita instalación. Usa únicamente la conexión ya disponible dentro del TV; no requiere internet/Ethernet. Una salida denegada o agotada por tiempo también se guarda. «Completa» significa recorrido y archivos comprobados, no respuesta satisfactoria de todos los servicios.

## Contenido y conservación

```text
TVBASE/
├── AccesoUSB-0.8.apk
├── TVBASE-P291-A9-0.1.1-RECOVERY.zip   # conservada; no repetir Update
├── recovery.img                     # conservado; arranque no demostrado
├── TVBASE-MEDIA.txt
├── LEEME-AHORA.txt
├── TVBASE-evidencia-…/               # informes anteriores conservados
├── TVBASE-diagnostico-…txt
└── carpetas de Android y del volumen
```

Cada captura0.8 crea `TVBASE-postintento-...`. Conservar las carpetas parciales y cualquier `TVBASE-respaldo-*`. No existe un respaldo original del TV confirmado; `usb-antes.img` en PC es del antiguo pendrive.

Se retiraron14 archivos antiguos o reemplazados,573.327.869 bytes, tras archivarlos en PC y verificar sus hashes. Incluye APK0.2–0.7, guías anteriores, ROM0.1 retirada y ZIP de Fable. ROM0.1.1, recovery, informes y marcador permanecen. No se formateó ni reparó el volumen.

Preparador vigente: [preparar-postintento-08.ps1](../preparacion-usb/preparar-postintento-08.ps1). Exige identidad exacta del Kingston, pruebas, fuentes y firma de la APK; copia y verifica por lectura. La limpieza usa una lista de archivos explícitos, sin borrar carpetas. [Guía que está en USB](instalador/LEEME-POSTINTENTO-0.8.txt).

El intento0.7 queda documentado en [fotos y análisis](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md), su [recibo](../preparacion-usb/entrada-oem-07-estado.json) y el [estado](../docs/ESTADO.md). No es la instrucción vigente de instalación.
