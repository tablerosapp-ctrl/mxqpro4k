# TV Base · empezar aquí

Android simplificado instalado en la memoria interna de TV boxes, con una APK común para Android TV, WebView, video local y administración propia. El primer destino es **P291 / `gxlx2_p291_1g`**. El segundo equipo P271 es únicamente una referencia de diagnóstico.

**Estado al 7/9/2026:** el usuario abrió el menú OEM, seleccionó la ROM completa 0.1.1 y confirmó Update. Tras Copying apareció la preparación Android al **2 %, inmóvil por más de diez minutos**. No repetir Update ni la entrada 0.7 como solución. La firma está comprobada contra el certificado OTA del P291, pero **recovery, instalación y respaldo original siguen sin confirmar**. [Nuevo resultado](diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md). Git local conserva el hilo; publicación pública autorizada en tablerosapp-ctrl/mxqpro4k, en preparación.

- [Empezar desde Claude Desktop / Fable 5.1](docs/ENTREGA-FABLE.md): contexto y revisión independiente H2.
- [Colaboración y dos hipótesis](docs/COLABORACION.md): responsabilidades, evidencia y formato de retorno.
- [Publicación y uso del clon](docs/PUBLICACION.md): historial saneado y dependencias que permanecen locales.

- [Mapa visual del proyecto](docs/index.html): grafo navegable de componentes, archivos y roadmap; funciona sin internet.
- [Estado y siguiente paso](docs/ESTADO.md): qué se sabe, qué falta y qué hacer según el resultado del TV.
- [Pasos vigentes con el pendrive](rom-simplificada/INSTALACION-USB.md): instrucciones vigentes para la prueba.
- [Especificación y aceptación](docs/ESPECIFICACION.md): requisitos identificados y pruebas necesarias.
- [Mapa de archivos](docs/MAPA-ARCHIVOS.md) y [árbol generado](docs/ARBOL-ARCHIVOS.txt).
- [Roadmap y propuestas](docs/ROADMAP.md): orden de trabajo y condiciones para avanzar.
- [Decisiones y lecciones](docs/DECISIONES.md): por qué se eligió cada camino.
- [Historial Git local y futura publicación](docs/GIT.md).
- [Reproducir y mantener](docs/DESARROLLO.md): entradas, herramientas, verificaciones y documentación.
- [Arquitectura del producto](ARQUITECTURA-ANDROID-TV.md): fundamentos de Android, WebView, almacenamiento y video.

Para retomar en otra sesión: leer **AGENTS → ESTADO → ESPECIFICACION → MAPA → ROADMAP**. Después abrir solo los archivos del componente afectado. [proyecto.json](docs/proyecto.json) conecta los identificadores y las evidencias para consulta automática. Los recibos de cada operación son la prueba de lo ejecutado; los objetivos y propuestas no acreditan funciones terminadas.

La [limpieza documentada](docs/LIMPIEZA.md) retiró 6.615.135.611 bytes de temporales y extracciones regenerables. Las fuentes, claves locales, ROM firmadas, respaldos y registros se conservan. El dossier HTML y los documentos archivados son antecedentes fechados, no instrucciones de instalación vigentes.
