# Actualizador original del P291: análisis estático

7 de septiembre de 2026. Se analizó exclusivamente la copia real de `OTAUpgrade.apk` obtenida por Acceso USB0.6, sin ejecutar código en el TV ni modificar el USB. Esta carpeta es evidencia privada; no corresponde publicar el APK original.

## Identidad y método

- Origen: `../TVBASE-evidencia-690a4d7ced1f49f9916ac18cfe6106a2/OTAUpgrade.apk`.
- Tamaño: 190.988 bytes. SHA256: `9ffb822fc76974ee9df8c5493f0929638b69140f71506946cb410bab489a1d9c`.
- Es idéntico por SHA256 al APK anteriormente obtenido del segundo TV. Esto permite reutilizar conocimientos de ese código; no equipara firmware, certificados, particiones ni hardware de los dos TV.
- Manifiesto y recursos: `aapt2 dump xmltree` y `dump badging`. Código: extracción local de `classes.dex`, `dexdump -d -f` y separación de métodos. Las referencias numéricas siguientes son líneas de `dexdump.txt`; los archivos `*.asm.txt` conservan dichas referencias.
- No se ejecutó el APK, no se invocaron sus componentes y no se leyó el framework ni el recovery originales con este análisis.

## Resultado decisivo

En Android9/API28, el actualizador original **prepara un paquete interno y solicita escribir BCB antes del reinicio**. Es distinto de solicitar solamente `reboot:recovery` o `reboot:update`. Esto ofrece una vía concreta para intentar la instalación original, pero no demuestra que el cargador acepte BCB al encender en frío ni que el mapa de bloques haya quedado preparado después de un fallo.

El flujo normal del menú local es:

1. `Select` permite elegir un nombre terminado en `.zip`; no valida su contenido ni firma.
2. El primer `Update` crea `/cache/recovery/command` **antes** de mostrar la confirmación final. Cancelar esa confirmación solo cierra el diálogo; no borra la orden.
3. El `Update` de la confirmación inicia la copia y preparación. En API28 fuerza el modo3 y, para un ZIP del pendrive, intenta copiarlo a `/data/cache/update.zip`.
4. `installPackage` intenta primero el método privado `updateWithBCB`. Solo si devuelve false llama a `RecoverySystem.installPackage` como alternativa.
5. La vía privada escribe `/cache/recovery/uncrypt_file` con la ruta interna, elimina el viejo `/cache/recovery/block.map`, invoca por reflexión `setupBcb` con `--update_package=@/cache/recovery/block.map` y `--locale=...`, y llama a `PowerManager.reboot("recovery-update")`.

La APK no genera por sí misma el nuevo `block.map`: no llama a `processPackage` ni ejecuta `uncrypt`. Esa parte depende del framework y sus servicios. Un apagado y encendido solo podría continuar la instalación si los datos, el mapa y la orden persistente llegaron a quedar correctos y el cargador real los utiliza.

## Componentes y entradas

Paquete `com.droidlogic.otaupgrade`, versionCode2, versionName `2.0201411271418`, minSDK23/targetSDK23, compilado con API28. Declara `sharedUserId=android.uid.system`, biblioteca `droidlogic.software.core`, permisos RECOVERY, REBOOT y ACCESS_CACHE_FILESYSTEM, entre otros. No hay proveedores de contenido.

El manifiesto no escribe explícitamente `android:exported` ni permisos por componente. Los siguientes valores son la interpretación de los valores predeterminados de un manifiesto con target23 y sus filtros; no son una comprobación dinámica adicional de PackageManager.

| Componente | Filtros del manifiesto | Exportación predeterminada |
| --- | --- | --- |
| `.MainActivity` | MAIN + LAUNCHER/LEANBACK_LAUNCHER; SYSTEM_UPDATE_SETTINGS + DEFAULT, prioridad -1 | Sí |
| `.UpdateActivity` | CONNECTIVITY_CHANGE | Sí |
| `.LoaderReceiver` | BOOT_COMPLETED; `com.android.otaupdate.aml.backup`, `.restore`; CONNECTIVITY_CHANGE | Sí |
| `.UpdateService` | `com.android.update.action.check`, `.download`, `.autocheck` | Sí |
| `.FileSelector`, `.BackupActivity`, `.BadMovedSDcard`, `.ABCheckUpService` | Sin filtros | No |

`MainActivity.onCreate` construye la interfaz (16243) y `onResume` conecta botones y maneja únicamente avisos de resultado de backup/restore (16566). Abrir explícitamente `.MainActivity` no selecciona ZIP ni ejecuta Update por esos métodos. No se identificó un Intent público para pasar un ZIP local y preparar BCB sin reinicio. El extra `file` se consume solo como resultado interno de FileSelector en `onActivityResult` (16014).

En `UpdateService.onStartCommand` (22481), las acciones comprobadas `com.android.update.check` y `.download` difieren de los filtros que contienen `.action`; la tercera acción sí coincide. Son rutas de actualización en línea y no acreditan una entrada para instalación local ni preparación sin reinicio.

