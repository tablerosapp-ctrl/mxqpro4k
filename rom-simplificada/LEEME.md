# Estado actual y construcción de la base

**Tras analizar la captura física0.5:** la ROM0.1.1 sigue preparada, sin instalar y sin respaldo original del TV confirmado. El registro posterior al intento0.4 muestra un aviso de reinicio del kernel y más de ocho minutos de actividad posterior: favorece un atasco al cerrar el sistema, sin identificar la función causante. Recovery existe como partición de24MiB, con lectura de contenido denegada; no se demostró ejecución del recovery USB. [Evidencia del P291](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md).

La herramienta nueva es **Acceso USB0.6**, un complemento sin reinicio para obtener primero `otacerts.zip`, después el APK de OTAUpgrade ya identificado en este P291 y finalmente la configuración pendiente. La captura0.5 quedó incompleta por una cuota de APK consumida antes de alcanzar OTAUpgrade; además, una colisión con el alias `hash` de mksh hizo aceptar digests binarios vacíos. Se conserva aquella versión y su evidencia, y se construye0.6 en fuentes/salida independientes. La nueva copia USB0.6 ya está verificada; su ejecución física enTV sigue pendiente. La ROM0.1.1 y el recovery externo permanecen intactos. Seguir [Instalación USB](INSTALACION-USB.md) y [Estado](../docs/ESTADO.md) para el recibo y el paso vigente.

El resto de este documento describe la construcción de la primera imagen Amlogic 0.1 y su revisión. El contenedor .img no es el entregable de instalación actual. La copia defectuosa de debugfs fue eliminada conservando sus registros.

---

# ROM Android TV Base — primera imagen experimental

5 de septiembre de 2026. **Ya existe una imagen completa reconstruida en la PC. No se ha flasheado ni probado su arranque.** Está dirigida al perfil P291 del primer TV del dossier, cuya compatibilidad física con esta base todavía debe comprobarse. El segundo TV leído por WiFi es P271: no es destino de esta imagen.

Archivo: `salida/TVBASE-P291-A9-0.1-EXPERIMENTAL.img`.

**Revisión preparada0.1.1:** `salida/TVBASE-P291-A9-0.1.1-RECOVERY.zip`, 573.089.164 bytes, SHA256 `e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205`. La versión0.1 se retiró porque conserva scripts que intentan sustituir recovery al iniciar Android;0.1.1 los desactiva. Ninguno de los intentos posteriores ha mostrado aceptación del ZIP ni instalación. El ZIP real sustituye system, vendor, product, odm y boot, con respaldo previo obligatorio; omite las particiones de bootloader, recovery, DTB, dtbo, vbmeta y datos. El boot nuevo incluye kernel, ramdisk y contenido de arranque del candidato, por lo que conservar la partición DTB no certifica por sí solo la compatibilidad. [Instalador, comprobaciones y límites](instalador/README.md). Resolver la entrada con la evidencia nueva antes de elegir otra forma de instalar.

- Tamaño: 1.342.736.696 bytes.
- SHA-256: `73be8916f504e883dd536271a64694701f798e4e3408090eaa59cbce88db3798`.
- Formato: contenedor de particiones Amlogic. No es una imagen de disco para escribir directamente con Imager ni un ZIP de actualización local.
- Base: Android 9 ARM32, candidato HG680-LC/P291 publicado por ophub y ya analizado en `analisis-rom`.

## Cambios incluidos dentro de la imagen

