# Extractor 0.2: copia a la SD preparada para RK3229-C

Derivado separado de [0.1](../extractor-recovery-0.1/README.md). La foto del nuevo intento muestra verificación del paquete RK1 con resultado 0, ejecución de nuestro binario y parada en la búsqueda del USB marcado: encontró cero destinos válidos. Eso acredita que el ejecutable empezó, pero no distingue USB ausente, sin montar o rechazado por alguna condición de 0.1. No se llegó al inventario ni a la copia de bloques.

Esta variante usa la **misma SD que contiene `/mnt/external_sd/update.zip`**. No selecciona otro USB como alternativa ni modifica montajes. El usuario continúa eligiendo el último RK3229-C; compartir carcasa o DT con A/B no hace transferible el plan ni acredita una identidad física.

## Contrato de destino

- Un único montaje raíz `/mnt/external_sd`, vfat y RW tanto en el montaje como en su superblock. Un montaje RO se informa expresamente y se detiene; no se remonta.
- Partición directa `mmcblkNp1` de una tarjeta física MMC cuyo `device/type` sea **SD**, nunca MMC/eMMC. Sysfs, `st_dev`, major:minor e ioctl de lectura deben coincidir. La ruta no puede ser virtual ni USB.
- Geometría exacta de la tarjeta preparada: disco 8.053.063.680 B, partición 8.052.015.104 B desde el sector 2048 (1 MiB). No hay offsets de eMMC fijos ni escritura de bloques en SD.
- `removable` debe ser 0 o 1 y queda registrado; no se usa como prueba de que sea SD. El CID real de SD se lee al ejecutar y se fija mediante hash para las revalidaciones; no se deduce del número del lector de Windows.
- Marcador de esquema `tvbase-recovery-media-1`, `media_id=tvbase-recovery-sd-rk3229-c-20260909`, en `TVBASE-EXTRACCION/MEDIA.json`. El plan APK conserva esquema 1 y sus bytes; `PLANES` y `CAPTURAS` deben estar preparadas previamente.
- El ZIP debe ser archivo regular de esa misma tarjeta en la ruta fija; se conserva su `st_dev`, inode y tamaño. Cada revalidación comprueba montaje, topología, CID, geometría, marcador y paquete.
- Antes de crear la carpeta de captura y durante las revalidaciones se excluye coincidencia o relación de ascendencia entre la SD y **todas** las fuentes eMMC, incluso las que después no se seleccionen.

Los directorios y archivos de salida se siguen fijando con descriptores y `openat/mkdirat`, sin seguir enlaces ni sobrescribir. Los archivos se sincronizan y releen; un error real de sincronización detiene el proceso. No se escribe sobre la memoria interna, no se instala ROM, no hay montaje, formato, borrado, reinicio, recuperación automática ni red. El recovery anfitrión puede escribir sus propios registros/metadatos.

## Capacidad y duración

El motor `capture.go` y la selección de fuentes conservan los bytes de 0.1: partes de hasta 1 GiB, buffer de 256 KiB, reserva de **128 MiB**, SHA durante copia, relectura del destino y segunda lectura del origen. No se reduce la comprobación para hacer caber una tarjeta.

La eMMC declarada por C es de 7.818.182.656 B; sumando la reserva necesita 7.952.400.384 B, antes de cualquier área boot adicional. Frente a los 8.033.837.056 B libres informados al iniciar esta revisión, deja 81.436.672 B adicionales. La cabida final depende de los orígenes reales y del espacio que consulte el programa después de escribir su inventario. Las áreas boot expuestas se suman; si falta espacio se conserva un fallo y **no se empieza la copia de bloques**. No se promete una copia completa del aparato: RPMB, áreas en uso y memorias no soportadas permanecen omitidas.

Las tres lecturas pueden tardar. El progreso muestra fases `copy`, `verify_destination` y `verify_source` con MiB reales. Una llamada al kernel bloqueada no tiene plazo universal; no se fuerza reinicio. No se guarda otra captura de C ni se pasa a A/B hasta importar/verificar y archivar la SD en PC.

## Informes y comprobación

`inventario.json` mantiene el esquema 1 y añade `destination`, con la prueba de identidad/topología/montaje de SD. El informe del motor mantiene `tvbase-recovery-capture-0.1` porque no cambió su contrato de copia. Los `.img.partial` conservan esa extensión incluso al concluir: el manifiesto y el resultado determinan el estado; `failed-report.json` o `resultado-error.json` prevalecen.

El nuevo [verificador PC](verificar-captura.py) admite inventarios 0.1 anteriores y verifica también `destination` cuando está presente. Nunca abre los dispositivos o rutas sysfs registrados, ni interpreta userdata. No editar el verificador antiguo para aceptar el nuevo campo. Las pruebas de [lector](PRUEBAS-LECTOR-PC.json) emplean archivos ordinarios simulados, no una SD ni un TV.

## Fuentes y límites de pruebas

- `capture.go` y `capture_test.go`: motor 0.1 conservado, sin cambios de bytes.
- `selection.go` y `selection_test.go`: reglas 0.1 conservadas.
- `sd_policy.go` / `sd_policy_test.go`: política de destino, separación y cabida, ejecutables en Windows con fixtures.
- `sd_linux.go`: lectura de evidencia SD y revalidación; solo se ejecuta físicamente dentro del recovery.
- `main_linux.go`: integra SD, retira búsqueda USB, conserva plan e inventario; `platform_linux.go` conserva el confinamiento de salida ajustando su tipo a `sdTarget`.
- [Empaquetado RK2](../extractor-recovery-rk2/README.md): receta separada de compilación y firma; no forma parte de la preparación de medios.

Una revisión estática independiente no encontró bloqueantes en estas guardas ni en su integración. Las pruebas Windows verifican motor, política y lector; compilar pruebas Linux no equivale a ejecutarlas. La lectura de sysfs/ioctl y el montaje SD RW en el recovery real siguen pendientes hasta el próximo intento. No hay restauración ensayada ni certificación antimalware.
