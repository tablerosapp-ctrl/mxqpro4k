# Especificación del producto y aceptación

## REQ-19 · Reconocimiento combinado y originales desde recovery

El usuario amplió el reconocimiento: APK normal para identificar y observar Android, luego paquete independiente de extracción basado en su informe para recovery compatible. [Implementación y contrato](../diagnostico/extractor-recovery-0.1/README.md). No se instala una ROM ni se modifica el recovery al copiar; entrada y aceptación del paquete se califican por perfil. El plan liga SHA/UUID de la captura y DT declarado, no acredita identidad física ni habilita instalación. El mapa y tamaños se descubren y revalidan en recovery. El adaptador inicial admite eMMC interna y registra omisiones; no se promete extracción de RPMB/MTD/UFS o todos los TV.

**VAL-12:** primera APK íntegra, plan derivado sin campos arbitrarios, selección de ABI/entrada/firma revisadas, copia física de fuentes compatibles con SHA de origen/destino/relectura y adquisición privada PC. Debe rechazar diferencias, espacio insuficiente, fuentes ocupadas y USB cambiado sin sobrescribir otras capturas. Sin plan coincidente solo inventario. Pruebas PC no cierran VAL-12 ni acreditan recuperación/restauración. Relaciona C-RECON/C-EXTRACT/C-PERFIL/C-USB y REQ-11/18/19.

**REQ-14 y optimización, prioridad explícita:** revisar remanentes de teléfono, mensajes y contactos, KeyChain/Llavero e Intent Filter Verification Service, además del resto del software heredado. [Matriz de revisión](REVISION-COMPONENTES-HEREDADOS.md). Identificar paquete, hash, origen, dependencias y tráfico real antes de clasificar o retirar; no etiquetar malware por nombre ni certificar limpieza por la lista de APK. En esta etapa solo se registra el trabajo; no se quitan servicios.

## Reconocimiento autorizado · implementación 0.1

REQ-18 tiene [APK y formato implementados](../diagnostico/reconocedor-0.1/README.md), pruebas PC y [entrega USB verificada](evidencia/RECONOCEDOR-USB-01.md). Aceptación física pendiente: capturas P291/P271 diferenciadas, acceso parcial explícito y exportación real desde Android. No hay reconocimiento privilegiado o instalación Rockchip acreditados. La autorización actual reemplaza la espera de OK para este trabajo; otros cambios de producto/ROM/servidor permanecen propuestos.

**VAL-11 · Reconocimiento e informes por unidad.** APK en Android sin root/ADB, ficha por instalación y sesión, P291/P271 diferenciados con su evidencia, desconocidos sin autorización de instalación; omisiones/denegaciones explícitas. ZIP local y exportación real verificados por lectura, contenido anterior conservado, fallo USB recuperable sin repetir captura terminada y importación privada comprobada. Pruebas PC y entrega Windows son parciales respecto de esta aceptación física. Relaciona REQ-18 y C-RECON/C-USB/C-PERFIL.

## Actualización de aceptación · instalación física y siguiente etapa propuesta

REQ-01 tiene instalación en memoria interna y primer arranque observados, ampliados por [varios reinicios sin pendrive informados por el usuario](evidencia/REINICIOS-P291-SIN-USB.md); no se especificó el tipo de ciclo. VAL-06 tiene seis respaldos guardados y adquiridos en PC, además de recibos verificados de formato, montaje vacío de solo lectura y cinco escrituras. VAL-07 es parcial: hay una foto del inicio, conexión WiFi y reinicios reportados; faltan comprobar el proveedor WebView, el hardware y la estabilidad medida. [Evidencia física](evidencia/INSTALACION-FISICA-P291-022.md).

REQ-02/03/10 incluyen **ISSUE-HOME-01**: la tecla Home no vuelve al inicio. La [revisión local](hipotesis/HOME-P291.md) plantea hipótesis que requieren datos actuales del TV; no establece una causa ni una corrección. El usuario prueba su APK. Este avance todavía no permite aceptar multimedia, almacenamiento o actualizaciones.

**Ampliación solicitada, con el diseño pendiente del OK del usuario:**

