# Limpieza del proyecto · 6/9/2026

Se eliminaron **6.615.135.611 bytes** (6,62 GB decimales / 6,16 GiB). [Plan con verificaciones](evidencia/limpieza-plan.json) · [Recibo de eliminación](evidencia/limpieza-resultado.json).

| Retirado | Motivo y conservación |
| --- | --- |
| Armbian `.img` expandida, 3,69 GB | Gzip conservado; se comprobó hash del comprimido y del contenido descomprimido contra la imagen antes de eliminarla |
| Dos ZIP intermedios sin firma, 1,15 GB | Contenido previo a la firma comparado byte a byte con los ZIP firmados conservados |
| product/odm/boot extraídos en `instalador/payload`, 281 MB | Coinciden con manifiesto; el empaquetador vuelve a extraerlos del candidato original |
| Imagen defectuosa del intento debugfs, 1,34 GB | No fue entregada; se conservaron causa, comandos, logs/fsck y su hash en el recibo |
| Caché Go y dos `__pycache__`, 159 MB | Regenerables; fuentes y binarios finales conservados |

No se eliminaron la fuente community, el gzip Armbian, las ROM firmadas, el contenedor original0.1, los RAW activos, el respaldo del pendrive anterior, claves, fotos, logs de fallos ni las pruebas. Se conservó ROM0.1 como referencia histórica y para comprobar rechazo de versiones; está retirada del flujo de instalación.

Los scripts de copia/formato viejos permanecen en sus rutas como antecedentes; los preparadores de instalación0.2/0.3 tienen error explícito de retirada. El script actual es `preparar-entrada-amlogic.ps1`. Los binarios de herramientas se conservaron: retirar sus archivos a ciegas habría roto dependencias locales.

## Orden documental

`AGENTS.md` ahora contiene continuidad vigente y enlaces. Su crónica anterior íntegra se guardó en `historico/AGENTS-hasta-20260906-2004.md`. Las guías anteriores de instalación/recovery se guardaron antes de reemplazarlas por instrucciones0.4. Sus enlaces originales se interpretan desde su ubicación antigua, indicada en `historico/README.md`.

La limpieza se hizo solo dentro de la ruta absoluta comprobada del proyecto, rechazando enlaces y cambios de contenido posteriores al inventario. Dos precontroles detectaron una normalización incorrecta de rutas/tipo del ancestro y abortaron antes de borrar; se corrigió el control. La ejecución final terminó correctamente. No se modificó el pendrive durante esta limpieza.

Los scripts `planificar-limpieza.py` y `aplicar-limpieza.ps1` conservan la operación concreta para auditoría; no son una recomendación de ejecutarlos otra vez. El aplicador rechaza una segunda ejecución cuando ya existe recibo.
