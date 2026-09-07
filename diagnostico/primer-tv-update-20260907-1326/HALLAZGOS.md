# Primer intento OEM con la ROM completa: detenido al 2 %

7/9/2026. El usuario aportó cuatro fotos secuenciales y confirmó **más de diez minutos sin avance al 2 %**. Los originales se copiaron a esta carpeta con SHA coincidente y quedan fuera de Git. [Manifestación y hashes](resumen-saneado.json).

## Qué muestran las imágenes

1. Menú original Update con Select y Update.
2. ROM P291 A9 0.1.1 RECOVERY seleccionada, junto a la confirmación de actualización.
3. Diálogo del fabricante con Preparing/Copying.
4. Diálogo del sistema Android, Preparando para actualizar, 2 %, superpuesto al anterior.

Este es el primer intento comunicado con el ZIP completo desde el menú OEM. El anterior 2 % correspondía al ZIP vacío. **Ahora no se puede atribuir el bloqueo solo a aquel archivo vacío.** El menú se abrió; no apareció recovery ni resultado de nuestro ejecutable de instalación. No se recibieron registros nuevos del TV ni se leyó el USB durante este intento. La APK0.7 no captura automáticamente el fallo posterior.

## Interpretación sustentada y sus límites

Se conservó la [fuente exacta AOSP Android9](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-9.0.0_r1/services/core/java/com/android/server/power/ShutdownThread.java), SHA `621940271d7af066dfb99bc4cc87db7747bc24f36af728aad99b6c74fe120a9b`. Asigna 2 % tras la notificación inicial de apagado, 4 % al regresar ActivityManager y 20 % antes de procesar el paquete. La barra numérica se crea cuando falta el mapa de bloques y existe la solicitud de procesamiento.

La pantalla es compatible con un atasco previo al reinicio, alrededor del cierre de ActivityManager. **Es una inferencia:** no se extrajo el framework instalado y una interfaz congelada puede no reflejar el punto real del proceso. No demuestra que ActivityManager sea la causa, que uncrypt falte ni que el paquete interno sea íntegro. Tampoco acredita BCB/mapa correcto o aceptación de firma por recovery. El límite de quince minutos del procesamiento posterior de paquetes en AOSP no convierte diez minutos al 2 % en una espera normal de ese procesamiento.

El [APK real analizado](../primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md) prepara archivos/BCB antes de pedir reinicio. Su copia tiene controles débiles; llegar a esta pantalla no prueba integridad de la copia interna. Sus órdenes pueden haber persistido aunque no haya instalación. El [pstore de intentos anteriores](../primer-tv-evidencia-20260907-000948/HALLAZGOS.md) apuntaba también a un cierre atascado, pero no es un log de este intento y no debe presentarse como tal.

## Decisión operativa

No repetir Update, ni reabrir el menú para otro intento idéntico, ni crear otra APK cuyo único cambio sea pedir otro reinicio. Acceso0.7 cumplió la apertura de menú comunicada, pero **la ruta OEM con ZIP completo también quedó atascada**. VAL-05 y la instalación interna siguen pendientes.

Para salir del bloqueo comunicado, se indica un único ciclo manual: cortar la alimentación diez segundos y volver a conectarla manteniendo el pendrive. Es una salida de un sistema inmóvil, no una confirmación de que la actualización esté preparada ni una garantía de recuperación. Puede haber órdenes persistentes y no se promete ausencia de riesgo al cortar. Si aparece progreso real de instalación, mantener alimentación/USB y dejarlo continuar; si aparece recovery/error, conservar el texto y no elegir wipe; si vuelve Android, no repetir Update. El resultado físico de ese ciclo queda pendiente de respuesta.

El siguiente trabajo debe distinguir preparación y cierre mediante registros específicos, o establecer una entrada física a recovery confirmada para esta placa. No se exige red del primer TV ni se habilita root. Una captura general idéntica no resolvería qué ocurrió después de Update; cualquier instrumento nuevo debe registrar ese intervalo y conservar el resultado. No modificar la ROM o atribuir el fallo al pendrive basándose solo en estas fotos.
