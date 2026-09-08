# Auditoría de servicios de los originales P291

7/9/2026. Se revisaron localmente boot y configuraciones de system/vendor/product/odm del **primer P291 respaldado**. Esta auditoría no ejecutó firmware, no se conectó al TV, no modificó imágenes y no construyó un entregable. Las decisiones y rutas exactas están en [seleccion-servicios.json](seleccion-servicios.json); no es una receta para ejecutar automáticamente.

Se extrajeron 166 archivos de configuración: 78 de system, 80 de vendor, uno de product y siete de boot; odm no contenía archivos que coincidieran con esta selección. Esto no significa que odm esté vacío. El inventario completo y los manifest de APK pertenecen al trabajo del agente principal. Las pruebas privadas quedan en `privado/auditoria-servicios/`.

## Accesos que la nueva ROM debe cerrar

| Evidencia original | Resultado | Selección |
| --- | --- | --- |
| `vendor/build.prop`, L48–49 | `service.adb.tcp.port=5555`, `ro.adb.secure=0` | TCP desactivado y autenticación requerida. Validar también propiedades persistentes heredadas de data. |
| `system/etc/prop.default`, L5, L8 y L37 | `ro.secure=1`, `ro.debuggable=1`, `persist.sys.usb.config=adb` | Conservar `ro.secure=1`; depuración desactivada y USB sin ADB por defecto. ADB USB solo si se conserva una vía explícita autenticada. |
| `system/xbin/su` | Setuid `04750`, propietario root, grupo shell | Retirar. Su acceso UID0 fue confirmado previamente en el equipo; no es una deducción basada solamente en el nombre. |
| `system/xbin/procmem` | Setuid/setgid `06755`, root:root | Retirar este ejecutable de diagnóstico elevado. |
| `boot/init.usb.rc`, L15 | Servicio adbd con `--root_seclabel=u:r:su:s0` | Retirar esa opción y aplicar conjuntamente los cambios de configuración anteriores. La opción sola no determina si existe root. |
| `boot/init.rc`, L750–759 | Consola shell y arranque por `ro.debuggable=1` | Eliminar el servicio/arranque de consola. |
| `vendor/etc/init/hw/init.amlogic.board.rc`, L4 y L12 | Arranca consola incondicionalmente | Retirar ambos `start console`; cambiar solo ro.debuggable no basta. |
| `vendor/etc/init/hw/init.amlogic.rc`, L473–475 | Activa depuración serie kgdb/fiq en userdebug | Retirar ese bloque de depuración conservando los ajustes de hardware restantes. |

El barrido de archivos regulares de las cuatro particiones encontró como set-ID los dos ejecutables señalados. `vendor/xbin/busybox` está en `0755`, sin setuid: su presencia no demuestra un root abierto. No se auditó aquí cada posible mecanismo privilegiado de todo el framework.

Por decisión de integración, este **prototipo conserva SELinux permisivo**, igual que el original. Cerrar ADB, su y consola no equivale a certificar seguridad de producción. El gestor propio debe limitar operaciones y verificar firmas; no debe introducir otra interfaz de shell/root genérica para APK o red. Cambiar a enforcing exige validar políticas y funcionamiento del hardware.

## Servicios OEM que deben retirarse o neutralizarse

`vendor/bin/preinstall.sh` llama a `su`, concede a Facebook permisos de ubicación y almacenamiento, e instala APK desde `/vendor/preinstall/` al faltar un marcador o cambiar el conteo. También modifica provisionamiento y HDMI CEC. `init.amlogic.rc` define el servicio en L500–504 y lo inicia en L512–513. Hay que retirar servicio, trigger y contenido OEM asociado, y sustituir únicamente el provisionamiento requerido por el inicio propio. Estos hechos no son una atribución de malware.

`boot/init.rc` declara `flash_recovery` en L767. Su script `/system/bin/install-recovery.sh` utiliza `applypatch`, boot y `/system/recovery-from-boot.p` para reconstruir recovery. Debe quedar neutralizado para que no deshaga decisiones de la nueva plataforma. Esto **no** justifica borrar `uncrypt`, `setup-bcb` o `clear-bcb`, que son componentes útiles para un actualizador propio controlado.

`init.amlogic.rc` también inicia `factoryreset` al completar el arranque, pero `/vendor/bin/factoryreset.sh` no está en la imagen original. Puede retirarse esa llamada residual y su servicio. No se debe borrar el bloque entero: también activa ZRAM y ajusta CPU. El script `startsoftdetector.sh` referenciado por `softprobe` tampoco aparece en vendor; su comportamiento no puede inferirse ni debe presentarse como demostrado.

La retirada de actualizadores/aplicaciones OEM se determina con el inventario de APK del agente principal. No basta con desactivar su icono si quedan receptores de arranque, servicios, privilegios o mecanismos que reinstalen el paquete.

## Bluetooth, WiFi y video

El original utiliza **`persist.vendor.btmodule`**, sin guion bajo, en `init.amlogic.rc` L523–528. La candidata anterior utilizaba `persist.vendor.bt_module`: sus reemplazos literales no son reutilizables sin adaptación. La retirada de Bluetooth debe cubrir aplicaciones, declaraciones de funciones, HAL VINTF, servicio y triggers de reinicio/carga; cambiar una preferencia o `config.disable_bluetooth` aisladamente no basta.

