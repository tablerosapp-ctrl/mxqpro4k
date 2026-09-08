# Instalación 0.2.1 con preparación de userdata

Estado: instalador0.2.1 compilado, revisado y empaquetado; firma Python/OpenJDK, cinco SHA/CRC y validador Windows correctos. [Recibo final](salida/TVBASE-P291-A9-0.2.1-VERIFICACION.json): ZIP573688933B, SHA256 `dcb152c77e55cb067d6e88a8144990a3edb5d06568ea8cdfdc414a0fa21aac58`. No se ha ejecutado el instalador en el TV ni se ha escrito el USB desde esta tarea. La variante vive en este directorio; no modifica `empaquetado/`, sus releases0.2.0 ni las imágenes originales.

## Resultado y límites de la variante

El instalador 0.2.1 debe resolver la condición que 0.2.0 delegaba: respaldar los datos originales y crear una partición de datos limpia antes de escribir Android. Las cinco imágenes de plataforma serán **exactamente las de 0.2.0**; la versión dentro de Android seguirá siendo 0.2.0. Solo cambia el instalador y su manifiesto.

La operación propuesta es `install_reviewed_with_userdata_migration`, con política `backup_raw_userdata_then_format_ext4` y manifiesto de formato 3. Los validadores de 0.2.0 deben rechazar este nuevo contrato. No se reutiliza un ZIP anterior ni se cambia su firma o contenido.

El respaldo de datos no se vuelve a copiar automáticamente al Android limpio: eso reintroduciría aplicaciones y configuraciones OEM. Una restauración posterior de esos datos requiere una operación explícita y la misma identidad del equipo. El restaurador de cinco particiones conserva los datos existentes, pero **no restaura este nuevo respaldo de userdata**. Se prepara una variante ORIGINAL-RESTORE-0.2.1 corregida para ARM32; la0.2.0 permanece histórica.

## Evidencia disponible

- P291: `gxlx2_p291_1g`, API28, partición `/dev/block/data`, dispositivo `179:20`, tamaño **3.495.952.384 bytes**. Los aliases y el mismo eMMC deben comprobarse nuevamente en recovery.
- `etc/recovery.fstab` original: `/dev/block/data /data ext4 defaults encryptable=footer`.
- `vendor/etc/fstab.amlogic`, conservado en la plataforma0.2.0: `/data` ext4, `wait,check,quota,formattable,reservedsize=32M`; no declara cifrado para `/data`.
- La captura previa de Android montaba `/dev/block/data` directamente como ext4. Esto describe aquel estado; el instalador comprobará el estado real antes de leer o escribir.
- El ramdisk original contiene `mke2fs_static` y `e2fsdroid_static`. La revisión independiente confirma ELF32 ARM estáticos, sin intérprete ni dependencias dinámicas. `make_ext4fs` standalone no está presente.
- El `init.rc` conservado ajusta propietario/modo de `/data`, restaura su contexto SELinux y crea los directorios de Android durante el arranque. El instalador no debe preinstalar aplicaciones OEM ni reconstruir sus datos.

## Imágenes inmutables

| Partición | Bytes | Major:minor | SHA256 de plataforma0.2.0 |
| --- | ---: | --- | --- |
| system | 1342177280 | 179:18 | `e602d62182400f2b785b9044dd28b767791bcafb411146f988b719c6e722dc7b` |
| vendor | 943718400 | 179:16 | `57c1f319e1c1f7df6918b2ffd513b1b0a63611e498fa6000826ee34206ef9fee` |
| product | 134217728 | 179:19 | `c8550c937cb85257e58d8d70414b9162141d9e20cf199406d4ca3cfacf8ab00e` |
| odm | 134217728 | 179:17 | `97836d5a1b016b64d3875c82cb5f3b4daee0f56d8eea3675b4231086429cbe67` |
| boot | 16777216 | 179:11 | `c1a71479498bdfd8368fb1ade42ae293cb97f6087c43c3a8f8f31535725113fc` |

