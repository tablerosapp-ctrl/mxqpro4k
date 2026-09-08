# Incidencias de construcción y correcciones

Las incidencias ocurrieron sobre copias de imágenes en la PC. No hubo operaciones sobre el TV ni el Kingston. Los respaldos originales y las copias de los intentos fallidos se conservan en los directorios privados; no se reusaron como releases.

## 1 · Atributo largo sin valor visible

El primer intento se detuvo al inspeccionar los atributos del ejecutable allocator de system. `debugfs 1.44.5` mostraba `security.selinux (41)` sin representar el valor. El parser suponía que toda línea incluía `= valor`; la integridad de los archivos no había fallado, sino la interpretación de la salida.

La corrección admite el formato de nombre/tamaño sin valor mostrado y utiliza `ea_get -f` para recuperar los bytes exactos. Compara tamaño y SHA256 del valor binario, sin depender de escapes o truncamiento de pantalla. La prueba reprodujo una etiqueta real de 41 bytes, once alteraciones de metadatos/contenido y seis respuestas malformadas. [Evidencia EA41](empaquetado/EVIDENCIA-PLAN-EA41.json). Las etiquetas de directorios nuevos también se verifican.

## 2 · Bloques de atributos huérfanos al quitar APK de product

En el segundo intento system y vendor superaron sus controles; product falló en ext4: los bloques 2008–2015 seguían marcados como ocupados sin propietario. El original product pasa fsck y tiene inodos de 128 bytes, con sus etiquetas SELinux en bloques externos. Los ocho bloques correspondían exactamente a los ocho inodos de cuatro APK retiradas y sus directorios. La herramienta de eliminación dejó sus bits de asignación; no era un error del original ni del pendrive.

Se probaron alternativas sobre copias nuevas: retirar primero los atributos no liberó esos bloques; liberar solo los bits dejó incorrectos los contadores. La corrección final usa operaciones nativas para liberar exclusivamente ese rango, ajustar sus dos contadores y recalcular el checksum del descriptor. [product_ea.py](product_ea.py) exige SHA original, geometría, plan de ocho retiradas, propietarios anteriores, ausencia de propietarios vivos y el diagnóstico exacto de fsck antes de modificar. Rechaza cualquier otro fallo.

La verificación posterior limita el cambio al bitmap, contadores/checksum y tiempo de escritura normal de debugfs, con todos los otros bytes idénticos; exige fsck cero y compara los catorce nodos restantes con sus atributos. Ocho pruebas negativas comprueban el rechazo antes de escribir en casos de fuente, tamaño, propietario, contadores o plan distintos. [Evidencia product](empaquetado/EVIDENCIA-PRODUCT-EA.json). No se implementó una reparación general del sistema de archivos.

## Regla para continuar

El control adicional de bloques libres encontró una diferencia de 58 bloques en vendor: su grupo 5 tiene el bitmap sin inicializar y reserva superblock, tabla de descriptores y 56 bloques de expansión. Leer ese bitmap crudo como si estuviera inicializado contaba metadatos como libres. Se corrigió el lector, sin modificar la imagen, reconstruyendo las reservas desde la geometría y comparando cada contador de grupo. La prueba sintética reproduce la diferencia y rechaza un byte no cero en un bloque realmente libre.

La [verificación final de composición](COMPOSICION-VERIFICADA.json) terminó con 39 APK exactas y 353.890 bloques realmente libres en cero entre las cuatro particiones ext4. Ese control no examina el sobrante interno de bloques asignados ni certifica seguridad del código conservado.

La receta final usa un directorio nuevo de construcción y vuelve a verificar todas las particiones. Tener un archivo de imagen, una firma o un proceso debugfs terminado no basta para aceptar el resultado. El recibo [IMAGENES-0.2.0.json](IMAGENES-0.2.0.json), cuando se completa, identifica cada salida; [verificar-composicion.py](verificar-composicion.py) comprueba luego el inventario real de APK y todos los bloques libres del resultado.

Los efectos de una instalación física, WiFi, WebView, tráfico y restauración quedan fuera de estas pruebas de PC.
