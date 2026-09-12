# Estado operativo

## Colaboración mediante Drive · 12/9/2026

Se revisa la carpeta que el usuario ya subió para Fable y se prepara acceso local de lectura y descarga selectiva verificada. [Contrato y estado](DRIVE-COMPARTIDO.md). Lo omitido continúa excluido: cualquier subida adicional requiere justificación y OK. No se recibieron nuevos resultados físicos RK3 durante esta revisión ni se contactaron TV/SD/USB. La conexión del conector no equivale a sincronización local continua.

La autorización local de lectura terminó; el inventario falló por el límite de solicitudes del cliente compartido de rclone. Proyecto propio creado, API habilitada, política aceptada por autorización explícita y cliente de escritorio conectado con código 0. Inventario propio de 9.355 archivos / 6.421.648.788 bytes, todos coinciden con SHA local. Descarga de prueba y refresh verificados; modo Prueba de Google, permanencia pendiente. El plan de 5 TB se conserva para archivos propiedad de la cuenta titular. Revisión horaria creada solo para la selección actual de un informe de prueba; no es sincronización de toda la carpeta.

## Relevo actual a Fable

El usuario continuará con Fable después de probar RK3. [Guía completa de continuidad](ENTREGA-FABLE.md): estado por equipo, artefactos y hashes, corrección aplicada, adquisición posterior, interpretación de éxito/fallo, pendientes e historial. Resultado físico RK3 todavía no comunicado; no se modificaron TV, SD ni artefactos durante este relevo documental.

## Vigente · RK3 entregado; backup se intenta al final

El extractor0.2/RK2 funcionó desdeSD y copió4MiB de `parameter` correctamente. Se detuvo en64MiB de `backup` porque dos lecturas del origen dieronSHA distintos. La captura parcial quedó conservada y verificada enPC; las doce fuentes posteriores no se intentaron. [Evidencia](evidencia/ERROR-RK2-BACKUP-C.md).

Por indicación del usuario, **0.3/RK3 no excluye backup: copia las otras particiones antes y lo intenta al final mediante RAM**, con dos lecturas de origen iguales antes de guardar y verificarSD. El paquete está compilado, revisado y copiado/releído; siete archivos anteriores siguen iguales y el Kingston no cambió. [Entrega y límites](evidencia/EXTRACTOR-SD-03.md).

**Siguiente:** soloSD, en el mismo RK3229-C: recovery → Apply update from SD card → update.zip. Esperar cierre y devolverSD tras expulsar. Ante error conservartexto sinrepetir/wipe. No usarA/B/P271. La ejecución físicaRK3, respaldo de las demás particiones y restauración permanecen pendientes. Home, WebView, auditoría y capa común no se modificaron.

## Antecedente · entrega RK2 antes de la prueba física

## Vigente · extractor SD0.2/RK2 preparado para C

El recovery real aceptó y ejecutó RK1, pero el extractor no encontró un destino USB válido y abortó antes de crear una captura. [Evidencia](evidencia/ERROR-RK1-DESTINO-USB.md). No hay respaldo nuevo de Rockchip en ese intento.

Por pedido del usuario se preparó **0.2/RK2 con carga y copias en la misma SD**. Compilación, firma, revisión y entrega están verificadas en PC. Kingston se conservó; se archivaron los dos archivos anteriores de SD antes de sustituirlos, sin formato. [Entrega y alcance](evidencia/EXTRACTOR-SD-02.md).

**Siguiente:** usar solo SD en el último RK3229-C, recovery CNV8b.20230725; Apply update from SD card → update.zip. Esperar cierre, conservar error sin repetir/wipe y devolver SD a PC tras expulsarla desde Android. No usar todavía en A/B. La copia física0.2, su adquisiciónPC y restauración siguen pendientes; aceptaciónRK1 no equivale a éxitoRK2.

## Antecedente · preparación RK1 antes de la prueba

## Vigente · SD RK1 y Kingston preparados para extraer RK3229-C

La SD de8GB quedó FAT32 TVBASESD, con extractor RK1 idéntico como `update.zip` y guía; ambos archivos fueron copiados, sincronizados y releídos. El Kingston de32GB se conservó como destino con el plan C existente. [Entrega y recibos](evidencia/SD-RK3229-C.md). El [recibo final](../preparacion-usb/sd-rk3229-c-final-estado.json) acredita DiskPart terminado y comprobaciones independientes de MBR, geometría y FAT32; la [entrega](../preparacion-usb/sd-rk3229-c-entrega-estado.json) acredita las dos copias.

Se conservaron los fallos anteriores: Clear-Disk dejó MBR sin particiones y se detuvo una guarda; luego se canceló una elevación. Tras el aviso «estoy», el continuador puso a cero y releyó96MiB, pero Windows expuso una partición de todo el medio desdeoffset0 y otra guarda abortó. La interpretación como superfloppy es compatible con documentación Microsoft, no una causa confirmada. La finalización separada usó DiskPart y verificó el resultado; no se repitieron los preparadores ni se reescribieron sus recibos.

El recovery del firmware aportado coincide en compilación con la foto y exige clave Rockchip v3/SHA256. RK1 conserva el ejecutable ARM32 0.1; firma y contenido están comprobados en PC. El ELF usa ruta fija SD/update.zip e intenta montar USB al inicio cuando `argc <= 1`; falta observar ese montaje en C. [Análisis y límites](evidencia/RECOVERY-CNV8B-SD.md). Aceptación del ZIP y extracción física siguen pendientes; preparar los medios no cierra VAL-12.

