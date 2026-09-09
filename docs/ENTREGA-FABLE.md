# Continuidad para Fable 5.1 · prueba RK3

Este es el punto de entrada vigente para continuar desde Claude Desktop en otra PC. El usuario pidió documentar todo antes del relevo y continuará con Fable después de esta prueba. **El resultado físico de RK3 todavía no fue comunicado a esta sesión.** No inferir éxito, error ni estado actual del TV a partir de la entrega de la SD.

La última entrega publicada antes de este relevo corresponde al commit público `57eb693a967fb9a9c1155ad7a48fa7856d1f2ddd` (Git operativo local `9a682b383377955db927fa4a686a7f5c07e1bf4b`). Esta guía se publica después. Al comenzar, registrar el HEAD público realmente recibido y leer cualquier evidencia posterior; no quedarse fijado a ese commit si ya llegaron resultados nuevos.

## Lectura inicial y objetivo

1. Esta guía y [ESTADO](ESTADO.md): qué ocurrió y qué sigue pendiente.
2. [Fallo físico RK2](evidencia/ERROR-RK2-BACKUP-C.md) y [entrega RK3](evidencia/EXTRACTOR-SD-03.md).
3. [Contrato del extractor0.3](../diagnostico/extractor-recovery-0.3/README.md), [revisión independiente](../diagnostico/extractor-recovery-rk3/REVISION.md) y sus recibos.
4. [Matriz de perfiles](MATRIZ-PERFILES.md), [especificación](ESPECIFICACION.md), [grafo](index.html), [mapa de archivos](MAPA-ARCHIVOS.md) y [roadmap](ROADMAP.md).

El producto final es Android simplificado instalado en memoria interna, conservando los drivers adecuados de cada placa, especialmente video. Debe ejecutar APK Flutter y contenido web en WebView, reproducir y almacenar video local, eliminar contenido y recibir actualizaciones propias de APK/navegador y, después de validar su mecanismo, del sistema. Sin Play Store ni cuentas o servicios OEM innecesarios. El usuario toleraría Linux solo si resuelve también la ejecución de APK; esa alternativa no está implementada ni sustituye por decisión tácita la base Android.

La carga multimedia real incluye dos videos de aproximadamente1280 superpuestos, uno con transparencia, y canvas; VP9 es prioritario. La respuesta anterior «un video hasta1080p sinDRM» fue ampliada por esa prueba posterior. No deducir mejor rendimiento solo por quitar aplicaciones o subir la versión del navegador.

El diseño contempla una capa común de producto y bases por hardware: reconocimiento y copia profunda para nuevos equipos/lotes, instalación rápida para unidades calificadas y catálogo firmado compartido por USB e Internet. [Plan de producto](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md), [lotes y actualizaciones](PROPUESTA-LOTES-Y-ACTUALIZACIONES.md). Esas propuestas no son funciones ya operativas.

## Estado por equipo

| Equipo | Evidencia alcanzada | Pendiente |
| --- | --- | --- |
| P291, gxlx2_p291_1g | TV Base instalado mediante0.2.2 sobre plataforma0.2.0; cinco escrituras y seis respaldos verificados. Usuario confirma WiFi y varios reinicios sin USB. | Home no vuelve al menú. Proveedor WebView efectivo de la APK, VP9/alfa/canvas, recursos/tráfico, recuperación y actualizaciones remotas por validar. |
| P271, gxlx_p271_1g | Reconocimiento Android e inventario adquiridos; archivos accesibles conservados. | Copia profunda/entrada y ROM propias. No es intercambiable con P291. |
| RK3229-A y B | Capturas APK e inventarios importados. Mismo DT comercial, diferencias de firmware, radio y memoria; RAM anómala en B. | Copias profundas y calificación independiente. |
| RK3229-C, último Rockchip, CNV8b.20230725 | Reconocimiento recibido mediante copia manual; recovery accesible; RK2 ejecutó y dejó captura parcial en SD. | Nueva prueba RK3 y adquisición de sus resultados. No existe ROM Rockchip construida. |

Las carcasas MXQPro4K5G/MX9 no identifican una base compatible. Las etiquetas Android11/13 de algunos RK contradicen API25/fingerprint7.1.2: usar la evidencia técnica de la matriz. P291 integra Chrome/WebView138, pero el proveedor usado por la APK aún debe medirse; no trasladarlo directamente a los RK API25.

## Qué pasó en Rockchip C

