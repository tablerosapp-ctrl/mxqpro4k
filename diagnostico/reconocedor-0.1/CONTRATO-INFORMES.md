# Reconocedor 0.1: exportación e importación de informes

Este contrato separa **integridad del archivo**, **resultado del diagnóstico** y
**compatibilidad para instalar**. Un ZIP íntegro puede describir una captura
parcial o fallida. Importarlo no convierte un perfil candidato en uno calificado.
La importación opera solo en PC: no consulta el TV, modifica el USB ni ejecuta
drivers. Las capturas anteriores y sus recibos permanecen intactos.

## Archivo exportado

Carpeta del medio: `TVBASE-RECONOCIMIENTO/INFORMES`.

Nombre: `TVBASE-<profile>-<installationId8>-<sessionUUID8>.zip`.

- `profile` coincide exactamente con `suggested_profile`: de 1 a 64 caracteres
  minúsculos ASCII, letras, números, `_` o `-`; empieza por letra o número.
  La APK usa `desconocido` cuando no hay candidato, o una familia con sufijo
  `-desconocido`; el importador también admite `unknown`. La confianza será `unknown`.
- `installationId8` son los primeros ocho caracteres hexadecimales de `device_id`
  sin guiones; `sessionUUID8`, los de `capture_id` sin guiones.
- Los UUID completos y canónicos, en minúsculas, están dentro del informe.
  Los ocho caracteres del nombre no sustituyen la identidad completa.
- `device_id` es estable para esa instalación de la APK. Reinstalarla o borrar
  sus datos puede cambiarlo; clonar sus datos puede duplicarlo. No acredita una
  identidad física ni debe sustituir la comprobación individual antes de instalar.

Entradas obligatorias: `informe.json` y `manifest.json`, UTF-8 sin BOM.
El resto de los archivos solo puede estar bajo `details/` o `drivers/`.
No hay entradas de directorio explícitas ni archivos fuera de esos espacios.
Los nombres exportados deben ser seguros para Windows; si una ruta original no
lo es, el recolector elige un nombre seguro y conserva la ruta original únicamente
en sus metadatos. No exporta symlinks como enlaces ejecutables.

### informe.json

Campos obligatorios:

| Campo | Contrato |
|---|---|
| `schema` | `tvbase-recognition-1` |
| `capture_id` | UUID completo de esta captura |
| `device_id` | UUID completo de la instalación de la APK |
| `suggested_profile` | Candidato, por ejemplo `p291`, `p271` o `unknown` |
| `profile_confidence` | `declared`, `corroborated` o `unknown`; declaración del recolector, no aprobación del importador |
| `display_name` | Nombre visible no vacío, hasta 256 caracteres; no es identidad fuerte |
| `android` | Objeto con los metadatos Android disponibles |
| `hardware` | Objeto con las observaciones de hardware y sus límites |
| `webview` | Objeto con la evidencia del proveedor y su alcance |
| `export_limits` | Objeto con omisiones, denegaciones, errores, presupuestos y límites de exportación |

Se admiten campos adicionales de datos, sin interpretarlos como instrucciones.
El exportador puede incluir `capture_status`; el importador lo conserva. También
admite `status` como dato de resultado si falta el primero. No exige que todas las
etapas hayan concluido correctamente. Los metadatos vacíos son preferibles a
inventar una lectura no disponible.

### manifest.json

Objeto con exactamente `schema`, `capture_id` y `files`:

```json
{
  "schema": "tvbase-recognition-files-1",
  "capture_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "files": [
    {"path": "informe.json", "bytes": 123, "sha256": "<64 caracteres hexadecimales minúsculos>"}
  ]
}
```

El ejemplo solo describe la forma. El tamaño y la huella se calculan sobre los
bytes reales. Cada entrada tiene exactamente `path`, `bytes` y `sha256`.
La lista incluye `informe.json` y todos los archivos de `details/` y `drivers/`;
excluye el propio `manifest.json`. El `capture_id` debe coincidir con el informe.
No se permiten entradas adicionales, duplicadas ni omitidas.

**El manifiesto no está firmado.** CRC y SHA comprueban coherencia e integridad,
pero no impiden que alguien sustituya conjuntamente archivos y manifiesto.
El hash integral del ZIP conservado en PC vincula la copia adquirida con su
contenido; tampoco es una prueba de identidad física o de autenticidad del TV.

## Límites y validación previa

- Hasta 20.000 entradas, incluido el manifiesto.
- Hasta 128 MiB por archivo; todo archivo terminado en `.json`, hasta 16 MiB.
- Hasta 2,5 GiB descomprimidos por captura y 3 GiB para el ZIP completo.
  El presupuesto de copia previsto para el recolector es 1,5 GiB; los límites
  del importador dejan margen y no prometen que todos los drivers sean legibles.
