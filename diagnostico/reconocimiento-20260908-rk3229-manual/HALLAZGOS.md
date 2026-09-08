# RK3229-C: inventario 0.3 recibido mediante copia manual

Revisión local del 8 de septiembre de 2026. Los dos ZIP nuevos suman **41.155 B**: una ficha inicial de 1292 B y su inventario posterior de 39.863 B. Ambos contienen únicamente `informe.json` y `manifest.json`. Se releyeron los ZIP, sus CRC y los dos hashes de informes declarados en los manifiestos; los 401.434 B expandidos coinciden. El enlace `parent_capture_id` y la identidad de instalación entre ambas fichas coinciden. Son dos etapas de una captura, no dos equipos.

También se conservaron dos recibos `.local.json`, de 486 y 485 B: **971 B** en total. Su adquisición privada declara `pc_copies_verified`, relectura PC correcta y originales sin modificar. Los originales, los recibos y el catálogo permanecen privados. Este documento omite UUID de instalación/captura/volumen, nombres de archivos privados e identificadores personales. La revisión no contactó el TV ni modificó el pendrive, firmware o recibos.

## Una tercera variante documental, sin certificar identidad física

Se asigna la etiqueta local **RK3229-C** a esta combinación de firmware y almacenamiento. Difiere de las variantes [RK3229-A y RK3229-B](../reconocimiento-20260908-rk3229-usb/HALLAZGOS.md): modelo `MBOX`, compilación `CNV8b.20230725` y nombre MMC `Q7XSAB`. Su identificador de instalación tampoco coincide con los de A/B. Estos datos distinguen las capturas y son coherentes con el tercer equipo referido por el usuario; no son una identificación independiente de los chips ni un conteo certificado de aparatos.

| Observación | RK3229-A | RK3229-B | RK3229-C nuevo | P271 conservado |
| --- | --- | --- | --- | --- |
| DT | `rockchip,rk3229` | Igual | Igual | `gxlx_p271_1g` |
| Modelo declarado | TVBOX | TV BOX-3 | MBOX | Perfil Amlogic P271 |
| API | 25 | 25 | 25 | 28 |
| Etiqueta Android / versión del fingerprint | 11.1 / 7.1.2 | 13.0 / 7.1.2 | 11.1 / 7.1.2 | 9 / 9 |
| ABI Android | ARM32 | ARM32 | `armeabi-v7a`, `armeabi` | ARM32 |
| RAM visible declarada, B | 1.046.405.120 | 549.755.813.888, anómala | 1.046.446.080 | 1.031.192.576 |
| Nombre MMC declarado | QNW00M | 008GB0 | Q7XSAB | DG4008 |
| Área de usuario MMC declarada, B | 7.818.182.656 | 7.818.182.656 | 7.818.182.656 | 7.820.083.200 |
| Módulo WiFi observado | ssv6158 | ssv6x5x | ssv6x5x | 8822bs |
| Binding SDIO | SSV6XXX_SDIO | SSV6XXX_SDIO | SSV6XXX_SDIO | rtl88x2bs |
| Paquetes visibles | 69 | 88 | 74 | No comparado aquí |
| Códecs anunciados | 33 | 28 | 28 | 50 |

La comparación P271 procede de su [captura conservada](../reconocimiento-20260908-p271-mx9/HALLAZGOS.md). Las etiquetas 11.1/13.0 no acreditan esas versiones de Android: en C, API 25, fingerprint y paquete `android` declaran Android 7.1.2. El fingerprint observado es `Android/rk322x_box/rk322x_box:7.1.2/NHG47K/CNV8b.20230725:userdebug/test-keys`.

C declara kernel **3.10.104**, compilación del 25 de julio de 2023; la fecha y el parche declarado `2023-01-05` no son certificaciones de actualización. Procfs muestra cuatro entradas ARMv7, implementador `0x41`, parte `0xc07`, revisión 5 y texto `Rockchip RK3229`. `MemTotal=1021920 kB` coincide con los 1.046.446.080 B de la API Android, aproximadamente 998 MiB visibles. Son datos del mismo sistema, no dos mediciones físicas independientes. B mantiene pendiente la anomalía de 512 GiB; no trasladarla a C.

## Almacenamiento y mapa parcial observado

