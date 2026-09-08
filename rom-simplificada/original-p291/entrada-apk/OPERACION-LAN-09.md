# Operación de Acceso USB 0.9 desde la PC

El [cliente entrada-lan09.py](entrada-lan09.py) permite iniciar y observar el helper de la APK 0.9 ya sellada cuando el diálogo de actualización al 2 % tapa la pantalla. Usa la conexión ADB de la sesión privada existente. No hace visible la Activity ni elimina el diálogo. El pendrive sigue siendo el origen de la ROM y el destino de los respaldos; esta vía de operación necesita LAN durante la preparación y su observación.

**Estado de este cliente: verificado en PC, no ejecutado en el TV durante su desarrollo.** Sus pruebas no acreditan el desacoplamiento físico del helper, fsync del pendrive, escritura ENV/BCB, entrada a recovery, instalación o restauración. La [liberación de la APK](LIBERACION-09.json) y sus siete fuentes permanecen intactas. El cliente no compila ni instala otra APK.

## Autorización y alcance

`prepare` inicia una operación real: el helper verifica el ZIP 0.2.1, respalda ENV/misc y órdenes de cache, neutraliza esas órdenes y prepara ENV/BCB para intentar abrir el menú de recovery. No es una prueba de lectura. La escritura de ENV puede impedir el arranque si queda incompleta; su restauración y el retorno del cargador no están probados. El programa no reinicia ni instala automáticamente la ROM.

Al evitar la pantalla se evita también su confirmación. **Antes de ejecutar `prepare`, el operador debe contar con una confirmación explícita en la conversación para esta preparación y explicar el riesgo de modificar ENV/BCB.** `--accept-env-bcb-risk` expresa esa elección al programa, y `--authorization-note` registra su referencia en el recibo privado. Escribir esos argumentos no genera autorización ni sustituye una respuesta del usuario. El cliente puede comprobar que están presentes; no puede comprobar quién autorizó la acción.

El diálogo antiguo y el hilo de cierre OEM pueden seguir activos. Este cliente no los cancela ni garantiza que permanezcan detenidos. Las comprobaciones del helper detectan determinados cambios de cache y bloques durante la preparación; no eliminan toda posible concurrencia del sistema original.

## Requisitos antes del único lanzamiento

1. El primer P291 debe conservar Android original, alimentación estable y la conexión ADB existente. No ejecutar `adb root`, abrir otro servicio, cambiar autenticación ni repetir Update.
2. Conectar al TV el pendrive ya preparado con el marcador y `TVBASE-P291-A9-0.2.1-RECOVERY.zip`. La APK exige 573688933 bytes y SHA256 `dcb152c77e55cb067d6e88a8144990a3edb5d06568ea8cdfdc414a0fa21aac58`. La comprobación USB/ZIP se ejecuta dentro del helper antes de modificar los bloques; el cliente PC no sustituye ese control.
3. La APK instalada debe ser `local.tvbase.acceso`, archivo único de 61843 bytes, SHA256 `1d0f267e818acca5562048f9961c7c234f36b8cc81f827cb3eac9e3fcd2505a4`. El cliente vuelve a obtener su ruta mediante `pm path`; no fija una ruta de instalación antigua.
4. El destino se lee de `diagnostico/primer-tv-lan-20260907-184926/privado/session.json`. Solo se acepta una dirección LAN IPv4 con puerto 5555; no hay una IP real en las fuentes publicadas. `--session` permite indicar otro archivo privado verificado, pero `status` exige que su destino coincida con el del intento original. El programa no conecta ni descubre otros equipos.
5. Obtener la autorización descrita arriba. No usar el comando siguiente como una comprobación inocua.

Desde la raíz del proyecto, con el Python disponible en PC:

```text
python -X utf8 -B rom-simplificada/original-p291/entrada-apk/entrada-lan09.py prepare --accept-env-bcb-risk --authorization-note "Referencia a la confirmación explícita recibida"
```

El cliente crea un nonce nuevo y un recibo privado `entrada-apk/privado/lan09-<nonce>/attempt.json`. Persiste ese archivo y un puntero exclusivo `entrada-apk/privado/LAN09-ACTIVE.json`, sincroniza los archivos y verifica sus bytes antes de lanzar. Los cambios posteriores del recibo se reemplazan de forma atómica; en Windows se utiliza `MoveFileExW` con `WRITE_THROUGH`, además de `os.fsync` y lectura posterior. Esto solicita persistencia al sistema; no prueba la resistencia de la PC o del dispositivo a una falla eléctrica. Windows no se presenta como una prueba de fsync de directorios FAT32 del TV.

Antes de `launch`, comprueba UID shell 2000, `su` existente con UID 0, API 28, DT `gxlx2_p291_1g`, build original exacto, kernel 4.9.113 y ruta/tamaño/SHA de la APK instalada. También enumera el directorio temporal como root para confirmar la ausencia de `/data/local/tmp/tvbase-entry-in-progress`; un error de lectura o una ruta existente detienen el lanzamiento. El helper vuelve a verificar el perfil y crea exclusivamente ese estado interno.

