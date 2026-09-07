# Recovery original: firma, BCB y compatibilidad de arranque

7/9/2026. Análisis **offline** de `recovery.img`, `boot.img` y `misc.img` del respaldo crítico adquirido a las 19:41. No se ejecutaron binarios del TV, no se modificaron imágenes originales y no se generó otro paquete. La evidencia derivada queda en `privado/recovery-original-analisis/` dentro de este directorio de diagnóstico.

**La aceptación de la firma SHA-256 de 0.1.2 por el recovery interno no está acreditada.** Su única clave coincide con la del ZIP, pero está expresada en el formato que AOSP 9 interpreta como SHA-1. Además, el arranque de 0.1.2 contiene diferencias de kernel y configuración de hardware respecto del original. Un cambio de firma no resuelve esas diferencias.

## Respaldos inspeccionados

Se volvieron a cotejar tamaño, SHA256, estado verificado y códigos de adquisición contra el manifest privado del respaldo. Las copias se verificaron nuevamente en PC:

| Imagen original | Bytes | SHA256 |
| --- | ---: | --- |
| `recovery.img` | 25165824 | `4d7fda26b485657e48bcbb5b253ac81ea21c3a34f21d01e52cbe1dc18295c6af` |
| `boot.img` | 16777216 | `13e027a3aae1af232d1d700421486f32b7958a9fa0a157d8cbd3c47243ab697d` |
| `misc.img` | 8388608 | `c8b5991390836e2f03693d8a4f6f2f4ea2b223c20951a119155fba19cf542549` |

Son copias de las particiones seleccionadas, no una demostración de restauración. No incluyen por sí solas todos los datos del equipo ni convierten la adquisición de un sistema encendido en una instantánea atómica.

## Clave y algoritmo de firma

El ramdisk del recovery contiene una sola entrada en `res/keys`, sin prefijo `vN`, con RSA de 2048 bits y exponente 3. Se comprobaron también sus parámetros numéricos auxiliares. La clave pública coincide exactamente con el certificado de prueba del ZIP 0.1.2, cuyo SHA256 es `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc`. El archivo de claves tiene SHA256 `cd0788004cfa998c7bbede4811b791187139504a01415b9d30df5609458398df`.

En el [verificador oficial de AOSP 9](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/verifier.cpp), `load_keys` interpreta la entrada sin prefijo como versión 1: RSA/exponente 3 con SHA-1. La versión 3 utiliza la misma clase de clave con SHA-256. `verify_file` selecciona el hash según esa configuración, no simplemente según el certificado incluido en el ZIP.

Se reprodujo esa selección sobre **la firma y los bytes firmados reales de 0.1.2**:

| Comprobación en PC | Resultado |
| --- | --- |
| Firma integral actual, RSA/SHA-256 y certificado del ZIP | Verifica. |
| Misma firma, mismos datos y misma RSA, con SHA-1 seleccionado por la política AOSP 9 v1 | No verifica: `InvalidSignature`. |
| Ejecución del verificador original del TV | No realizada. |

Por tanto, la política AOSP 9 **rechaza esta combinación**. Esto es una reproducción del comportamiento de referencia con los datos reales; no prueba que el ejecutable OEM no tenga modificaciones. El binario original `sbin/recovery`, SHA256 `436aa9c6fadc637d0c16d1924a22707b74214960bcd09c876d7b0964a5524dc3`, contiene mensajes compatibles con ese verificador, pero no expone símbolos útiles de `load_keys`/`verify_file`. Las cadenas de texto no acreditan equivalencia de código. Debe conservarse la conclusión operativa: **SHA-256 no acreditada; compatibilizar el paquete sin modificar recovery es una opción pendiente de revisión**.

El ZIP no contiene firmas JAR `.SF`/`.RSA` ni `MANIFEST.MF`. La firma analizada es PKCS#7 sobre el archivo completo, almacenada en el comentario final del ZIP. `META-INF/com/android/otacert` contiene el certificado; no sustituye esa firma ni la convierte en una firma JAR.

## Alternativa de firma propuesta, todavía no construida

Preparar un **archivo nuevo**, manteniendo el ZIP SHA-256 publicado localmente intacto, con firma integral PKCS#7/RSA-SHA1 compatible con la clave v1. Se conservarían los bytes de las entradas, los cinco payloads, el manifest y el instalador; solamente cambiarían la firma/comentario final, su footer y la longitud del comentario EOCD. No se modificarían las claves ni la partición recovery.

Antes de considerarlo entregable:

