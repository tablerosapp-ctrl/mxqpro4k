# Entrega del extractor independiente de recovery 0.1

El usuario amplió el reconocimiento y aprobó el recorrido combinado: APK para identificar, plan asociado al informe y extracción de originales desde recovery compatible. Se construyó un ejecutable nuevo; no se modificaron el instalador0.2.2 ni sus imágenes y no se contactó el TV. [Contrato y fuentes](../../diagnostico/extractor-recovery-0.1/README.md) · [Recibo compilación](../../diagnostico/extractor-recovery-0.1/COMPILACION.json) · [Recibo USB](../../preparacion-usb/extractor-01-estado.json).

## Paquetes y pruebas PC

| Variante | Bytes ZIP | SHA256 |
| --- | ---: | --- |
| ARM32 | 1380373 | `1f45405d22193b1e09cc694bc5328be6e8aa7f071e0d77323cacc15611063f08` |
| ARM64 | 1308031 | `5502123db9fc92cfd5f3173b32bfaff37e83e733752c91c888d70652fec0ac85` |

Nueve archivos de construcción sellados, ELF estáticos sin intérprete/segmento dinámico; firma v1/SHA1 verificada en Python y OpenJDK, contenido y CRC verificados. Once comandos de construcción terminaron con código0. Las pruebas Go ejecutadas en Windows incluyen 21 funciones principales y 71 eventos PASS contando subcasos/padres; no son 71 ensayos físicos independientes. Las pruebas Linux ARM32/ARM64 se compilaron pero no se ejecutaron.

Motor: límites de tamaño/espacio, fuentes cortas/largas/cambiantes, corrupción de destino, creación exclusiva, fallos de sincronización/cierre, cambio de identidad, prevalencia de recibo fallido y comprobación de manifiesto. Selección: RO de montaje/superblock, padre ocupado, particiones superpuestas y áreas estables. El generador de plan se prueba con el validador real de ZIP y rechaza salida existente, datos inválidos y fallos de persistencia. [Resumen de pruebas](../../diagnostico/extractor-recovery-0.1/PRUEBAS-PC.json).

La suite Python combinada ejecutó40 métodos:39 pasaron y uno se omitió explícitamente por falta de privilegio Windows para crear symlinks reales. Pasaron la guarda simulada de reparse y una prueba real de hardlink. Se incluyen15 pruebas del plan y25 del verificador de captura; este último comprueba también hashes agregados, archivos extra, cierres fallidos e inventario sin imágenes.

La revisión independiente detectó y se corrigieron cuatro problemas antes de firmar: enlace sysfs `device`, bloqueo de hijas de un padre ocupado, fijación del destino con descriptores/openat/mkdirat y distinción de montaje realmente RW. Se añadieron guardas de swap y de áreas boot con particiones hijas. La revisión final no encontró nuevos bloqueantes; es revisión estática, no prueba Linux/TV.

## Kingston

Preparación nueva `preparar-extractor-01.ps1`: CheckOnly y una ejecución Prepare con código0. Identidad física/UniqueId/tamaño/USB/no sistema comprobados. Cierre 8/9/2026,15:50:21 ART. Nueva carpeta `TVBASE-EXTRACCION`, dos ZIP, guía y marcador: cuatro archivos con Flush(true) y SHA por relectura. PLANES y CAPTURAS vacíos.

Los 200 archivos previos de hasta64MiB se cotejaron por hash; siete mayores por metadatos, sin atribuirles una nueva lectura integral. El inventario anterior quedó igual, incluida la APK de reconocimiento. No se borró, formateó, reparó ni cambió ninguna partición. Espacio libre:23341367296B. Se indicó expulsión segura; `safe_removal_pending=true`, `volume_flush_verified=false`. No repetir el preparador ni reescribir este recibo.

## Alcance pendiente

Sin un plan coincidente el extractor guarda solo inventario. No existe todavía plan de una captura APK física nueva. Debe recibirse ese informe para asociarlo, elegir ABI y revisar la entrada/firma del equipo; [P271](RECOVERY-P271-ALCANCE.md) tiene antecedentes distintos de P291. La correspondencia DT es de perfil declarado, no identidad física acreditada.

El adaptador lee eMMC interna; puede omitir áreas ocupadas o no admitidas. No obtiene RPMB/MTD/UFS por este código. No monta/desmonta, modifica bloques, instala ROM ni reinicia; el recovery anfitrión puede escribir registros/metadatos. Relecturas iguales no son una instantánea atómica. No hay nueva captura de TV, ejecución recovery, restauración o ausencia de malware acreditadas.

La próxima etapa también incluye la [revisión de componentes heredados](../REVISION-COMPONENTES-HEREDADOS.md) solicitada por el usuario. No se retiraron servicios en esta entrega.
