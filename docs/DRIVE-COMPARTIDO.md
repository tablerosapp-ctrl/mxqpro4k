# Archivos privados compartidos: Drive y GitHub

## Ampliación aprobada y subida para Fable · 12/9/2026

Después de revisar la petición de Fable, explicar los cinco archivos, destinos y un total de **575.330.503 bytes**, el usuario dio su OK explícito. Se subieron exclusivamente esos cinco archivos con la cuenta titular del almacenamiento de Drive. Se comprobaron por lectura posterior sus tamaños, ubicación, propietario y permisos; los SHA256 informados por Google coinciden con la relectura de los originales locales y el manifiesto aprobado. Esta comprobación no fue una descarga integral de los archivos desde Drive.

Rutas relativas a la carpeta privada compartida:

| Ruta | Bytes | SHA256 |
| --- | ---: | --- |
| `extractor-rk3-release-20260909-02/TVBASE-EXTRACTOR-0.3-RK3-ARM32-RECOVERY.zip` | 1463158 | `ff9595f7a64a64df77f1c1d4904a896922e62a6be51d6a9e94247e79da985d01` |
| `extractor-rk3-release-20260909-02/COMPILACION.json` | 25906 | `5480f011b29597e9e2533056066dc3952787a616b64e926f21c72db3cae2800a` |
| `extractor-rk3-build-20260909-01/FALLO.json` | 1134 | `7af66c06ff0ee758fb4b6a44b17b272718c5973cd325b0715fcbac41232530ae` |
| `extractor-rk3-build-20260909-01/compilar-fallido.py` | 20300 | `fc858dfe736742459cb2bdc3db40fee45709b214c5193d3b9f0b101a0824c5bb` |
| `releases/P291/0.2.2/TVBASE-P291-A9-0.2.2-RECOVERY.zip` | 573820005 | `163d4ce6e6fd4e02f06cb6646c53c259d1d3100547ee5c616c578782c3e54421` |

Los cuatro archivos RK3 se agregaron a sus carpetas existentes. El instalador P291 se colocó en la nueva ruta `releases/P291/0.2.2`. La revisión encontró un ZIP homónimo de solo 15 bytes en una carpeta de pruebas: contiene `fixture-new-zip` y no es un instalador. Se conserva como evidencia histórica; usar la ruta y el hash de esta tabla.

`FALLO.json` y `compilar-fallido.py` documentan el fallo de una guarda del primer build en PC, no un intento de instalación ni un nuevo fallo físico del TV. El ZIP RK3 es el extractor específico de RK3229-C; su vinculación privada permanece en el binario y no habilita otros equipos. El P291 es el instalador 0.2.2, no el restaurador adicional de 913.294.443 bytes. No se subieron ese restaurador, respaldos, userdata, claves de firma ni credenciales de Google.

El conector cargó los cuatro archivos pequeños. Rechazó el P291 antes de transmitirlo porque 573.820.005 bytes superan su límite de 536.870.912 bytes; se cargó el ZIP íntegro desde la interfaz de Drive, sin dividirlo ni reconstruirlo. No se modificaron permisos de la carpeta ni originales locales. Los recibos con IDs y enlaces permanecen privados.

**Para Fable:** descargar los archivos necesarios desde estas rutas y verificar el SHA256 de la tabla. Si ya tiene una `BASELINE.json` anterior, estos cinco IDs nuevos quedan fuera de esa lista: `inventory` no la amplía y `select` no los admite automáticamente. Puede descargarlos manualmente desde Drive a una carpeta de trabajo separada y verificar sus hashes. No borrar ni reemplazar la baseline para eludir ese control. Esta entrega no implementa una ampliación automática del programa de sincronización.

La conexión rclone y la revisión horaria siguen siendo de solo lectura y mantienen su selección previa. Esta autorización se limita a los cinco archivos de la tabla; el resto de faltantes sigue pendiente de justificación y OK. No hubo contacto con TV, SD o USB; el resultado físico RK3 continúa pendiente en esta sesión.

## Alcance inicial autorizado el 12 de septiembre de 2026

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

## Uso del plan de 5 TB

La conexión utiliza el mismo almacenamiento de Google Drive de la cuenta propietaria. El proyecto exclusivo de Google Cloud identifica el cliente que accede a Drive; no cambia el destino de los archivos ni crea almacenamiento Cloud Storage. No se activó facturación ni prueba gratuita.

