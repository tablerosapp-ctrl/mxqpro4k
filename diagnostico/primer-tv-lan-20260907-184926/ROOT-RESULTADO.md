# Root confirmado y bloqueo localizado

El 7/9/2026 el usuario pidió concentrar el trabajo en obtener root y después explicar las vías de instalación forzada, con sus riesgos, para decidir. Esta instrucción sustituye la restricción anterior de no habilitar root para esta exploración. No autoriza a ejecutar por sorpresa un reinicio de emergencia o una grabación directa antes de presentar esa decisión.

## Acceso obtenido

A las 19:33:21 ART, `/system/xbin/su 0 /system/bin/id` devolvió UID 0 y contexto SELinux `su`. El Android original es userdebug y ya contiene ese su. No se instaló un paquete de root, no se reinició adbd y no se cambió la autenticación. SELinux ya estaba Permissive al leerlo; no se ejecutó setenforce. El acceso por comando se comprobó; no se afirma una modificación nueva y persistente del firmware.

## Resultado útil

- La copia interna `/data/cache/update.zip` mide 573082917 B y su SHA coincide con la ROM 0.1.2: `6c0c4307208c8d0e1a958a3fc6c790fa94021a850599985b0a41b340b821bb99`.
- `/cache/recovery/uncrypt_file` contiene esa ruta. `command` contiene solo un salto de línea. `block.map` **no existe** en la lectura con root. El respaldo de misc confirma BCB con `boot-recovery` y `--update_package=@/cache/recovery/block.map`: referencia el mapa ausente. [Inspección del original](RECOVERY-ORIGINAL.md).
- Una única SIGQUIT a system_server identificado produjo una traza Java de 107301 B, SHA `af90d91809cf26af69b54dde9e91f455e999f9e00cb461ad2d8bb71ed7f9f94c`. [Análisis con líneas y código real](ANALISIS-UPDATE-012.md).
- La cadena observada es ShutdownThread → Future de BatteryStats → consulta síncrona al hilo WiFi → arranque del HAL esperando respuesta. No es un problema de batería física; el servicio de consumo espera estadísticas de WiFi. La traza no localiza la instrucción dentro del proceso HAL o del driver.

La captura Java no consultó BatteryStats mediante Binder. ART pudo pausar brevemente los hilos y escribió su informe de diagnóstico; eso se distingue de una simple lectura de archivos. No se repitió la consulta BatteryStats rechazada anteriormente.

## Respaldo

**Doce particiones seleccionadas verificadas**, con lectura de PC y SHA remoto iguales: ocho particiones críticas, 102 MiB, y system/vendor/product/odm, 2436 MiB. Ambas etapas terminaron con código 0; suman 2538 MiB, aproximadamente 2,66 GB. No incluyen datos/cache ni toda la eMMC y no hay restauración probada. [Resumen del respaldo](RESPALDO-resumen-saneado.json).

Se preparó [respaldar-p291-lan.py](../respaldar-p291-lan.py), de solo lectura. Valida perfil, UID, compilación, arranque, aliases, tamaños y montajes. Guarda imágenes en una carpeta privada nueva de la PC, comprueba hashes contra el TV y conserva cualquier lectura fallida como `.parcial`. No accede al pendrive ni remonta o escribe particiones.

Las etapas cubren ocho particiones críticas y cuatro particiones de sistema RO. No incluyen userdata/cache ni todas las áreas de la eMMC, no son un snapshot atómico del equipo y no hay restauración probada. El recibo de cada ejecución determina qué terminó; la mera existencia del script no acredita respaldo. El respaldo de misc conserva la preparación del Update ya ocurrido, no un estado anterior al intento.

## Lección de adquisición

En esta combinación de Windows/ADB, `shell -T` alteró los saltos de línea de la traza: 108967 B y hash distinto. Esa copia se conservó como fallida. La lectura mediante `exec-out` dio 107301 B y hash remoto exacto. Para binarios se utiliza exec-out y un marcador aleatorio al final que permite comprobar el código remoto real; el código 0 del transporte por sí solo no demuestra éxito del comando. No normalizar imágenes binarias.

## Estado

No se preparó aún el mapa, no se ha forzado otro reinicio ni se instaló la ROM 0.1.2. Los originales seleccionados quedaron respaldados y el recovery real fue revisado; sus diferencias con el candidato requieren preparar una imagen compatible antes de concretar la intervención forzada. Root amplía lo posible, pero no acredita recuperación desde un TV que deje de arrancar.

## Copia interna retirada del intento pendiente

Después de detectar las diferencias de arranque/firma y del pedido del usuario de decidir antes de forzar, se preservó el ZIP como `/data/cache/TVBASE-0.1.2-preservada-no-instalar.zip`. Se comprobó antes que no existían block.map ni un proceso uncrypt activo y que el tamaño/hash eran los correctos. El renombrado terminó con código 0; la ruta activa `/data/cache/update.zip` quedó ausente y el archivo conservado volvió a verificarse por SHA. No se borró el ZIP, no se escribieron boot/system/vendor ni se pidió reinicio.

Esto retira el archivo que consumiría el intento OEM si la espera se liberara. **No cancela el hilo Java ni limpia BCB**: la orden de boot-recovery y uncrypt_file siguen referenciando la preparación anterior. El TV puede seguir mostrando 2%; no presentarlo como cancelación completa del arranque ni indicar un corte asumiendo BCB limpio. El pendrive y la release en PC permanecen intactos.
