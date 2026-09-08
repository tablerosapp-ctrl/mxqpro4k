# Revisión independiente del gestor de actualizaciones

Revisión local del componente [gestion-tvbase](../componentes/gestion-tvbase/README.md), realizada durante su desarrollo el 7/9/2026 ART. No se conectó al TV, no se instaló el APK y no se modificaron imágenes ni fuentes del autor durante la auditoría. La auditoría de arranque y servicios originales está separada en [AUDITORIA-SERVICIOS.md](AUDITORIA-SERVICIOS.md).

## Contratos revisados

El verificador comprueba RSA/SHA256 sobre los bytes decodificados exactos del payload antes de interpretar sus campos. La política del dueño viene en un recurso interno del APK; el manifiesto remoto no puede ampliar paquetes, certificados ni hosts. Se cotejan la identidad, versión, certificado y compatibilidad real del APK con el manifiesto, y se exige una versión superior a la instalada. La copia enviada a PackageInstaller vuelve a comprobar tamaño y SHA256 sobre los mismos bytes transferidos.

El receiver de instalación no está exportado y exige ID y token aleatorio de su sesión. Un resultado de éxito también se contrasta con el paquete realmente instalado. La revisión no encontró una vía por la que una aplicación externa ordinaria pueda sustituir el manifiesto firmado o hacer instalar un paquete sin el certificado permitido. Esto es revisión de código, no prueba de aislamiento en la ROM física.

La configuración entregada está desactivada y carece de destino de red. Cuando se configure, el componente solo abre conexiones HTTPS salientes hacia los hosts permitidos, sin redirecciones, comandos de shell ni puerto de escucha. El historial de secuencia y preparación se conserva en almacenamiento privado; el estado crítico usa confirmación síncrona y los archivos preparados se sincronizan. Cambiar servidor o clave requiere distribuir una nueva configuración dentro del APK: no existe todavía importación de configuración por pendrive.

## Hallazgos iniciales aceptados por el autor

| ID | Condición concreta | Consecuencia | Corrección solicitada |
| --- | --- | --- | --- |
| G1 | Los dos jobs compartían un único campo `engine`. Un segundo job podía reemplazarlo aunque su operación retornara por `BUSY`. | Detener el primer job cancelaba el segundo motor y dejaba trabajar al primero. | Asociar cada `JobParameters` a su motor y conservar reintento cuando exista otra operación. |
| G2 | Toda llamada a `schedule` reemplazaba `WINDOW_JOB` con el horario del día siguiente. | Abrir la pantalla o terminar el otro job podía detener una ventana activa o aplazar una ventana pendiente. | Conservar una ventana vigente; reemplazarla solo al consumirla o cambiar su política. |
| G3 | Se elegía el primer APK nuevo antes de aplicar `autoApps` y `autoBrowser`. | Una aplicación no automática al principio del manifiesto podía impedir indefinidamente actualizar Chrome automático. | En ejecución automática, seleccionar paquetes de un rol habilitado. |
| G4 | La ventana se comprobaba antes de verificar y copiar hasta 512 MiB al instalador. | Una copia prolongada podía enviar la instalación después de terminar la ventana. | Comprobar de nuevo ventana, caducidad y cancelación inmediatamente antes de `commit`. |
| G5 | El callback comprobaba ID/token y luego modificaba estado sin sincronización con `reconcile` ni el registro de otra sesión. | Un resultado legítimo atrasado podía borrar el ID o archivo preparado de una sesión posterior. | Serializar autenticación, transición y retiro de archivos con el mismo bloqueo que usa el motor. |

