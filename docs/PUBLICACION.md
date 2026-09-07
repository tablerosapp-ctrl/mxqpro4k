# Publicación pública y continuidad local

El usuario autorizó publicar en **tablerosapp-ctrl/mxqpro4k**, con visibilidad pública. Claude Desktop se usará desde otra PC y otra cuenta; no se comparten credenciales.

## Qué se publica

Documentación, fuentes propias, recetas, inventarios, hashes y conclusiones saneadas. El historial de main se conserva como una secuencia equivalente, con identidades locales anonimizadas en todas sus versiones. Los commits públicos tienen SHA distintos de los locales porque cambian esos textos.

No se publican claves privadas, contraseñas, tokens, firmware, APK, fotos originales, SDK/herramientas ni registros crudos. El número de serie del dossier, la identidad individual del Kingston, el nombre de esta PC y su ruta de usuario se sustituyen en el espejo. Los originales operativos no cambian: sus guardas y las firmas de los artefactos siguen coincidiendo con lo probado.

**Los preparadores USB publicados contienen identidades anonimizadas y deben rechazar equipos reales hasta configurarlos correctamente.** No sustituir esa comprobación por elegir una letra o un disco cualquiera. Los resultados SHA de fuentes describen los archivos locales originales; una copia saneada o normalizada por Git no tiene necesariamente los mismos bytes. Los hashes de ROM/APK sí identifican los artefactos originales, que no se incluyen.

## Ubicaciones y actualización

| Ubicación en la PC operadora | Función |
| --- | --- |
| Git de la raíz del proyecto | Historia operativa original, artefactos y guardas de esta unidad |
| `privado/publicacion-redacciones.json` | Configuración del dueño/repositorio y sustituciones locales; excluida |
| `.publicacion/repositorio/` | Espejo Git saneado, con remoto origin público; excluido del Git operativo |
| `.publicacion/estado.json` | Relación de commits locales/públicos y última verificación; excluida |
| `docs/herramientas/publicar-github.py` | Exporta, revisa y publica; usa el gestor de credenciales sin guardar tokens |

Antes de cada publicación: actualizar documentación, comprobarla, crear commit local, ejecutar `publicar-github.py --prepare`, revisar el resultado y ejecutar `--publish`. El preparador no accede a GitHub. La publicación exige cuenta exacta, repositorio público, historia sin patrones de secretos, espejo sin cambios ajenos y avance compatible con el remoto. **No usa force-push.** Si el remoto recibió cambios, se detiene hasta revisarlos; no se descartan aportes de otra persona.

El espejo no es una copia de seguridad del firmware. No agregar el remoto público al Git operativo ni hacer un push directo desde allí: esa historia conserva identificadores locales. Si cambian las reglas de anonimización tras publicar, revisar la migración y los hashes antes de continuar; el script no fuerza una reescritura remota.

## Trabajo desde Claude Desktop

El repositorio público se puede leer o clonar sin invitación. Para aportar, usar issues o un fork con pull request desde la otra cuenta. En esta fase conviene devolver las dos revisiones como documentos/issues independientes; [COLABORACION](COLABORACION.md) fija el formato y los límites.

Antes de una nueva exportación, el operador revisa cualquier aporte remoto y lo integra en las fuentes operativas. Si hay commits remotos que no pertenecen a la línea exportada, resolver explícitamente esa integración; el chequeo de avance debe seguir activo. No instalar nada en un TV ni ejecutar preparadores USB como parte de la revisión documental en otra PC.

La comprobación local de documentación incluye binarios y herramientas presentes solo en la PC operadora. En el clon público, los enlaces hacia esos artefactos locales pueden faltar: consultar manifiestos y conclusiones. No declarar pruebas físicas o compilación reproducida a partir de un clon que carece de esas dependencias.
