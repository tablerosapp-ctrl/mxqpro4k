# Herramienta SD Rockchip recibida: alcance y límites

Revisión estática del 8 de septiembre de 2026. El usuario aportó la carpeta rotulada «Rockchip Create Upgrade Disk Tool v1.53» y mostró el recovery del último RK3229 con Android 7.1.2/NHG47K/CNV8b.20230725 y la opción **Apply update from SD card**. Esta revisión leyó archivos, calculó SHA256, consultó recursos PE y Authenticode y examinó las tres páginas del manual. **No ejecutó el EXE, no creó una tarjeta, no escribió al TV ni publicó binarios.**

La utilidad crea medios de arranque, actualización o reparación a partir de firmware. **No es una herramienta de extracción de los originales del TV.** Para que el recovery ya abierto seleccione un ZIP desde una SD normal, no corresponde ejecutar las funciones Create o Restore de esta utilidad.

## Inventario y procedencia comprobable

La carpeta contiene **26 archivos / 1.912.865.074 bytes**, incluidos dos contenedores de firmware, tres binarios de cargador/arranque, el EXE, dos configuraciones, un PDF, un RAR, dos archivos de idioma y catorce registros históricos. Los registros suman 39.762 B y sus nombres abarcan 2018–2025; su presencia no acredita ejecuciones en esta PC ni en estos TV.

| Archivo recibido | Bytes | SHA256 |
| --- | ---: | --- |
| Rockchip Create Upgrade Disk Tool v1.53.exe | 678.400 | `cded548705e7a069652774e4e51d4839c2431838b85f12da2383733b584fe2cd` |
| config.ini | 1.232 | `92e0b33c81a02631c6de111ad9c92f06dd288d14b35ee91c8562547236bf7853` |
| sd_boot_config.config | 147 | `f8889a9dc3e8fe4f9425d94819cb657173086b73636c1db15569a8a830de8520` |
| sd repair manual Chinese.pdf | 204.884 | `2b5a8d48bbe9070fbc6102d864c689fedbedabb8b180f44255f687b91154a52f` |
| SDBoot.bin | 152.366 | `8b798a7e2efeeedaebad0bd8e22e0790a97c208603a1635d066fa9d34a33ae02` |
| rk32xx_loader_v1.00.232.bin | 151.886 | `f463933c3b914dcd0301298d9166b021c4b7ee6bf99e4edc452c35ac012e5708` |
| rk3399_loader_v1.07.106.bin | 264.526 | `88bf65c192c1f48ae278347c938df98b14305f73fb06787f9428253f1739bdda` |
| SD_Firmware_Tool._v1.46.rar | 444.035 | `8e672e920d8ae3c51fc698f017989938fe2fc07345584c50c585399976d3af6b` |
| 202302151607.img | 1.002.971.608 | `5cea7fd814477c8a7e936aefd99b52d3109cfb573aab0b1cdab9fbad953de618` |
| D-RK3228-ssv6256-CNV8b-11.1-1G8-0725_21.img | 907.946.456 | `8728cf503b79f22000110c41a1d7b1f3b10a975bc15e8256461f6ef72285c89e` |

El EXE es **PE32 x86**, subsistema gráfico Windows. Sus recursos declaran `SD_Firmware_Tool.exe`, empresa `Rockchip` y versiones de archivo/producto `1.5.3.0`. La cabecera COFF declara 21/3/2018; esos campos son editables y no autentican procedencia. Authenticode devolvió **NotSigned**, sin certificado de firmante, y la tabla de certificados PE está vacía. Esto no certifica malware ni ausencia de malware: falta una firma verificable o un hash oficial independiente que autentique esta copia.

Las cabeceras de los dos archivos `.img` comienzan por `RKFW`; las de los tres `.bin`, por `BOOT`; el RAR corresponde al formato RAR5. No se ejecutaron ni desempaquetaron sus cargas. Los nombres que mencionan fechas, CNV8b, RK3228, RK32xx o RK3399 no prueban correspondencia byte por byte con el firmware del equipo. En particular, el nombre comercial o la coincidencia parcial de una compilación no autorizan instalar las imágenes adjuntas.

El conjunto mezcla referencias de versión: carpeta/EXE 1.53, archivo comprimido rotulado 1.46 y captura del manual con interfaz 1.52/SDBoot 2.12. No debe presentarse como una distribución uniforme autenticada de Rockchip 1.53.

## Qué describen la configuración y el manual locales

`config.ini` selecciona inglés y trae **`UPGRADE_FW_MODE=TRUE`**; `PCBA_MODE` y `SDBOOT_MODE` están vacíos. `USE_FW_LOADER=true` lleva un comentario que limita esa opción a proyectos RK3288. No se extrapola a RK3229 ni se alteró la configuración.