- RK1 fue aceptado y ejecutado por recovery, pero no encontró un pendrive montado que cumpliera las guardas. Abortó antes de capturar bloques. El aviso de metadata no impidió ejecutar el extractor.
- Se preparó SD0.2/RK2 para cargar el ZIP y guardar las copias en la misma SD. No requiere Kingston como destino.
- RK2 copió y verificó `parameter`, p1, 4MiB. Después falló al releer `backup`, p10, 64MiB: el SHA de la primera lectura y del archivo SD coincidió; el de la segunda lectura del origen fue distinto. Doce fuentes posteriores quedaron sin intentar por el orden alfabético p1→p10. Cache p11 estaba montada RW y se omitió por la guarda normal.
- Se adquirieron y verificaron en PC nueve archivos de la SD, 72.719.981B, más la foto archivada aparte. La captura tiene dos imágenes, inventario y dos registros de fallo; no hay cierre de éxito. [Verificación parcial PC](evidencia/RK2-C-CAPTURA-PARCIAL-PC.json) acredita únicamente4MiB como origen verificado.
- El usuario rechazó excluir directamente la zona cambiante. Pidió intentar el resto antes y dejar esa zona para el final con otra variante. Esto rige [ADR-37](DECISIONES.md) y la entrega RK3.

La diferencia de SHA no prueba malware, un escritor concreto ni una avería de eMMC/SD. `backup` no aparece montada ni con holders en el inventario. No confundirla con cache. El mapa de recovery tiene quince particiones: parameterp1, backupp10, systemp14, userdatap15. Android había mostrado catorce; no reutilizar sus índices ni offsets.

## Qué cambió en RK3 y qué está en la SD

**Paquete:** `TVBASE-EXTRACTOR-0.3-RK3-ARM32-RECOVERY.zip`, 1.463.158B, SHA256 `ff9595f7a64a64df77f1c1d4904a896922e62a6be51d6a9e94247e79da985d01`. En SD se llama `update.zip`. [Construcción](../diagnostico/extractor-recovery-rk3/COMPILACION.json), [revisión](../diagnostico/extractor-recovery-rk3/REVISION.json), [entrega](../preparacion-usb/sd-rk3229-c-03-estado.json), [relectura independiente](evidencia/SD-03-LECTURA-FINAL.json).

- Fuentes elegibles ordenadas físicamente; backup se intenta última. No se clona todaeMMC porque impediría separar su orden. Guardas RW/holders permanecen y no se desmonta para forzar lecturas.
- Orígenes ordinarios: copia/SHA → sincronización y relectura SD → segunda lectura de origen. El cuerpo `captureOne` conserva la lógica de0.2.
- Backup64MiB: verifica memoria, lee a RAM, relee el origen y compara ambos SHA antes de escribir datos de backup en SD. Solo si coinciden guarda RAM, sincroniza y relee SD, exigiendo el mismo SHA. Presupuesto mínimo128MiB; si Linux3.10 no tiene MemAvailable, usa una estimación conservadora documentada. No se garantiza que no pueda agotarse la memoria.
- Acceso normal con caché de kernel, sinO_DIRECT ni snapshot atómico. La hipótesis es reducir el intervalo y evitar alternar escrituraSD con lecturaeMMC; su efectividad física sigue pendiente.
- Exige DT, CID de esta eMMC y mapa recoveryC completo. El CID real se vincula en el binario privado; fuente pública sin esa vinculación rechaza la operación. **No es un ZIP genérico para A/B, P271 ni otro ejemplar.**
- Si backup falla, los archivos de fuentes anteriores y sus estados verified permanecen. Si falla una fuente anterior, el motor se detiene y backup no se intenta. No hay modo general de ignorar errores.

SD8053063680B, FAT32TVBASESD, partición8052015104B desde1MiB. Quedaron7962386432B libres. Con cacheRW se seleccionan14fuentes/7679770624B, incluido backup; exige7813988352B con reserva128MiB. La capacidad se recalcula en recovery; no se elimina una fuente para hacerla caber.

Se sustituyeron únicamente ZIP y guía, tras archivar/verificar los anteriores. Los otros siete archivos —marcador, planC y cinco de la captura— permanecen iguales. Copia, flush de archivos y relectura SD comprobados; expulsiónWindows y flush del volumen no observados. No se formateó, reparó ni escribió en crudo; Kingston se conservó. El preparador03 ya terminó: **no repetirlo** ni reconstruir releases selladas por rutina.

## Pruebas y errores de desarrollo conservados

