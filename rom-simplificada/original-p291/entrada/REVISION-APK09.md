# Revisión independiente de Acceso USB0.9

**Fuentes revisadas para compilar en PC. No se acredita preparación física de ENV/BCB, separación real del proceso en el TV, persistencia del Kingston ni arranque de recovery.** El APK final y su política de ZIP deben cotejarse después de compilar. El [recibo de esta revisión](REVISION-APK09.json) fija los hashes de los siete archivos fuente examinados; modificar cualquiera invalida ese vínculo.

La aplicación prepara una entrada al menú del recovery original. No instala las imágenes de Android, no formatea datos y no reinicia automáticamente. El [análisis de recovery/ENV](ANALISIS-RECOVERY.md) explica la condición de preboot y los riesgos que siguen vigentes. La confirmación de la aplicación distingue esta modificación del arranque de la instalación posterior.

## Correcciones exigidas y comprobadas

| Hallazgo | Resultado revisado |
|---|---|
| Un timeout con KILL abarcaba la escritura de ENV; cerrar el ADB podía terminar también su proceso hijo. | Se retiró KILL. Un launcher crea el worker con setsid/nohup y descriptores independientes. El worker exige SID y grupo propios, ausencia de terminal, SIGHUP ignorada y stdin/stdout/stderr concretos antes de acceder al USB o modificar el arranque. Las consultas ADB posteriores son separadas. |
| Los checkpoints se guardaban solo en USB; al perderlo podía faltar el estado de un fallo parcial. | Hay checkpoints internos sincronizados antes de cada rename de cache y antes de escribir BCB/ENV, además de la copia USB. El fallo se intenta persistir primero dentro del TV. Una pérdida de observación devuelve estado desconocido, sin afirmar que el proceso terminó ni permitir relanzarlo. |
| Un marcador USB completo podía existir antes de terminar otras escrituras obligatorias. | El cierre es un contrato entre manifiesto USB, marcador, prepared interno y estado interno; un archivo COMPLETO aislado no acredita preparación. El lector comprueba sus hashes/nonces, ausencia de INCOMPLETO, sincronización y lock liberado. INCOMPLETO tiene precedencia. |
| La consulta de estado tomaba el lock durante el arranque y podía provocar que el worker abortara. | Las lecturas de stage no toman el lock. Se intenta únicamente al validar prepared; si el worker aún lo tiene, se informa stage. |
| La consulta podía leer un stage viejo y ver desaparecer el PID después de que el worker hubiera completado. | Ante PID ausente, vuelve a leer estado/fallo antes de declarar resultado indeterminado; un prepared nuevo pasa por el mismo control terminal. |
| El recibo describía restaurar bootcmd antes de recovery como garantía universal. | Se registra que depende de alcanzar bootcmd. No se afirma restauración del hash completo de ENV, atomicidad de saveenv ni rollback probado. |

La guarda añadida por el coordinador también se cotejó: el montaje FAT32 debe corresponder a un dispositivo de bloque cuya ruta sysfs sea USB; se contrastan mountinfo, st_dev, rdev, nodo fuente y marcador. No se acepta simplemente un directorio con ese nombre. Las comprobaciones se repiten antes de las fases mutadoras.

## Orden y comportamiento de fallo

El flujo revisado identifica API28, build, DT, kernel y UID0; verifica el ZIP exacto fijado por la compilación; lee ENV/misc completos y exige sus SHA aprobados. Calcula los cambios con un codec independiente de I/O y coteja los hashes de los prefijos propuestos. Guarda ambos respaldos y el estado de los cuatro archivos concretos de cache, con creación exclusiva, fsync de archivo/directorio y lectura posterior.

Antes de escribir, compara nuevamente las particiones completas. Las órdenes antiguas se renombran individualmente solo si aún coinciden con lo respaldado. Cada operación está precedida por estado persistente. No se restaura automáticamente ninguna orden OEM. Después se escribe BCB y finalmente ENV, con límites de2048 y65536 bytes respectivamente, fsync y lectura comparativa de cada partición completa. El codec conserva los campos ajenos de BCB y las demás claves/cola de ENV. Si una comprobación falla, no avanza a la siguiente fase ni solicita reset.

El directorio interno activo y la preferencia de intento impiden repetir la preparación a ciegas. Se puede volver a observar el mismo nonce sin relanzar el worker. Si el proceso muere después de empezar una escritura, las marcas indican que pudo quedar parcialmente aplicada; no son prueba de que el contenido original siga intacto. No hay restauración automática ni promesa de recuperar un TV que deje de arrancar.

Las consultas de estado comprueban el código de salida del comando con nonce. Un cierre ADB por sí solo no equivale a éxito. AUTH, canal incorrecto, checksum inválido, salida truncada, exceso de tamaño o resultado incompleto impiden mostrar preparación completa. El único destino de red es127.0.0.1; no se aceptan comandos de intents ni archivos del pendrive como código. El helper usa únicamente el `su` original; no instala root, modifica autenticación ni reinicia adbd.

## Verificación independiente en PC

- Se repitieron las13 regresiones del [codec Python](test_codec_entrada.py).
- Un harness Java propio compiló el `EntryCodec.java` real, leyó los respaldos actuales solo desde PC y contrastó sus cuatro hashes de salida con [la prueba Python](VALIDACION-CODEC.json). Coinciden el registro ENV, ENV completo, BCB2048 y misc completo;11 entradas negativas fueron rechazadas. También se cotejaron valores/orden y regiones ajenas. No se escribieron imágenes candidatas.
- Un servidor ADB falso en loopback de la PC verificó12 casos del cliente real: fragmentación de cabeceras y UTF8, AUTH, magic, checksum, tamaños, canales, cierre, línea incompleta, reutilización y rechazo de host externo. El servidor nunca ejecutó los comandos recibidos y no contactó el TV.
- La compilación con API28 pasó sobre los siete hashes revisados. Esa comprobación usó METHOD_REVIEWED=false y política de ZIP vacía; no produjo un APK utilizable ni reemplaza el cotejo posterior de la compilación final.

Los harness, salidas y clases de revisión permanecen en `entrada/privado/`. No se simularon las APIs Android de archivos, fsync, locks, conjuntos de sesión ni block devices para llamarlas prueba física. El parser de recibos y la coordinación de procesos se revisaron por código; los casos ADB no son una simulación completa del instalador.

## Límites de aprobación

`approved=true` en el recibo permite que el compilador verifique estas fuentes exactas y prepare el APK con la política exacta del ZIP0.2.1. **Es aprobación de revisión offline para construir, no una autorización adicional para ejecutar escrituras en el TV.** El coordinador conserva la decisión sobre entrega y el usuario verá la acción de preparación concreta.

Antes de declarar el APK final revisado deben coincidir: fuentes, recibo de método, política generada, hash/tamaño del ZIP real, paquete/versionCode, certificado y hash del APK. El instalador0.2.1 mantiene su propia revisión, incluido respaldo de `/data` y guarda de ENV normal antes de formato; esta revisión no los sustituye.

Siguen sin acreditarse: persistencia efectiva de este USB en el TV, operación completa del worker desacoplado, resultado del cambio de ENV, montaje USB en recovery y arranque de Android nuevo. Las comprobaciones dentro del helper fallan antes de mutar si no se acredita su separación del transporte, pero esa defensa también requiere su primera comprobación física.
