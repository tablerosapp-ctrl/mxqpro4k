# RK3229: dos variantes observadas y una exportación pendiente

Revisión local del 8 de septiembre de 2026. Se verificaron cinco ZIP adquiridos: el [P271 ya conservado](../reconocimiento-20260908-p271-mx9/HALLAZGOS.md) y cuatro ZIP nuevos del reconocedor 0.2. Estos cuatro son **dos fichas iniciales y sus dos inventarios posteriores**, con los enlaces entre capturas comprobados. No representan cuatro equipos. Los identificadores de instalación de la APK tampoco certifican identidad física.

La verificación estricta comprobó estructura, tamaños, CRC y los 2467 hashes de archivos declarados en los cinco manifiestos; los resultados coinciden con el catálogo. Los originales permanecen privados. Esta revisión no contactó equipos ni modificó el pendrive, firmware o recibos anteriores.

## Comparación de las capturas RK3229

Se usan las etiquetas locales **RK3229-A** y **RK3229-B** para distinguir las dos variantes de firmware y almacenamiento observadas. A declara el nombre eMMC `QNW00M`; B declara `008GB0`. Son nombres informados por el sistema, no una identificación independiente del chip ni un conteo certificado de aparatos.

| Evidencia | RK3229-A | RK3229-B |
| --- | --- | --- |
| DT observado | `rockchip,rk3229` | `rockchip,rk3229` |
| Modelo declarado | TVBOX | TV BOX-3 |
| API y fingerprint | API 25; fingerprint con Android 7.1.2 | API 25; fingerprint con Android 7.1.2 |
| Etiqueta de versión declarada | 11.1 | 13.0 |
| ABI Android | ARM32: armeabi-v7a y armeabi | ARM32: armeabi-v7a y armeabi |
| CPU declarada por el kernel | Cuatro entradas ARMv7; parte 0xc07 | Igual |
| Kernel Android | 3.10.104; compilación de febrero de 2023 | 3.10.104; compilación de julio de 2025 |
| RAM declarada por Android y procfs | 1.046.405.120 B | 549.755.813.888 B: **512 GiB anómalos** |
| eMMC: nombre declarado | QNW00M | 008GB0 |
| eMMC: área de usuario expuesta | 7.818.182.656 B | 7.818.182.656 B |
| Partición p13: tamaño bruto | 2.147.483.648 B | 3.221.225.472 B |
| Partición p14: tamaño bruto | 5.339.348.992 B | 4.273.995.776 B |
| Sistema de archivos de datos: capacidad declarada | 5.171.970.048 B | 4.140.040.192 B |
| Módulo WiFi cargado | ssv6158 | ssv6x5x |
| Driver enlazado al dispositivo SDIO | SSV6XXX_SDIO | SSV6XXX_SDIO |
| Paquete Google WebView | 69.0.3497.100, habilitado | 74.0.3729.157, deshabilitado |
| Paquete Chrome | 66.0.3359.158, habilitado | 86.0.4240.185, habilitado |
| Paquetes visibles para la APK | 69 | 88 |
| Códecs anunciados por Android | 33 | 28 |
| Pantalla declarada | 1280 × 720, 60 Hz | 1280 × 720, 60 Hz |

Las etiquetas 11.1 y 13.0 son incompatibles con API 25 y los fingerprints que declaran 7.1.2. **No acreditan Android 11 ni Android 13.** Tampoco se certifican las fechas de parches o compilación declaradas por ese firmware. En B, tanto la API de memoria como procfs informan 512 GiB: no es una segunda medición independiente que confirme esa capacidad. La RAM física queda indeterminada. En A se observa aproximadamente 998 MiB de RAM visible para el sistema, sin identificar físicamente los chips.

Ambos inventarios declaran MMC no removible y catorce particiones del área de usuario. Se conservaron los tamaños observados de p13 y p14 **sin asignarles aliases de sistema o datos**: estas capturas no aportan sus inicios ni la correspondencia completa entre aliases y dispositivos. La capacidad del sistema de archivos no equivale al tamaño bruto de una partición. La enumeración de bloques tiene tres entradas omitidas por límite; no permite afirmar presencia o ausencia de otras áreas a partir de lo no recorrido.

Los nombres de módulos y el enlace SDIO acreditan configuración de software observada, no asociación WiFi, tráfico, estabilidad ni identificación independiente del chip de radio. También se observó un dispositivo USB con driver `usb-storage`. Los recorridos adicionales de buses quedaron excluidos del inventario rápido.

## WebView y video: declaraciones, no pruebas de ejecución

El reconocedor 0.2 no instanció WebView. Su consulta del proveedor seleccionado quedó como API no disponible; por ello, los paquetes y estados de habilitación de la tabla **no identifican el proveedor efectivamente usado por la APK del usuario**.

