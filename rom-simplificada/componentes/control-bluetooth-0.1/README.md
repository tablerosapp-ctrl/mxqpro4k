# Control Bluetooth 0.1

Auxiliar Android9/API28 para una solicitud explícita de apagar Bluetooth, autorizada por el usuario. Mantiene disponible una restauración manual que solicita encender Bluetooth. No reconstruye automáticamente un estado anterior averiado. El padre valida el primer P291 antes de instalar; esta APK comprueba API28, no la placa.

Paquete `com.tvbase.bluetoothcontrol`, Activity `.ControlActivity`. Solo permisos normales `BLUETOOTH` y `BLUETOOTH_ADMIN`. No usa red, ADB, root, comandos del sistema, APIs ocultas ni reinicio. No toca WiFi. Abrirla sin extra consulta el estado y no cambia el adaptador. No pide concesiones privilegiadas.

## Uso explícito

Botones visibles «Desactivar Bluetooth» y «Restaurar Bluetooth». Para el operador que ya validó la identidad mediante ADB normal:

```
am start -n com.tvbase.bluetoothcontrol/.ControlActivity --es accion desactivar
am start -n com.tvbase.bluetoothcontrol/.ControlActivity --es accion restaurar
```

Son dos alternativas; no ejecutar consecutivamente. Cada Intent consume su extra; recrear la Activity no repite la acción. La apertura simple no envía ninguna solicitud de activar/desactivar. Solo se admite una consulta/acción en vuelo; otra se rechaza sin cola. El estado y el resultado se muestran en pantalla, en SharedPreferences privadas `resultado`/`ultimo` y en logcat bajo `TVBASE_BT`. No exporta preferencias ni un proveedor de archivos.

Las llamadas se ejecutan fuera del hilo de interfaz. A los8s la pantalla avisa si siguen pendientes: ese plazo no cancela el servidor ni habilita otro intento. El registro `en_vuelo` se guarda con `commit()` antes de la llamada; falla sin invocarla si no se pudo registrar. Si el proceso muere dejando una solicitud pendiente, una nueva instancia conserva el registro y bloquea nuevas solicitudes: requiere revisar ese resultado desde la PC, no reenvía por rutina ni resetea el registro. No garantiza que una caída del almacenamiento conserve datos que Android no logró guardar.

`disable()` persiste la preferenciaOFF y `enable()` solicita el encendido. Su retorno booleano se registra como aceptación, separado del estado que se lee después y de las notificaciones `ACTION_STATE_CHANGED`. OFF visible no demuestra que cesaran reinicios del servicio, BLE o actividad del controlador; hay que comprobarlo en los registros externos. La operación puede esperar o fallar por el mismo problema del sistema observado. No constituye una reparación del driver ni garantiza que el ajuste sea inmune a un kernel panic.

La Activity es exportada para una invocación explícita del operador, sin receiver de arranque ni servicios. Otra app instalada podría enviar un Intent explícito a esta Activity, como puede llamar la API de Bluetooth con esos permisos normales en Android9. Herramienta de diagnóstico local, no componente de administración para producción.

## Fuente y verificación

Compilador: `rom-simplificada/instalador/compilar-control-bluetooth.py`. Genera un directorio nuevo, conserva la clave de componentes existente, verifica compilación API28, paquete/versión/permisos, alineación, integridadZIP y firma; enlaza las fuentes/constructor/APK con SHA256 en `compilacion/control-bluetooth-0.1/componente.json`. No incluye pruebas de ejecución física.

Fuentes primarias AOSP9:

- [BluetoothCommand: svc usa la API del adaptador](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/cmds/svc/src/com/android/commands/svc/BluetoothCommand.java).
- [BluetoothAdapter: disable/enable y aceptación asíncrona](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/core/java/android/bluetooth/BluetoothAdapter.java).
- [BluetoothManagerService: permisos, preferencia y mensajes de apagado](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/services/core/java/com/android/server/BluetoothManagerService.java).
- [Definiciones: BLUETOOTH_ADMIN es normal](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/core/res/AndroidManifest.xml).
- [Shell AOSP9: no declara BLUETOOTH_ADMIN](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/packages/Shell/AndroidManifest.xml).

La presencia de `svc bluetooth` no acredita que UID2000 pueda usarlo. En el P291 se debe conservar el resultado real de permisos; esta APK declara los permisos normales para usar la API bajo su propio UID, sin modificar los permisos de shell. No se utilizan números de transacciones Binder.
