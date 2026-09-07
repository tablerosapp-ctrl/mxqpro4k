# Colaboración: Codex y Fable 5.1

**Novedad para Fable: root y cadena del bloqueo confirmados.** [ResultadoROOT](../diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md) · [PilaJava y VDEX real](../diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md). El Future deBatteryStats espera una consultaWiFi, cuyo hilo esperaIWifi.start/HAL. Copia interna delZIP correcta, block.map ausente. Se preservan originales; no ejecutarforzado sin ladecisióndelusuario.

**Antecedente: intento0.1.2 con registro real del cierre.** [HallazgosLAN](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md) y [comparación de radios](../diagnostico/primer-tv-lan-20260907-184926/COMPARACION-RADIOS.md). Bluetooth inhabilitado desde arranque no evitó2%. La secuencia registra setupBCB reconocido → ActivityManager → BatteryStats.shutdown, sin preparación del mapa observada. Prioridad H1: distinguir la espera interna de BatteryStats; H2: no confundir acuseBCB con mapa/ZIP preparados. No repetir Update.

**Antecedente: retorno físico0.8 disponible para Fable:** [hallazgos](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md). WiFi/BatteryStats timeout5s,6ANR Bluetooth/140,477s, Pstore cambiado sin tramo de cierre.63archivos adquiridos;25sellos de datos válidos y cierre vacío pese al aviso de éxito. Hipótesis fortalecida, causalidad no demostrada. No pedir otra actualización; se prepara observación en vivo del primerP291 mediante LAN ofrecida por el usuario.

El usuario pidió publicar primero documentación e historial y después contrastar dos hipótesis en paralelo. Confirmó que Fable 5.1 ya está trabajando desde Claude Desktop en otra PC y con otra cuenta GitHub. Esta sesión no puede invocarlo directamente ni atribuirle resultados antes de recibirlos. Codex completó su [primera revisión H1](hipotesis/H1-RESULTADO-CODEX.md); el ZIP de Fable ya fue recibido y contrastado. [Revisión conjunta y decisiones](hipotesis/REVISION-CONJUNTA-FABLE.md): captura0.8 preparada con PROP-09/PROP-13 fase1; las hipótesis siguen abiertas.

Repositorio público verificado: **[tablerosapp-ctrl/mxqpro4k](https://github.com/tablerosapp-ctrl/mxqpro4k)**. Permite lectura sin invitación. Para escribir desde otra cuenta se pueden usar issues o un fork con pull request; no se conceden permisos de administración por este pedido. [Recibo de publicación](evidencia/publicacion-github.json).

## Punto de partida compartido

Leer, en este orden: [README](../README.md), [ESTADO](ESTADO.md), [ESPECIFICACION](ESPECIFICACION.md), [MAPA](MAPA-ARCHIVOS.md), [ROADMAP](ROADMAP.md) y [evidencia del último intento](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md).

- Primer TV: P291, `gxlx2_p291_1g`, Android9/API28, shell UID2000 por ADB exclusivamente local. LED averiado, WiFi afectado. No exigir Ethernet/red ni habilitar root.
- Segundo TV: P271; su hardware/bootloader/particiones no se transfieren al primero. Solo se reutiliza análisis del APK OEM porque los bytes de ambos coinciden por SHA.
- Objetivo: Android simplificado en eMMC, instalación por pendrive, drivers de video conservados, APK Flutter común, navegador/WebView y contenido local. No investigar la actualización automática que afectó WiFi.
- Captura0.6 completa: 25 archivos y diez SHA. El APK OEM y los certificados del P291 están identificados. La firma integral del ZIP0.1.1 verifica contra el certificado OTA real; no conocemos las claves del recovery interno.
- Intento0.7: menú OEM, ZIP completo elegido y confirmado, Copying, preparación Android2% por más de diez minutos. No recovery observado ni instalación/respaldo confirmados. No hay un log nuevo de ese intervalo.
- El ciclo manual indicado para salir del bloqueo no tiene resultado comunicado. No inventar que volvió Android o recovery. Las anteriores vueltas a Android pertenecen a otros intentos.

## Dos hipótesis para revisión independiente

| Línea | Responsable previsto | Pregunta central | Documento |
| --- | --- | --- | --- |
| H1 | Codex; revisión inicial disponible | Distinguir H1a, cierre Java OEM, de H1b, cierre tardío del kernel en el intento ADB anterior | [H1: resultado de Codex](hipotesis/H1-RESULTADO-CODEX.md) |
| H2 | Fable 5.1, desde Claude Desktop | ¿La cadena paquete interno → mapa → BCB → bootloader → recovery queda inválida o incompleta, aunque se resuelva el cierre? | [H2: preparación y recovery](hipotesis/H2-PREPARACION-RECOVERY.md) |

Pueden coexistir. Ninguna está demostrada por una barra al2%, una firma válida en PC o una coincidencia del DT. Trabajar en documentos separados y compartir primero hallazgos reproducibles. [Mensaje completo para Fable](ENTREGA-FABLE.md).

## Contrato de trabajo y retorno

1. Indicar commit público revisado, archivos y líneas. Diferenciar observación del TV, verificación local, referencia externa e inferencia.
2. Explicar qué dato confirmaría y qué dato refutaría la hipótesis. Priorizar el análisis de material existente.
3. Entregar diagnóstico, contradicciones encontradas y la prueba mínima que distinguiría causas. Incluir salida esperada, condición de detención y cómo guardar el resultado.
4. No ejecutar instalaciones, borrar, cambiar permisos, preparar BCB, pedir otro reinicio ni repetir capturas generales como parte del análisis. La coordinación decide la siguiente prueba física después de comparar ambas revisiones.
5. No modificar fuentes/releases originales para hacer coincidir pruebas anteriores. No usar las claves de desarrollo ni publicar firmware, APK de terceros o informes privados.

Formato de retorno: estado de la hipótesis; evidencia a favor/en contra; causa demostrada o solo sospechada; prueba mínima; riesgos reales; archivos que cambiarían; pregunta pendiente. Puede entregarse como issue, documento en un fork/PR o texto que el usuario copie entre ambas sesiones. No hace falta compartir cuentas o credenciales.

## Alcance del repositorio público

Contiene fuentes propias, recetas, contratos, historial saneado, manifiestos y conclusiones. Imágenes de firmware, APK, SDK, claves, fotos originales y registros crudos quedan en la PC operadora. Algunos enlaces a artefactos locales estarán ausentes al clonar; los hashes y hallazgos públicos permiten reconocerlos. No solicitar esos binarios antes de comprobar si son necesarios para la pregunta concreta.

El historial publicado anonimiza identificadores locales, manteniendo intactos el Git operativo y los artefactos firmados. Los SHA de artefactos describen los binarios originales; los SHA de fuentes de pruebas describen los bytes locales previos a normalización/anonimización. **Un clon es material de revisión, no un instalador listo para cualquier USB.** [Proceso de publicación](PUBLICACION.md).

## Actualización LAN y variante sinBluetooth

[Lectura del primerP291](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md): panic en glResetTrigger del móduloWiFi desde coordinaciónBluetooth; ANR con esperas de limpieza/inicialización. API BluetoothOFF e inhabilitación del paquete persisten tras apagado, pero el kernel aún cargaBT y WiFi quedaLoading. Usuario pide prescindir deBluetooth; [ROM0.1.2](../rom-simplificada/SIN-BLUETOOTH-0.1.2.md) preparada y entregada. Fable puede revisar si la exclusión cubre la carga sin dañarWiFi; no afirmar corrección física ni cierre del2%. Switch interno probado sin efecto.
