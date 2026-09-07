# Especificación del producto y aceptación

Versión documental2, tras la prueba física de Acceso USB0.4. Recoge el pedido vigente del usuario. La evolución de su APK no bloquea preparar y probar la plataforma. El alcance no incluye investigar la actualización automática que afectó al WiFi del primer equipo.

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
| REQ-11 | Recuperabilidad y diagnóstico | Antes de escribir, guardar/verificar originales; demostrar restauración desde una entrada disponible cuando Android falle | Entrada0.4 falló sin recovery visible; recopilador0.5 preparado para ampliar evidencia sin reiniciar. Respaldo y restore físicos pendientes · C-ENTRY, C-REC, C-ZIP |
| REQ-12 | Segundo WebView opcional | Automatización en segundo plano sin degradación inaceptable del video principal, tolerando cierre por memoria | Secundario y propuesto · C-APP |

No se deducen FPS, bitrate, perfil VP9 ni resolución completa de la descripción «1280». La doble composición es referencia obligatoria; sus archivos se incorporarán cuando existan. La limpieza o un motor nuevo pueden cambiar el rendimiento en ambas direcciones: **mejorar rendimiento es una hipótesis que debe medirse**.

## Contratos entre componentes

- **Perfil de placa:** DT exacto, API/ABI, memoria real, particiones, boot/kernel/DTB, firmware, decodificadores e inputs. Separar confirmado, inferido y no leído. P291 y P271 son perfiles distintos.
- **Recopilador0.5 vigente:** ADB loopback existente en127.0.0.1:5555, perfil P291/API28 y una carpeta nueva del USB marcado. Captura datos de arranque, registros pstore como bytes, APK/permisos del actualizador de este P291, certificados OTA públicos y configuración legible. Verifica tamaño y SHA de las copias; conserva ausencias, límites y denegaciones. No reinicia, no abre el actualizador, no instala ROM ni modifica permisos/autenticación. La prueba física y la copia USB requieren sus propios recibos, independientes de la compilación.
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
| VAL-03 | Protocolo y contrato de Acceso USB por versión | 0.4:12 casos y7 controles locales, entrada física fallida. 0.5:`EVIDENCIA-TESTS-0.5.json` registra casos ADB, controles, sintaxis y escenarios sintéticos de la revisión probada; captura real pendiente |
| VAL-04 | Copia leída del USB, con recibo de cada versión | `preparacion-usb/evidencia-05-estado.json` acredita copia0.5 y lectura SHA, código0 (7/9,00:00). Recibo0.4 conservado como histórico |
| VAL-05 | Recovery visible/identificado y aceptación del ZIP en P291 | No superada:0.3 y0.4 dejaron sin señal, sin recovery visible |
| VAL-06 | Respaldo completo y escritura verificada de cinco particiones | Pendiente; exigir `respaldo.json` e `instalacion.log` reales |
| VAL-07 | Primer arranque sin USB, identificación, hardware y proveedor WebView efectivo | Pendiente |
| VAL-08 | Suite APK/web/video/local/controles comparada con referencia | Pendiente |
| VAL-09 | Restauración ensayada, actualización y fallo controlado recuperable | Pendiente |

La suite funcional no equivale a certificación CTS/CDD. Usarlos como referencia de compatibilidad según [arquitectura](../ARQUITECTURA-ANDROID-TV.md). No dar por aceptada una etapa física a partir de simulaciones del protocolo o coincidencia de hashes en PC.

La evidencia0.5 se acepta como captura solamente cuando existe su carpeta completa con verificaciones finales y se lee en la PC. Obtener un informe puede concluir correctamente dejando archivos denegados o fuera de límite: eso debe figurar como limitación, nunca como lectura exitosa de su contenido. Los certificados `otacerts.zip` del Android instalado no demuestran la lista de claves del recovery. Ninguna captura sustituye el respaldo de las cinco particiones requerido antes de instalar ROM0.1.1.
