# Particiones nominales Amlogic del primer P291 · corrección 0.2.2

El intento físico con el ZIP 0.2.1 alcanzó su instalador en recovery y mostró `ERROR: destino no eMMC particionada: system`. La guarda de [block()](../../rom-simplificada/original-p291/instalacion-021/main_linux.go) exigía que el nombre final de sysfs tuviera la forma `mmcblkNpN`. El error se produce durante `prepareTargets`, antes de alcanzar respaldo, formato de userdata o escritura de imágenes por ese instalador. No demuestra una instalación ni una falla de la eMMC.

## Observado en el equipo

La captura local `diagnostico/primer-tv-lan-20260907-184926/privado/root-particiones.txt`, SHA256 `4f6eac3259635edb6eaeacad3483653c6ed67c13f36fd5cbd8b956f7b5a35a14`, conserva dos representaciones del mismo dispositivo: `/dev/block/system` tiene `179:18`, mientras `/proc/partitions` muestra `mmcblk0p18` con ese mismo número. `/dev/block/by-name` estaba ausente. El archivo crudo permanece privado.

| Nombre lógico | major:minor | Número indicado por `/proc/partitions` | Tamaño en bytes |
| --- | --- | --- | --- |
| system | 179:18 | 18 | 1342177280 |
| vendor | 179:16 | 16 | 943718400 |
| odm | 179:17 | 17 | 134217728 |
| product | 179:19 | 19 | 134217728 |
| boot | 179:11 | 11 | 16777216 |
| env | 179:4 | 4 | 8388608 |
| data | 179:20 | 20 | 3495952384 |

El disco observado es `mmcblk0`, `179:0`, con 7471104 KiB: **7650410496 bytes, equivalentes a 14942208 sectores de 512 bytes**. Los tamaños de la tabla proceden de los bloques de 1024 bytes de `/proc/partitions`; no son offsets de inicio.

## Explicación por fuente primaria

Referencia fija: repositorio Khadas Linux, commit `d71236547be9b86d527de0f62c2092ec032fd0fa`, rama consultada `khadas-vims-pie`. Es fuente de referencia; no se acredita identidad completa con el kernel compilado del TV.

- [emmc_partitions.c, líneas 1006–1083](https://github.com/khadas/linux/blob/d71236547be9b86d527de0f62c2092ec032fd0fa/drivers/amlogic/mmc/emmc_partitions.c#L1006): `add_emmc_each_part` conserva inicio, tamaño y número; asigna `pname` al dispositivo, mantiene `part_type` y fija como padre directo `disk_to_dev(disk)`. Por tanto, una partición llamada `system` puede ser hija real de `mmcblk0`, con estructura `…/block/mmcblk0/system`.
- [partition-generic.c, líneas 68–88](https://github.com/khadas/linux/blob/d71236547be9b86d527de0f62c2092ec032fd0fa/block/partition-generic.c#L68) y [171–203](https://github.com/khadas/linux/blob/d71236547be9b86d527de0f62c2092ec032fd0fa/block/partition-generic.c#L171): los atributos de partición exponen `partition`, `start` y `size`; los dos últimos corresponden a sectores.
- [genhd.c, líneas 887–893](https://github.com/khadas/linux/blob/d71236547be9b86d527de0f62c2092ec032fd0fa/block/genhd.c#L887): `/proc/partitions` imprime mediante `disk_name(disk, partno)`. Esto explica que allí figure el nombre tradicional aunque sysfs use el lógico.

SHA256 de las fuentes leídas, en el mismo orden: `e43bec994e36ae5f0d0e708ecee512b3ebd96f92e682998e621be15cc6c56395`, `91a5a133df79cd88930e01ecf56f766158e815ddcb9236ec4d9602cc70683186` y `0816cab8a42afe709ec21c0c5b6f1ca06fc47cce15fce3bc674b0a4bb4f5973b`.

## Contrato para verificar durante 0.2.2

La corrección debe identificar el bloque por su descriptor, `rdev`, tamaño y topología; aceptar solamente el nombre lógico esperado o su variante tradicional. El padre directo debe coincidir canónicamente con `/sys/dev/block/179:0` y `/sys/class/block/mmcblk0`, acreditar tipo `MMC` y tamaño del perfil. Cada destino debe conservar `dev`, número de partición y tamaño exactos, con intervalo válido dentro del padre, sin desbordamiento ni solapamientos. Se mantienen destinos únicos, padre común, rechazo de USB/SD/disco completo/boot/RPMB/mapper, ausencia de montajes y revalidación antes de escribir.

**Todavía no se capturaron en recovery los enlaces sysfs completos ni los atributos `start`, `partition`, `dev`, `size` y tipo del padre.** La foto confirma únicamente el basename `system`. Los inicios no deben inventarse: el preflight debe leerlos, registrarlos y comprobar su estabilidad antes de cualquier escritura. Una identidad incompleta o incoherente debe detener la instalación, conservando el informe. Este documento no acredita que 0.2.2 haya superado esas comprobaciones ni que la ROM esté instalada.
