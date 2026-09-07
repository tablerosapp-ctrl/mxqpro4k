# Decisiones y lecciones

Cada decisión identifica su alcance. Las referencias de AOSP/Amlogic explican el diseño, pero no prueban que el cargador instalado en el P291 sea idéntico.

| ID | Decisión y motivo | Consecuencia / revisión |
| --- | --- | --- |
| ADR-01 | Android nativo interno y APK común, por pedido del usuario y referencia funcional actual | Armbian sirve solo como herramienta temporal. No sustituir el objetivo por actualizar Chrome en el sistema chino. |
| ADR-02 | Perfil por placa; P291 es destino y P271 diagnóstico | Un nombre comercial o un DT coincidente no acredita todos los drivers. Confirmar capacidades en cada placa. |
| ADR-03 | Conservar APIs y multimedia mientras se quita software prescindible | No borrar bibliotecas por su nombre ni recortar funciones por la APK actual. Medir VP9/alfa/canvas. |
| ADR-04 | Chrome138 Monochrome más overlay en la base Android9 inicial | Navegador instalado no acredita proveedor WebView efectivo. Android9 limita futuras versiones oficiales. |
| ADR-05 | ZIP con respaldo y cinco particiones; boot al final | Evita incorporar bootloader/DDR de fábrica en la receta. No hace atómica la actualización ni garantiza recuperación. |
| ADR-06 | ROM0.1.1 desactiva scripts heredados de reemplazo de recovery | Omitir una partición al flashear no basta si Android la escribe en el siguiente arranque. 0.1 queda retirada. |
| ADR-07 | Corregir cierres/canales ADB según protocolo | 0.2 falló; 0.3 pasó consultas físicas. Mantener AUTH, checksum e IDs desconocidos como errores, sin deshabilitar autenticación. |
| ADR-08 | Tras fallar `reboot:recovery`, probar `reboot:update` con recovery externo del candidato | Hipótesis basada en código de referencia; la prueba0.4 también quedó sin señal. No repetirla sin evidencia nueva (ADR-13). |
| ADR-09 | Informe y SHA antes de pedir update; sin reintentos automáticos | Conserva el estado previo, pero no captura el fallo posterior; por eso se agrega0.5 sin reinicio. No saltar una denegación de escritura/lectura del USB. |
| ADR-10 | Añadir clave pública AOSP al recovery externo y mantener verificación | La clave original del candidato era diferente. Solo cambiar lista de confianza y propiedades; no desactivar la comprobación de firma. Clave experimental, no de producción. |
| ADR-11 | Identificar USB establemente y comprobar lectura | D:/E: y número de disco cambian. No repetir fallos sin cambio concreto/evidencia; herramientas en PC. |
| ADR-12 | Documentación por estado, contratos, grafo y evidencia; limpieza auditada | Conservar historia sin dejar pasos retirados como instrucciones activas. No mover fuentes si los scripts dependen de sus rutas. |
| ADR-13 | Tras fallar update0.4, recopilar sin reiniciar el actualizador real y pstore completo del P291 | Los informes previos no registran el fallo; la partición recovery existe pero no pudo leerse. No repetir otra entrada sin nueva evidencia. |
| ADR-14 | Git local con fuente/documentación/evidencia revisada y artefactos grandes fuera | Excluir claves e informes crudos. Autoría temporal explícita del agente; GitHub aún sin destino ni publicación. |

## Incidentes que no deben repetirse

- **USB y formato:** tres grabaciones fallaron con errores nativos y redetección. Cambiar letra no cambió la conexión. La cuarta funcionó tras cambiar físicamente de ruta. «No aparece en Explorador» no equivalía a «no existe el disco». El volumen pudo recuperarse. No atribuir causa precisa sin evidencia.
- **ZIP vacío:** llegó a selección pero terminó detenido al 2 %. Volvió Android. No es instalador de ROM y ya no está activo en el USB.
- **Error de ADB 0.2:** el cliente respondía CLSE y confundía mensajes tardíos de canales cerrados. Los cierres no se responden, se ignoran paquetes de canales completados de la misma conexión y se acepta CLSE remoto cero heredado. 0.3 confirmó consultas reales.
- **Sin señal tras recovery:** no demuestra instalación oculta, apagado físico ni recovery averiado. El LED no funciona. No inferir root de UID shell/userdebug/test-keys.
- **debugfs:** el port Cygwin creó nombres literales con barras al usar destinos absolutos de `write`. Usar `cd`, nombre simple y verificar contenido, metadatos y fsck. Se conservan comandos/causa/logs; la imagen defectuosa local fue eliminada en la limpieza.
- **Preservación de recovery:** auditar scripts y servicios del siguiente arranque además de la lista de particiones que escribe el ZIP.
- **Versiones:** no copiar la APK nueva bajo nombre viejo. Los preparadores0.2/0.3/0.4 son históricos; el actual es `preparar-evidencia-05.ps1`.

## Evidencia de la entrada alternativa

El [servicio ADB Android9](https://android.googlesource.com/platform/system/core/+/refs/tags/android-9.0.0_r1/adb/services.cpp) solicita `sys.powerctl` con el argumento recibido. La [implementación Amlogic de reinicio](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/common/cmd_reboot.c) distingue recovery/factory_reset de update. La [configuración de referencia P271](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/board/amlogic/configs/gxl_p271_v1.h) busca recovery externo en su flujo update; su copia está en `instalador/gxl_p271_v1-referencia.h`. **La inferencia que motivó0.4** era que ese modo podía alcanzar USB donde recovery no lo hizo; el ensayo no consiguió un menú visible. No es una lectura del U-Boot instalado en el primer TV.

La rutina [wipeisb](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/common/cmd_wipeisb.c) puede limpiar 4096 bytes de la cabecera instaboot si existe. Recovery puede procesar órdenes anteriores. Por eso no se afirma que entrar en ese modo sea totalmente ajeno a escrituras internas.

El [verificador de recovery AOSP](https://android.googlesource.com/platform/bootable/recovery/+/721f679/verifier.cpp) define claves `v3` RSA2048/exponente3/SHA256. Se conservó la clave del recovery candidato y se agregó la que verifica nuestro ZIP, sin modificar el ejecutable verificador. [Prueba local exacta](../rom-simplificada/instalador/recovery-externo/PREPARADO.json). Esto no prueba autenticación/arranque del ramdisk por el cargador real.


Evidencia de ADR-13: [análisis de informes0.4](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md). Implementación/criterios de ADR-14: [historial local y GitHub](GIT.md).
