# Estado operativo

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