- Go:38 pruebas principales/187 eventos pass; incluye backup simulado64MiB cambiante, dos lecturas antes de crear archivoSD y conservación de una fuente previa. PruebasLinux compiladas paraARM32, no ejecutadas en recovery.
- LectoresPC:38 métodos,37pasados/1omitido porque esa cuenta Windows no podía crear symlinks reales. Comprobaciones de reparse/hardlinks y demás casos sí ejecutadas. [Recibo](../diagnostico/extractor-recovery-0.3/PRUEBAS-LECTOR-PC.json).
- Firma integral v3/RSA-SHA256 verificada con Python/OpenJDK y un parserDER/RSA independiente; cinco alteraciones rechazadas. CID enlazado comprobado desde símboloELF, puntero/longitud y segmentosPT_LOAD. Replay del inventario real confirmó selección de14fuentes y backupúltima; CID distinto y geometría modificada rechazados.
- Primer buildRK3 abortó en una guardaPC que buscaba ldflags en buildinfo pese a `-trimpath`. No fue un intento enTV/SD. Se conservó el fallo y se corrigió la comprobación leyendo el valor real enlazado del ELF. Build02 es la entrega sellada.
- Git inicialmente normalizó dos recibos. Se añadieron reglas de conservación y se reaplicaron al índice; el siguiente commit preserva bytes exactos. Los archivos originales y la SD no cambiaron. El commit público de entrega incluye esa corrección.

Estos ensayos no acreditan aceptación física deRK3, captura completa, ausencia de malware ni restauración delTV.

## Cómo continuar después de la prueba del usuario

Primero registrar el mensaje final que vio, si volvió al menú y si hubo interrupciones. La selección indicada fue **mismoC → recovery → Apply update from SD card → update.zip**, soloSD, sinwipe ni instaladoresP291. No repetir la prueba automáticamente. Si todavía está copiando/verificando, mantener alimentación y SD; la pantalla muestra etapas de extracción, no instalación deROM.

Cuando la SD regrese a una PC:

1. Identificar el medio por identidad/capacidad/partición y contenido, nunca solo por letra. Antes de limpiarlo, copiar a una carpeta privada nueva todos sus archivos, incluida la captura anterior y cada carpeta nueva de CAPTURAS. Mantener el árbol y los registros originales.
2. Registrar un manifiesto de adquisición con rutas relativas, tamaños, SHA de origen antes de copiar, SHA de copiaPC y otra lectura del origen; sincronizar los archivos. No montar las imágenes ni ejecutar su contenido. Toda diferencia conserva un estado incompleto. La adquisición PC es una evidencia separada de lo que afirmó el extractor.
3. Elegir cada captura por sus propios registros e identidad; el reloj delTV no es fiable. No mezclar partes de intentos distintos. `.img.partial` no significa por sí mismo fallo: también se conserva esa extensión en fuentes verificadas.
4. Si tiene `resultado.json` y `report.json` de cierre favorable, usar el lector completo. Si tiene ambos registros de fallo, usar el lector parcial. Trabajar sobre la copiaPC y conservar salida/código de la herramienta.

Desde la raíz del clon, con Python3.11+ y sustituyendo `CAPTURA_LOCAL` por la carpeta copiada:

```text
python diagnostico/extractor-recovery-0.3/verificar-captura.py --capture CAPTURA_LOCAL
python diagnostico/extractor-recovery-0.3/verificar-parcial.py --capture CAPTURA_LOCAL
```

Se elige uno según los registros, no se ejecuta el segundo para convertir un rechazo del primero en éxito. `selected_sources_verified_pc` acredita la selección verificada con sus omisiones; no todaeMMC. `failed_capture_files_verified_pc` significa que se comprobaron archivos de una captura fallida: contar solamente `verified_source_bytes` y conservar el estado global incompleto. Backup con hashes distintos nunca es un original estable.

Si faltan registros, existen marcadores contradictorios o el lector rechaza los archivos, conservarlos para revisión específica. El lector parcial es estricto y no cubre todas las interrupciones posibles; no alterar el JSON ni inventar un cierre para que pase. Si falta evidencia de verificación de una parte, registrar pendiente.

| Resultado nuevo | Acción útil siguiente |
| --- | --- |
| Selección completa verificada | Comparar con inventarioC/plan, documentar fuentes y omisiones; preparar inspección de drivers/firmware de esas copias. Restauración continúa sin probar. |
| Solo backup falla al final | Conservar y verificar el resto; registrar ambos SHA/etapa. Analizar qué cambió sin desechar fuentes buenas ni debilitar la comprobación. |
| Falla antes de backup | Identificar primera fuente/etapa y alcance real; no atribuirlo automáticamente a p10. |
| Error de memoria en backup | Las fuentes anteriores pueden estar verificadas; documentar el presupuesto observado antes de proponer otra variante. |
| Perfil/SD/espacio rechazado | Revisar inventario y guardas concretas; no quitar la validación de identidad ni elegir otro disco por letra. |

