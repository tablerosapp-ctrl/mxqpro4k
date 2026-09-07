# Opciones de instalación con el acceso root existente

7/9/2026. Documento para decidir el siguiente paso en el **primer P291, DT `gxlx2_p291_1g`**. Se confirmó acceso root mediante el `su` ya presente; no se instaló root ni se cambió la autenticación ADB. La preparación manual, SysRq y USB Burning descritos aquí **no se han ejecutado**. Están verificadas doce particiones seleccionadas: ocho críticas, 102 MiB, y cuatro de sistema, 2436 MiB. Suman 2538 MiB, aproximadamente 2,66 GB. No incluyen datos/cache ni toda la eMMC. [Recibo saneado](RESPALDO-resumen-saneado.json). No hay restauración probada.

**Revisión posterior del recovery original:** la firma SHA256 del ZIP 0.1.2 no está acreditada bajo la clave v1, y su boot contiene cambios reales de geometría/IRQ/video. [Comparación exacta](RECOVERY-ORIGINAL.md). Las opciones de abajo requieren antes una imagen coherente con el P291; no proponemos forzar 0.1.2 ni resolverlo solo con otra firma. La propuesta preferente es derivar la ROM de los originales respaldados.

## Qué cambió con el diagnóstico

La captura del primer TV muestra esta cadena: cierre de Android → BatteryStats → consulta síncrona a WifiStateMachine → espera de respuesta del HAL WiFi. BatteryStats registra consumo de energía; su nombre no demuestra que exista una batería física averiada. El punto interno del HAL/driver sigue pendiente. El ZIP 0.1.2 copiado a `/data/cache/update.zip` tiene el hash esperado; la orden de actualización referencia un `block.map` que todavía no existe. Por ello falta preparación aunque el archivo de la ROM ya esté completo. [Evidencia y límites](ANALISIS-UPDATE-012.md).

Root permite leer el estado original y preparar una ruta que evite el cierre Java bloqueado. No demuestra que el recovery arranque, que acepte el ZIP ni que un reinicio normal supere el cierre del kernel.

| Opción | Qué resolvería | Qué falta acreditar | Riesgo principal |
| --- | --- | --- | --- |
| **1. Preparación manual y recovery original** | Preparar mapa/orden sin depender de BatteryStats y usar el instalador interno. | Recovery original compatible, mapa persistido y entrada efectiva a recovery. | Preparación parcial o reinicio bloqueado; instalación sin retorno automático probado. |
| **2. Reset de emergencia después de preparar** | Intentar evitar las esperas del cierre normal para que el cargador vuelva a arrancar. | Interfaz SysRq presente; reset físico, preparación completa y respeto de la orden todavía por probar. | Pérdida de escrituras/corrupción; puede volver a Android o seguir sin imagen. |
| **3. Grabación Amlogic por USB desde PC** | Trabajar antes de Android mediante BootROM/cargador compatible. | Cable/puerto de datos, enumeración USB, perfil exacto de placa y contenedor de imagen. | Cargadores DDR o distribución de memoria incompatibles pueden impedir el arranque. |

## Primero: conservar y comprobar el estado original

1. Resolver los nombres de partición contra los dispositivos y tamaños reales. Obtener copias verificadas de recovery, boot y los componentes críticos de arranque que existan en el mapa del P291; conservar también el estado de `misc`/BCB y los archivos de preparación de cache. No extrapolar offsets o aliases del P271 ni del candidato.
2. Registrar tamaño, códigos de lectura y SHA256 de cada copia; comparar lectura del TV y archivo de PC. Identificar por separado lo que no pudo leerse. Un respaldo de particiones críticas no es un respaldo completo de aplicaciones/datos, ni demuestra que exista una vía para restaurarlo.
3. Abrir **en PC** el recovery original: examinar kernel/DT, fstab, ejecutable y claves de paquetes. Comparar con el ZIP firmado 0.1.2 y con los tamaños/dispositivos previstos por su instalador. La validación previa contra el certificado OTA del Android activo no sustituye la comprobación contra las claves de este recovery.
4. Conservar la copia interna del ZIP sin modificar mientras se evalúa su mapa. Documentar qué orden queda persistida y qué se esperaría del próximo arranque, incluida cualquier opción de borrado. Resolver las diferencias antes de elegir una intervención.