G2 se apoya además en el contrato de Android: programar un job con el mismo ID reemplaza al anterior y detiene su ejecución si estaba activo. [JobScheduler.schedule](https://developer.android.com/reference/android/app/job/JobScheduler#schedule(android.app.job.JobInfo)). G5 es una carrera entre componentes propios; no demuestra suplantación de callbacks por otra aplicación.

La reproducción local de G1 usa una copia intacta de `UpdateJob.java`, SHA256 `d2600e60321e2acb5cf6e4594f0a577398f1f42acc5c7d30bfe90e671f088330`. Con sustitutos limitados de JobService y del contrato `BUSY`, detener WINDOW produjo `window.cancelled=false; poll.cancelled=true`. Compilación y reproducción terminaron con código 0. Fuente, sustitutos y recibo quedan en `privado/auditoria-servicios/job-snapshot-inicial/`; el ejecutor es `privado/auditoria-servicios/repro-job.py`. No se ejecutó Android ni PackageInstaller: la prueba acredita la asociación incorrecta de motores del código inicial.

## Cierre de correcciones

El autor aceptó los cinco hallazgos e incorporó un mapa de motores por job, conservación de la ventana vigente con huella de política, filtro por rol automático, comprobación posterior a la copia y un bloqueo común de las transiciones de sesión. Los cinco escenarios quedan cerrados por revisión de las fuentes corregidas.

G1 se repitió con otra copia intacta de `UpdateJob.java`, SHA256 `06caf398d432a3d516c2a4624d8458ecfdbdbc11f799a2fefca039093c3ab25b`. El mismo escenario produjo `window.cancelled=true; poll.cancelled=false`, con compilación y ejecución de código 0. El recibo está en `privado/auditoria-servicios/job-snapshot-corregido/resultado.json`. Esta segunda prueba cubre la cancelación entre jobs superpuestos, no todas las intercalaciones del ciclo de vida.

Los dos ajustes de frontera también están incorporados: `beforeCommit` comprueba cancelación, emisión, caducidad y ventana inmediatamente antes de `session.commit`, después de las escrituras de preferencias; la finalización se publica en el hilo principal y comprueba que el motor todavía corresponde a la misma instancia del job. La versión final de `UpdateJob.java`, SHA256 `858210afbd9a13131f43a338201b7fc52b264604949e3516d9de4c1c830a7cee`, fue revisada y compilada, pero no es el snapshot intermedio ejecutado con sustitutos de la prueba anterior.

**Resultado de revisión: apto para liberar como componente experimental desactivado.** APK final de 57.810 bytes, SHA256 `73f0a2e73857cc83484caa3034bf69b8aa88422945153d71499f81c8ab81d320`. El cotejo independiente confirmó los nueve archivos del componente contra el recibo de compilación, la correspondencia del APK y Core con el recibo de 38 pruebas host del autor, y `assets/owner.conf` dentro del APK exactamente desactivado. Una nueva ejecución local de apksigner para API28 y aapt terminó con código 0; confirmó paquete `local.tvbase.gestion`, versión 1, API mínima y objetivo 28, y certificado SHA256 `d2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613`.

| Fuente final relevante | SHA256 |
| --- | --- |
| `UpdateCore.java` | `fd41e4dd27d10d57553fe961cf025f2959a37c1f43d95b18301036e5f669c347` |
| `ManagerEngine.java` | `710cf5363c77133dbbb9cb5de1bec6809927a2ce7d0df18a35b712f4f8d7d117` |
| `InstallReceiver.java` | `4c10eeb5b0d51ffd2faa0b4364735542baa0fbc9214872637c8573e7c0531523` |
| Recibo de compilación | `983ed25e83910c603760abafae89f93d4301d3b6240e120416b9789aa5b60349` |
| Recibo de pruebas del autor | `313a1f722383ec54504d04c7c3e9ca977e2fc3776b66c2d002f3937fd6ac6b16` |

Recibos del componente: [compilacion-resultado.json](gestion/compilacion-resultado.json) y [pruebas-resultado.json](gestion/pruebas-resultado.json). Comprobación independiente: `privado/auditoria-servicios/gestor-final/resultado.json`, `signature.txt` y `badging.txt`; ejecutor `privado/auditoria-servicios/verificar-gestor-final.py`. La confirmación para el recibo de liberación se comunicó al autor y queda ligada a este APK y estos hashes. No hay prueba física del gestor.

## Límites que permanecen

- Ni este análisis ni compilar el APK acreditan la concesión real de `INSTALL_PACKAGES`, una instalación silenciosa, TLS en el TV, activación del proveedor WebView o rendimiento de video.
- Un borrado de datos del gestor, una restauración antigua o root pueden reiniciar o alterar el historial contra repetición. No hay rollback automático ni rotación dinámica de certificados.
- El reloj del TV determina caducidad y mantenimiento. JobScheduler puede diferir trabajos y la plataforma puede exigir interacción o rechazar una instalación.
- Actualizar Chrome puede cerrar sus usuarios WebView. El gestor no promete reabrir las aplicaciones ni recuperar su reproducción.
- El prototipo conserva el SELinux permisivo original, documentado por el constructor. Reducir ADB, root y servicios no convierte esta revisión en certificación de seguridad de producción.
