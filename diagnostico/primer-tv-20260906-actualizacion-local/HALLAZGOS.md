# Actualizador local accesible en el primer TV

Fecha de recepcion: 6/9/2026. Evidencia: dos fotografias proporcionadas por el usuario despues de instalar y abrir Acceso USB en el primer TV. No son una nueva lectura ADB ni evidencia del segundo TV P271.

## Datos visibles

La captura `acceso-usb.png` muestra:

- Android 9, API 28.
- `ro.product.device=ampere`, `ro.product.board=ampere`.
- `ro.build.display.id=ampere-userdebug 9 PPR1.180610.011 20250226 test-keys`.
- `service.adb.tcp.port=5555`, `persist.adb.tcp.port` no definido, `ro.adb.secure=0`.
- Boton «Abrir actualizacion local» habilitado; acceso alternativo del fabricante no disponible.

La captura `actualizador-local.png` confirma que se abrio la pantalla Update del equipo, con una seccion Online update y otra UpdateLocale. En esta ultima aparecen los botones Update y Select. No se ve un archivo seleccionado.

## Alcance

Queda confirmada una entrada a la pantalla del actualizador local que antes no era visible en el launcher. Posteriormente el usuario confirmo que Select muestra `update.zip` al conectar el pendrive. La pantalla blanca inicial correspondia al pendrive desconectado, segun su correccion; no es evidencia de un fallo del selector ni del USB. Todavia no se ha observado aceptacion de un paquete por el recovery, arranque externo ni instalacion de la nueva ROM. Las propiedades ADB no demuestran un servicio accesible, autorizacion efectiva o root. Estas fotos tampoco identifican el DTB; el perfil P291 procede del dossier anterior.

La inspeccion del actualizador del segundo TV sigue siendo evidencia de ese segundo equipo: no se ha demostrado que ambas APK sean identicas.

## Siguiente accion fisica

Seleccionar `update.zip` y registrar la pantalla resultante antes de pulsar Update, en particular cualquier opcion de borrado. El `update.zip` de 22 bytes que ya estaba en el pendrive es un ZIP vacio de la prueba anterior; no contiene la ROM nueva. La ROM experimental completa permanece en la PC como contenedor Amlogic, no como un ZIP de recovery listo para elegir.