El empaquetador debe leer y verificar `IMAGENES-0.2.0.json`, `COMPOSICION-VERIFICADA.json` y el recibo final0.2.0, fijando sus hashes. No debe regenerar imágenes. Se conserva el kernel y DTB originales, el ramdisk revisado y la firma whole-file SHA1 compatible con la clave v1 original; la verificación PC no acredita ejecución por recovery.

## Capacidad del pendrive

`data.img` ocupa 3.495.952.384 bytes, menos que el máximo de archivo FAT32 de 4.294.967.295 bytes. Quedan 799.014.911 bytes de margen por archivo; no necesita dividirse ni cambiar FAT32.

Los seis respaldos crudos suman **6.067.060.736 bytes**. Se exige al menos **6.603.931.648 bytes libres** antes de empezar (los respaldos más 512MiB de margen), después de copiar los ZIP y auxiliares de entrega. Cada archivo queda por debajo del límite FAT32. El cálculo usa el espacio realmente disponible del volumen USB montado, no la capacidad nominal del Kingston.

La carpeta nueva del respaldo se crea con nombre único y nunca reemplaza otra `TVBASE-respaldo-*`. El respaldo de userdata puede contener información privada; permanece en el pendrive y en el archivo local privado, no en GitHub.

## Secuencia de instalación

1. Verificar interfaz de recovery, UID0, perfil P291, geometría de las seis particiones y mismo eMMC; ausencia de esquema A/B o dinámico. Verificar que boot actual sea el original adquirido antes de esta primera instalación. Verificar USB físico, marcador, montaje y espacio libre. Leer ENV desde179:4/8MiB: validar CRC32 de su registro64KiB y exigir `bootcmd=run storeboot` y el flujo de preboot/recovery original. Si aún queda la entrada transitoria, detenerse en el menú sin formatear. No se exige hash de toda ENV porque `saveenv` puede exportar variables de ejecución.
2. Abrir el ZIP directamente desde el USB marcado. Verificar manifiesto, SHA y CRC de los cinco payloads completos y la identidad de las herramientas nativas antes de cualquier escritura en el TV. El ZIP no puede depender de `/data/cache/update.zip` ni de un descriptor situado en `/data` que vaya a formatearse.
3. Si `/data` está montada por recovery, identificar el montaje y desmontarlo normalmente. No usar desmontaje forzado ni diferido. Rechazar montajes en otro destino, dispositivos `dm-*` dependientes o un montaje que siga ocupado. Las otras cinco particiones también deben estar desmontadas. Leer de nuevo los aliases y montajes antes de cada acceso destructivo.
4. Copiar las seis particiones a archivos nuevos `*.img.parcial`. Para cada una: tamaño exacto, SHA durante copia, sincronización del archivo, cierre real, nueva lectura del USB con SHA y nueva lectura del origen desmontado con SHA. Los tres valores deben coincidir. Los cinco originales también deben coincidir con los hashes adquiridos. Comprobar de nuevo identidad y montajes después de cada lectura.
5. Renombrar cada archivo solo cuando esté verificado; sincronizar el directorio. Escribir un manifiesto de respaldo que incluya identidad, nombres, bytes, hashes, códigos y comprobaciones reales. Sincronizar archivo y directorios, releer el manifiesto y confirmar nuevamente los archivos. Registrar y sincronizar `backup_verified` **antes** de comenzar el formato.
6. Revalidar ENV, destinos y herramientas; registrar `format_started`, ejecutar el formateador nativo verificado sobre `/dev/block/data` con argumentos fijos, comprobar su código real y el superblock creado. No encadenar comandos de shell ni usar el resultado visual como éxito.
7. Sincronizar y comprobar los datos estructurales del nuevo ext4. Montar `/data` desde el dispositivo real con `ro,noload,nodev,nosuid,noexec`. Exigir un único montaje de ese `major:minor` y contenido vacío o solo `lost+found` vacío; no aceptar un marcador como sustituto. Registrar `userdata_prepared` con parámetros, código y comprobaciones.
8. Reutilizar las guardas de flasheo para escribir `system`, `vendor`, `product`, `odm` y finalmente `boot`. Antes de cada escritura comprobar destinos desmontados y `/data` realmente vacía/RO. Sincronizar cada partición, releerla entera y comparar con el hash del payload. No escribir bootloader, recovery, DTB, vbmeta, misc ni otras particiones desde esta operación.
9. Registrar `installed_verified` únicamente tras las cinco relecturas correctas. Sincronizar el cierre y mostrar la ubicación del respaldo. El reinicio final debe formar parte del procedimiento acordado; no se confunde un paquete preparado con una instalación terminada.

