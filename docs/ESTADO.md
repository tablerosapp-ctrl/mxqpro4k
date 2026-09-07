# Estado operativo

Estado actualizado: **7/9/2026, 00:00 ART**. Informes adquiridos el6/9 a las23:38. El usuario confirma que Acceso USB0.4 también deja «Sin señal», sin recovery visible. Se leyeron dos informes del Kingston y se comprobó que los tres artefactos entregados siguen intactos. **No repetir el botón0.4.** [Hallazgos nuevos](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md).

La partición recovery existe (24MiB), pero su cabecera y órdenes fueron denegadas a UID2000. Los dos informes son anteriores a pedir el reinicio y solo difieren en la hora; el fragmento pstore no registra el fallo0.4. Acceso USB0.5 recoge evidencia sin reiniciar para leer el actualizador real de este P291 y el registro persistente completo. La APK0.5 ya está copiada y leída/verificada en el Kingston; su primera captura física está pendiente. Aún no hay ROM instalada ni respaldo original del TV confirmado.

## Entregable vigente: evidencia 0.5 sin reinicio

| Archivo | Función | Validación |
| --- | --- | --- |
| `AccesoUSB-0.5.apk` | Recoge registros del arranque y archivos del actualizador original; no solicita reinicio | Compilación/firma, protocolo ADB, guardas y archivos sintéticos en PC; ejecución Android pendiente |
| `recovery.img` | Recovery externo preparado del candidato | Estructura y hashes comprobados; arranque en P291 no demostrado |
| `TVBASE-P291-A9-0.1.1-RECOVERY.zip` | ROM experimental con cinco particiones y respaldo previo obligatorio | Contenido, ext4, firmas y hashes comprobados; instalación física pendiente |
| `TVBASE-MEDIA.txt` | Identifica nuestro medio | Marcador exacto requerido |
| `LEEME-AHORA.txt` | Pasos de recopilación 0.5 | Debe coincidir con la revisión entregada |

[Copia0.5 verificada](../preparacion-usb/evidencia-05-estado.json), proceso con código nativo0: APK45.459bytes y LEEME1.314bytes; lectura SHA coincidente. [Pruebas0.5](../rom-simplificada/instalador/EVIDENCIA-TESTS-0.5.json): 12 escenarios ADB, siete sintaxis y15 casos con archivos sintéticos, más guardas. No acreditan ejecución Android. La APK0.4 se retiró como `.no-usar` y la guía anterior quedó archivada en el USB. La entrega anterior 0.4 queda en el [recibo histórico](../preparacion-usb/entrada-amlogic-estado.json). La ROM y el recovery se conservan; los dos informes anteriores se mantienen íntegros. No elegir versiones `.no-usar`.

Última identificación: Kingston DataTraveler 3.0, USB, 30.943.995.904 bytes, no sistema/no arranque de PC. D: era su letra, FAT32 `TVBASE`, volumen 30.925.651.968 bytes. **La letra no es identidad.** UniqueId:

```text
USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL
```

Marcador: `TVBASE-P291-20260906-4dc82786`. No volver a formatear ni reconstruir el pendrive para la prueba actual.

## Qué ocurrió realmente

