# Candidato Android 9 P291: inspeccion local, 5/9/2026

Se descargo un candidato concreto y se examinaron sus bytes, sin ejecutar sus programas, instalar herramientas incluidas ni escribir dispositivos.

## Resultado

- El archivo incluye **gxlx2_p291_1g**, coincidente con el identificador del dossier original. Tambien incluye P291 y P295 para 1g, 2g y 3g.
- El DTB P291 1g contiene `arm,mali-450`, `amlogic, vdec` y `amlogic, amhdmitx`. Esto confirma configuracion prevista, no funcionamiento en nuestro equipo.
- El texto de propiedades de la imagen declara Android **9**, SDK **28**, ABI `armeabi-v7a`, placa `S905L3`, producto `p291_iptv` y modelos `HG680-LY`/`HG680-LC`.
- Fingerprint: `Fiberhome/p291_iptv/p291_iptv:9/PPR1.180610.011/4.350135.00.21v1:userdebug/test-keys`.
- Parche de seguridad declarado: **2018-08-05**. No es una base actualizada ni el producto Android minimo terminado.
- Declara `ro.treble.enabled=true` dentro de ESTE candidato. No acredita Treble en ninguno de los TV boxes del usuario ni garantiza una GSI.
- No aparecen `P05L`, `5V300A1` ni `1C11H16M` en la busqueda literal sobre la IMG. No se ha confirmado coincidencia de placa, parametros DDR, arranque ni perifericos. **Compatibilidad no confirmada: la coincidencia del DTB por si sola no la demuestra.**

## Archivo e integridad

Origen del mantenedor: https://github.com/ophub/kernel/releases/tag/tools

Archivo: `android_tv_mgv2000-s905l3b_and_hg680-lc-s905l3_v9.tar.xz`, **489920948 bytes**.

SHA-256 local, coincidente con el digest publicado por GitHub:

`d5854687c8241e57769019497745b38019b7a6d3cab2be7cf06d918474cbda8e`

IMG extraida con nombre local `candidato-android9.img`, **1323007268 bytes**.

SHA-256 local de la IMG:

`bd8a8d9c02f6aa1119e5ea7708f2b49a1e4c7fef6169d30bbd1604981eb042e5`

El nombre original de la IMG identifica un paquete HG680-LC/S905L3 de grabacion por cable. El TAR contiene tambien un EXE USB Burning Tool 2.1.6.8, un PDF y dos JPG. Esos archivos no se extrajeron ni ejecutaron.

## Tipo y limites del analisis

Contenedor Amlogic V2, magic `0x27b51956`, 30 entradas: USB DDR/UBOOT, cargador de grabacion, configuraciones y particiones boot, bootloader, dtbo, logo, metadata, odm, product, recovery, system, vbmeta, vendor y DTB. **No es un pendrive Android arrancable ni un ZIP de actualizacion local listo para usar.**

El lector se basa en la estructura de contenedor publicada por [7Ji/ampack](https://github.com/7Ji/ampack/blob/master/src/image.rs), sin ejecutar ese programa. Se comprobaron magic, version, longitudes, limites de partes y cabeceras FDT. Se conserva la referencia fuente en `formato-ampack-image.rs` y el lector acotado en `inspeccionar-rom.py`.

La verificacion posterior **confirmo el CRC32 interno del contenedor y los 12 SHA-1 de las particiones**, incluido `_aml_dtb`. El CRC calculado y declarado es `0xa8710cf7`; se uso el algoritmo publicado por AMpack, que procesa desde byte 4, empieza en `ffffffff` y no aplica XOR final. Los elementos VERIFY contienen el prefijo `sha1sum ` y 40 caracteres hexadecimales, segun la fuente del formato.

El detalle gzip quedo localizado: al elemento `_aml_dtb` le falta **un byte final `00` del campo ISIZE**. El trailer esperado es `f979a10100780500` y los bytes almacenados terminan en `f979a101007805`. La tabla declara 92736 bytes y el elemento VERIFY comienza inmediatamente despues; esos mismos 92736 bytes coinciden con su SHA-1. Por tanto, no es un error de offsets del lector ni una descarga distinta de la publicada. Como prueba exclusivamente en memoria se agrego ese `00`: zlib valido CRC y longitud y produjo exactamente los mismos 358400 bytes, que contienen los seis DTB completos. **No se modifico la IMG ni se creo una ROM reparada.** La completitud del contenido descomprimido esta acreditada, pero sigue sin probarse si el cargador de esta placa tolera el trailer recortado.

No se montaron sistemas de archivos. Las propiedades de Android se localizaron como texto con sus offsets; no se dio por probado que todas sean las efectivas en arranque.

El informe detallado y lista TAR estan en `informe-inspeccion.json`; la comprobacion posterior, en `integridad-interna.json`; el origen y digest publicados, en `origen-github.json`. Los DTB descomprimidos quedan como datos en `datos-dtb-2.bin` y `datos-dtb-10.bin`. `dtb-comprimido-original.gz` conserva exactamente el elemento original de 92736 bytes. El verificador reproducible es `verificar-integridad-interna.py`, con referencias fuente `formato-ampack-crc32.rs` y `formato-ampack-sha1sum.rs`.

## Relacion con el dossier

Las dos imagenes que el dossier ya enumeraba son **Armbian** (kernels 6.12.91 y 6.18.33). No eran ROM Android alternativas. Este candidato Android se agrega como material de analisis aparte. El nuevo TV box ofrecido por el usuario sigue siendo otro dispositivo y no hereda la identidad, compatibilidad ni resultados del original.
