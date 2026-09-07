# Historial local y futura publicación

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

El destino, propietario y visibilidad del repositorio remoto todavía deben definirse. Preparar Git local no crea un repositorio en GitHub ni publica sus archivos. Cuando se elija el destino, revisar el índice y la historia, comprobar que no hay datos privados ni binarios excluidos, agregar el remoto correcto y publicar la rama elegida. Autenticarse mediante el mecanismo de Git/GitHub disponible en la PC, sin guardar tokens en el proyecto ni en la URL del remoto.

La política de distribución de imágenes, APK de terceros y ROM debe decidirse antes de publicar binarios como releases. Git conserva sus manifiestos; no se ha configurado Git LFS, CI, publicación de releases ni actualización automática por el mero hecho de preparar este repositorio.

Git y GitHub permiten seguir cambios del proyecto. No reemplazan el respaldo original del TV, una copia de las claves ni un mecanismo probado de recuperación del dispositivo.

## Registro inicial del 7/9/2026

La rama local es `main`. Se incorporan el estado de la plataforma, el resultado físico fallido0.4 y la entrega0.5 de evidencia sin reinicio, con sus fuentes/pruebas/recibo USB. El primer commit representa el estado reunido hoy; no se inventaron commits anteriores. Consultar `git log -1` para su identificador y autor efectivo.

La [auditoría del índice](evidencia/git-inicial.json) no encontró binarios ni patrones de secretos de alta confianza entre los archivos revisados. `git diff --cached --check` señaló espacios de salidas históricas y líneas finales vacías de dos fuentes; se conservaron para no alterar registros ni las fuentes vinculadas por hash a la release. No se declaró esa comprobación de formato como aprobada. Las pruebas funcionales y la lectura del USB tienen sus recibos separados.

`.gitattributes` normaliza terminaciones de línea en el índice. Los hashes de fuentes/recibos describen los bytes locales usados en la comprobación; no deben confundirse con el hash de una versión del texto normalizada por Git. Para artefactos distribuidos se utiliza siempre su SHA-256 del manifiesto y la lectura del USB.
