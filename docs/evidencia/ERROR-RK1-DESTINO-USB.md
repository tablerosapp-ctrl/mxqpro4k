# RK3229-C: extractor ejecutado, destino USB no encontrado

El usuario probó RK1 con SD y Kingston conectados. La foto muestra verificación del paquete con `result 0`, ejecución de «TV Base - Extracción de originales 0.1» y el error **«se requiere un único pendrive marcado y montado por recovery; encontrados 0»**, seguido de Status1/Installation aborted. Ambos medios volvieron a la PC.

Esto acredita aceptación del ZIP y ejecución del extractor en ese recovery. El aviso anterior sobre `META-INF/com/android/metadata` no impidió ejecutarlo; no se identifica como causa de la detención. No prueba el hash de la partición recovery del aparato.

## Alcance del fallo

El código sellado0.1 ejecuta `recoveryContext → findUSB` antes de leer DT, plan, inventario o crear el destino. El error corresponde a `findUSB`; no empezó a copiar particiones ni a crear una captura. Recovery puede escribir sus propios registros/metadatos, aunque el extractor no instala ni formatea.

La selección0.1 exige simultáneamente montaje RW, filesystem compatible, raíz de montaje, topología USB física, directorio y marcador exactos. Cero candidatos no distingue entre USB sin montar, montaje RO, filesystem distinto u otro control incumplido. Por tanto, la explicación del usuario de que recovery no monta el pendrive es plausible, todavía no demostrada con su tabla de montajes.

## Conservación al volver a PC

- Foto183594B, SHA256 `8b5be121e1b2ced17553aeecebf0d62718fadeddcda962a0744b624250b4d12a`, conservada en privado.
- SD: `update.zip`1380273B SHA256 `0f7fe7a5f609290f69597c599ac8c72954b4fc7e04957cd27b279a368f060c38`, idéntico al RK1 entregado. Guía2125B SHA256 `e0f0ed9fe72f6d30cc9b18a01aa8968321b0b38845c7838d49ff812efab17e24`. Ambos archivados y releídos en PC.
- SD sin carpeta de capturas; Kingston conserva `CAPTURAS` vacío y plan C401B SHA256 `f5f15963b2d8d98eb81e17b45f824f541ef2b47f7d511ac0b29e12d5a7b67311`.
- Windows volvió a enumerarlos con números de disco distintos: se identificaron por identidad completa y tamaño, no por número o letra. SD FAT32/TVBASESD con8033837056B libres; Kingston FAT32/TVBASE. Windows informa Healthy para SD y Warning para Kingston; no se ejecutó reparación, formato ni borrado del Kingston, ni se atribuye ese estado a una causa específica.

Originales y recibo privado: `privado/rk3229-c-sin-usb-20260909/ADQUISICION.json`. Esta adquisición solo leyó los medios.

## Decisión siguiente

El usuario solicita evaluar el respaldo en SD. Se prepara una versión separada0.2/RK2: cargar y guardar en la misma SD externa, identificarla como tarjeta SD física, excluirla de fuentes y conservar los controles de integridad. No se cambia ni vuelve a ejecutar RK1. La eMMC declarada7818182656B más reserva134217728B cabe en el espacio informado; áreas boot y tamaño real elegido se suman nuevamente en recovery. Un mapa mayor o falta de espacio detienen la copia conservando el inventario. La extracción física sigue pendiente.
