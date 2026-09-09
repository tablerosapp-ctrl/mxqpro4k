# Bases conocidas y siguiente extracción

## Actualización de evidencia de C

RecoveryC confirmó eMMC7818182656B y quinceparticiones; Android había mostrado catorce. `parameter` p1 quedó verificada; `backup` p10 cambió entre lecturas. `system` y `userdata` son p14/p15 en recovery. [Evidencia](evidencia/ERROR-RK2-BACKUP-C.md). No trasladar índices/offsets entre entornos ni variantes. RK3 se vinculó solo a esta unidad para intentar el resto y backup alfinal; no hay aún ROMRockchip ni respaldo completo.

Actualizado el 8 de septiembre de 2026. Esta matriz reúne las configuraciones observadas; no autoriza intercambiar ROM entre ellas. A/B/C son etiquetas locales de inventario. El nombre comercial MXQ Pro 4K 5G se repite en placas distintas.

| Base | Android observado | Memoria interna expuesta | Radio observada | Originales / estado |
| --- | --- | ---: | --- | --- |
| P291, DT `gxlx2_p291_1g` | API 28 / Android 9 | 7.650.410.496 B | `wlan_mt7663_sdio`; WiFi funciona según usuario tras TV Base | Originales y respaldo de conversión verificados. TV Base instalada; Home y calificación multimedia pendientes. |
| P271, DT `gxlx_p271_1g` | API 28 / Android 9 | 7.820.083.200 B | `8822bs`, SDIO `024c:b822` | Inventario y archivos accesibles adquiridos. No imágenes de particiones; plan de lectura preparado. |
| RK3229-A, TVBOX | API 25; fingerprint Android 7.1.2 | 7.818.182.656 B, eMMC `QNW00M` | `ssv6158` | Inventario adquirido; sin imágenes. |
| RK3229-B, TV BOX-3 | API 25; fingerprint Android 7.1.2 | 7.818.182.656 B, eMMC `008GB0` | `ssv6x5x` | Inventario adquirido; RAM declarada de 512 GiB anómala, física indeterminada. Sin imágenes. |
| RK3229-C, MBOX / `CNV8b.20230725` | API 25; fingerprint Android 7.1.2 | 7.818.182.656 B, eMMC `Q7XSAB` | `ssv6x5x` | Inventario recibido por copia manual. El usuario confirma que puede abrir recovery. Primera extracción seleccionada. |

Fuentes: [P291 instalado](evidencia/INSTALACION-FISICA-P291-022.md), [P271](../diagnostico/reconocimiento-20260908-p271-mx9/HALLAZGOS.md), [RK3229-A/B](../diagnostico/reconocimiento-20260908-rk3229-usb/HALLAZGOS.md), [RK3229-C](../diagnostico/reconocimiento-20260908-rk3229-manual/HALLAZGOS.md). Los nombres eMMC y módulos son declaraciones del sistema; no sustituyen identificación física ni pruebas de red.

## Un solo plan RK activo para la primera copia

Los tres RK anuncian el mismo DT `rockchip,rk3229`, pero sus radios, firmware y particiones difieren. El [extractor0.1](../diagnostico/extractor-recovery-0.1/README.md) selecciona por DT y rechaza dos planes coincidentes. Se selecciona en PC únicamente el plan derivado del inventario C, y se indica al usuario el último aparato capturado. El plan P271 tiene otro DT y puede permanecer.

Esta selección manual permite la primera copia de lectura sin cambiar el ejecutable sellado. **No demuestra identidad física:** usar otro RK con ese mismo DT asociaría su captura al informe C. Por eso se obtiene primero C y se devuelve el USB a la PC para verificar su nuevo inventario y asociarlo correctamente antes de preparar A o B. No recorrer todos los RK con este mismo plan.

El mapa de bloques se obtiene nuevamente en recovery. El informe Android no decide rutas ni offsets de lectura. El extractor comprueba tamaños, montajes y estabilidad, divide las imágenes en partes aptas para FAT32 y no desmonta, formatea, instala ni reinicia. Áreas ocupadas o no admitidas quedan omitidas explícitamente. El recovery anfitrión puede guardar sus propios registros o metadatos.

La aceptación del ZIP y la primera captura física C siguen pendientes. Un error de firma se conserva como resultado; no se renombra a `update.zip`, cambia la verificación o prueba un instalador de ROM por rutina.

## Consecuencia para la capa común y el navegador

Las etiquetas Android 11.1/13.0 de los Rockchip no reflejan la API observada. No podemos llevar automáticamente Chrome138 del P291 a esos Android7: Chromium fija Chrome119 como última rama para Nougat/API25 y sube el mínimo a API26 desde120. [Aviso del equipo Chromium](https://groups.google.com/a/chromium.org/g/chromium-dev/c/B9AYI3WAvRo/m/tpWwhw4KBQAJ). Android8/9, a su vez, deja de recibir Chrome desde139. [Notas oficiales de Chrome](https://support.google.com/chrome/a/answer/10314655?hl=en).

Por tanto, una base RK que conserve API25 tendría un techo de motor distinto. Un motor instalado tampoco acredita que sea el proveedor WebView usado por la APK. No se eligió ni descargó un navegador RK en esta revisión. Para superar ese techo habrá que evaluar una base Android posterior compatible con sus componentes de video/red; esa compatibilidad aún no está demostrada.

La capa común puede compartir inicio, configuración, almacenamiento de contenidos y administración, pero cada base deberá declarar su API, proveedor WebView y capacidades comprobadas. Los binarios de GPU/video/radio no se consideran intercambiables por compartir SoC. No se aprobará una variante por la lista de códecs: deberá ejecutar la APK, VP9 con transparencia y canvas, control remoto, red y almacenamiento. [Objetivos y aceptación](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md).

## Trabajo después de recibir las imágenes C

1. Verificar el resultado, cada parte y sus hashes; preservar originales privados y registrar omisiones. No montar userdata ni publicarla en claro.
2. Analizar boot, recovery, sistema y componentes multimedia/radio adquiridos; localizar configuración real de arranque, confianza y servicios. No clasificar malware solo por nombre.
3. Definir la receta de esa base con [revisión de componentes heredados](REVISION-COMPONENTES-HEREDADOS.md), proveedor WebView y límites de actualización. Obtener A/B/P271 por separado, sin trasladar imágenes ni datos privados entre unidades.

La instalación rápida del lote y las actualizaciones remotas dependen de estas bases calificadas. Esta entrega prepara extracción, no una nueva ROM.
