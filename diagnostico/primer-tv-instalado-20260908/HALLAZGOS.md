# Primer P291 · instalación 0.2.2 completada

La revisión independiente del 8/9/2026 confirma el cierre del instalador 0.2.2: seis respaldos íntegros conservados en PC, formato de userdata terminado, comprobación de contenido vacío y cinco imágenes de plataforma 0.2.0 escritas y releídas, con boot al final. La fotografía muestra el inicio **TV Base**. El usuario informa que volvió a conectar el WiFi y que el botón HOME no regresa al inicio; esos resultados se mantienen separados de la evidencia del instalador.

El usuario pidió estudiar y documentar antes de ejecutar próximos pasos. Esta revisión no contactó el TV, no leyó ni escribió el pendrive, no restauró imágenes y no cambió aplicaciones, configuración ni fuentes del instalador.

## Evidencia conservada y verificación independiente

La adquisición USB→PC terminó `verified`, código 0, a las 12:46:58 ART. Su recibo declara 199 archivos y 6.091.261.673 bytes; SHA256 del recibo: `9cda3bb9690d288ffeb8dc6da2872e7732973bf8791d7e0c397ccf08875bb525`.

El [verificador independiente](verificar-adquisicion.py) leyó nuevamente **13 archivos locales**: seis imágenes de respaldo, cinco JSON de etapas, el log de instalación y la fotografía. Comprobó tipo regular, tamaño físico y SHA contra el recibo de adquisición, las tres sumas de cada respaldo declaradas por el TV y el manifiesto sellado 0.2.2. No volvió a leer los demás archivos históricos de la adquisición. Un caso válido y 15 alteraciones de metadatos rechazadas comprueban el parser, únicamente en PC.

El resultado reproducible y los SHA completos están en [resumen-saneado.json](resumen-saneado.json). Los registros originales, la fotografía y las imágenes permanecen privados. No se modificaron los recibos sellados de entrega, construcción ni preparación 0.9.

## Respaldo y cierre de etapas

Los seis respaldos suman **6.067.060.736 bytes**. System, vendor, product, odm y boot coinciden también con los cinco originales P291 usados para construir la plataforma. El nuevo respaldo de userdata tiene **3.495.952.384 bytes**, SHA256 `b58c363f8712254b8da01376db4408237d2af52d0ea7e79f1b8a375e31616b88`. Su copia PC coincide con copia inicial, relectura USB y relectura posterior del origen declaradas por el instalador. Esto acredita una copia íntegra, no una restauración ensayada.

| Registro persistido | Resultado comprobado |
| --- | --- |
| `00-backup-verified.json` | `backup_verified`; paquete 0.2.2, perfil P291 y seis registros `verified`, con tamaños y tres SHA coincidentes. |
| `10-format-started.json` | Inicio de formato para userdata 179:20; partición de 3.495.952.384 bytes y filesystem de 3.495.936.000 bytes. Por sí solo no acredita terminación. |
| `11-format-result.json` | Formateador `exit=0`, sin timeout ni salida truncada; 853.500 bloques de 4 KiB. |
| `20-userdata-prepared.json` | Footer de 16 KiB limpio y releído; montaje RO vacío verificado y desmontado. |
| `instalacion.log` | Cinco pares exactos `INICIO`/`VERIFICADO`: system, vendor, product, odm, boot. Los cinco SHA son los de plataforma 0.2.0. |
| `90-installed-verified.json` | `installed_verified`, `package_id=TVBASE-P291-A9-0.2.2`, `platform_version=0.2.0`. |

En las [fuentes selladas 0.2.2](../../rom-simplificada/original-p291/instalacion-022/CONTRATO-MIGRACION.md), el recibo final solo se emite tras sincronizar y releer las cinco particiones y cerrar el log sin errores. Cada JSON exige escritura, sincronización de archivo/directorio y relectura. La adquisición posterior y esta relectura PC acreditan que los respaldos y recibos llegaron persistidos.

