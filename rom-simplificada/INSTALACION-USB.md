# Pendrive · estado de la instalación

## Actualización física · preparación ejecutada el7/9/2026

El usuario autorizó expresamente ENV/BCB y trasladó el Kingston al primer P291. Se ejecutó un único intento de Acceso USB0.9 por LAN: resultado `prepared`, códigos0 y lecturas finales verificadas. La adquisición independiente de ENV/misc actuales, respaldos e informes coincide con el cambio previsto; las órdenes antiguas de cache ya no están activas. [Resultado y siguiente paso](../docs/evidencia/PREPARACION-ENTRADA-P291-09.md).

No repetir `prepare`, no usar la APK oculta ni volver a Update. La preparación no instaló Android ni reinició el equipo. Después del ciclo físico indicado, el usuario informó que apareció un menú de recovery. Se le indicó la ruta EXT → udisk → ZIP0.2.1; todavía falta confirmar aceptación del paquete y resultado de instalación. Los datos/Android originales todavía no se borraron. Los apartados inferiores describen el momento anterior a esta ejecución, incluido su estado de autorización.

## Vigente · entrega0.2.1 verificada el7/9/2026 a las23:06ART

El Kingston autorizado contiene los cuatro archivos actuales. La copia terminó con código0 y se releían completos con SHA correcto. [Recibo de entrega](../preparacion-usb/original-021-estado.json) · [Contrato exacto](../preparacion-usb/entrega-original-021.json) · [Revisión independiente](../preparacion-usb/REVISION-ORIGINAL-021.json).

| Archivo en la raíz del USB | Función |
| --- | --- |
| `TVBASE-P291-A9-0.2.1-RECOVERY.zip` | Instalar la plataforma simplificada derivada del P291 real; seis respaldos antes de borrar userdata y escribir cinco particiones. |
| `TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-RECOVERY.zip` | Restauración separada de cinco imágenes OEM; conserva los datos actuales, no recupera userdata anterior. No elegir para instalar TV Base. |
| `AccesoUSB-0.9.apk` | Preparación explícita de entrada al recovery interno; ya instalada en el TV. |
| `LEEME-AHORA.txt` | [Guía exacta copiada](original-p291/LEEME-USB-021.txt), con riesgos, éxito y condiciones de parada. |

Se archivaron y verificaron enPC los cuatro archivos antiguos antes de retirarlos: ZIP0.1.2, recovery externo, auxiliarBluetooth y guía;598.275.472bytes. El marcador, informes y carpetas de respaldos se conservaron. Quedan29.429.121.024bytes libres, por encima de los6.603.931.648 exigidos para los seis respaldos nuevos. **No se formateó ni reparó el pendrive.** Windows mantiene Warning; la copia y lectura correctas no certifican toda la salud del volumen.

Antes de moverlo al TV, usar la **expulsión segura de Windows**. El recibo acredita Flush de archivos y lectura, no un flush final del volumen ni persistencia de sus metadatos después de desconectarlo. La expulsión todavía está pendiente.

### Continuación desde el diálogo2%

La APK0.9 se instaló correctamente, pero la captura confirma que el diálogo de actualización del sistema sigue tapando la pantalla. No repetir Update, no pulsar botones ocultos ni cortar alimentación para intentar abrir la APK. Conectar el Kingston al primer P291 y mantener LAN permite acompañar el acceso existente desde esta sesión.

La preparación nueva modifica64KiB del entorno de arranque ENV y2KiB de BCB, después de respaldarlos y verificarlos, y neutraliza las órdenes antiguas de cache. Una escritura incompleta o incompatibilidad puede impedir que Android arranque; el respaldo no acredita un rescate físico. **El usuario pidió conocer ese riesgo antes de decidir: aún no se autorizó específicamente ni se ejecutó.** El acceso por LAN debe respetar esa decisión aunque no use la confirmación visual de la APK.

La [operación desde PC](original-p291/entrada-apk/OPERACION-LAN-09.md) conserva un único intento y permite continuar su observación si se pierde la conexión. Usa el helper0.9 ya instalado y no requiere pulsar botones ocultos. Sus pruebas locales no acreditan preparación física.

Solo después de una preparación cuyo cierre y relectura sean verificados se podrá indicar el ciclo de alimentación con USB conectado para intentar llegar al menú original. El helper no reinicia ni instala automáticamente. En recovery, la ruta identificada es «Apply update from EXT» → «Update from udisk», eligiendo el ZIP de instalación0.2.1. Sigue pendiente demostrar ese ingreso físico.

No hay ROM instalada, recuperación ensayada, WiFi reparado ni prueba de WebView/video en la nueva plataforma. [Evidencia completa](../docs/evidencia/ENTRADA-ORIGINAL-P291-021.md) · [Estado](../docs/ESTADO.md).

## Historial conservado: las instrucciones siguientes no son vigentes


## Vigente · ROM 0.2.0 verificada solamente en PC

La [nueva ROM desde originales y la restauración](original-p291/README.md) están construidas y verificadas, pero **todavía no fueron copiadas al Kingston**. No se hizo otro formato, grabación ni limpieza. Se conservan los entregables y recibos anteriores.