Debe mostrarse progreso durante copia, relectura y formato, incluyendo etapa y bytes. Un timeout, falta de salida, fallo de sincronización o lectura incompleta es fallo; conservar parciales y registros. No reiniciar ni repetir automáticamente el formato tras un error.

## Tamaño del sistema de archivos y footer

Receta acordada: respaldar los **3.495.952.384 bytes completos**, y crear ext4 en **3.495.936.000 bytes**, equivalentes a **853.500 bloques de 4096 bytes**, reservando los últimos 16KiB que el recovery identifica como footer. Tras el respaldo íntegro, limpiar y releer esos 16KiB para impedir que quede un footer de cifrado anterior.

La reserva de footer no equivale a `reservedsize=32M`: esta última es una reserva de espacio de ext4 para el sistema. No se restaura una clave de cifrado ni se activa cifrado nuevo.

El binario original `/sbin/mke2fs_static`,697820B,SHA256 `2b1799d99503493f46f130f861889e0f03eb00d39cc633212890823bf1f86525`, recibe los argumentos fijos `-F -t ext4 -b 4096 -E nodiscard,lazy_itable_init=0,lazy_journal_init=0 /dev/block/data 853500`. Se fija `MKE2FS_CONFIG=/etc/mke2fs.conf`, cuyo SHA256 original es `dcd4750293852e9b06f6de4c51c24d3d3941e67f221872965c6f02251509cd02`. Las opciones extendidas están en la ayuda embebida del ejecutable. La configuración original crea inodos256 y no habilita64bit ni metadata_csum para ext4. `nodiscard` evita emitir descarte sobre el resto del dispositivo; la inicialización completa evita dejar trabajo de inicialización de journal/inodos pendiente.

