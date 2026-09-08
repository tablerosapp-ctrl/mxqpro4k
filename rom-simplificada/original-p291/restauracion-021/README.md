# Restauración original P291 0.2.1

Variante separada, exclusiva para restaurar las cinco imágenes originales adquiridas del primer P291. Corrige la consulta de tamaño BLKGETSIZE64 para ARM32; la prueba física de solo lectura confirmó que la orden anterior devuelve EINVAL22 y la nueva devuelve los tamaños exactos de env y data. Los archivos0.2.0 permanecen intactos como antecedentes.

Se conserva userdata existente. Este paquete no incluye formateador, no monta ni abre la partición de datos y no recupera automáticamente el respaldo de userdata de la instalación0.2.1. Reintroduce el Android y software OEM contenidos en los originales. No es una variante depurada ni rollback automático.

Antes de escribir exige recovery, P291/DT y geometría exactos, cinco destinos desmontados y un USB físico con el marcador previsto. El manifiesto admite exclusivamente restauración y los cinco hashes originales fijados en el código; otro payload es rechazado aunque su descripción sea coherente.

El ZIP se abre directamente desde el USB. Se respaldan las cinco particiones actuales en una carpeta nueva, comparando SHA durante copia, relectura del USB y relectura del origen desmontado. Se sincronizan archivos, directorios y recibo; una comprobación final de las copias precede a la restauración. Se necesitan al menos3.107.979.264bytes libres. Se escribe boot al final, con fsync y lectura completa por partición; errores de archivo/log/cierre se propagan. No hay sync global ni reinicio automático.

Si existe una restauración anterior marcada como iniciada sin cierre verificado, se detiene para conservarla. Una interrupción puede dejar una mezcla de imágenes; conservar respaldo y recovery y revisar el registro antes de otra acción. La presencia del ZIP no acredita que el recovery sea accesible ni que una restauración funcione físicamente.

## Fuentes y reproducción

El empaquetador y verificador provienen de0.2.0, en este directorio nuevo. Las guardas de USB, persistencia, copias verificadas y flasheo incorporan las correcciones de instalacion-021. Se excluyen sus herramientas y funciones de formato de userdata. El formateo no es una operación admitida por este ejecutable.

```text
python empaquetar_original.py --operation restore --build-only
python empaquetar_original.py --operation restore
```

Utiliza las herramientas y claves ya presentes enPC. Compilación y salida usan nombres nuevos y fallan si existen. Las cinco imágenes, sus respaldos originales y los releases previos no se modifican. La firma integral mantiene la compatibilidad experimental con la clave v1 del recovery real; no es una firma de producción.

Estado: ZIP sellado, 913.294.443 bytes, SHA256 `42580206f254fab0a2280cd263a48882677e7ddf5cfd609382a840c8d0fb103a`. Superó 45 eventos de prueba Go, compilación ARM32, firma integral Python/OpenJDK, CRC, hashes de cinco imágenes y validador Windows. [Recibo final](salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-VERIFICACION.json) · [Revisión independiente](REVISION-INDEPENDIENTE.json). No ejecutado en el TV.
