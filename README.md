# TV Base · empezar aquí

Android simplificado instalado en la memoria interna de TV boxes, con una APK común para Android TV, WebView, video local y administración propia. El primer destino es **P291 / `gxlx2_p291_1g`**. El segundo equipo P271 es únicamente una referencia de diagnóstico.

**Estado al 7/9/2026:** [root confirmado mediante el acceso incorporado](diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md). La [ROM 0.1.2 sin Bluetooth](rom-simplificada/SIN-BLUETOOTH-0.1.2.md) está en Kingston y su copia interna fue verificada. **No está instalada.** El respaldo de doce particiones seleccionadas está verificado; no incluye datos/cache ni toda la eMMC y no hay restauración probada.

El intento volvió al 2%. Una traza Java identifica la cadena de espera: cierre de Android → estadísticas de consumo → servicio WiFi → arranque del HAL. El mapa requerido por recovery todavía no existe. Se preservan originales antes de proponer una intervención forzada, que el usuario quiere decidir tras conocer sus riesgos. [Análisis actual](diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md) · [Estado](docs/ESTADO.md).

La [comparación con los originales](diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md) detectó diferencias de configuración de arranque y una compatibilidad de firma pendiente. **No forzar 0.1.2 tal como está.** La propuesta es derivar la siguiente ROM de los originales de este P291, conservando su kernel/DTB/video y aplicando la simplificación y las mejoras. [Opciones y riesgos](diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md).

El [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k) conserva el hilo saneado de colaboración con Fable. Los binarios y registros privados permanecen locales.

- [Empezar desde Claude Desktop / Fable 5.1](docs/ENTREGA-FABLE.md): contexto y revisión independiente H2.
- [Colaboración y dos hipótesis](docs/COLABORACION.md): responsabilidades, evidencia y formato de retorno.
- [Primera revisión H1 de Codex](docs/hipotesis/H1-RESULTADO-CODEX.md): antecedente que distingue cierre Java y kernel, anterior a la traza obtenida con root.
- [Publicación y uso del clon](docs/PUBLICACION.md): historial saneado y dependencias que permanecen locales.

- [Mapa visual del proyecto](docs/index.html): grafo navegable de componentes, archivos y roadmap; funciona sin internet.
- [Estado y siguiente paso](docs/ESTADO.md): qué se sabe, qué falta y qué hacer según el resultado del TV.
- [Pasos vigentes con el pendrive](rom-simplificada/INSTALACION-USB.md): instrucciones vigentes para la prueba.
- [Especificación y aceptación](docs/ESPECIFICACION.md): requisitos identificados y pruebas necesarias.
- [Mapa de archivos](docs/MAPA-ARCHIVOS.md) y [árbol generado](docs/ARBOL-ARCHIVOS.txt).
- [Roadmap y propuestas](docs/ROADMAP.md): orden de trabajo y condiciones para avanzar.
- [Decisiones y lecciones](docs/DECISIONES.md): por qué se eligió cada camino.
- [Historial Git local y publicación](docs/GIT.md).
- [Reproducir y mantener](docs/DESARROLLO.md): entradas, herramientas, verificaciones y documentación.
- [Arquitectura del producto](ARQUITECTURA-ANDROID-TV.md): fundamentos de Android, WebView, almacenamiento y video.

Para retomar en otra sesión: leer **AGENTS → ESTADO → ESPECIFICACION → MAPA → ROADMAP**. Después abrir solo los archivos del componente afectado. [proyecto.json](docs/proyecto.json) conecta los identificadores y las evidencias para consulta automática. Los recibos de cada operación son la prueba de lo ejecutado; los objetivos y propuestas no acreditan funciones terminadas.

La [limpieza documentada](docs/LIMPIEZA.md) retiró 6.615.135.611 bytes de temporales y extracciones regenerables. Las fuentes, claves locales, ROM firmadas, respaldos y registros se conservan. El dossier HTML y los documentos archivados son antecedentes fechados, no instrucciones de instalación vigentes.
