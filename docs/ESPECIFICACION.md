# Especificación del producto y aceptación

Versión documental4, 7/9/2026, tras completar la captura0.6 y probar el ZIP real por el menú OEM, detenido al2%. Recoge el pedido vigente del usuario. La evolución de su APK no bloquea preparar y probar la plataforma. El alcance no incluye investigar la actualización automática que afectó al WiFi del primer equipo.

## Objetivo y alcance

Sustituir el Android del integrador por una base propia interna, con servicios necesarios de Android, drivers compatibles y un entorno web actualizable. Distribuir una misma APK Flutter/web para nuestra ROM y Android TV comercial. Quitar cuentas, tienda y servicios ajenos prescindibles; conservar APIs, medios, almacenamiento, red e inputs. No se busca una ROM universal por nombre comercial «MXQ».

**Estados:** `construido` acredita artefacto; `verificado_local` acredita comprobaciones en PC; `observado_tv` exige evidencia del aparato; `propuesto` no está implementado. Un requisito se acepta solamente con su prueba de salida, no por tener un archivo o marcar una tarea terminada.

## Requisitos trazables

| ID | Requisito | Criterio de aceptación | Estado actual / componentes |
| --- | --- | --- | --- |
| REQ-01 | Android interno mediante pendrive | Instalar en P291, retirar USB y completar arranques normales con identificación TVBASE | ZIP construido/verificado; físico pendiente · C-ROM, C-ZIP, C-USB |
| REQ-02 | Compatibilidad de hardware por placa | Registrar video/decodificadores, audio, red, almacenamiento, entradas y encendido con su perfil real | Candidato analizado; físico pendiente · C-BASE, C-PERFIL |
| REQ-03 | Android simplificado con APIs estándar | Inicio propio y ajustes funcionales; APK instala/actualiza; servicios retirados ausentes sin romper framework o drivers | 16 APK retiradas y cambios verificados localmente · C-ROM, C-INICIO |
| REQ-04 | Navegador y proveedor WebView mejorados | Verificar paquete/versión realmente usados por la APK, navegación y su actualización sin Play Store | Chrome138 y overlay integrados; proveedor físico pendiente · C-CHROME, C-WEB |
| REQ-05 | Conservar video y composición | Reproducir los dos VP9 de referencia, uno con alfa, más canvas; comparar estabilidad, tiempos y memoria con la misma carga | Funciona en sistema viejo según usuario; nueva base sin medir · C-WEB, C-BASE |
| REQ-06 | Video hasta 1080p sin DRM | Un video 1920×1080, audio, búsqueda, repetición y reproducción sostenida; parámetros de muestra registrados | Pendiente; no implica dos 1080p simultáneos · C-WEB |
| REQ-07 | Contenido en memoria interna | Descargar/verificar, reproducir offline, buscar dentro del video, consultar espacio y borrar selectivamente sin borrar credenciales | Propuesto · C-APP, C-GESTION |
| REQ-08 | Misma APK y evolución del producto | APK firmada funciona en nuestra ROM y Android TV; detecta capacidades y no requiere recompilar ROM por cada lógica de negocio | Propuesto; sin exigir APK terminada para avanzar · C-APP |
| REQ-09 | Actualizaciones propias | Separar APK/motor/sistema/contenido; requisitos y firmas verificados, despliegue por grupos, persistencia de datos y reporte de resultado | Solo instalador local experimental construido · C-GESTION, C-ZIP |
| REQ-10 | Controles remotos | Recorrer inicio, ajustes y aplicación con flechas/OK/atrás; registrar mapas IR/USB/Bluetooth/CEC aplicables | Inicio construido; pruebas de control pendientes · C-INICIO, C-PERFIL |
| REQ-11 | Recuperabilidad y diagnóstico | Antes de escribir, guardar/verificar originales; demostrar restauración desde una entrada disponible cuando Android falle | Entrada0.4 sin recovery; captura0.5 parcial analizada y defecto SHA reproducido. Captura 0.6 completa, firma contra certificado P291 verificada; menú OEM 0.7 observado, Update con ZIP real detenido al 2 %. Recovery, respaldo y restore pendientes · C-ENTRY, C-REC, C-ZIP |
| REQ-12 | Segundo WebView opcional | Automatización en segundo plano sin degradación inaceptable del video principal, tolerando cierre por memoria | Secundario y propuesto · C-APP |

