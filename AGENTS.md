# Continuidad de TV Base

Leer primero [README](README.md), [estado](docs/ESTADO.md), [especificación](docs/ESPECIFICACION.md), [mapa](docs/MAPA-ARCHIVOS.md) y [roadmap](docs/ROADMAP.md). La crónica completa anterior está conservada en [histórico](docs/historico/AGENTS-hasta-20260906-2004.md); sus referencias eran relativas a la raíz y sus “estados vigentes” son históricos.

## Objetivo y autorización

- Android simplificado en memoria interna, instalado desde pendrive, con WebView/navegador mejorado, drivers y APIs compatibles con una APK en evolución. La APK terminada no bloquea preparar la plataforma. No sustituirlo por actualizar Chrome en el Android chino. No investigar la actualización automática que dañó WiFi.
- El usuario autoriza preparar el Kingston y la instalación final interna en el PRIMER TV; la autorización persiste. Revalidar destino/contenido; no volver a pedirla por rutina. También autorizó ordenar, limpiar lo innecesario y documentar el proyecto.
- El primer TV no se conectará a Ethernet/red como requisito. El ADB de Acceso USB usa exclusivamente 127.0.0.1:5555 ya disponible. No habilitar root ni alterar autenticación.

## Estado que prevalece · 7/9/2026 00:00 ART

- PRIMER TV: P291, DT gxlx2_p291_1g, Android9/API28, UID2000 shell confirmado por foto de APK0.3. LED roto. SEGUNDO TV leído por WiFi: P271 gxlx_p271_1g; NO destino de esta ROM. No extrapolar su firmware/certificados/particiones al P291.
- Antecedente0.3: reboot:recovery de APK0.3 dejó Sin señal más de diez minutos; tras un ciclo de alimentación el usuario informó inicio con Android, aparentemente sin cambios. No se vio recovery ni se seleccionó el ZIP real. No hay instalación ni respaldo original del TV confirmados.
- Entregable0.4 probado: ROM TVBASE-P291-A9-0.1.1-RECOVERY.zip + AccesoUSB-0.4.apk + recovery.img + marcador/LEEME-AHORA. Kingston copiado y LEÍDO/verificado, código nativo0, recibo preparacion-usb/entrada-amlogic-estado.json. Resultado físico0.4: otra vez Sin señal, sin recovery visible. No repetir ese botón. Reportes adquiridos en diagnostico/primer-tv-reportes-20260906-233826; resumen saneado y hallazgos versionables.
- APK0.4: informe en USB marcado, SHA de ROM/recovery, una solicitud reboot:update. Recovery externo del mismo candidato conserva kernel/DTB/ejecutable y cambia solo res/keys y prop.default; añade la clave pública de prueba del ZIP, manteniendo verificación. No se flashea la partición recovery con ese archivo. No está probado que el cargador instalado acepte/ejecute este recovery. Código Amlogic de referencia puede limpiar cabecera instaboot y recovery puede procesar órdenes previas: no afirmar cero escrituras internas.
- ROM0.1.1 desactiva install-recovery.sh y flash_recovery heredados; conserva Chrome138 e inicio propio. Instala system/vendor/product/odm/boot con respaldo original previo y lectura de hashes; preserva el resto según receta. No A/B, sin rollback ni restauración automática probados. Boot contiene kernel/DTB del candidato: preservar la partición DTB no acredita toda compatibilidad.
- APK0.4 pasó 12 casos locales ADB y 7 controles de secuencia. La captura0.4 sí se ejecutó en el TV; su entrada no mostró recovery. Proveedor WebView/rendimiento de la ROM siguen sin prueba física. Ver docs/evidencias antes de afirmar éxito físico.

