# Historial local y publicación pública

## Cierre SD del 8/9/2026 ART

Finalización nativa comprobada, extractor RK1 y guía copiados/releídos. Fuentes nuevas y recibos separados conservan los dos fallos de preparación y su causa observada; el estado vigente ahora es SD lista y extracción física pendiente. Kingston y respaldos previos conservados; publicación exclusivamente del espejo saneado.

## Registro del 8/9/2026 · recovery CNV8b y SD

Se versionan inspector de paquete RKFW/RKAF, variante de firma RK1 del extractor, verificación Java/Python, preparadores SD y documentación del recovery/medio. La herramienta y firmware aportados, el prefijo de la tarjeta y las extracciones permanecen privados. Los recibos anteriores y el respaldo cifrado publicado no se modifican. La publicación usa exclusivamente el espejo saneado.

## Registro del 8/9/2026 · extractor combinado y revisión de servicios

Nuevas fuentes Go/Python y pruebas del extractor independiente, generador de planes y verificador PC; documentación del P271, matriz de componentes heredados, contrato y recibos saneados. Los ZIP ejecutables y planes/datos por unidad permanecen privados. La publicación usa exclusivamente el espejo saneado; no vuelve a subir ni modifica el respaldo cifrado previo.

## Registro del 8/9/2026 · reconocedor autorizado y USB preparado

Se versionan fuentes Java, constructor, importador/pruebas, contrato y guía del reconocedor0.1; recibos saneados de compilación y entrega. La APK y fixtures se conservan en privado. Las capturas futuras deben importarse a directorios privados nuevos; no se publican ZIP, identificadores o drivers adquiridos. La publicación usa el espejo saneado y no reemplaza las releases previas ni el respaldo cifrado.

## Registro del 8/9/2026 · reconocimiento, producto y actualización por perfil

Se agrega el relato del usuario de varios reinicios sin USB, con su alcance explícito y separado de los recibos anteriores. PROP-17 / REQ-18 / ADR-29 documentan reconocimiento sobre Android como primer entregable, medición de WebView/recursos/tráfico, producto común con logo y versiones por perfil compartidas entre USB e Internet. Se actualizan grafo y roadmap; no se implementan aún esos cambios ni se contacta el TV o pendrive.

El respaldo cifrado ya publicado conserva su release y sus recibos; esta publicación documental no vuelve a subirlo. El espejo público contiene documentos y fuentes saneadas. Los originales y claves permanecen privados.

## Registro del 8/9/2026 · instalación física 0.2.2 y Home pendiente

Se versionan la evidencia de instalación terminada, los scripts de adquisición y revisión independiente, el resumen saneado, la incidencia Home y el diseño propuesto de capa común, lotes y actualizaciones. El estado, requisitos, grafo y roadmap distinguen lo instalado de las pruebas pendientes y de los cambios que esperan el OK del usuario.

