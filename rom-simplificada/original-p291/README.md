# TV Base desde los originales del P291

Esta revisión implementa el pedido de construir una ROM interna simplificada desde los originales adquiridos del **primer P291 / gxlx2_p291_1g**. La preparación trabaja sobre archivos de PC; no instala ni reinicia el TV. El segundo P271 y la ROM candidata anterior no aportan sus drivers a esta imagen.

**Resultado local:** cinco imágenes y dos ZIP construidos y verificados. Instalación: **573.492.264 bytes**, SHA256 `bd4a8dd7df8d61580c5b450867bda2ef2b214b400b4cafcce5a26baa5c48a614`. Restauración original: **913.228.907 bytes**, SHA256 `a10aee68042ef9f945a4160fd897d0db1943e28dd58e0a03918d138e9f1a8e3f`. Los paquetes permanecen en PC, sin copiar al pendrive ni aceptación física del recovery. [Recibo de instalación](empaquetado/salida/TVBASE-P291-A9-0.2.0-VERIFICACION.json) · [Recibo de restauración](empaquetado/salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.0-VERIFICACION.json).

La base elegida es Android 9, para mantener APK, framework multimedia y controladores conocidos. Es una derivación depurada del original, **no una reconstrucción completa de AOSP ni una certificación de ausencia de código malicioso**. Sustituir también todo el framework necesita otra etapa de integración y pruebas de hardware; Linux con un entorno Android añadiría una compatibilidad aún no probada en esta placa.

## Composición

| Parte | Tratamiento |
| --- | --- |
| Kernel, multi-DTB y drivers de video/red | Conservados desde el P291 real; comparación de hashes y atributos de los archivos que permanecen. |
| System/vendor/product/odm | Copias con geometría original; selección explícita de paquetes y servicios. |
| Navegador y WebView | Chrome Monochrome 138.0.7204.179 ARM32, firma Google conservada; proveedor declarado por overlay. Se retira WebView 66. |
| Inicio y ajustes | Inicio propio, acceso a ajustes TV y selección de APK desde USB; APIs y proveedores de Android conservados. |
| Actualizaciones propias | Gestor separado del WebView, HTTPS saliente y manifiesto firmado; política por paquete, certificado y horario. Sin destino ni tareas de red mientras esté desactivado. |
| Bluetooth | Se retiran APK, HAL, declaraciones y carga de sus módulos; WiFi se conserva, sin afirmar reparación. |
| Accesos de diagnóstico heredados | TCP ADB desactivado, autenticación requerida para ADB, USB sin depuración por defecto; su, procmem elevado y consola retirados. |
| Datos anteriores | El instalador exige una migración separada a userdata limpia; no borra ni conserva silenciosamente APK OEM en ella. |

La selección retira 51 APK originales y conserva 34 paquetes de plataforma/hardware. Agrega Chrome y cuatro componentes propios (inicio, selección WebView, valores iniciales y gestor). Las bibliotecas y servicios compartidos de video, audio, red, almacenamiento, IR y CEC se preservan según su función. [Política de paquetes](politica-paquetes.json) · [Auditoría de servicios](AUDITORIA-SERVICIOS.md).

El primer inicio configura Bluetooth y WiFi apagados; Ethernet permanece disponible. WiFi puede probarse desde ajustes, con sus drivers originales. Esto evita activar automáticamente la radio que quedó bloqueada en la instalación anterior; no resuelve por sí mismo su causa. No se modifica el kernel/SDIO para presentarlo como reparado.