Ambas listas anuncian decodificadores VP9 y HEVC con nombres Rockchip y otros con nombres Google. Los rangos declarados de los decodificadores Rockchip incluyen máximos de ancho 4096 y alto 2160; esos límites independientes no prueban reproducción conjunta a una resolución y frecuencia determinadas. A añade cinco entradas con sufijo `secure`, incluida VP9, ausentes en la lista B. Ni esos nombres ni sus capacidades anunciadas demuestran aceleración física, seguridad de reproducción o funcionamiento.

No se ensayaron decodificación, VP9 con alfa, canvas, videos simultáneos ni rendimiento. Tampoco se inicializó EGL para medir el renderer gráfico. Los datos de pantalla y las declaraciones gráficas del firmware no sustituyen esas pruebas.

## Estado real y límites de la captura

Las fichas iniciales tienen estado `basic_checkpoint`; los inventarios asociados, `inventory_with_explicit_limits`. Estos últimos tardaron 1702 ms en A y 1499 ms en B, y terminaron con observaciones y sin lector pendiente declarado.

Los cuatro ZIP RK suman **84.222 B**. Cada uno contiene únicamente el informe y su manifiesto. El tamaño reducido corresponde al [diseño del reconocedor 0.2](../reconocedor-0.2/README.md): no copia binarios de drivers ni recorre profundamente el árbol DT. No son respaldos de ROM ni capturas de particiones.

Cada inventario alcanzó el techo de 160 intentos de lectura de metadatos: 128 observaciones, 32 fuentes no disponibles por ENOENT, una omisión general de límite y cinco exclusiones explícitas. Se registraron 6866 B de texto en A y 6988 B en B, sin timeouts de esa sección. Las ausencias ENOENT no son denegaciones de permisos, y lo omitido por límite no demuestra ausencia de hardware.

Los tres comandos auxiliares conservan estado `partial`, código de salida desconocido y la indicación de que el proceso podría continuar. Tener texto de salida y un inventario terminado no permite convertir esos estados en códigos de éxito. La captura se realizó con privilegios de APK normal, sin root, ADB ni solicitudes de red.

## Equipo pendiente y exportación USB

El usuario identifica el tercer equipo cuyo intento de exportación falló como Rockchip y aclara que no es P291 ni P271. Informa también que las carcasas comparten la denominación comercial «MXQ Pro 4K 5G». Se conserva esa identificación como declaración del usuario: **no hay informe ni DT exacto de ese tercer equipo**, y el nombre de la carcasa no permite asignarle ninguna de las dos variantes anteriores.

Las dos capturas recibidas muestran un volumen USB FAT32 montado y una vista de almacenamiento accesible desde Android. No contienen resultados de enumeración de StorageManager ni una comprobación de permisos de escritura directa que permita explicar el fallo `automatic null` del tercer equipo. Un montaje RW no acredita por sí solo acceso de escritura para una APK normal.

El reconocedor **0.3 ya está entregado**, con selector propio y alternativa manual para la exportación de ese equipo. Su [recibo de entrega](../../preparacion-usb/reconocimiento-03-estado.json) acredita copia y relectura en PC; la exportación física desde ese TV sigue pendiente. Tampoco atribuye el fallo a un permiso, proveedor o ruta concreta sin evidencia de ese aparato.

## Alcance para un plan de extracción desde recovery

La MMC no removible declarada por ambos RK permite considerarlos candidatos al [adaptador eMMC del extractor](../extractor-recovery-0.1/README.md). No se observó NAND como almacenamiento principal en estas fichas; tampoco se demostró que no existan otros chips. El adaptador actual no respalda MTD/NAND: esa tecnología requiere tratamiento propio de geometría, ECC y OOB.

La ABI Android orienta hacia ARM32, pero no demuestra la ABI, el kernel ni la ejecución del recovery instalado. Permanecen sin acreditar entrada, confianza de firma, ejecución del extractor y lectura física de bloques en estos RK. Recovery deberá comprobar nuevamente topología, tamaños por ioctl, inicios, montajes, consumidores y estabilidad. El Android capturado tenía datos, caché y metadatos montados RW; no aporta una instantánea estable de todos sus bloques.

**Ambas variantes comparten exactamente el mismo DT. Dos planes coincidentes simultáneos harían abortar el extractor.** Debe mantenerse seleccionado un solo plan para ese DT cuando corresponda preparar su uso, conservando por separado la captura que lo origina. La coincidencia DT vincula un perfil declarado; no certifica identidad física ni hace intercambiables sus ROM. Las diferencias de firmware, memoria, particiones, radio y códecs impiden aprobar esa equivalencia a partir de estos informes.

Esta revisión conserva insumos privados para esa evaluación; no creó ni cargó planes operativos. Las limitaciones de confianza y ejecución explicadas para [P271](../../docs/evidencia/RECOVERY-P271-ALCANCE.md) tampoco quedan resueltas para Rockchip por compartir formato ZIP, API o firma de aplicaciones Android.
