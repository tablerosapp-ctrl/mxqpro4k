# Instalador 0.2.1: aborto en identificación de system

## Observado en el TV

El usuario alcanzó el menú de recovery tras la preparación ENV/BCB 0.9 y el ciclo de alimentación. Seleccionó `TVBASE-P291-A9-0.2.1-RECOVERY.zip`. La fotografía muestra:

```
ERROR: destino no eMMC particionada: system
E:Error in /udisk/TVBASE-P291-A9-0.2.1-RECOVERY.zip (Status 1)
Installation aborted.
```

Esto acredita que recovery ejecutó nuestro `update-binary`. No acredita instalación ni identifica mediante hash la imagen de recovery que se ejecutó. El usuario confirmó después: **Kingston conectado a la PC y TV todavía encendido en recovery**. ADB no estaba disponible en recovery; no se solicitó otro reinicio.

## Causa localizada y alcance

En [main_linux.go de 0.2.1](../../rom-simplificada/original-p291/instalacion-021/main_linux.go), `block()` resuelve el enlace `/sys/dev/block/<major:minor>` y exige que su último componente tenga el formato `mmcblkNpN`. La fotografía prueba que el último componente fue `system`. Esa condición rechaza el nombre lógico que admite el controlador Amlogic; **no demuestra una avería de la eMMC**. La misma condición está en el restaurador 0.2.1.

Orden comprobado en el código de la versión entregada:

1. `loadPackage`: lectura de ZIP/manifiesto.
2. `prepareTargets`: perfil, destinos; falla en el primer destino, `system`.
3. Solo después se resuelve el USB, valida ENV, verifica payload y prepara userdata.
4. `executeMigration` se ejecuta todavía más adelante: seis respaldos, formato, cinco escrituras.

**Este intento no llegó a crear los seis respaldos, desmontar/formatear userdata ni grabar las imágenes Android.** El texto «Si ya comenzó la escritura…» es una advertencia condicional común a cualquier error, no evidencia de escritura. Esto no significa que no haya habido ninguna escritura interna: la preparación anterior modificó ENV/BCB y recovery puede escribir sus propios registros o metadatos.

El inventario del Kingston al volver a PC conserva ambos ZIP 0.2.1, AccesoUSB 0.9 y la captura `TVBASE-entrada09-*`; no presenta ninguna carpeta `TVBASE-respaldo-*` en la raíz. No se formateó ni reparó el pendrive.

## Corrección 0.2.2

Conservar las cinco imágenes de plataforma 0.2.0 y reemplazar exclusivamente el instalador/restaurador que identifica los bloques. Admitir el nombre lógico esperado o el nombre MMC estándar, comprobando descriptor, rdev, atributos, padre MMC canónico, geometría y rangos. No convertir la comprobación fallida en un bypass. [Fuente Amlogic y contrato de identidad](PARTICIONES-AMLOGIC-P291-022.md).

Los offsets `start` y los enlaces sysfs completos todavía no fueron capturados en recovery. Se leen, registran y fijan durante el preflight para revalidarlos antes de escribir; no se inventan offsets. La fuente de referencia no prueba que el kernel del TV sea idéntico a ese commit.

La comprobación anterior había trasladado al instalador una suposición sobre los nombres MMC. La sonda física ARM32 comprobó la consulta de tamaño, no esta resolución de sysfs. La regresión nueva cubre nombres lógicos Amlogic, nombres tradicionales y rechazos de identidades/rangos incorrectos; su aprobación en PC tampoco sustituye la ejecución del adaptador Linux dentro del recovery real.

Mantener recovery abierto y entregar nuevos ZIP independientes; no volver a ejecutar AccesoUSB 0.9 ni su preparación, ni usar Update del Android original. La corrección y las pruebas de PC no acreditan todavía una instalación física exitosa.

## Trazabilidad

- [Preparación previa verificada y recovery observado](PREPARACION-ENTRADA-P291-09.md).
- [Entrega 0.2.1, recibo inmutable](../../preparacion-usb/original-021-estado.json).
- [Recibo del error y fotografía conservada localmente](ERROR-INSTALADOR-P291-021.json).
- REQ-01/02/10, C-ZIP/C-REC/C-TV, VAL-05/06/07, M1/M2. M1 tiene menú y ejecución observados; M2 permanece pendiente.
