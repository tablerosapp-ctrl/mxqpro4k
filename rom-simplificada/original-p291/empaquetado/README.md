# Paquetes del P291 original · 0.2.0 verificada en PC

Este componente trabaja **solo en PC**. Separa una ROM derivada de las imágenes originales del primer P291 y un paquete que restaura exactamente esas cinco particiones originales. Ninguna compilación, firma o prueba local acredita la entrada a recovery, la instalación o una restauración física.

Ambos ZIP fueron generados y pasaron sus comprobaciones. Los recibos de [instalación](salida/TVBASE-P291-A9-0.2.0-VERIFICACION.json) y [restauración](salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.0-VERIFICACION.json) registran tamaño, hashes, payloads, firma y límites. Las siguientes instrucciones documentan su construcción; no se debe repetir un comando sobre sus salidas existentes. No hubo copia USB ni operación sobre el TV.

## Entradas de la ROM

`empaquetar_original.py --operation install --revision-report RUTA` recibe un informe JSON revisado. Las rutas son relativas a la raíz del proyecto. Los archivos modificados deben estar dentro de `rom-simplificada/original-p291/`; un archivo sin cambios puede apuntar directamente a su adquisición privada verificada.

```json
{
  "version": "0.2.0",
  "package_id": "TVBASE-P291-A9-0.2.0",
  "dt_id": "gxlx2_p291_1g",
  "reviewed": true,
  "bluetooth_disabled": true,
  "images": {
    "system": {"path": "RUTA", "bytes": 1342177280, "sha256": "SHA256", "source_sha256": "SHA256_ORIGINAL", "fsck_exit": 0},
    "vendor": {"path": "RUTA", "bytes": 943718400, "sha256": "SHA256", "source_sha256": "SHA256_ORIGINAL", "fsck_exit": 0},
    "product": {"path": "RUTA", "bytes": 134217728, "sha256": "SHA256", "source_sha256": "SHA256_ORIGINAL", "fsck_exit": 0},
    "odm": {"path": "RUTA", "bytes": 134217728, "sha256": "SHA256", "source_sha256": "SHA256_ORIGINAL", "fsck_exit": 0},
    "boot": {"path": "RUTA", "bytes": 16777216, "sha256": "SHA256", "source_sha256": "SHA256_ORIGINAL"}
  },
  "boot_review": {
    "approved": true,
    "kernel_sha256": "9968c75f691f67dcb805ef8105e1ca534f73430bcf8b3920a066580e326b791a",
    "dtb_sha256": "13e54b5f1bba959e398da74b9d0859d08ba1747840ed3866eca1f3461c550d01",
    "ramdisk_sha256": "SHA256_DEL_RAMDISK_REVISADO"
  }
}
```

Es una plantilla, no un informe válido. El empaquetador exige hashes reales de 64 dígitos, tamaños exactos, fuentes originales verificadas y `fsck_exit` entero cero. Relee las imágenes y los manifiestos de las adquisiciones. Comprueba directamente la cabecera Android v1, su identificador, el kernel y el multi-DTB en el boot resultante; no confunde conservar el nombre de placa con conservar sus bytes. El ramdisk puede cambiar tras su revisión; no se exige que el boot completo permanezca idéntico.

Las capacidades originales son 1280 MiB system, 900 MiB vendor, 128 MiB product, 128 MiB odm y 16 MiB boot. El instalador exige también sus números major/minor observados y que pertenezcan al mismo eMMC. La geometría del candidato 0.1.2 no se utiliza.

## Compilar y verificar

```text
python -B test_firma_ota_v1.py
python -B empaquetar_original.py --operation install --build-only
python -B empaquetar_original.py --operation restore --build-only
```

Las compilaciones quedan en una carpeta nueva bajo `privado/original-p291-empaquetado/`. El ejecutable Windows solo valida paquetes. El ARM está separado y únicamente permite actuar desde recovery. Las salidas existentes provocan un error; nunca se sobrescriben releases anteriores. Los tests Go usan imágenes pequeñas y geometría reducida **solo en fixtures**; una prueba separada comprueba las constantes originales reales.

Con el informe aprobado, la operación `install` genera un nuevo ZIP. `restore` genera otro ZIP desde los originales adquiridos, sin usar imágenes modificadas. Ambos se verifican con SHA256 de cada payload, CRC, validador Go y firma integral Python/OpenJDK. Los originales, las claves y los releases 0.1.x permanecen intactos.

## Firma compatible con la política original

La única clave extraída de recovery tiene formato v1, RSA de 2048 bits y exponente 3. [AOSP 9 selecciona SHA-1 para este formato](https://android.googlesource.com/platform/bootable/recovery/+/android-9.0.0_r1/verifier.cpp). `firma_ota_v1.py` construye PKCS#7 sin atributos sobre los bytes reales que preceden al campo de longitud del comentario EOCD. No cambia solamente una etiqueta: calcula una nueva firma RSA/SHA1. Los hashes de contenido y los recibos siguen usando SHA256.

La clave pública se coteja con la captura de `res/keys` y con el certificado OTA existente. El verificador Python reproduce la política SHA1 y OpenJDK analiza/verifica PKCS#7 de forma independiente. Ninguno ejecuta el recovery OEM: **su aceptación física continúa pendiente**. Las claves públicas de prueba y SHA1 atienden compatibilidad heredada; no constituyen el sistema de confianza para una flota en producción. No se modifican las claves ni la partición recovery.

## Migración de userdata explícita

La ROM utiliza `fresh_userdata_required`. El instalador no acepta un simple marcador: comprueba el dispositivo `/dev/block/data`, su tamaño original, su identidad `179:20`, el mismo eMMC, un único montaje `/data` de solo lectura y el contenido real. Solo admite un directorio vacío o `lost+found` vacío. Datos, APK, configuración OEM o un supuesto archivo de autorización provocan un rechazo **antes de escribir las particiones del sistema**.

Por ello, preparar y respaldar lo que se quiera conservar de userdata es una operación separada, que aún necesita diseño/revisión y autorización concreta del contenido que se retirará. Este ZIP no formatea, borra, mueve ni migra userdata, no monta `/data` automáticamente y no restaura silenciosamente APK OEM desde ella. Tampoco contiene respaldo de videos o datos de aplicaciones. La configuración del actualizador OEM puede tener efectos propios que este paquete no controla.

El paquete de restauración lleva la política explícita `preserve_existing_userdata`: restaura system/vendor/product/odm/boot originales y conserva userdata tal como esté. Devuelve también el software y la configuración de las imágenes OEM, incluido el comportamiento original de boot. No es una ROM saneada, ni restaura datos que hubieran sido retirados antes por otra operación.

## Escritura y recuperación todavía pendientes

Dentro de recovery, el instalador verifica todos los payloads, rechaza destinos montados, exige un USB marcado, respalda las cinco particiones, sincroniza archivos/directorios y relee los hashes antes de escribir. Revalida geometría y montajes antes de cada escritura; boot queda al final. Para la primera instalación exige además que el boot actual coincida con el original adquirido. La restauración no impone ese hash al boot dañado que deba reemplazar.

El diseño no es A/B y no incluye rollback automático. El ZIP de restauración será útil únicamente si se demuestra una entrada a un recovery capaz de ejecutarlo. Antes de entregar una prueba física siguen pendientes una ruta completa y comprobada para el paquete en recovery y, para instalar la ROM, la operación explícita de preparación de userdata.
