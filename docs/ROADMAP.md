# Roadmap y propuestas

## Actualización vigente · entrada0.9 e instalador0.2.1

| Etapa | Avance actual | Salida pendiente |
| --- | --- | --- |
| M0 · Plataforma y paquete | Plataforma0.2.0 inmutable; instalación0.2.1 firmada/verificada en PC; Acceso0.9 compilado/revisado; restaurador0.2.1 separado | Instalación/restaurador0.2.1 y APK0.9 copiados y releídos en USB, VAL-04 completada. Falta expulsión segura y traslado alTV. |
| M1 · Entrada | Método ENV/BCB preparado y revisado; probes físicos de formateador en archivo y tamaño ARM32 correctos | Decisión específica del usuario tras riesgos; después preparación persistente y recovery identificado. Los probes no cierran VAL-05. |
| M2 · Instalación | Migración implementada: seis respaldos íntegros antes de preparar userdata, cinco imágenes0.2.0 y boot al final | Respaldo físico, formato/RO, cinco relecturas y arranque interno sin USB, VAL-06/07. |
| M3 · Hardware/web/video | Drivers/kernel/DTB preservados y Chrome138 declarado | Proveedor efectivo, WiFi/Ethernet, controles, instalación APK y dos VP9/alfa/canvas medidos. |
| M4 · Recuperación | Restaurador0.2.1 devuelve cinco OEM conservando userdata | Ensayar entrada desde Android nuevo/fallido y restauración; data.img requiere receta propia fijada al respaldo futuro. |
| M5–M7 | Gestor APK/motor integrado y desactivado; resto conserva su alcance | App/contenido, servidor y VAL-10, ROM remota, producción y nuevas bases/perfiles. |

**ADR-26 / PROP-01:** la siguiente entrada ya no es repetir Update. Prepararía64KiB de ENV y2KiB BCB para el recovery interno y neutralizaría las órdenes antiguas, sin reset automático. El usuario todavía no decidió usar este método; la escritura de ENV añade riesgo de impedir el arranque. M1 queda pendiente aunque el pendrive se prepare correctamente. La APK0.9 ya está instalada, pero el diálogo2% la oculta: no ordenar una pulsación invisible ni cortar para abrirla. El [cliente LAN](../rom-simplificada/original-p291/entrada-apk/OPERACION-LAN-09.md) está preparado para acompañar la APK sin pulsaciones ocultas; no fue ejecutado y también depende de la decisión específica.

**PROP-02 / C-REC:** restaurar cinco imágenes no recupera los archivos de userdata. No presentar el respaldo de doce particiones actual como copia de toda eMMC, ni el futuro respaldo de seis como ya creado. El Android nuevo elimina su/ADB TCP inicial y no tiene gestor con REBOOT/RECOVERY: la reentrada y actualización completa posterior deben demostrarse.

**C-USB:** copia/relectura0.2.1 completadas a23:06:04ART, cuatro archivos verificados y código0 en [recibo propio](../preparacion-usb/original-021-estado.json). La expulsión segura Windows sigue pendiente y no se verificó el vaciado final de metadatos del volumen. Cuatro archivos viejos fueron archivados y comprobados enPC antes de retirarlos; no hubo formato/reparación. VAL-04 no cierra M1 ni acredita instalación. [Evidencia vigente](evidencia/ENTRADA-ORIGINAL-P291-021.md).

## Revisiones previas conservadas

## Antecedente · derivación original 0.2.0

**M0 / PROP-15:** cinco imágenes y ZIP0.2.0 construidos desde los originales, verificados en PC. Firma según recovery v1 y recorte por política. La copia USB de esta versión está pendiente; M0 no acredita entrada física.

**PROP-02:** paquete separado de restauración original construido y verificado. No cierra M4: todavía no se ensayó ejecutar recovery y recuperar el equipo.

