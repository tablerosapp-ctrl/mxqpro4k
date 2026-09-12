# Propuesta de aviso de privacidad de TV Base Drive

**Borrador para aprobación del titular. No se configuró como política publicada en Google.**

TV Base Drive es una herramienta local de colaboración técnica para consultar una carpeta de Google Drive compartida por su propietario y descargar archivos seleccionados. El código y la documentación se encuentran en el [repositorio TV Base](https://github.com/tablerosapp-ctrl/mxqpro4k).

La versión actual solicita acceso de solo lectura a Google Drive. Ese permiso permite leer archivos accesibles para la cuenta; la configuración del programa limita sus operaciones a la carpeta elegida. Esta limitación local no equivale a un permiso de Google restringido exclusivamente a esa carpeta.

El programa consulta nombres, identificadores, tamaños, fechas y hashes para inventariar y comprobar los archivos. Solo descarga los archivos seleccionados dentro del inventario autorizado. Las copias, versiones y registros se conservan en la computadora de cada participante. Los originales locales y los archivos de Drive no se reemplazan ni borran por la herramienta. Esta versión no realiza subidas.

Las credenciales se guardan localmente fuera del repositorio y de la carpeta compartida. Cada participante autoriza su propia cuenta. El programa se conecta a Google para autenticar y consultar Drive; no incorpora un servidor de TV Base al que envíe esos archivos, ni funciones de publicidad, venta de datos o entrenamiento de modelos. Si un participante entrega archivos a una herramienta de IA u otro servicio, esa acción es independiente de esta conexión y requiere atender los permisos y condiciones de ese servicio.

El acceso compartido depende de los permisos configurados por el propietario en Google Drive. El usuario puede revocar la autorización desde la seguridad de su cuenta Google y detener las revisiones locales. Revocar el acceso no elimina las copias previamente descargadas: su conservación y eliminación se gestionan en cada computadora. No existe un plazo automático de borrado en esta versión.

Las consultas sobre el acceso pueden dirigirse al correo de asistencia que muestra la pantalla de consentimiento de TV Base Drive. No incluir archivos privados, claves, tokens ni identificadores de equipos en las incidencias públicas de GitHub.

El aviso deberá revisarse antes de ampliar permisos, habilitar subidas o cambiar dónde se procesan o conservan los datos.
