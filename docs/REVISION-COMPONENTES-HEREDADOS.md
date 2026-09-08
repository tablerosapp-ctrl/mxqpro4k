# Revisión prioritaria de componentes heredados y conexiones

**Petición explícita del usuario, 8/9/2026:** en la siguiente etapa, quitar los remanentes de teléfono que no necesita TV Base —almacenamiento de mensajes, teléfono, contactos, llavero y otros—, revisar especialmente el nombre visible `IntentFilterVerificationService` y auditar posible malware y conexiones. Se registra como trabajo **importante, junto con la optimización de recursos y reproducción**, dentro de REQ-14 y [PROP-17](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md). No se aplicó ninguna retirada, desactivación, cambio de permisos, modificación del TV o nueva ROM en esta revisión.

El resultado buscado es una base enfocada en la APK, WebView, video y administración propia, con una justificación concreta para cada componente conservado. La sospecha del usuario se conserva como asunto a investigar: un nombre visible, un permiso de Internet o una firma heredada no prueban por sí solos que un binario sea malicioso o seguro.

## Lo que ya sabemos y lo que falta identificar

La [política 0.2.0](../rom-simplificada/original-p291/politica-paquetes.json) conservó proveedores y servicios para mantener APIs del framework. La [composición verificada en PC](../rom-simplificada/original-p291/COMPOSICION-VERIFICADA.json) registra 39 APK, incluidas estas cinco. Son hashes de las imágenes construidas y selladas; no una nueva lectura de los paquetes actualmente instalados ni una certificación de su comportamiento.

| Archivo dentro de system | SHA256 registrado en la composición 0.2.0 |
| --- | --- |
| `/priv-app/TelephonyProvider/TelephonyProvider.apk` | `d2ffc2742db8bf7b554034be9e2b5187849770dc22ac498a67d617b9c6245dff` |
| `/priv-app/ContactsProvider/ContactsProvider.apk` | `ca1351867d0a447462628bc61bf5c18bba50762d63bb00e596aa22e41fad988a` |
| `/app/KeyChain/KeyChain.apk` | `1a5ff2d43344314976cc3a16e4304b2fca4f150e54e9390c69856d7bec14ce5a` |
| `/app/CertInstaller/CertInstaller.apk` | `a18bbf8c7db67a8cd759efa9343fa4e331c2965c841bf9110f2d9049bbf32358` |
| `/priv-app/StatementService/StatementService.apk` | `f020a53d5c4ff60e456e72ae6015dcc32e682191151246840b1c6fc9d7687e13` |

El nombre visible «almacenamiento de mensajes» podría corresponder a un proveedor y no a una aplicación de mensajería. «Teléfono», «contactos» y «llavero» también requieren identificar paquete, versión, ubicación del APK y etiqueta real. No aparecen APK separadas llamadas Phone, Dialer o Messaging en la lista de 39 archivos; eso no identifica la pantalla que vio el usuario ni demuestra que el framework carezca de APIs de telefonía.