1. Revisar el código de envoltura y la propuesta conjunta con Fable. No basta con cambiar una etiqueta de algoritmo.
2. Verificar con la clave extraída y la selección SHA-1 del verificador de referencia; contrastar además con una implementación independiente que admita ese algoritmo.
3. Confirmar todos los SHA256 de payloads, CRC del ZIP, manifest e instalador idénticos, y aceptación por el validador del paquete en PC. Comprobar que los registros ZIP y datos previos a EOCD permanecen iguales.
4. Emitir nombre y recibo nuevos con tamaño/hash exactos. No sustituir silenciosamente 0.1.2 ni reutilizar su recibo de firma SHA-256.

Esta alternativa atiende un requisito del recovery heredado. No acredita todavía su ejecución física, el mapa de bloques ni la compatibilidad del nuevo arranque.

## BCB real en misc

La [estructura oficial de Android 9](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/bootloader_message/include/bootloader_message/bootloader_message.h) ubica el mensaje en el byte **0** de misc: `command` ocupa 32 bytes, `status` los siguientes 32, `recovery` comienza en 64 y ocupa 768; `stage` comienza en 832. La [implementación de lectura/escritura](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/bootloader_message/bootloader_message.cpp) utiliza ese desplazamiento.

La copia original contiene:

```text
command = boot-recovery
status = vacío
recovery = recovery
           --update_package=@/cache/recovery/block.map
           --locale=es-ES
stage = vacío
```

La orden persistente de entrar a recovery está acreditada por lectura de la partición. En esa estructura no figura una opción de wipe. Esto no garantiza todos los efectos del recovery ni acredita que haya arrancado. Según las lecturas posteriores a Update ya documentadas, `block.map` está ausente aunque la copia interna del ZIP sea íntegra. Un reinicio forzado no crea ese mapa: la orden actualmente guardada no tiene completo el recurso que referencia.

## Fstab y acceso a particiones/USB

El recovery original tiene una fstab v2. Usa los mismos alias `/dev/block/recovery`, `/boot`, `/misc`, `/system`, `/vendor`, `/odm`, `/product`, `/cache` y `/data` observados en Android; los cinco destinos de la ROM están contemplados. System/vendor/product/odm se declaran ext4 y boot como emmc. Esto confirma correspondencia de nombres, no prueba que todos monten correctamente bajo recovery.

La entrada `/dev/block/sd##` → `/udisk`, tipo `auto`, expresa el patrón USB del fabricante. No debe confundirse con un alias literal ausente. La fstab contempla lectura de un disco USB **una vez ejecutado recovery**; no demuestra que el bootloader arranque un `recovery.img` externo desde el pendrive. El SHA256 de la fstab extraída es `adbf7454c9f4f452b014fd3394496f3f4e675cbe16366cac278077c56c40cfd4`.

## Kernel y árbol de dispositivos

Boot y recovery originales contienen **el mismo kernel y el mismo multi-DTB**. Ambos tienen cabecera Android v1 con extensión de 1648 bytes y verifican su identificador bajo el algoritmo de esa versión. Esto favorece estudiar la entrada al recovery original, conservando su soporte de hardware, en vez de asumir necesario un recovery del candidato.

| Componente | Original respaldado | Boot de 0.1.2 |
| --- | --- | --- |
| Kernel | 9914832 bytes; SHA256 `9968c75f691f67dcb805ef8105e1ca534f73430bcf8b3920a066580e326b791a` | 9995832 bytes; SHA256 `51de4ded699adabff796fe9e363390c822f97ae8e792b6dff2c76bc64202054a` |
| Multi-DTB | 174080 bytes sin compresión; 3 perfiles | 92737 bytes gzip, 358400 al expandir; 6 perfiles |
| Perfil `gxlx2_p291_1g` | 56828 bytes; SHA256 `832137e970f01f67d23ba466beff7308860d48a71f315e80d993299e6bf71925` | 58929 bytes; SHA256 `ce988d18ea6cfa1379d08aaf9c6b47fad41303c98ad3d78baa493c2d5cc2c707` |

Que ambos contengan el mismo nombre de perfil no hace equivalentes sus configuraciones. Hay 465 diferencias de propiedades en la comparación directa; muchas son renumeraciones de referencias `phandle` y **no** deben contarse como cambios físicos independientes. Entre las diferencias de valores que requieren revisión están:

| Nodo:propiedad exacta | Original | Candidato |
| --- | --- | --- |
| `/partitions/vendor:size` | 943718400 bytes (900 MiB) | 335544320 bytes (320 MiB) |
| `/sdio@d0070000/sdio:f_max` | 100000000 Hz | 200000000 Hz |
| `/wifi:interrupt_pin` | GPIO 89, flags 0 | GPIO 100, flags 0 |
| `/wifi:irq_trigger_type` | `GPIO_IRQ_LOW` | `GPIO_IRQ_HIGH` |
| `/emmc@d0074000/emmc:f_max` | 100000000 Hz | 50000000 Hz |
| `/meson-fb:display_mode_default` | `720p60hz` | `1080p60hz` |
| `/reserved-memory/linux,di_cma:size` | 41943040 bytes | 0 |
| `/reserved-memory/linux,vdin1_cma:size` | 16777216 bytes | 20971520 bytes |