| ID | Requisito propuesto | Criterio de aceptación futuro |
| --- | --- | --- |
| REQ-15 | Capa común de producto y perfiles de hardware calificados | Contratos y API comunes; inventario exacto por perfil y pruebas de video, red, controles, arranque y recuperación. Un nombre comercial compartido no basta para aceptar otra variante. |
| REQ-16 | Dos recorridos: calificar el lote e instalar con rapidez sus unidades compatibles | Calificación exhaustiva del primer ejemplar e identificación individual obligatoria en todos. Política de respaldo aprobada para cada operación, sin clonar secretos ni calibración de otra unidad. Detención ante diferencias y resultado comprobado por unidad. |
| REQ-17 | Actualizaciones por componente con menor trabajo y conservación de datos | Separar APK, motor, contenido y ROM. Medir tiempos por fase, evitar reinstalaciones innecesarias y probar migración, conservación de datos y recuperación. Mantener las comprobaciones de integridad y no prometer tiempos sin medirlos. |
| REQ-18 | Reconocimiento de varias familias desde USB con Android operativo | Ficha comparable y evidencia con fuente, permisos y límites; P291 y P271 diferenciados, perfiles desconocidos rechazados para instalación. Captura parcial explícita sin ADB/root; informes persistentes con hashes y errores de acceso/USB controlados. Rockchip requiere adaptación y ensayo por perfil. |

Estos requisitos extienden REQ-02/08/09/11/14; no están implementados ni aceptados. [PROP-16: propuesta y condiciones](PROPUESTA-LOTES-Y-ACTUALIZACIONES.md). ADR-28 registra la propuesta y el límite expresado por el usuario: documentar y proponer ahora, esperar su OK explícito para nuevos cambios o pruebas físicas. Cualquier reducción futura de respaldos exige una política aprobada; el contrato 0.2.2 de seis respaldos no se altera retroactivamente.

**PROP-17 / ADR-29:** reconocimiento es el primer entregable propuesto. REQ-15 incorpora logo e interfaz común; REQ-17, catálogo/perfiles firmados compartidos por USB e Internet con ejecutores distintos y conservación/migración según operación. REQ-14 requiere inventario y observación de consumo/tráfico; REQ-04/05, proveedor real dentro de la APK y composición VP9/alfa/canvas medida. No se afirma limpieza total, rendimiento superior ni extracción universal de drivers. [Plan y aceptación](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md).


## Antecedente: estado anterior a la prueba física de 0.2.2

## Contrato vigente · corrección de identidad0.2.2

**ADR-27** mantiene la plataforma0.2.0 y el contrato de migración respaldada deADR-26. Instalación/restauración022 sustituyen la guarda de nombre insuficiente de021 por identidad del descriptor y sysfs, padreMMC exacto, geometría, rangos sin solapamiento y revalidación antes de escribir. Los starts se capturan en cada ejecución y se fijan durante ella; no se inventan offsets originales. [Contrato/evidencia](evidencia/INSTALADOR-P291-022.md).

REQ-01/02/10/11/14: ejecución021 abortada antes debackup/formato/flash; entrega022 verificadaPC, instalación física pendiente. REQ-04/05 y el resto del producto mantienen su aceptación física pendiente. La preparación09 ya autorizada y ejecutada no se repite;022 se selecciona en el recovery abierto. La APK09 fija021 y no se adapta implícitamente por cambiar deZIP.

VAL-02/04 acreditan pruebas y copia022; VAL-05 acredita menú y ejecución021 con límite de identidad delrecovery. VAL-06/07 exigen respaldo físico, formato/RO, cinco relecturas, arranque y proveedor efectivos. No cerrar M2 por testsPC. No reescribir los recibos sellados de versiones anteriores.


## Antecedente de la entrega 0.2.1

## Contrato vigente · plataforma0.2.0, instalador0.2.1 y acceso0.9