Siguiente: expulsar ambos medios en Windows, conectarlos al último C antes de entrar al recovery y elegir Apply update from SD card → update.zip. Mantener alimentación y medios hasta terminar; conservar el resultado. No wipe, Recovery System ni instaladores P291. Tras volver al menú, reiniciar Android y expulsar el almacenamiento; devolver Kingston a PC antes de cambiar a A/B. No repetir ninguna preparación completada.

## Antecedente · SD sin particiones y elevación Windows cancelada

El respaldo anterior de la SD está guardado. El formato se detuvo tras quitar la partición porque Windows conservó MBR en su estado. El continuador nuevo está listo, pero Windows canceló la solicitud de administrador; el proceso no llegó a iniciarse. No hay una continuación activa. Hace falta volver a mostrar esa solicitud cuando el usuario pueda aceptarla. Kingston sigue conservado. [Detalle y entregable preparado en PC](evidencia/SD-RK3229-C.md). No retirar medios hasta comprobar el cierre y la copia. La guía final aún no está copiada a la SD.

## Antecedente · selección de USB C

## Vigente · RK3229-C capturado; paso a extraer originales

La copia manual del último Rockchip llegó íntegra: dos ZIP de 41.155 B en total y dos recibos locales conservados y comprobados en PC. Son ficha inicial e inventario de la misma instalación APK. [Hallazgos C](../diagnostico/reconocimiento-20260908-rk3229-manual/HALLAZGOS.md). No necesita repetir reconocimiento. La selección USB funcionó según el usuario, pero la escritura automática no; la transferencia manual está comprobada por la lectura en PC.

Tenemos P291 instalado, P271 reconocido y tres configuraciones RK3229 distintas. [Matriz y efecto sobre Android/WebView](MATRIZ-PERFILES.md). C es el último equipo, MBOX/CNV8b.20230725, eMMC Q7XSAB. El usuario confirmó que puede abrir su recovery. Se selecciona este para la primera extracción con el ejecutable ARM32 0.1 ya construido, sin rehacerlo. El plan solo asocia el informe candidato; no prueba identidad física ni fija offsets. Solo un plan RK puede quedar activo porque A/B/C anuncian el mismo DT.

La [preparación C](../preparacion-usb/preparar-extraccion-rk3229-c.ps1) agrega plan y guía conservando los archivos anteriores. La [entrega](evidencia/EXTRACCION-RK3229-C.md) terminó código0: dos archivos nuevos, 5078B; anteriores conservados, 23.270.916.096B libres. No repetir el preparador. La aceptación del ZIP, lectura en recovery e imágenes C permanecen pendientes. No usar los instaladores P291 ni Update de Android para esta captura. Después de C, devolver el USB para verificar y cambiar el plan antes de A/B. No existe todavía una ROM RK construida.

## Antecedente · entrega0.3

## Vigente · RK3229-A/B capturados; corrección0.3 entregada

[Cinco ZIP verificados](../diagnostico/reconocimiento-20260908-rk3229-usb/HALLAZGOS.md): P271 histórico más dos fichas iniciales y sus inventarios RK3229. Diferencias de firmware, WiFi y particiones; igual DT no autoriza intercambiar ROM. API25/fingerprint7.1.2 contradicen etiquetas11.1/13.0; RAM anómala en una variante. Los cuatro nuevos ZIP suman84.222B, sin imágenes de bloques por diseño. No repetir estas capturas.

El equipo que no guardó es otro Rockchip según el usuario, con carcasa igual y sin DT exacto. Fotos0.2 acreditan selector Android ausente y ficha inicial local. [Reconocedor0.3](../diagnostico/reconocedor-0.3/README.md) y guía copiados/releídos en Kingston, [recibo](../preparacion-usb/reconocimiento-03-estado.json); fuentes/recibos sellados. Selector propio, búsqueda acotada y alternativa explícita Descargas para copiar manualmente con Archivos. Una copia local nunca se declara USB. [Pruebas y entrega](evidencia/RECONOCEDOR-USB-03.md). Ejecución Android0.3 pendiente; no garantía de acceso siAndroidloimpide.

Siguiente: actualizar0.3 soloelTVfallido, conservar datos y completar su ficha; si usaDescargas copiarTVBASE-PARA-COPIAR alUSB. Próximarecepción revisar esa carpeta eINFORMES. No preparar dos planes RK conigualDT; no se añadieronplanes. Entrada/firma/ejecuciónrecoveryRK/P271 y copia profunda siguenpendientes. SinTVcontact, formato, borrados o nuevasROM. Home/multimedia/limpieza/auditoría/servidor permanecen fuera deestaentrega.

## Antecedente · corrección0.2


## Vigente · captura P271 verificada; reconocedor0.2 preparado para MX9

El USB volvió con un informe P271 íntegro y sin informe MX9 ni extracción desde recovery. [Hallazgos](../diagnostico/reconocimiento-20260908-p271-mx9/HALLAZGOS.md). La captura P271 agrega mapa sysfs con inicios y 157.174.723 bytes de archivos accesibles. No equivale a un respaldo de particiones. P271 difiere de P291 en memoria y WiFi; no reutilizar su ROM.

