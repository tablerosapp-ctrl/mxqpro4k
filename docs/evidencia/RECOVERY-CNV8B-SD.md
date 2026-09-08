# Recovery CNV8b: firma Rockchip y carga desde SD

Revisión del 8/9/2026. El firmware aportado identifica la compilación `CNV8b.20230725`, coincidente con el informe del RK3229-C y la pantalla comunicada por el usuario. Se examinó su recovery extraído en PC. **No se leyó ni calculó el hash de la partición recovery del TV:** la coincidencia de compilación no acredita igualdad binaria con el ejemplar instalado.

El ejecutable examinado exige una clave distinta de la usada en el extractor 0.1 y contiene una ruta fija para la instalación desde SD. Hay una pareja pública de desarrollo Rockchip que coincide con esa clave. Esto permite preparar una variante de firma y de entrega, conservando el ejecutable extractor, sin atribuir todavía aceptación física ni una captura realizada.

## Archivos examinados y método

| Archivo del firmware | Bytes | SHA256 |
| --- | ---: | --- |
| `sbin/recovery` | 1.004.880 | `75486016cfdb1b8c8b8cab53fc09b493e889148ae398b6885d80d548b7dfe142` |
| `res/keys` | 1.400 | `96a7556cb8f2f377a318def54bfb732a125fead794ad86fbcc9937b8718a36ca` |
| `etc/recovery.fstab` | 2.277 | `e961b0e1e4f44fbadef8aba872ea27d86dc40a422143680a3798c9ed27022a6c` |

Se analizaron estructura ELF, cadenas, referencias relativas al PC y llamadas Thumb. Para desensamblar se utilizó la biblioteca LLVM incluida en las herramientas Android locales, desde un proceso de análisis de 32 bits; **no se ejecutó el ELF del firmware**. El binario carece de tabla de símbolos de funciones, por lo que los nombres de funciones indicados debajo describen su comportamiento y su correspondencia con el código fuente de referencia.

Las direcciones de la tabla siguiente son virtuales del ELF. En esta sección `.text`, el offset de archivo es la dirección virtual menos `0x8000`; no son offsets de particiones ni direcciones para escribir al TV.

## La firma 0.1 original no corresponde a este recovery

