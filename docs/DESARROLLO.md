# Desarrollo, reproducción y continuidad

## Dónde está cada verdad

| Información | Fuente principal |
| --- | --- |
| Pedido, alcance y aceptación | `ESPECIFICACION.md`; fundamentos en `../ARQUITECTURA-ANDROID-TV.md` |
| Resultado físico y próximo paso | `ESTADO.md` y evidencias fechadas de `../diagnostico/` |
| Qué se copió al USB | `../preparacion-usb/entrada-amlogic-estado.json` y carpeta del recibo |
| Qué contiene cada ROM | Manifiesto/VERIFICACION de `../rom-simplificada/salida/` |
| Conexiones entre requisitos, archivos y etapas | `proyecto.json`; mapa y HTML derivados |
| Motivo de una elección | `DECISIONES.md` |
| Trabajo pendiente y propuestas | `ROADMAP.md` |

Los JSON de prueba y recibos se conservan como evidencia de una ejecución. Cambiar el texto de una especificación no cambia su resultado. Evitar varios párrafos titulados «estado vigente» con fechas distintas en una misma guía operativa: trasladar la historia al registro correspondiente.

La prueba física de Acceso USB0.4 terminó sin señal y sin recovery visible. Los informes recuperados fueron creados antes del reinicio; no capturaron su fallo posterior. Confirman una partición recovery de24MiB, pero su lectura fue denegada. El siguiente componente es **Acceso USB0.5, recopilador sin reinicio**: su construcción y pruebas locales están separadas de la [copia USB0.5 ya verificada](../preparacion-usb/evidencia-05-estado.json); la captura física sigue pendiente. La ROM0.1.1 permanece sin instalar. [Evidencia del resultado](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md).

## Cadena de construcción local

La cadena existe como scripts y herramientas locales, **no como una construcción integral automatizada desde una carpeta vacía**. Algunos pasos fijan versiones/rutas y rechazan una salida existente. No ejecutar todos los scripts indiscriminadamente ni sobrescribir un entregable que el usuario esté probando.

| Paso | Entrada → implementación → salida |
| --- | --- |
| Analizar candidato | Archivo community y manifiesto → `analisis-rom/inspeccionar-rom.py`, `verificar-integridad-interna.py` → particiones/DTB/hashes |
| Inventariar y extraer | Candidato → `rom-simplificada/inspeccion/inventariar-ext4.py`, `preparar-copias.py` → inventarios y copias RAW |
| Inicio y overlay | Fuentes `componentes/`, SDK28, ECJ y herramientas Android → `compilar-componentes.py` → inicio/overlay |
| Evidencia0.5 | `componentes/acceso-usb/generar-scripts.py` → scripts fijos y `EvidenciaScripts.java`; Java/XML → `instalador/compilar-evidencia05.py` → `compilacion/acceso-usb-0.5/acceso-usb.apk`, firma y `componente.json` |
| Base0.1 | RAW originales + Chrome + inicio/overlay → `simplificar.py`, `verificar-y-empaquetar.py` → ext4/sparse/contenedor y pruebas |
| Revisión0.1.1 | system0.1 → `instalador/corregir-recovery-0.1.1.py` → system revisado, logs, `revision.json` |
| Ejecutable de recovery | Go ARM32 con ID de versión explícito → `instalador/main_linux.go`, `package.go` → `trabajo/revision-0.1.1/update-binary` |
| ZIP0.1.1 | Revisión + cinco particiones + ejecutable → `instalador/empaquetar.py --revision-report rom-simplificada/trabajo/revision-0.1.1/revision.json` → ZIP firmado y manifiesto |
| Recovery externo | Recovery original y clave pública del ZIP → `instalador/preparar-recovery-externo.py` → recovery.img y PREPARADO.json |
| Entrega USB0.5 vigente | APK0.5 + prueba/firma + identidad estable → `preparacion-usb/preparar-evidencia-05.ps1` → `evidencia-05-estado.json`, copia y lectura verificadas |
| Entrega USB0.4, histórica | Artefactos + pruebas + identidad del Kingston → `preparacion-usb/preparar-entrada-amlogic.ps1` → copia/lectura y recibo; no repetir la entrada fallida |

Las rutas de la tabla son relativas a la raíz del proyecto. Los scripts locales derivan ROOT desde su ubicación; no moverlos para embellecer el árbol. La limpieza retiró payload extraídos y ZIP sin firma que `empaquetar.py` regenera al construir una salida nueva. Los RAW activos, fuentes, herramientas y archivos finales siguen presentes.

### Versionado que importa

- Al compilar Go para una revisión, usar `-X main.allowedPackageID=TVBASE-P291-A9-0.1.1` en `-ldflags`; `GOOS=linux`, `GOARCH=arm`, `GOARM=7`, `CGO_ENABLED=0`. El valor histórico por defecto del fuente es0.1. El binario entregado0.1.1 ya está comprobado.
- El ejecutable Windows de validación necesita el mismo ID. La prueba de versión anterior rechazada está en `RECOVERY-COMPROBACION-0.1.1.json`.
- `empaquetar.py` sin `--revision-report` apunta a la versión histórica. No usarlo como atajo para producir un nuevo entregable.
- APK0.5, ROM0.1.1 y recovery externo0.1 tienen versiones independientes. Aumentar una no implica aumentar las otras. El recopilador0.5 no solicita update/recovery ni instala la ROM. Cada preparador debe usar el archivo y SHA de su versión concreta; un recibo0.4 no acredita una entrega0.5.
- Las fuentes, APK y resultados anteriores0.4 se conservan en `compilacion/acceso-usb-0.4-archivado/`. Su secuencia `EntradaAmlogic` es histórica y no se incluye en la compilación0.5. No compilar los harness0.4 contra los fuentes actuales.
- Conservar continuidad de firma de APK. `rom-simplificada/claves-desarrollo/` contiene material local sensible; no publicarlo ni imprimir sus contenidos. Las claves públicas de prueba AOSP se distinguen de esa clave privada local.