Preservar los archivos de WiFi, firmware, cfg80211, HAL, supplicant y `wifi_preload`. Este último enlaza con `libwifi-hal` y componentes de supplicant. La pila ya obtenida situó el cierre esperando una llamada de inicio del HAL WiFi; desactivar Bluetooth no constituye por sí solo una reparación probada de esa espera. No cambiar SDIO, DTB o kernel como parte de la limpieza de servicios.

`vendor/etc/init/hw/init.amlogic.media.rc` carga explícitamente firmware, `decoder_common`, `stream_input`, códecs —incluido **`amvdec_vp9.ko` en L22**—, encoder y VPU. Deben conservarse sus bytes y dependencias, junto con OMX, SurfaceFlinger, gralloc/composer, audio, `systemcontrol` y subtítulos. Tampoco retirar TEE/DRM o bibliotecas de fabricante solo porque la primera aplicación reproduzca video sin DRM: pueden formar parte de la ruta multimedia compartida.

Conservar `load_remote`, `remotecfg.sh`, tablas IR, HAL IR/CEC y `hdmicecd`. `droidlogic.software.core.xml` registra `droidlogic.jar` y privilegios de `com.droidlogic`, incluido CEC; no debe desaparecer toda esa biblioteca por contener también un permiso Bluetooth. La política de paquetes y las dependencias deben decidir la retirada por componente.

## Qué se pudo establecer sobre red

La revisión de estas configuraciones no encontró una URL operativa de actualización/telemetría o un proxy remoto fijado. Las coincidencias HTTP de los XML eran licencias. **No prueba ausencia de llamadas de red**: faltan la ejecución y el análisis completo de APK/bibliotecas, y Android puede generar tráfico de conectividad, hora o resolución mediante configuración del framework.

- `netd` y su socket `dnsproxyd` son parte del DNS y la conectividad Android; no representan por su nombre un proxy ajeno.
- `racoon`, `mtpd` y `mdnsd` están `disabled`/`oneshot`. Su presencia no acredita una VPN conectada ni una configuración externa.
- `statsd` y `mediametrics` tienen consumidores del framework. El nombre de métricas no demuestra envío a terceros. Priorizar la retirada de agentes de envío concretos identificados frente a eliminar APIs internas a ciegas.
- `rc_server` enlaza con Binder y `libremotecontrolserver`; no se observaron imports directos de sockets de red en ese ejecutable pequeño. La biblioteca no quedó auditada integralmente: no se afirma que no pueda usar red.
- `systemcontrol` importa funciones de sockets y contiene una cadena de revocación de certificados Google. Eso no demuestra contacto con ese destino ni telemetría. Su función de pantalla y sus dependencias obligan a conservarlo hasta identificar una operación de red concreta separable.

Los XML Google otorgan privilegios y excepciones de batería/datos, check-in y backup a GMS/Vending y otros paquetes. Recortarlos por **paquete efectivamente retirado**, conservando entradas de componentes mantenidos. Un archivo llamado `privapp-permissions-google.xml` también contempla un instalador de APK Google; no debe borrarse por nombre sin revisar la política real, que en esta base mantiene `com.android.packageinstaller`.

## Comprobación independiente de boot.py

Se ejecutó `boot.py` sobre el original **solo en memoria**, sin guardar una imagen final. Un parser CPIO independiente comprobó que cambian únicamente `init.rc` e `init.usb.rc`; kernel, DTB, nombres, modos, UID/GID, inodos, fechas y demás entradas quedan conservados. También se verificaron rellenos, rechazo de un origen alterado y permanencia del original sin cambios.

Código de la primera revisión SHA256 `0371f17b35d26f20c36ed8cf8190cbece741bfb6bf677b20c941b80a85f2a669`. Resultado esperado de ese código y fuente: 16777216 bytes, SHA256 `c1a71479498bdfd8368fb1ade42ae293cb97f6087c43c3a8f8f31535725113fc`. No se encontraron defectos en esta comprobación acotada; no acredita arranque físico ni valida todavía los cambios complementarios de vendor/system.

**Actualización de revisión del 7/9/2026 ART:** el código vigente de `boot.py` tiene SHA256 `29bb7e273c34e5ec06366f0db387aecd3d4a8086ef3f352724d9a539e7ea0274`. Se comprobó que su única diferencia respecto del código anterior es agregar `'ramdisk_sha256': sha(newram)` al diccionario de resultados: retirar exactamente esa línea recupera el SHA256 anterior. No cambia el algoritmo ni los bytes producidos.

Se repitió la transformación vigente sobre el boot respaldado **en memoria, sin guardar imágenes ni modificar el original**, y se contrastó con el lector CPIO independiente: solo cambian `init.rc` e `init.usb.rc`, con los mismos nombres y modos de entrada y kernel/DTB idénticos. El resultado volvió a ser 16777216 bytes y SHA256 `c1a71479498bdfd8368fb1ade42ae293cb97f6087c43c3a8f8f31535725113fc`; el ramdisk comprimido dio SHA256 `ab85369fe4883d272be2c1914f45624b0e882393e99b7dbd230189b3cc93feb1`, coincidente con el campo nuevo. La comprobación terminó con código 0. La prueba privada `revision-boot.json` se conserva intacta como recibo de la primera versión; este cierre identifica el código vigente y la repetición local. Ninguna de las dos prueba un arranque físico.

Las 14 selecciones de [seleccion-servicios.json](seleccion-servicios.json) distinguen retirada, edición, preservación y trabajo pendiente, con hashes de las fuentes disponibles y controles de aceptación. El JSON enlaza por hash las pruebas privadas `extraccion.json`, `init-bloques.json`, `setid-y-root.json`, `servicios-binarios-estaticos.json` y `revision-boot.json`.
