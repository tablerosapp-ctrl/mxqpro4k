# Restauración después de una instalación0.2.1

Se preparó por separado `TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-RECOVERY.zip`, con la consulta de geometría corregida para ARM32. [Recibo sellado](../restauracion-021/salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-VERIFICACION.json). La versión0.2.0 queda histórica y no se ofrece como restaurador operativo. El contrato restaura exclusivamente system/vendor/product/odm/boot originales y conserva userdata tal como se encuentre. Puede devolver el Android OEM con datos limpios, pero no devuelve automáticamente los archivos anteriores. Devuelve también las configuraciones y herramientas privilegiadas originales del OEM.

El instalador0.2.1 guarda previamente seis imágenes crudas en una carpeta nueva `TVBASE-respaldo-021-*`. Su `00-backup-verified.json` identifica el equipo, tamaño y tres SHA por archivo. `data.img` contiene el volumen completo, incluido su antiguo footer. Este respaldo es privado y no se sube a GitHub.

Un paquete de restauración de seis particiones se puede preparar **cuando exista ese respaldo físico**. Su receta deberá fijar el SHA exacto del recibo y de `data.img`, verificar la copia nuevamente en PC y firmar un manifiesto separado. No se inventa ahora ese hash, no se escoge automáticamente cualquier carpeta parecida y no se interpreta la presencia de un nombre como prueba de respaldo.

El contrato para ese paquete separado será:

1. Exigir P291, USB marcado y el recibo y seis imágenes exactos; comprobar tamaños, hashes e identidad real de las particiones. Verificar toda la fuente antes de escribir y mantener todos los destinos desmontados.
2. Restaurar system/vendor/product/odm originales, luego la imagen cruda completa de data y finalmente boot original. No arrancar Android entre escrituras. Data debe restaurarse y releerse con SHA correcto **antes** de habilitar el boot original como último paso.
3. Sincronizar y releer cada destino. Conservar siempre las fuentes del pendrive. Registrar el resultado como restaurado únicamente tras las seis verificaciones; un fallo detiene la operación y mantiene recovery sin reinicio automático.

El paquete de seis aún no está generado porque todavía no existe un recibo físico de userdata de esta instalación. La nueva variante de cinco ya tiene recibo de compilación, firma y verificación. Ninguna de estas descripciones acredita que se haya ensayado físicamente la restauración o que siempre pueda accederse al recovery.

La ROM nueva elimina el `su` heredado, no habilita ADB TCP y su gestor no tiene permiso REBOOT/RECOVERY. El acceso por APK que se utiliza sobre el Android OEM no constituye una ruta acreditada de vuelta desde Android nuevo. La siguiente actualización completa necesitará demostrar la entrada disponible desde ese estado; no se promete instalar otra ROM como si fuera una actualización ordinaria de APK.
