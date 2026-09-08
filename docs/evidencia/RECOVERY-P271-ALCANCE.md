# P271: alcance comprobado para un extractor desde recovery

Revisión local del 8/9/2026. El usuario pide ahora extraer los originales desde recovery, sin instalar una ROM ni una APK; informa que la entrada del P271 es parecida a la del P291 y que puede entrar con facilidad en otros equipos. Esa observación orienta el trabajo, pero no acredita todavía una secuencia concreta de entrada, un ZIP aceptado ni una captura de bloques del P271. Esta revisión no contactó ningún TV, no escribió al pendrive y no montó ni modificó firmware.

## Evidencia del segundo TV

La captura conservada del 5/9 identifica **`gxlx_p271_1g`**, distinto de `gxlx2_p291_1g`. Fue obtenida con Android activo y acceso shell **UID 2000**, no root. El [perfil del segundo TV](../../diagnostico/android-20260905-142854-a8286d9a/PERFIL-SEGUNDO-TV.md) y su [registro estructurado](../../diagnostico/android-20260905-142854-a8286d9a/perfil-segundo-tv.json) documentan Android 9/API 28, ABI `armeabi-v7a,armeabi`, kernel 4.9.113 `armv7l`, plataforma `ampere` y WiFi `8822bs`/SDIO `024c:b822`. La ABI orienta la construcción de un ejecutable ARM32; no demuestra que el recovery instalado lo ejecute.

`ro.bootloader` informa `unknown`. Las propiedades de A/B, slot y verificación de arranque están vacías en esa captura: no prueban que esos mecanismos estén ausentes. No hay en este conjunto una imagen adquirida de boot, recovery o bootloader del P271, ni sus claves internas de recovery, ni un respaldo integral de su almacenamiento.

## Geometría: semejanzas que no autorizan reutilizar el perfil P291

La lectura original `diagnostico/android-20260905-142854-a8286d9a/particiones.txt` muestra estos valores de `/proc/partitions`. La conversión es de bloques de 1024 bytes; no son offsets.

| Entrada observada | Major:minor | Bloques de 1024 B | Bytes |
| --- | --- | ---: | ---: |
| mmcblk0 | 179:0 | 7636800 | 7820083200 |
| mmcblk0p6 | 179:6 | 24576 | 25165824 |
| mmcblk0p11 | 179:11 | 16384 | 16777216 |
| mmcblk0p16 | 179:16 | 921600 | 943718400 |
| mmcblk0p17 | 179:17 | 131072 | 134217728 |
| mmcblk0p18 | 179:18 | 1310720 | 1342177280 |
| mmcblk0p19 | 179:19 | 131072 | 134217728 |
| mmcblk0p20 | 179:20 | 3579712 | 3665625088 |

La misma lectura lista aliases `boot`, `bootloader`, `cache`, `cri_data`, `data`, `dtbo`, `env`, `logo`, `metadata`, `misc`, `odm`, `param`, `product`, `recovery`, `reserved`, `rsv`, `system`, `tee`, `vbmeta` y `vendor`, dirigidos a `/dev/block/<nombre>`. **No muestra el rdev del destino de cada alias:** no permite asignar por sí sola `recovery` a p6, `boot` a p11 o `data` a p20. El parecido con P291 no reemplaza esa comprobación. Tampoco captura los starts, topología sysfs completa o lectura ioctl de tamaños en recovery.

La capacidad del disco P271, **7.820.083.200 B**, difiere de los **7.650.410.496 B** del primer P291. También difiere p20. Los valores P291 fijados en [block_layout.go del instalador 0.2.2](../../rom-simplificada/original-p291/instalacion-022/block_layout.go) no sirven como geometría genérica. Se observan además dispositivos `mmcblk0boot0`, `mmcblk0boot1` y `mmcblk0rpmb`; listarlos no acredita haberlos leído ni respaldado.

Android tenía `/system`, `/vendor` y `/data` montados. Una copia secuencial de bloques mientras el sistema escribe no constituye por sí sola una instantánea consistente. El extractor desde recovery debe acreditar por separado sus orígenes, estado de montaje, estabilidad y resultado de lectura. El nombre recovery no garantiza que todas las particiones estén desmontadas ni que el propio recovery no escriba registros o metadatos.

## Entrada y aceptación de paquetes

