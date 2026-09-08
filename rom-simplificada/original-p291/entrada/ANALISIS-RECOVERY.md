# Entrada al recovery original P291

Estado: análisis y transformaciones de bytes verificados en PC. **No se ha escrito ENV ni BCB, reiniciado el TV, montado el USB ni ejecutado un programa ARM como parte de esta revisión.** El resultado define una entrada al menú; no autoriza ni demuestra una instalación. Las fuentes públicas son referencias identificadas, no el código fuente acreditado del ejecutable instalado.

## Resultado que cambia la siguiente prueba

El recovery original contiene el menú **Apply update from EXT → Update from udisk** y la ruta `/udisk`. Hay fundamento para usar el ZIP directamente desde esa ruta. El bloqueo anterior del cierre de Android no demuestra ausencia de recovery ni imposibilidad de usar USB; son etapas distintas.

Para entrar al menú se propone reemplazar las órdenes pendientes por `recovery\n--show_text\n`, sin `--update_package`, wipe, resize ni sideload. Una orden que contenga solamente `recovery\n` no es suficiente: en AOSP9 y en la referencia Khadas, la ausencia de opciones hace que `get_args()` vuelva a leer `/cache/recovery/command`.

**BCB preparado no equivale a recovery arrancado.** El ENV real arranca `boot`, y sus comandos no invocan `bcb`. La referencia `imgread kernel boot` tampoco consulta BCB. Un reset de emergencia sin argumento no acredita selección de recovery. La opción adicional de ENV transitorio se describe más abajo como propuesta pendiente de revisión y consentimiento para esa escritura.

## Evidencia local y alcance

Las imágenes se adquirieron anteriormente con root y verificación independiente; aquí se leen sus copias. La adquisición nueva de ENV y misc realizada por la tarea principal coincide con las originales. No se publican identificadores de red, cuenta ni contenido de datos del usuario.

| Elemento | Bytes | SHA256 |
|---|---:|---|
| recovery original | 25.165.824 | `4d7fda26b485657e48bcbb5b253ac81ea21c3a34f21d01e52cbe1dc18295c6af` |
| `/sbin/recovery` extraído | 1.829.824 | `436aa9c6fadc637d0c16d1924a22707b74214960bcd09c876d7b0964a5524dc3` |
| `/etc/recovery.fstab` | 1.893 | `adbf7454c9f4f452b014fd3394496f3f4e675cbe16366cac278077c56c40cfd4` |
| ENV original y adquisición actual | 8.388.608 | `49e48fddb963d1a4ebaf5889916bba8b59141bcc1eeef71ac1dad5c6425af775` |
| misc original y adquisición actual | 8.388.608 | `c8b5991390836e2f03693d8a4f6f2f4ea2b223c20951a119155fba19cf542549` |

La extracción privada contiene 167 entradas CPIO, modos, hashes y cabeceras ELF en `entrada/privado/recovery-extraido/inventario.json`. El script usa únicamente las funciones del parser previo; no ejecuta el módulo antiguo ni sus operaciones sobre otro candidato. El primer análisis ELF rechazó una suposición de ARM32 universal: `remotecfg` es AArch64. Se corrigió el lector para distinguir ambos formatos antes de cerrar el inventario. Ningún binario extraído se ejecutó.

El [análisis anterior del recovery](../../../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md) documenta claves y diferencias con el candidato retirado. Esta revisión usa siempre el original P291.

## Montajes, argumentos y herramientas reales

El fstab original declara `/dev/block/sd## /udisk auto defaults defaults`. El ejecutable contiene `/udisk`, `Update from udisk` y el selector de `.zip`. El fstab declara además `/dev/block/data /data ext4 defaults encryptable=footer`, `/dev/block/cache /cache ext4`, `/dev/block/misc /misc emmc` y las cinco particiones del sistema. Son aliases del recovery; no usar la ruta Android `/storage/<volumen>` como si fuera la ruta del mismo USB tras reiniciar.

En `init.rc`, el servicio es `/sbin/recovery` **sin argumentos en argv**. El ramdisk configura el directorio temporal, loopback, USB gadget y las tablas de controles remotos. Los montajes externos se resuelven en recovery, no quedan acreditados por crear el directorio. `init.recovery.amlogic.rc` incluye consola y servicios de control remoto; el original también permite adbd en su configuración de depuración. No se presume que LAN, ADB ni el control remoto vayan a estar disponibles o funcionar igual al arrancar recovery.