[Reconocedor0.2](../diagnostico/reconocedor-0.2/README.md) construido y entregado: ficha inicial exportada antes del inventario, sin copias masivas de drivers/DT, consultas con un solo trabajador real y sin escrituras tardías. [Evidencia y pruebas](evidencia/RECONOCEDOR-USB-02.md), [reciboUSB](../preparacion-usb/reconocimiento-02-estado.json). APK90515B más guía y planP271 copiados/releídos; todos los archivos anteriores conservados. No repetir preparador ni modificar fuentes/recibo sellados. No hay prueba física0.2 todavía.

Siguiente: actualizar APK del MX9 desde TVBASE-RECONOCIMIENTO, capturar, esperar inventario guardado y devolver USB expulsado. El usuario confirmó más de15min sin progreso en0.1. La foto no permite conocer SoC ni operación bloqueada; 0MB era compatible con redondeo. P271 no necesita repetir captura; su plan ya está derivado y en el USB. Entrada/firma/ejecución de recoveryP271 pendientes. No usar Update/AccesoUSB09/ENV/BCB ni ROMP291 en otros perfiles por semejanza. Home, capa común, video/WebView, auditoría de servicios y servidor siguen pendientes.

## Antecedente · entrega inicial del modo combinado


## Vigente · modo combinado y extractor0.1 entregados

El usuario aprobó APK de identificación y paquete independiente para extraer originales desde recovery según esa información. [Contrato](../diagnostico/extractor-recovery-0.1/README.md) · [Entrega verificada](evidencia/EXTRACTOR-RECOVERY-01.md). DosZIP ARM32/ARM64 compilados, firmas Python/OpenJDK y copia/relectura Kingston comprobadas. La APK anterior y todos los respaldos permanecen; nueva carpeta TVBASE-EXTRACCION con CAPTURAS/PLANES vacíos. Recibo extractor-01-estado.json código0; no repetir preparador ni modificar la guía sellada.

**Siguiente:** primera captura APK en P271/TV elegido, importación y plan derivado del ZIP íntegro. Después comprobar entrada/firma/ABI del recovery y ejecutar solo extractor adecuado. Sin plan coincidente guarda inventario, sin imágenes. No hay captura física del extractor, nueva APK recibida ni aceptación P271/Rockchip. No ejecutar Update/AccesoUSB09/ENV-BCB P291 a ciegas para reconocer. Las guardas abren fuentesRO, validan mapa real y omiten áreas ocupadas/desconocidas; no desmontan, formatean, flashean ni reinician.

**Nueva prioridad para la etapa de producto:** [telefonía, mensajes, contactos, llavero e Intent Filter Verification Service y resto del software heredado](REVISION-COMPONENTES-HEREDADOS.md). Revisar identidad/dependencias y tráfico/malware; ningún servicio retirado y ninguna clasificación de malware basada solo en su nombre. Home, WebView de la APK, rendimiento, servidor y nueva ROM siguen pendientes.

La autorización de extracción amplía la captura de Android; no autoriza esta vez instalar otra ROM ni cambiar el recovery. La siguiente sección documenta la primera entrega APK, que sigue conservada.

## Vigente · reconocedor 0.1 construido y entregado en Kingston

El usuario autorizó implementar el reconocimiento y preparar el USB para varios TV consecutivos. [Reconocedor](../diagnostico/reconocedor-0.1/README.md) · [Entrega y pruebas](evidencia/RECONOCEDOR-USB-01.md) · [Recibo USB](../preparacion-usb/reconocimiento-01-estado.json).

APK106899B, SHA f631d5a16fa26266276f3be6f7f1e9f924ff95ea26dd922ff18f105022e1d813, paquete `com.tvbase.reconocimiento`, API21+/target28. Es una aplicación normal sin root, ADB, red, reinicio o instalación de ROM. Recoge observaciones Android y copias seleccionadas de archivos estáticos legibles, registra límites y guarda un ZIP único por captura. Nombre sugerido por perfil y UUID local de instalación; no prueba identidad física ni compatibilidad para flashear.

Kingston: nueva carpeta TVBASE-RECONOCIMIENTO con tres archivos verificados e INFORMES vacío; archivos anteriores conservados. Preparación única terminó código0. No se repite ni se formatea. Ya se indicó expulsarlo de Windows; no se observó esa retirada ni se acredita flush de volumen. Primera ejecución física de la aplicación y sus proveedores USB pendiente.

Próximo paso: una captura en el P291 conocido, luego otros Android si el primer guardado funciona; cada resultado permanece separado. Ante exportación fallida usar la copia local terminada, no repetirlecturas por rutina. Al volver USB a PC, verificar/importar ZIP a un directorio privado nuevo. Un error de acceso se considera dato pendiente, no ausencia de hardware. Cambios Home/ROM/servidor no incluidos en esta entrega.

La espera de OK de las secciones inferiores fue superada para reconocimiento por la instrucción posterior del usuario. Las evidencias de instalación del P291 permanecen vigentes con sus límites.

## Antecedente · planificación previa al reconocedor

## Vigente · 8/9/2026, P291 funciona sin USB; reconocimiento como siguiente entregable

El respaldo también está [publicado cifrado en GitHub](RESPALDO-GITHUB.md): nueve partes y manifiesto verificados, con la clave privada separada en esta PC. Se probó recuperar los archivos en PC; esto no acredita restauración física del TV.