El respaldo seleccionado y la comparación de recovery/boot ya se completaron; detectaron las diferencias descritas al inicio. La copia interna del ZIP fue preservada con otro nombre, sin cancelar el hilo Java ni limpiar BCB; [estado exacto](ROOT-RESULTADO.md). La imagen compatible, la preparación que escriba mapa/BCB y el método de arranque se concretarán después; documentarlos no equivale a haberlos ejecutado.

## 1. Preparar manualmente y utilizar el recovery original

La propuesta es emplear el mecanismo de `uncrypt` del sistema para preparar el paquete fuera de la secuencia de cierre bloqueada, y verificar después la orden de arranque. En AOSP son operaciones diferentes: preparar BCB no crea por sí mismo el mapa del paquete. Se debe contrastar el binario/servicio original del P291 antes de usar sus parámetros. [Análisis del actualizador y referencias AOSP](ANALISIS-UPDATE-012.md).

La secuencia revisable sería: conservar el estado previo; confirmar el ZIP; generar el mapa mediante la implementación original; comprobar dispositivo, tamaño de bloque, rangos, tamaño del paquete y persistencia; comprobar que la orden BCB referencia exactamente ese mapa y no introduce un borrado no previsto. Cuando sea técnicamente posible, verificar que la lectura por esos rangos reconstruye el mismo ZIP. La ejecución de `uncrypt` y la escritura de BCB son operaciones con efectos persistentes, no simples consultas.

Solo después se evaluaría la entrada a recovery. Un reinicio directo puede evitar ShutdownThread de Java, pero todavía pasar por notifiers y `device_shutdown()` del kernel. Por eso completar el mapa no garantiza resolver los apagados sin señal. [Análisis de ambas rutas de cierre](../../docs/hipotesis/H1-RESULTADO-CODEX.md).

**Condición para continuar:** imagen compatible, respaldo aceptado, recovery original revisado y preparación verificable. Una falla de preparación detiene esta vía antes de reiniciar. La próxima receta debe conservar las comprobaciones y respaldos aplicables del instalador anterior, adaptados y verificados contra los originales; no se propone omitirlos. [Antecedente de la ROM sin Bluetooth](../../rom-simplificada/SIN-BLUETOOTH-0.1.2.md).

## 2. Evaluar un reset de emergencia, con la preparación ya validada

