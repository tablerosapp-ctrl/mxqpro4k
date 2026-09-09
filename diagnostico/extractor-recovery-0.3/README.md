# Extractor 0.3: originales del Rockchip C y backup al final

Versión separada de [0.2](../extractor-recovery-0.2/README.md), dirigida únicamente a la unidad RK3229-C cuyo recovery ya produjo el inventario físico. La captura anterior acreditó copia y relectura de `parameter` y una discrepancia entre dos lecturas de `backup` (`mmcblk0p10`, 64 MiB). Esa discrepancia no identifica al escritor ni demuestra por sí sola un defecto de eMMC o SD. Los archivos y recibos anteriores se conservan; no se convierten en un respaldo completo.

El usuario pidió conservar el avance del resto del equipo e intentar también esa zona con una variante. Esta versión **difiere backup hasta el final**, conserva las comprobaciones y cambia únicamente el orden de sus lecturas. Si vuelve a fallar, los orígenes anteriores que hayan superado sus comprobaciones siguen identificados como verificados en el informe parcial.

## Identidad y mapa específicos

[source_policy.go](source_policy.go) contiene la política `rk3229-c-backup-last-1`. Antes de seleccionar y durante cada revalidación exige:

- DT `rockchip,rk3229` y SHA del CID eMMC igual al adquirido en esa unidad. El valor se incorpora durante la construcción privada mediante `main.rk3229CExpectedCID`; una compilación sin esa vinculación se detiene. La fuente pública no contiene ese identificador.
- Un padre `mmcblk0` de 7.818.182.656 B y exactamente las quince particiones del inventario de **recovery**: `parameter` es p1, `backup` p10, `system` p14 y `userdata` p15. No se reutiliza la numeración observada en Android.
- Nombres, rutas de dispositivo, major:minor, padre sysfs, comienzos, tamaños y conjuntos exactos de aliases. Un alias faltante, adicional, duplicado o cambiado detiene la selección; no se interpreta por parecido.
- Ningún segundo disco eMMC o área adicional no incluida en el mapa aprobado. Si aparece otra topología se requiere una revisión nueva.

La vinculación CID limita esta excepción a la unidad observada; no autentica un kernel hostil. Compartir carcasa o DT no habilita A/B, P271 ni otro TV. Las pruebas Linux de identidad/ioctl siguen siendo las del adaptador; los tests Windows no las sustituyen.

## Orden y alcance

La selección trabaja por particiones y prohíbe siempre la lectura de toda el área de usuario eMMC, incluso cuando cache esté RO. Así `backup` no puede quedar incluida indirectamente dentro de una copia del disco completo.

Se conservan las guardas de montajes RW, superblock RO, holders y padre en uso. Ninguna partición se desmonta, remonta o modifica para hacerla elegible. Entre las elegibles, las particiones siguen el orden físico de inicio y `backup` queda última. `uboot`, `resource`, `kernel`, `boot`, `recovery`, `system` y `userdata` se intentan antes. Si cualquier origen anterior falla, el motor sigue deteniéndose y backup queda sin intentar; no existe una opción general de continuar ignorando errores.

Con cache RW como en la captura anterior se seleccionan catorce particiones que suman **7.679.770.624 B**, incluido backup. Más la reserva de 128 MiB requieren **7.813.988.352 B**. Con cache elegible son quince particiones/7.813.988.352 B, más la reserva: 7.948.206.080 B. La decisión final usa el espacio real al ejecutar, después de crear el inventario. No se eliminan capturas antiguas para obtener espacio ni se empieza a copiar si no alcanza.

El destino sigue siendo la SD preparada de 8.053.063.680 B y su montaje `/mnt/external_sd`, con el mismo marcador y plan de 0.2. Las comprobaciones de identidad, separación eMMC/SD, paquete en la misma tarjeta, escritura exclusiva, sincronización y relectura permanecen. No se necesitan USB ni red. No se instala una ROM ni se escribe una partición interna; recovery puede escribir sus registros por su cuenta.