`res/keys` declara una clave `v3`, RSA de 2048 bits y exponente 3. Su representación de 64 palabras, `n0inv` y `RR` se verificó matemáticamente. En el [verificador AOSP 7.1.2](https://android.googlesource.com/platform/bootable/recovery/+/android-7.1.2_r8/verifier.cpp#512), v3 selecciona RSA, exponente 3 y SHA256.

El certificado usado por el [extractor 0.1 original](../../diagnostico/extractor-recovery-0.1/COMPILACION.json) tiene DER SHA256 `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc`. Su módulo RSA es diferente y su paquete usa SHA1. **Cambiar sólo SHA1 por SHA256 con aquella clave no resuelve la incompatibilidad.**

Se compararon los certificados públicos testkey, platform, media y shared de AOSP 7.1.2 y Rockchip Android 7.1. Sólo coincide exactamente, en módulo y exponente, el [certificado testkey Rockchip](https://github.com/rockchip-android/build/blob/c8a3e0a0958efd0b96a6d26fe2a15921bc0fb97d/target/product/security/testkey.x509.pem), fijado al commit `c8a3e0a0958efd0b96a6d26fe2a15921bc0fb97d` de `rockchip-android/build`, rama consultada `rk3399-box-7.1`.

| Identificador público comprobado | SHA256 |
| --- | --- |
| Certificado Rockchip, archivo PEM de 1.440 B | `10a7b524d14750a12b44472524340df6b300f1b648fb63c3b17a161bde1e08d7` |
| Certificado Rockchip, representación DER | `cf2ab3818595c4eda08cec72bbe39bc377a30b764a3eebde52536eae01808525` |
| Módulo RSA de recovery/certificado, entero big-endian de 256 B | `e4bb357ac62c64f73383cd8fe62b9dabed4cf9ceb710ae437495a948bddffd8b` |

La pareja de desarrollo correspondiente se conservó exclusivamente en el área privada del proyecto, con creación exclusiva, fsync y relectura. Dos comprobaciones locales verificaron que sus números públicos N/e coinciden con el certificado y `res/keys`. El recibo privado de adquisición tiene SHA256 `6aa2e6ce9aa5dbac5d839eb93097ac9d5a82d55052b688fad840a1ec2ef51b1d`. Aquí no se reproduce material de clave ni propiedades crudas. Una clave de desarrollo compartida sirve para esta compatibilidad heredada; no constituye una raíz de confianza de producción.

## Ruta fija de SD y conservación del USB

| Evidencia directa del ELF | Dirección virtual / offset de archivo | Interpretación |
| --- | --- | --- |
| Carga de la cadena `/mnt/external_sd/update.zip` en r0 | `0xf61c` y suma de PC en `0xf628` / `0x761c`, `0x7628` | La llamada de instalación usa esa ruta fija. |
| Llamada con ruta, puntero de wipe-cache, `/tmp/last_install`, montaje no solicitado y retry cero | `0xf62e` → `0x8f48` / `0x762e` → `0x0f48` | Corresponde al instalador de paquetes; no recibe aquí la ruta elegida en el navegador. |
| Rutina de preparación de montajes | `0x12184` / `0xa184` | Monta `/tmp` y `/cache`; exceptúa `/mnt/external_sd`, `/mnt/usb_storage` y `/backup` del desmontaje general. |
| Llamada al montaje USB desde el inicio | `0xe10a` → `0xc19c` / `0x610a` → `0x419c` | Se ejecuta bajo la condición observada `argc <= 1`. |
| Intentos de montaje VFAT y NTFS | `0xc388`, `0xc3aa` / `0x4388`, `0x43aa` | Recorre nodos `sd*` de `/dev/block` y monta en `/mnt/usb_storage`. |

Los intentos USB usan flags decimales 3076 (`MS_NOATIME | MS_NODEV | MS_NODIRATIME`), sin `MS_RDONLY`. La rutina reintenta hasta diez veces, esperando un segundo entre fallos. Esto acredita que **el firmware examinado intenta montar USB para escritura al inicio**, no que un pendrive concreto haya quedado montado o sano. Insertarlo después de estar en el menú no acredita una nueva ejecución de ese intento.

También se comprobó en el ELF la búsqueda automática inicial de `/mnt/usb_storage/update.zip` y `/mnt/usb_storage/update.img`. Por ello, la futura entrega debe verificar la ausencia de esos nombres genéricos en la raíz del Kingston. Si ya existen, se conservan y se revisan antes de continuar; no se eliminan ni sustituyen automáticamente. La copia genérica `update.zip` necesaria para esta ruta fija corresponde **sólo a la SD**, y debe tener el mismo SHA que el paquete RK1 revisado en PC.

El [código público Rockchip 7.1](https://github.com/rockchip-android/bootable-recovery/blob/rk3399-box-7.1/recovery.cpp) contiene las mismas decisiones de ruta fija y búsqueda USB; [roots.cpp](https://github.com/rockchip-android/bootable-recovery/blob/rk3399-box-7.1/roots.cpp) contiene las excepciones de montaje. Es corroboración del análisis del ELF adquirido, no prueba independiente del firmware instalado en C.

## Consecuencia para la entrega y límites

La ruta concreta viable para este firmware es **cargar el extractor desde la SD y guardar las copias nuevas en el Kingston**, con ambos medios disponibles antes de entrar al recovery. La SD de 8 GB sirve como medio de carga; no se presenta como destino suficiente para respaldar la eMMC de C. El extractor 0.1 continúa exigiendo USB físico marcado, montaje RW, plan C y validación independiente de orígenes. No necesita convertirse en un escritor de imágenes sobre SD para esta ruta.

El paquete `TVBASE-EXTRACTOR-0.1-RK1-ARM32-RECOVERY.zip` requiere un recibo nuevo que compruebe firma integral RSA/SHA256 con la clave Rockchip y la identidad exacta del ejecutable con el ARM32 sellado de 0.1. Este documento no sustituye ese recibo, no modifica el release original y no acredita por sí solo que la variante ya esté construida o entregada.

Una firma que verifica en PC con la clave extraída acredita compatibilidad criptográfica con **ese archivo de claves**. Todavía faltan la aceptación del recovery físico, el montaje real de Kingston, la ejecución del extractor y la relectura de las copias. La copia puede omitir particiones montadas RW y no incluye RPMB ni todos los chips. El recovery anfitrión conserva sus propias acciones sobre registros/metadatos; no se afirma cero escrituras de todo el entorno. No se ha flasheado ni ejecutado el firmware aportado durante este análisis.
