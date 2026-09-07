# Antecedente: prueba Armbian retirada de la ruta activa

Este documento registra las pruebas iniciales. Sus pasos y estados NO son la instalación vigente. Usar [Instalación USB actual](rom-simplificada/INSTALACION-USB.md) y [Estado](docs/ESTADO.md). La imagen expandida se eliminó en la limpieza; el gzip verificado y los registros se conservan.

---

# Primera prueba con pendrive

Objetivo actual: Android minimo instalado en la memoria interna del TV box, con amplia compatibilidad para versiones futuras de la APK, WebView actualizable y videos locales. Se validara con pruebas generales; la aplicacion en desarrollo y su composicion VP9 seran una referencia adicional cuando esten disponibles. Ver [arquitectura vigente](ARQUITECTURA-ANDROID-TV.md).

El pendrive puede servir como herramienta temporal de acceso o identificacion. Armbian no es el sistema final elegido. La instalacion interna sigue pendiente: no hay una imagen Android validada para esta unidad y Windows no detecto un dispositivo Amlogic en modo de grabacion en la ultima comprobacion. No investigar la causa de la actualizacion del Android original.

## Preparacion

- Estado vigente (5/9/2026): imagen Armbian grabada y verificada correctamente. El usuario la probo y el TV box inicio Android habitual; no se ha demostrado entrada al arranque externo. El usuario descarta conectar el TV box a la red. Se agrego un `update.zip` vacio para probar la entrada por Actualizacion local, pendiente de que el usuario encuentre esa opcion.
- Pendrive: Kingston DataTraveler 3.0 de 32 GB, identificado inicialmente como D: y posteriormente como E:.
- Imagen: Armbian 26.05.0, Ubuntu Noble, S905L2, kernel 6.12.91, edicion server.
- Descarga original y archivo descomprimido guardados en `images`.
- SHA-256 de la descarga contrastado con el publicado por GitHub.
- Configuracion inicial original: `meson-gxl-s905l2-x7-5g.dtb`.
- Esta edicion muestra una consola de texto; todavia no incluye un escritorio ni navegador.
- El resultado de grabacion se registra en `preparacion-usb/estado-grabacion.json`.

## Registro de grabacion

- Primer intento: interrumpido. Raspberry Pi Imager termino con codigo 1.
- Windows registro un evento `disk`, ID 153, el 4 de septiembre de 2026 a las 22:34, con un reintento de E/S en el disco 1, bloque `0x43b000`.
- Despues del error, el usuario recupero el pendrive. Se comprobo de nuevo su identificador: es el mismo Kingston DataTraveler 3.0, disco 1, D:, etiqueta NUEVO VOL, FAT32. Volumen: 30925651968 bytes; libres: 30925602816 bytes; sin elementos de usuario en la raiz. Windows lo muestra accesible y sin proteccion de escritura. No se hizo una prueba completa de su memoria.
- Segundo intento: iniciado el 4 de septiembre de 2026 a las 22:55:19, tras volver a comprobar identidad, contenido vacio, imagen y firma de la herramienta. Termino con codigo 1 a las 22:59:32.
- Windows registro otro evento `disk` 153 a las 22:59:31, esta vez en el bloque `0x3de800`. La fecha de ultima llegada del dispositivo USB coincide con ese momento: el sistema volvio a detectar el pendrive durante la escritura. Esto no permite decidir por si solo entre un problema del puerto, conexion o pendrive.
- Tras el segundo intento Windows informo cero particiones reconocidas en el Kingston. El intento posterior con otra version del grabador y la recuperacion estan documentados debajo. Los tres primeros intentos fallaron; el cuarto completo escritura y verificacion en el nuevo puerto.

## Probar en el TV box

### Paso vigente: entrada por Actualizacion local, sin red

El medio ya esta grabado correctamente. Una consulta posterior desde Windows confirmo BOOT FAT32, `uEnv.txt`, `aml_autoscript` y `s905_autoscript`; la configuracion inicial y los archivos de arranque siguen presentes. Encender y volver al Android habitual no acredita que se haya intentado ejecutar el kernel del USB.