REQ-01/11/14 mantienen el objetivo de Android interno por pendrive. **ADR-26** separa tres operaciones: preparar la entrada ENV/BCB, instalar con migración respaldada y restaurar cinco imágenes OEM. La plataforma0.2.0 no cambia; los ejecutables de instalación/restauración0.2.1 corrigen la consulta de tamaño ARM32. El usuario ya autorizó el método específico de entrada al responder «si ejecuta», después de conocer el riesgo de ENV/BCB. No se requiere reiterar esa confirmación; identidad, ZIP, USB y LAN siguen siendo comprobaciones técnicas obligatorias.

La preparación0.9 ya autorizada conserva el contrato: perfil y ZIP exactos, respaldo de metadatos, sincronización/relectura, modificación acotada de64KiB ENV y2KiB BCB y neutralización de órdenes antiguas. No selecciona paquete ni reinicia automáticamente. La ejecución única terminó prepared y fue comprobada independientemente a23:41:53ART: metadatos/respaldos y relecturas ENV/BCB correctos. [Evidencia física](evidencia/PREPARACION-ENTRADA-P291-09.md). No se pidió reset ni se borró userdata ni se escribieron las imágenes Android; el usuario después confirmó el menú de recovery tras el ciclo físico indicado. La foto posterior acredita ejecución de nuestro update-binary y aborto Status1 por «destino no eMMC particionada: system». No fija la imagen/hash de recovery ni acredita instalación. No repetir la preparación.

El instalador0.2.1 exige data179:20 de3495952384B, sin montajes ni mappings, y seis respaldos crudos verificados en el USB antes de crear ext4. Reserva16KiB para footer; la preparación debe terminar con superblock exacto, contenido vacío comprobado RO y volumen nuevamente desmontado. Exige6603931648B libres; el mayor archivo cabe FAT32. ENV debe haber vuelto a `bootcmd=run storeboot`, con CRC y flujo originales, antes de cualquier formato. [Contrato exacto](../rom-simplificada/original-p291/instalacion-021/CONTRATO-MIGRACION.md).

El restaurador0.2.1 acepta solo las cinco imágenes originales, respalda las cinco actuales antes de escribir y conserva userdata. Recuperar data.img requiere otro paquete fijado al respaldo físico que todavía no existe. No hay rollback, restauración física ni reentrada desde Android nuevo acreditados.

## Base de producto conservada · derivación original P2910.2.0

El usuario autorizó construir desde las particiones originales ya respaldadas, preservando los drivers de video y las APIs de Android. Se mantiene Android 9 para esta primera derivación; cambiar a Linux o a un framework nuevo sigue condicionado a demostrar compatibilidad APK y multimedia. [Composición y límites](../rom-simplificada/original-p291/README.md).

**REQ-14 · Reducir software y conexiones ajenas.** Retirar precargas, reinstaladores OEM y accesos de diagnóstico elevados que no requiere el producto, con una selección explícita y comprobable. Conservar servicios de plataforma/hardware por dependencia. La denuncia de llamadas de red del usuario no identifica por sí sola procesos, VPN ni malware. La aceptación exige inventario final y tráfico atribuido por proceso durante arranque, reposo, reproducción y actualización; no puede haber destinos OEM inexplicados. La auditoría estática y la eliminación de APK son preparación local, no aceptación física ni certificación de limpieza total.

**REQ-09, primera implementación.** El gestor independiente puede actualizar APK únicas y Chrome mediante HTTPS, manifiesto firmado, hash, certificado, versión, API/ABI y ventana de mantenimiento. Se entrega desactivado porque el usuario aún no proporcionó dirección ni clave pública de su servidor. No inventar un endpoint. Actualizar toda la ROM, administrar videos, trabajar con APK divididas, rotar claves y reanudar automáticamente la reproducción siguen pendientes.

**VAL-10 · Gestor y comunicaciones.** En PC: probar firma alterada, caducidad, repetición, hosts, metadatos, cancelación y horario; vincular fuentes y APK revisadas. En TV: confirmar permiso de instalación, TLS con servidor propio, instalación válida y rechazada, interrupción, reinicio, persistencia y actualización de Chrome mientras hay consumidores WebView. Capturar destinos y atribuir tráfico. Los resultados locales no acreditan esta salida física. Relaciona REQ-09/14 y M6.