## Variante acotada para backup

[buffered_backup.go](buffered_backup.go) se habilita únicamente para el `backup` exacto de 64 MiB y al final de la lista. No es un modo genérico para imágenes grandes.

1. Comprueba presupuesto de memoria antes de reservar un buffer de 64 MiB: exige otros 64 MiB de margen. Usa `MemAvailable` si el kernel lo expone. En Linux 3.10, si falta, admite una estimación conservadora `MemFree + Buffers + Cached - Shmem - Dirty - Writeback`, con campos completos en kB, aritmética comprobada y al menos 512 MiB de MemTotal. Descuenta hasta cero y rechaza valores incoherentes. Es una estimación, no una garantía contra agotamiento de memoria.
2. Abre el origen O_RDONLY validando identidad/tamaño y lo lee completo a RAM, calculando SHA. Cierra, revalida y vuelve a abrir el origen para una segunda lectura y SHA. **No escribe datos del backup en SD entre ambas lecturas.**
3. Si los SHA difieren, no crea la parte de backup en SD. Conserva ambos valores, el error y las fuentes anteriores en `failed-report.json`. No considera válida una lectura cambiante.
4. Si coinciden, escribe el buffer en una parte exclusiva de 64 MiB, sincroniza archivo, cierra y relee el archivo desde SD. Su SHA debe coincidir con las dos lecturas del origen; luego revalida y sincroniza el directorio.

Estas son dos aperturas y lecturas consecutivas del origen; se usa acceso normal del kernel, **sin O_DIRECT**. Pueden intervenir sus cachés. La hipótesis de trabajo es reducir el intervalo entre lecturas y evitar alternar escritura SD y lectura eMMC; no se presenta como causa demostrada ni como snapshot atómico.

El resto de las fuentes conserva el cuerpo de `captureOne`: copia/SHA → sincronización y relectura del destino → reapertura/relectura del origen. Mantiene partes de hasta 1 GiB, buffer de 256 KiB y tres SHA concordantes. Un error de lectura, sincronización, identidad o SHA en cualquier fuente sigue deteniendo el motor. La nueva rama no cambia el criterio de aceptación del resto.

## Informes y pruebas

`inventario.json` añade `source_policy`: ID, `expected_identity_bound=true`, `deferred_source=mmcblk0p10`, motivo de la discrepancia observada y `whole_user_area_allowed=false`. Ese objeto no contiene el CID compilado. El inventario de evidencia sí conserva hashes de identidad y se guarda en privado.

El formato de informe mantiene `tvbase-recovery-capture-0.1` con el campo opcional `verification_order=source_source_destination` solo cuando comenzó la variante RAM de backup. `sha256` y `reread_sha256` corresponden a las dos lecturas del origen; `Parts[].sha256` y estado reflejan copia/sincronización/relectura de SD. Si la captura se detuvo antes de backup, no aparece ese campo en la fila omitida.

Los `.img.partial` conservan sus nombres. `failed-report.json` y `resultado-error.json` prevalecen sobre un resultado favorable; una fuente anterior puede estar verificada aunque la captura total sea parcial. El [verificador PC 0.3](verificar-captura.py) valida explícitamente estos contratos. No ejecuta los dispositivos o rutas del JSON ni interpreta userdata.

Los tests usan archivos ordinarios y el mapa de recovery como fixture sin CID privado: selección exacta, aliases ambiguos, identidad ausente, whole prohibida con cache RO, montajes/holders, backup al final, presupuesto de memoria, orden de las dos lecturas antes de SD, discrepancias, errores de IO/sync y conservación de fuentes previas. Una prueba del motor recorre el backup simulado de 64 MiB y comprueba que una segunda lectura diferente no genera sus datos en SD. Compilar pruebas Linux no equivale a ejecutarlas en recovery. La aceptación y extracción física de esta versión deben comprobarse en el TV.
