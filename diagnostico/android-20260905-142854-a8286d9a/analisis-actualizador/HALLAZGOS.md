# Actualizador del segundo TV: analisis estatico

Analizado exclusivamente el APK copiado a la PC (190988 bytes). No se ejecuto codigo de la APK ni se enviaron comandos al TV en este analisis. Alcance: tablas, referencias y limites de instrucciones DEX de los metodos relevantes; no equivale a una auditoria completa de toda la aplicacion.

## Resultado util

- Paquete instalado: `com.droidlogic.otaupgrade`. Su actividad de entrada es `.MainActivity`, publicada en el lanzador y en `android.settings.SYSTEM_UPDATE_SETTINGS` (confirmado por el informe de PackageManager).
- Existe una funcion REAL de actualizacion local: `MainActivity.onClick` construye un Intent de clase `FileSelector` y usa `startActivityForResult`. Otra rama lee el archivo seleccionado y prepara `InstallPackage`.
- `FileSelector$ZipFileFilter.accept` acepta directorios y nombres terminados en `.zip`, sin distinguir mayusculas. No es un selector de imagenes de fabrica `.img`.
- `MainActivity.onCreate` construye la pantalla y `PrefUtils`; ese constructor abre SharedPreferences `update`. `onResume` registra listeners y controla visibilidad. En estos metodos no aparecen arranque de UpdateService, descarga, comprobacion de Internet ni reinicio.
- La rama online esta separada en `onClick`: `checkInternet`, Intent con accion `com.android.update.check`, clase `UpdateActivity`. No abrir esta ultima para la inspeccion local.
- `PrefUtils.isUserVer` consulta `ro.secure`, `ro.debuggable` y `ro.otaupdate.local`; la visibilidad de controles puede variar con esas propiedades.

## Limite de la inspeccion segura

Abrir la pantalla principal y el selector para ver los medios disponibles es una inspeccion acotada. No es necesario instalar otra APK. Abrir el selector directamente por componente puede estar restringido si no esta exportado; la via prevista es su boton en MainActivity.

**No pulsar Actualizar local solamente para mirar la confirmacion.** La rama de `MainActivity.onClick` invoca `PrefUtils.createAmlScript` ANTES de `UpdateDialog`. `createAmlScript` borra/recrea `/cache/recovery/command` y escribe `--update_package=...`, `--locale=...` y, segun las casillas, `--wipe_data` o `--wipe_media`. Por tanto, llegar a ese dialogo ya puede modificar una orden persistente de recovery.

Evitar las ramas online, backup, restore, actualizar y las casillas de borrado mientras solo se examina el equipo. No se demostro todavia que el recovery acepte un paquete determinado ni que la placa ejecute aml_autoscript desde USB.

## Evidencia local

- `referencias-dex.json`: metodos, offset de codigo, palabras DEX y referencias decodificadas.
- `strings.txt`: tabla de cadenas de classes.dex.
- `leer_dex.py`: analizador local que genero ambos archivos; no utiliza ADB ni ejecuta la APK.
