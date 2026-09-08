# Especificación del producto y aceptación

## Contrato vigente · plataforma0.2.0, instalador0.2.1 y acceso0.9

REQ-01/11/14 mantienen el objetivo de Android interno por pendrive. **ADR-26** separa tres operaciones: preparar la entrada ENV/BCB, instalar con migración respaldada y restaurar cinco imágenes OEM. La plataforma0.2.0 no cambia; los ejecutables de instalación/restauración0.2.1 corrigen la consulta de tamaño ARM32. Preparar archivos está autorizado; el usuario aún debe decidir el método específico de entrada tras conocer sus riesgos.

La APK0.9 solo podrá preparar la entrada después de esa decisión: perfil y ZIP exactos, respaldo de metadatos, sincronización/relectura, modificación acotada de64KiB ENV y2KiB BCB y neutralización de órdenes antiguas. No selecciona paquete ni reinicia automáticamente. No aceptar una desconexión o un aviso de preparación como prueba de recovery.

El instalador0.2.1 exige data179:20 de3495952384B, sin montajes ni mappings, y seis respaldos crudos verificados en el USB antes de crear ext4. Reserva16KiB para footer; la preparación debe terminar con superblock exacto, contenido vacío comprobado RO y volumen nuevamente desmontado. Exige6603931648B libres; el mayor archivo cabe FAT32. ENV debe haber vuelto a `bootcmd=run storeboot`, con CRC y flujo originales, antes de cualquier formato. [Contrato exacto](../rom-simplificada/original-p291/instalacion-021/CONTRATO-MIGRACION.md).

El restaurador0.2.1 acepta solo las cinco imágenes originales, respalda las cinco actuales antes de escribir y conserva userdata. Recuperar data.img requiere otro paquete fijado al respaldo físico que todavía no existe. No hay rollback, restauración física ni reentrada desde Android nuevo acreditados.

## Base de producto conservada · derivación original P2910.2.0

El usuario autorizó construir desde las particiones originales ya respaldadas, preservando los drivers de video y las APIs de Android. Se mantiene Android 9 para esta primera derivación; cambiar a Linux o a un framework nuevo sigue condicionado a demostrar compatibilidad APK y multimedia. [Composición y límites](../rom-simplificada/original-p291/README.md).

**REQ-14 · Reducir software y conexiones ajenas.** Retirar precargas, reinstaladores OEM y accesos de diagnóstico elevados que no requiere el producto, con una selección explícita y comprobable. Conservar servicios de plataforma/hardware por dependencia. La denuncia de llamadas de red del usuario no identifica por sí sola procesos, VPN ni malware. La aceptación exige inventario final y tráfico atribuido por proceso durante arranque, reposo, reproducción y actualización; no puede haber destinos OEM inexplicados. La auditoría estática y la eliminación de APK son preparación local, no aceptación física ni certificación de limpieza total.

**REQ-09, primera implementación.** El gestor independiente puede actualizar APK únicas y Chrome mediante HTTPS, manifiesto firmado, hash, certificado, versión, API/ABI y ventana de mantenimiento. Se entrega desactivado porque el usuario aún no proporcionó dirección ni clave pública de su servidor. No inventar un endpoint. Actualizar toda la ROM, administrar videos, trabajar con APK divididas, rotar claves y reanudar automáticamente la reproducción siguen pendientes.

**VAL-10 · Gestor y comunicaciones.** En PC: probar firma alterada, caducidad, repetición, hosts, metadatos, cancelación y horario; vincular fuentes y APK revisadas. En TV: confirmar permiso de instalación, TLS con servidor propio, instalación válida y rechazada, interrupción, reinicio, persistencia y actualización de Chrome mientras hay consumidores WebView. Capturar destinos y atribuir tráfico. Los resultados locales no acreditan esta salida física. Relaciona REQ-09/14 y M6.

**Migración y confianza.** La primera instalación debe partir de userdata limpia para no reintroducir APK o preferencias OEM desde los datos anteriores. El instalador0.2.1 respalda el volumen completo antes de prepararlo; no vuelve a copiar datos OEM al sistema nuevo. La APK explica el borrado de aplicaciones, cuentas, ajustes y archivos internos. La preparación física y la restauración posterior siguen pendientes. El experimento conserva framework original, SELinux permisivo y firma de plataforma heredada: la base de producción exige otro trabajo de integración, claves propias y pruebas. No equiparar el ZIP local con un producto terminado.

El proveedor WebView efectivo, las dos capas VP9 (una con alfa) y canvas, los controles, Ethernet/WiFi y el arranque interno siguen sujetos a VAL-07/08. Chrome 138 es el techo de Android 9; una versión nueva del navegador no demuestra mayor rendimiento.

Versión documental6, 7/9/2026, tras preparar instalador0.2.1 y acceso0.9; el intento OEM permanece detenido al2%. Recoge el pedido vigente del usuario. La evolución de su APK no bloquea preparar y probar la plataforma. El alcance no incluye investigar la actualización automática que afectó al WiFi del primer equipo.

## Objetivo y alcance