## Herramientas presentes

Python del runtime local, Java21 JRE + ECJ, SDK Android28, Android build-tools37, Go1.27.1, debugfs/e2fsck Cygwin. Las descargas/versiones están en `tools/` y los recibos respectivos. Python requiere `cryptography` para las verificaciones de firma. No hay un requisito actual de WSL, Docker o red del primer TV.

### Construcción y pruebas de Acceso USB0.5

`componentes/acceso-usb/generar-scripts.py` es la fuente de los siete pasos de shell. Genera `scripts/etapa-0.sh` a `etapa-6.sh` y su representación Java `EvidenciaScripts.java`; no editar por separado solo uno de los derivados. `Evidencia.java` valida placa, carpeta e identificador, controla la secuencia y exige el cierre de la última etapa. `AdbLocal.java` limita la conexión a127.0.0.1 y solo permite las consultas/etapas declaradas. `Acceso.java` expone el botón de captura y no abre el actualizador.

`instalador/compilar-evidencia05.py` regenera scripts, compila una salida0.5 independiente y exige que la clave de firma existente esté presente; no crea otra implícitamente. Verifica versión5/0.5, firma API28 y ausencia de rutas `reboot:recovery`, `reboot:update`, `EntradaAmlogic` y `startActivity` en el DEX. La existencia de `classes/` detiene otra construcción sobre esa salida: para una revisión usar una versión/directorio nuevos. No borrar esa protección ni ejecutar el antiguo `compilar-componentes.py --only acceso-usb` como atajo hacia0.5.

La compilación también crea las clases anfitrionas en `instalador/host-classes-0.5`, incluida `EvidenciaHarness.java`. Con esas clases presentes, la prueba local es:

```powershell
& 'C:/Users/usuario-local/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' 'rom-simplificada/instalador/test_evidencia05.py'
```

El resultado está en `instalador/EVIDENCIA-TESTS-0.5.json`: casos ADB, controles de perfil/secuencia/ruta/reintento, rechazo de host externo, sintaxis de scripts y escenarios de copia con archivos sintéticos. El recibo especifica los casos efectivamente ejecutados sobre la revisión correspondiente. El harness usa sockets en loopback de la PC; no conecta al TV. La sintaxis se verifica con el shell de MinGit. En las pruebas de copia, Python sustituye `stat` y `sha256sum`, y `sync` se simula como éxito/fallo: verifican flujo y bytes binarios, **no Android toybox ni persistencia eléctrica del USB**. Conservar los resultados y revisar diferencias antes de repetir una prueba que sobrescribe su JSON.

Para reproducir0.4, usar sus fuentes archivadas junto con `AdbHarness.java`, `EntradaHarness.java` y `test_adb.py`, conservando los recibos0.4 existentes. Sus doce casos ADB y siete controles siguen siendo evidencia de aquella versión; no convierten el apagado observado en un acceso válido a recovery.

Para una edición documental no hace falta recompilar la ROM ni repetir todas sus pruebas. Verificar referencias/grafo y que los hashes de los entregables no cambiaron es suficiente. Una edición real del instalador sí exige sus controles pertinentes y una versión explícita.

## Flujo de trabajo guiado por especificación

1. Localizar REQ y etapa M afectados. Si es una necesidad nueva, escribir primero el comportamiento y criterio de aceptación.
2. Registrar la decisión o propuesta que modifica el diseño; distinguir hecho de hipótesis.
3. Abrir el componente C y sus archivos desde el grafo. Implementar el cambio acotado.
4. Ejecutar la prueba VAL correspondiente; guardar resultado, versión, equipo y límites.
5. Actualizar `ESTADO.md`, roadmap y `proyecto.json`. Mantener como pendientes las comprobaciones físicas no realizadas.
6. Regenerar y comprobar el mapa desde la raíz:

```powershell
& 'C:/Users/usuario-local/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' 'docs/herramientas/generar-mapa.py'
& 'C:/Users/usuario-local/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' 'docs/herramientas/verificar-documentacion.py'
```

El generador solo lee archivos del proyecto y escribe documentación local; no accede al pendrive ni ejecuta scripts del firmware. `index.html` es autónomo y utiliza su JSON embebido; no necesita servidor, CDN o internet. El inventario JSON completo agrupa las claves sensibles sin enumerarlas; solo guarda rutas, tamaños y clasificación, nunca contenidos.

## Pendientes de ingeniería de construcción

Crear un comando integral reproducible con directorios de salida versionados, catálogo de herramientas y pruebas automatizadas de paquete/recuperación es una mejora propuesta. No está resuelto por este mapa. Ya se inició Git local en esta carpeta; [GIT](GIT.md) define exclusiones, autoría y publicación futura. Un clon no contiene herramientas, imágenes ni claves privadas. Los documentos históricos conservados son antecedentes, y los commits registrarán los cambios a partir de esta incorporación.