**Migración y confianza.** La primera instalación debe partir de userdata limpia para no reintroducir APK o preferencias OEM desde los datos anteriores. El instalador0.2.1 respalda el volumen completo antes de prepararlo; no vuelve a copiar datos OEM al sistema nuevo. La APK explica el borrado de aplicaciones, cuentas, ajustes y archivos internos. La preparación física y la restauración posterior siguen pendientes. El experimento conserva framework original, SELinux permisivo y firma de plataforma heredada: la base de producción exige otro trabajo de integración, claves propias y pruebas. No equiparar el ZIP local con un producto terminado.

El proveedor WebView efectivo, las dos capas VP9 (una con alfa) y canvas, los controles, Ethernet/WiFi y el arranque interno siguen sujetos a VAL-07/08. Chrome 138 es el techo de Android 9; una versión nueva del navegador no demuestra mayor rendimiento.

Versión documental6, actualizada tras confirmar el usuario el menú de recovery y recibir instrucciones de instalación0.2.1; elZIP ejecutó update-binary y abortó con Status1 por la guarda eMMC de system. El2% describe el estado OEM anterior al ciclo físico. Recoge el pedido vigente del usuario. La evolución de su APK no bloquea preparar y probar la plataforma. El alcance no incluye investigar la actualización automática que afectó al WiFi del primer equipo.

## Objetivo y alcance

Actualización7/9, sesiónLAN: el usuario pide **instalar sin Bluetooth en el primerP291**. Bluetooth deja de ser una función exigida para este perfil. WiFi y Ethernet se conservan como objetivos; eliminar Bluetooth no acredita por sí mismo reparar WiFi. La siguiente variante debe impedir tanto el inicio del servicio como la carga automática del móduloBluetooth, sin retirar el controladorWiFi ni presentar funcionesBluetooth que no ofrece.

Sustituir el Android del integrador por una base propia interna, con servicios necesarios de Android, drivers compatibles y un entorno web actualizable. Distribuir una misma APK Flutter/web para nuestra ROM y Android TV comercial. Quitar cuentas, tienda y servicios ajenos prescindibles; conservar APIs, medios, almacenamiento, red e inputs. No se busca una ROM universal por nombre comercial «MXQ».

**Estados:** `construido` acredita artefacto; `verificado_local` acredita comprobaciones en PC; `observado_tv` exige evidencia del aparato; `propuesto` no está implementado. Un requisito se acepta solamente con su prueba de salida, no por tener un archivo o marcar una tarea terminada.

## Requisitos trazables

