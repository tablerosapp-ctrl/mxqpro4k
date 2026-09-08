# Reconocimiento TV Base 0.1

Implementación inicial autorizada por el usuario el 8/9/2026. Capturas secuenciales de varios TV box desde un mismo pendrive, sin reemplazar Android. REQ-18 / PROP-17. La autorización habilita construir y preparar este reconocedor; no activa actualizaciones, cambia la ROM o aplica la corrección Home.

## Uso

Seguir [LEEME-USB.txt](LEEME-USB.txt). Instalar `Reconocimiento-TVBase-0.1.apk` en cada equipo, abrirla y pulsar **Capturar y guardar este equipo**. Si Android requiere autorización de carpeta, elegir `TVBASE-RECONOCIMIENTO` del USB. Al terminar, esperar **GUARDADO Y RELEÍDO EN EL PENDRIVE**, expulsar el almacenamiento desde Android y continuar con el próximo TV.

No necesita Internet, root o ADB. Android mínimo 5/API21, compilación SDK28/target28, código Java sin librerías nativas propias; no implica prueba física en todas esas versiones. La APK declara solo lectura/escritura de almacenamiento, con selector de documentos como alternativa. No contiene permisos INTERNET, REBOOT, RECOVERY o INSTALL_PACKAGES ni modifica particiones/radios. La inicialización local de WebView y un contexto EGL identifican implementaciones; no son pruebas de rendimiento.

## Identidad e informes

Cada instalación de la APK conserva un UUID local; cada captura usa otro UUID nuevo. Se propone un nombre a partir de datos legibles de DT/Build (`p291`, `p271`, `rockchip-rk…` o desconocido), con sufijo de unidad. El usuario puede añadir un nombre. El perfil siempre es candidato y no autoriza instalación; propiedades de Android no prueban identidad física. Borrar datos de la aplicación o copiar esos datos puede cambiar o duplicar la asociación y exige revisión.

Cada ZIP lleva `informe.json`, `manifest.json`, archivos `details/` y `drivers/`. El manifiesto contiene tamaños y SHA-256, sin firma criptográfica de procedencia. El exportador verifica el ZIP local y la copia USB por lectura; un recibo adyacente indica los límites de sincronización del transporte. Los proveedores de documentos pueden no permitir sincronizar directorios; no se afirma persistencia total en ese caso. Un error real de I/O no se trata como simple falta de soporte.

La última captura local terminada puede exportarse nuevamente, verificando cualquier archivo final ya existente. Un intento incompleto de copia se conserva como `.partial` y un nuevo intento usa otro nombre temporal. No se borran capturas previas. La APK conserva su copia privada y sus fuentes de captura; no limpia archivos personales para liberar espacio. Esos archivos privados consumen memoria interna, especialmente tras varias pasadas en el mismo equipo.

Si un corte deja el recibo `.export.json` vacío o truncado, la reexportación se detiene para revisar ese recibo en PC. El ZIP y la copia local se conservan; no se sobrescribe el recibo ni se requiere repetir la captura. La relectura del recibo del selector no acredita fsync propio; el transporte se marca sin sincronización de directorio acreditada.

## Cobertura y límites

- Build/API/ABI, RAM/almacenamiento accesible, pantallas, lista de codecs/capacidades anunciadas, dispositivos de entrada, paquetes visibles/firmas/permisos y características de Android.
- Fuentes acotadas de `/proc` y sysfs, propiedades permitidas, buses/driver enlazado cuando sea legible, geometría declarada y DT accesible. Datos declarados y observados se distinguen; no se lee toda la eMMC.
- DT prioritario y luego archivos estáticos seleccionados de vendor/odm/system/product/system_ext: firmware, módulos, HAL/bibliotecas relevantes, configuración multimedia, entrada y arranque. Se excluyen rutas de datos de aplicaciones, credenciales, calibración individual y configuraciones privadas de red. No es un respaldo completo de drivers/ROM.
- Hasta 1,5 GiB de lecturas de archivos seleccionados, ajustado al espacio interno libre; máximo 128 MiB por archivo y 18.000 entradas en el recolector de archivos. El límite de tiempo de esa etapa es 12 minutos entre operaciones. Índices registran selección, omisiones, denegaciones y límites; no se consideran vacíos los archivos no accesibles.
- Sin dumps WiFi/BatteryStats conocidos por bloquearse. Una espera del cliente terminada no garantiza cancelar una llamada retenida en el kernel; no hay repetición automática. Las tareas API con plazo devuelven datos en memoria y no escriben después del cierre de la captura.
- WebView se identifica después de inicializarlo en **este proceso**. No acredita el proveedor de la APK Flutter del usuario, ni aceleración VP9 con alfa, rendimiento o ausencia de malware. API21–25 informan la ausencia de la API pública del paquete; no inventan su versión a partir de otra aplicación.

Los archivos fuente se conservan con rutas originales en índices y nombres de exportación derivados; los nombres evitan colisiones de Windows. La importación no extrae rutas largas de DT al sistema de archivos Windows. Un módulo/driver en disco no acredita carga ni funcionamiento.

## Fuentes y verificación

[MainActivity.java](src/MainActivity.java): interfaz, identidad, WebView/EGL y coordinación. [HardwareCollector.java](src/HardwareCollector.java) y [FileCollector.java](src/FileCollector.java): observaciones e inventarios. [ReportArchive.java](src/ReportArchive.java): manifiesto y ZIP verificado. [UsbStore.java](src/UsbStore.java): identificación de medio, exportación directa/selector, fsync y relectura.

[compilar.py](compilar.py) produce una carpeta privada nueva y un recibo con fuentes/hash/firma. Conserva la clave de desarrollo existente; no es firma de producción ni aplicación privilegiada. [Contrato e importador](CONTRATO-INFORMES.md), [pruebas del importador](test_importar_informes.py) y [prueba real del ZIP Java](tests/test_archive.py) verifican capturas completas/parciales, integridad y entradas malformadas en PC. El archivo JSON usado en pruebas Java es una dependencia de host, fuera de la APK.

La preparación USB se realiza con [preparar-reconocimiento-01.ps1](../../preparacion-usb/preparar-reconocimiento-01.ps1), identificando el Kingston exacto y conservando todo lo anterior. La primera ejecución física de la aplicación y la exportación desde Android siguen pendientes al construirla. Recibir y verificar el primer ZIP permitirá fijar el alcance real de cada modelo y las capturas adicionales necesarias.

Los informes y binarios adquiridos se guardan privados. Solo fuentes, contratos y resúmenes saneados se publican en Git; no cargar capturas crudas al repositorio público.
