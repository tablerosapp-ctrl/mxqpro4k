# Archivos privados compartidos: Drive y GitHub

## Alcance autorizado el 12 de septiembre de 2026

El usuario compartió en Drive parte de `privado` para trabajar con Fable desde otra PC y otra cuenta. Autorizó revisar y preparar la sincronización **solo del contenido ya subido**. No subir archivos omitidos ni incorporar futuras capturas automáticamente: antes explicar su utilidad, tamaño y destino y obtener su OK. No se autorizaron borrados locales ni en Drive. El enlace de la carpeta y sus IDs se guardan localmente; solicitar el enlace al usuario en la otra sesión, sin publicarlo en este repositorio.

GitHub conserva código, contratos, grafo y conclusiones saneadas. Drive conserva los insumos privados que el usuario decidió compartir. La disponibilidad de un archivo en Drive no acredita integridad de una captura ni autoriza a ejecutar un instalador o trasladar drivers entre placas. [Estado técnico](ESTADO.md), [relevo](ENTREGA-FABLE.md), [colaboración](COLABORACION.md).

## Qué significa el respaldo de GitHub

**No reemplazar lo subido por `backup-github-20260908`.** Esa carpeta prepara y comprueba el respaldo del P291; no incluye el material Rockchip y no constituye el espacio de trabajo completo. Contiene también la clave de descifrado, que debe permanecer separada. El respaldo cifrado ya está publicado: [release P291](https://github.com/tablerosapp-ctrl/mxqpro4k/releases/tag/respaldo-p291-20260908), [alcance y recuperación](RESPALDO-GITHUB.md).

El inventario local de esta revisión contó 58.487.952.686 bytes en 32.621 archivos (54,47 GiB), antes de generar los nuevos registros de Drive. `backup-github-20260908` representa 37.266.285.610 bytes (34,71 GiB):

| Contenido | Bytes | Función |
| --- | ---: | --- |
| `recuperacion-probada` | 19.248.744.678 | Salidas de la comprobación de recuperación en PC; no una nueva captura de TV. |
| `release-assets` | 4.504.908.410 | Partes cifradas y manifiesto destinados a la release. |
| `TVBASE-P291-RESPALDO-20260908.zip.age` | 4.504.905.988 | Archivo cifrado antes de dividirlo. |
| `RESPALDO-PRIVADO.zip` | 4.503.806.236 | Archivo previo al cifrado. |
| `VERIFICACION-DESCIFRADA.zip` | 4.503.806.236 | Salida usada para comprobar el descifrado. |

Estos tamaños explican la acumulación de copias de trabajo, sin afirmar igualdad de todos sus bytes a partir del tamaño. No se borró nada. No hace falta subir esta carpeta completa para la colaboración actual; si en el futuro se necesita un insumo exclusivo, proponer ese archivo concreto, sin incluir la clave por defecto.

La comparación inicial encontró 108 entradas en la raíz de Drive. Además del respaldo, no aparecen dos carpetas locales de pruebas de solo 47.900 y 44.386 bytes. No se identificó otra carpeta omitida de 9 GiB en ese nivel. **La coincidencia de carpetas no prueba que sus archivos internos estén completos**: el control por archivo y SHA es un paso separado. Los nuevos registros de esta revisión también quedan fuera del alcance subido.

## Diseño de sincronización de esta etapa

La conexión local usa rclone con permiso Google `drive.readonly`. Las credenciales viven en `LOCALAPPDATA/TVBaseDrive`, fuera del repositorio y de `privado`; cada PC inicia sesión con su propia cuenta. El límite `root_folder_id` dirige el programa a la carpeta compartida, pero no reduce por sí mismo el alcance del permiso OAuth sobre la cuenta. No copiar tokens entre PCs. [Documentación oficial de Drive en rclone](https://rclone.org/drive/).

El [programa](../colaboracion/drive/drive.py) ofrece:

1. `inventory`: obtiene un inventario recursivo de archivos nativos con ID, ruta, tamaño y SHA256. Conserva la primera lista como `BASELINE.json`; inventarios posteriores no amplían automáticamente el alcance. Omite atajos y documentos de los editores Google, que no son imágenes o archivos binarios originales.
2. `compare`: compara las rutas remotas con `privado` local, incluyendo SHA cuando el tamaño coincide. No rellena faltantes, borra ni reemplaza. Un inventario no es una instantánea atómica de Drive: repetir la comprobación si alguien estaba subiendo/modificando archivos.
3. `select --path`: descarga un archivo de la lista inicial, comprueba ID y SHA antes/después y guarda un objeto local separado. Para usar una carpeta, Fable selecciona sus archivos concretos según el inventario, sin dar por autorizado todo lo que se agregue después.
4. `refresh`: revisa únicamente los IDs seleccionados; si cambia el contenido de un archivo existente, conserva la nueva versión junto a la anterior. No modifica las imágenes, recibos ni fuentes originales del proyecto. Un cambio de ID, descarga interrumpida o hash incorrecto detiene ese archivo y conserva el resultado para revisar.

Esto permite tener actualizada la **selección local de archivos compartidos**, sin descargar todos los gigabytes en cada PC. No es un espejo bidireccional de `privado`: **las subidas están deshabilitadas** durante esta etapa. Los archivos nuevos u omitidos no se incorporan por existir dentro de una carpeta conocida. El código no incluye órdenes de subida ni borrado de Drive. Tampoco propaga borrados locales/remotos.

Los originales sellados siguen siendo inmutables. Para trabajar sobre ellos, crear un derivado aparte y registrar procedencia/hash; recibir una versión cambiada no convierte esa versión en evidencia válida. Las propuestas de Fable y el código se intercambian por PR. Para subir nuevas capturas, derivados o entregables a Drive, registrar primero la autorización concreta del usuario.

## Preparación de la otra PC de Fable

Instalar Git, Python 3.11 o posterior y rclone. En esta PC se preparó rclone 1.75.1 de la [distribución oficial](https://rclone.org/downloads/), comprobado con su SHA256SUMS servido por HTTPS; no se verificó adicionalmente una firma GPG independiente. Mantener el ejecutable fuera de Git. Python 3.11 es necesario para `hashlib.file_digest`.

Clonar el [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k), leer esta guía y pedir al usuario el enlace privado de Drive. La cuenta Google de esa PC debe poder ver la carpeta; no es necesario que sea la misma cuenta que usa GitHub. Cada PC mantiene configuración, lista seleccionada, caché y registros propios. No ejecutar la publicación del espejo ni preparadores de USB desde el clon público.

Desde la raíz del clon, sustituyendo los valores de ejemplo por rutas reales y el ID recibido privadamente:

```powershell
python colaboracion/drive/conectar.py --rclone C:/Herramientas/rclone.exe --folder-id ID_RECIBIDO_DEL_USUARIO
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe inventory
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe compare --manifest privado/drive-compartido/BASELINE.json
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe select --path RUTA_EXACTA_DEL_INVENTARIO
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe refresh
```

El inicio de sesión se completa en el navegador. El log de conexión puede contener secretos: queda fuera del proyecto y no se pega en chats ni PR. Si la conexión se interrumpe y deja configuración parcial, revisar el estado; el script no la reemplaza automáticamente. [Configuración oficial](https://rclone.org/commands/rclone_config_create/).

Los objetos descargados quedan bajo `privado/drive-compartido/objetos`, separados por ID y hash; las selecciones y recibos están junto a ellos. No subir esa carpeta nueva sin autorización: contiene copias y metadatos privados de la sincronización. El usuario puede ver la selección en los JSON de `seleccion`; detener la revisión periódica no borra objetos.

## Verificación y estado operativo

Las pruebas locales del programa cubren rutas inseguras, nombres duplicados, falta de hash, órdenes de escritura rechazadas, selección fuera del alcance, cambio de ID, conservación de versiones y descarga corrupta preservada. Son pruebas PC con proveedor simulado; no sustituyen una transferencia real.

La lectura del conector ya confirmó acceso a la carpeta. La conexión local y sus primeras transferencias se acreditarán mediante recibos nuevos en esta revisión. No afirmar sincronización continua por haber instalado un conector: requiere conexión local válida, selección de archivos y revisión periódica activa. Con la PC apagada o sin Internet no hay actualizaciones locales; Drive sigue disponible para la otra PC.

Antes de ampliar a subidas: lista de archivos exactos, motivo, tamaños, origen/hash y aprobación. Después, implementar una versión separada con control de conflictos. No usar `rclone sync`, `bisync --resync` ni sincronizar `privado` completo como atajo: [sync puede borrar elementos del destino](https://rclone.org/commands/rclone_sync/).
