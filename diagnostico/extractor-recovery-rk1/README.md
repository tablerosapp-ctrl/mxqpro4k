# Extractor 0.1 · paquete RK1 para recovery CNV8b

Variante de firma y empaquetado del extractor ARM32 0.1 existente. El ejecutable permanece idéntico: SHA256 `05221a82892e3aa6958d128d497c81645f8fdeae5cd494f320385f1e6d060e48`. No contiene imágenes para flashear. Conserva el [contrato y límites del extractor](../extractor-recovery-0.1/README.md).

La foto del último RK3229-C coincide en fingerprint con el recovery extraído de la imagen que aportó el usuario. Su clave v3 requiere RSA/SHA256 y un certificado de desarrollo Rockchip distinto del P291. [Evidencia y revisión del ejecutable de recovery](../../docs/evidencia/RECOVERY-CNV8B-SD.md). No se leyó todavía el hash de la partición recovery del TV: esta correspondencia no acredita aceptación física.

`empaquetar.py` comprueba el ZIP original sellado, conserva su ejecutable y updater-script, modifica los metadatos descriptivos y certificado y firma el ZIP completo. `firma_ota_v3.py` deriva del helper v1 de la entrega022, en archivo separado; cambia clave anclada, parser v3, digest/OID SHA256 y texto identificador. No modifica las fuentes ni recibos anteriores. `VerifyWholeZip.java` comprueba PKCS7 con OpenJDK y exige el certificado esperado y SHA256. Los casos negativos cubren certificado P291, paquete SHA1 anterior, contenido alterado y footer alterado.

Construcción local, sin contacto con medios ni TV:

```text
python -B diagnostico/extractor-recovery-rk1/empaquetar.py --output privado/extractor-rk1-NUEVO
```

Requiere los insumos privados ya adquiridos y las herramientas locales descritas en la receta. El directorio de salida debe ser nuevo. Conservar todo intento y no entregar los ZIP negativos ni unsigned.zip. [Recibo de construcción](COMPILACION.json).

El único ZIP para el usuario es `TVBASE-EXTRACTOR-0.1-RK1-ARM32-RECOVERY.zip`, 1.380.273 bytes, SHA256 `0f7fe7a5f609290f69597c599ac8c72954b4fc7e04957cd27b279a368f060c38`. Se copia idéntico como `update.zip` en la SD porque el ejecutable CNV8b usa esa ruta fija. Esta excepción está sustentada en el ejecutable aportado; no es una regla general de todos los recovery.

La SD es el medio de carga; el Kingston marcado es el destino de las capturas y debe estar conectado antes de entrar al recovery. No añadir `update.zip` ni `update.img` al Kingston: ese recovery también busca actualizaciones automáticas en USB. El plan activo corresponde solamente a RK3229-C; volver a PC antes de pasar a A/B.

La clave de desarrollo publicada por Rockchip permite compatibilidad de laboratorio; no es una raíz de confianza para nuestras actualizaciones de producción. No hay instalación, copia física ni restauración RK certificadas. El recovery anfitrión puede escribir sus propios metadatos y registros; las fuentes internas del extractor se abren solo para lectura.
