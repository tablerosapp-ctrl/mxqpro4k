# TV Base · empezar aquí

Android simplificado instalado en la memoria interna de TV boxes, con una APK común para Android TV, WebView, video local y administración propia. El primer destino es **P291 / `gxlx2_p291_1g`**. El segundo equipo P271 es únicamente una referencia de diagnóstico.

**Estado al7/9/2026:** [ROM0.1.2 sin Bluetooth](rom-simplificada/SIN-BLUETOOTH-0.1.2.md) construida, firmada y copiada/leída enKingston. ConservaWiFi/Chrome138; WiFi recuperado, recovery, respaldo e instalación **todavía no confirmados**. [ReciboUSB](preparacion-usb/rom-012-estado.json).

La conexiónLAN del primerP291 obtuvo un panic en la coordinaciónBluetooth→WiFi y trazasANR precisas. Se apagóBluetooth y se inhabilitó su aplicación en Androidactual; tras un apagado físico el ajuste persiste, pero el firmware todavía carga los módulos y hay esperas delkernel. La nuevaROM suprime esa cargaBluetooth; falta entrar al instalador. El switch interno ya fue probado sin resultado por el usuario; se prepara observación del cierre OEM con la nueva condiciónBluetooth. [HallazgosLAN](diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md) · [Estado y próximo paso](docs/ESTADO.md). No repetirUpdate ni declarar el cierre reparado. La captura0.8 previa queda [documentada como parcial](diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md).

El [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k) conserva el hilo saneado de colaboración conFable. Los binarios y registros privados permanecen locales.

- [Empezar desde Claude Desktop / Fable 5.1](docs/ENTREGA-FABLE.md): contexto y revisión independiente H2.
- [Colaboración y dos hipótesis](docs/COLABORACION.md): responsabilidades, evidencia y formato de retorno.
- [Primera revisión H1 de Codex](docs/hipotesis/H1-RESULTADO-CODEX.md): distingue cierre Java y kernel; pendrive leído, sin evidencia nueva del último intento.
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
