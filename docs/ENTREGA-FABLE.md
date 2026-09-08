# Mensaje para Fable 5.1 en Claude Desktop

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
