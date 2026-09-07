# Instalacion de la ROM simplificada desde pendrive

Actualizado: 6 de septiembre de 2026.

**Ultima prueba fisica:** con BOOT/update.zip seleccionado, Android quedo mas de cinco minutos al 2 % en «Preparando para actualizar». Tras un ciclo de alimentacion volvio Android normal. No se demostro entrada al USB/recovery. No repetir esa actualizacion con ZIP vacio. [Evidencia](../diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md).

**Ruta vigente, 6/9 19:25:** Acceso USB **0.3** solicita `reboot:recovery` mediante ADB local, previa comprobacion de placa/API/identidad. Corrige el manejo de cierres y respuestas tardias tras el error "Identificador ADB inesperado" de 0.2. El usuario aclaro que no llego a instalar el ZIP. El paquete vigente es `salida/TVBASE-P291-A9-0.1.1-RECOVERY.zip`: desactiva las rutinas heredadas que intentan reemplazar recovery al arrancar, conserva las demas mejoras y exige respaldo previo de las cinco particiones que modifica. ROM y APK nuevas ya estan copiadas y verificadas en el Kingston FAT32 TVBASE (D: al prepararlo), sin otro formato. Recibo `preparacion-usb/revision-011-estado.json`, estado `verificado`; codigo de copia 0. Los archivos anteriores estan retirados con extension `.no-usar`. [Implementacion y limites](instalador/README.md). Faltan entrada efectiva a recovery, aceptacion de firma e instalacion fisica. El preparador inicial que formateaba esta retirado; no repetirlo.

El resultado buscado es **una ROM Android nueva, simplificada, con Chrome y el proveedor WebView 138 integrados en la imagen e instalada en la memoria interna**. El pendrive transporta el instalador. El sistema no debe depender de conservarlo conectado. Este documento define la instalacion; la seleccion de la ROM y la integracion de los componentes web se resuelven por separado. No propone actualizar una APK del Android original como sustituto del objetivo.

**La grabacion de Android desde almacenamiento USB existe en el codigo de Amlogic. Su disponibilidad y su activacion en el primer TV P291 aun no estan demostradas.** Copiar otra imagen al Kingston no modifica por si mismo el orden de arranque del TV.

## Hechos y limites del proyecto

| Elemento | Comprobado | Todavia no comprobado |
| --- | --- | --- |
| Kingston de 32 GB | Imagen Armbian grabada y verificada en el nuevo puerto de PC | Ejecucion por el cargador del TV |
| Primer TV | El dossier informa `gxlx2_p291_1g`, Android 9, 1 GB; al encender con el USB inicia su Android habitual | Que U-Boot haya intentado ejecutar el USB, que incluya `usb_burn`, o que una ROM candidata sea compatible |
| Acceso del primer TV, actualizado 6/9 | Acceso USB abre el actualizador local; Select muestra update.zip con el pendrive conectado. El usuario descarta conectarlo a red | Aceptacion del paquete por recovery, entrada a modo update y reset operativo |
| Segundo TV de diagnostico | Es P271, con una APK `com.droidlogic.otaupgrade` que contiene selector local ZIP | Que su APK, permisos, recovery, U-Boot o ROM sean iguales a los del P291 |
| `update.zip` agregado al USB | ZIP vacio valido, 22 bytes, comprobado por lectura; es un activador potencial | Aceptacion por la aplicacion original y entrada a modo update; no contiene la nueva ROM |

La prueba de arranque fallida no prueba por si sola un DTB incorrecto: el cargador puede continuar hacia Android sin ejecutar el medio externo. No cambiar DTB ni volver a grabar el USB para intentar corregir una entrada que no se ha activado.

## Tres formatos diferentes

| Archivo o medio | Quien lo interpreta | Uso |
| --- | --- | --- |
| Imagen de disco Armbian `.img` | Grabador de PC escribe sus sectores; U-Boot ejecuta luego los archivos de arranque | Sistema externo temporal |
| `aml_upgrade_package.img` | Herramientas de fabrica Amlogic o comandos de grabacion de su U-Boot | Contenedor de particiones, DTB y componentes de arranque para instalar internamente |
| Paquete de sistema `*.zip` firmado | Actualizador Android y recovery compatibles | Instalacion de la ROM mediante recovery |