La fuente AOSP utiliza la etiqueta **Intent Filter Verification Service** para StatementService y su manifest declara el paquete `com.android.statementservice`, con un receptor para verificación de enlaces. Es una correspondencia de referencia, todavía no una identificación del binario que el usuario vio. [Etiqueta AOSP](https://android.googlesource.com/platform/frameworks/base/%2B/1c1ae5d/packages/StatementService/res/values/strings.xml) · [Manifest AOSP](https://android.googlesource.com/platform/frameworks/base/%2B/699c1e4e/packages/StatementService/AndroidManifest.xml).

Android puede comprobar que una web autoriza a una APK a abrir sus enlaces consultando `/.well-known/assetlinks.json`; esa conexión puede tener una función legítima. Hay que contrastar dominio, APK que desencadenó la consulta, momento y contenido del código. No se atribuye a este TV ninguna consulta que no se haya observado. [Verificación oficial de App Links](https://developer.android.com/training/app-links/verify-applinks).

KeyChain también es una función habitual de Android: ofrece acceso autorizado a claves privadas y cadenas de certificados del almacén de credenciales. Retirarlo puede afectar consumidores de esas credenciales; no se debe confundir su presencia con robo de contraseñas ni asumir que todas las conexiones HTTPS dependen de él. El papel exacto de la APK OEM y sus consumidores permanece por revisar. [API oficial KeyChain](https://developer.android.com/reference/android/security/KeyChain).

## Matriz de revisión pendiente

Todas las decisiones de esta matriz están pendientes de identificación y validación. Retirar significa preparar un cambio nuevo y acotado, con prueba y recibo propios; no editar las fuentes, imágenes o recibos sellados de 0.2.0/0.2.2.

| Componente señalado | Motivo de revisión | Identificación y dependencias que faltan | Criterio de retirada o conservación y prueba |
| --- | --- | --- | --- |
| Almacenamiento de mensajes / posible `com.android.providers.telephony` | Un TV sin función telefónica podría no necesitarlo. | Confirmar etiqueta, APK/hash, autoridades de providers, permisos y consumidores en framework, ajustes y APK del usuario. | Retirar solo si las funciones requeridas y sus consumidores se mantienen; probar arranque, ajustes, instalación/actualización de APK, WebView, archivos y video. |
| Teléfono, marcación y componentes relacionados | Identificar remanentes y servicios sin utilidad para el producto. | Obtener paquete exacto antes de asumir `com.android.phone`; revisar si es UI, proveedor, servicio del framework o biblioteca compartida. | Distinguir ocultar una entrada de eliminar su implementación; comprobar dependencias y errores nuevos, además de CPU/memoria en reposo. |
| Contactos / posible `com.android.providers.contacts` | Reducir proveedores sin consumidores necesarios. | Confirmar identidad, autoridades, cuentas/sincronización y accesos de aplicaciones o ajustes. | No inspeccionar ni publicar agendas personales; probar consumidores con datos de prueba, inicio, APK y permisos antes de retirar. |
| Llavero / posible `com.android.keychain`, y `com.android.certinstaller` | Evaluar qué gestión de credenciales necesita TV Base. | Confirmar APK/hash/certificado firmante, bindings y consumidores; separar KeyChain, instalador de certificados, almacén de CA y keystore. | Conservar las funciones necesarias o ofrecer sustitución probada. Verificar navegación HTTPS, certificado cliente si se usa, red con certificados si se usa, instalación de APK y rechazo de certificados no confiables. No resolver fallos desactivando validación TLS. |
| `IntentFilterVerificationService` / posible `com.android.statementservice` | Sospecha explícita del usuario y revisión de conexiones automáticas. | Confirmar etiqueta→paquete→APK/hash/firma; leer manifest/código y receptores, dominios declarados por apps y atribución de tráfico al UID/proceso. | Si su función no es necesaria, proponer retirada/configuración acotada y probar enlaces HTTP/HTTPS, selección de navegador, enlaces hacia la APK, instalaciones y WebView. Un nombre AOSP no certifica que la APK OEM sea idéntica. |
| Otros servicios, binarios y bibliotecas heredados | Reducir superficie y consumo; investigar persistencia o red sin explicación. | Inventariar init, receptores, jobs, permisos, privilegios, UID compartidos, bibliotecas nativas, endpoints y carga de código. | Decidir por evidencia de función y dependencia; proteger WiFi, HDMI/audio/control, kernel/DTB, codecs/HAL, TEE/DRM usados y recuperación. Medir después de cada cambio. |

## Método y evidencia exigidos

Primero se vincula cada observación visible con una identidad reproducible: perfil y unidad, nombre de paquete, versión, ruta del APK, SHA256 y huella de su firmante. También se registran UID, componentes exportados, permisos, estado habilitado y origen de la información. Una etiqueta o package name puede imitar a otro componente; un hash coincidente acredita bytes, no ausencia de vulnerabilidades o actividad maliciosa. Las omisiones por permisos quedan explícitas.

El análisis local contrasta esos bytes con la composición sellada y revisa manifest, código, bibliotecas nativas y mecanismos de persistencia. La [auditoría previa de servicios](../rom-simplificada/original-p291/AUDITORIA-SERVICIOS.md) ya distingue sockets y métricas internas de envío acreditado. No certificó ausencia de llamadas de red, y no debe reinterpretarse como tal. Ninguna APK, captura privada o imagen del TV se sube automáticamente a un servicio público de análisis.

Después, en una fase de pruebas del TV autorizada por separado, se observa arranque, reposo, uso de la APK, reproducción y actualización en intervalos definidos. Se correlacionan destinos y volumen con UID/proceso y evento cuando el acceso lo permita. La captura en una red de prueba complementa la lectura del Android, con los límites de ambos métodos: una IP o ubicación geográfica no identifica por sí sola malware; un UID compartido puede impedir atribuir una conexión a una única APK. No hace falta capturar contraseñas ni descifrar comunicaciones personales.

Antes de ensayar una retirada se conserva la línea de base y una ruta de recuperación comprobada para el perfil. Se prepara una revisión nueva con la menor modificación suficiente y posibilidad concreta de volver al estado anterior. No se promete reversión automática: la restauración P291 sigue sin ensayo. No se repiten dumps de WiFi/BatteryStats que ya dejaron trabajo bloqueado.

La aceptación incluye Home y ajustes, instalación y actualización de la APK, proveedor WebView real, red, lectura/escritura USB, video local, los dos VP9 con alfa/canvas, audio/HDMI y reinicios acordados. CPU, memoria, temperatura y tráfico se comparan bajo la misma carga. Si una función de certificados, enlaces o archivos no forma parte del producto, se registra esa decisión y su alcance; no se da por probado lo que no se ensayó.

Cada componente termina con uno de estos resultados: conservar con motivo; retirar con pruebas; sustituir/configurar con pruebas; o pendiente por evidencia insuficiente. El informe de red concluye con hallazgos concretos y cobertura —por ejemplo, actividad no explicada en cierto proceso o ausencia de ella durante el intervalo observado—, sin prometer una certificación absoluta de sistema libre de malware.
