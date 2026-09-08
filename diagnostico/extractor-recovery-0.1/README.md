# Extracción combinada: APK y recovery · 0.1

El usuario pidió ampliar la identificación para conservar originales y reutilizar los drivers de varios TV. La APK existente describe Android en funcionamiento; este programa independiente obtiene imágenes desde un recovery compatible. **No contiene instalación, formato, restauración, comandos de entrada, montaje/desmontaje ni reinicio.** No se reutiliza el ZIP instalador P291, que continúa a formato y flash después de respaldar.

**Entrega PC y USB comprobada:** [recibo de construcción](COMPILACION.json) y [evidencia/recibo Kingston](../../docs/evidencia/EXTRACTOR-RECOVERY-01.md). Falta la primera captura física y el plan real de cada equipo.

## Flujo

1. Ejecutar [Reconocimiento0.1](../reconocedor-0.1/README.md) sobre Android y guardar su ZIP verificado en el Kingston.
2. En PC importar/verificar el ZIP y ejecutar `preparar-plan.py --apk-report <ZIP> --output <archivo-nuevo-en-privado>`. Produce únicamente un plan de lectura: referencia al SHA/UUID de captura, nombre/perfil y DT observado. No acepta comandos, offsets, imágenes a escribir o campos desconocidos. La copia de ese plan a `TVBASE-EXTRACCION/PLANES` se prepara después de recibir la captura real.
3. Revisar la ruta de entrada y la firma aceptada por el recovery de ese perfil. [P271: hechos y límites](../../docs/evidencia/RECOVERY-P271-ALCANCE.md). Entrar al recovery no garantiza que acepte nuestro ZIP; el ejecutable también debe ser compatible con su kernel/arquitectura. No ejecutar Update de una ROM para obtener un respaldo.
4. Seleccionar el ZIP extractor apropiado desde recovery. El programa exige UID0, proceso recovery activo, ausencia de zygote/system_server y un USB físico marcado ya montado RW. No monta el pendrive por su cuenta. Con un plan cuya identidad DT coincida exactamente, descubre de nuevo tamaños/rutas/mapa y copia las fuentes estables. Sin plan coincidente, guarda **solo inventario**, indicado en pantalla y en `resultado.json`.
5. Conservar el resultado y llevar USB a PC para verificar/archivar las imágenes. El lector `verificar-captura.py --capture <carpeta>` comprueba el cierre, manifiesto, tamaños y SHA de partes y fuentes sin abrir los dispositivos del JSON ni interpretar userdata. Ante error no repetir automáticamente: conservar archivos y mensaje. Cada ejecución usa una carpeta nueva aleatoria; nunca sobrescribe otra captura.

La APK asigna UUID de instalación, no un identificador físico acreditado. Coincidir por DT vincula un **perfil declarado**, no demuestra por sí solo que sea el mismo ejemplar. Recovery registra hashes de los CID eMMC accesibles y su propio identificador de captura. Dos planes que coincidan con el mismo DT causan parada: se debe elegir en PC el plan del equipo conectado. Nunca publicar los planes ni imágenes en claro.

## Qué copia esta versión

Adaptador de **eMMC interna MMC no removible**, ARM32 (GOARM5) y ARM64. Lee sysfs, rdev, tamaño por ioctl, inicios y relaciones de particiones. Acepta nombres lógicos como `system` del P291 y nombres estándar; no fija offsets ni capacidades del P291.

- Prefiere el área de usuario eMMC completa cuando no tiene consumidores que puedan modificarla y todas sus particiones están desmontadas o con montaje y superblock RO. La imagen incluye huecos y tabla de particiones expuestos por esa área.
- Si una partición está montada RW, omite el área completa y copia las particiones hermanas estables. Si el padre completo está en uso, tampoco copia sus hijas. Dispositivos con holders, incluidos mappers activos, y swap se consideran ocupados.
- Copia áreas boot0/boot1 expuestas y estables por separado; no cambia `force_ro`. Rechaza copiar una de esas áreas si presenta particiones hijas no evaluadas.
- RPMB, MTD/NAND, UFS, controladores de almacenamiento no reconocidos y fuentes inaccesibles no se presentan como respaldados. NAND requiere otro adaptador que trate su geometría/ECC/OOB; no basta tratarlo como eMMC.
- No desmonta `/cache` ni otros volúmenes del recovery. Un resultado puede ser parcial de forma deliberada. La lectura fallida de un bloque necesario para validar el inventario detiene el proceso.

**No se promete una copia de toda la memoria del aparato.** `all_device_storage_copied` permanece falso: incluso una eMMC principal completa más boot0/1 no incluye RPMB u otros chips. Los datos personales pueden estar incluidos en las áreas copiadas, incluso cifrados; se conservan como binarios privados sin montarlos ni reutilizarlos en otra unidad. La copia refleja ese momento: en el P291 ya modificado contendrá TV Base, no volverá a obtener el OEM original conservado previamente.

## Integridad y almacenamiento

Partes de hasta 1 GiB, aptas para FAT32, sin compresión ni grandes buffers. Antes de copiar exige espacio para todas las fuentes elegidas más 128 MiB. No elimina respaldos para hacer lugar. Los aproximadamente 23 GB libres actuales no permiten acumular un número ilimitado de TV: depende de la memoria ocupada por cada extracción.

Cada fuente se abre exclusivamente en lectura. Se compara SHA durante copia, relectura de las partes y nueva lectura completa del origen; se revalida topología, CID accesible, montajes y destino entre fases. Una lectura doble idéntica detecta cambios observados, no constituye un snapshot atómico contra cualquier escritor oculto.

Los archivos conservan extensión `.img.partial` incluso cuando sus bytes están verificados: se evita depender de un renombrado que pudiera sobrescribir en FAT32 o fallar en kernels viejos. **El manifiesto determina su estado.** `report.json` describe fuentes/partes; `failed-report.json`, si existe, prevalece. `resultado.json` contiene el hash del manifiesto y alcance, y solo se crea al concluir. La comprobación PC deberá cotejar partes, manifiesto y resultado; un texto en pantalla aislado no sustituye esos archivos.

El destino se fija con descriptores de directorio USB; `mkdirat/openat` crean exclusivamente archivos ordinarios nuevos, sin seguir enlaces ni caer sobre almacenamiento interno si desaparece el montaje. Se exige fsync de archivos y directorios, además de relectura. El extractor no escribe bloques del TV; **el recovery anfitrión puede escribir sus propios registros/metadatos**. No se promete cero escrituras de todo el entorno.

Las lecturas de dispositivos y sysfs tienen límites de tamaño y número. Una llamada bloqueada en el kernel puede seguir detenida; no hay un plazo duro universal ni se fuerza reinicio. El progreso muestra fase y bytes reales, no un porcentaje simulado.

## Construcción y estado

[Empaquetado](README-EMPAQUETADO.md) produce dos ZIP independientes, sin payload de ROM; reutiliza el firmador v1 del P291 sin modificarlo. La clave de prueba/SHA1 conservan compatibilidad experimental, no son seguridad de producción ni prueban aceptación P271/Rockchip. Los dos ZIP requieren una elección de arquitectura; no despachan otra imagen al fallar.

Fuentes: `capture.go` motor independiente del sistema; `selection.go` selección y montajes; `platform_linux.go` lecturas y salida USB; `main_linux.go` protocolo recovery y asociación al plan; `preparar-plan.py` vinculación con APK validada. Pruebas PC con archivos simulados y compilación cruzada no acreditan ejecución real en un recovery. La primera captura APK, el plan real, aceptación del ZIP y respaldo físico de cada nuevo perfil siguen pendientes.
