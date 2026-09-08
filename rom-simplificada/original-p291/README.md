# TV Base desde los originales del P291

## Vigente · instalador/restaurador0.2.2

La plataforma0.2.0 conserva sus cinco imágenes. [022](../../docs/evidencia/INSTALADOR-P291-022.md) corrige el rechazo del nombreAmlogic system en instalación/restauración; susZIP ya están copiados/releídos enKingston. TV todavíarecovery, ROM noinstalada. Usar022 desdeese menú, sin repetir AccesoUSB09/prepare/Update. El error021 ocurrió antesdebackup/formato/flash; fuentes/recibos anteriores se conservan.


## Antecedente de la entrega 0.2.1

## Preparación física0.9 completada

Tras la autorización explícita del usuario se ejecutó un único intento por LAN en el primer P291. ENV/BCB se guardaron y releían correctos, sus respaldos y el informe quedaron verificados enUSB y PC, y se neutralizaron las dos órdenes activas anteriores. [Evidencia física](../../docs/evidencia/PREPARACION-ENTRADA-P291-09.md). La preparación no reinició, borró userdata ni instaló la ROM. Después del ciclo físico indicado, el usuario informó un menú de recovery; aceptación del ZIP y arranque de TV Base siguen pendientes. Las referencias inferiores a autorización o ejecución pendientes corresponden a la entrega previa.

Esta revisión implementa el pedido de construir una ROM interna simplificada desde los originales adquiridos del **primer P291 / gxlx2_p291_1g**. La preparación trabaja sobre archivos de PC; no instala ni reinicia el TV. El segundo P271 y la ROM candidata anterior no aportan sus drivers a esta imagen.

**Entrega vigente: instalador0.2.1 y plataforma0.2.0.** Las cinco imágenes se conservan; el nuevo instalador respalda seis particiones y prepara userdata limpia antes de escribir Android. ZIP: **573.688.933 bytes**, SHA256 `dcb152c77e55cb067d6e88a8144990a3edb5d06568ea8cdfdc414a0fa21aac58`. El restaurador separado0.2.1 contiene cinco imágenes OEM: **913.294.443 bytes**, SHA256 `42580206f254fab0a2280cd263a48882677e7ddf5cfd609382a840c8d0fb103a`; conserva userdata y no recupera su respaldo. Ambos están sellados/verificados en PC. [Instalación y migración](instalacion-021/CONTRATO-MIGRACION.md) · [Restauración](restauracion-021/README.md) · [Estado de la copia USB](../INSTALACION-USB.md).

[Acceso USB0.9](entrada-apk/README.md) prepara un método nuevo de entrada al recovery interno mediante ENV/BCB. Modificar el entorno de arranque puede impedir iniciar Android; el usuario pidió conocer el riesgo antes de decidir. La APK está instalada, pero el diálogo OEM del2% sigue tapando la pantalla. No se modificaron ENV/BCB ni se reinició el TV. La preparación por LAN, tras esa decisión específica, evita depender de pulsaciones ocultas; no debe ejecutarse como prueba inocua. [Evidencia y límites](../../docs/evidencia/ENTRADA-ORIGINAL-P291-021.md).

Los paquetes0.2.0 permanecen históricos e inmutables; sus ejecutables usaban una consulta de tamaño de64bits incompatible con ARM32. La corrección0.2.1 fue comprobada en lectura en el TV. No repetir los ZIP anteriores.

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
| Datos anteriores | El instalador0.2.1 respalda y relee userdata completa antes de crear ext4 limpio; no reimporta APK ni datos OEM al Android nuevo. |

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
5. [Instalación0.2.1](instalacion-021/CONTRATO-MIGRACION.md) y [restauración0.2.1](restauracion-021/README.md) generan paquetes separados. El [empaquetado0.2.0](empaquetado/README.md) conserva el antecedente inmutable. La firma heredada SHA1 se comprueba por dos implementaciones; no sustituye la aceptación física del recovery.

Las entradas y salidas privadas, originales y versiones anteriores se conservan. Una comprobación fallida detiene la construcción; no se convierte en éxito por existir un archivo o por terminar debugfs con código 0. Las pruebas locales no acreditan instalación, tráfico limpio, WiFi recuperado ni restauración efectiva.

[Imágenes finales](IMAGENES-0.2.0.json) · [Incidencias y correcciones verificadas](INCIDENTES-CONSTRUCCION.md) · [Prueba final de la receta](empaquetado/EVIDENCIA-PLAN-FINAL.json) · [Corrección acotada de product](empaquetado/EVIDENCIA-PRODUCT-EA.json). El primer intento conservado detectó un formato de atributo largo; el segundo encontró bloques de atributos huérfanos dejados por debugfs. La tercera construcción completó todos los controles. No se corrigieron esos fallos sobre el dispositivo ni se sobrescribieron los intentos anteriores.

La [verificación adicional de composición](COMPOSICION-VERIFICADA.json) confirma las 39 APK por hash, la configuración desactivada dentro del gestor y todos los bloques realmente libres en cero. Reconstruye los metadatos de grupos ext4 sin bitmap inicializado; no confunde sus reservas con espacio libre ni examina la holgura de bloques asignados. Su lector tiene una prueba con contenido libre alterado que debe rechazar.
