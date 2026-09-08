# Entrada original y preparación de datos 0.2.1

## Resultado posterior a la entrega

El usuario ya autorizó y se completó la [preparación física ENV/BCB](PREPARACION-ENTRADA-P291-09.md), con cierre y lectura independientes verificados. El helper no instaló la ROM ni emitió reinicio; tras el ciclo físico posterior, el usuario informó un menú de recovery. La instalación sigue pendiente. Este documento conserva la construcción y entrega previas; sus menciones a decisión/ejecución pendientes son históricas.

Trabajo del 7/9/2026 ART, posterior a la construcción de plataforma0.2.0. Este documento distingue resultados físicos de artefactos terminados y pendientes de ejecución. El usuario volvió a conectar el Kingston a la PC y confirmó que el primer P291 continúa al2% con LAN.

## Observado en el primer TV

La comprobación actual devuelve UID0 mediante el `su` existente, DT `gxlx2_p291_1g`, API28 y la compilación original esperada. Kernel4.9.113, ARM32. `/data` corresponde directamente a `179:20`, ext4, 3.495.952.384 bytes; la propiedad de cifrado informa `unencrypted`. System/vendor permanecen montados de solo lectura. No se instaló root ni se cambió la autenticación.

Se ejecutó una vez un helper propio con `app_process`, SDK28, a través de LAN. Creó exclusivamente un directorio temporal y un archivo de64bytes; comprobó UID/perfil, fsync del archivo, su directorio y el padre, identidad de inode, bytes y SHA. Resultado terminal correcto y código remoto0. Esto acredita ese acceso y sincronización en ext4; no prueba todavía fsync del Kingston ni entrada a recovery. [Fuentes y contrato](../../rom-simplificada/original-p291/entrada-apk/PROBE-EJECUCION.md).

Se adquirieron de nuevo las particiones `env` y `misc`, 8MiB cada una, verificando SHA antes, copiaPC y SHA después. El estado actual coincide con los originales correspondientes. Las órdenes de cache observadas son `command` de un byte de salto de línea y `uncrypt_file` de23bytes que todavía apunta al ZIP antiguo. `block.map` y `zipinfo` están ausentes. Los datos crudos se conservan localmente y no se publican.

No se escribió ENV/BCB ni se flasheó una partición en esta revisión. No se pidió reinicio, Update, formato de particiones, cambio de radios ni otra consulta BatteryStats. Las escrituras normales sobre el sistema de archivos se limitaron a herramientas, archivos de prueba propios y la instalación de APK0.9; ART puede crear su caché de ejecución.

Actualización posterior: se probó además el formateador original sobre un **archivo regular temporal**, sin montar ni formatear particiones. Creó ext4 con la geometría exacta prevista, código0 y superblock correcto: 853.500bloques de4096bytes, inodos256 y features `0x3c/0x242/0x7b`. El archivo y las dos herramientas temporales fueron retirados al terminar. [Recibo saneado de la prueba física](../../rom-simplificada/original-p291/instalacion-021/FORMATEADOR-PRUEBA-TV.json). Esto acredita ABI, opciones y estructura producida; no acredita todavía el montaje ni la escritura de userdata desde recovery.

La sonda ARM32 abrió ENV/data de solo lectura y confirmó `BLKGETSIZE64=0x80041272`, tamaños exactos y código0. La constante anterior `0x80081272` devolvió EINVAL22. Este defecto afectaba a los ejecutables0.2.0 de instalación y restauración; ambos tienen reemplazo0.2.1 separado. La sonda se retiró. No se acepta compilación exitosa como prueba de ABI en el equipo.

A las22:55ART, `adb install -r` terminó con Success para la APK0.9 sellada y `am start` aceptó la solicitud. **La captura posterior de las22:59ART muestra el diálogo del sistema detenido al2% sobre fondo negro: la APK no está visible.** Instalar/abrir no eliminó el diálogo ni ejecutó la preparación. La conexión LAN permite acompañar el método sin depender de botones tapados, después de la decisión explícita del usuario.

Se añadió un [cliente de operación por LAN](../../rom-simplificada/original-p291/entrada-apk/OPERACION-LAN-09.md) que invoca el mismo helper de la APK sellada. Conserva un nonce antes del único lanzamiento y permite retomar consultas de estado sin relanzar; no cambia el diálogo ni emite reinicios. No se ejecutó su preparación real. Esta vía evita la confirmación visual, por lo que la decisión específica debe registrarse en la conversación antes de usarla; un argumento de línea de comandos no sustituye esa decisión.

## Incidencias preservadas

- La consulta filtrada de símbolos del kernel devolvió algunos nombres, pero finalizó con código remoto136 después de17segundos. No se acepta como captura completa ni se repite. La existencia de símbolos o de `/proc/sysrq-trigger` no demuestra un reset eficaz.
- Una primera adquisición con `dd` no superó tamaño/hash: `exec-out` puede mezclar las estadísticas de stderr con el flujo binario. Se cambió al lector `cat`, sin estadísticas de éxito, conservando tamaño exacto, marcador de salida y hashes independientes. La segunda adquisición verificó ambas particiones. No se aceptó el código de transporte0 como prueba de integridad.
- El `truncate` original del TV convirtió3.495.936.000 en un valor negativo de32bits y rechazó crear el tamaño lógico del archivo de prueba. El formateador todavía no había sido ejecutado. Se extendió ese mismo archivo regular mediante un único bloque final, se verificó el tamaño exacto y solo entonces se ejecutó mke2fs. No extrapolar el defecto de ese applet a Go, mke2fs ni la capacidad de FAT32; conservar las APIs de64bits necesarias para archivos grandes.