| ID | Requisito | Criterio de aceptación | Estado actual / componentes |
| --- | --- | --- | --- |
| REQ-13 | P291 sin Bluetooth, con red conservada | Tras arrancar la nueva ROM no se carga btmtksdio ni HAL/servicio Bluetooth; WiFi/Ethernet e inputs se prueban por separado | Plataforma0.2.0 verificada en PC; físico pendiente · C-ROM/C-TV |
| REQ-01 | Android interno mediante pendrive | Instalar en P291, retirar USB y completar arranques normales con identificación TVBASE | ZIP ejecutado enrecovery; instalador0.2.1 abortó en guarda eMMC de system, sin ROM instalada · C-ROM, C-ZIP, C-USB |
| REQ-02 | Compatibilidad por placa | Registrar codecs, audio, red, almacenamiento, inputs y encendido con perfil real | Originales P291 respaldados, geometría/kernel/DTB preservados; ROM sin prueba física · C-ORIG/C-PERFIL |
| REQ-03 | Android simplificado con APIs estándar | Inicio/ajustes, instalación APK y drivers funcionales sin servicios retirados | 51 APK retiradas,34 originales y5 agregadas; comprobado en imágenes · C-ROM/C-INICIO |
| REQ-04 | Navegador y proveedor WebView mejorados | Verificar paquete/versión realmente usados por la APK, navegación y su actualización sin Play Store | Chrome138 y overlay integrados; proveedor físico pendiente · C-CHROME, C-WEB |
| REQ-05 | Conservar video y composición | Reproducir los dos VP9 de referencia, uno con alfa, más canvas; comparar estabilidad, tiempos y memoria con la misma carga | Funciona en sistema viejo según usuario; nueva base sin medir · C-WEB, C-BASE |
| REQ-06 | Video hasta 1080p sin DRM | Un video 1920×1080, audio, búsqueda, repetición y reproducción sostenida; parámetros de muestra registrados | Pendiente; no implica dos 1080p simultáneos · C-WEB |
| REQ-07 | Contenido en memoria interna | Descargar/verificar, reproducir offline, buscar dentro del video, consultar espacio y borrar selectivamente sin borrar credenciales | Propuesto · C-APP, C-GESTION |
| REQ-08 | Misma APK y evolución del producto | APK firmada funciona en nuestra ROM y Android TV; detecta capacidades y no requiere recompilar ROM por cada lógica de negocio | Propuesto; sin exigir APK terminada para avanzar · C-APP |
| REQ-09 | Actualizaciones propias | APK/motor/sistema/contenido separados, firmas, compatibilidad y reporte | Gestor APK/motor integrado y desactivado; servidor y prueba física pendientes, OTA completa no implementada · C-GESTION/C-ZIP |
| REQ-10 | Controles remotos | Recorrer inicio, ajustes y aplicación con flechas/OK/atrás; registrar mapas IR/USB/Bluetooth/CEC aplicables | Inicio construido; pruebas de control pendientes · C-INICIO, C-PERFIL |
| REQ-11 | Recuperabilidad y diagnóstico | Respaldar y verificar antes de escribir; demostrar restauración desde una entrada disponible si Android falla | 12 particiones originales respaldadas; instalación0.2.1 prepara seis respaldos futuros. Entrada0.9 preparada/verificada; recovery ejecutó update-binary0.2.1, que abortó. Restauración sin ensayo físico · C-ENTRY/C-REC/C-ZIP |
| REQ-12 | Segundo WebView opcional | Automatización en segundo plano sin degradación inaceptable del video principal, tolerando cierre por memoria | Secundario y propuesto · C-APP |

No se deducen FPS, bitrate, perfil VP9 ni resolución completa de la descripción «1280». La doble composición es referencia obligatoria; sus archivos se incorporarán cuando existan. La limpieza o un motor nuevo pueden cambiar el rendimiento en ambas direcciones: **mejorar rendimiento es una hipótesis que debe medirse**.

## Contratos entre componentes

