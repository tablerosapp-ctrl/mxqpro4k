# Instalador experimental de Android por USB

**Estado corregido del 6/9:** la revision 0.1 omitio escribir recovery en el instalador, pero heredo dos scripts `install-recovery.sh` y el servicio `flash_recovery` que intentan sustituirlo al iniciar Android. No se ha observado una escritura efectiva por esos scripts. La revision 0.1.1 desactiva ambos scripts y detiene ese servicio. No usar 0.1 en nuevas instalaciones. El usuario aclaro con una foto que NO llego a instalar el ZIP: Acceso USB 0.2 fallo antes del reinicio con "Identificador ADB inesperado". Acceso USB 0.3 corrige el protocolo y pasa nueve pruebas locales. La instalacion fisica y el primer arranque siguen pendientes.

Paquete vigente: `TVBASE-P291-A9-0.1.1-RECOVERY.zip`, 573089164 bytes, SHA256 e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205. Comprobaciones en `../salida/RECOVERY-VERIFICACION-0.1.1.json` y `RECOVERY-COMPROBACION-0.1.1.json`: fsck 0, 2426 archivos restantes identicos, metadatos/SELinux de los cinco archivos modificados comprobados, firma Python/OpenJDK y validacion Go de todas las imagenes. El verificador 0.1.1 rechaza un paquete de la version anterior. Las otras cuatro imagenes de particion son identicas a 0.1.

APK vigente: Acceso USB 0.3, 24979 bytes, SHA256 6cba89eeae7cbd97a03360f1eba91ad689b513ab38981353839824cfa1f71877, misma firma de desarrollo que 0.2. Ya no responde a CLSE; ignora respuestas tardias solo de canales cerrados de esta conexion y acepta cierres heredados con identificador remoto cero. `ADB-TESTS-0.3.json` documenta las pruebas. No se conoce la pareja exacta de identificadores de la foto 0.2: el defecto esta corregido, pero no se afirma solucion fisica hasta probar 0.3.

Se construyo un ZIP de recovery real a partir de las particiones verificadas de TVBASE-P291-A9-0.1. No es el ZIP vacio usado antes ni el contenedor Amlogic renombrado.

## Componentes y acciones

- `TVBASE-P291-A9-0.1-RECOVERY.zip`: contiene imagenes RAW de system, vendor, product, odm y boot; las cuatro primeras son sistemas Android y la ultima contiene el kernel. Se instalan en ese orden, con boot al final.
- `update-binary`: ejecutable ARM32 estatico para el recovery, compilado localmente con Go. No requiere un shell, bibliotecas del Android instalado ni root obtenido por una APK. El recovery debe ejecutarlo como root tras aceptar la firma.
- `AccesoUSB.apk` version 0.2: se comunica exclusivamente con 127.0.0.1:5555. Comprueba `id`, API 28 y `gxlx2_p291_1g` antes de solicitar `reboot:recovery`. Ese servicio evita la ruta Java/PowerManager que quedo detenida al 2 %. No hace root, habilita ADB, modifica su autenticacion, descarga archivos ni inicia actualizaciones de Chrome separadas.

La APK requiere INTERNET porque Android exige ese permiso tambien para sockets locales. Su codigo no admite direcciones externas. Si recibe AUTH, informa que falta autenticacion y termina. Una respuesta OKAY de ADB acredita la apertura del servicio, no la ejecucion fisica del reinicio; el mensaje distingue solicitud enviada de resultado observado.

## Comprobaciones antes de escribir Android

El instalador exige el DT exacto `gxlx2_p291_1g`, un proceso recovery, UID 0, esquema sin A/B/dynamic partitions, destinos MMC particionados del mismo dispositivo, nombres y tamanos validos, particiones objetivo desmontadas y cabecera vbmeta vacia cuando existe. Comprueba los SHA-256 de las cinco imagenes completas antes de abrir cualquier destino para escritura.

Busca el pendrive por el marcador TVBASE-MEDIA.txt y una unidad USB identificada mediante sysfs, montada como FAT32/exFAT. Si el recovery la monto solo lectura, intenta remontar exclusivamente esa unidad para guardar el respaldo. Si no puede escribir o falta espacio, termina antes de modificar Android.

Guarda las cinco particiones originales completas, cada una con sincronizacion y verificacion de lectura, junto con respaldo.json. Solo entonces escribe las imagenes nuevas y comprueba por lectura cada SHA-256. Registra el progreso en el recovery y en instalacion.log dentro del respaldo. No formatea userdata ni toca bootloader, recovery, DTB, dtbo, vbmeta, claves, env o misc como parte de la receta. El propio recovery puede mantener sus registros/ordenes habituales.

La sustitucion no A/B no es atomica: un error de alimentacion o escritura durante la instalacion puede dejar un sistema parcial. El respaldo se conserva para recuperarlo desde el recovery retenido. No existe recuperacion automatica probada en este equipo.

## Evidencia y limites

`../salida/RECOVERY-VERIFICACION.json` registra las imagenes y la firma completa del ZIP. `FIRMA-OPENJDK-OK.txt` registra una segunda verificacion con PKCS7 de OpenJDK y el rechazo de una copia alterada. `ADB-TESTS.json` registra pruebas locales del protocolo con fragmentacion de paquetes, rechazo de AUTH, checksum incorrecto, cierre tras solicitud de reinicio y mensaje de error. No se envio un reinicio de prueba a otro TV.

La firma utiliza la clave **publica de prueba** de AOSP, descargada con su certificado del tag android-9.0.0_r1. Su certificado DER SHA256 es a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc, igual al certificado OTA extraido del segundo TV; aun no se comprobo el certificado del primer TV ni su aceptacion en recovery. No es una clave de produccion ni una forma de deshabilitar la verificacion.

La placa coincidente y los controles de instalacion no certifican toda la compatibilidad de drivers/kernel/DTB ni el primer arranque. Se conserva la particion DTB del equipo real. La imagen boot del candidato incluye kernel, ramdisk y su contenido secundario DTB; conservar la particion DTB no demuestra que el cargador vaya a utilizarla en lugar del contenido de boot. La imagen mantiene los limites y pendientes descritos en `../LEEME.md`, incluido probar WebView efectivo, composicion VP9 y posibles incompatibilidades con datos del Android anterior.

## Fuentes

- [Formato no A/B de recovery](https://source.android.com/docs/core/ota/nonab/inside_packages).
- [Servicio ADB de Android 9](https://android.googlesource.com/platform/system/core/+/refs/tags/android-9.0.0_r1/adb/services.cpp), que fija sys.powerctl para el reinicio sin pasar por ShutdownThread.
- [SignApk de AOSP 9](https://github.com/aosp-mirror/platform_build/blob/android-9.0.0_r1/tools/signapk/src/com/android/signapk/SignApk.java), firma PKCS7 directa y footer de comentario ZIP. Se conserva copia en tools/firmar-ota.
- [Claves de prueba AOSP](https://github.com/aosp-mirror/platform_build/tree/android-9.0.0_r1/target/product/security).
- [Descargas oficiales de Go](https://go.dev/dl/); catalogo, archivo y SHA256 en tools/instalador-go. Compilador usado go1.27.1 windows/amd64; destino GOOS=linux GOARCH=arm GOARM=7 CGO_ENABLED=0.