El [análisis estático del actualizador P271](../../diagnostico/android-20260905-142854-a8286d9a/analisis-actualizador/HALLAZGOS.md) identifica `com.droidlogic.otaupgrade/.MainActivity` y un selector de ZIP. El APK mide 190988 B y tiene SHA256 `9ffb822fc76974ee9df8c5493f0929638b69140f71506946cb410bab489a1d9c`; coincide byte por byte con el obtenido después del P291. Puede reutilizarse el análisis de ese código, no las características del bootloader o recovery.

**Pulsar Update no es una consulta inocua ni una entrada de diagnóstico:** el código intenta recrear `/cache/recovery/command` antes de presentar la confirmación; puede incluir opciones de borrado según sus preferencias. Cancelar el diálogo no limpia esa orden. La presencia de la actividad, el selector y su código no demuestra que el recovery P271 acepte un ZIP concreto o que haya completado una entrada física.

La referencia local `rom-simplificada/instalador/gxl_p271_v1-referencia.h` incluye `storeboot`, BCB, `update`, búsqueda de `aml_autoscript` y de `recovery.img`. Es código público de referencia de una configuración P271, **no una extracción del U-Boot de este equipo**. No demuestra GPIO, puerto USB, offsets ENV/BCB, variables vigentes ni comportamiento de este ejemplar.

Por ello, no repetir Update, AccesoUSB09, el preparador ENV/BCB del P291 ni su ZIP de instalación para obtener una copia. La preparación P291 modificó metadatos de arranque específicos y está documentada por separado; no es un extractor universal. Si el usuario ya llega al recovery de un equipo, se puede evaluar allí un paquete de extracción independiente sin añadir esa preparación. Si la entrada P271 sigue sin resolverse, requiere una ruta comprobada para ese aparato; este documento no prescribe una escritura de ENV o BCB.

## Confianza de firma: Android y recovery son evidencias diferentes

El P271 conserva `otacerts-del-segundo-tv.zip` de 1073 B, SHA256 `7dd077650421772a3114c9132cd3da989b65f073459b7d8023e7138f2323a6c8`. Su [certificado OTA](../../diagnostico/android-20260905-142854-a8286d9a/certificados-ota.json) tiene huella SHA256 `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc`, igual al almacén Android P291. **No se leyó `/res/keys` del recovery P271.** La coincidencia del certificado Android no determina el algoritmo que el recovery selecciona ni acredita aceptación de firma.

Para el P291 sí se examinó el recovery original: una clave RSA de 2048 bits, exponente 3 y formato v1 sin prefijo, asociada a SHA1. [Análisis histórico de recovery P291](../../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md). El paquete 0.2.2 usó firma integral PKCS#7 RSA-PKCS1v1.5/SHA1, y su [ejecución física](INSTALACION-FISICA-P291-022.md) tiene evidencia propia. Ese antecedente no convierte al extractor nuevo en probado, ni extiende la aceptación al P271 o a Rockchip.

En el empaquetador P291, `KEYFILE` identifica la copia local de `res/keys` y `SIGNING` el directorio local de firma; [empaquetador](../../rom-simplificada/original-p291/instalacion-022/empaquetar_original.py) y [verificador de firma v1](../../rom-simplificada/original-p291/instalacion-022/firma_ota_v1.py) documentan las rutas y verificaciones. No se reproduce ni publica material privado. El SHA256 esperado de `res/keys` P291 es `cd0788004cfa998c7bbede4811b791187139504a01415b9d30df5609458398df`.

## Resultado y límites de la revisión

Hay base para construir un extractor ARM32 separado que observe y copie bloques desde un recovery compatible, conservando informes por unidad y denegaciones explícitas. Permanecen sin acreditar para P271: entrada concreta, claves/algoritmo del recovery, ejecución del extractor, mapa de bloques revalidado, exportación USB física y restauración. La condición de solo extracción corresponde al ejecutable nuevo; no se obtiene ejecutando parcialmente el instalador 0.2.2, cuyo flujo continúa automáticamente del respaldo al formato y flash.

Esta revisión releyó los archivos locales; no generó evidencia nueva del TV. Sellos de las lecturas crudas usadas: `particiones.txt` SHA256 `a35695e8dae4890f5a91721394bdaf7dc1e5dd7dad975262adcfcc4ad56a6324`; `permisos.txt` SHA256 `d489668649bf9b4cdb4ce53e992319557649604310cf22eab775a1a1bff42015`. Las capturas originales y cualquier futura imagen se conservan privadas; un respaldo no debe transferir identidad, claves o datos personales a otro TV.