- **Perfil de placa:** DT exacto, API/ABI, memoria real, particiones, boot/kernel/DTB, firmware, decodificadores e inputs. Separar confirmado, inferido y no leído. P291 y P271 son perfiles distintos.
- **Diagnóstico0.8, histórico:** once etapas de lectura con límites, perfil P291/API28/UID2000, carpeta nueva, autocontrol SHA y sellos estrictos. Recopila console/pmsg, log anterior, log actual filtrado y consultas WiFi/BT/batería/espacio/WebView. No cambia radios ni reinicia. COMPLETO acredita recorrido e integridad de archivos; denegaciones, timeouts y truncamiento permanecen explícitos. [Contrato detallado](hipotesis/REVISION-CONJUNTA-FABLE.md). Captura física parcial por cierre no persistido; no repetir0.8.
- **Entrada 0.7, histórica:** usa ADB loopback existente, comprueba UID2000/P291/API28, marcador del USB y tamaños/SHA exactos de ROM 0.1.1 y OTAUpgrade capturado. Autocontrol SHA conocido y digest estricto. Abre únicamente MainActivity del OEM sin extras, Update, reinicio propio ni escritura BCB. La confirmación de apertura no demuestra instalación. Timeout de lectura del ZIP de cinco minutos, sin reintentos automáticos. El menú ya se conocía; cambia el paquete real y su validación previa.
- **Complemento0.6, completado:** ADB loopback existente en127.0.0.1:5555, perfil P291/API28 y carpeta nueva en USB marcado. Cinco etapas: creación → autocontrol SHA y certificados OTA → APK específico acreditado de OTAUpgrade → configuración/identidad → verificación final. Certificados y APK son obligatorios; origen ilegible, cambio de ruta, tamaño inválido o cualquier digest inválido detiene la captura. Funciones con prefijo propio, toybox explícito, SHA de `abc` conocido y validación de64 caracteres hexadecimales en cada consumidor. No reinicia ni abre el actualizador; tampoco instala ROM ni modifica permisos/autenticación. Fuentes y salida0.6 separadas de0.5; entrega y prueba física requieren evidencia propia.
- **Recopilador0.5, histórico:** ya se obtuvieron dos capturas parciales del mismo arranque. La cuota consumida por Google Play Services impidió copiar el quinto APK, OTAUpgrade, y no se alcanzaron certificados/configuración. La colisión con el alias `hash` de mksh produjo digests binarios vacíos aceptados como iguales; no se acredita su comprobación en el TV. Conservar código, datos y pruebas Bash originales, que no reprodujeron ese fallo. Los textos sellados y los hashes de adquisición en PC tienen validaciones separadas.
- **Entrada0.4, histórica:** informe previo → hashes de ROM/recovery → `reboot:update`. En el TV terminó sin señal. Los dos informes recuperados preceden al reinicio y no registran ese fallo. No repetir el intento a partir de sus pruebas locales ni de la existencia de una partición recovery de24MiB cuyo contenido sigue sin leerse.
- **Recovery externo:** archivo Android boot para carga temporal; clave de prueba agregada a la lista aceptada, verificación activa. No es un contenedor Amlogic de fábrica ni una imagen de disco MBR.
- **ZIP0.2.1 vigente:** cinco payloads0.2.0 inmutables; respaldo previo de esas cinco particiones y de userdata. Solo tras persistencia y tres SHA correctos prepara ext4, lo verifica RO/desmontado y escribe boot al final. Fuentes en `original-p291/instalacion-021/`; restaurador separado conserva datos.
- **Aplicación/administración, propuesto:** interfaz versionada para catálogo, descargas, diagnóstico y limpieza. El contenido web no recibe root. Limpiar videos, caché, sesión o toda la aplicación son órdenes distintas.
- **Actualizaciones, propuesto:** manifiestos declaran placa, API/ABI, versiones, hashes y firma; conservar continuidad de firma, datos y estado del agente. Actualizar WebView termina procesos que lo cargaron, por lo que la coordinación debe estar fuera de esos procesos.

## Pruebas que cierran cada etapa

| ID | Evidencia necesaria | Estado |
| --- | --- | --- |
| VAL-01 | Integridad y perfil de originales/candidatos | Doce particiones P291 adquiridas; diferencias del candidato documentadas. No es respaldo de toda eMMC. |
| VAL-02 | ext4/metadatos y composición0.2.0; firma/CRC/payload de paquetes0.2.1 | Instalación y restauración0.2.1 verificadas en PC con recibos propios. No ejecución física. |
| VAL-03 | Protocolo y contrato por versión de acceso | APK0.9 revisada e instalada por LAN, apertura solicitada pero APK oculta tras diálogo2% confirmado por captura; helpers de archivo/ABI probados en TV. Preparación ENV/BCB física completada; código0, fsync/relecturas y cierre comprobados independientemente. No acredita recovery. |
| VAL-04 | Copia y relectura del USB con recibo de esta entrega | Completadas0.2.1/Acceso0.9 a23:06:04ART, cuatro SHA y código0 en `preparacion-usb/original-021-estado.json`. El reciboPC conserva la limitación histórica de expulsión/flush; USB ya identificado y utilizado enTV, con cierre0.9 posterior verificado por separado. |
| VAL-05 | Recovery identificado, ENV normal y ZIP directo USB aceptado | Preparación autorizada («si ejecuta»), ejecutada y verificada. Ciclo físico y menú de recovery confirmados por el usuario. Foto posterior: ZIP0.2.1 ejecutó update-binary, aborto Status1 por guarda eMMC de system. Identidad exacta/hash delrecovery y ENV normal no acreditados; no confundir ejecución con instalación. No repetir prepare ni OEM/Update al2%. |
| VAL-06 | Seis respaldos previos, migración y cinco escrituras verificadas | Instalador0.2.1 abortado con Status1; alcance del punto de fallo en revisión. Exigir `00-backup-verified.json`, resultado de formato/RO y `90-installed-verified.json` físicos, sin sustituirlos por pruebas PC. |
| VAL-07 | Primer arranque sin USB, identificación, hardware y proveedor WebView efectivo | Pendiente |
| VAL-08 | Suite APK/web/video/local/controles comparada con referencia | Pendiente |
| VAL-09 | Restauración ensayada, actualización y fallo controlado recuperable | Pendiente |

