# Extractor 0.2 · paquete RK2 con destino SD

Receta nueva para compilar el extractor ARM32 0.2 y firmarlo con la confianza v3/RSA-SHA256 de CNV8b. Se ejecuta completamente en PC; no accede al TV ni a medios externos. Las fuentes y paquetes 0.1/RK1 permanecen intactos. El código del extractor está en [extractor-recovery-0.2](../extractor-recovery-0.2/README.md).

La prueba física RK1 llegó a ejecutar `update-binary` y abortó porque encontró cero destinos USB que cumplieran sus condiciones. Esto acredita aceptación y ejecución de aquel paquete, pero no demuestra que el pendrive estuviera completamente ausente del recovery. RK2 cambia el ejecutable para usar la SD desde la que se carga el ZIP, con marcador propio, montaje de escritura y prueba física de tarjeta SD separada de las fuentes MMC internas. La aceptación y copia física con RK2 deben verificarse por separado.

La receta reutiliza por ruta y SHA los archivos inmutables `firma_ota_v3.py` y `VerifyWholeZip.java` de RK1. Compila y ejecuta pruebas de lógica en Windows; compila las pruebas Linux/ARM32 sin ejecutarlas. Valida ELF ARM32/EABI5 estático, parámetros de Go, firma integral con Python y OpenJDK, CRC, nombres, contenido y permisos del ZIP. Los casos negativos comprueban certificado ajeno, corrupción del contenido y corrupción del footer. No se incluye ninguna imagen de partición ni clave privada.

```text
python -B diagnostico/extractor-recovery-rk2/compilar.py --build-dir privado/extractor-rk2-build-NUEVO --output-dir privado/extractor-rk2-release-NUEVO
```

Ambos directorios deben ser nuevos y separados, bajo `privado`. La receta conserva todo intento fallido. Los insumos privados y herramientas locales figuran por ruta y hash en el recibo de compilación. El único entregable es `TVBASE-EXTRACTOR-0.2-RK2-ARM32-RECOVERY.zip`; los archivos unsigned y negativos se conservan en el directorio privado de compilación y nunca deben entregarse.

La [compilación verificada](COMPILACION.json) produjo un ZIP de **1.387.097 bytes**, SHA256 `3d9e6a18c023ccc4a355aab738537655049016634dcf855990b307aa619486cd`. El ejecutable tiene 3.342.496 bytes y SHA256 `b750e354db6eb1053b4edda7abf35f91a147e1ad0108fb55a004c4f2ea36a7b0`. Pasaron 25 pruebas principales de Go (104 eventos de aprobación incluidos los subcasos), cuatro rechazos negativos de firma en Python y dos rechazos en OpenJDK. Las pruebas Linux ARM32 compilaron, pero no se ejecutaron en Linux ni en el TV. Este recibo no acredita preparación de SD ni captura física.

Se conserva el formato de cuatro entradas del paquete previo. No se añade `META-INF/com/android/metadata`: el aviso de ausencia observado fue anterior a la ejecución real del extractor y no causó el rechazo del destino. No se inventa un tipo OTA de ROM ni sus precondiciones para ocultar un aviso informativo.

La clave pública de desarrollo Rockchip es una medida de compatibilidad de laboratorio; no es la confianza que usaremos en las actualizaciones de producción. El extractor no instala, monta, formatea ni reinicia. Puede omitir regiones ocupadas o inaccesibles y no implementa restauración ni una instantánea atómica. El recovery anfitrión puede escribir sus propios registros y metadatos.