**TV Base arrancó en el primer P291. La instalación 0.2.2 y los seis respaldos están verificados; el usuario confirma que puede conectarse por WiFi. Queda pendiente el botón Home del control.** La foto acredita el launcher y los recibos recuperados acreditan el cierre del instalador. El usuario prueba su APK; no se accedió al TV durante esta revisión.

| Área | Resultado |
| --- | --- |
| Instalación 0.2.2 / plataforma 0.2.0 | Seis respaldos, formato correcto y userdata vacía antes de instalar. Cinco escrituras verificadas por lectura, con boot al final. |
| Conservación | 199 archivos y 6.091.261.673 bytes guardados y verificados en PC. Los seis respaldos suman 6.067.060.736 bytes, incluida userdata. El USB se leyó sin limpiarlo ni escribir en él. |
| Arranque | TV Base visible en la foto. El usuario confirma varios reinicios correctos sin pendrive; cantidad y tipo de ciclo no especificados. |
| Red | El usuario confirma que puede conectarse por WiFi. Estabilidad, navegación y distintas redes pendientes de prueba específica. |
| Control | ISSUE-HOME-01: casita/Home no vuelve al inicio. Prioridad funcional siguiente. |
| APK y multimedia | El usuario sigue probando. Faltan comprobar el proveedor WebView efectivo y el rendimiento con dos videos VP9, uno con transparencia, más canvas. |
| Recuperación y actualizaciones | Restaurador de cinco particiones OEM preparado, sin ensayo físico ni recuperación automática. Conserva userdata; no recupera su respaldo. Gestor integrado y desactivado; nuevas actualizaciones pendientes. |

[Evidencia física](evidencia/INSTALACION-FISICA-P291-022.md) · [Hallazgos](../diagnostico/primer-tv-instalado-20260908/HALLAZGOS.md) · [Resumen verificado](../diagnostico/primer-tv-instalado-20260908/resumen-saneado.json) · [Incidencia Home](INCIDENCIAS.md).

Los sectores de inicio de las particiones y sus enlaces sysfs con nombres lógicos quedaron registrados durante esta ejecución. La ausencia de esas capturas en documentos anteriores corresponde a su fecha; no se deben reescribir los recibos sellados. El error de 0.2.1 quedó superado por 0.2.2 y no reapareció en esta instalación. El reloj del TV marcaba 2020: impide fechar la operación con fiabilidad y calcular su duración total exacta.

**Límite de trabajo vigente:** documentar, guardar evidencias y proponer. El usuario pidió no ejecutar el trabajo siguiente sin su OK explícito. Esto prevalece sobre la autorización general anterior para continuar instalando. No modificar el TV, instalar otra ROM, corregir Home, configurar el servidor ni aplicar un modo rápido ahora.

La [propuesta PROP-16](PROPUESTA-LOTES-Y-ACTUALIZACIONES.md) distingue producto, perfil de hardware e identidad de cada unidad. Separa la calificación de nuevos lotes de la instalación rápida de unidades que coincidan. Optimizar los respaldos y las actualizaciones por componente requiere una política explícita; no se clonan datos específicos de otra unidad ni se omiten comprobaciones de integridad. Ningún ahorro de tiempo está medido todavía.

La [revisión local de Home](hipotesis/HOME-P291.md) propone comprobar la configuración inicial y la traducción de la tecla. Son hipótesis: no se conocen esos datos actuales del TV ni hay una corrección probada.

M2 tiene instalación y primer arranque observados, ahora ampliados por [varios reinicios sin pendrive informados por el usuario](evidencia/REINICIOS-P291-SIN-USB.md). VAL-06 tiene respaldo, formato y escrituras comprobados por los recibos y la adquisición. VAL-07 sigue parcial: pruebas de hardware, proveedor WebView y estabilidad medida pendientes. El informe no especifica desconexiones de alimentación. M3 incluye Home y multimedia; M4, con reentrada y restauración, sigue pendiente.

**Prioridad reformulada por el usuario:** [PROP-17](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md) propone primero reconocimiento sobre Android para varias familias, con informes y permisos explícitos; después instalación rápida por perfil. El producto común con logo, auditoría de recursos/tráfico, proveedor WebView real y actualización remota se diseñan juntos. USB e Internet deben compartir catálogo/compatibilidad, con operaciones distintas para conversión OEM y actualización conservando datos. Orden de bases: P291 → P271 → Rockchip por identificar. REQ-18 y ADR-29 registran el alcance. Son cambios documentales; no hay nuevos programas ni pruebas en el TV o pendrive.


## Historial conservado: los estados siguientes son anteriores

## Antecedente · 7/9/2026 ART, ROM original P291 0.2.0 verificada en PC

La autorización de construir desde los originales se implementó en [original-p291](../rom-simplificada/original-p291/README.md). Las cinco imágenes conservan geometría real, kernel y multi-DTB; los archivos ajenos al recorte conservan bytes, dueño, modo y atributos. Se retiran 51 APK y quedan 34 originales más Chrome y cuatro componentes propios. [Evidencia y grafo del cambio](evidencia/ROM-ORIGINAL-P291-020.md).