## Evidencias por función

| Función | Línea de dexdump | Observación |
| --- | --- | --- |
| `FileSelector$ZipFileFilter.accept` | 13808 | Directorios o sufijo `.zip` en minúsculas; no verificación de firma |
| `MainActivity.onActivityResult` | 16014 | Guarda ruta y muestra basename |
| `MainActivity.onClick` | 16069 | `createAmlScript` precede a `UpdateDialog` |
| `MainActivity.UpdateDialog` | 15829 | Construye confirmación y pasa ruta/modo a InstallPackage |
| `MainActivity$2.onClick` | 15681 | Cancel llama solo a `dismiss()` |
| `PrefUtils.createAmlScript` | 28378 | Crea command; añade package, locale y wipes opcionales; IOException capturada, sin lectura de comprobación |
| `PrefUtils.getAttribute` | 26961 | Mapea USB/SD a `/udisk/` o `/sdcard/`; fallback `/cache/` |
| `InstallPackage$1.onClick` | 14311 | Inicia preparación tras confirmación; no cancela la orden anterior |
| `InstallPackage$1$1.run` | 14216 | Llama a copia auxiliar y `OtaUpgradeUtils.upgrade` |
| `OtaUpgradeUtils.upgrade` | 2651 | API28 fuerza modo3; copia a ubicación interna y sigue al instalador |
| `UpdatePositionStage.getDefaultPostion` | 11024 | En API>=25 devuelve `/data/cache` |
| `OtaUpgradeUtils.installPackage` | 2526 | API>=26: BCB privado primero; RecoverySystem.installPackage si devuelve false |
| `OtaUpgradeUtils.updateWithBCB` | 2211 | uncrypt_file → borra block.map → setupBcb → recovery-update |
| `OtaUpgradeUtils.copyFile` | 1957 | Copia de 1024 bytes; comprobación débil y retorno true al terminar el bucle |
| `OtaUpgradeUtils.changeCommand` | 1888 | Sustituye líneas por prefijo y las concatena sin restaurar separadores intermedios |

## Límites y defectos relevantes del actualizador original

- **Firma:** en todo el DEX no hay llamada a `RecoverySystem.verifyPackage`, carga de claves OTA ni verificación de certificados del ZIP. La existencia de callbacks `onVerifyFailed` no implica su uso. El APK no abre `otacerts.zip`. La aceptación de la firma corresponde a otros componentes y debe verificarse por separado. La firma del APK, los certificados de Android y las claves de recovery son asuntos diferentes.
- **Copia:** `copyFile` compara los bytes copiados con `FileInputStream.available()` después de llegar a EOF. Normalmente difieren y llama a un callback con código3, pero devuelve true igualmente. El flujo API>=24 continúa hacia la instalación incluso si la copia devuelve false. Una barra de progreso no acredita integridad del archivo interno.
- **Orden previa a confirmación:** `createAmlScript` captura fallos de escritura y devuelve un modo igualmente; la aparición del diálogo no prueba que el archivo haya quedado escrito. No hace fsync ni lectura posterior.
- **Wipes:** `createAmlScript` admite wipe_data y wipe_media. El diálogo también puede recrear la orden con ambos true si la preferencia privada `update_with_script` vale true; su valor predeterminado es false, pero no se leyó el valor real. En API28 los checkboxes se ocultan en onCreate. La orden BCB de la vía privada solo contiene package y locale; no asumir que las opciones de borrado se transmiten de forma coherente por todas las rutas.
- **Ruta USB inicial:** `getAttribute` depende de FileListManager y compara algunos tipos con identidad de String. Usa solo el basename del ZIP; pierde subdirectorios. El flujo API28 posterior vuelve a escribir la ruta interna.
- **BCB:** si no encuentra ningún método cuyo nombre contenga `setupBcb`, el código puede llegar igualmente a pedir el reinicio. El simple comienzo del apagado no prueba éxito de esa escritura.
- **Orden de caché:** `changeCommand` concatena sin saltos las líneas conservadas. Antes del reinicio BCB intenta quitar la línea update_package; no confiar en que el archivo command restante conserve opciones interpretables.

## Decisión que habilita y comprobaciones pendientes

El menú explícito `com.droidlogic.otaupgrade/.MainActivity` es una entrada local concreta, del APK cuyo SHA se conoce. Puede abrirse sin disparar Update automáticamente; el usuario conserva la selección y confirmación del ZIP real. Se debe verificar primero el perfil P291/API28, el APK actual y el ZIP exacto del pendrive para no redirigir a otra aplicación o paquete.

Este análisis no habilita afirmar instalación, copia íntegra interna, escritura BCB real, recuperación funcional, compatibilidad de la nueva ROM o restauración. La captura0.6 es evidencia de lectura; no contiene una ejecución nueva del flujo de instalación. No se propone otro reinicio vacío ni otro recopilador general.
