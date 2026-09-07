# TV Base · empezar aquí

Android simplificado instalado en la memoria interna de TV boxes, con una APK común para Android TV, WebView, video local y administración propia. El primer destino es **P291 / `gxlx2_p291_1g`**. El segundo equipo P271 es únicamente una referencia de diagnóstico.

**Estado al7/9/2026, 00:00 ART:** Acceso USB0.4 también dejó el TV sin señal. Los informes confirman que existe una partición recovery de24MiB, pero no registran el fallo posterior al reinicio. Acceso USB0.5 está copiado y verificado en el Kingston: recopila evidencia sin reiniciar para analizar el actualizador real del P291. **No hay instalación ni respaldo original del TV confirmados.** Git local iniciado; GitHub aún no publicado.

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
