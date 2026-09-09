# RK3229-C: origen backup cambia entre lecturas

El recovery aceptó y ejecutó el extractor0.2/RK2 y guardó en la misma SD. La foto muestra `verify_source mmcblk0p10: 64 / 64 MiB`, diferencia SHA256 entre copia y relectura del origen, Status1 e Installation aborted. El usuario devolvió la SD y pidió resolverlo. Posteriormente indicó que la zona inestable debe intentarse al final con otra variante, conservando antes el resto del avance.

## Evidencia recuperada

La adquisición privada `privado/rk3229-c-rk2-p10-20260909/ADQUISICION.json` conserva nueve archivos de la SD, 72.719.981B: ZIP/guía, marcador, plan y cinco archivos de la captura. Cada archivo se copió, sincronizó en PC y comprobó con SHA de origen, destino y otra lectura del origen. Se archivó además la fotografía. No se modificó la SD durante la adquisición, no se contactó al TV y no se montaron las imágenes copiadas.

- `parameter`, mmcblk0p1, 4.194.304B: estado verified, parte y dos SHA de origen concordantes. SHA256 `7a368d759e1398a37fc0e30498ac4b71e29322ee02e47fc32938fabf1cf176c0`.
- `backup`, mmcblk0p10, 67.108.864B: archivo SD y copiaPC coinciden con el SHA de la primera lectura `602414e8216dbbaf96339f9c210c7e85792d0b36952e7adadf0ac32c0fad5bfd`. La segunda lectura del origen dio `54b878b2a76ee30d991a67ac24c39eb1072508e7e8711c7b3694af99fd6d3cf0`. Fuente failed, parte destination_verified. Es un archivo conservado, no un original estable verificado.
- Doce fuentes posteriores quedaron sin intentar. `cache` p11 estaba montada RW y se omitió antes de copiar. `backup` p10 no figura montada ni con holders en el inventario.
- Están presentes `failed-report.json`, `resultado-error.json` e `inventario.json`. No hay informe o resultado de éxito. [Comprobación PC por fuente](RK2-C-CAPTURA-PARCIAL-PC.json): únicamente 4MiB cuentan como origen verificado.

Las partes conservan la extensión `.partial` también cuando su fuente fue verificada. El estado del informe y sus SHA determinan el alcance. No se renombraron ni completaron los registros originales. Capturas, plan, CID y bloques permanecen privados; se publica este resumen.

## Mapa real y límites de interpretación

Recovery expone eMMC de7.818.182.656B y quince particiones. Android había expuesto catorce: en recovery aparece `parameter` p1 y cambian los índices (`system` p14, `userdata` p15). La corrección usa el mapa físico recuperado, no offsets inferidos de Android ni los de A/B. La SD quedó acreditada como destino separado, de tipoSD y geometría correspondiente; no se confunde su identidad con eMMC ni con el serial del lector Windows.

La diferencia de SHA demuestra que el flujo de bytes leído del origen cambió entre pasadas. No identifica por sí sola al proceso escritor, un fallo de eMMC/SD ni malware. `cache` y `backup` son particiones distintas. El código Rockchip de referencia contiene escrituras de backup en una rama de actualización de imagen, pero no se observó esa rama ejecutándose simultáneamente en el TV: [recovery.cpp](https://github.com/rockchip-android/bootable-recovery/blob/rk3399-box-7.1/recovery.cpp), [rkimage.cpp](https://github.com/rockchip-android/bootable-recovery/blob/rk3399-box-7.1/rkimage.cpp).

El orden alfabético anterior llevaba p1 → p10 y detenía el intento antes del resto. [0.3/RK3](EXTRACTOR-SD-03.md) ordena por posición y difiere backup; no lo elimina de la selección. Las áreas montadas RW siguen fuera por el contrato existente. No hay respaldo completo ni restauración Rockchip probada.
