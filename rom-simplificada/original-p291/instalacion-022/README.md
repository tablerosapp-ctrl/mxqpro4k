# Instalador P291 0.2.2

Esta variante corrige el aborto de0.2.1 al resolver `system` en sysfs. Conserva las cinco imágenes de la plataforma0.2.0 y el flujo de seis respaldos, preparación de userdata y escritura verificada. No se modifica el ZIP0.2.1 para corregirlo.

ZIP sellado y verificado:573820005bytes, SHA256 `163d4ce6e6fd4e02f06cb6646c53c259d1d3100547ee5c616c578782c3e54421`. [Recibo de firma/payload/validador](salida/TVBASE-P291-A9-0.2.2-VERIFICACION.json), [pruebas](EVIDENCIA-TESTS.json), [revisión independiente](REVISION-LAYOUT-022.json) y [cotejo final de ambas variantes](CIERRE-022.json). El sellado no acredita copiaUSB ni instalación física.

La [fuente Amlogic fijada](https://github.com/khadas/linux/blob/d71236547be9b86d527de0f62c2092ec032fd0fa/drivers/amlogic/mmc/emmc_partitions.c#L1006) asigna el nombre lógico a la partición y el dispositivo del disco como padre. Por eso una partición válida puede terminar en `mmcblk0/system`; exigir exclusivamente `mmcblk0p18` la rechazaba. La foto acredita el aborto concreto, no una avería de la eMMC.

`block_layout.go` acepta el nombre lógico esperado o el convencional únicamente si coinciden rdev de fstat, dev de sysfs, número de partición, tamaño ioctl y tamaño sysfs. Exige una hija directa del mismo disco canónico, cotejado mediante `/sys/class/block/mmcblkN` y `/sys/dev/block/179:0`, tipoMMC y capacidad7.650.410.496bytes. Rechaza USB, SD, mapper, disco entero, boot/rpmb y nombres cruzados.

Los desplazamientos `start` no se capturaron en los respaldos originales. No se inventan: se exige un valor positivo, rango dentro del disco sin desbordamiento ni solapamiento, y se conserva la primera observación. Cada guarda posterior compara la identidad y geometría completas; el recibo del conjunto de respaldos incorpora esos valores como observados, no como datos adquiridos originalmente. Los errores identifican fase, partición y atributo.

`block_device_linux.go` realiza únicamente las lecturas del dispositivo/sysfs para esta guarda. Los atributos ausentes, malformados o redirigidos causan error. El mismo código se usa en el restaurador0.2.2. La revalidación alcanza los cinco destinos, ENV y userdata antes de respaldar, formatear o escribir. Las transacciones incompletas0.2.1 y0.2.2 siguen bloqueando un reintento automático.

Las pruebas de `block_layout_test.go` usan la forma de sysfs documentada por el fabricante y valores ficticios de start con los tamaños reales. No equivalen a una captura de sysfs del TV. La compilación ARM y las pruebasPC tienen su propio recibo; el empaquetador exige `REVISION-LAYOUT-022.json` con todos los hashes de fuentes y el suyo antes de sellar el ZIP. Una revisión anterior no autoriza otra fuente.

La política de datos permanece en [el contrato0.2.1](../instalacion-021/CONTRATO-MIGRACION.md). La variante0.2.2 mantiene respaldo completo previo, fsync y tresSHA, desmontaje normal, formateador original, comprobaciónRO y boot al final. No tiene rollback ni reinicio automático. La aceptación e instalación físicas de este ZIP requieren evidencia propia.
