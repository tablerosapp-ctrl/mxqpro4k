# Chrome/WebView integrado en la ROM Android 9

Estado: investigacion y componentes preparados; no se modifico una imagen ni se instalo software en el TV box. El objetivo vigente es entregar Android simplificado con el navegador/WebView ya integrado en su memoria interna. El APK se utiliza como componente de esa imagen, no como instalacion individual a realizar por el usuario.

## Decision tecnica

Para una primera base Android 9 compatible con esta placa, integrar Google Chrome **Monochrome 138 para ARM de 32 bits**, preservando su firma Google. Esta variante contiene navegador y proveedor WebView. Chrome 139 y posteriores exigen Android 10: conservar Android 9 fija el limite de actualizacion oficial en la rama 138. Es un avance respecto de Chrome 70, pero no convierte Android 9 en una plataforma con futuras actualizaciones oficiales de Chrome. [Limite anunciado por Google](https://support.google.com/chrome/thread/352616098/sunsetting-chrome-support-for-android-8-0-oreo-and-android-9-0-pie?hl=en-GB).

Componente elegido e integrado en la imagen experimental: APK unico **138.0.7204.179**, `com.android.chrome`, versionCode `720417920`, variante `armeabi-v7a`, minSDK 26 y maxSDK 28. Se verifico su firma criptografica general y para API 28, su certificado Google, el hash del archivo y la ausencia de splits obligatorios. SHA256: `3d9414001b3e2555831cd014df2c9ae5a6eab10190c4cffce7ecaad3c0f53f23`. Informe: `actualizacion-chrome/verificacion/ejecucion-20260905-144336-4f3410eb/resultado.json`. El bundle 138.0.7204.180 se verifico como referencia; sus cuatro APK son autenticos, pero no son el formato elegido. En el repositorio publico, el paso de .179 a .180 solo cambia `chrome/VERSION`. [Commit oficial .180](https://chromium.googlesource.com/chromium/src/+/refs/tags/138.0.7204.180).

La inspeccion del bundle .180 confirma directamente: targetSDK 35; biblioteca `lib/armeabi-v7a/libmonochrome.so`; metadato `com.android.webview.WebViewLibrary=libmonochrome.so`; componentes WebView; y ninguna dependencia obligatoria de biblioteca Trichrome. No extrapolar el resultado criptografico del bundle al APK .179: cada archivo se verifica por separado. La arquitectura Monochrome esta documentada por Chromium para Android 7–9. [Integracion Chromium](https://chromium.googlesource.com/chromium/src/+/d4afc97b7/android_webview/docs/aosp-system-integration.md#monochrome).

## Como queda dentro del sistema

Ubicacion propuesta en el sistema de archivos de la imagen: `/system/app/Chrome/Chrome.apk`, APK 0644, directorio 0755, propietario root:root. Al reconstruir el sistema se preserva el archivo firmado y su alineacion. En un producto AOSP construido desde fuentes, el modulo precompilado usa `LOCAL_CERTIFICATE := PRESIGNED`; se controla el procesamiento de DEX/JNI y se vuelve a verificar el APK resultante. No se cambia el manifiesto ni se vuelve a comprimir el APK firmado. Si se sustituye una preinstalacion anterior, se retira su APK y cualquier artefacto OAT/ODEX/VDEX asociado, dentro de la imagen de trabajo, sin dejar dos paquetes `com.android.chrome` contradictorios.

El Android framework debe listar `com.android.chrome` como proveedor permitido y predeterminado. La configuracion AOSP esta compilada desde `frameworks/base/core/res/res/xml/config_webview_packages.xml`; una copia suelta de ese XML en `/system/etc` **no la sustituye**. Se modifica el recurso de la compilacion o un overlay compatible con esa ROM y se comprueba su valor efectivo. Si el candidato ya tiene la entrada correcta, se conserva.

Ejemplo para una imagen que siempre preinstala Chrome y lo usa como unico proveedor:

```xml
<webviewproviders>
    <webviewprovider packageName="com.android.chrome"
        description="Chrome WebView" availableByDefault="true" />
</webviewproviders>
```

Sin elemento `signature`, AOSP 9 exige que sea una aplicacion de sistema. Con elementos `signature`, exige coincidencia con uno de los certificados publicos completos codificados en Base64; **no se escribe aqui el hash SHA256**. La clave de firma del APK es independiente de la firma del sistema/OTA: una ROM con test-keys puede contener una APK firmada por Google. Los builds debug omiten algunos controles del proveedor, por lo que no sirven para acreditar que una configuracion incorrecta funcionara en produccion. [Seleccion de proveedor AOSP 9](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r61/services/core/java/com/android/server/webkit/WebViewUpdater.java).

El respaldo Chrome 70 del segundo TV verifico con un unico firmante APK cuyo SHA256 es `f0fd6c5b410f25cb25c3b53346c8972fae30f8ee7411df910480ad6b2d60db83`. Los cuatro APK .180 coinciden. El sello Source Stamp es una firma de distribucion distinta; se registra aparte y no se confunde con otro firmante APK. Informes en `actualizacion-chrome/verificacion/`.

## Permisos y SELinux

No hace falta convertir Chrome en aplicacion privilegiada, asignarle UID system ni firmarlo con la clave de plataforma para que actue como WebView. De hecho, el segundo TV usa actualmente Chrome 70 desde `/data/app`, sin los flags SYSTEM/PRIVILEGED, como proveedor activo. Es evidencia del equipo inspeccionado, no prueba del funcionamiento de una ROM candidata todavia no examinada.

Para una integracion normal en `/system/app`, no se agrega una lista de permisos privilegiados de Chrome. `INTERNET` y los demas permisos normales se procesan por PackageManager; los permisos peligrosos conservan sus reglas de concesion. Las capacidades de almacenamiento y red de la aplicacion Flutter deben declararse en esa aplicacion: el WebView se carga en su contexto y no obtiene acceso general al equipo por estar preinstalado. Ubicar Chrome en `/system/priv-app` abre obligaciones adicionales de allowlist en Android 9 y no es necesario para este diseño. [Allowlist oficial](https://source.android.com/docs/core/permissions/perms-allowlist).

Con la politica AOSP 9, los archivos bajo `/system` reciben `u:object_r:system_file:s0`. Una aplicacion no privilegiada con targetSDK >=28, salvo una regla especifica del fabricante, usa el dominio `untrusted_app`; los procesos aislados y el zygote WebView tienen sus dominios existentes. **No se necesita proponer un nuevo permiso SELinux por adelantado**. Se conservan las politicas `app`, `isolated_app`, `shared_relro` y `webview_zygote` de la base funcional. No se cambia SELinux a permissive ni se elimina el aislamiento del renderizador para resolver una pantalla negra. Los permisos exactos adicionales, si alguno existe en el candidato, solo se justifican con una denegacion reproducible y el recurso concreto que necesita. [seapp_contexts AOSP 9](https://android.googlesource.com/platform/system/sepolicy/+/android-9.0.0_r61/private/seapp_contexts), [file_contexts](https://android.googlesource.com/platform/system/sepolicy/+/android-9.0.0_r61/private/file_contexts).

## Espacio y funciones que deben conservarse

El reporte del **segundo TV** muestra `/system` de aproximadamente 1,2 GiB con 199 MiB libres, `/data` con aproximadamente 1,9 GiB libres y 1 GB de RAM. El Chrome 70 respaldado mide 67.265.948 bytes y esta en `/data/app`; no se puede contabilizar ese espacio como liberable en `/system`. El APK unico .179 mide 160.143.409 bytes, aproximadamente 152,72 MiB. Agregarlo al sistema actual dejaria un margen reducido antes de DEX, metadatos y otras modificaciones. La ROM candidata puede tener otro contenido: se mide su particion y el tamaño final descomprimido, no solo el ZIP de descarga, antes de decidir que cabe.

Se conservan kernel/DTB y controladores GPU/VPU, EGL/GLES, codecs, OMX/MediaCodec, Hardware Composer y servicios multimedia de una base probadamente compatible. También zygote, WebView loader/RELRO, PackageManager, instalador de paquetes, almacenamiento/documentos, descargas, certificados CA, fuentes y componentes de red. La simplificacion retira aplicaciones ajenas al objetivo despues de revisar dependencias; no recorta estas API comunes. Ninguna mejora de version garantiza por si sola mejor rendimiento de dos videos VP9, transparencia y canvas en 1 GB de RAM.

## Comprobaciones de la imagen integrada

1. Antes de empaquetar: verificar APK .179 completo, firma, ABI, metadato WebView y ausencia de splits obligatorios; comprobar proveedor compilado y espacio real.
2. Despues de reconstruir: volver a verificar hash/firma del APK dentro de la imagen y conservar los contextos y modos de archivos. Resolver el mecanismo real de instalacion y firmas de la ROM por separado: integrar Chrome no activa el arranque por pendrive.
3. Tras instalar y arrancar: `dumpsys webviewupdate` debe identificar `com.android.chrome` version 138 como valido, habilitado para todos los usuarios y con RELRO finalizado. Las aplicaciones se reinician al cambiar de proveedor.
4. Abrir una APK de prueba WebView y medir navegacion, video local, VP9/transparencia/canvas, estabilidad y memoria; confirmar que siguen activos los codecs del fabricante. Probar tambien sin Play/GMS/cuentas.
5. Probar una actualizacion del componente con la misma firma y una actualizacion de la APK de producto desde el futuro gestor propio. El mantenimiento posterior debe conservar la autenticidad del APK y planificar Android mas nuevo para superar la rama 138.

Fuentes oficiales descargadas para reproducibilidad en `fuentes-webview/`. Antecedentes locales: `diagnostico/android-20260905-142854-a8286d9a/particiones.txt`, `webview.txt`, `memoria.txt` y `actualizacion-chrome/paquete-antes.txt`.

## Resultado de la construccion

La ROM P291 candidata realmente usaba WebView 66 `com.android.webview` en `/product/app/webview`; su recurso compilado solo listaba ese paquete. Se agrego Chrome en `/system/app` y un overlay estatico en `/vendor/overlay/TVBaseWebView`, preservando el framework firmado original. El overlay lista Chrome como predeterminado y el WebView antiguo como recuperacion. Ambas entradas y el manifiesto del overlay fueron inspeccionados despues de compilar. El proveedor efectivo solo se confirmara tras arrancar.

El `system` del candidato tenia 483 MiB libres antes de modificarlo y conserva unos 440 MiB despues del recorte e integracion; estos son datos del candidato, separados del segundo TV. Los 11 archivos modificados/agregados se verificaron dentro de las particiones y la imagen se empaqueto. Ver `LEEME.md` y `salida/VERIFICACION.json`. No se actualizo Chrome en el Android actual de ningun TV.
