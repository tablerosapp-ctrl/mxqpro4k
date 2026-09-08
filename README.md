# TV Base · empezar aquí

Android simplificado instalado en la memoria interna de TV boxes, con una APK común para Android TV, WebView, video local y administración propia. El primer destino es **P291 / `gxlx2_p291_1g`**. El segundo equipo P271 es únicamente una referencia de diagnóstico.

**Estado al 7/9/2026 ART:** [ROM 0.2.0 desde los originales del primer P291](rom-simplificada/original-p291/README.md) construida y verificada en PC, con un paquete separado de restauración original. Incluye Chrome/WebView 138, inicio y ajustes, 34 paquetes originales conservados, 51 retirados y cuatro componentes propios. El gestor de APK/navegador está integrado y desactivado hasta configurar el servidor del dueño.

**No está instalada ni copiada al pendrive.** Falta resolver la entrada efectiva a recovery y preparar userdata limpia antes de la prueba. No repetir Update con 0.1.2 ni interpretar el ZIP nuevo como una solución automática al cierre bloqueado. [Resultados, archivos y límites](docs/evidencia/ROM-ORIGINAL-P291-020.md) · [Estado operativo](docs/ESTADO.md).

Se conservan kernel, multi-DTB y controladores de los originales reales, además de parte del framework. Es una derivación depurada de Android 9, no una reconstrucción AOSP ni una certificación de ausencia de tráfico OEM. SELinux permisivo y firma de plataforma heredada son límites del experimento. WiFi, proveedor WebView efectivo, video y restauración física siguen pendientes.

Los respaldos verifican doce particiones seleccionadas (2538 MiB), sin userdata/cache ni toda la eMMC. La espera del intento anterior está localizada en el cierre de Android por WiFi/HAL. Su ZIP se preservó fuera de la ruta activa, pero BCB y el hilo Java no quedaron cancelados. [Diagnóstico original](diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md).

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
