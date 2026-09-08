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
| ADR-14 | Git local con fuente/documentación/evidencia revisada y artefactos grandes fuera | Excluir claves e informes crudos. Autoría temporal explícita del agente; publicación posterior en tablerosapp-ctrl/mxqpro4k mediante espejo saneado. |
| ADR-15 | Recopilar directamente OTAUpgrade acreditado en este P291 y dar prioridad a sus certificados | SYSTEM_UPDATE_SETTINGS resolvió GMS y el límite4 dejó afuera OTAUpgrade. El complemento0.6 excluye esos splits y no repite datos de arranque ya adquiridos. |
| ADR-16 | Nombres de funciones propios, SHA estricto y pruebas con mksh real | El alias hash de Android produjo valores vacíos en0.5; Bash no detectó la colisión. Validar64hex en cada resultado y un contenido conocido antes de copiar. Mantener un límite nunca justifica declarar éxito de una captura incompleta. |

| ADR-17 | Captura P291 completa, firma integral verificada con su otacerts y entrada explícita al menú OEM con el ZIP real | La misma vía antes solo recibió un ZIP vacío. 0.7 comprueba perfil/USB/ROM/APK y abre MainActivity; no inicia Update ni corrige el reinicio. La OEM prepara BCB/mapa mediante framework y solicita recovery interno; éxito real y claves internas pendientes. |

| ADR-18 | No repetir Update tras el intento OEM con ROM completa detenido al 2 % más de diez minutos | La firma válida y el ZIP completo no resolvieron el cierre. Separar observación visual de copia/BCB/mapa; recuperar control mediante un único ciclo manual, resultado pendiente, y orientar la investigación al intervalo posterior o a entrada física confirmada. |

## Incidentes que no deben repetirse

- **USB y formato:** tres grabaciones fallaron con errores nativos y redetección. Cambiar letra no cambió la conexión. La cuarta funcionó tras cambiar físicamente de ruta. «No aparece en Explorador» no equivalía a «no existe el disco». El volumen pudo recuperarse. No atribuir causa precisa sin evidencia.
- **ZIP vacío:** llegó a selección pero terminó detenido al 2 %. Volvió Android. No es instalador de ROM y ya no está activo en el USB.
- **Error de ADB 0.2:** el cliente respondía CLSE y confundía mensajes tardíos de canales cerrados. Los cierres no se responden, se ignoran paquetes de canales completados de la misma conexión y se acepta CLSE remoto cero heredado. 0.3 confirmó consultas reales.
- **Sin señal tras recovery:** no demuestra instalación oculta, apagado físico ni recovery averiado. El LED no funciona. No inferir root de UID shell/userdebug/test-keys.
- **debugfs:** el port Cygwin creó nombres literales con barras al usar destinos absolutos de `write`. Usar `cd`, nombre simple y verificar contenido, metadatos y fsck. Se conservan comandos/causa/logs; la imagen defectuosa local fue eliminada en la limpieza.
- **Preservación de recovery:** auditar scripts y servicios del siguiente arranque además de la lista de particiones que escribe el ZIP.
- **Versiones:** no copiar la APK nueva bajo nombre viejo. Los preparadores0.2/0.3/0.4 son históricos; el nuevo es `preparar-entrada-oem-07.ps1`, con su propio recibo y pruebas.

## Evidencia de la entrada alternativa