- Instalación: `TVBASE-P291-A9-0.2.0-RECOVERY.zip`, 573492264 bytes, SHA256 `bd4a8dd7df8d61580c5b450867bda2ef2b214b400b4cafcce5a26baa5c48a614`.
- Restauración de cinco particiones originales: `TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.0-RECOVERY.zip`, 913228907 bytes, SHA256 `a10aee68042ef9f945a4160fd897d0db1943e28dd58e0a03918d138e9f1a8e3f`.
- Gestor 0.1: 57810 bytes; revisión exacta y 38 pruebas host. Incluido como priv-app con INSTALL_PACKAGES; desactivado, sin URL ni clave pública de servidor. APK y Chrome, sin OTA completa ni administración de videos todavía.

Los dos ZIP superan CRC, hashes de payload, validador del instalador y firma integral Python/OpenJDK acorde a la clave v1 del recovery real. **No se ejecutó recovery ni se instaló/restauró una ROM. No se modificaron TV ni USB durante esta construcción.** La última copia física sigue siendo 0.1.2 histórica; no se debe repetir su Update.

La receta elimina Play/GMS, precargas, reinstalador OEM, entrada remota prescindible, Bluetooth, su/procmem elevados y consola. Desactiva depuración por USB/red inicial y exige autenticación ADB. Conserva drivers WiFi/video/red/IR/CEC y empieza con WiFi apagado. No acredita reparar el bloqueo del driver. El framework original, SELinux permisivo y firma de plataforma heredada siguen siendo límites experimentales; falta observación de tráfico por proceso.

**Trabajo necesario antes de instalar:** entrada a recovery y ruta de paquete comprobadas; preparación revisada de userdata según lo que haya que conservar. El instalador exige /data de solo lectura y realmente limpia; no hace el borrado ni acepta un marcador como sustituto. El ZIP de restauración repone las cinco imágenes OEM, incluido su software, conservando userdata; no tiene rollback automático ni restauración física probada. Después se validan arranque interno, ajustes, APK por USB, Ethernet/WiFi, dos VP9/alfa/canvas, proveedor WebView y actualizaciones propias.

El último estado persistente observado del TV no cambia por construir archivos en PC: el ZIP0.1.2 quedó preservado fuera de la ruta activa, pero BCB y el hilo Java no fueron cancelados. No indicar un corte o reset suponiendo vuelta segura a Android. [Opciones conocidas](../diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md).

## Antecedentes fechados: lo siguiente describe revisiones previas

## Vigente · 7/9/2026, root y espera del servicio WiFi

[Root ya confirmado](../diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md), solicitado ahora por el usuario: el su incorporado devuelve UID 0. No se instaló root ni cambió la autenticación. La traza Java identifica ShutdownThread → Future de BatteryStats → consulta WiFi → IWifi.start esperando respuesta. [Detalle verificable](../diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md). Root lee el ZIP interno íntegro y demuestra que block.map falta. Las denegaciones descritas abajo corresponden al acceso shell anterior.

El respaldo de doce particiones seleccionadas está verificado en PC: ocho críticas, 102 MiB, y cuatro de sistema, 2436 MiB; ambas etapas terminaron con código 0. Total: 2538 MiB, aproximadamente 2,66 GB. No incluye datos/cache ni toda la eMMC y no hay restauración probada. No se ha ejecutado escritura de particiones ni otro reinicio. El usuario pidió las opciones forzadas y sus riesgos antes de decidir; no pasar directamente a flashear o a un reinicio de emergencia.

La copia del ZIP 0.1.2 se preservó con otro nombre en `/data/cache/TVBASE-0.1.2-preservada-no-instalar.zip`; SHA comprobado y ruta activa ausente. No se flasheó ninguna partición. Esto impide consumir ese archivo por la ruta antigua, pero **no limpia BCB ni cancela el hilo Java**. No inferir que un corte vuelva a Android.

La revisión del recovery y boot originales detecta una firma SHA256 no acreditada por la clave v1 de recovery y cambios reales en DTB: vendor 900 → 320 MiB, IRQ WiFi 89 → 100, SDIO y reservas de video. [Detalle](../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md). No forzar 0.1.2 ni corregir solo la firma. PROP-15 propone una nueva ROM desde los originales, conservando perfil/video, sin asegurar la reparación de WiFi.

La [ROM 0.1.2 sin Bluetooth](../rom-simplificada/SIN-BLUETOOTH-0.1.2.md) está construida y entregada en Kingston: [copia y lectura verificada](../preparacion-usb/rom-012-estado.json), 19:12:34 ART, código 0. Se archivaron y verificaron en PC tres archivos viejos antes de retirarlos; informes, recovery y respaldos permanecen. No volver a preparar ni formatear el USB.

El usuario autorizó excluir Bluetooth del primer P291 y conservar WiFi como objetivo. La [observación LAN](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md) revela un panic en la coordinación BT → WiFi. La API normal guardó Bluetooth OFF; quedó actividad residual y se inhabilitó solamente com.android.bluetooth para usuario 0. Tras el apagado físico indicado, volvió Android con otro bootID: el ajuste 0 y el paquete inhabilitado persisten, sin proceso de la APK Bluetooth. Sin embargo, el firmware sigue cargando el módulo Bluetooth y el de WiFi queda en Loading con hilos D. **No está demostrado que el cierre se haya reparado.**

La ROM nueva elimina la pila/HAL/módulo Bluetooth operativo y conserva 170 archivos WiFi, además de boot/product/odm de 0.1.1. Los drivers son distintos de los del TV actual, sin prueba física de corrección. No se instaló TVBASE. El arranque de recovery, la restauración del respaldo, el primer arranque de TVBASE y WebView/video siguen pendientes.

