# Mensaje para Fable 5.1 en Claude Desktop

## Reconocedor 0.1 implementado y entregado

El usuario autorizó empezar. [Entrega](evidencia/RECONOCEDOR-USB-01.md): APK normal API21+ y formato de capturas secuenciales, ya copiados/releídos en Kingston; primera ejecución Android pendiente. [Fuentes y límites](../diagnostico/reconocedor-0.1/README.md). El importador verifica ZIP/manifiesto/tamaños/CRC/SHA sin extraer, conserva copias privadas y no convierte un perfil candidato en permiso de instalación. Las fuentes y el recibo vinculan la APK exacta; conservar esta versión para comparar con próximos informes. No publicar capturas/binarios crudos.

## Resultado físico y trabajo siguiente, pendiente de OK

**Nuevo alcance del 8/9/2026:** el usuario confirma varios reinicios correctos sin pendrive. [Registro](evidencia/REINICIOS-P291-SIN-USB.md). [PROP-17](PLAN-RECONOCIMIENTO-Y-PRODUCTO.md) reordena el siguiente trabajo: reconocimiento sobre Android para varias familias, calificación P291/P271/Rockchip, capa común con logo y catálogo firmado compartido por USB/Internet. Se requieren mediciones de proveedor WebView en la APK, VP9/alfa/canvas, recursos y tráfico. No hay adaptación Rockchip ni actualización remota de ROM implementadas. Las revisiones de código confirman piezas reutilizables, no un diagnóstico universal ya listo.

El primer P291 arrancó TV Base; el usuario confirma que puede conectarse por WiFi. El pendrive trajo seis respaldos y los recibos de formato correcto, montaje vacío de solo lectura y cinco escrituras verificadas por lectura. El cierre del instalador 0.2.2 indica `installed_verified`. Se guardaron y verificaron en PC 199 archivos, con un total de 6.091.261.673 bytes; los seis respaldos incluidos suman 6.067.060.736 bytes. [Evidencia](evidencia/INSTALACION-FISICA-P291-022.md) · [Hallazgos y resumen](../diagnostico/primer-tv-instalado-20260908/HALLAZGOS.md).

Incidencia abierta: Home, la tecla de la casita del control, no vuelve al inicio. El usuario prueba su APK; todavía no están comprobados el proveedor WebView efectivo ni el rendimiento multimedia. [ISSUE-HOME-01](INCIDENCIAS.md). La [revisión local de Home](hipotesis/HOME-P291.md) plantea hipótesis sobre la configuración inicial y la traducción de la tecla; los datos actuales del TV son desconocidos.

La [propuesta PROP-16](PROPUESTA-LOTES-Y-ACTUALIZACIONES.md) separa una capa común de producto de las bases por perfil de hardware. Distingue la calificación del primer ejemplar de la instalación rápida del resto, con identidad y respaldos individuales, y plantea actualizaciones por componente. REQ-15/16/17 y ADR-28 registran ese diseño como propuesto. Se deben medir las fases: no todo el tiempo de instalación correspondió a copiar respaldos, y aún no se puede prometer un ahorro.

El usuario pidió revisar las propuestas antes de actuar: no modificar el TV, construir o instalar otra ROM, corregir Home ni activar el servidor sin su OK explícito. Se permiten revisiones documentales; los cambios siguientes siguen pendientes. La recuperación y la reentrada desde el Android nuevo no se probaron.


## Antecedente: estado anterior a la prueba física de 0.2.2

## Vigente · error de nombre Amlogic corregido en0.2.2

La preparaciónENV/BCB09 funcionó: menú recovery y ejecución021 observados. El instalador abortó con destino no eMMC particionada: system antes debackup/formato/flash. [Error y alcance](evidencia/ERROR-INSTALADOR-P291-021.md). La fuenteAmlogic asigna nombres lógicos manteniendo parent/part_type; [referencias fijadas y geometría](evidencia/PARTICIONES-AMLOGIC-P291-022.md).

022 corrige instalación y restauración con validación completa de padreMMC, rdev/atributos/tamaños/rangos y revalidación. Misma plataforma0.2.0; dosZIP022 entregados/releídos, TV todavíarecovery. [Estado y evidencias](evidencia/INSTALADOR-P291-022.md). No repetir entrada09/Update, no proponer quitar la guarda. Próximas dos líneas de revisión: compatibilidad real del preflight de022 y plan de reentrada/actualización desdeAndroid nuevo. No hay respaldo deuserdata ni instalación física concluida.


## Antecedente de la entrega 0.2.1

## Resultado físico posterior · preparación0.9 completada

Ya existe [evidencia física de la preparación ENV/BCB](evidencia/PREPARACION-ENTRADA-P291-09.md), autorizada expresamente y ejecutada una sola vez en el primer P291. Cierre `prepared`, respaldos/recibos verificados y adquisición posterior de ENV/misc exacta. La preparación no instaló Android ni reinició. Después del ciclo físico posterior, el usuario informó un menú de recovery; aún falta confirmar la aceptación del ZIP y la instalación. No repetir launch/Update. Los apartados inferiores conservan el pedido de revisión previo a esta ejecución.

## Revisión vigente · instalador0.2.1 y entrada0.9

