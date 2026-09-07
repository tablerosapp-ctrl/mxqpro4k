# Colaboración: Codex y Fable 5.1

El usuario pidió publicar primero documentación e historial y después contrastar dos hipótesis en paralelo. Fable 5.1 se usará desde Claude Desktop en otra PC y con otra cuenta GitHub. Esta sesión no puede invocarlo directamente ni atribuirle resultados antes de recibirlos.

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
| H1 | Codex | ¿Android se bloquea al cerrar sus servicios antes de generar el mapa y reiniciar? | [H1: cierre de Android](hipotesis/H1-CIERRE-ANDROID.md) |
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
