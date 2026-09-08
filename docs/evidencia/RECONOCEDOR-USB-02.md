# Reconocedor 0.2 entregado y primera captura P271 conservada

## Resultado

Se verificó y guardó la captura P271 recibida y el recibo original, además de la foto del MX9. [Hallazgos y límites](../../diagnostico/reconocimiento-20260908-p271-mx9/HALLAZGOS.md). No había informe MX9 ni imágenes nuevas desde recovery. No se contactó ni modificó un TV en esta revisión.

Se construyó y entregó Reconocimiento TV Base 0.2: **90.515 bytes**, SHA256 `336bfab87d9d4d2983cad8f920545988cb2bbea44b6ff31edde066b5b0604b51`. Paquete y firmante iguales a 0.1; versión 2/0.2, API21+/target28, sin permisos de red, root, ADB, reinicio ni instalación. [Fuentes y contrato](../../diagnostico/reconocedor-0.2/README.md), [compilación](../../diagnostico/reconocedor-0.2/COMPILACION.json), [pruebas PC](../../diagnostico/reconocedor-0.2/PRUEBAS-PC.json).

La ficha inicial se cierra y exporta antes del inventario. Son archivos y UUID distintos; un fallo de exportación inicial detiene las consultas opcionales. El botón permite completar desde la ficha conservada sin releer DT. Se omite la copia masiva de archivos/DT, se conserva inventario acotado de bindings y se limita a un trabajador real de observación. El timeout no libera ese trabajador hasta su salida; datos tardíos nunca escriben sesiones. Las operaciones de almacenamiento aún pueden bloquear. No se acredita solución física del MX9 hasta recibir la siguiente captura.

## Entrega

Kingston fue identificado por UniqueId, modelo, capacidad, USB, condición no sistema/no boot y marcador. Un CheckOnly sin escritura seguido de **una** preparación, ambos con código0. [Preparador](../../preparacion-usb/preparar-reconocimiento-02.ps1), [recibo](../../preparacion-usb/reconocimiento-02-estado.json). No repetirlos.

Se agregaron tres archivos nuevos, 92.973 bytes, con Flush(true) y SHA por relectura:

- `TVBASE-RECONOCIMIENTO/Reconocimiento-TVBase-0.2.apk`.
- `TVBASE-RECONOCIMIENTO/LEEME-0.2.txt`.
- `TVBASE-EXTRACCION/PLANES/P271.json`, 376 bytes, SHA256 `112e438c447c64257d897a7d0947cb4cf07e2884a52b5e3960e471756c9eeac3`.

El plan privado se derivó del ZIP P271 íntegro: contiene identidad DT/vínculos de captura y operación `capture_read_only`, sin offsets ni órdenes. Sigue pendiente entrada/firma/ejecución del recovery P271. No es autorización para instalar una ROM.

Se conservaron 205 archivos anteriores comprobados por SHA y ocho grandes por metadatos, además del inventario de carpetas. El contenido de esos ocho no se rehasheó durante preparación; el ZIP P271 sí tuvo una adquisición independiente íntegra anterior. Quedaron 23.271.522.304 bytes libres. Sin formato, reparación ni borrado. No se acredita flush de volumen ni expulsión física de Windows; usar expulsión segura.

## Siguiente prueba

Actualizar la APK existente del MX9 con la 0.2, sin desinstalar ni borrar datos. Comprobar versión, capturar y esperar **INVENTARIO GUARDADO Y RELEÍDO**. Si solo queda la ficha inicial, completar desde ella; si una lectura permanece viva, no iniciar otra captura. Expulsar desde Android y devolver el USB. Los dos ZIP son intencionales y el importador conserva su relación sin confundirlos con dos equipos.

No repetir P271 por rutina ni usar AccesoUSB09/ROM P291 en él. Su informe ya aporta datos para la siguiente revisión de entrada a recovery. Las versiones 0.1, extractor0.1 y sus recibos siguen inmutables; las limitaciones históricas se documentan en evidencia nueva.