- **Chrome 138.0.7204.179 Monochrome**, con navegador y WebView, en `/system/app/Chrome/Chrome.apk`. APK original de Google, firma y hash verificados, sin recompresión ni modificación del paquete.
- **Inicio TV propio**, de aproximadamente 17 KB, para elegir aplicaciones y abrir ajustes con el control remoto. Sin cuentas, publicidad, servicio de fondo ni permiso de red. Se retiraron las dos copias del inicio Shafa y su intermediario de arranque.
- Un **overlay estático** de Android selecciona Chrome como proveedor WebView. El WebView 66 original se conserva como recuperación en esta primera imagen; el proveedor efectivo debe comprobarse tras arrancar. El recurso original solo admitía `com.android.webview`: copiar Chrome sin cambiar esa selección habría sido insuficiente.
- Se retiraron **16 APK**: cuatro aplicaciones de video preinstaladas, tienda, dos copias de Shafa, FHStartHome, asistentes Xiri y aplicaciones identificadas de TR-069, diagnóstico remoto y Andlink. Lista exacta y rutas en `trabajo/cambios.json`.
- Se sustituyeron los dos scripts que reinstalaban aplicaciones ajenas por scripts sin acciones. Se quitaron la apertura de consola Telnet de fábrica y la preparación de cuentas IPTV de los scripts afectados, conservando la detección de hardware.
- `tvbase.rc` desactiva siete servicios de administración, diagnóstico, asistente e introducción de arranque. También se retiró el inicio explícito posterior de `stbdetector`. La desactivación se basa en el comportamiento de `stop` y `class_start` de AOSP 9; falta observarla en el equipo.
- Identificador visible `TVBASE-P291-A9-0.1-experimental` y español de Argentina como idioma predeterminado. Los ajustes del fabricante pueden carecer de traducción.

La base ya venía sin Google Play/GMS. Se conservaron sus ajustes porque integran red, audio y pantalla. No se borraron bibliotecas del fabricante por su nombre ni se suprimieron APIs Android. Aún quedan componentes del fabricante cuya sustitución requiere una prueba funcional, entre ellos interfaces IPTV y los propios ajustes. Esta primera imagen no representa una auditoría completa del software del proveedor.

## Qué se comprobó

- Sistemas de archivos `system` y `vendor`: verificación ext4 sin errores tras los cambios y tras limpiar bloques libres.
- **3.493 archivos conservados**: contenido idéntico al candidato, además de permisos y propietarios comprobados. Esto incluye las bibliotecas y controladores que permanecen en esas particiones.
- Los once archivos agregados o sustituidos coinciden con sus componentes de origen y tienen contextos SELinux comprobados. Los APK propios están firmados con una clave de desarrollo local; Chrome mantiene la firma Google.
- Imágenes Android sparse: su expansión coincide con las copias ext4 verificadas.
- Contenedor final: CRC32 `0xd99e2c6f` y **12 verificaciones SHA-1 de particiones** coincidentes.
- Bootloader, kernel/boot, DTB, recovery y todos los elementos ajenos a `system` y `vendor` son idénticos al candidato. La imagen fuente original sigue intacta.
- Quedan aproximadamente 440 MiB libres en `system` y 101 MiB en `vendor`.

Evidencia: `salida/VERIFICACION.json`, `salida/*-fsck.txt` y `trabajo/cambios.json`. Se conservan causa y registros de un intento local fallido en `trabajo/fallo-debugfs-ruta-absoluta`: el port de debugfs creó nombres incorrectos al usar destinos absolutos. Se detectó antes de empaquetar, se restauró la copia original y se corrigió el método con cambio de directorio y nombre de archivo simple. No afectó al pendrive ni al TV.

## Qué falta para instalar y aceptar la ROM

