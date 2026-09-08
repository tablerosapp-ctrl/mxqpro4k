# Respaldo cifrado del primer P291 en GitHub

## Alcance y estado

El usuario pidió conservar el respaldo en el repositorio público. Se prepara una copia **cifrada**, con la clave privada guardada por separado en la PC. Esta autorización amplía la conservación y publicación del respaldo; los cambios en Home, la ROM, otros equipos y el servidor siguen esperando su OK.

La publicación se realiza como archivos de una Release, fuera del historial Git. GitHub permite distribuir archivos grandes mediante [Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases); se usan partes de 512 MiB para que cada archivo quede debajo de su límite. Los originales permanecen intactos.

**Publicado y verificado:** [Descargar el respaldo cifrado](https://github.com/tablerosapp-ctrl/mxqpro4k/releases/tag/respaldo-p291-20260908). Nueve partes, 4.504.905.988 bytes cifrados, y un manifiesto público. Se verificaron 465 archivos al descifrar en PC; GitHub confirmó tamaños y hashes de los diez assets y su acceso público anónimo. [Recibo de publicación](evidencia/RESPALDO-GITHUB-PUBLICADO.json) · [Manifiesto de las partes](evidencia/RESPALDO-CIFRADO.json). La comprobación remota usa los SHA256 de la API; no se descargaron nuevamente los 4,5 GB desde GitHub.

## Qué se conserva

- Las doce imágenes de los dos respaldos OEM originales del primer P291.
- La imagen de userdata anterior a la instalación 0.2.2. Son **13 imágenes únicas de esos tres conjuntos, 6.157.238.272 bytes**. Las otras cinco imágenes del respaldo nuevo coinciden con originales existentes; el índice conserva sus equivalencias y el recuperador puede reconstruir esas copias.
- Los manifiestos y registros de esas adquisiciones, los informes anteriores conservados en la adquisición del USB, las evidencias de instalación y la foto del primer inicio. Algunas capturas históricas incluyen otras copias de metadatos de arranque; no se confunden con los trece archivos de los tres conjuntos principales.
- Los ZIP exactos de instalación y restauración 0.2.2, con sus recibos de verificación. El restaurador recupera cinco imágenes OEM y conserva userdata: no restaura el archivo `data.img`.

Este conjunto contiene datos privados y por eso se cifra íntegramente. No incluye la clave de descifrado ni las claves de firma del proyecto. Tampoco es una copia de toda la eMMC ni una instantánea atómica: algunas particiones se adquirieron con Android activo. No se ha probado una restauración física. Conservar misc, ENV o TEE no autoriza escribirlos en otro equipo ni reponerlos sin un procedimiento específico.

## Cifrado y verificaciones

Se utiliza [age](https://github.com/FiloSottile/age), versión 1.3.2 oficial, con un destinatario X25519 generado para este respaldo. Su distribución de Windows se coteja con el tamaño y SHA256 publicados por GitHub. El contenido secreto de la clave nunca se pasa por argumentos ni se imprime; en Windows el archivo privado queda accesible únicamente para la cuenta operadora y SYSTEM.

El [preparador](herramientas/preparar-respaldo-cifrado.py) comprueba los archivos contra los manifiestos existentes mientras los comprime. Después cifra, descifra de nuevo, compara el ZIP completo y relee todos sus archivos. También comprueba que concatenar las partes reproduce exactamente el archivo cifrado. Las fuentes no se montan ni se modifican.

Se ejecutó también el recuperador completo contra las partes reales: **465 archivos y cinco copias equivalentes verificados**. [Recibo de la prueba en PC](evidencia/RECUPERACION-RESPALDO-PC.json). Se sincronizaron los archivos; en Windows no se acredita sincronización de directorios. El ensayo no restauró el TV.

El [publicador](herramientas/publicar-respaldo-cifrado.py) acepta exclusivamente las partes cifradas declaradas y el manifiesto público. Primero sube a un borrador; solo publica cuando los nombres, tamaños y hashes de todos los archivos remotos coinciden. No carga originales ni claves. Ante una interrupción conserva el borrador para revisar y continuar, sin reemplazar archivos distintos por el mismo nombre.

## Recuperar los archivos en otra PC

1. Descargar todas las partes y `RESPALDO-CIFRADO.json` de la misma Release, en una carpeta.
2. Obtener la clave privada por una vía separada. En la PC operadora está en `privado/backup-github-20260908/CLAVE-PRIVADA-RESPALDO-P291.txt`. **Guardar otra copia segura de esa clave fuera de esta PC**: el respaldo de GitHub no permite recuperarla. No adjuntarla al repositorio, a una issue ni a una Release.
3. Tener Python y el ejecutable oficial `age`. Usar el [recuperador de archivos](herramientas/recuperar-respaldo-cifrado.py) indicando manifiesto, archivo de clave, ejecutable y un directorio de salida nuevo. Ejemplo:

```text
python docs/herramientas/recuperar-respaldo-cifrado.py --manifest DESCARGAS/RESPALDO-CIFRADO.json --key RUTA-PRIVADA/CLAVE-PRIVADA-RESPALDO-P291.txt --age HERRAMIENTAS/age.exe --output RECUPERADO-NUEVO
```

El recuperador comprueba hashes, descifra y extrae en la PC; reconstruye los cinco archivos equivalentes como copias verificadas. Un error debe conservarse como incompleto, sin dar por recuperado el respaldo. **Este paso recupera archivos; no instala ni restaura el TV, no toca el pendrive y no habilita diagnóstico.** La restauración del equipo requiere un procedimiento aparte.

Fuentes y contexto: [instalación física](evidencia/INSTALACION-FISICA-P291-022.md), [hallazgos de la adquisición](../diagnostico/primer-tv-instalado-20260908/HALLAZGOS.md) y [política de publicación](PUBLICACION.md).