Esta opción complementa la anterior: **un reset no crea `block.map` ni instala una ROM**. En Linux 4.9 de referencia, SysRq `b` llama a `emergency_restart()`; esa ruta no atraviesa la preparación normal con `device_shutdown()`. Eso fundamenta la hipótesis de evitar ese cierre, pero no prueba la implementación final del kernel Amlogic instalado ni el resultado del reset. [SysRq de Linux 4.9](https://raw.githubusercontent.com/torvalds/linux/v4.9/drivers/tty/sysrq.c), [rutas de reinicio de Linux 4.9](https://raw.githubusercontent.com/torvalds/linux/v4.9/kernel/reboot.c).

**La interfaz `/proc/sysrq-trigger` existe y es escribible por root; no se disparó ninguna operación.** La lectura de `/proc/sys/kernel/sysrq` dio 0. La documentación distingue ese control del teclado de la interfaz privilegiada `/proc/sysrq-trigger`; 0 no prueba que root no pueda invocarla. No se cambió ese valor. La presencia de la interfaz no acredita que el hardware vaya a reiniciar correctamente.

La documentación del kernel establece que `b` reinicia sin sincronizar ni desmontar. `s` intenta sincronizar y `u` intenta remontar los sistemas de archivos como solo lectura; se exige observar su finalización, no asumirla por haber enviado una petición o esperado unos segundos. Esas operaciones también pueden quedar pendientes. No se han ejecutado aquí. [Documentación oficial de SysRq](https://docs.kernel.org/admin-guide/sysrq.html).

Antes de plantear este reset deben estar cerrados los respaldos, la revisión del recovery y la preparación persistida de la opción 1. Aun así, puede haber pérdida de datos recientes, corrupción o un arranque que no siga BCB: este mecanismo no transporta por sí mismo el argumento `recovery`. Si falta evidencia de sincronización, esa incertidumbre debe quedar expresamente presentada en la decisión; no se convertirá en éxito mediante un timeout. Se omiten comandos ejecutables para no transformar este análisis en una instrucción de reinicio.

## 3. USB BootROM/Burning desde la PC

Esta ruta utiliza un enlace USB de datos PC–TV antes de Android. LAN permite el diagnóstico actual, pero no transporta la enumeración ni el protocolo BootROM. El dossier identifica tres USB-A y no establece cuál permite modo dispositivo. En algunas placas Amlogic el enlace requiere un cable especial A–A al primer controlador USB; hay que identificar el puerto y la alimentación adecuados del P291 antes de conectar. No se deduce su disposición a partir de una placa Khadas ni se propone puentear pines. [Flujo de arranque documentado por U-Boot](https://docs.u-boot.org/en/latest/board/amlogic/boot-flow.html).

El primer objetivo sería detectar el dispositivo y registrar VID/PID. Si coincide con el protocolo compatible, puede limitarse el sondeo a `identify`, una consulta USB de entrada; no cargar DDR/U-Boot ni escribir almacenamiento durante esa identificación. Reconocer el dispositivo no prueba que pueda respaldar/restaurar eMMC. P291 no figura entre las placas comprobadas de la herramienta abierta. [pyamlboot](https://github.com/superna9999/pyamlboot), [implementación de identificación](https://github.com/superna9999/pyamlboot/blob/master/pyamlboot/pyamlboot.py).

El ZIP recovery 0.1.2 **no es una imagen Burning**. El candidato original contiene un contenedor Amlogic V2 con cargadores DDR/UBOOT y particiones; producir una variante 0.1.2 requiere recomponer y verificar ese formato y su perfil de placa. La imagen experimental 0.1 anterior no representa los cambios 0.1.2. El nombre comercial S905L2 sigue sin resolver por sí solo la variante: el DT confirmado es `gxlx2_p291_1g`, mientras el candidato declara S905L3. No elegir un perfil genérico GXL/VIM por semejanza. [Inventario local del candidato](../../analisis-rom/RESULTADO.md), [formato del contenedor](https://raw.githubusercontent.com/superna9999/pyamlboot/master/AML-IMAGE-FORMAT.md), [procedimiento de Khadas para su propia placa](https://docs.khadas.com/products/sbc/vim1/install-os/install-os-into-emmc-via-usb-tool).

El wrapper Khadas `flash-tool --parts=none` **no es un sondeo de solo lectura**: puede emitir `erase_bootloader`/`reset` y cargar código en RAM. Su comentario sobre el efecto de `erase_bootloader` no acredita lo que hará el cargador del P291. No se usará para una detección inocua. [Código del wrapper](https://github.com/khadas/utils/blob/master/aml-flash-tool/flash-tool).

Se puede preparar offline el inventario de cargas, la comparación con los originales y un sondeo limitado a identificación. La grabación requiere primero demostrar el enlace/modo y resolver el perfil DDR/cargador, preservando los originales y las particiones ajenas a la receta. [Límites ya acordados de recuperación](../../docs/hipotesis/H2-PREPARACION-RECOVERY.md).

## Lo que no constituye una opción lista

Sobrescribir `system` o `vendor` mientras el Android que los utiliza sigue montado y ejecutándose expone código y sistemas de archivos a cambios parciales; tener root no elimina ese problema. No se presenta como atajo listo ni se propone escribirlos en vivo. Tampoco hay rollback automático, recovery arrancado o recuperación de WiFi acreditados. La siguiente decisión se apoya primero en el respaldo y la comparación del recovery original, y conserva las incertidumbres que continúen abiertas.