Después de esta adquisición, decidir con el usuario si se trabaja sobre C o se prepara otra unidad. A/B requieren una política propia y sus evidencias. No dar por completada la capa común ni instalarROM como consecuencia automática de tener un respaldo.

## Archivos disponibles y privados

| Material | Ubicación/alcance |
| --- | --- |
| Fuentes y contratos del extractor | `diagnostico/extractor-recovery-0.3/`: Go, lectoresPython, tests y README. |
| Receta y recibosRK3 | `diagnostico/extractor-recovery-rk3/`: compilar.py, COMPILACION, REVISION y README. |
| Evidencia de la SD | `docs/evidencia/EXTRACTOR-SD-03.md`, `SD-03-LECTURA-FINAL.json`, `preparacion-usb/sd-rk3229-c-03-estado.json`. |
| CapturaRK2 y foto originales | EnPCoperadora: `privado/rk3229-c-rk2-p10-20260909/`, con ADQUISICION.json y árbolSD. Son privados. |
| ZIP/binaryRK3 | `privado/extractor-rk3-release-20260909-02/` y `privado/extractor-rk3-build-20260909-02/`; el ZIP exacto también está enSD como update.zip. |
| Intento de build descartado | `privado/extractor-rk3-build-20260909-01/`; no usarlo como release. |
| RespaldoP291 publicado | [Release cifrada](https://github.com/tablerosapp-ctrl/mxqpro4k/releases/tag/respaldo-p291-20260908), [alcance y recuperación de archivos](RESPALDO-GITHUB.md). Clave separada, nunca pública; restauraciónTV no probada. |
| CapturaRockchip enGitHub | Solo resumen saneado/hashes, no bloques niuserdata. La ReleaseP291 no incluye Rockchip. |

Documentar todo no significa publicar claves, CID, userdata, ROM o registros privados en claro. GitHub contiene fuentes, decisiones, evidencia saneada y el historial; algunos enlaces a insumos privados estarán ausentes en el clon. Las herramientas y claves no vienen con Git. Los preparadores públicos tienen identidades anonimizadas y no deben ejecutarse sobre medios reales sin restituir una configuración privada comprobada. No cambiar guardas para hacer funcionar el clon.

## Trabajo de producto que sigue abierto

Home del P291; logo e inicio; proveedorWebView usado por la APK; videoVP9/transparencia/canvas y almacenamientooffline; consumo y tráfico; revisión de servicios de teléfono/contactos/mensajes, KeyChain e IntentFilterVerification y dependencias; actualización remota firmada y mecanismo de recuperación; reconocimiento porfamilia e instalación rápida porlote. [Incidencias](INCIDENCIAS.md), [componentes heredados](REVISION-COMPONENTES-HEREDADOS.md), [roadmap](ROADMAP.md).

No clasificar un paquete como malware solo por el nombre. P291 conserva framework/firmaOEM y SELinuxpermisivo: no es AOSP limpio ni tiene certificado antimalware. El gestor propio está incluido y desactivado; el usuario tiene servidor pero no proporcionó URL para configurarlo. No inventar endpoint ni afirmar que actualizaROM/remotamente ya.

## Coordinación e historial

La prueba y preparación de extracción fueron autorizadas. Este relevo documental no ordena otra operación física ni cancela autorizaciones previas; cualquier instrucción nueva del usuario debe incorporarse explícitamente. Fable trabaja desde otra cuenta/PC: registrar commit, archivos revisados, resultado observado, hipótesis, cambio propuesto y criterio de detención. Puede devolver documento o PR/fork; no necesita las credenciales de esta cuenta.

No reescribir recibos ni releases para documentar un resultado posterior. Hacer la siguiente corrección como versión nueva si cambia código sellado. No repetir UpdateOEM al2%, entradaENV/BCBP291, instaladoresP291 o formatosSD por leer instrucciones históricas.

La [entrega anterior para Fable](https://github.com/tablerosapp-ctrl/mxqpro4k/blob/57eb693a967fb9a9c1155ad7a48fa7856d1f2ddd/docs/ENTREGA-FABLE.md) conserva la crónica previa. La [colaboración histórica H1/H2](https://github.com/tablerosapp-ctrl/mxqpro4k/blob/57eb693a967fb9a9c1155ad7a48fa7856d1f2ddd/docs/COLABORACION.md) corresponde al bloqueo delP291 antes de su instalación; no es el trabajo activo deRK3. Todo sigue disponible enGit y en los documentos de evidencia enlazados.