El recibo queda marcado `launch_issued=true` y sincronizado **antes** de invocar ADB. El transporte usa una lista de argumentos y `exec-out`; no pasa los comandos por PowerShell ni permite comandos procedentes del USB. La sintaxis replica [EntryContract.java](src/EntryContract.java): `su 0`, `app_process` y la clase `PreparationHelper` de la misma APK, operación `launch`, nonce. No se llama directamente a `prepare`, que es una fase interna del proceso desacoplado.

## Continuar la observación tras una desconexión

`launched` solo confirma que el lanzador inició el proceso. Guardar la ruta del recibo que imprime el cliente y ejecutar:

```text
python -X utf8 -B rom-simplificada/original-p291/entrada-apk/entrada-lan09.py status --attempt "RUTA_PRIVADA_DEL_INTENTO/attempt.json"
```

`status` no tiene un argumento para aceptar riesgos y no puede emitir `launch`. Lee el nonce conservado, exige el mismo destino y APK, vuelve a validar el perfil, consulta el estado y agrega una observación al recibo. Se puede volver a ejecutar después de perder la conexión. Debe hacerse con el mismo recibo y antes de la instalación o de cambios de firmware que invaliden este perfil.

| Resultado | Qué acredita y cómo continuar |
| --- | --- |
| `launched` | Lanzamiento confirmado, preparación todavía pendiente. Consultar `status`. |
| `stage` | Fase observada del helper. Seguir observando; no ejecutar otro `prepare`. |
| `prepared` | El helper confirma sus recibos internos/USB, ausencia de fallo y hash del manifiesto. El cliente exige además lecturas finales ENV/BCB declaradas y salida remota 0. La ROM aún no se instaló; cualquier ciclo de alimentación es una acción física posterior y separada. |
| `incomplete` | El helper declaró un fallo. Conservar alimentación, USB e informes para revisar antes de otra acción. |
| `indeterminate`, timeout o salida inválida | No hay un resultado acreditado. El proceso remoto podría continuar. Consultar el mismo intento; no relanzar ni suponer cancelación. |
| `preflight_failed` | El cliente no emitió `launch`; conserva la causa y bloquea repetirlo automáticamente. Revisar el recibo y la causa antes de decidir otro intento. |

El parser rechaza nonces distintos, JSON ambiguo, estados desconocidos, respuestas duplicadas, códigos no válidos, resultados después del código final y un `prepared` sin sus campos de lectura/hash. No interpreta un cierre ADB o su código local 0 como preparación correcta. Exige `TVBASE_ENTRY` y `TVBASE_EXIT` coherentes. Un `incomplete` preservado por el helper puede acompañarse de código remoto 0 o 1 y sigue siendo un fallo.

La consulta terminal del helper verifica recibos y sincronización; no vuelve a leer los bloques ENV/misc en cada consulta. Su lectura completa de bloques pertenece al cierre de la preparación, y una modificación ajena posterior no queda descartada por leer otra vez el mismo recibo.

## Límites y conservación

Cada conexión tiene un plazo de 30 segundos y retiene como máximo 128 KiB por canal durante la lectura. Ante exceso o timeout, se detiene únicamente el proceso `adb.exe` de la PC y se conservan los bytes parciales disponibles. No se envía `kill`, señal, reset ni otra orden al TV. El helper desacoplado puede continuar; perder el transporte nunca se convierte en autorización para relanzarlo.

El puntero privado no se elimina automáticamente ni siquiera después de éxito o fallo previo al lanzamiento. Un segundo `prepare` queda bloqueado antes de consultar el TV. Un lock de archivo también impide dos clientes simultáneos sobre el mismo recibo. Si el puntero o el recibo resultan parciales, la salida es conservadora: preservar y revisar, no borrar para sortear el bloqueo. El estado interno `tvbase-entry-in-progress` del TV se conserva igualmente.

Los comandos, respuestas, destino, nonce y nota de autorización se guardan bajo `privado/`, con hashes de stdout/stderr y resultado de cada consulta. No publicar estos recibos crudos. Las pruebas emplean destinos ficticios y procesos Python locales; [test_entrada_lan09.py](test_entrada_lan09.py) no ejecuta ADB.

La vía LAN no escribe las preferencias de la Activity. La pantalla no conoce el nonce creado por la PC y su botón de observación no podrá retomar este intento. Continuar con el cliente PC; no tocar a ciegas «Preparar» en el TV. El bloqueo interno impide una segunda preparación, pero no hace visible ni actualiza la interfaz.

No se encontró una vía acreditada para cerrar el progreso del framework sin alterarlo. La [referencia AOSP local](../../../tools/h1-referencias/ShutdownThread.java) liga `CLOSE_SYSTEM_DIALOGS` a la confirmación inicial y crea aparte el progreso no cancelable. `am start`, BACK/HOME o detener la APK OEM no acreditan que ese progreso desaparezca ni que se cancele su hilo de cierre.