Sysfs declara `mmcblk0`, dispositivo `179:0`, tipo `MMC`, no removible, nombre `Q7XSAB` y 15.269.888 sectores de 512 B. Procfs coincide con el área de usuario de 7.818.182.656 B y enumera catorce particiones. Los tamaños siguientes derivan de `/proc/partitions`; no incluyen inicios ni prueban ausencia de huecos o solapamientos:

| Partición expuesta | Tamaño bruto, B |
| --- | ---: |
| mmcblk0p1 | 4.194.304 |
| mmcblk0p2 | 8.388.608 |
| mmcblk0p3 | 4.194.304 |
| mmcblk0p4 | 1.048.576 |
| mmcblk0p5 | 15.728.640 |
| mmcblk0p6 | 12.582.912 |
| mmcblk0p7 | 12.582.912 |
| mmcblk0p8 | 33.554.432 |
| mmcblk0p9 | 67.108.864 |
| mmcblk0p10 | 134.217.728 |
| mmcblk0p11 | 16.777.216 |
| mmcblk0p12 | 4.194.304 |
| mmcblk0p13 | 2.147.483.648 |
| mmcblk0p14 | 5.347.737.600 |

Frente a A, C reduce p7 de 20 MiB a 12 MiB y aumenta p14 en 8 MiB. Frente a B, p13 es de 2 GiB en lugar de 3 GiB y p14 también difiere. **No asignar nombres lógicos ni offsets a estas particiones por semejanza.** Los montajes citan aliases `system`, `cache`, `metadata` y `userdata` bajo `30020000.rksdmmc/by-name`, pero esta ficha no relaciona cada alias con un número pN.

La capacidad del sistema de archivos `/data` es 5.180.227.584 B; `/system` y `/vendor` informan 2.080.194.560 B. La coincidencia de capacidades no demuestra particiones independientes ni su igualdad binaria. `/data`, `/cache` y `/metadata` estaban montados RW; `/system`, RO. El inventario de Android no constituye una instantánea estable de bloques.

Procfs también enumera `mmcblk0rpmb`, `179:32`, con 512 KiB declarados. **No se abrió ni copió RPMB** y queda fuera del adaptador de copia del extractor. La enumeración limitada no permite concluir presencia o ausencia de otras áreas, como boot0/boot1. No hay imágenes de particiones, userdata ni memoria completa en estos ZIP.

## Radio, WebView, video y software

Se observa `ssv6x5x` en estado `Live` y el enlace SDIO `mmc2:0001:1` al driver `SSV6XXX_SDIO`, bajo el controlador `30010000.rksdmmc`. Coincide el nombre de la pila con B, pero no identifica de forma independiente la radio ni prueba asociación WiFi, bandas de 5 GHz, tráfico o estabilidad. La denominación comercial «5G» no resuelve esas capacidades.

Google WebView **55.0.2883.91** y Chrome **65.0.3325.109** aparecen habilitados. Son versiones distintas de A y B. La consulta del proveedor WebView seleccionado está marcada `api_not_available`; el reconocedor no cargó WebView. No se conoce el proveedor que ejecutará la APK del usuario.

La lista anuncia 28 códecs, incluidos VP9 y HEVC con nombres Rockchip y Google. Las consultas de capacidades de `OMX.google.vorbis.decoder`, `OMX.google.raw.decoder` y `OMX.google.flac.encoder` registraron `NullPointerException`; no convertirlas en capacidades verificadas. No se instanciaron códecs ni EGL, ni se probaron aceleración, VP9 con alfa, canvas o videos simultáneos. La pantalla declara 1280 × 720 a aproximadamente 60 Hz; los valores xdpi/ydpi de 2.147.483,75 son anómalos y no describen una densidad física fiable.

Entre los 74 paquetes visibles no aparece `com.android.documentsui`. Esto es compatible con la foto anterior de `ActivityNotFoundException` al solicitar el selector, pero la visibilidad del inventario no certifica ausencia total de proveedores. Se observan `android.rockchip.update.service` 1.8.1, `com.adups.fota` 5.14 y `com.adups.fota.sysoper` 5.3.3; su presencia no prueba uso de Update, tráfico ni malware. No se activó ninguno.