El archivo `sd_boot_config.config` contiene `loader_update=0`, `fw_update=0`, `pcba_test=0` y `demo_copy=0`. Esos valores de un archivo auxiliar no convierten el EXE ni todos sus modos en una operación de lectura. La herramienta tiene configuración de interfaz separada y genera contenido para la tarjeta; no se comprobó dinámicamente qué combinación produciría esta copia.

Los textos de idioma anuncian pérdida de datos del disco seleccionado, escritura de MBR, cargador, parámetros y recovery, formateo del volumen y copia de firmware. El EXE contiene cadenas para dispositivos físicos Windows y referencias a formateo; importa `CreateFile`, `WriteFile`, `DeviceIoControl` y `FlushFileBuffers`. Son evidencias estáticas de capacidades y mensajes, no una ejecución observada ni una auditoría completa de todos sus caminos.

El PDF incluido se titula «Guía de uso de tarjeta SD de reparación», versión documental 1.0, fecha 1/2/2018, y se presenta como documentación pública de Rockchip. Se verificaron visualmente sus páginas relevantes. Indica combinar **SD Boot + reparación**, elegir firmware y crear la tarjeta. Su diagrama muestra la dirección **SD → almacenamiento del equipo**, con parámetros, U-Boot y resto del firmware; describe reparación automática y reinicio. Advierte que la tarjeta de reparación no debe usarse como tarjeta de arranque normal. La autoría declarada del PDF no autentica por sí sola el ejecutable ni los archivos que lo acompañan.

## Modos: contraste con fuentes primarias

| Uso | Operación descrita | Relación con obtener originales |
| --- | --- | --- |
| SD normal con un ZIP | El recovery instalado lee un archivo seleccionado por el usuario. | Es la vía que corresponde evaluar para el extractor, sin fabricar una SD de arranque. |
| Upgrade Firmware | Crea una tarjeta especial con firmware; el equipo compatible puede actualizarse automáticamente al arrancar con ella. | Escribe firmware al equipo; no respalda sus originales. |
| SD Boot | Reescribe la disposición de la tarjeta para arrancar y ejecutar el sistema suministrado desde ella. | No equivale a copiar un ZIP; requiere firmware y soporte específicos. No acredita ausencia de escrituras internas de ese sistema. |
| SD Boot + reparación | El manual local describe trasladar firmware de la tarjeta al almacenamiento del aparato. | Sustituye contenido interno; no es recuperación de una copia existente ni extracción. |
| Restore del disco | Los textos locales describen restaurar MBR y formatear el medio. | No restaura el TV ni recupera sus originales; puede perder datos de la tarjeta seleccionada. |

El fabricante de placas Firefly documenta `Upgrade Firmware` como preparación seguida de actualización automática del equipo, y distingue `SD Boot`, que modifica las particiones de la SD y depende del dispositivo/SDK. Son fuentes primarias de sus placas, **no una certificación del RK3229 aquí capturado ni del EXE recibido**. [Actualización mediante SD](https://community.t-firefly.com/en/docs/products/motherboard/ROC-RK3399-PC-PLUS/05-upgrade-firmware-sd), [arranque mediante SD](https://wiki.t-firefly.com/en/iCore-3562JQ/06-boot_firmware_sd.html).

Como referencia de implementación, el código Rockchip Android 7.1 distingue el arranque de fábrica desde SD/USB, lee `sd_boot_config.config` y transforma valores no nulos de `fw_update` en argumentos de actualización. Su ruta de actualización SD invoca funciones de actualización de firmware o particiones. No se ha demostrado que sea el código exacto del recovery de este TV. [Fuente `sdboot.cpp`](https://github.com/rockchip-android/bootable-recovery/blob/rk3399-box-7.1/sdboot.cpp).

## Aplicación a la siguiente etapa

La opción fotografiada **Apply update from SD card** justifica estudiar una SD de datos que transporte el ZIP extractor hasta el recovery ya existente. No exige usar el EXE aportado ni copiar sus imágenes, loaders o configuración de fábrica. La selección del ZIP, su firma, su ejecución y el destino de las copias siguen siendo comprobaciones separadas.

El [extractor 0.1](../../diagnostico/extractor-recovery-0.1/README.md) exige un destino USB físico marcado, ya montado con escritura; no convierte una SD nativa en ese destino ni monta el USB automáticamente. Leer el ZIP desde SD no demuestra que pueda guardar imágenes en ella o que recovery mantenga disponible el Kingston. Esa adaptación o combinación de medios se revisa por separado. No se preparó ninguna tarjeta ni se aplicó firmware en esta revisión.