No repetir Update con 0.1.2 ni ejecutar su guía antigua. El ZIP nuevo no corrige por sí solo la espera del cierre de Android. Antes de una prueba se necesita una entrada a recovery y una ruta de paquete verificadas, además de preparar userdata limpia. Su instalador comprueba esos datos, pero no los borra o migra automáticamente. [Resultados y límites](../docs/evidencia/ROM-ORIGINAL-P291-020.md).

El paquete separado de restauración recupera cinco particiones OEM si se logra ejecutar recovery; no es una recuperación probada ni restaura userdata retirada. No se indicó otro reset en esta revisión. El BCB/hilo Java anteriores no quedaron cancelados al renombrar el ZIP.

## Historia de las entregas anteriores

## Vigente: no repetir Update con0.1.2

Elpendrive conserva ROM0.1.2 ysu [recibo de entrega](../preparacion-usb/rom-012-estado.json). Elintento posterior quedó al2%; ahora hayroot confirmado yuna traza que identifica laesperaWiFi. ElZIPinterno sepreservóíntegro conotronombre y se retiróde larutaactiva; faltaba elmapa requerido porrecovery. BCB yelhiloJava no quedaroncancelados.

La [comparación contra losoriginales](../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md) detectó diferencias dearranque ycompatibilidad defirma sinacreditar. Se conservan losarchivos entregados y susrecibos; no seha preparado otroZIPni seha escrito unaROM. No usar laguía antiguadelpendrive como indicación deotroUpdate. La propuesta siguiente deriva de losoriginales delprimerP291. [Opciones para decidir](../diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md).

## Instrucciones históricas conservadas


**Actualización:0.8 ya fue ejecutada y revisada. No repetirla.** Los informes útiles llegaron verificados; el cierre quedó vacío pese al aviso de finalización. [Resultado](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md). Los pasos de abajo conservan lo que se probó. La corrección de persistencia aún no está desplegada; esta revisión no preparó otra APK ni cambió el pendrive.

Próxima conexión ofrecida por el usuario: primerP291 por LAN al router y PC por WiFi. No hace falta mover el USB para cada consulta si su ADB existente resulta accesible. Mantener alimentación y HDMI del TV; esperar identidad comprobada antes de cualquier intervención.

**Entrega vigente:0.8, copiada y leída el7/9/2026 a las15:54 ART.** [Recibo](../preparacion-usb/postintento-08-estado.json). La ROM completa quedó detenida al2% con el actualizador OEM; todavía no hay instalación ni respaldo del TV confirmados. Esta captura aplica las partes de la [revisión de Fable](../docs/hipotesis/REVISION-CONJUNTA-FABLE.md) que permiten observar el fallo sin otro reinicio.

1. Cuando el **primer TV P291** muestre Android normalmente, conectar el Kingston.
2. Instalar **AccesoUSB-0.8.apk**, actualizando Acceso USB, y abrirla.
3. Pulsar una vez **«Guardar diagnóstico del último intento»**. Esperar el resultado; puede tardar unos minutos.
4. Al terminar, o si muestra un error, devolver el pendrive a esta PC. No repetirlo; conservar el mensaje de error.

No pulsar Update ni los botones de reinicio anteriores. Si Android sigue detenido en actualización, la captura aún no puede ejecutarse: comunicar ese estado. El resultado del último ciclo de alimentación sigue sin confirmar.

La APK busca registros anteriores y consulta WiFi, Bluetooth, batería, espacio y WebView. No cambia radios ni solicita instalación. Usa únicamente la conexión ya disponible dentro del TV; no requiere internet/Ethernet. Una salida denegada o agotada por tiempo también se guarda. «Completa» significa recorrido y archivos comprobados, no respuesta satisfactoria de todos los servicios.

## Contenido y conservación

```text
TVBASE/
├── AccesoUSB-0.8.apk
├── TVBASE-P291-A9-0.1.1-RECOVERY.zip   # conservada; no repetir Update
├── recovery.img                     # conservado; arranque no demostrado
├── TVBASE-MEDIA.txt
├── LEEME-AHORA.txt
├── TVBASE-evidencia-…/               # informes anteriores conservados
├── TVBASE-diagnostico-…txt
└── carpetas de Android y del volumen
```

Cada captura0.8 crea `TVBASE-postintento-...`. Conservar las carpetas parciales y cualquier `TVBASE-respaldo-*`. No existe un respaldo original del TV confirmado; `usb-antes.img` en PC es del antiguo pendrive.

Se retiraron14 archivos antiguos o reemplazados,573.327.869 bytes, tras archivarlos en PC y verificar sus hashes. Incluye APK0.2–0.7, guías anteriores, ROM0.1 retirada y ZIP de Fable. ROM0.1.1, recovery, informes y marcador permanecen. No se formateó ni reparó el volumen.

Preparador vigente: [preparar-postintento-08.ps1](../preparacion-usb/preparar-postintento-08.ps1). Exige identidad exacta del Kingston, pruebas, fuentes y firma de la APK; copia y verifica por lectura. La limpieza usa una lista de archivos explícitos, sin borrar carpetas. [Guía que está en USB](instalador/LEEME-POSTINTENTO-0.8.txt).

El intento0.7 queda documentado en [fotos y análisis](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md), su [recibo](../preparacion-usb/entrada-oem-07-estado.json) y el [estado](../docs/ESTADO.md). No es la instrucción vigente de instalación.