El [servicio ADB Android9](https://android.googlesource.com/platform/system/core/+/refs/tags/android-9.0.0_r1/adb/services.cpp) solicita `sys.powerctl` con el argumento recibido. La [implementación Amlogic de reinicio](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/common/cmd_reboot.c) distingue recovery/factory_reset de update. La [configuración de referencia P271](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/board/amlogic/configs/gxl_p271_v1.h) busca recovery externo en su flujo update; su copia está en `instalador/gxl_p271_v1-referencia.h`. **La inferencia que motivó0.4** era que ese modo podía alcanzar USB donde recovery no lo hizo; el ensayo no consiguió un menú visible. No es una lectura del U-Boot instalado en el primer TV.

La rutina [wipeisb](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/common/cmd_wipeisb.c) puede limpiar 4096 bytes de la cabecera instaboot si existe. Recovery puede procesar órdenes anteriores. Por eso no se afirma que entrar en ese modo sea totalmente ajeno a escrituras internas.

El [verificador de recovery AOSP](https://android.googlesource.com/platform/bootable/recovery/+/721f679/verifier.cpp) define claves `v3` RSA2048/exponente3/SHA256. Se conservó la clave del recovery candidato y se agregó la que verifica nuestro ZIP, sin modificar el ejecutable verificador. [Prueba local exacta](../rom-simplificada/instalador/recovery-externo/PREPARADO.json). Esto no prueba autenticación/arranque del ramdisk por el cargador real.


Evidencia de ADR-13: [análisis de informes0.4](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md). Implementación/criterios de ADR-14: [historial local y GitHub](GIT.md).

La nueva evidencia0.5 y sus límites están en [hallazgos](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md). La reproducción del defecto SHA se documenta en [MKSH-HALLAZGO-0.5](../rom-simplificada/instalador/MKSH-HALLAZGO-0.5.md).

Evidencia de ADR-17: [captura completa P291](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md), [firma integral contra certificados reales](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json) y [análisis del actualizador](../diagnostico/primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md). No confundir confianza del Android instalado con las claves de recovery ni inferir que un apagado prepara correctamente BCB/block.map.

Evidencia ADR-18: [intento con ROM completa](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md). No atribuir al nuevo intento el pstore de otro reinicio ni dar por presentes reportes que0.7 no genera.

## ADR-19 · Captura dirigida tras la revisión de Fable

Adoptar PROP-09 y fase1 de PROP-13 con0.8, para aprovechar el intento ya ocurrido sin otro Update, reinicio o cambio de radios. Diferenciar espera Java y kernel, persistencia desconocida y errores de consulta. SHA estricto/carpeta nueva/estados con límite. [Revisión y contrato](hipotesis/REVISION-CONJUNTA-FABLE.md). Preparador vigente: `preparar-postintento-08.ps1`; los anteriores quedan históricos.

## ADR-20 · Separar captura, persistencia y respuesta del servicio

Tras [0.8](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md), un mensaje de éxito y una lectura desde caché no acreditan que el cierre llegue al mover el USB. No reconstruir el cierre vacío ni repetir los datos ya íntegros. Exigir sincronización dirigida y errores explícitos antes de otra entrega. `dumpsys` puede retornar0 al agotar un servicio; interpretar también el texto. No repetir consultas de BatteryStats en bucle: pueden dejar trabajo pendiente en el servicio. La LAN ofrecida requiere el primerP291; no extrapolar delP271 ni elevar permisos.

## ADR-21 · Excluir Bluetooth del primer perfil

El usuario autoriza prescindir deBluetooth para instalar; WiFi sigue siendo objetivo. La [lecturaLAN](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md) documenta un panic en la coordinación BT→WiFi y esperas de inicialización/limpiezaBluetooth. Separar el ajuste reversible en Androidactual de la nueva recetaROM. No cambiar autenticación ni permisosdel shell para apagar una radio: usar los controles/API normales de Android. El candidato tiene binarios distintos, pero eso no prueba una corrección. La variante siguiente conserva0.1.1 y sus recibos; debe suprimir las rutas de inicio/cargaBluetooth y conservar las deWiFi, verificándolas antes de entregar. REQ-13/PROP-14.


## ADR-22 · Usar el root incorporado tras el pedido explícito

El usuario pidió concentrarse en root después del nuevo2% y conocer las opciones de instalación forzada antes de elegir. Esa autorización actual reemplaza la restricción previa para esta exploración. El su ya existente confirmóUID0; no se instalóroot ni se cambió autenticación/SELinux. La trazaJava única localizó la espera deWiFi y la lectura conroot acreditóZIPinterno íntegro/mapaausente. [Resultado](../diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md). No repetir BatteryStatsdump; diferenciar lectura, capturaART, preparaciónpersistente ygrabación.

## ADR-23 · Contrastar la ROM contra los originales antes de forzar

El respaldo permitió leer elrecoveryoriginal y elDTB real. La clave de recovery es formatoAOSPv1/SHA1 y elZIP0.1.2 usaSHA256: la política de referencia rechaza la combinación, aunque no se ejecutó elverificadorOEM. Además cambian geometríavendor, IRQWiFi y parámetros devideo/SDIO en elboot candidato. [Comparación](../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md). La coincidencia deDT-id y elhecho de que unaimagenquepa no acreditan elmapa delpróximoarranque.

No promover0.1.2 mediante una firma distinta como única corrección. Completar originales verificables y preferir una nuevaROM simplificada desdeellos, conservando kernel/DTB/geometría/video. ExcluirBluetooth y softwareprescindible e integrarChrome/WebView/iniciopropio mantiene elobjetivo de reemplazo enmemoriainterna porUSB. RecuperarWiFi sigue pendiente devalidación. Presentarpreparación y método dereset/instalación conriesgosalusuario antesde forzarlos. REQ-02/09/11/13, PROP-15, C-ORIG/C-ROM/C-TV.

## ADR-24 · Derivación original con selección explícita

El usuario autorizó construir sobre las adquisiciones originales P291. Se conservan kernel, multi-DTB, framework multimedia, controladores y geometría real; se retiran paquetes/servicios por una política revisada y se agregan inicio, Chrome/WebView, valores iniciales y gestión propia. Android 9 mantiene el contrato APK; Linux con contenedor Android y una reconstrucción completa de AOSP requieren integración adicional. [Receta](../rom-simplificada/original-p291/README.md) y [auditoría](../rom-simplificada/original-p291/AUDITORIA-SERVICIOS.md).

La validación compara contenido, propietario, modo y atributos extendidos de cada nodo conservado; comprueba también directorios nuevos y elimina bloques libres de las imágenes entregadas. Se retiran ADB por red predeterminado, su elevado y consola. SELinux permisivo y claves de plataforma heredadas permanecen como límites del experimento, no como configuración final de producción. REQ-02/03/04/13/14, C-ORIG/C-ROM/C-WEB, M0/M3.

## ADR-25 · Separar actualización propia, migración y restauración

El gestor tiene identidad propia, permiso acotado INSTALL_PACKAGES y comunicación HTTPS saliente; no agrega root ni un servidor de comandos. Comprueba firma del manifiesto y de cada APK, versión y compatibilidad. Está desactivado hasta configurar el servidor y la clave pública del dueño. La actualización de Chrome puede cerrar sus consumidores y se limita a mantenimiento; no se promete reproducción continua ni rollback. [Implementación](../rom-simplificada/original-p291/gestion/README.md). REQ-09/14, C-GESTION, VAL-10.

La ROM exige userdata limpia, verificada por su contenido y montaje, antes de escribir. El instalador no la borra ni migra automáticamente. La restauración es un ZIP separado que recupera cinco particiones originales, incluido su software OEM, y conserva los datos que existan en ese momento; no recupera datos retirados. La firma SHA1 del ZIP responde a la política heredada del recovery; el gestor usa SHA256/RSA. La aceptación física de recovery y el procedimiento de migración siguen pendientes. REQ-01/09/11/14, C-ZIP/C-REC, M1/M2/M4.


## ADR-26 · Entrada ENV/BCB condicionada y migración0.2.1

La preparación del instalador debe resolver la migración que0.2.0 exigía sin realizarla. Se conservan sus cinco imágenes y se crea el instalador0.2.1: copia cruda de cinco particiones más userdata, persistencia comprobada, tres SHA por respaldo y orígenes desmontados. Solo después crea ext4 limpio, comprueba contenido mediante montaje RO, desmonta y escribe las imágenes con boot al final. El ZIP no repone los datos OEM en Android limpio. [Contrato y pruebas](../rom-simplificada/original-p291/instalacion-021/CONTRATO-MIGRACION.md). REQ-01/11/14, C-ZIP, M2.

AccesoUSB0.9 prepara una entrada distinta: respalda metadatos, modifica64KiB de ENV y2KiB BCB y neutraliza órdenes previas, sin seleccionar un paquete ni reiniciar automáticamente. El bootcmd transitorio debe restaurar `run storeboot` y solicitar saveenv antes de cargar recovery. Si preboot entra antes y deja el transitorio pendiente, instalación y restauración deben rechazar escrituras al comprobar ENV. Ni CRC correcto ni respaldo prueban una recuperación física tras una escritura incompleta. [Evidencia y riesgos](evidencia/ENTRADA-ORIGINAL-P291-021.md).

El usuario autorizó el reemplazo y la preparación de archivos, pero pidió conocer las opciones forzadas y sus riesgos antes de decidir. Por ese pedido, al preparar la entrega **el uso específico quedó pendiente de su decisión**, sin deducirla de la autorización para copiar el USB. Posteriormente, tras explicar el riesgo concreto de ENV/BCB, el usuario respondió **«si ejecuta»** a la pregunta explícita. **La autorización específica ya está otorgada y no se debe pedir de nuevo.** Después se comprobó identidad/USB/LAN y se ejecutó una sola preparación. El cierre independiente de23:41:53ART confirmó prepared/código0,21 archivos con21 sellosUSB, siete copias internas, ENV/BCB escritos y releídos y órdenes antiguas preservadas. No se pidió reset ni se borró userdata ni se escribieron imágenes Android. [Resultado físico](evidencia/PREPARACION-ENTRADA-P291-09.md). Después del ciclo físico10s indicado, el usuario informó «Apareció un menú de recovery». Se indicó aplicar TVBASE-P291-A9-0.2.1-RECOVERY.zip desde EXT/udisk, sin wipe separado ni restaurador, conservando USB/alimentación y esperando final/error antes de reiniciar. La foto posterior muestra ejecución de nuestro update-binary y aborto con «destino no eMMC particionada: system», Status1 / Installation aborted. Se acredita la entrada delZIP al instalador; no identidad exacta/hash delrecovery ni ROM instalada. Mantener recovery sin repetirZIP/wipe/restore/reset. Revisar guardblock(), el layoutsysfs y el orden de llamadas antes de implementar una nueva revisión; conservar el fallo y no eliminar la guarda indiscriminadamente. No se agrega una confirmación rutinaria a copiar archivos. Una captura posterior confirmó la APK0.9 instalada pero oculta tras el diálogo2%: no indicar pulsar botones invisibles ni cortar para abrirla. El acompañamiento LAN usa el acceso existente y cuenta con la autorización recibida; no abre servicios ni cambia autenticación. No repetir Update ni reset anteriores. C-ENTRY/C-USB/C-REC, M1/VAL-04/05.

La sonda física O_RDONLY mostró que el literal ioctl64 `0x80081272` heredado devolvía EINVAL22; ARM32 requiere `0x80041272` y devuelve los tamaños exactos. Se corrige en instalación y restauración0.2.1, conservando0.2.0 histórica. El formateador original funcionó sobre un archivo regular temporal con el superblock esperado; no se formateó ni montó una partición. Pruebas nativas limitadas y tests PC no equivalen a instalación.

El restaurador0.2.1 repone únicamente cinco imágenes OEM, con copia previa de las actuales y sin tocar userdata. Restaurar data.img exige otra receta atada al respaldo físico que todavía no existe. La plataforma nueva retira su y ADB TCP predeterminado; el gestor no tiene REBOOT/RECOVERY. Reentrada desde Android nuevo, actualización completa posterior y restauración física siguen pendientes. Esta decisión actualiza el procedimiento de migración de ADR-25, manteniendo separadas APK/motor/ROM/contenido y sin prometer rollback. M4/REQ-09/11.

## ADR-27 · Identidad Amlogic sin depender del nombre MMC tradicional

La foto del error021 demuestra que sysfs termina en system; el código aborta antes de migración. La fuente del kernel Amlogic admite nombres lógicos de partición. Se crean instalador/restaurador022 separados; se conserva la plataforma y se verifica descriptor/rdev, atributos, padreMMC canónico exacto, tamaños/rangos/no solapamiento y revalidación. No admitir cualquier nombre ni ignorar errores. Los offsets no capturados se leen/fijan durantepreflight. [Evidencia](evidencia/INSTALADOR-P291-022.md) · [Fuente](evidencia/PARTICIONES-AMLOGIC-P291-022.md).

La entrada09 ya se consiguió; no repetir preparación ni reiniciar para corregir un error de instalador. Entrega por archivos, archivando los dosZIP021 y su guía, y verificando que reportes/respaldos permanezcan iguales. La prueba enPC no acredita la instalación022. Las fuentes y recibos021 se conservan sin sobrescribir.

## ADR-28 · Propuesta de capa común, lotes y actualizaciones; ejecución pendiente de OK

Tras el primer arranque exitoso y WiFi reportado, el usuario solicita dos recorridos: uno exhaustivo para calificar nuevos lotes/variantes y otro rápido para instalar el resto que coincida. Se propone separar producto, perfil de hardware e identidad de unidad; revisar respaldos críticos y política de userdata por operación; actualizar APK/motor/contenido/ROM de forma independiente y medir antes de prometer reducción de tiempos. La receta exacta sigue como propuesta. [Diseño](PROPUESTA-LOTES-Y-ACTUALIZACIONES.md).

La restricción inmediata sí rige: documentar/guardar/proponer, sin nuevos cambios ni pruebas físicas hasta su OK. ISSUE-HOME-01 queda registrado, sin corregir. Se conservan imágenes y recibos 0.2.2 inmutables; el éxito físico se registra en nueva evidencia, no reescribiendo los recibos de construcción.

## ADR-29 · Reconocimiento primero, producto común y versiones por perfil

El usuario solicita considerar logo, aprovechamiento de recursos, comprobación de tráfico sospechoso, WebView efectivo y actualización remota. Informa varios reinicios sin USB correctos y propone dos pendrives: reconocimiento de cualquier familia, incluidos Rockchip, e instalación rápida para perfiles conocidos. [Observación separada](evidencia/REINICIOS-P291-SIN-USB.md).

Se propone una aplicación de reconocimiento sobre Android y adaptadores de lectura por permisos/familia, con ficha y evidencia comparables. No se promete arranque USB universal, acceso a drivers protegidos desde una APK normal ni una ROM automáticamente compatible. El diagnóstico distingue candidato de perfil calificado. Se prioriza P291, después P271 y cada Rockchip identificado.

PROP-17 y REQ-18 amplían PROP-16: la capa común y los contratos se diseñan desde el inicio; un catálogo/perfiles firmados sirve a USB e Internet, con ejecutores separados para APK, contenido y ROM. El manifiesto actual no admite perfiles ni USB y necesita una versión nueva, sin relajar verificaciones. Una actualización conservadora no reutiliza el formateo de conversión OEM. Se miden video, recursos y tráfico antes de atribuir mejoras o certificar limpieza. [Plan completo](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md).

La implementación y las pruebas físicas siguen pendientes del OK pedido por el usuario. Esta revisión documenta el diseño y la nueva observación, sin cambios en TV, USB, servidor o artefactos sellados.

## ADR-30 · Reconocedor normal Android autorizado y capturas secuenciales

El usuario dio OK para implementar el paso0 y preparar Kingston, con distintos TV que irá conectando en secuencia. Se construye Reconocimiento0.1 como APK normal/API21+, sin root/ADB/red, que guarda una captura única por pasada y datos accesibles con límites explícitos. Identidad local de instalación, perfil candidato y evidencia se mantienen separados: el nombre P291 no autoriza instalar.

Se conserva todo el contenido previo del USB. La carpeta nueva contiene APK/guía/marcador y acumula ZIP en INFORMES. Copia local, manifiesto/hash, relectura y recibo por transporte permiten revisar exportaciones; un archivo parcial no se convierte en éxito. El importadorPC no extrae ni ejecuta drivers, y almacena datos privados. [Entrega, revisión y pruebas](evidencia/RECONOCEDOR-USB-01.md).

La autorización no activa servidor, modifica ROM ni corrige Home. La captura física y escritura desde Android siguen pendientes al entregar; no se declara reconocimiento completo de toda placa o respaldo de la ROM. Fuentes/entrega0.1 se conservan para comparar con los ZIP que devuelva el usuario.
