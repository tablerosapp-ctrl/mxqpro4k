# Verificacion criptografica de APK

El script `verificar-apks.ps1` ejecuta el `apksigner` oficial de Android Build Tools 37.0.0 con Java Temurin 21 portatil. No instala, modifica ni vuelve a firmar APK. Las herramientas estan dentro de `tools/verificacion-apk`; no requieren Java del sistema ni cambios de PATH.

Desde la raiz del proyecto:

```powershell
& '.\actualizacion-chrome\verificacion\verificar-apks.ps1' -ApkPath '.\actualizacion-chrome\chrome-70-original.apk'
```

Para verificar todos los APK extraidos de un bundle, pasar una lista de rutas:

```powershell
$apks = @(Get-ChildItem -LiteralPath '.\actualizacion-chrome\splits' -Filter '*.apk' -File | Select-Object -ExpandProperty FullName)
& '.\actualizacion-chrome\verificacion\verificar-apks.ps1' -ApkPath $apks
```

Cada ejecucion crea una carpeta de informes separada. Se comprueba la firma con `verify --verbose --print-certs` y otra vez especificamente para Android 9/API 28. Se conservan las salidas completas, los codigos nativos, el hash SHA256 del archivo antes y despues y el certificado obtenido por el verificador. Todos los APK deben verificar y coincidir con el certificado esperado. La validacion criptografica no reemplaza la comprobacion de nombre de paquete, version, ABI, dependencias y funcionamiento del WebView.

El certificado de `Source Stamp Signer` se informa por separado: acredita el sello de distribucion y no constituye otro firmante APK. La primera ejecucion del bundle 138.0.7204.180 (`ejecucion-20260905-143919-c0bbe8c8`) verifico criptograficamente los cuatro archivos, pero el wrapper original marco falsamente diferencia de certificados al incluir tambien ese sello. El parser fue corregido para distinguir ambos y exigir un unico firmante APK; la verificacion posterior aprobo los cuatro archivos.

El bundle 138.0.7204.180 esta verificado como referencia, pero NO fue elegido como componente final. El usuario aclaro que requiere una ROM simplificada con las mejoras ya integradas, no una instalacion APK individual. Se prepara la variante APK unica 138.0.7204.179 como componente de esa ROM. No se instalo ningun paquete mediante este procedimiento.

La APK original `chrome-70-original.apk`, de 67.265.948 bytes, verifico correctamente el 5/9/2026 mediante esquemas v2 y v3, con salida 0 en ambas modalidades. SHA256 del archivo:

`352c61df2f1eb5082bb2acba1a3e5fa04a5c0200680dcafab431135f287f1bf0`

Certificado firmante unico Google, SHA256:

`f0fd6c5b410f25cb25c3b53346c8972fae30f8ee7411df910480ad6b2d60db83`

Ese certificado se usa como valor esperado predeterminado para futuras actualizaciones; se obtuvo de una verificacion completa del respaldo, no solo de extraer un certificado de un ZIP. Para otro paquete o un cambio de clave justificado, se debe indicar explicitamente `-ExpectedCertificateSha256` y validar por separado la autorizacion de esa clave o su historial de rotacion.

La procedencia y hashes de las herramientas figuran en `herramientas.json`. El ZIP Android se verifico contra el SHA1 publicado en el catalogo oficial descargado por HTTPS; tambien se registro su SHA256 local. El ZIP Java se verifico contra el SHA256 publicado por la API oficial de Adoptium. Ambos metadatos originales se conservaron bajo `tools/verificacion-apk`.

Fuentes: [apksigner oficial](https://developer.android.com/tools/apksigner), [catalogo Android](https://dl.google.com/android/repository/repository2-3.xml), [Adoptium](https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jre&os=windows&vendor=eclipse).
