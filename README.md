# TV Base · empezar aquí

**TV Base funciona en el primer P291: el usuario confirma WiFi y varios reinicios correctos sin pendrive. La instalación 0.2.2 y los seis respaldos están verificados. Queda pendiente el botón Home del control.** [Resultado físico y respaldos](docs/evidencia/INSTALACION-FISICA-P291-022.md) · [Reinicios informados](docs/evidencia/REINICIOS-P291-SIN-USB.md).

El objetivo es Android simplificado en memoria interna, instalado desde pendrive, con una APK común para Android TV, WebView, video local y administración propia. El primer destino probado es **P291 / gxlx2_p291_1g**; el segundo P271 es otro perfil y no recibió esta ROM.

La plataforma 0.2.0, construida desde los originales de este P291, quedó instalada mediante el instalador 0.2.2. Los registros del USB acreditan seis respaldos, la preparación de userdata y cinco imágenes escritas y verificadas por lectura, con boot al final. La foto muestra el inicio de TV Base. Se conservaron y verificaron en PC **199 archivos, con un total de 6.091.261.673 bytes**; los seis respaldos incluidos suman 6.067.060.736 bytes. La adquisición no modificó el pendrive.

**ISSUE-HOME-01:** el botón Home del control no vuelve al menú. [Incidencia y criterio de cierre](docs/INCIDENCIAS.md). La [revisión local de Home](docs/hipotesis/HOME-P291.md) plantea hipótesis; todavía no se conocen los ajustes ni la traducción de esa tecla en el TV instalado. El usuario está probando su APK. Quedan por comprobar el proveedor WebView efectivo, el rendimiento con dos videos VP9 —uno con transparencia— y canvas, el consumo, el tráfico y la estabilidad prolongada. Tampoco se ensayó la recuperación desde la nueva ROM. Los reinicios sin USB están informados; no se especificó el tipo de cada ciclo.

La base incluye Chrome/WebView 138, inicio y ajustes propios y un gestor de actualización desactivado hasta configurar el servidor. Conserva el kernel, DTB y drivers originales, además del framework y la firma de plataforma heredados; SELinux sigue en modo permisivo. El funcionamiento informado de WiFi corresponde a este ejemplar: no certifica todos los equipos ni identifica la causa exacta de su recuperación.

**Próximo entregable propuesto:** USB de reconocimiento sobre Android, con informes comparables y acceso explícito por niveles para Amlogic y futuros Rockchip. Después se califica P291, se completa P271 y se adaptan nuevas placas. La capa de producto común incluye logo, controles y contratos de capacidades; USB e Internet compartirán catálogo firmado, con instalación rápida por perfil y actualización por componente. [Plan actualizado, PROP-17](docs/PLAN-RECONOCIMIENTO-Y-PRODUCTO.md) · [Política de lotes y respaldos, PROP-16](docs/PROPUESTA-LOTES-Y-ACTUALIZACIONES.md). No hay arranque USB universal ni actualización remota de ROM probada. Implementación y pruebas físicas esperan el OK solicitado por el usuario; el contrato actual de seis respaldos se conserva.

- [Respaldo cifrado publicado en GitHub](docs/RESPALDO-GITHUB.md): originales, datos previos y paquetes 0.2.2, con clave privada separada.
- [Estado](docs/ESTADO.md), [especificación](docs/ESPECIFICACION.md), [roadmap](docs/ROADMAP.md) y [decisiones](docs/DECISIONES.md).
- [Grafo navegable](docs/index.html), [mapa](docs/MAPA-ARCHIVOS.md), [árbol](docs/ARBOL-ARCHIVOS.txt) y [contrato del grafo](docs/proyecto.json).
- [Guía de instalación y estado](rom-simplificada/INSTALACION-USB.md), [entrega para Claude/Fable](docs/ENTREGA-FABLE.md) y [repositorio público](https://github.com/tablerosapp-ctrl/mxqpro4k).
- [Desarrollo](docs/DESARROLLO.md), [Git](docs/GIT.md) y [publicación saneada](docs/PUBLICACION.md).

Para retomar: AGENTS → ESTADO → ESPECIFICACION → MAPA → ROADMAP. Los recibos de construcción/entrega anteriores conservan sus estados históricos; la prueba física tiene evidencia nueva. No sobrescribir releases, originales o respaldos. Claves, imágenes y registros privados permanecen locales.
