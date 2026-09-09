# Extractor 0.3 · paquete RK3 para el ejemplar RK3229-C

Esta receta nueva compila el extractor ARM32 0.3 y conserva la firma v3/RSA-SHA256 que el recovery CNV8b aceptó en RK2. Solo trabaja en la PC. Las fuentes y entregas 0.1/RK1 y 0.2/RK2 permanecen intactas.

RK2 comenzó la copia en SD, pero rechazó `mmcblk0p10` porque la lectura original y la repetición de la lectura no coincidieron. Por pedido del usuario, 0.3 deja esa región `backup` para el final, conservando primero el resultado de las demás fuentes elegibles. Para `backup` aplica una variante acotada a sus 64 MiB: dos lecturas completas del origen comparadas en RAM antes de escribir la SD, seguidas de sincronización y relectura del destino. Una diferencia de SHA sigue siendo un error fatal. Las otras fuentes mantienen el orden de copia, relectura del destino y relectura del origen.

La variante requiere un presupuesto de memoria de 128 MiB. Si el kernel no informa `MemAvailable`, usa una estimación conservadora que descuenta `Shmem`, `Dirty` y `Writeback`, y exige al menos 512 MiB de memoria total. No usa lectura directa mediante `O_DIRECT` ni abre el origen para escritura. No convierte la copia fallida en un respaldo válido, no garantiza que la última partición sea estable y no atribuye una causa concreta al cambio observado.

La política nueva queda limitada al mapa completo de quince particiones observado en recovery y al ejemplar RK3229-C de esa captura. Se usan las particiones elegibles por separado para poder ordenar `backup` al final; no se elige la eMMC entera como una sola fuente. El número de partición visto desde Android no sustituye ese mapa. La identidad de su eMMC se obtiene de un inventario privado sellado y se incorpora al ejecutable mediante el enlazador; su valor no aparece en las fuentes públicas, los metadatos del ZIP ni el recibo público. El binario y sus registros de construcción se conservan en privado. No es un paquete para cualquier Rockchip ni autoriza pasar a otra unidad con la misma carcasa.

```text
python -B diagnostico/extractor-recovery-rk3/compilar.py --build-dir privado/extractor-rk3-build-NUEVO --output-dir privado/extractor-rk3-release-NUEVO --inventory privado/RUTA-A-INVENTARIO-SELLADO.json
```

Los dos directorios de salida deben ser nuevos, separados y estar bajo `privado`. La receta rechaza un inventario distinto del sellado; no permite elegir otro CID por argumento. Comprueba que ninguna fuente pública contiene ese valor y que el recibo y los metadatos tampoco lo divulgan. Los intentos fallidos se conservan.

La construcción ejecuta las pruebas de lógica en Windows y compila las pruebas Linux/ARM32 sin ejecutarlas. Revisa ELF ARM32/EABI5 estático, opciones Go, enlace de identidad, firma integral mediante Python y OpenJDK, CRC, nombres y permisos del ZIP, más casos negativos de firma. Reutiliza por ruta y SHA los auxiliares inmutables de RK1. No incorpora imágenes de particiones ni clave privada al ZIP.

La [construcción verificada](COMPILACION.json) produjo `TVBASE-EXTRACTOR-0.3-RK3-ARM32-RECOVERY.zip` de **1.463.158 bytes**, SHA256 `ff9595f7a64a64df77f1c1d4904a896922e62a6be51d6a9e94247e79da985d01`. El ejecutable tiene 3.621.965 bytes, SHA256 `b788619ef93b0d4df7ad7f55121df3aa019988f67954aab5bac20191c1188f50`. Pasaron 38 pruebas principales de Go, con 187 eventos de aprobación incluidos los subcasos, cuatro rechazos negativos en Python y dos en OpenJDK. Las pruebas Linux/ARM32 compilaron, pero no se ejecutaron allí ni en el TV.

El primer intento de construcción se conserva como fallido: la comprobación esperaba ver los parámetros del enlazador en la información de Go, pero `-trimpath` los omite en esta herramienta. La construcción final verifica el valor real de la variable mediante el símbolo ELF, su puntero y longitud, y el segmento cargable que contiene la cadena; conserva la tabla de símbolos y omite la información de depuración. El recibo enlaza el fallo y la receta anterior sellados, sin divulgar la identidad.

La aceptación del nuevo ejecutable, el fin de la extracción física y la utilidad para restaurar no se deducen de las pruebas en PC. La SD debe conservar el marcador y plan correspondientes al mismo equipo.

El extractor abre los bloques internos para lectura. No monta, desmonta, formatea, instala ni reinicia. El recovery anfitrión puede seguir escribiendo sus registros o metadatos. No hay instantánea atómica ni restauración implementada. La clave pública de desarrollo Rockchip se usa para compatibilidad de laboratorio, no como confianza de producción para futuras actualizaciones.
