# Reconocimiento TV Base 0.2

Corrección del bloqueo observado con 0.1 en el equipo comercializado como MX9 5G. El modelo interno del MX9 sigue sin identificar. La foto muestra 1410 entradas revisadas y 1246 copias con contadores redondeados a 0 MB; no identifica la operación detenida. El plazo de 0.1 solo se evaluaba entre llamadas, y no garantizaba salir de una lectura bloqueada.

La aplicación primero cierra y exporta una ficha pequeña con Android y DT accesible. Solo después recoge el inventario: capacidades declaradas, paquetes, memoria, propiedades y bindings accesibles. No copia binarios de drivers ni recorre todo el device tree. Esa adquisición profunda queda en el [extractor por recovery](../extractor-recovery-0.1/README.md).

Cada fase usa UUID, directorio y ZIP propios; el inventario enlaza la ficha inicial con `parent_capture_id`. La ficha inicial no se reescribe. Si falla su exportación, no comienza el inventario. Se puede volver a guardarla y completar el inventario sin repetir su lectura. Los datos y preferencias de 0.1 se conservan al actualizar el mismo paquete y firmante.

Las consultas potencialmente bloqueantes comparten un único trabajador sin cola. Una espera vencida no libera ese trabajador: solo su finalización real lo hace. Mientras siga vivo se omiten nuevas consultas y se impide otra captura; se permite exportar archivos ya cerrados. Los trabajadores de observación solo producen datos en memoria. Nunca escriben en la carpeta que se está empaquetando. Las operaciones de almacenamiento local o proveedor USB todavía pueden bloquear; no se promete cancelación de una llamada del kernel.

WebView: se consulta el paquete seleccionado por el framework cuando la API lo ofrece, sin crear una vista. No equivale al proveedor cargado por la APK del usuario ni a una prueba de video. No se inicia EGL en esta versión. Los nombres de módulos/bindings y capacidades declaradas tampoco prueban funcionamiento ni ausencia de malware.

Importación compatible con `tvbase-recognition-1`; el nuevo importador conserva `capture_state` y la referencia a la ficha inicial. El importador 0.1 registraba `unspecified` porque buscaba otro campo, aunque el informe original sí tenía su estado. No se modifican archivos ni catálogos históricos.

Construcción y pruebas: [COMPILACION.json](COMPILACION.json), [evidencia](../../docs/evidencia/RECONOCEDOR-USB-02.md). [Guía USB](LEEME-USB.txt). La corrección requiere prueba física en el MX9; las pruebas de PC no la sustituyen.