Se revalido la [guia de CoreELEC](https://wiki.coreelec.org/coreelec:ceboot), que documenta el ZIP vacio como una entrada posible al arranque externo en algunos equipos. No garantiza la entrada en este P291. Al entrar en modo update, el `aml_autoscript` presente puede guardar configuracion del cargador. No presentar esa prueba como instalacion de Android ni como una operacion incapaz de escribir estado interno.

Se descarto ampliar Acceso USB para investigar la pantalla blanca tras la correccion del usuario. En esta investigacion no se modifico ni recompilo la APK, no se escribio el pendrive y no se enviaron ordenes al TV.

## Resultado de la activacion: detenido al 2 %

El usuario selecciono BOOT/update.zip y, siguiendo la indicacion del agente, ejecuto Update y su confirmacion local. La foto `preparando-2-por-ciento.png` muestra el dialogo de sistema «Actualizacion del sistema Android», «Preparando para actualizar...» y 2 %, superpuesto al actualizador. El usuario confirma mas de cinco minutos sin avance y que ese paso no se puede detener desde la interfaz.

No hay evidencia de reinicio, entrada a recovery, ejecucion del USB ni instalacion de la nueva ROM. El ZIP preparado tiene 22 bytes y no contiene particiones ni instrucciones de instalacion. No confundir el 2 % de preparacion mostrado con escritura del 2 % de la ROM. Pueden haberse escrito ordenes de recovery o estado de preparacion; no afirmar ausencia de toda escritura interna.

La [implementacion publicada de ShutdownThread en AOSP](https://android.googlesource.com/platform/frameworks/base/+/3b58eff/services/core/java/com/android/server/power/ShutdownThread.java) asigna 2 % al cierre inicial del sistema, antes de terminar ActivityManager (4 %), PackageManager (6 %) y preparar el paquete (desde 20 %). Es una referencia para interpretar el dialogo, no codigo extraido de este TV. La apariencia y el bloqueo son compatibles con un reinicio de actualizacion atascado; sin registros del primer TV no se puede atribuir una causa precisa.

Se amplio el analisis estatico del APK del segundo TV a InstallPackage y OtaUpgradeUtils. Sus referencias incluyen preparacion de ordenes, instalacion mediante recovery y reinicio via PowerManager. No acredita que la implementacion del primer TV sea identica.

Siguiente paso indicado: ante mas de cinco minutos estables al 2 % y sin cancelacion disponible, un unico ciclo de alimentacion, desconectando 10 segundos y reconectando con el pendrive presente. Observar si vuelve Android, aparece recovery/error o arranca externamente. No repetir Update automaticamente ni elegir borrado/restablecimiento. El resultado del ciclo fisico sigue pendiente.

**Resultado confirmado despues:** el usuario informa que el equipo arranco Android normal tras el ciclo de alimentacion. No se observo recovery ni sistema externo. El Kingston se devolvio a la PC para preparar el instalador real de ROM. No repetir esta activacion mediante el ZIP vacio.

## Acceso USB 0.2: error antes del reinicio

El usuario inicialmente dijo "Ya esta instalando el ZIP", pero corrigio esa descripcion: no habia podido avanzar. La foto `acceso-02-identificador-adb.png` muestra Acceso USB 0.2 sobre Android, con `IOException - Identificador ADB inesperado`. Ese error solo se emite al leer paquetes ADB; en la secuencia de esta APK aparece durante las consultas previas o antes de aceptar el servicio de reinicio. No hay evidencia de entrada a recovery ni escritura de la ROM. No registrar aquella frase inicial como una instalacion realizada.

La imagen confirma que se obtuvo una respuesta ADB; no es un error de deteccion del USB, ni confirma root. No se guardo una traza de los identificadores reales del TV, por lo que no se puede atribuir definitivamente a una respuesta tardia concreta.

Se encontro y corrigio un defecto en el cliente: respondia a CLSE y rechazaba paquetes tardios de canales anteriores como si fueran del canal nuevo. El [protocolo AOSP](https://github.com/aosp-mirror/platform_system_core/blob/android-9.0.0_r1/adb/protocol.txt) indica que no se responde a CLOSE y que se ignoran respuestas de canales cerrados. El [codigo Android 9](https://github.com/aosp-mirror/platform_system_core/blob/android-9.0.0_r1/adb/adb.cpp) tambien admite CLSE(0,id) en conexiones antiguas. Acceso USB 0.3 aplica esas reglas en la misma conexion, conserva el rechazo a identificadores desconocidos y agrega detalles de la consulta/canal al error.

Nueve pruebas locales pasaron, incluida la secuencia de tres consultas y solicitud de recovery con cierres/datos tardios, CLSE con identificador cero, rechazo de AUTH/checksum/canal desconocido y error al reiniciar. No se reinicio ningun TV durante esas pruebas. La correccion aun requiere prueba fisica en el primer equipo. El usuario reconecto el Kingston a la PC para copiar APK 0.3 y ROM 0.1.1.

## Acceso USB 0.3: consultas correctas, pantalla negra tras solicitar recovery

La foto `acceso-03-estado-correcto.png` confirma el resultado real de "Ver estado del acceso" en el PRIMER TV: "Acceso interno disponible", placa `gxlx2_p291_1g`, Android API 28, UID/GID 2000 (shell), contexto SELinux `u:r:shell:s0` y lectura de `/proc/partitions`. Esta captura valida ADB local y las consultas sucesivas de 0.3 en el equipo real; no prueba root. El recorte muestra dispositivos ram/zram, sin las particiones eMMC necesarias para determinar sus tamanos.

Despues, el usuario pulso "Entrar al instalador de la ROM (reinicia)". Vio "Comprobando acceso interno..." y luego el equipo quedo sin imagen, descrito como apagado y aun conectado a la alimentacion. Todavia no hay imagen ni confirmacion del menu recovery, aceptacion de firma o ejecucion del ZIP. Se solicito tiempo transcurrido, estado/color del LED y si el televisor indica "Sin senal".

El codigo de Acceso USB 0.3 solo consulta id/DT/API y solicita `reboot:recovery`; no entrega una ruta de ZIP ni escribe una orden de instalacion. El [servicio ADB publicado de Android 9](https://android.googlesource.com/platform/system/core/+/refs/tags/android-9.0.0_r1/adb/services.cpp) sincroniza y fija `sys.powerctl=reboot,recovery` para esa solicitud. El dispositivo podria conservar ordenes antiguas del actualizador de fabrica; no se han leido ni descartado, por lo que tampoco se afirma ausencia de toda escritura interna. La pantalla negra no acredita que este instalando, que recovery este averiado ni que realmente haya cortado su alimentacion.

El usuario confirma despues mas de diez minutos con el televisor indicando "Sin senal" y sin haber desconectado la alimentacion. Aclara que la luz del TV box no funciona: no usarla como indicador de encendido, apagado o actividad en este equipo. No vio recovery ni selecciono el ZIP nuevo. Se indico un unico ciclo de alimentacion de diez segundos, conservando el pendrive conectado, y observar durante hasta dos minutos si aparece logo, Android o recovery. Si vuelve Android, no repetir la solicitud desde la APK; si aparece recovery, permanecer en el menu. El resultado de este ciclo aun no fue comunicado. No confundirlo con el ciclo previo del actualizador al 2 %.


## Resultado del ciclo y preparación 0.4 · 6/9/2026 20:04

El usuario informó que volvió a iniciar mostrando Android, con el pendrive presente y aparentemente sin cambios. No vio recovery ni seleccionó el ZIP real. Devolvió el pendrive a la PC para preparar la siguiente vía. No registrar este resultado como instalación ni como confirmación de recovery averiado.

Acceso USB0.4 guarda un informe y verifica ROM/recovery en el medio marcado antes de solicitar reboot:update. Se preparó recovery.img del candidato P291 para carga temporal en RAM, con la clave del ZIP agregada y verificación de firmas activa. Sus componentes de kernel/DTB/ejecutable permanecen iguales. Esta vía difiere de la solicitud recovery fallida; su funcionamiento en el cargador instalado sigue pendiente. Ver ../../rom-simplificada/instalador/recovery-externo/PREPARADO.json y ../../preparacion-usb/entrada-amlogic-estado.json. La copia terminó con código0 y lectura SHA coincidente; no hubo nuevas órdenes al TV desde PC.

La siguiente observación física debe incorporarse a docs/ESTADO.md y a este registro. El informe del USB no existe en el proyecto hasta que vuelva del equipo; no inventar su resultado ni el respaldo de particiones originales.


## Resultado posterior de Acceso USB0.4

El usuario confirma Sin señal de nuevo y ausencia de recovery visible. Se adquirieron y compararon los informes guardados: sí existe recovery de24MiB, UID2000 no pudo leerla, y ambos informes preceden a la solicitud0.4. No hubo instalación ni respaldo original confirmado. El análisis, hashes y siguiente decisión están en [hallazgos de informes USB](../primer-tv-reportes-20260906-233826/HALLAZGOS.md). No repetir el botón0.4; preparar captura del estado posterior sin reinicio.
