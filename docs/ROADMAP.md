# Roadmap y propuestas

Orden por dependencias, sin fechas prometidas. Una etapa se cierra con evidencia y sus criterios de salida; la preparación local no sustituye el resultado físico.

| Etapa | Situación | Trabajo y salida verificable | Dependencia |
| --- | --- | --- | --- |
| M0 · Base y paquete | Preparación local completada | Candidato inspeccionado, ROM0.1.1 firmada, captura 0.6 completada, firma contra P291 verificada y recovery externo preparado; VAL-01 a 04 | Ninguna |
| M1 · Entrada USB P291 | **ROM real llegó al 2 %; reinicio/entrada pendientes** | Recovery visible, origen identificado y ZIP aceptado; VAL-05 | M0 |
| M2 · Instalación y arranque | Pendiente | Respaldo completo, cinco escrituras verificadas, arranque TVBASE desde eMMC sin USB; VAL-06 y 07 | M1 |
| M3 · Hardware y multimedia | Pendiente | Perfil real y suite de APIs/web/video/controles; dos VP9 + alfa/canvas y un 1080p; VAL-08 | M2 |
| M4 · Recuperación repetible | Pendiente | Ensayar acceso sin Android y restauración con originales; documentar qué fallos cubre; VAL-09 | M1, M2; antes de ampliar pruebas destructivas |
| M5 · Aplicación y contenido | Propuesto | APK común, catálogo local, descargas verificadas, borrado selectivo y ciclo offline | Especificación desde ahora; aceptación M3 |
| M6 · Administración propia | Propuesto | Agente, distribución firmada por grupos, actualización independiente de APK/motor/sistema y continuidad de datos | M3, M4, M5 |
| M7 · Android más nuevo y otras placas | Propuesto | Cada perfil supera entrada, recuperación y multimedia; base de Android que permita motor mantenido | Criterios M3/M4; investigación puede adelantarse |

## Propuestas ordenadas

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