El usuario probó el switch interno de la placa tanto con Android como al conectar alimentación, sin efecto visible. No repetir esa vía ni dar por confirmado que sea RESET. Pasó el pendrive al TV y ejecutó un nuevo Update con ROM 0.1.2; confirmó el 2%. El registro de 19:25:38–40 ART muestra setupBCB reconocido, cierre de ActivityManager y entrada en BatteryStats.shutdown. Después continúa Android sin marcas de avance a PackageManager ni preparación del paquete. La lectura inicial de la pila como shell fue denegada; la posterior traza obtenida con root localizó la cadena de espera descrita arriba. No repetir Update ni inferir instalación de una caída de ADB.

La revisión automática rechazó una reconsulta BatteryStats por riesgo de dejar trabajo atascado: no se ejecutó. Se usaron registros y procesos como alternativa. No repetirla por otro conector.

## Antecedente · captura física0.8 revisada el7/9/2026

El Kingston trajo63archivos:25sellos de datos válidos, etapas1–9 válidas, pero COMPLETO/su SHA/etapa10 vacíos. El usuario vio aviso de éxito: **cierre no persistido, captura parcial con informes útiles verificados**. No repetir0.8. Su código no exigía sincronización antes de avisar; corrección pendiente de implementar/desplegar. [Hallazgos y próximo paso](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md) · [Resumen verificable](../diagnostico/primer-tv-postintento-20260907-183025/resumen-saneado.json).

Se observaron6ANR de Bluetooth en140,477s antes/durante la instalación de la captura, WiFi en activando sin interfaz y timeout de5s en WiFi y BatteryStats. Ambos dumps devolvieron0 con texto de timeout: no son respuestas completas. Pstore nuevo con driver Mediatek Bluetooth SDIO y129CMD53; no contiene el intervalo de cierre. Esto apoya investigar radios/BatteryStats, **sin demostrar la causa del2%** ni resolver mapa/BCB/recovery.

Android está activo con build original y WebViewChrome70. La captura acredita ese estado; el ciclo exacto de vuelta a Android sigue sin identificar. No hay instalación de nuestra ROM ni respaldo del TV confirmados.

El usuario ofreció LAN para lectura en vivo. Próximo paso: primerP291 por cable al router; PC por WiFi sirve. Esperar su IP, comprobar identidad/acceso existente, observar los fallos y preparar una intervención reversible separada de Update. El segundoP271 no sustituye al primero. No elevar privilegios ni repetir dumps bloqueados en bucle. No se cambiaron radios ni escribió/reinició el TV durante esta revisión.

## Antecedente de la entrega local

## Entrega0.8 del7/9/2026,15:54 ART (histórica)

Ayuda de Fable recibida y revisada; Kingston limpiado y Acceso USB0.8 copiado/leído. [Revisión y decisiones](hipotesis/REVISION-CONJUNTA-FABLE.md) · [Recibo de entrega/limpieza](../preparacion-usb/postintento-08-estado.json).

**No hay ROM instalada ni respaldo original del TV confirmados.** El último intento observado sigue detenido al2%; el resultado del ciclo manual no se comunicó. No se inventa una vuelta a Android.

Si Android está disponible, instalar **AccesoUSB-0.8.apk** desde el Kingston y pulsar una vez **«Guardar diagnóstico del último intento»**. Al terminar o mostrar un error, devolver el pendrive. [Pasos vigentes](../rom-simplificada/INSTALACION-USB.md). No repetir Update ni botones de reinicio anteriores.

0.8 busca log del arranque anterior, console/pmsg y registros actuales filtrados; consulta WiFi, Bluetooth, batería, espacio y WebView con límites de tiempo/tamaño. No cambia radios, no abre el actualizador ni escribe BCB/particiones. Usa ADB local existente, UID2000/P291/API28, carpeta nueva y hashes estrictos con autocontrol. Una consulta denegada o agotada se registra como tal. «Completa» no acredita respuesta de todos los servicios.

Pruebas PC:12ADB,21fixtures con mksh real/alias activo y11etapas verificadas sintácticamente bajo POSIX y mksh. APK53651B, SHA `e103db68fb4deea3479db9a72844eea6e69c5d9beb66403b5673a9636377a148`; firma habitual y versión8/0.8 verificadas. [Pruebas](../rom-simplificada/instalador/EVIDENCIA-TESTS-0.8.json). Los adaptadores de PC no sustituyen Android/toybox; timeout se comprueba también en el TV al iniciar. **Captura física0.8 pendiente.**

De Fable se adoptan PROP-09 y fase1 de PROP-13. BatteryStats tiene una espera sin límite en AOSP9; WiFi/BT piden estadísticas de forma asíncrona y la espera explícita de respuestas tiene timeout. Un dumpsys lento no demuestra que retenga el cierre. La barra2% tampoco confirma uncrypt_file, block.map o BCB. PROP-12 pasa al roadmap con correcciones; PROP-08 sigue sin una lectura/restauración Amlogic probada en este P291.