No se deducen FPS, bitrate, perfil VP9 ni resolución completa de la descripción «1280». La doble composición es referencia obligatoria; sus archivos se incorporarán cuando existan. La limpieza o un motor nuevo pueden cambiar el rendimiento en ambas direcciones: **mejorar rendimiento es una hipótesis que debe medirse**.

## Contratos entre componentes

- **Perfil de placa:** DT exacto, API/ABI, memoria real, particiones, boot/kernel/DTB, firmware, decodificadores e inputs. Separar confirmado, inferido y no leído. P291 y P271 son perfiles distintos.
- **Entrada 0.7:** usa ADB loopback existente, comprueba UID2000/P291/API28, marcador del USB y tamaños/SHA exactos de ROM 0.1.1 y OTAUpgrade capturado. Autocontrol SHA conocido y digest estricto. Abre únicamente MainActivity del OEM sin extras, Update, reinicio propio ni escritura BCB. La confirmación de apertura no demuestra instalación. Timeout de lectura del ZIP de cinco minutos, sin reintentos automáticos. El menú ya se conocía; cambia el paquete real y su validación previa.
- **Complemento0.6, completado:** ADB loopback existente en127.0.0.1:5555, perfil P291/API28 y carpeta nueva en USB marcado. Cinco etapas: creación → autocontrol SHA y certificados OTA → APK específico acreditado de OTAUpgrade → configuración/identidad → verificación final. Certificados y APK son obligatorios; origen ilegible, cambio de ruta, tamaño inválido o cualquier digest inválido detiene la captura. Funciones con prefijo propio, toybox explícito, SHA de `abc` conocido y validación de64 caracteres hexadecimales en cada consumidor. No reinicia ni abre el actualizador; tampoco instala ROM ni modifica permisos/autenticación. Fuentes y salida0.6 separadas de0.5; entrega y prueba física requieren evidencia propia.
- **Recopilador0.5, histórico:** ya se obtuvieron dos capturas parciales del mismo arranque. La cuota consumida por Google Play Services impidió copiar el quinto APK, OTAUpgrade, y no se alcanzaron certificados/configuración. La colisión con el alias `hash` de mksh produjo digests binarios vacíos aceptados como iguales; no se acredita su comprobación en el TV. Conservar código, datos y pruebas Bash originales, que no reprodujeron ese fallo. Los textos sellados y los hashes de adquisición en PC tienen validaciones separadas.
- **Entrada0.4, histórica:** informe previo → hashes de ROM/recovery → `reboot:update`. En el TV terminó sin señal. Los dos informes recuperados preceden al reinicio y no registran ese fallo. No repetir el intento a partir de sus pruebas locales ni de la existencia de una partición recovery de24MiB cuyo contenido sigue sin leerse.
- **Recovery externo:** archivo Android boot para carga temporal; clave de prueba agregada a la lista aceptada, verificación activa. No es un contenedor Amlogic de fábrica ni una imagen de disco MBR.
- **ZIP de ROM:** perfil y marcador explícitos, cinco payloads y hashes. Valida destino, respaldo y lectura posterior. Escribe boot al final; no formatea userdata. El contrato implementado está en `instalador/main_linux.go` y `package.go`.
- **Aplicación/administración, propuesto:** interfaz versionada para catálogo, descargas, diagnóstico y limpieza. El contenido web no recibe root. Limpiar videos, caché, sesión o toda la aplicación son órdenes distintas.
- **Actualizaciones, propuesto:** manifiestos declaran placa, API/ABI, versiones, hashes y firma; conservar continuidad de firma, datos y estado del agente. Actualizar WebView termina procesos que lo cargaron, por lo que la coordinación debe estar fuera de esos procesos.