El esquema coincide con el formato vacío de [AOSP Android9 roots.cpp](https://android.googlesource.com/platform/bootable/recovery/+/refs/tags/android-9.0.0_r42/roots.cpp): mke2fs nativo y longitud descontando footer; e2fsdroid se necesita para poblar contenido, que aquí no se agrega. Esto fundamenta la receta, pero no reemplaza la prueba de ejecución del recovery de este TV.

La raíz ejecutó el binario y configuración originales en Android del primer TV sobre **un archivo regular nuevo**, sin formatear ni montar una partición. El código real fue0; el superblock obtenido tiene853500 bloques, inodos256, estado limpio1 y features `0x3c/0x242/0x7b`, exactamente los que exige esta variante. Se retiraron únicamente los temporales propios. Evidencia privada: `privado/mke2fs-prueba-fisica-20260907-224337/receipt.json`. Esto prueba ABI y argumentos del formateador, no el formato de un dispositivo de bloques ni su montaje en recovery. El intento previo de crear ese archivo con `toybox truncate` falló por desborde de32bits antes de ejecutar mke2fs; se conservó y la extensión sparse con `dd` sí funcionó.

La consulta de tamaño usa el número ioctl correspondiente al ABI del proceso: ARM32 `BLKGETSIZE64=0x80041272`, aunque el resultado siga siendo uint64. Se corrigió el literal de64bits heredado. La [implementación compat del kernel](https://android.googlesource.com/kernel/msm.git/+/android-6.0.1_r0.5/block/compat_ioctl.c) distingue ambos comandos. Las pruebas locales fijan los dos valores y la sonda separada se ejecutó en el primer TV abriendo ENV y data **solo en lectura**. El comando correcto devolvió ambos tamaños exactos con errno0; el heredado devolvió errno22/EINVAL en ambos. Evidencia privada: `privado/abi-probe-fisico-20260907-224633/receipt.json`. La sonda no ejecutó el instalador y su temporal se retiró correctamente.

Si el equipo presenta cifrado o un mapping inesperado al entrar en recovery, conservar el respaldo crudo posible pero no afirmar que sus archivos sean legibles. No formatear hasta resolver la discrepancia de perfil. Un formato ext4 no es un borrado forense de todos los bloques antiguos.

## Mensaje del acceso USB

Texto propuesto antes del botón de instalación:

> Se guardará en este pendrive una copia completa de los datos y de las cinco particiones que se reemplazan. Después se eliminarán del TV las aplicaciones, cuentas, ajustes y archivos internos actuales para instalar Android limpio. Los datos anteriores no se copiarán al sistema nuevo. Si la copia no puede verificarse, la instalación se detendrá antes de borrar.

El botón debe describir la acción: **«Respaldar e instalar Android limpio»**. No añade una autorización rutinaria: presenta de forma concreta la operación de reemplazo ya solicitada. El acceso debe verificar el ZIP exacto y mostrar el resultado de su preparación; nunca anunciar que ya instaló la ROM por haber enviado una orden de entrada a recovery.

## Fallos y recuperación

Hasta `backup_verified` no debe haber escrituras internas del instalador. Después del inicio del formato, la reversibilidad depende de conservar el respaldo y de poder volver a entrar al recovery. Si falla el formato o cualquier imagen, quedarse en recovery, conservar los seis archivos y registrar el punto exacto.

La variante es no A/B; no proporciona rollback automático. Los doce respaldos PC previos y las releases originales quedan intactos. Una interrupción no autoriza sobrescribirlos ni presentar un respaldo nuevo de datos ya formateados como si fuera el original. Detectar una transacción incompleta anterior y detenerse con su referencia; la reanudación o restauración se define como operación separada, sin repetir el borrado silenciosamente.

La plataforma nueva elimina el `su` heredado y no expone ADB TCP por defecto. El gestor incluido no tiene REBOOT/RECOVERY. Por ello no está acreditada una reentrada desde una APK en Android nuevo ni la actualización de la siguiente ROM por esa vía. Ver [restauración](RESTAURACION.md) para distinguir los cinco originales del respaldo futuro de seis particiones.

La entrada efectiva a recovery y el acceso a los archivos del USB siguen siendo una prueba física independiente. Resolver la migración de datos elimina una carencia real del instalador0.2.0, pero no demuestra por sí mismo esa entrada.

## Validación y reproducción

- Conservar la revisión independiente de la receta nativa con hashes/opciones exactas y la limitación de SELinux del primer arranque.
- Probar localmente el flujo con adaptadores: ningún formato antes de todos los respaldos; escritura corta, SHA distinto, USB lleno, sync fallido, datos montados o alias cambiado deben impedir formato. Un fallo después del formato debe impedir falso éxito o reinicio automático.
- Verificar que la nueva variante acepte solo este perfil y estas imágenes, rechace manifiestos0.2.0/operaciones distintas y conserve todos los releases previos.
- Compilar a un directorio privado nuevo y empaquetar en `instalacion-021/salida/`, sin sobrescribir entregables anteriores. Verificar firma, payloads, validador Windows y recibos por separado de la prueba física.

[EVIDENCIA-TESTS.json](EVIDENCIA-TESTS.json) registra57 eventos/53 pruebas hoja, tres fixtures binarias, nueve fallos de respaldo, seis escenarios de orden de migración y ocho rechazos ENV. El recibo distingue los adaptadores Windows de las comprobaciones físicas de formateador en archivo y de ioctl en lectura. El build del release está conservado en `privado/original-p291-empaquetado/TVBASE-P291-A9-0.2.1`; el empaquetador rechaza sobrescribirlo.