Los 199 archivos adquiridos, incluidas seis imágenes y la foto, permanecen en el archivo privado local. No se publican datos de usuario, firmware ni registros completos. Los recibos anteriores permanecen inmutables. La publicación sigue usando exclusivamente el espejo saneado de [GitHub](https://github.com/tablerosapp-ctrl/mxqpro4k); los registros siguientes son antecedentes fechados.

## Registro instalador0.2.1 y acceso0.9

La nueva entrega agrega preparación de userdata con seis respaldos, restaurador de cinco particiones corregido para ARM32 y acceso ENV/BCB revisado. Se versionan fuentes, pruebas, recibos y [evidencia actual](evidencia/ENTRADA-ORIGINAL-P291-021.md); los ZIP/APK, extracciones y observaciones crudas permanecen locales. La exclusión `**/privado/` cubre también los nuevos directorios anidados. Preparar el pendrive no equivale a aprobar el método de entrada ni a instalar la ROM.

La copia USB se documenta con su recibo, y la publicación continúa en el espejo saneado existente. No se reescriben releases0.2.0 ni la historia pública por esta revisión.

## Registro 0.2.0 desde originales P291

Se incorporan fuentes de construcción, política de paquetes, auditorías de servicios/gestor, pruebas, manifiestos de las cinco imágenes y recibos de los ZIP de instalación/restauración. [Resultado](evidencia/ROM-ORIGINAL-P291-020.md). El grafo y el estado distinguen verificación PC de instalación física pendiente.

Las adquisiciones, APK, imágenes, ZIP, herramientas, claves y pruebas privadas siguen fuera del historial público. No hubo otra limpieza de USB ni de las versiones anteriores. Se conservan los intentos de construcción fallidos y se documentan sus causas, sin convertirlos en releases. La publicación usa el espejo saneado existente y no fuerza el historial de GitHub.

Git conserva los cambios de fuentes, especificación, decisiones y evidencias revisadas. El pendrive y los archivos de varios GB siguen fuera del repositorio: sus manifiestos, tamaños, orígenes y SHA-256 permiten identificar qué se probó. Un commit acredita una versión de los archivos; no acredita que la ROM haya arrancado ni que una instalación física haya terminado.

## Qué entra al historial

| Grupo | Contenido versionado | Contenido que queda local |
| --- | --- | --- |
| Documentación | README, AGENTS, arquitectura, dossier histórico, `docs/`, árbol legible, grafo y roadmap | Inventario exhaustivo de esta PC (`docs/inventario.json`), capturas/informes crudos privados |
| Componentes propios | Java/XML de Inicio, WebView y Acceso USB; recetas Python; instalador Go y pruebas | APK, ejecutables, clases, dex y cachés |
| ROM candidata y derivadas | Manifiestos de origen, hashes, inventarios, recetas aplicadas, resultados de firma/ext4/payload | Imágenes originales o modificadas, ZIP, extracciones y herramientas |
| Diagnóstico físico | HALLAZGOS, perfiles revisados, scripts de captura; nuevos `resumen-saneado.json` o `evidencia-saneada.json` (también se admiten nombres en mayúsculas) | Informes originales, fotos, volcados, logs y respaldos de cada unidad |
| Operaciones del Kingston | Scripts, estados y resultados JSON con hashes y códigos nativos, conclusiones | Imágenes de respaldo, capturas extensas del dispositivo/Windows y logs completos de Imager |
| Firmas | Huellas de certificados y resultado de verificación | Directorio `claves-desarrollo`, keystore y contraseña; claves privadas de cualquier tipo |

Las reglas concretas están en [`.gitignore`](../.gitignore). No son una orden de borrado. Las fuentes originales, releases verificadas, claves y respaldos deben conservarse en esta PC y mediante respaldo externo independiente. Los archivos de trabajo excluidos pueden seguir siendo dependencias de las recetas: un clon del repositorio no trae por sí solo las herramientas, ROM ni claves necesarias para reproducir una firma idéntica. Consultar [DESARROLLO](DESARROLLO.md), los manifiestos de origen y sus hashes antes de reconstruir.

El mapa y árbol describen el espacio de trabajo completo. Algunos enlaces apuntan deliberadamente a artefactos locales excluidos; serán referencias a archivos ausentes al navegar solo el repositorio remoto. Los SHA y recibos versionados siguen siendo consultables.

## Revisión previa al primer commit

La auditoría inicial encontró la contraseña de firma separada en el directorio privado, no embebida en `compilar-componentes.py`. El código genera/lee ese archivo y entrega su ruta a las herramientas de firma. Se excluye el directorio completo; no cambiar ni regenerar la clave para preparar Git. Las claves públicas de prueba AOSP no son firma de producción; el proyecto conserva su procedencia y huella sin subir los archivos privados descargados.

Los scripts y recibos operativos conservan la identidad estable del Kingston como protección frente a escribir otra unidad. También hay rutas locales y antecedentes con direcciones de red privadas. No son contraseñas, pero la publicación pública de esos identificadores debe revisarse antes de GitHub. No sustituirlos ciegamente en los scripts operativos: crear una configuración local separada si se decide generalizar el proyecto. Los reportes nuevos del TV se guardan localmente y se versiona un resumen revisado con hash del original, fecha, equipo, observaciones y limitaciones; se omiten cuentas, tokens, MAC, números de serie y contenido ajeno al diagnóstico.

No se detectaron tokens de servicios ni claves privadas embebidas en la revisión de fuentes propias. Una búsqueda por patrones no garantiza ausencia total de secretos: revisar siempre los archivos que realmente se incorporarán, especialmente nueva evidencia. La lista de exclusión evita incorporar automáticamente los informes de futuras carpetas de diagnóstico.

En la inspección del 6/9/2026 Git estaba disponible y no había `user.name` ni `user.email` globales configurados. Para registrar esta preparación se eligió **`Codex (registro local)` / `codex@local.invalid`**, una identidad de automatización explícita, temporal y limitada a este repositorio; no representa el nombre ni el correo del usuario. La configuración global permanece intacta. El commit y su autor efectivo se comprueban con `git log -1`; cuando el usuario elija sus datos puede configurar la autoría local para futuros commits sin reescribir el historial por rutina.

## Flujo de trabajo

1. Mantener el repositorio en esta misma carpeta. Comprobar con `git status` qué cambió antes de tocar el USB o generar otra versión.
2. Actualizar la evidencia y [ESTADO](ESTADO.md); conectar el resultado con REQ/ADR/C/VAL/M en [proyecto.json](proyecto.json). Conservar también los fallos y la distinción entre observación, comprobación local e hipótesis.
3. Regenerar y verificar la documentación según [DESARROLLO](DESARROLLO.md). Revisar fuentes y documentación juntas cuando cambie un contrato.
4. Incorporar rutas concretas y revisar `git diff --cached --stat`, `git diff --cached --name-only` y `git diff --cached --check`. Usar `git check-ignore -v RUTA` para entender por qué falta un archivo; no forzar originales privados o binarios al índice.
5. Crear un commit por cambio verificable. Mensaje sugerido: `Documenta fallo de entrada USB en P291 y evidencia del informe`. Incluir en el cuerpo los IDs afectados y la validación efectuada. No marcar una versión como funcional por un commit o una compilación.
6. Para nuevos experimentos, abrir una rama descriptiva y conservar el estado anterior. Una etiqueta de entrega debe enlazar el commit con el manifiesto/hash de los archivos realmente copiados; no mover etiquetas que ya se hayan compartido.

Primer staging recomendado, después de inicializar Git y con las exclusiones activas:

```powershell
git add -- .gitignore .gitattributes AGENTS.md README.md ARQUITECTURA-ANDROID-TV.md PRUEBA-USB.md dossier-s905l2.html docs
git add -- analisis-rom rom-simplificada diagnostico preparacion-usb actualizacion-chrome
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
```

Estos comandos no publican nada. No usar `git add -f` para suplir un archivo excluido sin revisar su función. `.gitignore` tampoco expulsa secretos que ya estuviesen versionados: revisar el índice antes del primer commit evita incorporarlos a la historia.

## Paso posterior a GitHub

El [repositorio público tablerosapp-ctrl/mxqpro4k](https://github.com/tablerosapp-ctrl/mxqpro4k) está publicado. Se utiliza un espejo saneado; [PUBLICACION](PUBLICACION.md) reemplaza el procedimiento antiguo de push directo desde el Git operativo. Para nuevas versiones, revisar índice e historia, crear el commit local y preparar/publicar el espejo con el script documentado. El remoto pertenece únicamente al espejo. La autenticación usa el gestor de credenciales de la PC, sin guardar tokens en el proyecto ni en la URL.

La política de distribución de imágenes, APK de terceros y ROM debe decidirse antes de publicar binarios como releases. Git conserva sus manifiestos; no se ha configurado Git LFS, CI, publicación de releases ni actualización automática por el mero hecho de preparar este repositorio.

Git y GitHub permiten seguir cambios del proyecto. No reemplazan el respaldo original del TV, una copia de las claves ni un mecanismo probado de recuperación del dispositivo.

## Registro inicial del 7/9/2026

La rama local es `main`. Se incorporan el estado de la plataforma, el resultado físico fallido0.4 y la entrega0.5 de evidencia sin reinicio, con sus fuentes/pruebas/recibo USB. El primer commit representa el estado reunido hoy; no se inventaron commits anteriores. Consultar `git log -1` para su identificador y autor efectivo.

La [auditoría del índice](evidencia/git-inicial.json) no encontró binarios ni patrones de secretos de alta confianza entre los archivos revisados. `git diff --cached --check` señaló espacios de salidas históricas y líneas finales vacías de dos fuentes; se conservaron para no alterar registros ni las fuentes vinculadas por hash a la release. No se declaró esa comprobación de formato como aprobada. Las pruebas funcionales y la lectura del USB tienen sus recibos separados.

`.gitattributes` normaliza terminaciones de línea en el índice. Los hashes de fuentes/recibos describen los bytes locales usados en la comprobación; no deben confundirse con el hash de una versión del texto normalizada por Git. Para artefactos distribuidos se utiliza siempre su SHA-256 del manifiesto y la lectura del USB.

## Corrección del recopilador0.6

Se conserva0.5 íntegra y se agrega0.6 en un directorio propio. El cambio documenta dos fallos reales: selección de GMS que agotó la cuota antes de OTAUpgrade, y alias `hash` de mksh que produjo digests vacíos. Los informes crudos siguen fuera de Git; sus hallazgos saneados, la reproducción, las pruebas finales y el recibo USB quedan versionados. El registro del reinicio previo acota el atasco al cierre del sistema sin identificar aún su causa. No se registra una instalación de ROM como conseguida.

## Captura completa y entrada OEM 0.7

En ese hito se incorporaron la captura 0.6 saneada, la auditoría de firma contra el certificado real P291, el análisis del APK OEM y la entrada 0.7. Sus fuentes, pruebas y recibo de lectura USB identifican el entregable. Después, el intento con la ROM completa quedó detenido al 2 %. El historial distingue firma válida, apertura de menú e instalación física pendiente. GitHub todavía no estaba configurado en ese hito.

## Preparación pública del 7/9/2026

Se revisaron todos los blobs de la historia local. No se encontraron claves privadas ni tokens de alta confianza; sí identificadores de la unidad USB, de la PC y el serial del dossier. Se conserva la historia original y se exporta una secuencia equivalente anonimizando esos datos en todas sus versiones. El proceso, sus límites y la integración con otra cuenta se documentan en [PUBLICACION](PUBLICACION.md); las dos revisiones en [COLABORACION](COLABORACION.md). No se publican binarios ni fotos crudas.

## Publicación completada el 7/9/2026

Se creó el repositorio público en la cuenta autorizada, se publicó main sin forzar el historial y se verificó su acceso anónimo. El [recibo](evidencia/publicacion-github.json) identifica el primer commit remoto comprobado y su auditoría. Los commits posteriores de documentación quedan visibles en la historia; el recibo no pretende contener el SHA del mismo commit que lo incorpora. La guía para Claude y ambas hipótesis están incluidas; la revisión externa sigue pendiente.