**M1 → M2:** resolver entrada efectiva y ruta de paquete; diseñar preparación de userdata con conservación explícita de lo necesario. El instalador se niega a escribir sobre una migración pendiente. Luego instalar cinco particiones y probar arranque desde memoria interna sin pendrive. No repetir la ruta OEM bloqueada al2%.

**M3:** proveedor Chrome/WebView efectivo, ajustes/mando, instalación USB, Ethernet/WiFi, video local, dos VP9/alfa/canvas, memoria y tráfico atribuido. La eliminación de Bluetooth no acredita recuperar WiFi.

**M6 / PROP-12:** gestor APK/navegador implementado y revisado offline; falta servidor/configuración y VAL-10 en Android. Contenido, actualización de ROM, rollback, firmas de producción y reanudación automática siguen propuestos. El usuario dispone de servidor, pero no indicó su URL.

**M7 / PROP-05/06:** mover el framework a una base mantenida, conservar compatibilidad de video y desplegar SELinux/firma de producción. La derivación actual no sustituye ese trabajo. [Evidencia del avance](evidencia/ROM-ORIGINAL-P291-020.md).

## Roadmap y propuestas anteriores conservados

Orden por dependencias, sin fechas prometidas. Una etapa se cierra con evidencia y sus criterios de salida; la preparación local no sustituye el resultado físico.

| Etapa | Situación | Trabajo y salida verificable | Dependencia |
| --- | --- | --- | --- |
| M0 · Base y paquete | Preparación local completada | Candidato inspeccionado, ROM0.1.1 firmada, captura 0.6 completada, firma contra P291 verificada y recovery externo preparado; VAL-01 a 04 | Ninguna |
| M1 · Entrada USB P291 | **0.1.2 volvió al2%; registro llega a BatteryStats.shutdown** | Recovery visible, origen identificado y ZIP aceptado; VAL-05 | M0 |
| M2 · Instalación y arranque | Pendiente | Respaldo completo, cinco escrituras verificadas, arranque TVBASE desde eMMC sin USB; VAL-06 y 07 | M1 |
| M3 · Hardware y multimedia | Pendiente | Perfil real y suite de APIs/web/video/controles; dos VP9 + alfa/canvas y un 1080p; VAL-08 | M2 |
| M4 · Recuperación repetible | Pendiente | Ensayar acceso sin Android y restauración con originales; documentar qué fallos cubre; VAL-09 | M1, M2; antes de ampliar pruebas destructivas |
| M5 · Aplicación y contenido | Propuesto | APK común, catálogo local, descargas verificadas, borrado selectivo y ciclo offline | Especificación desde ahora; aceptación M3 |
| M6 · Administración propia | Propuesto | Agente, distribución firmada por grupos, actualización independiente de APK/motor/sistema y continuidad de datos | M3, M4, M5 |
| M7 · Android más nuevo y otras placas | Propuesto | Cada perfil supera entrada, recuperación y multimedia; base de Android que permita motor mantenido | Criterios M3/M4; investigación puede adelantarse |

## Propuestas ordenadas

**PROP-14 · Variante P291 sin Bluetooth, autorizada por el usuario.** EvidenciaLAN: panic en la ruta BT→WiFi y ANR durante inicialización/limpiezaBluetooth. Primero comprobar la desactivación normal en Androidactual; después preparar una revisión separada de0.1.1 que inhiba servicio, HAL y móduloBluetooth conservandoWiFi. Comparar todos los archivos ajenos al cambio y probar la red físicamente. No atribuir al cambio una reparaciónWiFi ni repetir Update sin resolver el cierre. REQ-13, C-ROM/C-TV, M1/M3. [EvidenciaLAN](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md).