La referencia [Khadas Android9 `recovery.cpp`](https://github.com/khadas/android_bootable_recovery/blob/khadas-vims-pie/recovery.cpp), líneas 1026–1108 de la copia examinada, monta `/cache`, desmonta y vuelve a montar `/udisk`, muestra el selector y llama a `install_package()` con la ruta elegida. El [montaje extendido](https://github.com/khadas/android_bootable_recovery/blob/khadas-vims-pie/roots.cpp) llama a `ensure_path_mounted_extra()` antes del caso normal ext4/vfat. La función externa completa no fue acreditada contra el binario del TV. AOSP9 puro no maneja por sí mismo el tipo `auto` de ese fstab. Por tanto, la presencia de UI, ruta y extensión respalda la propuesta, pero **el montaje efectivo de este Kingston en recovery permanece pendiente**. No se acredita compatibilidad con todos los formatos de USB.

| Herramienta original | Bytes | ABI / enlace | Uso acotado |
|---|---:|---|---|
| `/sbin/mke2fs_static` | 697.820 | ARM32, estático | Crear ext4 cuando el instalador autorizado tenga respaldo de datos |
| `/sbin/e2fsdroid_static` | 719.004 | ARM32, estático | Poblar/configurar ext4; no es necesario por defecto para un volumen vacío |
| `/sbin/busybox` | 866.920 | ARM32, estático | Su tabla contiene mount, umount, sync y restorecon; no se ejecutó |
| `/sbin/sh` | 288.840 | ARM32, estático | Shell original; no presupone herramientas de `/system` |
| `/sbin/resize2fs` | 410.672 | ARM32, estático | Presente; no se solicita para la entrada al menú |
| `/sbin/remotecfg` | 335.368 | AArch64, estático | Cargador original de tablas IR |

Todos tienen modo 0750; las cabeceras no contienen intérprete dinámico ni segmento PT_DYNAMIC. No hay `make_ext4fs` independiente. Presencia/ABI no equivalen a ejecución física probada.

Para el instalador separado 0.2.1 se contrastó la receta de `/data`: 3.495.952.384 bytes físicos; al reservar 16.384 bytes de footer quedan 3.495.936.000 bytes, equivalentes a **853.500 bloques de 4.096**. La referencia [AOSP9 `roots.cpp`](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/roots.cpp), líneas 264–323 examinadas, calcula la longitud y utiliza `mke2fs_static -F -t ext4 -b 4096 dispositivo bloques`; ejecuta e2fsdroid solamente cuando hay directorio que poblar.

El binario original reconoce `nodiscard`, `lazy_itable_init=0` y `lazy_journal_init=0`. La receta propuesta por el instalador fija esas opciones y `MKE2FS_CONFIG=/etc/mke2fs.conf`. Ese archivo tiene 1.178 bytes y SHA `dcd4750293852e9b06f6de4c51c24d3d3941e67f221872965c6f02251509cd02`: bloques 4096, inodos 256, ratio 16384, reserva 1%; ext4 añade journal, extent, huge_file, flex_bg, dir_nlink, extra_isize y uninit_bg. No activa 64bit para ext4. El hash de mke2fs es `2b1799d99503493f46f130f861889e0f03eb00d39cc633212890823bf1f86525`; el de e2fsdroid, `2f5225164ea2e26d64fad03850ac3f5d0490d5d0d70db9c229f94aaf94fd9320`.

Esta receta **no se ejecuta al preparar la entrada**. Requiere respaldar todo `/data`, detectar cualquier montaje del mismo dispositivo, comprobar el FS creado y dejar constancia de la dependencia de permisos/restorecon del primer arranque. El `reservedsize=32M` del vendor nuevo y el footer de 16KiB son conceptos diferentes. No se acredita una etiqueta SELinux offline simplemente porque el directorio esté vacío.

## Órdenes antiguas y rama OEM de zipinfo

El misc real contiene `boot-recovery` y la opción histórica `--update_package=@/cache/recovery/block.map`. En la adquisición actual, `/cache/recovery/command` contiene solamente un salto de línea; `uncrypt_file` contiene `/data/cache/update.zip` seguido de salto de línea; `block.map` y `zipinfo` están ausentes según lectura de la tarea principal. Es un estado observado, no una condición que el siguiente programa deba asumir sin volver a comprobarla.

La [fuente OEM de referencia `install.cpp`](https://github.com/khadas/android_bootable_recovery/blob/khadas-vims-pie/install.cpp), líneas 569–744, permite acotar los mensajes encontrados en el ejecutable original:

1. Cuando `needs_mount` está activo y la ruta empieza por `@`, llama a `try_recovery_update_package()`.
2. Si existe `/cache/recovery/zipinfo`, intenta montar `/data`. Si ese montaje falla, llama a `format_volume("/data")` **antes de verificar/ejecutar el update-binary del ZIP**.
3. Usa la descripción de zipinfo para copiar desde una posición cruda de eMMC hacia `/data/update.zip`, cambia la opción BCB a esa ruta y elimina zipinfo.
4. Una ruta literal `/udisk/archivo.zip` evita esa rama en la referencia. Una entrada que solo solicita el menú tampoco llama al instalador.

Los mensajes y rutas coinciden con los presentes en el binario P291, pero no constituyen una demostración completa de control de flujo de ese ejecutable. Se retiene la precaución concreta: respaldar y neutralizar los cuatro nombres de órdenes pendientes, y no reutilizar la ruta `@...` anterior. No afirmar que un ZIP con respaldo interno puede proteger `/data` de operaciones que el recovery haga antes de iniciarlo.

## Contrato BCB: menú, preservación y salida

Según [AOSP9 `get_args()` y `finish_recovery()`](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/recovery.cpp), la prioridad es argv real, opciones BCB y finalmente command. El servicio original no tiene opciones argv. `--show_text` aporta una opción explícita, mantiene la UI visible y evita la caída a command. Debe escribirse ASCII con saltos de línea reales:

```text
recovery
--show_text
```

El [layout AOSP9](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/bootloader_message/include/bootloader_message/bootloader_message.h) coincide con el BCB observado en offset0: command32 bytes, status32, recovery768, stage32 y reserved hasta completar2048. El contrato reemplaza solo command `[0,32)` y recovery `[64,832)`, con relleno NUL. Conserva exactamente status, stage, reserved y todo misc desde offset2048. **No poner a cero toda la partición misc.**

Secuencia propuesta para la APK de preparación, aún sujeta a revisión de su implementación:

1. Confirmar P291/API28/UID0, aliases, nodos de bloque, rdev y tamaño actuales. El mapa local identifica env179:4 y misc179:7 de8MiB; la integración vuelve a acreditarlos. No elegir por número de disco USB, nombre parecido ni SHA parcial.
2. Respaldar ENV y misc completos, registrar sus hashes y comparar antes/después. Respaldar los archivos exactos `/cache/recovery/{command,uncrypt_file,zipinfo,block.map}` que existan; distinguir ausencia de denegación o error. Persistir copia, manifiesto y directorio con fsync y lectura posterior, antes de neutralizarlos.
3. Neutralizar esos nombres exactos solo si todavía coinciden con lo respaldado; comprobar ausencia y sincronizar el directorio de cache. No borrar logs, respaldos, ZIP internos ni otros nombres por patrón.
4. Releer el estado previo de misc y compararlo con el respaldo autorizado. Escribir como máximo la región BCB de2048 bytes con sus campos ajenos conservados; fsync y releer. Exigir igualdad con la propuesta y verificar que el resto de los8MiB no cambió. Si no se puede acreditar persistencia, marcar incompleto y **no continuar a ENV/reset**.
5. Si se autoriza por separado ENV transitorio, prepararlo solo después de lo anterior. Guardar el recibo de la preparación en USB y memoria interna; cerrar sin reiniciar.

No restaurar automáticamente los archivos de órdenes históricas ni el BCB con `@block.map`: eso reactivaría el intento que se pretende eliminar. Una cancelación antes del reinicio debe desarmar solamente la solicitud propia, con comparación del estado actual y nueva lectura. El codec conserva las demás regiones y rechaza desarmar un BCB desconocido. El respaldo original se conserva para investigación o restauración deliberada, no se usa como orden de recuperación automática.

En AOSP9 y la referencia Khadas, `prompt_and_wait()` llama a `finish_recovery()` antes de mostrar el menú; esa función guarda logs/locale, borra el BCB, elimina command, desmonta cache y sincroniza. Errores se registran y no acreditan borrado exitoso. La salida **Reboot system now** vuelve a ejecutar esa limpieza; una entrada visible no significa cero escrituras internas. No usar `--just_exit` para pedir menú ni dejar una actualización automática con reintentos. El timeout del control puede provocar reinicio según la UI de referencia: no se promete espera indefinida.

La ruta literal `--update_package=/udisk/<ZIP aprobado>` es una posibilidad posterior a verificar montaje/paquete y aceptar la instalación. En AOSP/KHadas esa orden arranca la actualización sin selección manual; puede crear BCB de reintento. **No es la orden de esta preparación.** La opción escogida conserva selección manual para separar entrada, lectura USB e instalación.

## ENV original y posible entrada de una sola vez

La comparación offline de24 combinaciones de tamaño/cabecera encontró un único CRC válido: registro de65.536 bytes, cuatro bytes iniciales de CRC32 little endian, calculado sobre65.532 bytes. CRC `669da84f`; SHA del registro `bf46dac31234ff841af63765c579218e98c3d75f7ddfa41a217e586ee8ec20cd`. Hay60 claves únicas, doble NUL en offset5101,60.433 bytes de relleno cero dentro del registro y8.323.072 bytes cero hasta el fin de la partición. No se observa un registro redundante; esto no certifica la configuración compilada del bootloader.

Valores decisivos acreditados en el ENV:

| Variable | Flujo observado |
|---|---|
| `bootcmd` | `run storeboot` |
| `storeboot` | lee kernel de `boot`, llama bootm y, si retorna, `run update` |
| `preboot` | factory-reset-protect → display → upgrade-check → storeargs → tecla SARADC → switch-bootmode |
| `switch_bootmode` | factory_reset → recovery interno; update → flujo update; cold_boot → arranque normal/try_auto_burn |
| `upgrade_check` | paso3 → update; paso1 → defaults reservados y saveenv; valor actual2 |
| `wipe_data`, `wipe_cache` | ambos `successful` |
| `recovery_part`, `recovery_offset` | `recovery`, `0` |

Ningún valor contiene `bcb`. La [referencia Amlogic `cmd_imgread.c`](https://github.com/khadas/u-boot/blob/ff7d3afbb488794da734cfe0bf0060d8573de56d/common/cmd_imgread.c), función `do_image_read_kernel`, lee la partición que recibe como argumento y no redirige boot por BCB. [cmd_bcb.c](https://github.com/khadas/u-boot/blob/ff7d3afbb488794da734cfe0bf0060d8573de56d/common/cmd_bcb.c) sí puede ejecutar recovery al encontrar `boot-recovery`, pero requiere una invocación y opción de compilación activas. Eso no aparece en el flujo ENV observado. No se concluye que ningún otro código del bootloader pueda mirar misc; simplemente esa ruta no está acreditada.

Propuesta de valor transitorio **solo para revisión, no aplicada**:

```text
if setenv bootcmd 'run storeboot'; then if saveenv; then run recovery_from_flash; run storeboot; else run storeboot; fi; else run storeboot; fi
```

Si se alcanza ese comando y la referencia se comporta igual, primero restablece el bootcmd normal; entra a recovery solo si setenv y saveenv devuelven éxito. Si recovery retorna, intenta el flujo normal. No cambia recovery_part, DTB, kernel, claves, preboot ni el resto de las variables.

La fuente [Hush del commit examinado](https://github.com/khadas/u-boot/blob/ff7d3afbb488794da734cfe0bf0060d8573de56d/common/cli_hush.c) reconoce comillas simples e if/then/else/fi; `parse_string_outer` copia una cadena sin LF antes de evaluarla. El nuevo valor no tiene LF, por lo que en esa referencia cambiar la variable no invalida la cadena en ejecución. El ENV original sí contiene un LF en otra variable: el codec lo preserva sin normalizarlo. Esta inspección del parser no es una ejecución en el bootloader real.

[env_storage.c](https://github.com/khadas/u-boot/blob/ff7d3afbb488794da734cfe0bf0060d8573de56d/common/env_storage.c) delega en MMC; [env_mmc.c](https://github.com/khadas/u-boot/blob/ff7d3afbb488794da734cfe0bf0060d8573de56d/common/env_mmc.c) selecciona la partición env con CONFIG_STORE_COMPATIBLE y escribe CONFIG_ENV_SIZE mediante block_write. El retorno0 comprueba cantidad de bloques, **sin lectura posterior ni transacción de reversión**. [env_common.c](https://github.com/khadas/u-boot/blob/ff7d3afbb488794da734cfe0bf0060d8573de56d/common/env_common.c) exporta y recalcula CRC; si detecta CRC inválido al importar, carga valores por defecto e incluso llama a saveenv. Corromper ENV no es una forma inocua de volver atrás.

Límites materiales de esta opción:

- `preboot` se ejecuta antes de `bootcmd`. Una tecla, un modo de reinicio o protección OEM podrían entrar a recovery antes de restablecer el comando transitorio. **No se garantiza una sola entrada ni que salir del recovery desarme ENV.**
- La escritura inicial y saveenv pueden fallar o quedar interrumpidos. Un respaldo en PC no hace posible su restauración si el TV deja de arrancar y no hay otro acceso probado.
- Se preserva el resto de la partición, pero cambiar la longitud de bootcmd desplaza la representación serializada de las otras claves. El criterio correcto es mismos pares clave/valor y orden, mismo relleno, cola idéntica y CRC válido; no afirmar que solo cambian unos bytes contiguos del valor.
- Para aplicar, exigir el SHA del ENV vivo previamente aprobado, respaldo completo y comparación posterior. Si cambia el perfil, no aceptarlo solo porque su CRC sea válido. La reversión solo debe actuar sobre el valor transitorio propio, preservando cualquier otro estado conocido; no restaurar a ciegas los8MiB históricos.
- `saveenv` exporta también variables que preboot/bootloader hayan calculado durante ese arranque. Su objetivo aquí es restablecer **el valor de bootcmd**, no restaurar el hash completo del ENV histórico. La reversión byte exacta del codec es una comprobación de PC previa al arranque; no una promesa del resultado físico de saveenv.
- La selección de reset, su alcance y los riesgos se revisan fuera de este codec. No hay instrucción de SysRq, reboot, corte de alimentación o escritura de ENV ejecutada aquí.

Se acordó una guarda adicional para el instalador0.2.1: **antes de formatear `/data`**, leer el registro ENV y exigir CRC válido, bootcmd exactamente `run storeboot`, y las definiciones originales de preboot/recovery_from_flash junto a recovery_part/recovery_offset. Si todavía aparece el valor transitorio u otro desconocido, detenerse sin formatear y devolver error visible al menú. No exigir en esta etapa el hash completo histórico ni exactamente60 claves, porque saveenv puede incorporar variables de ejecución. Esta guarda reduce el riesgo de instalar un sistema nuevo mientras queda un arranque transitorio pendiente; no certifica la atomicidad de la preparación inicial.

## Firma y límites del resultado

El recovery original tiene una clave RSA2048 exponente3, formato sin prefijo v1. El análisis previo liga su clave pública al certificado de prueba utilizado en los paquetes. El parser AOSP9 asocia v1 con SHA1; una firma integral SHA256 anterior no acreditaba aceptación por este recovery. Los paquetes0.2.0 incorporan firma integral compatible RSA/SHA1 y tienen verificación PC documentada en [la composición de0.2.0](../../../docs/evidencia/ROM-ORIGINAL-P291-020.md). La firma JAR y la firma integral de recovery son mecanismos distintos. **Validar firma offline no acredita arranque del recovery, lectura deUSB ni ejecución física del instalador.**

El [codec puro](codec_entrada.py) y sus [13 regresiones host](test_codec_entrada.py) verifican CRC, límites, claves duplicadas, corrupción, cambios de snapshot, estado OEM pendiente, preservación de regiones y desarmado de solicitudes propias. El [recibo](VALIDACION-CODEC.json) incluye los hashes exactos de fuentes y resultados calculados solo en memoria sobre ENV/misc actuales. El ENV propuesto revierte al registro original byte por byte; los campos ajenos de misc y toda su cola se conservan. No se generaron archivos de imagen listos para escribir ni se simuló éxito de saveenv o del bootloader.

El siguiente entregable debe integrar estas guardas y dejar una preparación persistente verificable, todavía sin reset. La prueba física deberá distinguir expresamente: preparación completa, recovery visible, USB montado, firma aceptada, respaldo de datos, escritura de imágenes y Android nuevo iniciado. Ninguna de esas etapas posteriores se da por realizada en este documento.