- Nueva evidencia: recovery existe (179:6,24MiB), eMMC7.650.410.496B, system1.342.177.280B y vendor943.718.400B. No extrapolar product/odm sin aliases. ro.boot.bootreason y sys.boot.reason=recovery no prueban ejecución de recovery. Dos informes0.4 son pre-solicitud e idénticos salvo hora; reloj2020 no fiable. Pstore tail6000B idéntico/corrupto con SDIO CMD53timeouts, no demuestra fallo de USB/eMMC ni causa del apagado. Lectura de recovery/cache denegada como shell.
- Entregable vigente0.5: AccesoUSB-0.5.apk (45459B, SHA7e251f9d202c6ac9407734f2ca4c19077a8b02994f3a115205fdc10cf21b0874) y guía copiados/verificados, código0, recibo preparacion-usb/evidencia-05-estado.json. APK0.4 y guía retiradas con nombre histórico; ROM/recovery/reportes conservados. Pruebas12ADB,7sintaxis,15fixtures y guardas, solo PC. Próxima acción: instalar0.5 y recopilar SIN reiniciar; obtener actualizador real P291, otacerts públicos, pstore completo y boot_id/uptime/propiedades. No volver a Update con ZIP vacío ni pedir root/cambiar permisos. APKdel P271 no prueba flujo/certificados del primero. La captura física0.5 falta. Lee ocho informes obligatorios, pstore console/ftrace/dmesg binario, resuelve Activity real y copia candidatos APK públicos con límites y hashes. Nunca vuelve a pedir reboot. Los binarios/documentos0.4 se preservan como antecedente.
- Git local iniciado en main. Fuentes, docs y resúmenes saneados se versionan; claves/binarios/herramientas/capturas crudas quedan locales. Autoría de automatización Codex (registro local), codex@local.invalid, solo configlocal. GitHub no creado ni publicado. Revisar docs/GIT.md y git status antes de continuar.

## Pendrive y operaciones

- Identidad exacta: Kingston DataTraveler3.0, 30943995904 bytes, USB, no sistema/no boot de PC; UniqueId USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL. D: era su letra al entregar, FAT32 TVBASE. Nunca elegir por letra/número solamente.
- Herramienta vigente de COPIA POR ARCHIVOS: preparacion-usb/preparar-evidencia-05.ps1. Preparadores anteriores están retirados. No formatear, repetir Imager ni restaurar Armbian por rutina. Herramientas en PC, no instaladas al pendrive.
- Tres escrituras de Imager fallaron con disk153/redetección; la cuarta con Imager2.0.11.1 funcionó en conexión USB(16)/SS04. Cambiar letra no cambió puerto. El éxito apunta a diferencia de ruta, sin causa física exacta probada. No repetir una escritura fallida sin evidencia o cambio concreto; conservar error nativo/registro/lectura. ExitCode ausente no equivale a0.
- Conservar siempre TVBASE-respaldo-*, fuentes originales, claves locales y recibos. usb-antes.img respalda el antiguo PENDRIVE, no el TV. No hay respaldo del TV aún.
- No usar ZIP vacío ni Update del actualizador congelado al2%; no repetir reboot:recovery sin nueva evidencia. No usar LED roto para diagnóstico.

## Desarrollo y documentación

- Respetar contratos, criterios y IDs REQ/ADR/C/VAL/M de docs. Distinguir observado en TV, verificado en PC, hipótesis y propuesta. Actualizar estado y grafo tras cada resultado.
- Chrome138 es techo oficial de Android9; planificar otra base para motores futuros. Un navegador instalado no prueba el proveedor WebView activo ni mejora de rendimiento. Conservar dos VP9 (uno alfa) más canvas y las APIs para la app futura; no exigir su APK terminada.
- debugfs Cygwin: cd al directorio, write con basename, cd /. Verificar fsck/contenido/metadatos/SELinux. No volver a usar destinos absolutos en write.
- No sobrescribir releases verificadas para documentar. Rutas de herramientas/scripts existentes se conservan por dependencias. Claves de desarrollo no se imprimen ni publican.
- Limpieza completada: docs/evidencia/limpieza-resultado.json, 6615135611 bytes. Se quitaron cachés, ZIP sin firma, payload extraído, imagen Armbian expandida y copia defectuosa debugfs; fuentes/logs/finales/respaldos conservados. Armbian puede regenerarse del gzip comprobado. No ejecutar otra limpieza automáticamente.
