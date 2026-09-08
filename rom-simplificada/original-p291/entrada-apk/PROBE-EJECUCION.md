# Prueba mínima de app_process con el su existente

Preparada en PC; **no ejecutada en el TV por el autor de este componente**. No es otra APK para el usuario ni la entrada a recovery. Sirve para probar identidad y sincronización dirigida de un archivo temporal de 64 bytes antes de implementar la entrada final.

## Artefacto exacto

- JAR: `privado/probe-20260908-012842-890442/tvbase-root-probe-0.1.jar`, 8704 bytes.
- SHA256 JAR: `2dd8886340ea68d4bb36301aa65aef9e3afaa0e49359792b9439aa1186a5a24d`.
- SHA256 DEX: `bc63409c29ce0478cf2f508b2af4b75f8bcf44f752acdede6fc0571c645a83e8`.
- [Recibo de compilación](PROBE-COMPILADO.json): fuentes exactas, SDK 28, DEX 039 y 17 controles host del contrato. No se ejecutaron APIs Android en PC.
- [RootProbe.java](RootProbe.java), SHA256 `f5682a4d4538b5c5a0e2e5552db893f197e832a098efe0649374c42bf8207ee5`.
- [ProbeContract.java](ProbeContract.java), SHA256 `82ea5d656a6f6b079d7dbb502177df049902b8b555ca6201b694513e99f43424`.

El coordinador debe copiar por LAN este JAR a `/data/local/tmp/tvbase-root-probe-2dd8886340ea.jar` y verificar allí tamaño/SHA antes de ejecutar. La copia es una operación separada; este documento no acredita que haya ocurrido. El JAR contiene únicamente `classes.dex`, no un manifiesto de APK ni otro binario.

## Una ejecución propuesta

Nonce reservado para este intento: `860b59cf74cb8662a2a614fab4248349`.

Comando **dentro del Android**, después de comprobar el JAR transferido:

```sh
/system/xbin/su 0 /system/bin/sh -c 'CLASSPATH=/data/local/tmp/tvbase-root-probe-2dd8886340ea.jar /system/bin/toybox timeout -s KILL 20 /system/bin/app_process /system/bin local.tvbase.acceso.RootProbe 860b59cf74cb8662a2a614fab4248349'
```

El coordinador conserva stdout/stderr y el código remoto mediante el transporte `exec-out` y el marcador de cierre ya revisado. El plazo del transporte debe dejar margen al plazo de 20 segundos del proceso. Si el proceso queda en espera no interrumpible del kernel, el timeout no garantiza haberlo terminado; no repetir ni interpretar silencio como éxito.

El programa exige UID 0, API 28 y DT exacto antes de escribir. No admite argumento de destino: el único directorio posible para este nonce es `/data/local/tmp/tvbase-entry-probe-860b59cf74cb8662a2a614fab4248349`. La existencia previa del directorio provoca fallo, incluso si parece vacío. No se borra ni se reutiliza automáticamente.

## Resultado esperado y lectura

El programa emite líneas `TVBASE_ROOT_PROBE:` con JSON. Primero comunica identidad y fase; solo emite un `state=passed` terminal después de cerrar todos los descriptores sin error. Deben coincidir el nonce y el código remoto 0. Una línea parcial de identidad o fsync no alcanza.

Archivo esperado: `probe.bin`, 64 bytes, SHA256 `ed902196ce8b230c5577e4bb624e8f9a80016606009760738b06049661bea656`. Se conserva como evidencia, con modo 0600 dentro de un directorio nuevo 0700. El proceso exige creación exclusiva, fsync de archivo, de directorio y de su padre, y lectura posterior con identidad de inode/dispositivo, tamaño y bytes iguales. Devuelve además UID, API, DT, build y kernel observados.

Un resultado aprobado acredita esta prueba de `app_process`, lectura y fsync **en `/data/local/tmp` de este arranque**. No acredita persistencia del pendrive, montaje FAT32, BCB, uncrypt, recovery, instalación, reset ni supervivencia ante un corte. El proceso ART puede generar caché de ejecución. No se afirma cero escrituras internas: están previstas la transferencia del JAR, la carpeta temporal y su archivo pequeño.

Si falla, conservar tanto el informe como los archivos que existan. Las fases permiten diferenciar rechazo de identidad, arranque del helper, creación, fsync y lectura. El programa no toca `/dev/block`, no consulta servicios Binder, no abre sockets, no invoca shell adicional ni cambia propiedades.

## Incidente de compilación resuelto

El SDK 28 local no expone `OsConstants.O_DIRECTORY`. La primera compilación se detuvo y se conservó en su carpeta privada. La fuente final abre directorios con `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` y exige `S_ISDIR` e identidad equivalente mediante `fstat`, evitando introducir un número de flag dependiente de arquitectura. Esto se compiló correctamente; la prueba real sigue pendiente.
