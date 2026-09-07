# Estado operativo

Actualización del **7/9/2026, tras el intento físico con ROM completa**. Cuatro fotos muestran menú OEM → ZIP0.1.1 seleccionado y confirmado → Copying → diálogo de preparación Android al 2 %. El usuario confirma **más de diez minutos sin avance**. [Evidencia y análisis](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md).

**No hay instalación ni respaldo original del TV confirmados. No repetir Update.** La captura0.6 y las verificaciones criptográficas siguen válidas; no acreditan que el sistema consiga cerrar ni que recovery se haya ejecutado.

La referencia exacta Android9 sitúa 2 % después de la notificación de apagado y antes de regresar del cierre de ActivityManager; el procesamiento del paquete llega después. Esto favorece un atasco del cierre, aunque el framework del TV no se extrajo y la interfaz podría estar congelada. No atribuir una causa definitiva ni asegurar que no hubo escrituras de preparación.

Próxima acción física: un único ciclo de alimentación de diez segundos para salir del bloqueo, conservando el USB. No se presupone BCB/mapa correcto ni se promete que el corte carezca de riesgo. Si aparece instalación real, dejarla continuar; si aparece recovery/error, conservar el texto sin elegir wipe; si vuelve Android, no repetir Update. **Resultado del ciclo pendiente.**

## Qué habilita la evidencia nueva

- Se obtuvo el APK original de OTAUpgrade del primer P291. Coincide byte por byte con el APK antes leído del P271: se reutiliza el análisis del código, sin equiparar el hardware de ambos equipos.
- La firma integral de `TVBASE-P291-A9-0.1.1-RECOVERY.zip` pasó dos verificaciones independientes contra los certificados OTA capturados del P291. La confianza del Android actual coincide; las claves del recovery interno siguen sin leerse. [Recibo criptográfico](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json).
- En API28, el actualizador original copia el paquete USB a `/data/cache/update.zip`, prepara `uncrypt_file`, solicita BCB y luego `recovery-update`. El mapa de bloques depende del framework. El código no confirma la integridad de la copia interna ni la persistencia de BCB/mapa. [Análisis del APK](../diagnostico/primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md).
- La referencia Amlogic consulta BCB para arrancar recovery **interno**. Esto no demuestra el comportamiento del cargador instalado ni que vaya a cargar `recovery.img` del pendrive.

El menú Select/Update ya se abrió al principio, pero solo recibió el ZIP vacío de 22 bytes, que quedó al 2 %. El intento nuevo con la ROM completa llegó también al 2 % y quedó detenido. Acceso USB 0.7 verifica ese paquete y el APK original antes de abrir el mismo menú. **No corrige por sí mismo el atasco al reiniciar ni constituye otro método de flasheo.**

## Último entregable probado: Acceso USB 0.7

La APK solo abre **«Abrir actualización local»** tras comprobar el perfil P291/API28, el USB marcado, la integridad del ZIP y la identidad del actualizador. La selección y confirmación de Update quedan en el menú original. No hace otra captura general ni solicita un reinicio propio.

[Entrega 0.7 verificada](../preparacion-usb/entrada-oem-07-estado.json): copiado y leído el 7/9/2026 a las 12:34 ART, proceso terminado con código 0. APK de 29.075 bytes y guía de 1.537 bytes; hashes coincidentes. Pruebas locales: 12 casos ADB, 23 escenarios mksh, sintaxis de ambas etapas y controles de secuencia/perfil. Se conservan la ROM, recovery y todos los informes; 0.6 quedó retirada como .no-usar. [Pasos vigentes](../rom-simplificada/INSTALACION-USB.md). La ROM continúa siendo 0.1.1: no hace falta cambiar su firma por este hallazgo.

| Archivo | Función | Límite |
| --- | --- | --- |
| `AccesoUSB-0.7.apk` | Comprobar y abrir explícitamente el menú OEM | Menú OEM observado; Update con ROM real detenido al 2 % |
| `TVBASE-P291-A9-0.1.1-RECOVERY.zip` | ROM experimental con respaldo previo y cinco particiones | Sin instalación física; recovery interno aún no validado |
| `recovery.img` | Recovery externo preparado del candidato | Conservado; esta vía OEM solicita recovery interno |
| `TVBASE-MEDIA.txt` | Identifica el medio autorizado | Marcador exacto requerido |
| `LEEME-AHORA.txt` | Instrucciones de la entrega activa | Debe coincidir con su recibo |