Actualización7/9, sesiónLAN: el usuario pide **instalar sin Bluetooth en el primerP291**. Bluetooth deja de ser una función exigida para este perfil. WiFi y Ethernet se conservan como objetivos; eliminar Bluetooth no acredita por sí mismo reparar WiFi. La siguiente variante debe impedir tanto el inicio del servicio como la carga automática del móduloBluetooth, sin retirar el controladorWiFi ni presentar funcionesBluetooth que no ofrece.

Sustituir el Android del integrador por una base propia interna, con servicios necesarios de Android, drivers compatibles y un entorno web actualizable. Distribuir una misma APK Flutter/web para nuestra ROM y Android TV comercial. Quitar cuentas, tienda y servicios ajenos prescindibles; conservar APIs, medios, almacenamiento, red e inputs. No se busca una ROM universal por nombre comercial «MXQ».

**Estados:** `construido` acredita artefacto; `verificado_local` acredita comprobaciones en PC; `observado_tv` exige evidencia del aparato; `propuesto` no está implementado. Un requisito se acepta solamente con su prueba de salida, no por tener un archivo o marcar una tarea terminada.

## Requisitos trazables

| ID | Requisito | Criterio de aceptación | Estado actual / componentes |
| --- | --- | --- | --- |
| REQ-13 | P291 sin Bluetooth, con red conservada | Tras arrancar la nueva ROM no se carga btmtksdio ni HAL/servicio Bluetooth; WiFi/Ethernet e inputs se prueban por separado | Plataforma0.2.0 verificada en PC; físico pendiente · C-ROM/C-TV |
| REQ-01 | Android interno mediante pendrive | Instalar en P291, retirar USB y completar arranques normales con identificación TVBASE | ZIP construido/verificado; físico pendiente · C-ROM, C-ZIP, C-USB |
| REQ-02 | Compatibilidad por placa | Registrar codecs, audio, red, almacenamiento, inputs y encendido con perfil real | Originales P291 respaldados, geometría/kernel/DTB preservados; ROM sin prueba física · C-ORIG/C-PERFIL |
| REQ-03 | Android simplificado con APIs estándar | Inicio/ajustes, instalación APK y drivers funcionales sin servicios retirados | 51 APK retiradas,34 originales y5 agregadas; comprobado en imágenes · C-ROM/C-INICIO |
| REQ-04 | Navegador y proveedor WebView mejorados | Verificar paquete/versión realmente usados por la APK, navegación y su actualización sin Play Store | Chrome138 y overlay integrados; proveedor físico pendiente · C-CHROME, C-WEB |
| REQ-05 | Conservar video y composición | Reproducir los dos VP9 de referencia, uno con alfa, más canvas; comparar estabilidad, tiempos y memoria con la misma carga | Funciona en sistema viejo según usuario; nueva base sin medir · C-WEB, C-BASE |
| REQ-06 | Video hasta 1080p sin DRM | Un video 1920×1080, audio, búsqueda, repetición y reproducción sostenida; parámetros de muestra registrados | Pendiente; no implica dos 1080p simultáneos · C-WEB |
| REQ-07 | Contenido en memoria interna | Descargar/verificar, reproducir offline, buscar dentro del video, consultar espacio y borrar selectivamente sin borrar credenciales | Propuesto · C-APP, C-GESTION |
| REQ-08 | Misma APK y evolución del producto | APK firmada funciona en nuestra ROM y Android TV; detecta capacidades y no requiere recompilar ROM por cada lógica de negocio | Propuesto; sin exigir APK terminada para avanzar · C-APP |
| REQ-09 | Actualizaciones propias | APK/motor/sistema/contenido separados, firmas, compatibilidad y reporte | Gestor APK/motor integrado y desactivado; servidor y prueba física pendientes, OTA completa no implementada · C-GESTION/C-ZIP |
| REQ-10 | Controles remotos | Recorrer inicio, ajustes y aplicación con flechas/OK/atrás; registrar mapas IR/USB/Bluetooth/CEC aplicables | Inicio construido; pruebas de control pendientes · C-INICIO, C-PERFIL |
| REQ-11 | Recuperabilidad y diagnóstico | Respaldar y verificar antes de escribir; demostrar restauración desde una entrada disponible si Android falla | 12 particiones originales respaldadas; instalación0.2.1 prepara seis respaldos futuros. Entrada0.9 pendiente de decisión/uso y restaurador0.2.1 sin ensayo físico · C-ENTRY/C-REC/C-ZIP |
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
| VAL-03 | Protocolo y contrato por versión de acceso | APK0.9 revisada e instalada por LAN, apertura solicitada pero APK oculta tras diálogo2% confirmado por captura; helpers de archivo/ABI probados en TV. Preparación ENV/BCB y fsync del USB no probados físicamente. |
| VAL-04 | Copia y relectura del USB con recibo de esta entrega | Completadas0.2.1/Acceso0.9 a23:06:04ART, cuatro SHA y código0 en `preparacion-usb/original-021-estado.json`. Expulsión segura pendiente; vaciado final del volumen no acreditado. |
| VAL-05 | Recovery identificado, ENV normal y ZIP directo USB aceptado | Pendiente. El nuevo método exige decisión específica del usuario; no repetir OEM/Update al2%. |
| VAL-06 | Seis respaldos previos, migración y cinco escrituras verificadas | Pendiente. Exigir `00-backup-verified.json`, resultado de formato/RO y `90-installed-verified.json` físicos, sin sustituirlos por pruebas PC. |
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