## Pruebas que cierran cada etapa

| ID | Evidencia necesaria | Estado |
| --- | --- | --- |
| VAL-01 | Integridad del candidato y sus particiones | Local registrada en `analisis-rom/integridad-interna.json` |
| VAL-02 | ext4, contenido/metadatos, firma completa y hashes de payload 0.1.1 | Local registrada en `rom-simplificada/salida/RECOVERY-VERIFICACION-0.1.1.json` y `RECOVERY-COMPROBACION-0.1.1.json` |
| VAL-03 | Protocolo y contrato de Acceso USB por versión | 0.4: entrada física fallida. 0.5: pruebas locales conservadas, captura real parcial y falso positivo SHA identificado. 0.6: casos y resultados en `EVIDENCIA-TESTS-0.6.json`, incluida regresión pertinente con mksh real; captura física completa comprobada. 0.7: controles en ENTRADA-TESTS-0.7.json, menú físico observado; preparación de actualización detenida al 2 % |
| VAL-04 | Copia leída del USB, con recibo de cada versión | Copia0.6 verificada el7/9,00:22: `preparacion-usb/evidencia-06-estado.json`, código0 y SHA coincidente. `preparacion-usb/evidencia-05-estado.json` y recibo0.4 son históricos y no acreditan entrega0.6 |
| VAL-05 | Recovery visible/identificado y aceptación del ZIP en P291 | No superada:0.3/0.4 sin señal; OEM0.7 con ZIP real detenido al2% más de10min, sin recovery visible |
| VAL-06 | Respaldo completo y escritura verificada de cinco particiones | Pendiente; exigir `respaldo.json` e `instalacion.log` reales |
| VAL-07 | Primer arranque sin USB, identificación, hardware y proveedor WebView efectivo | Pendiente |
| VAL-08 | Suite APK/web/video/local/controles comparada con referencia | Pendiente |
| VAL-09 | Restauración ensayada, actualización y fallo controlado recuperable | Pendiente |

La suite funcional no equivale a certificación CTS/CDD. Usarlos como referencia de compatibilidad según [arquitectura](../ARQUITECTURA-ANDROID-TV.md). No dar por aceptada una etapa física a partir de simulaciones del protocolo o coincidencia de hashes en PC.

La captura0.5 no superó la completitud y no debe aceptarse retroactivamente por comparar sus dos copias en PC. Los [hallazgos físicos](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md) y la [regresión mksh](../rom-simplificada/instalador/MKSH-HALLAZGO-0.5.md) separan observación, defecto del recopilador e inferencia sobre el reinicio.

El complemento0.6 se acepta únicamente cuando se reciben en PC su cierre y sus archivos obligatorios con hashes válidos: autocontrol, `otacerts.zip`, `OTAUpgrade.apk` e informes requeridos. Las denegaciones o límites de lectura de la configuración se documentan como tales; no equivalen a obtener su contenido. Una compilación o regresión con mksh en PC no sustituye esa captura física. Los certificados `otacerts.zip` del Android instalado no demuestran la lista de claves del recovery. Ninguna captura sustituye el respaldo de las cinco particiones requerido antes de instalar ROM0.1.1.

Entrega complementaria0.6: [recibo USB](../preparacion-usb/evidencia-06-estado.json), 7/9/2026 a las00:22 ART, APK y guía copiadas/leídas con SHA coincidente. Captura 0.6 completada: 25 archivos adquiridos y diez SHA verificados. Ver [hallazgos](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md).

La firma integral de la ROM se verificó contra el certificado OTA realmente capturado del P291 mediante Python y OpenJDK. [Recibo](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json). No cierra VAL-05: aún falta aceptación por recovery interno y ejecución física del ZIP. Acceso 0.7 solo abre el menú tras sus controles; VAL-04 de esa versión cuenta con [recibo propio de copia/lectura](../preparacion-usb/entrada-oem-07-estado.json), del 7/9 a las 12:34 ART. El menú OEM ya se observó; Update con ZIP real quedó al 2 % por más de diez minutos.