Empezar por [ESTADO](ESTADO.md) y la [evidencia0.2.1](evidencia/ENTRADA-ORIGINAL-P291-021.md). La plataforma deriva de las particiones originales del primer P291; root se obtuvo mediante el `su` existente con autorización del usuario. Las restricciones y afirmaciones sobre ausencia de root/respaldos que siguen abajo son antecedentes, no el estado actual. No instalar ni probar en otro equipo.

La entrada propuesta ya está implementada y revisada en [Acceso USB0.9](../rom-simplificada/original-p291/entrada-apk/README.md): copia/verifica ENV y BCB, neutraliza órdenes antiguas y prepara una orden de arranque transitoria para mostrar recovery interno. **No se ejecutó: modifica ENV con riesgo de impedir el arranque y el usuario pidió decidir tras conocer ese riesgo.** La APK está instalada, pero el diálogo del sistema al2% continúa superpuesto. Instalarla o abrirla no lo cancela; el siguiente acompañamiento será por LAN, después de esa decisión.

La revisión externa útil puede seguir dos líneas independientes:

- Entrada: [análisis de recovery/ENV](../rom-simplificada/original-p291/entrada/ANALISIS-RECOVERY.md), orden preboot/bootcmd, limitaciones de saveenv, concurrencia del cierre OEM pendiente y persistencia del helper. No proponer como probado un rescate de un equipo sin arranque.
- Instalación/restauración: [contrato de migración](../rom-simplificada/original-p291/instalacion-021/CONTRATO-MIGRACION.md), seis copias antes del formato, verificación de ext4 vacío, cinco destinos/boot al final y [restaurador separado](../rom-simplificada/original-p291/restauracion-021/README.md). La constante ARM32 de tamaño fue confirmada físicamente en lectura; los ZIP anteriores0.2.0 quedan históricos.

Registrar commit público, hallazgo con ruta/línea, evidencia, supuesto y condición de parada. Los recibos acreditan firma/copia o pruebas locales según su alcance; recuperación, instalación, WebView activo y video físico siguen pendientes. El [estado USB vigente](../rom-simplificada/INSTALACION-USB.md) distingue la copia del resultado en TV.

## Historial del pedido anterior

## Actualización para la revisión conjunta · ROM original 0.2.0

Ya se construyó una derivación desde los originales del primer P291 y un ZIP separado de restauración. Revisar [composición/evidencias](evidencia/ROM-ORIGINAL-P291-020.md) y [receta](../rom-simplificada/original-p291/README.md). No hay instalación física ni entrega USB nueva. La candidata0.1.2 y el menú OEM bloqueado no son la próxima prueba.

La revisión externa puede concentrarse en dependencias tras el recorte, entrada/recovery con geometría original, migración de userdata y límites de confianza del framework heredado. El gestor APK/Chrome ya tiene revisión independiente offline; faltan pruebas Android y el servidor del dueño. No ejecutar scripts sobre otro TV ni inferir compatibilidad del P271.

Revisá el repositorio público https://github.com/tablerosapp-ctrl/mxqpro4k. Trabajamos sobre un TV box P291 y necesitamos una revisión independiente de la hipótesis H2, coordinada con Codex, que revisará H1. Primero leé docs/COLABORACION.md y el estado actual; registrá el commit público que recibiste.

Queremos instalar en su memoria interna una ROM Android simplificada desde un pendrive, conservar drivers de video y APIs para APK Flutter/WebView, videos locales y actualización propia. No buscamos solo actualizar Chrome en el Android existente. El primer TV no tendrá red como requisito. Su ADB local ya funciona como shell UID2000; no habilites root ni cambies autenticación.

Estado comprobado: la captura0.6 obtuvo el APK exacto de OTAUpgrade y otacerts del P291. La firma integral de nuestra ROM0.1.1 verifica en PC contra ese almacén. El recovery interno, sus claves y el bootloader instalado no se extrajeron. Al elegir y confirmar el ZIP completo en el menú OEM aparece Copying y luego preparación Android al2%, detenida más de diez minutos. No se observó recovery ni instalación; no hay respaldo original del TV confirmado. El resultado del último ciclo manual indicado todavía no fue comunicado.

Tu línea H2 está en docs/hipotesis/H2-PREPARACION-RECOVERY.md. Auditá la cadena de preparación persistente: copia a /data/cache/update.zip, uncrypt_file, block.map, setupBcb, bootloader e ingreso al recovery interno. Contrastá el código del APK real con AOSP9 y con la referencia Amlogic, sin confundir referencias con el firmware instalado. Identificá si tenemos un error en la interpretación o en el paquete, y qué evidencia mínima permitiría distinguirlo.

Antes de proponer una prueba física, devolvé: evidencia a favor/en contra, supuesto más débil, dato que refutaría H2, cambios concretos si los hubiera y condición de detención. No repitas Update ni propongas otra APK que solo solicite reboot. No presentes como instalado lo verificado en PC, ni el pstore de intentos viejos como un registro del intento actual. H1 y H2 pueden coexistir.

Podés responder mediante issue, fork/PR o texto para el usuario. No necesitás credenciales de esta cuenta GitHub. No publiques claves, firmware, APK de terceros o logs crudos. Si falta un archivo imprescindible, indicá su ruta y por qué cambiaría la conclusión; primero usá las conclusiones saneadas, hashes y fuentes ya incluidas.
