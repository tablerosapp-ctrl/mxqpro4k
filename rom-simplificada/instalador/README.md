# Instalador experimental P291

**Vigente:** ROM0.1.1 preparada pero sin instalar. Acceso USB0.4 dejó sin señal; la evidencia física0.5 ya analizada favorece un atasco al cerrar el sistema antes del reinicio físico. La captura0.5 quedó incompleta por su cuota de APK y aceptó SHA binarios vacíos por una colisión de nombre en mksh. **Acceso USB0.6 completa los archivos faltantes sin reiniciar ni abrir el actualizador**; se construye en fuentes/salida separadas. Su nueva copia al USB está verificada y no hay prueba física0.6 acreditada. [Hallazgos del P291](../../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md) · [Pasos para el usuario](../INSTALACION-USB.md) · [Estado](../../docs/ESTADO.md) · [Mapa](../../docs/MAPA-ARCHIVOS.md).

## Cadena de ejecución

```mermaid
flowchart LR
 A[Complemento 0.6 en Android actual] --> B[Certificados OTA APK y configuracion en USB]
 B --> C[Analizar en PC sin otro reinicio]
 C -. acceso por resolver .-> D[Recovery visible e identificado]
 D --> E[Seleccionar ZIP y verificar firma]
 E --> F[Controles y respaldo de originales]
 F --> G[system vendor product odm boot]
 G --> H[Lectura de hashes y resultado]
```

`../componentes/acceso-usb-0.6/` contiene los fuentes nuevos. `Acceso.java` presenta «Guardar archivos que faltan (no reinicia)»; `Evidencia.java` controla perfil, carpeta, secuencia y finalización; `AdbLocal.java` usa exclusivamente127.0.0.1:5555; `generar-scripts.py` genera los cinco scripts fijos y `EvidenciaScripts.java`. INTERNET es necesario para el socket local, no para conectarse a una red externa. No habilita ADB ni pide root; tampoco cambia autenticación ni solicita reiniciar. Los fuentes0.5 permanecen en `../componentes/acceso-usb/`; no se reemplazan para documentar la corrección.

Se crea una carpeta única `TVBASE-evidencia-*` y no se reutiliza ni se busca otro destino durante la secuencia. Las cinco etapas son creación → autocontrol y certificados → APK específico → configuración/identidad → cierre. Se lee primero `/system/etc/security/otacerts.zip`, después `/product/app/OTAUpgrade/OTAUpgrade.apk`; se exige que `pm path com.droidlogic.otaupgrade` coincida con la ruta ya acreditada en el primer P291. No se recopilan nuevamente los APK de Google que agotaron la cuota0.5. Ambos binarios son obligatorios; si faltan, son ilegibles o exceden el límite, la captura se detiene y conserva el parcial. Las lecturas denegadas de configuración se registran como tales.

El cálculo de hashes usa nombres `tvbase_*` y `/system/bin/toybox sha256sum`. Cada consumidor valida64 caracteres hexadecimales antes de comparar o guardar; la etapa inicial exige el SHA conocido de `abc`. El cierre comprueba por nombre los informes, FIN, binarios obligatorios y hashes. Cada etapa ADB tiene un plazo máximo de90segundos. El contrato incluye tamaños, estabilidad del origen, lectura de copia y `sync`; su aceptación física requiere una captura nueva válida. Esta recopilación no instala la ROM ni respalda las particiones del TV.

**Lección0.5:** el alias `hash` de mksh eludió la función del mismo nombre; las tres salidas vacías compararon iguales. Los tests con Bash no reprodujeron esa conducta. La [auditoría y regresión con mksh R56 real](MKSH-HALLAZGO-0.5.md) documenta la causa y sus límites. Además, la base omitida de Google Play Services y tres APK divididos consumieron cuatro posiciones antes de OTAUpgrade. Se conservan los datos y tests originales0.5; los hashes de adquisición en PC y de seis textos por captura son pruebas separadas del falso positivo binario en el TV.

