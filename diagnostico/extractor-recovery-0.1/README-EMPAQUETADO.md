# Empaquetado del extractor 0.1

`compilar.py` prepara dos ZIP de extracción separados, con el mismo código Go y distintas arquitecturas. El flujo combina una captura previa de la APK de reconocimiento, su validación en PC y un plan de extracción por identidad DT exacta. Sin un plan coincidente, recovery guarda solamente inventario; la copia de imágenes se habilita con el plan correspondiente. El empaquetador trabaja solamente en la PC. No contacta TV, no prepara pendrive ni entra en recovery.

| Paquete | Ejecutable | Entorno |
| --- | --- | --- |
| `TVBASE-EXTRACTOR-0.1-ARM32-RECOVERY.zip` | Linux ELF32 ARM, EABI5, `GOARM=5` con coma flotante por software | Recovery que pueda ejecutar ARM32 y confíe en la firma |
| `TVBASE-EXTRACTOR-0.1-ARM64-RECOVERY.zip` | Linux ELF64 AArch64, `GOARM64=v8.0` | Recovery de ARM64 que confíe en la firma |

Ambos se construyen con `CGO_ENABLED=0`, sin intérprete ELF ni segmento dinámico. El procesador físico puede soportar 64 bits mientras recovery es de 32 bits. No se deduce la variante correcta de la carcasa, del nombre MXQ ni solamente de la arquitectura de Android. La receta no instala un despachador ni prueba automáticamente ambos ZIP en un TV.

Cada ZIP contiene exclusivamente cuatro entradas:

- `META-INF/com/google/android/update-binary`: extractor Go; recibe versión API de recovery, descriptor de estado y ruta del ZIP.
- `tvbase/extractor.json`: versión, arquitectura, operación de lectura, SHA del ejecutable y fuentes.
- `META-INF/com/google/android/updater-script`: mensaje informativo para identificar el propósito del paquete.
- `META-INF/com/android/otacert`: certificado público de la firma.

No contiene imágenes Android, instrucciones de flasheo ni datos de otro equipo. La configuración del medio es un archivo externo `TVBASE-EXTRACCION/MEDIA.json`, con esquema `tvbase-recovery-media-1`. Los planes JSON, de esquema `tvbase-recovery-plan-1`, quedan en `TVBASE-EXTRACCION/PLANES` y proceden de capturas Android validadas en PC. El extractor exige que la identidad DT del recovery coincida exactamente con la del plan para copiar imágenes; una inferencia P291/P271 o un nombre comercial no sustituyen esta coincidencia. El empaquetador no genera el plan ni escribe esos archivos en el USB.

## Construcción nueva

Ejecutar con el Python existente que tenga `cryptography` disponible, desde la raíz del proyecto. Debe hacerse después de revisar y finalizar las fuentes:

```text
python diagnostico/extractor-recovery-0.1/compilar.py --build-dir diagnostico/extractor-recovery-0.1/privado/build-nuevo --output-dir diagnostico/extractor-recovery-0.1/privado/release-nueva
```

Las dos rutas deben ser nuevas, distintas, no anidadas entre sí y estar dentro del proyecto. Si existe cualquiera, se rechaza la operación. Una falla conserva los registros y resultados incompletos; no se reutiliza ni borra el intento. No distribuir archivos de una salida sin `COMPILACION.json` con estado `built_verified_pc`.

La receta usa Go, OpenJDK y ECJ ya presentes en `tools`. Desactiva la descarga de módulos y el cambio automático de toolchain. Ejecuta todas las pruebas del paquete Go en Windows antes de compilar ARM32 y ARM64; también compila, sin ejecutarlas, las pruebas para ambas variantes Linux. Comprueba clase ELF, arquitectura, EABI en ARM32, ausencia de `PT_INTERP`/`PT_DYNAMIC` y parámetros grabados por Go. Compilar correctamente no comprueba las llamadas del kernel ni los accesos de un recovery físico.

El Go local 1.27.1 admite `GOARM=5` y su configuración por defecto para ese valor usa software floating point; esto se comprobó en `tools/instalador-go/go/src/internal/buildcfg/cfg.go`. Se elige Linux como destino porque el ejecutable es estático y opera dentro de recovery. La [documentación oficial de requisitos de Go](https://go.dev/wiki/MinimumRequirements) indica Linux 3.2 o posterior para Go 1.24 y posteriores, además de `CONFIG_FUTEX` y `CONFIG_EPOLL` para kernels reducidos. Son mínimos del runtime; el kernel y la configuración del recovery de cada placa deben revisarse al calificarla. Este resultado no declara un recovery universal.

## Firma y verificación

Se reutilizan, sin editarlos, `firma_ota_v1.py` y `VerifyWholeZip.java` de `rom-simplificada/original-p291/instalacion-022`. Sus SHA256 están fijados en el nuevo script. El primero valida los bytes de `/res/keys` adquiridos del recovery original P291 y que corresponden al certificado y clave existentes. No se muestra ni copia la clave privada a las salidas.

La firma integral es PKCS7 RSA-PKCS1v1.5/SHA1, conforme al formato v1 observado en ese recovery. Después de firmar se verifica con el lector Python y, por separado, con el parser y verificador PKCS7 de OpenJDK. Además se releen las cuatro entradas, sus longitudes, metadatos, permisos del ejecutable y CRC. La clave de prueba y SHA1 responden a compatibilidad heredada; no constituyen la seguridad de actualizaciones del producto final.

`COMPILACION.json` registra SHA256 de fuentes, herramientas y dos ZIP, SHA de cada ejecutable y miembro ZIP, arquitectura ELF, pruebas realizadas, firmas verificadas, logs y límites físicos. `RESULTADO.json` en el directorio privado enlaza y sella ese recibo. Un error posterior a crear las carpetas conserva `FALLO.json` en el intento privado.

La confianza comprobada corresponde a la clave del recovery original P291. Un certificado coincidente en `otacerts.zip` de Android P271 no prueba que su recovery acepte estos ZIP. No se ha comprobado aceptación ni ejecución del nuevo extractor en P291, P271 o Rockchip por compilar o verificar las firmas en PC. El empaquetador tampoco resuelve la entrada a recovery, permite restaurar datos ni demuestra que una captura cubra toda la eMMC.