Los recibos y el log no están firmados: sus hashes preservan la evidencia recibida, sin convertirla en una atestación criptográfica del TV. El instalador registra el identificador del paquete y los cinco hashes de imágenes; **no registra el hash integral del ZIP ejecutado ni del recovery ejecutado**. El [release 0.2.2](../../rom-simplificada/original-p291/instalacion-022/salida/TVBASE-P291-A9-0.2.2-VERIFICACION.json) permanece como evidencia independiente del paquete preparado en PC. Tampoco se efectuó una nueva lectura de particiones después del arranque.

## Geometría ahora observada en recovery

El recibo 00 contiene por primera vez los inicios y las rutas completas de las siete particiones verificadas por este instalador. Todas terminan con el nombre lógico Amlogic y comparten el padre eMMC `mmcblk0`, dispositivo 179:0 y tamaño 7.650.410.496 bytes. Los rangos están dentro del disco y no se superponen.

| Partición | Dispositivo | Inicio, sectores de 512 B | Longitud, sectores de 512 B |
| --- | --- | ---: | ---: |
| env | 179:4 | 2.531.328 | 16.384 |
| boot | 179:11 | 2.809.856 | 32.768 |
| vendor | 179:16 | 3.059.712 | 1.843.200 |
| odm | 179:17 | 4.919.296 | 262.144 |
| system | 179:18 | 5.197.824 | 2.621.440 |
| product | 179:19 | 7.835.648 | 262.144 |
| data | 179:20 | 8.114.176 | 6.828.032 |

Estos valores pertenecen a esta ejecución real, no a una captura anterior ni a los casos sintéticos del validador. ENV integra la comprobación de geometría, pero no los seis nuevos archivos de respaldo. El recibo serializa la observación inicial; la estabilidad de las comprobaciones posteriores se deduce del cierre del código sellado. El texto crudo `device/type=MMC` no es un campo serializado del recibo, aunque el instalador exige ese valor antes de continuar.

## Reloj e intervalos

El reloj del TV marca **1/1/2020**, por lo que no se usa como fecha real. El recibo de respaldo declara 01:11:00 UTC; los inicios de escritura declaran:

| Imagen | Hora del reloj del TV | Diferencia hasta el siguiente inicio |
| --- | --- | ---: |
| system | 01:24:54 | 421 s |
| vendor | 01:31:55 | 414 s |
| product | 01:38:49 | 74 s |
| odm | 01:40:03 | 73 s |
| boot | 01:41:16 | No disponible |

Entre el recibo 00 y el primer inicio transcurren 834 segundos del reloj declarado. Ese intervalo incluye nuevas comprobaciones, formato y preparación; no es la duración del formateador. El log no fecha cada `VERIFICADO`, y los recibos 10/11/20/90 carecen de timestamp. No se conoce la duración exacta del respaldo completo, de cada escritura o de la instalación total. No se infiere a partir de fechas FAT.

## Observaciones de uso y pendientes

La foto de 271.722 bytes, SHA256 `bab991620b84b3b574c994daa8ea8a23a7e5fde603e7b17e758cc9fbb5eac6bd`, muestra el launcher **TV Base**, sus accesos y Chrome listado. No muestra la versión del motor ni prueba que sea el proveedor WebView activo.

- **WiFi:** el usuario informa reconexión. No se midieron Internet, estabilidad, velocidad ni causa de la recuperación.
- **ISSUE-HOME-01:** el usuario informa que HOME no regresa al inicio. Se registra abierto, sin adjudicar todavía la causa al mando, launcher o framework y sin aplicar cambios.
- **Multimedia/APK:** sin prueba acreditada del proveedor WebView, dos VP9/alfa/canvas ni rendimiento. Las pruebas que haga el usuario tendrán evidencia propia.
- **Recuperación:** siguen sin probarse arranque en frío sin USB, reentrada al recovery desde el Android simplificado, restaurador de cinco imágenes y restauración de userdata. Conservar seis imágenes no demuestra que esos recorridos funcionen.

No se propone ni ejecuta aquí una nueva prueba: los siguientes cambios o verificaciones del producto quedan sujetos al OK solicitado por el usuario.