Preparador vigente: [preparar-postintento-08.ps1](../preparacion-usb/preparar-postintento-08.ps1). D: al entregar; identidad estable y marcador de abajo revalidados. Se archivaron y retiraron14archivos,573.327.869B, verificando ambas copias antes de borrar. Quedan APK0.8/guía, ROM0.1.1, recovery, marcador e informes. No se formateó ni reparó el volumen; no se afirma haber corregido su indicador Warning/dirty. [Contenido vigente](../rom-simplificada/INSTALACION-USB.md).

## Antecedentes conservados

Antecedente del **7/9/2026, tras el intento físico con ROM completa**. Cuatro fotos muestran menú OEM → ZIP0.1.1 seleccionado y confirmado → Copying → diálogo de preparación Android al 2 %. El usuario confirma **más de diez minutos sin avance**. [Evidencia y análisis](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md).

**No hay instalación ni respaldo original del TV confirmados. No repetir Update.** La captura0.6 y las verificaciones criptográficas siguen válidas; no acreditan que el sistema consiga cerrar ni que recovery se haya ejecutado.

La referencia exacta Android9 sitúa 2 % después de la notificación de apagado y antes de regresar del cierre de ActivityManager; el procesamiento del paquete llega después. Esto favorece un atasco del cierre, aunque el framework del TV no se extrajo y la interfaz podría estar congelada. No atribuir una causa definitiva ni asegurar que no hubo escrituras de preparación.

Acción indicada entonces, cuyo resultado sigue pendiente: un único ciclo de alimentación de diez segundos para salir del bloqueo, conservando el USB. No se presupone BCB/mapa correcto ni se promete que el corte carezca de riesgo. Si aparece instalación real, dejarla continuar; si aparece recovery/error, conservar el texto sin elegir wipe; si vuelve Android, no repetir Update. **Resultado del ciclo pendiente.**

## Qué habilita la evidencia nueva

- Se obtuvo el APK original de OTAUpgrade del primer P291. Coincide byte por byte con el APK antes leído del P271: se reutiliza el análisis del código, sin equiparar el hardware de ambos equipos.
- La firma integral de `TVBASE-P291-A9-0.1.1-RECOVERY.zip` pasó dos verificaciones independientes contra los certificados OTA capturados del P291. La confianza del Android actual coincide; las claves del recovery interno siguen sin leerse. [Recibo criptográfico](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json).
- En API28, el actualizador original copia el paquete USB a `/data/cache/update.zip`, prepara `uncrypt_file`, solicita BCB y luego `recovery-update`. El mapa de bloques depende del framework. El código no confirma la integridad de la copia interna ni la persistencia de BCB/mapa. [Análisis del APK](../diagnostico/primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md).
- La referencia Amlogic consulta BCB para arrancar recovery **interno**. Esto no demuestra el comportamiento del cargador instalado ni que vaya a cargar `recovery.img` del pendrive.

El menú Select/Update ya se abrió al principio, pero solo recibió el ZIP vacío de 22 bytes, que quedó al 2 %. El intento nuevo con la ROM completa llegó también al 2 % y quedó detenido. Acceso USB 0.7 verifica ese paquete y el APK original antes de abrir el mismo menú. **No corrige por sí mismo el atasco al reiniciar ni constituye otro método de flasheo.**

## Antecedente físico: Acceso USB 0.7

La APK solo abre **«Abrir actualización local»** tras comprobar el perfil P291/API28, el USB marcado, la integridad del ZIP y la identidad del actualizador. La selección y confirmación de Update quedan en el menú original. No hace otra captura general ni solicita un reinicio propio.

[Entrega 0.7 verificada](../preparacion-usb/entrada-oem-07-estado.json): copiado y leído el 7/9/2026 a las 12:34 ART, proceso terminado con código 0. APK de 29.075 bytes y guía de 1.537 bytes; hashes coincidentes. Pruebas locales: 12 casos ADB, 23 escenarios mksh, sintaxis de ambas etapas y controles de secuencia/perfil. Se conservan la ROM, recovery y todos los informes; 0.6 quedó retirada como .no-usar. [Pasos vigentes](../rom-simplificada/INSTALACION-USB.md). La ROM continúa siendo 0.1.1: no hace falta cambiar su firma por este hallazgo.

| Archivo | Función | Límite |
| --- | --- | --- |
| `AccesoUSB-0.7.apk` | Comprobar y abrir explícitamente el menú OEM | Menú OEM observado; Update con ROM real detenido al 2 % |
| `TVBASE-P291-A9-0.1.1-RECOVERY.zip` | ROM experimental con respaldo previo y cinco particiones | Sin instalación física; recovery interno aún no validado |
| `recovery.img` | Recovery externo preparado del candidato | Conservado; esta vía OEM solicita recovery interno |
| `TVBASE-MEDIA.txt` | Identifica el medio autorizado | Marcador exacto requerido |
| `LEEME-AHORA.txt` | Instrucciones de la entrega activa | Debe coincidir con su recibo |

No activar borrados opcionales. En API28 el fabricante oculta sus casillas y puede tener preferencias privadas no leídas; no se garantiza conservar los datos del Android anterior. El primer Update ya puede escribir una orden en cache antes de mostrar la confirmación. Una barra, apagado o ausencia de señal no acreditan copia íntegra, BCB, recovery ni instalación. Si se repite el atasco, registrar fase, mensaje y tiempo; no prescribir un corte eléctrico suponiendo que la preparación terminó.

## Antecedentes que siguen siendo relevantes