Las fuentes de0.4, incluidos `Diagnostico.java` y `EntradaAmlogic.java`, están archivadas en `../compilacion/acceso-usb-0.4-archivado/fuentes/`. No forman parte de0.5 ni0.6. Los informes0.4 precedían a `reboot:update`; la posterior captura0.5 sí conserva un aviso de reinicio seguido de517 segundos de actividad del kernel. Esto favorece atasco durante el cierre, sin identificar el dispositivo o callback responsable ni acreditar ejecución del recovery externo. [Resultado físico y límites](../../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md).

## Recovery externo

`preparar-recovery-externo.py` produce `recovery-externo/recovery.img` desde `../inspeccion/recovery-original.img` del candidato. Conserva kernel, contenido secundario DTB, DTBO, ejecutable del recovery y 102 entradas CPIO. Modifica exactamente `res/keys` y `prop.default`; recompone tamaño/offset/headerSHA1 de Android boot v1. Mantiene longitud de 24MiB.

La clave original del recovery candidato es distinta de la AOSP usada para nuestro ZIP. Se conserva y agrega la clave v3 RSA2048/e3/SHA256 del ZIP. No se desactiva verificación de firmas. Las propiedades identifican el recovery como TVBASE y el dispositivo ampere. [PREPARADO.json](recovery-externo/PREPARADO.json) acredita los hashes y comprobaciones. La prueba0.4 no mostró que el cargador ejecutara este archivo. Se conserva como artefacto preparado; no se modifica la partición recovery para resolver esa incertidumbre.

El kernel y DTB secundario coinciden con el boot candidato. Este boot heredado declara versión1 con campos de extensión cero; no se normalizó ni se interpretó esa particularidad como prueba de arranque. No confundirlo con la cabecera del recovery externo que sí se verificó al reconstruir.

## ZIP y particiones

`empaquetar.py` contiene el empaquetado y la firma completa; `manifest-0.1.1.json` enumera las cinco imágenes. `main_linux.go` es la ejecución en recovery, `package.go` valida paquete y hashes, `main_windows.go` permite validar payload en PC. El ID permitido de versión debe fijarse al compilar una revisión; el valor por defecto del código corresponde al artefacto histórico0.1. Ver [desarrollo](../../docs/DESARROLLO.md).

Antes de escribir, el ejecutable exige proceso recovery/UID0, DT `gxlx2_p291_1g`, esquema sin A/B/dynamic, aliases de particiones MMC del mismo dispositivo, tamaños suficientes, objetivos desmontados y cabecera vbmeta vacía cuando existe. Lee/verifica íntegramente los cinco payloads.

Busca un USB real mediante sysfs, FAT32/exFAT y marcador exacto. Si está solo lectura intenta remontar exclusivamente ese medio. Exige espacio libre para respaldar **las cinco particiones originales completas**, sincroniza y verifica cada archivo por lectura. Solo entonces instala system, vendor, product, odm y **boot al final**, sincronizando y leyendo los hashes de destino. Registra `respaldo.json` e `instalacion.log` dentro de `TVBASE-respaldo-*`.

No formatea userdata ni escribe bootloader, recovery, partición DTB, dtbo, vbmeta, keys, env o misc como parte de su receta. Boot sí contiene kernel/ramdisk/DTB secundario del candidato. Recovery/cargador pueden escribir sus registros/órdenes o estado habitual. Una interrupción no A/B puede dejar un sistema parcial; no existe rollback automático.

La revisión0.1.1 neutraliza los dos scripts `install-recovery.sh` y detiene `flash_recovery` en ambos eventos de tvbase.rc. 0.1 queda retirada: omitir recovery en la receta no bastaba para conservarla tras arrancar Android.

## Evidencia local y límites

