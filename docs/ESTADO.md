# Estado operativo

Actualización del **7/9/2026 a las00:22 ART**, tras adquirir dos capturas de Acceso USB0.5. Ambas fallaron en etapa5 porque cuatro archivos de GMS consumieron el límite antes de OTAUpgrade. Además, un alias de Android anuló el cálculo SHA de binarios: los valores vacíos no acreditan su verificación en el TV. Los seis informes de texto por captura sí tienen SHA coincidente, y todas las copias USB→PC fueron verificadas. [Hallazgos](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md).

El pstore completo muestra que, tras cortar HDMI y entrar en la preparación del reinicio, el mismo kernel siguió activo517,24segundos. Favorece un atasco al cerrar el sistema antes del reinicio físico. La partición recovery existe, pero no se leyó su contenido ni se demostró su ejecución. **No hay ROM instalada ni respaldo original del TV confirmado.**

## Entregable vigente: complemento0.6 sin reinicio

| Archivo | Función | Estado |
| --- | --- | --- |
| `AccesoUSB-0.6.apk` | Autocontrol SHA → certificados → OTAUpgrade → configuración → cierre | Pruebas locales y copia/lectura USB verificadas; primera ejecución0.6 enTV pendiente |
| `recovery.img` | Recovery externo del candidato | Preparado/verificado localmente; arranque no demostrado |
| `TVBASE-P291-A9-0.1.1-RECOVERY.zip` | ROM experimental con respaldo previo y cinco particiones | Preparado/verificado localmente; no instalado |
| `TVBASE-MEDIA.txt` | Identifica el medio autorizado | Marcador exacto requerido |
| `LEEME-AHORA.txt` | Pasos del complemento vigente | Copiado y leído junto a la APK0.6 |

[Entrega0.6 verificada](../preparacion-usb/evidencia-06-estado.json): APK41.363B y guía1.216B, código nativo0, lectura SHA coincidente. Pruebas12ADB,5sintaxis POSIX+5mksh y20fixtures de funciones con mksh real. ROM/recovery y ambos informes se conservaron; APK0.5 quedó `.no-usar`.

Las entregas [0.5](../preparacion-usb/evidencia-05-estado.json) y [0.4](../preparacion-usb/entrada-amlogic-estado.json) conservan sus recibos. Su copia correcta en PC no demuestra una captura o un reinicio correcto en Android. No volver a ejecutar esas versiones.

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
8. El7/9 a las00:00 se entregó0.5 sin reinicio. Recoge pstore console/ftrace/dmesg, identifica la Activity de actualización y copia APK candidatos/certificados públicos cuando son legibles. Fija una sola carpeta USB, verifica ocho informes obligatorios y los binarios, y conserva errores. Se comprobaron APK/firma/pruebas/copia enPC. La ejecución física llegó a etapa5 y falló; sus controles SHA binarios tenían un defecto no cubierto por aquellas pruebas.
9. Se recuperaron dos capturas0.5 y se reprodujo la colisión del nombre hash con un alias incorporado de mksh. El complemento0.6 usa nombres propios, SHA estricto y autocontrol, y selecciona directamente los archivos faltantes.

Evidencias: [hallazgos del primer TV](../diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md), [historia anterior](historico/AGENTS-hasta-20260906-2004.md), [preparación del recovery](../rom-simplificada/instalador/recovery-externo/PREPARADO.json).

## Siguiente paso: estudiar los archivos que faltan

Con0.6 ya entregada, instalarla con Android iniciado y pulsar **«Guardar archivos que faltan (no reinicia)»**. Esperar la confirmación y devolver el USB a la PC. [Pasos vigentes](../rom-simplificada/INSTALACION-USB.md).

La siguiente sesión debe conservar los originales de la nueva carpeta, verificar los SHA y comprobar `COMPLETO.txt`. En0.6 son obligatorios OTAUpgrade y otacerts; un error o carpeta parcial exige revisar lo existente antes de solicitar otra captura. Los informes crudos permanecen privados; versionar conclusiones revisadas y hashes.

Analizar la implementación real de `com.droidlogic.otaupgrade`, que en este P291 está en `/product/app/OTAUpgrade/OTAUpgrade.apk`, usa UID1000 y tiene permisos REBOOT/RECOVERY. Determinar cómo valida el ZIP y prepara las órdenes persistentes de recuperación. Sus permisos no demuestran por sí solos que consiga reiniciar ni que recovery acepte nuestra firma. No repetir `reboot:update`, el ZIP vacío ni cambiar permisos para evitar esta investigación.

Si una futura instalación llega a escribir particiones, un error no equivale a ausencia de cambios. Conservar siempre los respaldos reales antes de ampliar pruebas.

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
