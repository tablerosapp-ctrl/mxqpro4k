# Estado actual y construcción de la base

**Tras la prueba física0.4:** el TV quedó sin señal y nunca mostró recovery. La ROM0.1.1 sigue preparada, sin instalar y sin respaldo original del TV confirmado. Los informes guardados fueron anteriores al reinicio y no capturaron su fallo; recovery existe como partición de24MiB, con lectura de contenido denegada. [Evidencia del P291](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md).

La herramienta nueva es **Acceso USB0.5**, que solo recopila evidencia del último intento sin reiniciar ni abrir el actualizador. Compilación y pruebas locales están documentadas. La [copia USB0.5 está verificada](../preparacion-usb/evidencia-05-estado.json); su primera captura física sigue pendiente. La ROM0.1.1 y el recovery externo permanecen intactos. Seguir [Instalación USB](INSTALACION-USB.md) y [Estado](../docs/ESTADO.md) para la entrega y el paso vigente.

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

## Herramienta vigente de evidencia del primer TV

`compilacion/acceso-usb-0.5/acceso-usb.apk` contiene **Acceso USB0.5**. Su botón «Guardar evidencia del último intento (no reinicia)» copia al pendrive datos de arranque, registros pstore en bytes, APK/permisos del actualizador original de este P291 y certificados OTA públicos cuando son legibles. Registra las denegaciones y verifica tamaños/hashes. Usa exclusivamente ADB local en127.0.0.1:5555; el permiso INTERNET permite ese socket, sin requerir WiFi ni red externa. No solicita root, no abre el actualizador, no reinicia y no instala la ROM.

Los originales se guardan en una carpeta nueva `TVBASE-evidencia-*`. Tras la lectura en PC, las conclusiones pueden orientar una entrada distinta. La captura no garantiza que todos los archivos estén accesibles ni que pstore conserve el fallo del intento anterior. No repetir0.4 para producir un reinicio adicional. Los fuentes/artefactos0.4 se conservan archivados en `compilacion/acceso-usb-0.4-archivado/`.

El Kingston dejó atrás la preparación Armbian: el ZIP vacío no es un instalador y no debe reutilizarse. Cada entrega posterior tiene un recibo propio de copia/lectura. La existencia de ROM/recovery en el medio no demuestra ejecución ni instalación en el TV.

## Reconstrucción

Todos los scripts actúan sobre archivos regulares dentro del proyecto, sin acceso a discos físicos ni ADB:

1. `preparar-copias.py`: extrae y expande las particiones desde la fuente cuyo hash se exige.
2. `compilar-componentes.py`: compila Inicio TV y el overlay. Para el recopilador0.5 se usa `instalador/compilar-evidencia05.py`, con salida/versionado independientes y clave local existente; no sobrescribir un APK entregado.
3. `simplificar.py`: aplica la receta explícita y valida las modificaciones.
4. `verificar-y-empaquetar.py`: limpia bloques libres, compara archivos, comprueba ext4, genera sparse y recompone el contenedor Amlogic.

Las comprobaciones evitan sobrescribir implícitamente un trabajo anterior. Para una segunda receta se debe usar una carpeta de trabajo nueva o archivar explícitamente la anterior. Las claves de desarrollo se conservan localmente en `claves-desarrollo`, excluidas por `.gitignore`; no son claves de producción ni reemplazan la firma de plataforma del fabricante.

Las herramientas de compilación y ext4 se guardan en la PC, en `tools/compilar-android`, `tools/verificacion-apk` y `tools/ext4-cygwin`. Los catálogos y hashes de sus descargas se conservan allí. La herramienta temporal Acceso USB se ejecuta en Android, no en Windows.

Las pruebas actuales de la herramienta están en `instalador/test_evidencia05.py` y `EVIDENCIA-TESTS-0.5.json`; cubren ADB simulado, controles y copias sintéticas con adaptadores, sin ejecutar el TV. El detalle de construcción, fuentes generadas e históricos está en [DESARROLLO](../docs/DESARROLLO.md). Git local conserva fuentes y evidencia seleccionada; imágenes, claves y capturas crudas permanecen fuera según [GIT](../docs/GIT.md).