El paquete Amlogic agrupa items como DDR, U-Boot, DTB y particiones. La extension `.img` no lo convierte en una imagen MBR lista para Imager. [Configuracion de empaquetado publicada](https://github.com/OpenAmlogic/amlogic-boards/blob/master/3.14/boards/mesongxb_p201_x/upgrade/aml_upgrade_package_enc.conf).

BurnCardMaker no debe tratarse como equivalente automatico para cualquier USB. La guia de Khadas prepara una TF/SD con `u-boot.bin.sd.bin` en sectores iniciales y archivos de instalacion en FAT32. Eso no demuestra que un P291 sin ranura SD pueda arrancar el mismo medio mediante un pendrive. [Guia del fabricante](https://github.com/khadas/documents/blob/master/CreateAndroidBurnCardViaCLI.md).

## Ruta A: paquete Amlogic leido desde el pendrive por U-Boot

El codigo publicado de `usb_burn` inicia USB, busca el archivo de configuracion, selecciona el dispositivo `usb 0` y llama a la rutina que graba el paquete Amlogic. Por tanto, un pendrive FAT legible con paquete y configuracion puede ser la fuente de una instalacion interna. El comando no consiste en exponer el TV como disco masivo a Windows: el TV es el host que lee el Kingston. [Implementacion Amlogic de usb_burn](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/drivers/usb/gadget/v2_burning/v2_usb_burn/optimus_usb_burn.c).

Contenido conceptual del instalador, aun no generado:

```text
pendrive/
  aml_autoscript              # Entrada revisada para el U-Boot de destino
  aml_sdc_burn.ini             # Configuracion de usb_burn, pese al nombre sdc
  rom-simplificada-p291.img    # Paquete Amlogic comprobado para esa placa
  manifiesto.json              # Placa admitida, versiones, hashes, particiones
  LEEME.txt
```

No basta ese arbol de archivos: tiene que existir una cadena de ejecucion. La secuencia prevista es:

1. Una entrada ya disponible pide modo update al cargador.
2. El cargador busca y ejecuta `aml_autoscript` en el USB.
3. El script valida el destino y las funciones disponibles antes de invocar la instalacion. Si no puede distinguir la placa o no existe `usb_burn`, termina sin escribir.
4. U-Boot lee el contenedor y graba las particiones aprobadas en la memoria interna.
5. Tras verificar la escritura, reinicia desde la memoria interna. El instalador no debe repetirse automaticamente en cada encendido con el USB conectado.

Esta es una especificacion de implementacion, no un script ya probado. No se puede prometer una validacion de hashes o atributos concretos sin comprobar que ese U-Boot tiene los comandos necesarios. Tampoco se reemplazara el `aml_autoscript` actual por un grabador automatico mientras falte el paquete compatible.

### Que activa la lectura

Como evidencia de la familia, la configuracion publica de P271 arranca normalmente mediante `storeboot`; cuando recibe `reboot_mode=update`, ejecuta `run update`. Ese flujo incluye la lectura de `aml_autoscript` desde `usb 0`. Tambien tiene una entrada por GPIO de upgrade. Es codigo de P271: **no certifica el GPIO, el puerto ni el comportamiento del P291**. [Configuracion Amlogic P271](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/board/amlogic/configs/gxl_p271_v1.h).

La guia de CoreELEC documenta distintas entradas, dependientes del aparato: actualizacion local, boton reset, determinadas teclas del control y reinicio update desde ADB. No afirma que todas esten disponibles en cada modelo. Que Android pueda leer archivos del pendrive tampoco prueba que el cargador lo haya leido durante el arranque. [Entradas documentadas](https://wiki.coreelec.org/coreelec:ceboot).

### Particiones y cargador

**`erase_bootloader=0` no significa "preservar el bootloader".** En la rutina publicada se evita cierta fase de borrado previo/reinicio hacia SD, pero si el paquete contiene el item `bootloader`, la rutina puede grabarlo al final. Tambien hay tratamiento de DTB y claves. Para conservar el cargador deben revisarse el contenido real del contenedor y la seleccion de particiones; no alcanza una opcion con nombre tranquilizador. [Rutina de instalacion Amlogic](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/drivers/usb/gadget/v2_burning/v2_sdc_burn/optimus_sdc_burn.c).

La ROM final debe conservar los datos de provision y calibracion necesarios. No se habilitara borrado total ni escritura de claves por rutina. No se asumira que omitir el bootloader hace compatible el resto de una ROM de otra placa.

## Ruta B: ROM completa en ZIP mediante el actualizador local existente

Un actualizador de sistema puede llevar un ZIP desde el USB al recovery y pedir su instalacion. Esta via permite sustituir particiones Android sin requerir que una APK normal tenga root, siempre que el actualizador tenga los permisos, el recovery acepte la firma y el paquete corresponda al dispositivo. Android distingue las claves de firma del sistema y las claves aceptadas por OTA; declarar `test-keys` no demuestra aceptacion. [Firma de compilaciones y paquetes OTA](https://source.android.com/docs/core/ota/sign_builds).

La inspeccion de la APK del **segundo TV P271** confirma un selector que filtra `.zip`. Su boton Actualizar escribe `/cache/recovery/command` antes de mostrar el dialogo de instalacion, con opciones de borrado segun las casillas. Por ello abrir la pantalla/selector y ejecutar la instalacion son operaciones diferentes. No se le entregara un contenedor Amlogic `.img` renombrado a `.zip`. Evidencia local: [analisis del actualizador](../diagnostico/android-20260905-142854-a8286d9a/analisis-actualizador/HALLAZGOS.md).

Actualizacion del 6/9: el usuario abrio el actualizador local del primer TV mediante Acceso USB. Las fotografias muestran UpdateLocale y los botones Select y Update; la actividad existente es accesible. Esto resuelve el acceso al menu, pero no demuestra que su APK sea identica a la del segundo TV ni que su recovery acepte nuestra ROM. No se copio la APK de actualizacion del P271 al P291: Acceso USB solo abre el componente instalado. Evidencia: [fotografias y hallazgos](../diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md).

## Posible activador offline sin root

Una APK sencilla puede buscar y abrir una **actividad de actualizacion ya instalada y exportada**, incluso si el launcher no muestra su acceso. Puede intentar la accion `android.settings.SYSTEM_UPDATE_SETTINGS` y, solo si se identifica el componente, abrir su pantalla. No necesita descargar firmware ni escribir particiones. Debe limitarse a mostrar la pantalla; no simular pulsaciones de Actualizar ni enviar intenciones de borrado.

Eso no equivale a crear una APK universal con permiso de reinicio especial. `PowerManager.reboot(reason)` exige `REBOOT`; en AOSP Android 9 es `signature|privileged`, y el broadcast `android.intent.action.REBOOT` esta protegido. Declarar esos permisos en una APK corriente no los concede. [API PowerManager](https://developer.android.com/reference/android/os/PowerManager#reboot(java.lang.String)), [manifiesto de AOSP Android 9](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-9.0.0_r1/core/res/AndroidManifest.xml).

La API de Device Owner permite un reinicio normal, requiere ese rol y no admite el argumento `update`. Tampoco convierte al propietario del dispositivo en root. [DevicePolicyManager.reboot](https://developer.android.com/reference/android/app/admin/DevicePolicyManager#reboot(android.content.ComponentName)).

Se reviso tambien el codigo actual de **Reboot to CoreELEC**, enlazado por su wiki: abre un socket a la IP del propio equipo, puerto 5555, negocia ADB y envia `shell:reboot update`. No obtiene privilegios por si mismo; depende de ADB TCP ya disponible y autorizado. No se presentara como solucion garantizada para el primer TV sin red ni ADB comprobado. [Codigo de la aplicacion](https://github.com/jamal2362/Reboot-to-CoreELEC/blob/main/app/src/main/java/com/jamal2367/coreelec/MainActivity.kt).

La diferencia con una conexion ADB existente es concreta: AOSP Android 9 implementa `adb reboot update` sin la comprobacion de root que usa especificamente para `reboot sideload`. Eso no habilita ADB cuando la ROM no lo expone y no obliga al cargador a reconocer el destino solicitado. [Servicio ADB de Android 9](https://android.googlesource.com/platform/system/core/+/refs/tags/android-9.0.0_r1/adb/services.cpp).

## Preparacion que se puede completar en la PC

1. Obtener y analizar una ROM candidata del perfil P291, con la lista exacta de sus particiones, DTB, ABI y componentes de arranque. No mezclar las pruebas del P271 con esa compatibilidad.
2. Construir la ROM simplificada con los componentes web integrados. Conservar las interfaces y los controladores necesarios para video, almacenamiento, red y controles.
3. Producir el contenedor de instalacion apropiado: Amlogic para `usb_burn` o ZIP para un recovery que lo acepte. Comprobar que contiene las versiones nuevas dentro de las particiones de la ROM, no solo APK sueltas al lado del instalador.
4. Generar inventario y hashes. Comprobar tamanos frente a la tabla de particiones del destino, coherencia de firmas/verificacion de arranque y politica explicita sobre bootloader/DTB/claves.
5. Preparar el USB solo con un mecanismo de entrada sustentado por evidencia para la placa. El manifiesto debe declarar pendientes los puntos no demostrados, en lugar de marcarlos automaticamente como compatibles.

## Condiciones para una prueba de instalacion concreta

Faltan dos elementos independientes: **un paquete de ROM compatible y una entrada ejecutable en el P291**. Tener uno no sustituye el otro. La preparacion de la ROM puede avanzar en la PC sin esperar una nueva conexion del primer TV.

Para declarar que el instalador por pendrive esta listo deben quedar establecidos:

- El paquete corresponde al perfil de placa de destino y contiene el Android simplificado y los componentes web acordados.
- El cargador ejecuta nuestro punto de entrada o el recovery admite nuestro ZIP.
- Se sabe exactamente que particiones se escribiran y como se comprobara el resultado.
- El arranque posterior funciona desde memoria interna con el USB retirado.

Estado al 6/9: la seleccion local funciona cuando esta conectado el pendrive. El intento real con el ZIP vacio quedo detenido al 2 % y el equipo volvio a Android tras cortar alimentacion. Esa via no se repetira. Se construyo un paquete ZIP con las particiones reales y un acceso directo al recovery que evita la ruta de reinicio del actualizador. La aceptacion y el arranque de la ROM experimental siguen pendientes; no se requiere investigar la causa de la OTA original.