La suite funcional no equivale a certificación CTS/CDD. Usarlos como referencia de compatibilidad según [arquitectura](../ARQUITECTURA-ANDROID-TV.md). No dar por aceptada una etapa física a partir de simulaciones del protocolo o coincidencia de hashes en PC.

## Evidencia histórica por versión: no sustituye los criterios actuales

La captura0.5 no superó la completitud y no debe aceptarse retroactivamente por comparar sus dos copias en PC. Los [hallazgos físicos](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md) y la [regresión mksh](../rom-simplificada/instalador/MKSH-HALLAZGO-0.5.md) separan observación, defecto del recopilador e inferencia sobre el reinicio.

El complemento0.6 se acepta únicamente cuando se reciben en PC su cierre y sus archivos obligatorios con hashes válidos: autocontrol, `otacerts.zip`, `OTAUpgrade.apk` e informes requeridos. Las denegaciones o límites de lectura de la configuración se documentan como tales; no equivalen a obtener su contenido. Una compilación o regresión con mksh en PC no sustituye esa captura física. Los certificados `otacerts.zip` del Android instalado no demuestran la lista de claves del recovery. Ninguna captura sustituye el respaldo de las cinco particiones requerido antes de instalar ROM0.1.1.

Entrega complementaria0.6: [recibo USB](../preparacion-usb/evidencia-06-estado.json), 7/9/2026 a las00:22 ART, APK y guía copiadas/leídas con SHA coincidente. Captura 0.6 completada: 25 archivos adquiridos y diez SHA verificados. Ver [hallazgos](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md).

La firma integral de la ROM se verificó contra el certificado OTA realmente capturado del P291 mediante Python y OpenJDK. [Recibo](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json). No cierra VAL-05: aún falta aceptación por recovery interno y ejecución física del ZIP. Acceso 0.7 solo abre el menú tras sus controles; VAL-04 de esa versión cuenta con [recibo propio de copia/lectura](../preparacion-usb/entrada-oem-07-estado.json), del 7/9 a las 12:34 ART. El menú OEM ya se observó; Update con ZIP real quedó al 2 % por más de diez minutos.

Actualización VAL-03/04 para0.8: [12casos ADB,21fixtures mksh y11etapas de sintaxis](../rom-simplificada/instalador/EVIDENCIA-TESTS-0.8.json), fuente/APK vinculados por hashes; [copia y lectura del USB](../preparacion-usb/postintento-08-estado.json), código0. Para aceptar captura física, adquirir la carpeta nueva, validar todos los sellos y el cierre e interpretar los estados por consulta. Un parcial se conserva y no se declara completo. VAL-05 a09 siguen pendientes. Los recibos anteriores no acreditan0.8.

Resultado físico0.8: [evidencia](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md). VAL-03 física parcial:25sellos de datos válidos; cierre/etapa10 de0bytes pese al aviso de fin. VAL-04 de entrega enPC sigue válido y no prueba persistencia de futuras capturas enTV. Para el siguiente recopilador, exigir sincronización dirigida y resultado comprobado antes del aviso, conservando error/timeout sin declarar éxito. La lectura USB→PC y la clasificación semántica se verifican por separado. VAL-05 a09 siguen pendientes. No volver a obtener datos0.8 ya íntegros.

REQ-13: [ROM0.1.2 construida](../rom-simplificada/SIN-BLUETOOTH-0.1.2.md), ext4 y firma/payload verificados, [entregaUSB propia](../preparacion-usb/rom-012-estado.json). La exclusión física deBluetooth y la red siguen pendientes deVAL-07/08. La desactivación en el Androidoriginal es una intervención de diagnóstico distinta.
