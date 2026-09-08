# Restaurador P291 0.2.2

Variante separada con las cinco imágenes OEM originales y la misma corrección de identificación de particiones que el [instalador0.2.2](../instalacion-022/README.md). Los archivos compartidos `block_layout.go`, `block_device_linux.go` y `block_layout_test.go` deben coincidir byte por byte.

ZIP sellado y verificado:913294443bytes, SHA256 `914c683a1e15f4d5e6fa622c7b390184444d9071636e580b5818bf4794f47d09`. [Recibo de firma/payload/validador](salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.2-VERIFICACION.json), [pruebas](EVIDENCIA-TESTS.json) y [revisión independiente](REVISION-LAYOUT-022.json). No se ha ensayado una restauración física.

Antes de escribir, respalda y verifica las cinco particiones actuales. Comprueba ENV normal y el layout canónico de la eMMC, conservando y revalidando los desplazamientos observados. Reconoce transacciones incompletas del restaurador0.2.1 y0.2.2. No abre, formatea ni restaura userdata; no repone su copia cruda. No reinicia automáticamente.

El empaquetador exige revisión independiente exacta de todas las fuentes Go y del builder. Firmas, hashes y pruebasPC no acreditan una restauración física. Los paquetes0.2.1 permanecen intactos como antecedente; no deben usarse para sortear una guarda que falle en esta versión.