1. Tres grabaciones Armbian fallaron; una cuarta terminó verificada tras cambiar físicamente la conexión USB. El TV siguió iniciando Android: no se demostró arranque de Armbian.
2. El ZIP vacío seleccionado originalmente no contenía ROM. Acceso 0.2 falló en el protocolo ADB; 0.3 corrigió las consultas, pero su petición de recovery quedó sin señal.
3. La entrada 0.4 con `reboot:update` tampoco mostró recovery. Sus dos informes preceden a esa solicitud; no describen el fallo posterior.
4. Las dos capturas 0.5 quedaron incompletas por la cuota consumida por GMS. El alias `hash` de mksh dejó vacíos los digests binarios. Los textos sellados y la adquisición en PC tienen validaciones separadas. [Hallazgos 0.5](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md).
5. Su pstore completo muestra 517,24 segundos de actividad del mismo kernel después del aviso de reinicio. Favorece un atasco durante el cierre previo al reinicio físico, sin identificar la función culpable. No demuestra ausencia de recovery ni causa SDIO.
6. La captura 0.6 sí obtuvo OTAUpgrade, otacerts y configuración accesible. La raíz init permanece denegada; una sección filtrada vacía de uncrypt no demuestra que falten sus servicios.

Las entregas anteriores conservan sus recibos: [0.6](../preparacion-usb/evidencia-06-estado.json), [0.5](../preparacion-usb/evidencia-05-estado.json) y [0.4](../preparacion-usb/entrada-amlogic-estado.json). No volver a ejecutarlas por rutina.

## Identidad del destino y límites

Primer TV: `gxlx2_p291_1g`, Android9/API28, shell UID2000; LED sin funcionamiento. El segundo P271 no es destino. El primer TV no requiere red: la conexión existente de la APK es ADB local dentro del propio equipo.

Kingston DataTraveler 3.0, USB, 30.943.995.904 bytes, no sistema/no arranque de PC. Última letra D:, FAT32 `TVBASE`, volumen 30.925.651.968 bytes. La letra no es identidad:

```text
USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL
```

Marcador `TVBASE-P291-20260906-4dc82786`. No formatear ni reconstruir el pendrive para esta entrega. Conservar todos los informes y cualquier `TVBASE-respaldo-*` nuevo. `usb-antes.img` respalda el antiguo pendrive, no el TV.

La ROM conserva recovery/cargador en su receta y desactiva los scripts heredados que reemplazaban recovery al arrancar. Instala system, vendor, product, odm y boot al final, con respaldo previo y lectura de hashes. No A/B, sin rollback automático ni restauración ensayada. El boot contiene kernel/DTB del candidato: la coincidencia del DT no demuestra compatibilidad completa de video, WiFi, DDR o control.

Chrome138 es el techo oficial de esta base Android9. El proveedor WebView efectivo y el rendimiento de VP9/alfa/canvas siguen pendientes de prueba física. Aplicación, administración remota y soporte de nuevas placas permanecen en el roadmap.

## Historial

Git local en `main`, con fuentes, documentación y evidencia revisada. Binarios, claves e informes crudos permanecen locales. El [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k) ya está publicado con historia saneada, SHA remoto y lectura anónima verificados. [Recibo de publicación](evidencia/publicacion-github.json) · [Flujo Git](GIT.md).

La APK0.7 no guarda un registro posterior a Update. No afirmar que habrá un nuevo reporte de este atasco en el pendrive sin leerlo. Las fotos actuales son la evidencia del intento; el pstore anterior corresponde a otra solicitud.

El usuario confirmó que Fable5.1 está trabajando desde otra PC/cuenta y pidió que Codex continúe H1 con el pendrive conectado a esta PC. Sus conclusiones se recibieron luego en el ZIP de Fable; ver actualización0.8 arriba. [Coordinación H1/H2](COLABORACION.md) · [Procedimiento público](PUBLICACION.md).

## Revisión H1 y nueva lectura del pendrive · 7/9/2026

La [revisión de Codex](hipotesis/H1-RESULTADO-CODEX.md) separa H1a (posible atasco Java en el OEM) y H1b (cierre tardío del kernel en el intento anterior). ADB solicita la propiedad de reinicio sin recorrer ShutdownThread Java en AOSP9. El pstore previo, con 517,236913s tras el notificador, no demuestra bloqueo de ActivityManager. La barra se actualiza de forma asíncrona y el plazo de10s no limita toda la llamada de cierre de AMS. No hay causa única demostrada.

Kingston D: revalidado y leído: 75 archivos de carpetas de evidencia más dos informes sueltos coinciden con los originales adquiridos; ROM/APK/recovery/guía coinciden con sus SHA. No hay una carpeta nueva de informe ni respaldo del TV. Windows marca el volumen sucio/Warning; CHKDSK sin reparación terminó el recorrido sin problemas, con una línea inicial de acceso denegado que se conserva como límite. No se formateó ni preparó otra entrega. [Recibo saneado](../diagnostico/h1-cierre-android/resumen-saneado.json).

Se agregó un parser offline con diez regresiones aprobadas y un diseño acotado de observación. En esa revisión inicial todavía no se desplegó un recolector nuevo ni se pidió otro Update. Una captura posterior del pstore puede aprovechar el intento ocurrido, si Android volvió a arrancar; el resultado de ese arranque sigue pendiente de respuesta. Comparar H1 con H2 antes de instrumentar otra actualización.