1. Tres grabaciones Armbian fallaron; al cambiar la conexión física se obtuvo escritura y lectura correctas. La diferencia apunta a la ruta USB, sin demostrar el componente causal exacto.
2. El TV inició Android habitual con Armbian conectado: no se demostró que ejecutara el USB.
3. El actualizador local encontró el antiguo ZIP vacío. Al ejecutar Update quedó al 2 % más de cinco minutos; tras un ciclo de alimentación volvió Android. Ese ZIP no contenía una ROM.
4. Acceso USB 0.2 falló con «Identificador ADB inesperado». El usuario corrigió su frase anterior «ya está instalando»: **no había llegado a instalar**.
5. Acceso USB 0.3 sí leyó en el primer TV `gxlx2_p291_1g`, API28, UID2000 shell y particiones. Eso confirma consultas ADB locales, no root.
6. Su solicitud `reboot:recovery` dejó «Sin señal» más de diez minutos. Tras un ciclo de alimentación el usuario informó inicio con «Android», aparentemente sin cambios. Nunca se vio recovery ni se eligió el ZIP real. El LED de este equipo no funciona.
7. Se preparó la entrada diferente 0.4: informe previo → hashes → `reboot:update` → posible recovery externo. La recopilación sí funcionó en el TV; el usuario informa de nuevo Sin señal al solicitar update. No hay recovery visible. Los informes no contienen la fase posterior al botón.
8. El7/9 a las00:00 se entregó0.5 sin reinicio. Recoge pstore console/ftrace/dmesg, identifica la Activity de actualización y copia APK candidatos/certificados públicos cuando son legibles. Fija una sola carpeta USB, verifica ocho informes obligatorios y los binarios, y conserva errores. Se comprobaron APK/firma/pruebas/copia; falta ejecutar la captura en el TV.

Evidencias: [hallazgos del primer TV](../diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md), [historia anterior](historico/AGENTS-hasta-20260906-2004.md), [preparación del recovery](../rom-simplificada/instalador/recovery-externo/PREPARADO.json).

## Siguiente paso: obtener evidencia del intento anterior

Con Android iniciado, instalar AccesoUSB-0.5.apk y pulsar **«Guardar evidencia del último intento (no reinicia)»**. Esperar la confirmación de guardado y devolver el Kingston a la PC. [Instrucciones completas](../rom-simplificada/INSTALACION-USB.md).

La siguiente sesión debe conservar primero los originales de la nueva carpeta `TVBASE-evidencia-…`, verificar sus hashes y leer `COMPLETO.txt`. La ausencia del marcador o un error en pantalla significan captura parcial: revisar lo guardado antes de pedir otra ejecución. Los reportes pueden contener datos privados; solo versionar el resumen revisado y sus hashes.

Analizar el pstore completo junto al arranque actual, y el actualizador que resuelva este P291. Decidir con esa implementación si puede recibir el ZIP real y cómo prepara la entrada. `otacerts.zip` permite examinar la validación del paquete en Android; no demuestra por sí solo las claves del recovery instalado. Una lectura denegada queda registrada y no justifica cambiar permisos.

Si en una futura instalación aparece recovery, identificar su origen y registrar aceptación del ZIP antes de afirmar que el acceso funciona. Un error durante escritura no prueba ausencia de cambios. Conservar siempre los respaldos reales si llegan a generarse.

## Límites vigentes

- Coincidir en el DT no demuestra compatibilidad completa de DDR, kernel, bootloader, video, WiFi o control.
- Recovery externo se preparó del candidato, conservando kernel, DTB, ejecutable y 102 entradas del ramdisk. Solo cambia `res/keys` y `prop.default`. La verificación de firmas permanece activa; la aceptación del ramdisk modificado por el cargador instalado no está demostrada.
- La ruta Amlogic de referencia puede limpiar la cabecera de instaboot. Recovery puede procesar órdenes previas en cache/BCB y escribir registros. No afirmar «cero escrituras internas» por el mero hecho de no seleccionar el ZIP.
- No hay respaldo del Android original del TV todavía. `usb-antes.img` es un respaldo del **pendrive anterior**, no del TV.
- La ROM conserva particiones de recuperación/cargador en su receta y desactiva el reemplazo heredado de recovery. La actualización no A/B no es atómica ni tiene rollback automático.
- Chrome 138 es el límite oficial de esta base Android 9. No garantiza Chrome actual indefinidamente ni más rendimiento por su número de versión.
- Actualizador remoto, APK de producto, catálogo de videos y soporte de nuevas placas permanecen en el roadmap.

## Historial del proyecto

Repositorio Git local en `main`, con fuentes, documentación y evidencia revisada. La identidad de automatización es explícita y local; GitHub no está configurado ni publicado. Ver [GIT](GIT.md). El commit no demuestra instalación física.
