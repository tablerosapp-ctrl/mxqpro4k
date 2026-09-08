# Instalación y restauración P291 0.2.2

## Estado

Corrección 0.2.2 copiada y releída en Kingston; TV en recovery. Instalación física pendiente. El usuario confirmó que mantuvo el TV encendido en recovery mientras devolvió el pendrive a PC. ADB está offline en recovery; no se volvió a preparar ENV/BCB ni se pidió reinicio.

El [error 0.2.1](ERROR-INSTALADOR-P291-021.md) se localizó en una condición que aceptaba únicamente nombres MMC tradicionales. Aborta antes de respaldar, formatear o escribir imágenes. La [fuente Amlogic](PARTICIONES-AMLOGIC-P291-022.md) explica el nombre lógico `system`. Las fuentes/ZIP/recibos 0.2.1 permanecen intactos.

## Cambio y controles

Instalador y restaurador 0.2.2 aceptan el nombre lógico esperado o el equivalente `mmcblkNpN`. El bloque abierto debe coincidir con rdev, atributos sysfs, número/tamaño de partición y padre directo MMC canónico 179:0 de7650410496B. Se verifican rangos sin solapamiento; cada primer layout se conserva y revalida antes de escribir. Los starts no se inventan ni se presentan como capturados anteriormente.

No cambia ninguna de las cinco imágenes de plataforma 0.2.0, ni kernel/DTB/drivers/Chrome. Permanecen la consulta ARM32 correcta, ENV normal, copia y tres hashes de respaldo, sync, formato con binario original, verificación vacía RO y cinco escrituras con boot al final. Se reconocen intentos parciales anteriores para no repetirlos automáticamente. [Fuentes y pruebas](../../rom-simplificada/original-p291/instalacion-022/) · [Restaurador](../../rom-simplificada/original-p291/restauracion-022/).

## Entrega comprobada en PC

| Archivo | Bytes | SHA256 |
| --- | ---: | --- |
| TVBASE-P291-A9-0.2.2-RECOVERY.zip | 573820005 | `163d4ce6e6fd4e02f06cb6646c53c259d1d3100547ee5c616c578782c3e54421` |
| TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.2-RECOVERY.zip | 913294443 | `914c683a1e15f4d5e6fa622c7b390184444d9071636e580b5818bf4794f47d09` |
| LEEME-AHORA.txt | 2856 | `762dfd86dfeeeb536de1d162718d182a8fd2020350abef417ba66d2ffe2184d4` |

[Contrato sellado de copia](../../preparacion-usb/entrega-original-022.json) · [Recibo de copia y lectura](../../preparacion-usb/original-022-estado.json) · [Revisión del preparador](../../preparacion-usb/REVISION-ORIGINAL-022.json) · [Cotejo final que resuelve el contrato pendiente de esa revisión](../../preparacion-usb/CIERRE-ENTREGA-022.json).

CierrePC: 2026-09-08T00:13:03.3593677-03:00, código0. Espacio libre: 29411508224B; requisito de instalación6603931648B. Los dos ZIP021 y su guía se archivaron y verificaron en PC antes de retirarlos del USB. Capturas, respaldo de entrada09, marcador y APK09 se comprobaron iguales antes/después. Sin formato ni reparación. Flush de archivos y relectura no demuestran por sí solos persistencia final de metadatos FAT: queda indicada expulsión segura de Windows.

## Siguiente ejecución física

Conectar el Kingston al TV aún en recovery, seleccionar Apply update from EXT → Update from udisk → `TVBASE-P291-A9-0.2.2-RECOVERY.zip`. No volver a AccesoUSB09: la preparación ya terminó y esa APK fija el ZIP021. No usar el ZIP ORIGINAL-RESTORE para instalar la versión simplificada, ni hacer wipe separado.

Seis respaldos de6067060736B deben completarse y verificarse antes de borrar userdata. Mantener alimentación y USB; comunicar cualquier error exacto sin repetir. Esperar el mensaje final antes de reiniciar. La copia/validación local no acredita formato de particiones, escritura de la ROM ni arranque.

El restaurador repone cinco OEM, conserva los datos existentes y no recupera userdata borrada. Reentrada desde Android nuevo, rescate y restauración física siguen pendientes. Plataforma Android9/Chrome138 conserva límites de framework/SELinux; proveedor efectivo, WiFi y carga de dosVP9/alfa/canvas requieren pruebas en el TV.

Trazabilidad: ADR-27, REQ-01/02/10/11/14, C-ZIP/C-REC/C-USB/C-TV, VAL-02/04 locales; VAL-06/07 y M2 físicos pendientes.
