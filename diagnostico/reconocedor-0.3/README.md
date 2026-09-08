# Reconocimiento TV Base 0.3

Corrige el guardado en un equipo declarado Rockchip por el usuario, con carcasa MXQ Pro 4K 5G. Sus fotos de 0.2 muestran `ActivityNotFoundException` para `ACTION_OPEN_DOCUMENT_TREE` y ausencia de un destino detectado automáticamente. La ficha inicial quedó conservada según la aplicación; no hay un ZIP de ese equipo en el USB recibido. No se conoce su DT exacto ni la causa precisa de la falta de acceso.

La detección 0.2 examinaba un solo nivel de tres directorios. La 0.3 agrega lectura acotada de mountinfo/mounts, rutas externas conocidas y contenedores OEM anidados, hasta tres niveles y 128 directorios. Un selector dentro de la APK muestra los destinos con el marcador correcto; el selector de Android se ofrece únicamente si existe. No se crean marcadores ni se busca dentro de datos privados. Los aliases se agrupan por identidad dev/inode del directorio o ruta canónica coincidente; igual contenido del marcador no basta para fusionar dos unidades. Antes de escribir se revalida identidad y marcador. No es una prueba independiente de hardware USB ni de permiso de escritura.

La búsqueda tiene un único trabajador propio, plazo de espera de ocho segundos y resultados inmutables. Si la llamada continúa bloqueada, el trabajador no se reemplaza. El trabajador de inventario heredado es independiente; ninguna de esas consultas escribe archivos de sesión. La revalidación, copia y sincronización posteriores no tienen un plazo absoluto. Las comprobaciones por rutas no equivalen a inmunidad frente a modificaciones concurrentes hostiles de sus ancestros.

## Alternativa explícita sin selector Android

El botón **Guardar en Descargas para copiar al USB** crea una copia local verificada bajo `Downloads/TVBASE-PARA-COPIAR`. Desde una ficha inicial 0.2 o 0.3 puede completar el inventario sin releer DT. El usuario debe copiar la carpeta con Archivos al USB. Esta elección amplía ADR-32: se exige persistir la ficha inicial en el destino elegido antes de las consultas adicionales, distinguiendo copia local y copia USB.

`LocalExport` conserva ZIP distintos, usa archivos exclusivos, sincroniza y relee; un archivo final incompleto o diferente se rechaza, no se sobrescribe. El recibo `.local.json`, schema `tvbase-recognition-local-export-1`, declara `usb_copy_verified=false` y no acredita sincronización de directorio. Un corte durante publicación puede dejar un archivo incompleto sin recibo: conservarlo y revisar. No se llama a `getExternalFilesDirs` durante búsqueda, porque esa API puede crear carpetas.

La copia local no sortea los permisos de almacenamiento. Si Android niega acceso a Descargas, se conserva la ficha privada y se informa el fallo. La aplicación no incorpora red, root, ADB, cambios de autenticación, reinicio ni flash. No acredita ausencia de malware.

## Continuidad y pruebas

Paquete/firma anteriores conservados; actualizar sin desinstalar ni borrar datos. El importador [0.2](../reconocedor-0.2/importar-informes.py) sigue validando los ZIP del schema existente, incluyendo `parent_capture_id`. Para una devolución manual, revisar también `TVBASE-PARA-COPIAR` en la raíz USB y conservar los recibos locales como tales. No convertirlos retrospectivamente en recibos de exportación Android a USB.

[Construcción](COMPILACION.json), [pruebas PC](PRUEBAS-PC.json), [entrega](../../docs/evidencia/RECONOCEDOR-USB-03.md), [guía USB](LEEME-USB.txt) y [variantes capturadas](../reconocimiento-20260908-rk3229-usb/HALLAZGOS.md). La ejecución 0.3 en el equipo que falló sigue pendiente.

Fuentes de las decisiones: formato de [mountinfo](https://www.kernel.org/doc/html/latest/filesystems/proc.html), permisos/alcance de [almacenamiento externo de la aplicación](https://developer.android.com/reference/android/content/Context#getExternalFilesDirs(java.lang.String)) y [StorageManager](https://developer.android.com/reference/android/os/storage/StorageManager). La 0.3 no depende de que `getExternalFilesDirs` enumere un USB transitorio.
