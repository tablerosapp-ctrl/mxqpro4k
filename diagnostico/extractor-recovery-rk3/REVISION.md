# Revisión independiente · extractor 0.3 / RK3

**Resultado: verificado en PC, sin hallazgos bloqueantes.** Se revisaron el núcleo Go, la integración Linux, la receta de construcción, los lectores de captura completa/parcial y el preparador de SD. Esta revisión no ejecutó el TV ni escribió en SD o Kingston. El [recibo íntegro](REVISION.json) fija los hashes revisados y el alcance.

El ZIP final contiene un ELF ARM32 estático, metadatos del extractor, el guion y el certificado público. Su tamaño es **1.463.158 B** y SHA256 `ff9595f7a64a64df77f1c1d4904a896922e62a6be51d6a9e94247e79da985d01`. La firma integral se comprobó con un parser DER independiente y exponenciación RSA directa usando únicamente el certificado y `res/keys` públicos; los cinco casos de alteración de datos, footer, firma, EOCD y clave distinta fueron rechazados. CRC, miembros, permisos y hashes también coincidieron con [COMPILACION.json](COMPILACION.json).

La variable de identidad no se dio por enlazada a partir del registro del compilador: se localizó `main.rk3229CExpectedCID` en la tabla de símbolos ELF, se resolvió su puntero y longitud y se compararon los 64 bytes reales con el inventario privado sellado. Ese valor no está en esta documentación, las fuentes o los metadatos públicos. El primer intento de construcción, rechazado antes de firmar por una comprobación de buildinfo incompatible con `-trimpath`, quedó preservado por separado.

## Cambio revisado

La política exige la unidad y el mapa de quince particiones de **recovery** ya observados. Ordena las fuentes elegibles por su comienzo físico y deja `backup` al final; impide elegir toda la eMMC. Las guardas de montajes, holders, separación con SD e identidad permanecen. Un replay independiente del JSON real eligió catorce fuentes y **7.679.770.624 B**, dejó cache RW fuera y rechazó un CID distinto o el comienzo de system alterado.

Para los 64 MiB exactos de backup, la nueva rama comprueba un presupuesto de memoria de 128 MiB, lee el origen a RAM y lo vuelve a abrir y leer inmediatamente. Solo si ambos SHA coinciden crea la parte en SD, la sincroniza y la relee para exigir el mismo SHA. Un error sigue deteniendo la captura y preserva las fuentes anteriores verificadas. Las otras fuentes conservan el cuerpo de `captureOne` y sus tres comprobaciones. El uso de acceso normal del kernel está documentado: **no se prueba acceso físico sin caché ni una instantánea atómica**.

El lector parcial conserva el estado global de fallo y solo suma fuentes cuyos datos, estados de parte y SHA de origen/destino coinciden. La copia fallida de backup no se transforma en un original estable. El preparador identifica ambos medios, fija el recibo de adquisición, exige los nueve archivos anteriores y respalda/verifica los dos que sustituye. Los otros siete quedan preservados; no formatea ni escribe bloques del TV.

## Comprobaciones y límites

- La construcción ejecutó **38 tests Go principales / 187 eventos aprobados** en Windows, incluidos orden RAM, presupuesto, errores de origen/destino y preservación de una fuente anterior tras un mismatch simulado de 64 MiB. Las pruebas Linux/ARM32 fueron compiladas, sin ejecución física.
- Los lectores registran **38 métodos: 37 aprobados y uno omitido**, porque la cuenta Windows no pudo crear enlaces simbólicos reales. El resultado sobre RK2 mantiene 4 MiB de parameter verificados y 64 MiB de backup fallidos, sin aceptar estos últimos como originales estables.
- La revisión repitió independientemente la firma/ELF/ZIP y el replay del inventario real. No duplicó los conjuntos de tests ya ejecutados; comprobó sus fuentes, recibos y hashes. El preparador pasó además análisis sintáctico sin ejecutarse.

La discrepancia anterior no identifica al escritor ni acredita SD/eMMC defectuosas o malware. La variante RAM reduce el intervalo entre lecturas y evita escribir backup a SD entre ellas; es una prueba distinta cuya aceptación y extracción en el TV siguen pendientes. Recovery puede escribir sus propios registros. La memoria disponible es una estimación y una interrupción del host puede impedir cerrar un informe. No se certifica copia completa, restauración, ausencia de malware, expulsión física ni seguridad de actualizaciones de producción.
