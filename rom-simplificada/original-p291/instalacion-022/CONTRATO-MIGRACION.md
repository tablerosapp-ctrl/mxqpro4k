# Contrato de instalación0.2.2

La plataforma sigue siendo0.2.0. Solo cambian el instalador, su identificación y la guarda de layout descrita en [README](README.md). Las imágenes system/vendor/product/odm/boot son bytes inmutables del release0.2.0; el empaquetador comprueba cada una contra su revisión original. El [contrato0.2.1](../instalacion-021/CONTRATO-MIGRACION.md) conserva la fundamentación de la receta y sus pruebas previas; sus estados de entrega son históricos.

Antes de respaldar, el instalador verifica recovery, UID0, DT del primerP291, cinco destinos originales, boot original, ausencia de A/B/mappings y USB físico marcado. La guarda nueva acepta nombres Amlogic únicamente con dispositivo/padre/atributos/tamaños consistentes. ENV exige CRC y flujo de arranque normal. No se acepta el bootcmd transitorio pendiente.

Userdata debe ser directamente legible como ext4, en179:20,3.495.952.384bytes. Se desmonta normalmente si recovery la montó en/data; no se fuerza el desmontaje ni se aceptan otros montajes/holders. Los cinco destinos también deben estar desmontados. Los starts observados se congelan al validar, se registran en el recibo y se revalidan antes de las operaciones siguientes. No se presentan como offsets adquiridos originalmente.

Los seis respaldos suman6.067.060.736bytes y requieren6.603.931.648bytes libres enUSB. Cada archivo cabe FAT32. Cada copia debe superar SHA de copia, fsync y cierre, relecturaSHA delUSB y SHA posterior del origen desmontado. Los cinco originales tienen además sus SHA fijados. Solo un archivo verificado se renombra desde `.parcial`; archivo/directorios y recibo se sincronizan y releen. Nada permite saltar el respaldo completo.

Después de `00-backup-verified.json`, se releen los seis respaldos y la estabilidad del origen de datos. Solo entonces se invoca el formateador original fijado porSHA con los argumentos probados sobre un archivo regular. Crea ext4 en3.495.936.000bytes (853500bloques4KiB), limpia/relee los últimos16KiB de footer y exige el superblock previsto. Verifica/data montadaRO/noload con contenido vacío o lost+found vacío, y la desmonta.

Se escriben system, vendor, product, odm y boot al final. Cada destino/layout/montaje y elUSB se comprueban nuevamente; cada escritura requiere fsync y SHA de relectura. `90-installed-verified.json` solo se emite al terminar todas. No hay reinicio automático. Se detectan transacciones incompletas0.2.1 y0.2.2; no se repite un formato automáticamente.

La preparación borra aplicaciones, cuentas, ajustes y archivos internos actuales después del respaldo; no reintroduce datosOEM enAndroid limpio. El [restaurador0.2.2](../restauracion-022/README.md) repone cinco imágenesOEM y conserva userdata, pero no restaura su copia cruda. Restaurar datos exige otra operación atada al respaldo real. No hay rollback ni rescate físico garantizado; un fallo tras empezar a escribir requiere conservar recovery y los respaldos.

La ROM nueva elimina su/ADB TCP predeterminado y el gestor no tiene REBOOT/RECOVERY. La próxima entrada desde Android simplificado y una actualización completa posterior siguen pendientes de prueba. El nuevoZIP y el backup/formato/arranque necesitan evidencia física propia; la revisión de la guarda no la sustituye.