**PROP-01 · Instalar mediante el actualizador real del P291.** La captura 0.6 completó los archivos faltantes y verificó sus hashes. La firma integral de ROM 0.1.1 coincide con los certificados OTA del P291. El APK OEM copia a /data/cache/update.zip y solicita preparar BCB antes del reinicio; el framework debe generar block.map. Acceso 0.7 solo comprueba el ZIP y abrirá ese menú, donde antes se había elegido un ZIP vacío. El primer intento con el paquete real también quedó al 2 % más de diez minutos. No repetir la ruta hasta disponer de evidencia del intervalo posterior o una entrada física distinta confirmada. No afirma corregir el cierre atascado ni verificar persistencia de BCB/mapa. Para la plataforma final, diseñar una preparación verificable separada del reinicio y ensayar la recuperación interna.

**PROP-02 · Paquete de restauración desde originales reales.** Después del primer respaldo, construir un ZIP de restauración específico de esa unidad/perfil, verificar sus payloads y demostrar que se puede entrar al recovery usado. No producir un supuesto respaldo original desde la ROM candidata. No prometer rollback automático en este esquema no A/B.

**PROP-03 · Suite de plataforma independiente.** Preparar muestras pequeñas con hashes, parámetros de video y una APK de diagnóstico estándar. Registrar versión efectiva de WebView, codecs, memoria, tiempos, reproducción offline y control. Cuando llegue la app real, agregarla sin reemplazar la suite general. Se puede desarrollar antes de completar M2, pero sus resultados físicos dependen del arranque.

**PROP-04 · Agente y catálogo separados del WebView.** Descargar a temporales, verificar antes de publicar, servir videos locales con búsqueda/lecturas parciales y mantener operaciones por identificador. Un proceso independiente coordina actualizaciones del motor y relanza la app. Definir un protocolo versionado; no acoplar el sistema a una página o versión concreta del negocio.

**PROP-05 · Base más reciente con video demostrado.** Android9/Chrome138 es una primera base experimental, con techo conocido de navegador. Evaluar Android más nuevo conservando la cadena de video por placa. Solo promoverlo si arranca y pasa la composición real. Linux con Android en contenedor queda como alternativa si aparece una ventaja medible; hoy añade integración sin beneficio comprobado.

**PROP-06 · Distribución para equipos reales.** Sustituir claves públicas de prueba por firma de producción bajo control del proyecto, evaluar condiciones de distribución de los componentes incluidos, documentar actualizaciones de seguridad y ensayar recuperación antes de desplegar una flota. Estas tareas no están hechas por generar el ZIP experimental.

**PROP-07 · Segundo WebView bajo presupuesto.** Medir la carga extra y pausar/recrear la automatización cuando haga falta. Prioridad secundaria. Descargas y consultas simples van en el componente nativo; usar otra página solo para tareas que necesiten su ejecución.

## Cómo incorporar un resultado

Relacionar el cambio con REQ → decisión → componente → prueba → etapa. Conservar mensajes de error, versiones, hashes y el contexto del equipo. Un fallo no cierra una etapa; sí puede cerrar una hipótesis. Actualizar primero [ESTADO](ESTADO.md) y el recibo/evidencia, después [proyecto.json](proyecto.json), este roadmap y el mapa generado.


**Actualización 7/9:** captura 0.6 completa, APK y certificados del P291 analizados. Entrada 0.7 probada: menú abierto y ZIP real confirmado, preparación detenida al 2 %; recovery e instalación pendientes. [Hallazgos](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md) · [Flujo Git](GIT.md).

## Revisión conjunta antes de otra prueba

El usuario pidió dos hipótesis en paralelo, tras publicar el estado. La [revisión H1 de Codex](hipotesis/H1-RESULTADO-CODEX.md) está disponible: separa el cierre Java OEM del cierre tardío del kernel en el intento ADB anterior. Incluye comprobación del pendrive, parser offline probado y diseño de observación sin otro reinicio automático. [H2](hipotesis/H2-PREPARACION-RECOVERY.md) ya recibió los aportes de Fable; la [revisión conjunta](hipotesis/REVISION-CONJUNTA-FABLE.md) adopta la captura0.8, con prueba física pendiente. Ambas hipótesis siguen abiertas. No se cierra M1 por este análisis. [Contrato de colaboración](COLABORACION.md).

## Aportes de Fable recibidos y revisados