Los especificadores GPIO anteriores resuelven en ambos árboles al controlador `/pinctrl@4b0/bank@4b0`; el cambio 89→100 no es solamente una renumeración de `phandle`. En cambio, `/wifi:power_on_pin` conserva GPIO 88 y flags 0 en ese mismo controlador.

Además cambian mapas del control remoto y la habilitación de entradas de video. Estos datos son valores del árbol, no mediciones de rendimiento ni pruebas de que cada parámetro vaya a aplicarse. En particular, la declaración distinta de vendor exige revisar qué árbol usa realmente el cargador/kernel y cómo determina las particiones: conservar una partición DTB separada no demuestra que el DTB incorporado en boot sea irrelevante.

Los dos perfiles declaran 17 entradas de particiones con los mismos nombres y el mismo orden lógico al resolver sus referencias. De sus propiedades `size`, solamente difiere vendor. Para los cinco destinos de instalación:

| Propiedad de partición | Original, bytes | Candidato, bytes | Capacidad observada en Android original |
| --- | ---: | ---: | ---: |
| `/partitions/boot:size` | 16777216 | 16777216 | 16777216 |
| `/partitions/vendor:size` | 943718400 | 335544320 | 943718400 |
| `/partitions/odm:size` | 134217728 | 134217728 | 134217728 |
| `/partitions/system:size` | 1342177280 | 1342177280 | 1342177280 |
| `/partitions/product:size` | 134217728 | 134217728 | 134217728 |

La imagen vendor de 320 MiB cabe en la partición actual de 900 MiB, pero **caber no demuestra conservar el mapa usado en el siguiente arranque**. La diferencia de tamaños declarados es 608174080 bytes. No se calculan aquí supuestos desplazamientos nuevos: el orden lógico del DTB tampoco reproduce por sí solo el orden físico observado de todas las particiones. Los tamaños de las 17 entradas, incluido el valor especial de data, están guardados en la evidencia privada; no se interpretó ese valor especial como una capacidad física real.

El boot candidato también marca versión 1 pero tiene su extensión a cero, como ya ocurría en el candidato heredado. Su identificador no coincide con los cálculos estándar probados sobre tres componentes ni con el de v1. Esto no demuestra corrupción bajo el formato particular del fabricante, pero impide presentarlo como una imagen Android v1 estándar validada. No se normalizó ni alteró aquí.

## Evidencia y decisión pendiente

El resultado reproducible privado es `recovery-original-analisis/resultado.json`, SHA256 `c018dfa9332180ee6896874fbfa45b1833c36494ecd8494be8378f77fe8fe6f4`. El lector `analizar.py` tiene SHA256 `1746c34e71e68aca4b687e7b060453991855fc49c2ae09c3969f8b8e5994b2d3`; reutiliza solamente funciones de los inspectores/empaquetadores existentes, sin ejecutar sus rutinas de construcción. El diff completo de propiedades está en `dtb-p291-diferencias.json`, SHA256 `3c01531959829195b5f5a0a83d96f32eaef7b9c52f45bb1c1054317bf9734b6d`. La comparación de tamaños está en `particiones-dtb.json`, SHA256 `dd7fc59ba33486f39f83c7028aff147025b2c50d244bb9b4a2bb236de96cc2ac`.

Antes de elegir una instalación siguen separados tres requisitos: **firma compatible**, **ruta de paquete completa para recovery** y **compatibilidad del arranque/payloads**. El respaldo reduce la pérdida de información, pero todavía no demuestra un método de restauración que funcione si el equipo deja de arrancar. Este análisis no ejecutó otra actualización ni un reinicio forzado.

La propuesta preferente es construir una nueva ROM simplificada **a partir de las imágenes originales de este TV**, una vez completadas y verificadas las copias de system/vendor/product/odm: conservar kernel, DTB, geometría y componentes de video originales, retirar Bluetooth y software prescindible e integrar el navegador/WebView y el inicio propios. Seguiría siendo una ROM para instalar en memoria interna desde USB, no solamente una actualización de aplicaciones. Permite reducir diferencias ajenas al objetivo, pero no garantiza reparar WiFi: su driver y servicio originales también presentaron el bloqueo documentado y deben validarse.

La alternativa es adaptar el candidato con el DTB original y revisar coherentemente kernel, módulos, ramdisk, fstab y particiones. Un reemplazo aislado de DTB no acredita compatibilidad entre kernel y drivers. Ambas son propuestas todavía no implementadas; no se debe entregar únicamente una nueva firma como si resolviera también la compatibilidad de hardware.