Chrome 138 es el techo oficial de Android 9; un motor posterior exige cambiar la base del sistema. El componente integrado mejora la versión respecto de Chrome 70, pero no acredita mejor rendimiento ni mantenimiento futuro de esa rama. [Anuncio de Chromium](https://groups.google.com/a/chromium.org/g/chromium-dev/c/vEZz0721rUY). La prueba de dos VP9, uno con alfa, más canvas sigue siendo obligatoria.

## Limpieza y límites de confianza

Se retiran Play/GMS, feedback/backup de Google, tiendas y entretenimiento precargados, launcher OEM, pruebas de fábrica, duplicación de pantalla, entrada remota por red y el actualizador OEM. Se elimina también el servicio que reinstalaba APK al iniciar. Los XML de permisos se recortan por paquete, conservando los privilegios de componentes necesarios.

El usuario informó llamadas de red que considera ajenas a su aplicación. No se atribuye una VPN, un origen geográfico ni malware a partir de ese dato. La auditoría estática separa servicios normales (DNS, red, métricas locales) de funciones prescindibles; aún falta capturar tráfico de la ROM arrancada, atribuirlo a procesos y comprobar que no quedan conexiones OEM. Chrome y Android pueden hacer sus propias conexiones de conectividad/hora/seguridad, distintas del gestor propio.

Esta versión experimental conserva SELinux permisivo, parte del framework y las claves de plataforma originales. No está lista para una flota de producción ni para prometer aislamiento completo frente a cualquier APK. La transición a políticas enforcing y firmas propias de plataforma requiere preservar dependencias y volver a probar arranque/video. El gestor no agrega listeners, acceso shell o root a la aplicación web.

## Actualizaciones

El usuario tiene servidor, pero no proporcionó aquí su dirección. La imagen incluye el gestor con `enabled=false`, sin inventar un endpoint. Su [documentación](gestion/README.md) describe cómo configurar la política del dueño y producir manifiestos firmados. APK y navegador pueden actualizarse independientemente; no se implementa una actualización de toda la ROM a través de ese gestor inicial.

El proceso del gestor permanece separado del WebView. Actualizar Chrome puede terminar procesos que lo utilizan; se controla por una ventana de mantenimiento y política del dueño, sin prometer reanudación automática de videos. El proveedor realmente cargado y la instalación remota siguen requiriendo prueba física.

## Construcción y evidencias

1. [inventariar-originales.py](inventariar-originales.py) relee las fuentes verificadas y extrae inventarios/manifest como datos privados.
2. [compilar-componentes.py](compilar-componentes.py) construye inicio y overlays aislados; [COMPONENTES.json](COMPONENTES.json) identifica sus APK. El gestor tiene compilación, pruebas y revisión separadas.
3. [construir.py](construir.py) aplica [politica-paquetes.json](politica-paquetes.json), conserva metadatos, comprueba ext4, hashes y atributos extendidos. Una copia con `e2image -ra` omite los bloques libres que contenían datos eliminados; se vuelve a comprobar el resultado.
4. [boot.py](boot.py) cambia únicamente las entradas auditadas del ramdisk, preservando kernel/DTB y verificando la cabecera Android v1.
5. [Empaquetado](empaquetado/README.md) genera por separado instalación y restauración de cinco particiones. La firma heredada SHA1 se comprueba por dos implementaciones; no sustituye la aceptación física del recovery.

Las entradas y salidas privadas, originales y versiones anteriores se conservan. Una comprobación fallida detiene la construcción; no se convierte en éxito por existir un archivo o por terminar debugfs con código 0. Las pruebas locales no acreditan instalación, tráfico limpio, WiFi recuperado ni restauración efectiva.

[Imágenes finales](IMAGENES-0.2.0.json) · [Incidencias y correcciones verificadas](INCIDENTES-CONSTRUCCION.md) · [Prueba final de la receta](empaquetado/EVIDENCIA-PLAN-FINAL.json) · [Corrección acotada de product](empaquetado/EVIDENCIA-PRODUCT-EA.json). El primer intento conservado detectó un formato de atributo largo; el segundo encontró bloques de atributos huérfanos dejados por debugfs. La tercera construcción completó todos los controles. No se corrigieron esos fallos sobre el dispositivo ni se sobrescribieron los intentos anteriores.

La [verificación adicional de composición](COMPOSICION-VERIFICADA.json) confirma las 39 APK por hash, la configuración desactivada dentro del gestor y todos los bloques realmente libres en cero. Reconstruye los metadatos de grupos ext4 sin bitmap inicializado; no confunde sus reservas con espacio libre ni examina la holgura de bloques asignados. Su lector tiene una prueba con contenido libre alterado que debe rechazar.