El certificado que PackageManager declara para `android`, Settings, PackageInstaller y RKUpdateService tiene SHA256 `2d370c21f5dfd553d2a796314b70925fb38adeef90864c920bbbbb12887d3522`; coincide con el certificado de plataforma observado en A/B. Es un hash de certificado informado, **no un hash de esas APK ni de la ROM**, y no demuestra qué firma acepta recovery. La APK de reconocimiento aparece como 0.3, código 3, con el certificado del proyecto esperado. No se capturaron imágenes de recovery ni su almacén de claves.

## Exportación manual y alcance del hallazgo USB

El inventario declara `export_method_requested=local_manual_copy`. Los dos recibos locales coinciden con el tamaño y SHA256 de sus respectivos ZIP y declaran destino `android_downloads`, `file_sync_verified=true` y `local_readback_sha256_verified=true`. Conservan `directory_sync_verified=false` y `usb_copy_verified=false`: acreditan el resultado declarado de la copia local, no una exportación directa de la APK al USB. La adquisición íntegra en PC confirma el contenido recibido tras la copia manual informada por el usuario; no modifica retrospectivamente esos recibos ni acredita expulsión física segura.

El registro de descubrimiento 0.3 terminó tras revisar **11 directorios**, sin timeout, trabajador pendiente o límite alcanzado. Encontró **un directorio con marcador válido** en `/storage/<UUID>/TVBASE-RECONOCIMIENTO`. Sus campos conservan `write_access_tested=false`, `writes_performed=false` y `automatic_selection_performed=false`. Se observaron además un volumen `vfat` montado bajo `/mnt/media_rw/<UUID>` y vistas FUSE, incluida `/storage/<UUID>`.

Las consultas a `/mnt/media_rw` y su descendiente registraron indisponibilidad; no guardaron un errno que permita afirmar exactamente permiso denegado frente a ausencia. **Descubrir y leer el marcador no demuestra poder escribir en el destino.** El registro nuevo tampoco reconstruye el estado del intento 0.2 que devolvió `automatic null`: no confirma una causa histórica de ruta, permisos o proveedor ni que la exportación directa esté resuelta. La copia manual permitió recibir estas fichas conservando esa incertidumbre.

## Límites y uso posterior desde recovery

El inventario de hardware terminó en **1599 ms**, con estado `finished_with_observations` y sin lector pendiente declarado. Alcanzó 160 intentos de lectura: 128 observaciones, 32 fuentes ausentes con ENOENT, cinco exclusiones y una omisión por límite; registró 6839 B de texto y ningún timeout de esa sección. Lo omitido no demuestra ausencia de hardware. La cadena del colector sigue declarando `HardwareCollector/0.2`, coherente con su reutilización por reconocimiento 0.3.

Los tres comandos auxiliares conservan estado interno `partial`, código de salida desconocido y `process_may_continue=true`. El inventario finalizado y la ausencia de lector pendiente no convierten retrospectivamente esos recibos en ejecución con código cero.

El usuario confirmó que **puede abrir recovery en C**. Se registra como observación del usuario; no demuestra aceptación del ZIP del extractor ni ejecución de su código. La ABI Android ARM32 y la MMC declarada orientan la evaluación del [extractor desde recovery](../extractor-recovery-0.1/README.md), pero no acreditan la ABI/kernel del recovery instalado, su confianza de firma ni lectura real de bloques. Bootloader figura como desconocido. Esta revisión no ejecutó el extractor ni instaló otra ROM.

A/B/C comparten exactamente `rockchip,rk3229`; esa coincidencia no permite repartir sus ROM ni seleccionar automáticamente una unidad física. C fue seleccionado para la primera extracción, con un único plan para ese DT y el ejecutable 0.1 ya sellado, según la [matriz vigente](../../docs/MATRIZ-PERFILES.md). Recovery deberá revalidar topología, tamaños, inicios, montajes y consumidores. El análisis de [P271](../../docs/evidencia/RECOVERY-P271-ALCANCE.md) ya separa certificados Android de confianza del recovery; esa distinción también corresponde a Rockchip y no hace transferibles las guardas entre perfiles. **Estas fichas son inventarios comparables: todavía no hay copias de bloques C ni una restauración ensayada.**
