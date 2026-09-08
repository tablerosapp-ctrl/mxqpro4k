# TV Base · empezar aquí

Android simplificado en memoria interna, instalado desde pendrive, con una APK común para Android TV, WebView, video local y administración propia. Primer destino: **P291 / gxlx2_p291_1g**. El segundo P271 es solo referencia de diagnóstico.

**Corrección 0.2.2 copiada y releída en Kingston; TV en recovery. Instalación física pendiente.** El ZIP0.2.1 llegó a ejecutar nuestro instalador, pero una comprobación rechazó el nombre Amlogic `system`. Ese intento se detuvo antes del respaldo, formato o grabación de Android. [Error y alcance](docs/evidencia/ERROR-INSTALADOR-P291-021.md).

La entrega0.2.2 corrige la identificación de particiones en instalación y restauración, conservando las cinco imágenes de plataforma0.2.0. Los dos ZIP y la guía están verificados en el pendrive. Se archivaron los archivos021 antes de retirarlos; informes y respaldos se conservan. [Cambio, pruebas y entrega](docs/evidencia/INSTALADOR-P291-022.md) · [ReciboUSB](preparacion-usb/original-022-estado.json).

El próximo paso es conectar el Kingston al TV todavía en recovery y elegir **TVBASE-P291-A9-0.2.2-RECOVERY.zip** mediante Apply update from EXT → Update from udisk. No repetir AccesoUSB0.9 ni Update del Android anterior. La [preparación ENV/BCB](docs/evidencia/PREPARACION-ENTRADA-P291-09.md) ya se ejecutó y verificó; el usuario vio recovery y la ejecución del ZIP. [Guía operativa](rom-simplificada/INSTALACION-USB.md).

La instalación respalda seis particiones, incluidos los datos, antes de borrarlos y escribir las cinco imágenes, con boot al final. Requiere6.603.931.648B libres. Los doce respaldos originales enPC cubren2538MiB, sin userdata/cache/todaeMMC; el respaldo adicional de datos todavía no existe. El restaurador devuelve cinco imágenes OEM, sin recuperar los datos borrados. No hay rollback ni reentrada desde Android nuevo demostrados.

La plataforma conserva kernel, DTB y drivers originales; incluye Chrome/WebView138, inicio/ajustes y gestor propio desactivado hasta configurar el servidor. Retira51APK, mantiene34originales y agrega5. Sin Play ni Bluetooth; WiFi no está reparado ni el rendimiento mejorado demostrado. Conserva framework/SELinux permisivo/firma de plataforma heredados. Proveedor WebView efectivo y dosVP9 —uno con alfa— más canvas siguen pendientes de prueba física.

- [Estado](docs/ESTADO.md), [especificación](docs/ESPECIFICACION.md), [roadmap](docs/ROADMAP.md) y [decisiones](docs/DECISIONES.md).
- [Grafo navegable](docs/index.html), [mapa](docs/MAPA-ARCHIVOS.md), [árbol](docs/ARBOL-ARCHIVOS.txt) y [contrato del grafo](docs/proyecto.json).
- [Entrega para Claude/Fable](docs/ENTREGA-FABLE.md), [colaboración](docs/COLABORACION.md) y [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k).
- [Desarrollo](docs/DESARROLLO.md), [Git](docs/GIT.md) y [publicación saneada](docs/PUBLICACION.md).

Para retomar: AGENTS → ESTADO → ESPECIFICACION → MAPA → ROADMAP. Distinguir pruebasPC de resultados físicos. Claves, imágenes, herramientas y registros privados permanecen locales. No sobrescribir releases, originales o recibos; no repetir formato ni limpieza por rutina.