- [RECOVERY-VERIFICACION-0.1.1.json](../salida/RECOVERY-VERIFICACION-0.1.1.json): ext4, 2426 archivos restantes idénticos, metadatos/SELinux y hashes de cinco imágenes, firma completa.
- [RECOVERY-COMPROBACION-0.1.1.json](../salida/RECOVERY-COMPROBACION-0.1.1.json): verificación independiente OpenJDK/Go y rechazo del paquete anterior.
- [ADB-TESTS-0.4.json](ADB-TESTS-0.4.json): 12 casos locales de protocolo; AUTH/checksum/canal desconocido siguen rechazándose.
- [ENTRADA-TESTS-0.4.txt](ENTRADA-TESTS-0.4.txt): siete casos de secuencia, incluidos fallos que impiden reiniciar.
- `EVIDENCIA-TESTS-0.6.json`: recibo de los casos y resultados efectivamente ejecutados por `test_evidencia06.py`, con `EvidenciaHarness06.java` y regresión pertinente bajo mksh real. No deducir cantidades ni éxito físico de esta lista.
- `compilar-evidencia06.py` → `../compilacion/acceso-usb-0.6/acceso-usb.apk` y `componente.json`: salida/firma propias de0.6; su copia USB tiene un recibo independiente ya verificado.
- [EVIDENCIA-TESTS-0.5.json](EVIDENCIA-TESTS-0.5.json): resultados históricos ADB/Bash/sintéticos; insuficientes para detectar el alias de mksh. La captura física ya ocurrió y fue parcial.
- [Componente0.5](../compilacion/acceso-usb-0.5/componente.json): APK histórica conservada con su firma y propósito de diagnóstico.
- [Recibo USB0.5](../../preparacion-usb/evidencia-05-estado.json): copia/lectura de aquella APK y guía, código0; no acredita completitud de captura ni comprobación binaria en el TV.
- [Recibo USB0.4](../../preparacion-usb/entrada-amlogic-estado.json): lectura SHA coincidente de aquella entrega. Para cualquier APK nueva corresponde un recibo nuevo.

Los tests de protocolo simulan respuestas; no ejecutan el shell del TV, su bootloader ni la instalación física. La regresión0.6 con mksh real cubre el mecanismo omitido en Bash0.5, pero no sustituye el toybox instalado, una copia física ni durabilidad eléctrica del USB. Compilación, pruebas PC, entrega USB y captura TV tienen evidencias separadas. Reproducción y salidas en [DESARROLLO](../../docs/DESARROLLO.md). Aún no existen respaldos originales del TV ni aceptación de firma/arranque/rendimiento demostrados. Las claves AOSP son públicas de prueba, no de producción. La firma de las APK propias utiliza una clave local que debe conservarse.

Fuentes y decisiones: [ADR-05 a ADR-10](../../docs/DECISIONES.md), [formato no A/B](https://source.android.com/docs/core/ota/nonab/inside_packages), [ADB Android9](https://android.googlesource.com/platform/system/core/+/refs/tags/android-9.0.0_r1/adb/services.cpp), [Amlogic P271 de referencia](https://android.googlesource.com/platform/external/u-boot/+/refs/heads/android-tv-s-beta3/board/amlogic/configs/gxl_p271_v1.h).

Entrega complementaria0.6: [recibo USB](../../preparacion-usb/evidencia-06-estado.json), 7/9/2026 a las00:22 ART, APK y guía copiadas/leídas con SHA coincidente. Primera ejecución0.6 en el P291 pendiente.

## Diagnóstico0.8 vigente

La entrada0.7 está retirada del USB tras atascarse el OEM al2%. [Uso vigente](../INSTALACION-USB.md):0.8 recoge evidencia dirigida, sin Update/reinicio/radios. Fuentes separadas en `../componentes/acceso-usb-0.8`, compilador `compilar-evidencia08.py`, pruebas `test_evidencia08.py` y `EVIDENCIA-TESTS-0.8.json`. [Contrato y límites](../../docs/hipotesis/REVISION-CONJUNTA-FABLE.md). No sobrescribir versiones verificadas ni confundir sus pruebas con una captura física.
