# TV Base P291 0.1.2: Bluetooth desactivado en la ROM

Esta revisión responde a REQ-13: prescindir deBluetooth en el primerP291 y conservarWiFi/Ethernet como objetivos. Está construida y verificada enPC; **todavía no instalada ni probada en el TV**.

El [ZIP0.1.2](salida/TVBASE-P291-A9-0.1.2-RECOVERY.zip) tiene573082917B, SHA256 `6c0c4307208c8d0e1a958a3fc6c790fa94021a850599985b0a41b340b821bb99`. El [recibo completo](salida/RECOVERY-VERIFICACION-0.1.2.json) reúne firma integral Python/OpenJDK, comprobación de los cinco payloads y aceptación por el validadorWindows de esa versión. El instalador requiere respaldo original antes de escribir y conserva las mismas guardas delperfilP291. La ROM0.1.1 y todos sus recibos permanecen intactos.

## Cambios

- Retira Bluetooth, BluetoothSettings y BluetoothRemote, incluidas sus optimizaciones locales.
- Retira las declaraciones positivas Bluetooth/BLE y agrega `unavailable-feature` para evitar que una preferencia heredada vuelva a habilitar el gestor.
- Neutraliza el servicio HALBluetooth y sus órdenes explícitas de inicio; retira solo su entrada del manifiestoHAL.
- Quita las tres reglas de cargaBluetooth de init y el módulo cargable `btmtksdio.ko`.
- Actualiza la identificación de la ROM a0.1.2, conservando la protección de recovery incorporada en0.1.1.

Solo cambia system/vendor. Product, odm y boot son idénticos a0.1.1. Los dos sistemas de archivos pasaronfsck, y cada archivo nuevo/reemplazado se leyó para comprobar contenido, permisos, propietarios y SELinux. Se cotejaron3486archivos restantes idénticos, incluidos170relacionados conWiFi.

Esto elimina la pilaBluetooth operativa y su móduloMTK. **No retira todos los auxiliaresBluetooth compilados en el kernel ni modifica los pines compartidos delDT.** Conserva las bibliotecas de API comunes para evitar romper otros componentes. DriversWiFi, firmware/EEPROM, serviciosWiFi y controles de alimentación compartidos permanecen iguales al candidato.

## Por qué no basta una preferenciaOFF

En la observaciónLAN, el estado visibleOFF coexistía con preferencia1, reinicios del servicio y una espera delHAL. La API normal guardó0, pero apareció una reactivación pendiente; luego se inhabilitó el paqueteBluetooth del Androidactual. Esos cambios de diagnóstico **no equivalen a instalar estaROM**. [Evidencia](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md).

En [SystemServer Android9](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/java/com/android/server/SystemServer.java), el gestor depende de la capacidadBluetooth. [SystemConfig Android9](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/core/java/com/android/server/SystemConfig.java) admite retirar explícitamente esa capacidad. La receta añade capas en servicio y módulo, además de esas declaraciones. Son fundamentos de diseño, no una prueba de arranque del candidato.

## Construcción y comprobación

1. [Preparador de imágenes](instalador/preparar-sin-bluetooth-0.1.2.py): copias aisladas y receta, lectura completa de cambios/restantes, fsck y metadatos.
2. [Revisión de imágenes](trabajo/revision-0.1.2/revision.json): cambios y SHA deWiFi conservados.
3. [Empaquetador](instalador/empaquetar-sin-bluetooth.py): instaladorARM32 y validadorWindows con ID0.1.2, pruebasGo y rechazo explícito de0.1.1 por el ejecutable nuevo; firma y comprobación integral.
4. [Manifiesto final](instalador/manifest-0.1.2.json): cinco particiones, tamaños y hashes.

Los scripts rechazan salidas previas; no volver a ejecutarlos sobre una revisión ya construida. No escriben dispositivos físicos.

## Pendiente físico

Todavía faltan entrada real a recovery, respaldo delTV, instalación, primer arranque y pruebaWiFi. Los binarios de radio del candidato son distintos de los actuales; su diferencia no demuestra que reparenWiFi. Bluetooth no se reactivará como parte de la prueba. El rendimientoWebView/video y la capacidad de restauración siguen pendientes.
