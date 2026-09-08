# Construcción y provisión del gestor de actualizaciones

Fuentes: [gestion-tvbase](../../componentes/gestion-tvbase/README.md). Todo lo de este directorio opera en la PC. No modifica imágenes ni accede al TV o al pendrive. El launcher y el compilador anteriores permanecen intactos.

## Entregables e integración

- [compilar-gestion.py](compilar-gestion.py): compila con las herramientas Android 28 existentes, alinea y firma usando la clave de componentes existente, cuyo contenido verifica que no cambió. El propietario de la ROM integra después el APK y el XML.
- [compilacion-resultado.json](compilacion-resultado.json): ruta y hash del APK real, hashes de fuentes/configuración y límites de verificación. La ubicación del APK se resuelve desde este recibo para evitar seleccionar una compilación vieja.
- [privapp-permissions-tvbase-gestion.xml](privapp-permissions-tvbase-gestion.xml): solo INSTALL_PACKAGES; mismo `/system` que el APK en priv-app.
- [probar-gestion.py](probar-gestion.py), [CoreTest.java](CoreTest.java) y [PolicyCheck.java](PolicyCheck.java): pruebas reales del verificador en JVM y validación de la política al compilar.
- [pruebas-resultado.json](pruebas-resultado.json): resultado de las regresiones offline. No sustituye una prueba Android de permisos, descarga y PackageInstaller.
- [manifest_tool.py](manifest_tool.py): prepara configuración y manifiestos firmados usando una clave del dueño ya existente. No genera una identidad de producción ni contacta un servidor.

Los outputs, registros de herramientas y claves efímeras de pruebas permanecen en `privado/`, excluido de publicación. Las claves reales existentes no se copian ahí ni se modifican. La firma de desarrollo del gestor es experimental; una distribución definitiva debe definir y conservar su identidad de firma.

## Compilar y probar

Desde la raíz del proyecto, con el Python local y las dependencias ya instaladas:

```text
python rom-simplificada/original-p291/gestion/compilar-gestion.py
python rom-simplificada/original-p291/gestion/probar-gestion.py
```

La compilación por defecto usa `enabled=false`, sin URL, clave pública del dueño ni trabajo de red programado. Para incluir una política real previamente preparada, agregar `--owner-config RUTA_LOCAL_OWNER_CONF`. El compilador verifica su sintaxis y política mediante el mismo Core Java antes de generar el APK. Los archivos de claves existentes son entradas, no destinos de generación.

## Configurar un servidor propio después

Faltan la dirección HTTPS concreta y la clave pública del dueño. El usuario confirmó que dispone de servidor, pero no proporcionó su dirección: la entrega conserva la capacidad desactivada. No hay importador de configuración USB dentro de la APK 0.1. La provisión inicial se realiza en la PC antes de compilar/integrar; para cambiarla después habrá que distribuir el gestor con la misma firma por la vía autorizada de instalación.

Preparar un JSON local de políticas de paquetes. Cada entrada contiene exactamente `package`, `certificateSha256` y `role`; este último vale `app` o `browser`. El certificado es el SHA256 del firmante de la APK, no el hash del archivo, la Source Stamp ni el certificado TLS. Chrome mantiene su certificado original; las APK de producto mantienen el suyo.

```text
python manifest_tool.py config --public-key CLAVE_PUBLICA_PEM --manifest-url URL_HTTPS_DEL_DUEÑO --hosts HOST_MANIFIESTO,HOST_APK --packages POLITICAS_JSON --out OWNER_CONF
```

Son marcadores para sustituir por datos reales, no un endpoint configurado. `--auto-apps` habilita mantenimiento remoto de aplicaciones y `--auto-browser` el del navegador. `--maintenance-start-utc HH:MM` y `--maintenance-minutes N` definen la ventana; `--poll-hours N` la frecuencia de consulta adicional. Sin las opciones auto, la configuración solo busca/prepara para instalación local. Ningún comando escribe en un archivo de salida existente.

## Publicar un manifiesto firmado

El servidor sirve un archivo de texto estático y las APK por HTTPS. No necesita ejecutar comandos recibidos desde el TV ni abrir conexiones entrantes a él. El manifiesto se genera desde un JSON con exactamente estas propiedades:

| Nivel | Campos y significado |
| --- | --- |
| Documento | `sequence` entero positivo monotónico; `issuedAt` y `expiresAt` en segundos Unix; `apks` con 1–16 entradas. |
| Cada APK | `package`, `versionCode`, `minSdk`, `maxSdk`, `abis` como lista, `bytes`, `sha256`, `certificateSha256`, `url`. |

`minSdk` debe coincidir con la APK real. `maxSdk` es el límite permitido por la publicación; se comprueba además el límite real si el APK lo declara. `abis` debe enumerar exactamente las ABI de sus bibliotecas `lib/<abi>/*.so`, o `['none']` si carece de ellas. Solo se admiten APK únicas; los bundles/splits requieren otra implementación. No publicar una versión igual o menor a la ya instalada. El payload puede durar como máximo 31 días y necesita un reloj válido.

```text
python manifest_tool.py sign --spec MANIFIESTO_JSON --key CLAVE_PRIVADA_PEM_DEL_DUEÑO --out MANIFIESTO_FIRMADO
```

La clave privada es un PEM RSA sin cifrar leído localmente por esta utilidad; debe mantenerse fuera del repositorio público y del servidor de archivos. La herramienta no la envía ni imprime. Una integración con un firmador externo/HSM queda pendiente. La publicación de una secuencia es inmutable: si cambian los APK, destinos o fechas se utiliza otra secuencia mayor.

Formato transportado: `TVBASE-SIGNED-1`, seguido de campos `payload` y `signature` en Base64. El payload decodificado empieza con `TVBASE-UPDATES-1` y contiene pares `clave=valor`, con campos de APK indexados `apk.0.*`. La firma es RSASSA-PKCS1-v1_5 con SHA256 sobre esos bytes UTF-8 exactos. No volver a serializar el payload al verificarlo. Se rechazan claves duplicadas/desconocidas y no se admiten comandos o scripts.

## Evidencia y límites

Las pruebas generan claves RSA efímeras dentro del directorio privado, verifican firmas y alteraciones, caducidad, repetición de secuencia, cambio de contenido, hosts, certificados declarados, API/ABI, metadatos del APK compilado y compatibilidad entre el generador Python y el verificador Java. El host `.invalid` de esos fixtures es reservado y nunca recibe una conexión. La firma del APK compilado se verifica con apksigner para API 28.

No se ejecutan clases Android mediante stubs en la JVM ni se presenta esa simulación como una instalación real. Queda pendiente, después de integrar y arrancar la nueva ROM: confirmar INSTALL_PACKAGES, probar el servidor real del dueño y una actualización válida/una rechazada, simular interrupción durante descarga/sesión, comprobar ajustes y control remoto, y medir el resultado de cambiar Chrome con la APK de producto. Los callbacks, JobScheduler y la sincronización de archivos de Android necesitan esa prueba física.

La configuración automática no transmite telemetría ni reportes de instalación a un backend: el resultado queda localmente en preferencias y en la pantalla del gestor. No hay rollback, rotación remota de claves ni reanudación automática del video. Un fallo de sincronización o de política detiene la operación; un timeout del cliente no garantiza cancelar una operación ya entregada a PackageInstaller.