- Directorio central de hasta 64 MiB, contado antes de cargarlo con `zipfile`.
  Los límites no necesitan contadores u offsets ZIP64 en el directorio final;
  sus valores centinela se rechazan. No se admiten archivos multidisco.
- ZIP almacenado o DEFLATE, sin cifrado interno. El importador no acepta
  ejecutables autoextraíbles ni bytes añadidos después del final del ZIP.
- Rutas de hasta 1024 bytes UTF-8 y componentes de hasta 255 unidades UTF-16.
  Se rechazan rutas absolutas, `..`, `.`, componentes vacíos, barras invertidas,
  `:`, caracteres de control, nombres reservados de Windows y terminaciones
  punto/espacio. También duplicados por mayúsculas o normalización Unicode NFC,
  y rutas que sean a la vez un archivo y el padre de otro.
- Se rechazan symlinks, nodos especiales, directorios explícitos y cabeceras o
  datos superpuestos. El origen local tampoco puede atravesar enlaces o junctions.
- Cada entrada se lee con límites antes de copiar el ZIP: CRC y SHA exactos,
  tamaño del manifiesto igual al del archivo y listado completo sin extras.
  Se rechazan claves JSON duplicadas, números no finitos, sustitutos Unicode
  aislados y estructuras excesivas. Los tamaños deben ser enteros, no booleanos.
- Por importación: hasta 1024 ZIP y hasta 64 MiB de `informe.json` acumulados.
  Si se supera el presupuesto de metadatos, dividir el lote.

Los `.json` adicionales se comprueban como archivos por tamaño, CRC y SHA; el
importador interpreta únicamente `informe.json` y `manifest.json`. No ejecuta
contenido, extrae drivers ni intenta corregir capturas.

## Uso del importador en PC

Desde la raíz del proyecto:

```text
python diagnostico/reconocedor-0.1/importar-informes.py --source CARPETA_INFORMES --verify-only
python diagnostico/reconocedor-0.1/importar-informes.py --source CARPETA_INFORMES --output CARPETA_NUEVA_DEL_PROYECTO
```

`--source` es una carpeta explícita: lectura sin recursión de todos sus `.zip`.
Se informa cuántas entradas no ZIP se omitieron. No se identifica un pendrive
por su letra para modificarlo; este programa nunca escribe en el origen.

`--verify-only` no crea archivos, incluso si se proporciona `--output`.
Para importar, el destino debe ser nuevo, estar dentro del proyecto y tener su
directorio padre ya creado. Origen y destino no pueden contenerse entre sí.
Un destino existente se rechaza; no se fusionan catálogos ni se sobrescriben
capturas antiguas. Todos los ZIP se validan antes de crear el destino.

```text
CARPETA_NUEVA/
└── privado/
    ├── zips/                     # ZIP completos copiados y releídos
    ├── catalogo.json             # Solo al completar todas las copias
    └── IMPORTACION-INCOMPLETA.json # Solo ante fallo durante conservación
```

La copia usa un archivo `.parcial`, sincroniza el archivo, comprueba el SHA
calculado al copiar y vuelve a leer el destino. Solo entonces conserva el nombre
final. No se acredita flush del directorio o del volumen de Windows: el índice
declara `directory_fsync_verified=false`. Ante fallo quedan las copias y parciales
de la carpeta nueva para revisión; no hay borrado ni reintento automático.

El catálogo conserva cada captura, sus metadatos y el resultado declarado. Agrupa
por UUID completo de instalación de la APK y muestra perfiles candidatos. Si un
mismo UUID informa distintos perfiles conocidos, señala conflicto para revisión.
No deduce que sean dos TV distintos ni elige automáticamente el último perfil.
Un `capture_id` repetido en el mismo lote se rechaza. No se infiere cronología del
reloj del TV o del orden de los nombres.

Los UUID, nombres, rutas y otros datos de los informes permanecen en `privado/`,
excluido del repositorio público. No publicar ese catálogo sin preparar y revisar
un resumen saneado aparte. Los ZIP se conservan íntegros: no hace falta extraer
datos personales para compararlos.

## Pruebas locales

```text
python -B diagnostico/reconocedor-0.1/test_importar_informes.py
```

Las pruebas usan únicamente fixtures ficticios dentro de una carpeta temporal
privada del proyecto. Cubren captura parcial/fallida válida, importación de varias
identidades y perfiles, conservación de origen/destino, fallos de copia, CRC/SHA,
listado exacto, duplicados, rutas Windows, Unicode, symlinks, límites/overflow,
JSON malformado y conflicto de identidad. No usan TV, USB, red ni drivers reales.
