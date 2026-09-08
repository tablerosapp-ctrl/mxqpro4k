# TV Base · empezar aquí

Android simplificado en memoria interna, instalado desde pendrive, con una APK común para Android TV, WebView, video local y administración propia. El primer destino es **P291 / `gxlx2_p291_1g`**; el segundo P271 es solo referencia de diagnóstico.

**Estado al 7/9/2026 ART:** la plataforma0.2.0 desde los originales del P291 permanece inmutable. El nuevo **instalador0.2.1** conserva esas cinco imágenes y prepara los datos: respalda seis particiones completas antes de crear userdata limpia y escribir Android. La **APK Acceso USB0.9** está compilada/revisada e instalada por LAN; se solicitó abrirla, pero una captura posterior confirma que el diálogo Android2% sigue superpuesto y la APK no es visible. El restaurador0.2.1 separado también está sellado/verificado; repone cinco particiones y **no recupera userdata**. [Evidencia vigente](docs/evidencia/ENTRADA-ORIGINAL-P291-021.md) · [Estado operativo](docs/ESTADO.md).

**La ROM no está instalada. La entrega0.2.1 quedó copiada y releída en el Kingston a23:06ART, código0.** Los dos ZIP, AccesoUSB0.9 y la guía coinciden con sus hashes; [recibo](preparacion-usb/original-021-estado.json). Falta expulsar de forma segura desde Windows y mover el USB al TV: no se acredita todavía el vaciado final de metadatos del volumen. El primer TV seguía al2% y accesible por LAN. No repetir Update. La nueva entrada modifica64KiB de ENV y2KiB de BCB para preparar el menú del recovery interno; requiere la decisión específica del usuario después de conocer este riesgo. **Todavía no se aprobó ni ejecutó ese método.** No se modificaron ENV/BCB ni se pidió otro reinicio durante la revisión.

Se probó el formateador original sobre un archivo temporal del TV y se comprobó en lectura la consulta de tamaño ARM32. Estas pruebas resolvieron opciones y un error de ABI; no acreditan formato de particiones, entrada a recovery ni instalación. [Contrato de migración](rom-simplificada/original-p291/instalacion-021/CONTRATO-MIGRACION.md).

La plataforma contiene Chrome/WebView138, inicio/ajustes,34 APK originales conservadas,51 retiradas y cinco agregadas. El gestor propio está desactivado hasta configurar el servidor del dueño. Conserva kernel, multi-DTB y controladores originales; sigue siendo una derivación de Android9 con framework y límites heredados, incluidos SELinux permisivo y firma de plataforma. WiFi, proveedor WebView efectivo, dos VP9/alfa/canvas y restauración física siguen pendientes.

Hay doce particiones originales verificadas en PC (2538MiB), sin userdata/cache ni toda la eMMC. La instalación0.2.1 creará el respaldo adicional de datos si llega a ejecutarse; ese respaldo todavía no existe. La ROM nueva retira su y ADB TCP predeterminado: no está demostrada la reentrada desde Android nuevo ni una siguiente actualización completa por APK.

El [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k) conserva el hilo saneado de colaboración con Fable. Binarios, claves y registros privados permanecen locales; una publicación no acredita una prueba física.

- [Estado y siguiente paso](docs/ESTADO.md), [pasos con el pendrive](rom-simplificada/INSTALACION-USB.md) y [operación acompañada por LAN](rom-simplificada/original-p291/entrada-apk/OPERACION-LAN-09.md), todavía sin ejecutar.
- [Especificación y aceptación](docs/ESPECIFICACION.md), [roadmap](docs/ROADMAP.md) y [decisiones](docs/DECISIONES.md).
- [Grafo navegable sin internet](docs/index.html), [mapa de archivos](docs/MAPA-ARCHIVOS.md) y [árbol generado](docs/ARBOL-ARCHIVOS.txt).
- [Entrega para Claude Desktop / Fable5.1](docs/ENTREGA-FABLE.md), [colaboración](docs/COLABORACION.md) y [publicación saneada](docs/PUBLICACION.md).
- [Reproducir y mantener](docs/DESARROLLO.md), [Git local](docs/GIT.md) y [arquitectura del producto](ARQUITECTURA-ANDROID-TV.md).

Para retomar: **AGENTS → ESTADO → ESPECIFICACION → MAPA → ROADMAP**. [proyecto.json](docs/proyecto.json) enlaza componentes, requisitos y pruebas. Los recibos acreditan operaciones ejecutadas; propuestas, compilaciones y hashes no acreditan instalación. El dossier HTML y los documentos históricos son antecedentes fechados.

La [limpieza anterior](docs/LIMPIEZA.md) retiró6.615.135.611bytes de temporales regenerables. La entrega0.2.1 archivó y verificó en PC cuatro archivos viejos antes de retirarlos del USB (598.275.472bytes); no hubo formato ni reparación. Informes, originales, claves locales, releases y respaldos se conservan.