Para aprovechar el plan del usuario, las futuras subidas grandes autorizadas deben realizarse con la cuenta titular de ese almacenamiento. Fable puede consultar y descargar con su propia cuenta. En una carpeta compartida de Mi unidad, el espacio se descuenta al propietario de cada archivo: subir desde otra cuenta consume el almacenamiento de esa otra cuenta. [Regla oficial de Google](https://support.google.com/drive/answer/9312312?hl=es). Los 5 TB son la capacidad total del plan, compartida con los otros servicios aplicables y el contenido que ya ocupa espacio; no 5 TB libres exclusivos para TV Base.

Los límites de solicitudes de la API son independientes del espacio ocupado. La configuración actual sigue siendo de lectura: esta explicación no autoriza subidas adicionales.

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
python colaboracion/drive/conectar.py --rclone C:/Herramientas/rclone.exe --folder-id ID_RECIBIDO_DEL_USUARIO --client-json C:/ConfiguracionPrivada/cliente-escritorio.json
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe inventory
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe compare --manifest privado/drive-compartido/BASELINE.json
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe select --path RUTA_EXACTA_DEL_INVENTARIO
python colaboracion/drive/drive.py --rclone C:/Herramientas/rclone.exe refresh
```

La conexión requiere un cliente OAuth propio de tipo escritorio; el cliente compartido de rclone ya no debe utilizarse. El JSON se entrega por un canal privado y se guarda fuera del clon y de Drive. El JSON identifica la aplicación; no sustituye la autorización de la cuenta de cada participante ni contiene su token de usuario. El proyecto ya está en producción: no hace falta registrar a Fable como usuario de prueba. Su cuenta Google debe tener acceso a la carpeta compartida y autorizar la aplicación por sí misma; la cuenta GitHub es independiente. La configuración y una descarga real en la otra PC todavía no fueron comprobadas desde esta sesión.

El inicio de sesión se completa en el navegador. El log de conexión puede contener secretos: queda fuera del proyecto y no se pega en chats ni PR. Si la conexión se interrumpe, revisar el estado y usar `--reconnect` únicamente con el mismo JSON y la misma carpeta. La migración inicial desde el cliente compartido usa `--replace-shared-client`, verifica alcance e identidad, conserva la configuración previa y no imprime credenciales. Una configuración ajena o de otro cliente se rechaza. No repetir una migración ya completada. [Configuración oficial](https://rclone.org/commands/rclone_config_create/).

Los objetos descargados quedan bajo `privado/drive-compartido/objetos`, separados por ID y hash; las selecciones y recibos están junto a ellos. No subir esa carpeta nueva sin autorización: contiene copias y metadatos privados de la sincronización. El usuario puede ver la selección en los JSON de `seleccion`; detener la revisión periódica no borra objetos.

## Verificación y estado operativo

Las pruebas locales del programa cubren rutas inseguras, nombres duplicados, falta de hash, órdenes de escritura rechazadas, selección fuera del alcance, cambio de ID, conservación de versiones y descarga corrupta preservada. Son pruebas PC con proveedor simulado; no sustituyen una transferencia real.

La lectura del conector ya confirmó acceso a la carpeta. La conexión local y su primera transferencia están acreditadas por los recibos privados de esta revisión. No afirmar sincronización continua por haber instalado un conector: requiere conexión local válida, selección de archivos y revisión periódica activa. Con la PC apagada o sin Internet no hay actualizaciones locales; Drive sigue disponible para la otra PC.

**Estado actualizado:** la segunda autorización local sí terminó y dejó un token de solo lectura. El primer inventario recursivo falló con HTTP 403 `RATE_LIMIT_EXCEEDED` en el proyecto compartido del cliente de rclone: no es un error de cuota de almacenamiento. La [documentación de rclone](https://rclone.org/drive/#making-your-own-client-id) indica que ese cliente compartido se retira durante 2026 y exige un cliente propio.

El usuario autorizó un proyecto exclusivo para TV Base. Se creó el proyecto y se habilitó Google Drive API, sin activar facturación. El usuario autorizó explícitamente aceptar la Política de Datos del Usuario de los Servicios de las APIs de Google. Se creó la aplicación y su cliente de escritorio, se descargó y verificó una copia privada del JSON fuera del proyecto, y se migró la conexión conservando la configuración anterior fuera de Git y Drive. El usuario completó la nueva autorización: proceso terminado con código 0, token presente, cliente propio y permiso `drive.readonly`.

**Aplicación en producción, confirmado el 12/9/2026.** El titular autorizó expresamente que cualquier cuenta Google pueda autorizar la aplicación. Tras esa autorización se confirmó el diálogo y la consola mostró «En producción». El rechazo anterior de revisión automática queda como antecedente resuelto por esa autorización específica; no se eludió mediante otro mecanismo.

El [aviso de privacidad vigente](DRIVE-PRIVACIDAD.md) está publicado y guardado en Google junto con la página del repositorio y el dominio de sus enlaces. Se conserva la [propuesta anterior](DRIVE-PRIVACIDAD-PROPUESTA.md). El cambio de audiencia no publica archivos ni concede acceso a la cuenta del propietario: cada participante inicia sesión y autoriza su propia cuenta, con los permisos de Drive que ya tenga.

Se renovó la autorización local **después** del paso a producción. El proceso terminó con código 0; se comprobó que el token de renovación cambió, el cliente y la carpeta son los mismos y el permiso sigue siendo `drive.readonly`. La revisión posterior de la selección terminó con código 0, un archivo comprobado y cero errores. La configuración anterior se conserva fuera del proyecto. No repetir migración ni reconexión sin una necesidad nueva.

La regla de siete días corresponde a tokens emitidos con estado Prueba; ya se obtuvo una nueva autorización en producción. Esto no garantiza acceso indefinido: Google contempla revocación, inactividad y otras causas de invalidez ([fuente oficial](https://developers.google.com/identity/protocols/oauth2#expiration)). Producción tampoco equivale a certificación de la aplicación por Google: la consola muestra un límite de 100 usuarios para permisos sin aprobación. No se realizó un proceso formal de verificación; no hace falta afirmar que esté verificada para acreditar el acceso observado.

La revisión horaria se actualizó para reconocer el nuevo estado y conserva frecuencia, alcance y silencio cuando no hay novedades. Las subidas siguen deshabilitadas; esta autorización no amplía la selección ni incorpora archivos faltantes.

El inventario propio terminó con código 0: **9.355 archivos nativos / 6.421.648.788 bytes (5,98 GiB)**. La comparación local terminó con **9.355 `equal_sha256`**, sin diferencias. Se descargó a una copia separada un informe existente de 288 bytes, se comprobó su identidad remota antes y después y su SHA256 local; una segunda revisión terminó con código 0. Son evidencias reales adicionales a las siete pruebas locales del programa, que también pasaron. No se subió ni borró contenido de Drive.

La primera solicitud de descarga coincidió con la comparación todavía activa y fue rechazada por el bloqueo de operación, antes de transferir; tras finalizar la comparación se realizó una nueva descarga correctamente. No se eliminó el bloqueo de otra operación.

Se creó una revisión horaria en esta tarea de Codex para `refresh`: solo actualiza copias de archivos expresamente seleccionados y conserva versiones. **La selección inicial contiene únicamente el informe de prueba de 288 bytes**, no los 9.355 archivos ni todos los gigabytes. El resto ya coincide con los originales locales y se descarga/selecta en cada PC según necesidad. La revisión no incorpora nuevos IDs ni publica cambios locales. Su ejecución depende de que la aplicación y el equipo estén disponibles, de la conexión y de los límites de uso; no es un servicio independiente de Windows. Registro de creación conservado privadamente; las dos primeras revisiones programadas terminaron con código 0, sin cambios ni errores, con recibos bajo privado. [Tareas programadas](https://learn.chatgpt.com/docs/automations?surface=app).

**Comparación recursiva de rutas:** se registraron 23.266 archivos locales / 52.066.303.898 bytes sin la misma ruta en la lista remota, excluyendo los registros nuevos de esta integración. De ellos, 37.266.285.610 bytes son `backup-github-20260908`; los demás suman 14.800.018.288 bytes. Esta revisión de ausencias no buscó copias idénticas bajo otros nombres y no acredita que todo falte por contenido. No atribuir la causa a un fallo de subida sin evidencia.

Entre las rutas ausentes se encuentran cinco imágenes de la adquisición de instalación P291 (incluida `data.img`), dos respaldos de entrada, copias de la APK del actualizador, parte de `original-p291-empaquetado` y cachés de compilación. No proponer subir todo como bloque: userdata puede contener datos de la unidad; cachés y copias de trabajo no tienen la misma utilidad que originales y recibos. Fable ya puede trabajar con el material disponible; evaluar faltantes concretos cuando una tarea los requiera.

**Faltante observado:** `extractor-rk3-release-20260909-02` aparece vacía tanto en el conector como en el navegador. La copia local del ZIP RK3 sigue conservada y verificada, 1.463.158 bytes; su [construcción y alcance](evidencia/EXTRACTOR-SD-03.md) están documentados. No se subió. Puede ser útil para que Fable contraste el paquete ejecutable con las fuentes, pero requiere aprobación específica como archivo faltante; el inventario recursivo confirmó que también falta su `COMPILACION.json` de 25.906 bytes. Ambos suman 1.489.064 bytes y pueden proponerse juntos para revisar RK3, con autorización antes de subir. No se determinó por qué quedó vacía.

Antes de ampliar a subidas: lista de archivos exactos, motivo, tamaños, origen/hash y aprobación. Después, implementar una versión separada con control de conflictos. No usar `rclone sync`, `bisync --resync` ni sincronizar `privado` completo como atajo: [sync puede borrar elementos del destino](https://rclone.org/commands/rclone_sync/).
