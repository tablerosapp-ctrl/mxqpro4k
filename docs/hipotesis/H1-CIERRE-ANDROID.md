# H1 · Bloqueo del cierre de Android

Responsable previsto: Codex. Estado: **hipótesis abierta; revisión conjunta aún no iniciada**.

## Enunciado

El Android actualmente instalado se atasca al cerrar servicios, antes de completar el procesamiento del paquete y el reinicio físico. Cambiar el ZIP o pedir otro modo de reboot no evita ese bloqueo.

## Evidencia disponible

- Último intento: cuatro fotos, ZIP completo seleccionado, Copying, diálogo Android2% durante más de diez minutos. [Resultado](../../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md).
- AOSP9 exacto asigna2% después de broadcast,4% tras ActivityManager,6% tras PackageManager y20% antes de uncrypt. Es una referencia, no el framework extraído del TV.
- Un pstore de intentos anteriores conserva517,24s de actividad del mismo kernel después del aviso de reinicio. No pertenece al intento OEM nuevo y no identifica el servicio culpable.

## Qué falta distinguir

Una UI congelada no localiza por sí sola el hilo detenido. También pueden existir problemas de preparación persistente (H2). El error de SDIO aparece durante Android funcionando y no basta para declarar que WiFi bloquea el apagado.

Confirmaría H1: registro y estado de hilos del mismo intento mostrando que el cierre no regresa, sin alcanzar procesamiento/reinicio de bajo nivel. Refutaría la variante de bloqueo temprano: evidencia del mismo intento mostrando uncrypt finalizado y reinicio físico ejecutado; entonces el fallo está después o la UI quedó desactualizada.

## Revisión requerida

Identificar los puntos de log, propiedades y permisos que permitan registrar ese intervalo mediante el ADB local existente, sin red y sin root. Justificar la supervivencia de cualquier recolector durante el cierre; abrir otra app después del bloqueo no es un método demostrado. Preferir material ya adquirido y no crear otra captura general.

Entregar un diseño acotado de observación y su condición de detención antes de pedir otra prueba física. No repetir Update ni reinicios para obtener un resultado sin instrumentación. Comparar el resultado con H2 antes de modificar ROM o bootloader.