## Por qué no basta con otro ZIP

El entorno real tiene `bootcmd=run storeboot`. Su secuencia `preboot` revisa modo de reinicio, tecla y estados de actualización; no aparece una llamada BCB en las60variables almacenadas. En las fuentes Amlogic de referencia, `imgread kernel boot` carga la partición que se le indica y la interpretación BCB corresponde a otra orden. Por tanto, preparar solo BCB y cortar alimentación no acredita que este cargador vaya a entrar en recovery.

El recovery original sí contiene el menú «Apply update from EXT» → «Update from udisk» y la ruta `/udisk`. Las fuentes OEM de referencia tienen además una rama capaz de formatear `/data` al intentar recuperar un paquete mediante `@block.map` y `zipinfo`. La nueva entrada debe neutralizar las órdenes antiguas después de respaldarlas y mostrar el menú, sin selección automática del paquete.

La APK0.9 contiene una orden de arranque transitoria que restaura el valor normal de `bootcmd` y solicita guardarlo antes de cargar el recovery interno. **Modificar ENV introduce un riesgo distinto del ZIP:** una escritura incompleta o una incompatibilidad puede impedir que Android arranque. El respaldo no demuestra que exista una vía física de rescate. El código de `saveenv` de referencia no ofrece readback ni transacción atómica. El usuario pidió conocer estos riesgos antes de decidir; la preparación todavía no se autorizó específicamente ni ejecutó.

`preboot` corre antes de `bootcmd`: si entra en recovery anticipadamente, la orden transitoria podría quedar pendiente. Por ello el instalador debe rechazar el formato mientras no observe `bootcmd` normal, con CRC y perfil de entorno válidos. Restablecer `bootcmd` no significa restaurar byte por byte todas las variables: U-Boot puede exportar valores calculados durante el arranque.

## Paquetes sellados y acceso revisado

La variante0.2.1 conserva exactamente las cinco imágenes de plataforma0.2.0 y añade el respaldo de userdata, seguido de su preparación como ext4 limpio. Antes de borrar debe verificar seis respaldos crudos, su persistencia en USB y la estabilidad de los orígenes desmontados. Son6.067.060.736bytes; se exigen6.603.931.648bytes libres, incluido margen. El archivo mayor cabe en FAT32.

La instalación0.2.1 tiene573.688.933bytes y SHA `dcb152c77e55cb067d6e88a8144990a3edb5d06568ea8cdfdc414a0fa21aac58`. Pasaron firma integral Python/OpenJDK, CRC, hashes de cinco imágenes, validador Windows y57eventos/53casos hoja de Go. [Recibo final](../../rom-simplificada/original-p291/instalacion-021/salida/TVBASE-P291-A9-0.2.1-VERIFICACION.json).

La restauración0.2.1 separada repone cinco particiones originales y conserva los datos que existan. ZIP913.294.443bytes, SHA `42580206f254fab0a2280cd263a48882677e7ddf5cfd609382a840c8d0fb103a`, con firma, CRC/payloadSHA, validador y revisión independiente correctos. **No restaura automáticamente userdata.** Una receta de restauración de seis particiones necesita el hash y recibo del respaldo de datos que todavía no se ha creado. La entrada posterior a recovery desde Android simplificado y una restauración física siguen pendientes. [Recibo final](../../rom-simplificada/original-p291/restauracion-021/salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-VERIFICACION.json).

La APK0.9 sellada tiene61.843bytes, SHA `1d0f267e818acca5562048f9961c7c234f36b8cc81f827cb3eac9e3fcd2505a4`; firmaAPI28 y DEX recompilado idéntico verificados independientemente. [Liberación](../../rom-simplificada/original-p291/entrada-apk/LIBERACION-09.json). Las pruebas físicas no incluyen aún desacoplamiento del helper, fsync del USB ni preparación ENV/BCB.

## Kingston

El dispositivo fue identificado de nuevo por USB, UniqueId y capacidad30943995904bytes, FAT32TVBASE. Windows sigue informando Warning/FullRepairNeeded. Las lecturas de los cuatro archivos de la entrega anterior coinciden con sus hashes. No se formateó ni se ejecutó reparación; la preparación nueva debe copiar y releer, archivando antes enPC el ZIP0.1.2, recovery externo antiguo, auxiliarBluetooth y guía. Los informes y respaldos permanecen.

La copia0.2.1/APK0.9 terminó el7/9/2026 a las23:06:04ART, código0: cuatro archivos nuevos copiados y releídos, cuatro archivos anteriores archivados enPC/verificados y retirados (598.275.472bytes), informes y respaldos conservados. Quedan29.429.121.024bytes libres. [Recibo físico de la copia](../../preparacion-usb/original-021-estado.json) y [revisión previa del contrato/script](../../preparacion-usb/REVISION-ORIGINAL-021.json). No hubo formato ni reparación. La expulsión segura permanece pendiente: el flush por archivo y la relectura no prueban persistencia de metadatos FAT tras desconexión. Esta entrega tampoco acredita entrada a recovery ni instalación.