1. Confirmar la entrada del **primer TV P291** al instalador por USB y la correspondencia de su hardware con el candidato. La coincidencia del DT del dossier no certifica DDR, cargador, WiFi ni toda la placa.
2. Preparar el medio y las particiones que se escribirán según esa entrada. El contenedor completo incluye bootloader/DDR del candidato; todavía no se ha seleccionado para grabación física. No asumir que `erase_bootloader=0` evita escribir un bootloader incluido.
3. Arrancar desde memoria interna, comprobar proveedor WebView 138, gráficos, video VP9, transparencia, canvas, audio, controles, red y almacenamiento local. No hay una mejora de rendimiento medida todavía.
4. Sustituir los componentes restantes que no hagan falta y desarrollar el gestor propio de actualizaciones, autenticación y recuperación. **Ese gestor todavía no está implementado.**
5. Para recibir Chrome oficial posterior a 138, preparar una base Android más reciente: Google finalizó el soporte de Android 8/9 en la rama 138. Esto no se resuelve cambiando el número de versión declarado por Android. [Anuncio oficial](https://support.google.com/chrome/thread/352616098/sunsetting-chrome-support-for-android-8-0-oreo-and-android-9-0-pie?hl=en-GB).

## Complemento0.6 de evidencia del primer TV

La salida `compilacion/acceso-usb-0.6/acceso-usb.apk` corresponde a **Acceso USB0.6**, con fuentes en `componentes/acceso-usb-0.6/`. El botón «Guardar archivos que faltan (no reinicia)» ejecuta cinco etapas: carpeta nueva, autocontrol SHA/certificados públicos, APK de OTAUpgrade, configuración/identidad y cierre verificado. La ruta `/product/app/OTAUpgrade/OTAUpgrade.apk` se exige porque fue acreditada en el P291; no se vuelve a recopilar Google Play Services. Certificados y APK son obligatorios: si no se pueden obtener, conserva el parcial e informa fallo.

El cálculo usa funciones `tvbase_*`, toybox explícito, validación de64 caracteres hexadecimales en cada consumidor y un autocontrol inicial con el SHA conocido de `abc`. La [auditoría mksh](instalador/MKSH-HALLAZGO-0.5.md) explica por qué las pruebas Bash de0.5 no detectaron la colisión de nombres. Los datos0.5 ya obtenidos sirven para el análisis, pero sus campos SHA binarios vacíos no se corrigen retroactivamente. Los tests y resultados0.6 se registran aparte.

Los archivos se guardan en una carpeta nueva `TVBASE-evidencia-*`. Usa exclusivamente ADB local en127.0.0.1:5555; INTERNET permite ese socket, sin requerir WiFi ni red externa. No solicita root, no abre el actualizador, no reinicia y no instala la ROM. La configuración inaccesible queda documentada; no se promete haberla leído. Fuentes/artefactos0.4 archivados y fuentes0.5 en `componentes/acceso-usb/` se conservan como históricos. No repetir0.4 para producir un reinicio adicional.

El Kingston dejó atrás la preparación Armbian: el ZIP vacío no es un instalador y no debe reutilizarse. Cada entrega posterior tiene un recibo propio de copia/lectura. La existencia de ROM/recovery en el medio no demuestra ejecución ni instalación en el TV.

## Reconstrucción

Todos los scripts actúan sobre archivos regulares dentro del proyecto, sin acceso a discos físicos ni ADB:

1. `preparar-copias.py`: extrae y expande las particiones desde la fuente cuyo hash se exige.
2. `compilar-componentes.py`: compila Inicio TV y el overlay. Para el complemento0.6 se usa `instalador/compilar-evidencia06.py`, con fuentes y salida versionadas independientes y clave local existente. `compilar-evidencia05.py` conserva la construcción histórica; no sobrescribir un APK entregado.
3. `simplificar.py`: aplica la receta explícita y valida las modificaciones.
4. `verificar-y-empaquetar.py`: limpia bloques libres, compara archivos, comprueba ext4, genera sparse y recompone el contenedor Amlogic.

Las comprobaciones evitan sobrescribir implícitamente un trabajo anterior. Para una segunda receta se debe usar una carpeta de trabajo nueva o archivar explícitamente la anterior. Las claves de desarrollo se conservan localmente en `claves-desarrollo`, excluidas por `.gitignore`; no son claves de producción ni reemplazan la firma de plataforma del fabricante.

Las herramientas de compilación y ext4 se guardan en la PC, en `tools/compilar-android`, `tools/verificacion-apk` y `tools/ext4-cygwin`. Los catálogos y hashes de sus descargas se conservan allí. La herramienta temporal Acceso USB se ejecuta en Android, no en Windows.

Las pruebas del complemento están en `instalador/test_evidencia06.py`, con `EvidenciaHarness06.java` y recibo `EVIDENCIA-TESTS-0.6.json`; consultar ese recibo para casos y resultados efectivamente ejecutados, incluida la regresión pertinente bajo mksh real. No equivalen a ejecutar el TV ni a entregar su APK en el USB. Las pruebas0.5 se conservan: Bash y adaptadores no reprodujeron su fallo real de SHA. El detalle de construcción, fuentes generadas e históricos está en [DESARROLLO](../docs/DESARROLLO.md). Git local conserva fuentes y evidencia seleccionada; imágenes, claves y capturas crudas permanecen fuera según [GIT](../docs/GIT.md).

Entrega complementaria0.6: [recibo USB](../preparacion-usb/evidencia-06-estado.json), 7/9/2026 a las00:22 ART, APK y guía copiadas/leídas con SHA coincidente. Primera ejecución0.6 en el P291 pendiente.