Se preparo `update.zip` en la raiz de BOOT: un ZIP vacio valido de 22 bytes, sin particiones Android, sin binarios y sin instrucciones de instalacion. Su copia fue leida y comparada; registro en `preparacion-usb/activacion-local.json`. Es una prueba del [metodo Update / Recovery_02 documentado por CoreELEC](https://wiki.coreelec.org/coreelec:ceboot), no una ROM Android ni un metodo universal.

Si la app del TV box ofrece Actualizacion local, seleccionar ese archivo con el pendrive conectado. Registrar si reinicia a consola/Armbian, abre recovery, vuelve a Android o rechaza el ZIP. Un rechazo previo al reinicio exige otra entrada y no se resuelve regrabando la misma imagen. No elegir borrado de datos ni formateo como parte de esta prueba.

Al entrar al modo update, el `aml_autoscript` que ya trae Armbian puede configurar el entorno de arranque y persistirlo con `saveenv`. Este paso no instala el producto Android interno. Se revisan por separado paquetes Android de la familia del reporte, para comprobar componentes antes de preparar una instalacion interna.

### Correccion del metodo de grabacion

El usuario recupero el volumen y lo reasigno como E:. Se comprobo que es el mismo Kingston, vacio y en FAT32. La herramienta siempre se ejecuta en la PC; la imagen se escribe directamente al USB. La prueba adicional por archivo fue propuesta, pero el usuario pidio omitirla y no se ejecuto.

El grabador 1.8.5 queda retirado. El nuevo procedimiento es `preparacion-usb/grabar-kingston-actual.ps1`, con Raspberry Pi Imager 2.0.11.1 oficial, SHA-256 y firma comprobados. Obtiene la letra actual a partir del identificador estable, comprueba de nuevo el contenido y guarda un registro detallado en un directorio por intento. La verificacion permanece habilitada. El archivo `estado-grabacion.json` registra el resultado efectivo, no la mera solicitud de inicio.

La version actual incluye cambios en el bloqueo de unidades y el manejo de errores de Windows. Es un cambio concreto de herramienta; todavia no prueba que el fallo anterior haya sido causado por ella. [Version oficial](https://github.com/raspberrypi/rpi-imager/releases/tag/v2.0.11).

Resultado del intento actualizado: fallo el 4/9/2026 a las 23:41. El registro `preparacion-usb/grabacion-20260904-234011-a03e047f/imager.log` contiene esperas de escritura y errores Win32 5 (acceso denegado), 433 (dispositivo inexistente) y 55 (dispositivo no disponible). No llego a verificar. Windows registro disk 153 en el bloque `0xc1b80` y una nueva deteccion del Kingston. La conexion fisica continua siendo USB(3)/HS03; la letra E: no representa otro puerto fisico. No se hizo una prueba por archivo ni otra grabacion despues de este fallo.

El wrapper inicial de este intento perdio el codigo numerico de salida del proceso. El fallo esta acreditado por el registro del grabador, no por ese campo nulo. La captura de procesos se corrigio y se probo con procesos inocuos que devuelven 0 y 7.

Resultado posterior: el 5/9 el usuario cambio fisicamente el USB. Windows lo ubico en USB(16)/SS04. La escritura con la misma imagen y Imager 2.0.11.1 comenzo a las 00:06:59 y completo con codigo 0 a las 00:11:26: escritura de 230 segundos, verificacion de 35.103 segundos y hash `4479b09374d92ffe4be625b5dded96c5d7d7a0e8c6bcb0a7d2894a839214a2f8` coincidente. El registro final dice `succeeded` y muestra la expulsion. Informe en `preparacion-usb/grabacion-20260905-000644-562f503b`. No se aplicaron personalizaciones ni se cambio el DTB de la imagen original. Esta prueba verifica el medio escrito, no el arranque ni la compatibilidad de la placa.

### Pasos de arranque, despues de una grabacion verificada

Antes de estos pasos: el 5/9/2026 el usuario informo que Windows rechazaba eliminar el volumen con "solicitud no compatible". La consulta fisica encontro el Kingston de 30943995904 bytes, sin proteccion de escritura; Windows mostraba una pseudoparticion en offset 0 y un volumen NTFS de 3274170368 bytes sin letra, sin archivos de usuario. Se guardo la cabecera: contenia NTFS directamente en sector 0.

Se ejecuto una restauracion, no otra grabacion de imagen: DiskPart limpio la estructura, creo una particion desde 1 MiB, formateo exFAT y asigno E:. Codigo de salida 0. Volumen resultante de 30937186304 bytes, etiqueta KINGSTON. Una prueba de 1 MiB escrito, leido y comparado por SHA-256 paso y se elimino su archivo. No es una prueba completa de memoria ni sustituye la verificacion pendiente de una imagen. Registro: `preparacion-usb/estado-recuperacion.json`; detalles: `preparacion-usb/recuperacion-20260905-000135`.

1. Esperar a que se confirme que la grabacion y su verificacion terminaron.
2. Retirar el pendrive de la PC cuando la herramienta lo haya expulsado, o expulsarlo de forma segura.
3. Desconectar la alimentacion del TV box.
4. Conectar el pendrive, HDMI, un cable Ethernet al router y, si hay uno disponible, un teclado USB.
5. Conectar la alimentacion y esperar entre dos y tres minutos.
6. Registrar si aparece Android, una consola de Armbian o una pantalla negra. Si el router muestra un nuevo equipo Armbian, anotar su direccion IP.

Si aparece una consola de Armbian, las credenciales iniciales publicadas por ophub son `root` / `1234`. Seguir el cambio de clave si el sistema lo solicita.

Si aparece Android, apagar por completo y probar otro puerto USB. Si sucede en todos, falta resolver la entrada al arranque externo; cambiar de DTB no resuelve por si solo esa etapa.

La [guia de ophub, seccion 12.4](https://github.com/ophub/amlogic-s9xxx-armbian/tree/main/documents#124-setting-the-box-to-boot-from-usbtfsd), distingue el primer arranque de una reinstalacion: describe entrar en modo update desde Android para activar el arranque externo. En este equipo el acceso necesario aun no esta confirmado. La primera prueba de encendido sirve para comprobar si su bootloader ya permite USB; si vuelve a Android, registrar ese resultado y resolver esa entrada antes de volver a grabar imagenes o cambiar DTB.

Una pantalla negra no prueba que Linux no haya arrancado: comprobar tambien si aparece un equipo nuevo en el router.

## Siguientes variantes

Cambiar una sola variable por prueba. La imagen contiene estos DTB candidatos:

1. `meson-gxl-s905l2-x7-5g.dtb` (inicial).
2. `meson-gxl-s905l2-ipbs9505.dtb`.
3. `meson-gxl-s905l3b-m302a.dtb`.
4. `meson-gxl-s905w-p281.dtb`.

Son candidatos, no compatibilidad comprobada con p291. Se cambia la linea `FDT=` en `uEnv.txt`, dentro de la particion BOOT. Hay una copia del archivo original en `preparacion-usb/boot-original`.

Tambien hay cuatro archivos `uEnv.txt` preparados en `preparacion-usb/variantes`, uno por candidato. Solo difieren en `FDT`; preservan el identificador del sistema y el resto de los parametros de la imagen inicial. Usarlos unicamente con esta imagen.

El primer criterio de exito es que arranque y tengamos acceso por consola o Ethernet. El siguiente es comprobar imagen, teclado y estabilidad para empezar a adaptar esa base.

## Alcance de esta prueba

- Esta prueba opcional usa el pendrive. `armbian-install` instala Linux en la memoria interna y no forma parte del camino elegido para el producto Android.
- No formatear las particiones del pendrive si Windows lo propone despues de grabar: una de ellas usa el sistema de archivos de Linux.
- No esta garantizado que el Android de fabrica arranque un USB automaticamente. La imagen original incluye un script de activacion que puede guardar configuracion del bootloader (`saveenv`); no se ha ejecutado ese script en el TV box desde la PC.
- Que Armbian arranque no demuestra que funcionen la decodificacion VP9, la transparencia ni la composicion del WebView en una nueva ROM Android. Esas pruebas corresponden a la base Android candidata.

Fuente de imagen y acceso inicial: https://github.com/ophub/amlogic-s9xxx-armbian/releases/tag/Armbian_noble_arm64_server_2026.06
# Actualizacion del 5/9/2026, 15:45

**Estado posterior, 6/9:** el usuario ya instalo Acceso USB en el primer TV y abrio su actualizador local. Las fotos muestran UpdateLocale, Select y Update. Continuar con Select para observar archivos; no pulsar Update ni Online update. El `update.zip` existente esta vacio y la ROM completa sigue en la PC. Ver `diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md`. Las instrucciones siguientes conservan el registro de preparacion previo a esta prueba.

Se construyo una primera ROM completa experimental con Chrome/WebView 138 integrado, inicio propio y retirada de aplicaciones del operador. Esta en `rom-simplificada/salida/TVBASE-P291-A9-0.1-EXPERIMENTAL.img`, verificada como contenedor Amlogic; no se ha grabado ni probado en el TV. Detalles y pendientes en `rom-simplificada/LEEME.md`.

Se agrego al BOOT del Kingston solamente `AccesoUSB.apk` (16.787 bytes), herramienta temporal para abrir el actualizador local existente y exportado. SHA256 y lectura coincidentes: `7ab7946dc15aef23af8a49ff5239e99716d0f679de6148ed9d24dc23c6614b8e`. Recibo: `preparacion-usb/acceso-instalador.json`. Se identifico el USB por su ID estable, modelo y capacidad; no tiene letra y se accedio por el identificador del volumen. No se cambiaron sus particiones ni se copio la ROM completa.

En el primer TV: abrir `AccesoUSB.apk` desde el explorador e iniciar Acceso USB. Usar «Abrir actualizacion local» solo para ver el menu. No pulsar «Actualizar» dentro del actualizador ni seleccionar el antiguo ZIP vacio todavia. Si el boton no esta disponible, esa actividad no esta expuesta. La instalacion de la ROM sigue pendiente de resolver la entrada y la compatibilidad; la aplicacion de acceso no flashea ni reinicia.

---