| ID | Decisión | Condición / relación |
| --- | --- | --- |
| PROP-08 | Investigar vías Amlogic fuera del cierre Android | P291/USB/lectura/restauración aún no probados; no entregar Burning como rescate garantizado. C-REC/M1/M4. |
| PROP-09 | Implementada en0.8, física pendiente | Log anterior/pstore/espacio/WebView; aprovechar el intento ya ocurrido. C-ENTRY/M1. |
| PROP-10 | Incorporada al objetivo de PROP-03 | Medición multimedia tras instalar; conservar referencia de dos VP9/alfa/canvas. M3. |
| PROP-11 | No adoptada ahora | No repetir Update con otro ZIP sin evidencia/instrumentación nueva. M1. |
| PROP-12 | Diseño adoptado con correcciones | Separar ROM/motor/APK/contenido; reconciliar persistencia y ensayar cada rollback. C-GESTION/M6. |
| PROP-13 | Solo fase1 implementada en0.8 | Consultas con plazo; sin cambiar radios ni reiniciar. Las fases posteriores dependen de evidencia. C-ENTRY/M1. |

La [revisión conjunta](hipotesis/REVISION-CONJUNTA-FABLE.md) explica discrepancias, fuentes y el resultado que permitiría elegir la siguiente intervención. Ninguno de estos aportes cierra VAL-05 a09.

## Resultado posterior0.8 y trabajo acotado

[Captura revisada](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md): PROP-09 obtuvo pstore nuevo pero no el tramo de cierre; PROP-13fase1 obtuvo timeouts de WiFi/BatteryStats y ANR repetidos deBluetooth. La captura global es parcial por cierre vacío; datos útiles con25SHA válidos. No se cierraM1. El usuario ofreció LAN: observar en vivo el primerP291 y validar acceso existente, antes de decidir una desactivación reversible de radios separada del reinicio. El siguiente recopilador debe corregir persistencia; no hay APK nueva entregada ni otra instalación ejecutada.

Resultado PROP-14: ROM0.1.2 construida y entregada; VAL-02 local y copiaUSB comprobadas. En Androidactual, ajusteOFF y paqueteBluetooth inhabilitado persisten tras apagado; módulos/kernel todavía esperan. No cierraM1 ni demuestraWiFi recuperado. Switchinterno probado porusuario sinresultado. El contraste OEM0.1.2 con registro vuelve al2%: setupBCB reconocido, entrada a BatteryStats.shutdown y ningún avance posterior observado. Resolver el cierre y verificar la preparación persistente antes de otro intento.


Actualización root: acceso incorporado confirmado por pedido delusuario. La pilaJava prueba espera delcierre porWiFi/HAL; elZIPinterno verifica ymapafalta. Ocho particionescríticas respaldadas (102MiB); etapa sistema en curso, restauración no probada. [Opciones y riesgos para decidir](../diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md). La preparación manual y elreset de emergencia todavía no se ejecutaron.


**PROP-15 · Derivar la ROM de los originales del primerP291.** Root permite respaldar lasimágenes que síarrancan enestaunidad y conservar sukernel, DTB ygeometría. Preparar unarevisiónnueva consimplificación, WebView e inicio propios yBluetooth excluido. ElWiFioriginal fallaba: conservar elperfil no acredita repararlo. Resolver firmacompatible, preparación delpaquete yrestauración antes deampliarpruebas. [Evidencia y alternativas](../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md). Propuesta no implementada;0.1.2 queda conservadapara análisis, no es elpróximo intento autorizadoautomáticamente.


Respaldo final de esta revisión:12particiones seleccionadas y2538MiB verificados, incluidas las cinco que escribiría laROM. VAL-06 no se marca concluida: la instalación/restauración física siguen sinensayo yno hay snapshotcompleto deuserdata/cache. Elrecibo está en [RESPALDO](../diagnostico/primer-tv-lan-20260907-184926/RESPALDO-resumen-saneado.json).