No activar borrados opcionales. En API28 el fabricante oculta sus casillas y puede tener preferencias privadas no leídas; no se garantiza conservar los datos del Android anterior. El primer Update ya puede escribir una orden en cache antes de mostrar la confirmación. Una barra, apagado o ausencia de señal no acreditan copia íntegra, BCB, recovery ni instalación. Si se repite el atasco, registrar fase, mensaje y tiempo; no prescribir un corte eléctrico suponiendo que la preparación terminó.

## Antecedentes que siguen siendo relevantes

1. Tres grabaciones Armbian fallaron; una cuarta terminó verificada tras cambiar físicamente la conexión USB. El TV siguió iniciando Android: no se demostró arranque de Armbian.
2. El ZIP vacío seleccionado originalmente no contenía ROM. Acceso 0.2 falló en el protocolo ADB; 0.3 corrigió las consultas, pero su petición de recovery quedó sin señal.
3. La entrada 0.4 con `reboot:update` tampoco mostró recovery. Sus dos informes preceden a esa solicitud; no describen el fallo posterior.
4. Las dos capturas 0.5 quedaron incompletas por la cuota consumida por GMS. El alias `hash` de mksh dejó vacíos los digests binarios. Los textos sellados y la adquisición en PC tienen validaciones separadas. [Hallazgos 0.5](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md).
5. Su pstore completo muestra 517,24 segundos de actividad del mismo kernel después del aviso de reinicio. Favorece un atasco durante el cierre previo al reinicio físico, sin identificar la función culpable. No demuestra ausencia de recovery ni causa SDIO.
6. La captura 0.6 sí obtuvo OTAUpgrade, otacerts y configuración accesible. La raíz init permanece denegada; una sección filtrada vacía de uncrypt no demuestra que falten sus servicios.

Las entregas anteriores conservan sus recibos: [0.6](../preparacion-usb/evidencia-06-estado.json), [0.5](../preparacion-usb/evidencia-05-estado.json) y [0.4](../preparacion-usb/entrada-amlogic-estado.json). No volver a ejecutarlas por rutina.

## Identidad del destino y límites

Primer TV: `gxlx2_p291_1g`, Android9/API28, shell UID2000; LED sin funcionamiento. El segundo P271 no es destino. El primer TV no requiere red: la conexión existente de la APK es ADB local dentro del propio equipo.

Kingston DataTraveler 3.0, USB, 30.943.995.904 bytes, no sistema/no arranque de PC. Última letra D:, FAT32 `TVBASE`, volumen 30.925.651.968 bytes. La letra no es identidad:

```text
USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL
```

Marcador `TVBASE-P291-20260906-4dc82786`. No formatear ni reconstruir el pendrive para esta entrega. Conservar todos los informes y cualquier `TVBASE-respaldo-*` nuevo. `usb-antes.img` respalda el antiguo pendrive, no el TV.

La ROM conserva recovery/cargador en su receta y desactiva los scripts heredados que reemplazaban recovery al arrancar. Instala system, vendor, product, odm y boot al final, con respaldo previo y lectura de hashes. No A/B, sin rollback automático ni restauración ensayada. El boot contiene kernel/DTB del candidato: la coincidencia del DT no demuestra compatibilidad completa de video, WiFi, DDR o control.

Chrome138 es el techo oficial de esta base Android9. El proveedor WebView efectivo y el rendimiento de VP9/alfa/canvas siguen pendientes de prueba física. Aplicación, administración remota y soporte de nuevas placas permanecen en el roadmap.

## Historial

Git local en `main`, con fuentes, documentación y evidencia revisada. Binarios, claves e informes crudos permanecen locales. GitHub no está configurado ni publicado. [Flujo Git](GIT.md).

La APK0.7 no guarda un registro posterior a Update. No afirmar que habrá un nuevo reporte de este atasco en el pendrive sin leerlo. Las fotos actuales son la evidencia del intento; el pstore anterior corresponde a otra solicitud.
