# HOME en el primer P291 · ISSUE-HOME-01

## Estado y alcance

El usuario informa que TV Base inició y que WiFi conecta. El detalle comunicado es que la tecla de la casita del control no vuelve al menú principal. Está probando su APK y pidió documentar, sin realizar ningún próximo cambio hasta recibir su **OK explícito**.

Esta revisión fue exclusivamente de archivos locales de la plataforma 0.2.0, cuyos payloads conserva el instalador 0.2.2. No se contactó el TV, no se capturó una pulsación y no se conoce el estado actual de sus ajustes de configuración inicial. No hay causa física confirmada ni corrección implementada. Las pruebas siguientes quedan pendientes de autorización; no deben ejecutarse por continuar esta documentación.

## Registro del inicio

El [manifest vigente](../../rom-simplificada/original-p291/componentes/inicio/AndroidManifest.xml), líneas 6–7, declara `local.tvbase.inicio/.Inicio`, actividad exportada con `singleTask` y filtro `MAIN` + `HOME` + `DEFAULT`. Por tanto, **no falta el filtro HOME** en esta fuente.

[Inicio.java](../../rom-simplificada/original-p291/componentes/inicio/Inicio.java):28 vuelve a dibujar el menú en `onResume()`. Su consulta de categorías `LEANBACK_LAUNCHER` y `LAUNCHER` (:44) sirve para enumerar aplicaciones; no sustituye el filtro HOME. No implementa interceptación de esa tecla. El tratamiento de Atrás (:96) solamente mantiene disponible la pantalla de inicio.

El [constructor](../../rom-simplificada/original-p291/construir.py):307 incorpora esta APK como `/system/app/InicioTV/InicioTV.apk`. La política retira el launcher OEM y agrega el propio; no se encontró una asignación explícita de actividad HOME preferida en las fuentes revisadas. La resolución efectiva del TV después del arranque todavía no fue consultada.

## Hipótesis prioritaria: configuración inicial pendiente

Nuestro [overlay de ajustes](../../rom-simplificada/original-p291/componentes/defaults/res/values/defaults.xml):8 fija `def_device_provisioned=true`, pero no define `user_setup_complete` ni `tv_user_setup_complete`. El constructor incorpora el overlay en vendor (:363–365). Esto por sí solo no acredita el valor final de ninguna de esas preferencias: se conserva `com.android.onetimeinitializer`, entre otros componentes originales, y no se inspeccionó la base de ajustes posterior al arranque.

La comprobación adicional se hizo sobre **el framework real del P291**, conservado byte por byte en la imagen final:

- Archivo interno: `/system/framework/oat/arm/services.vdex`.
- Copia adquirida local: `diagnostico/primer-tv-lan-20260907-184926/privado/services-p291.vdex`.
- SHA256, coincidente en ambas lecturas: `b051439a45d8e7d12839df445a43b0b97c4a9db267a2158a5fd8a5e2aa741649`.
- Formato: VDEX 019, CompactDex 001. Se reutilizaron en memoria las rutinas del lector acotado descrito en [ANALISIS-UPDATE-012](../../diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md). No se ejecutó el firmware ni se escribieron nuevas copias o resultados sobre los originales. No es una decompilación Java integral.

Métodos de `com.android.server.policy.PhoneWindowManager`; los offsets siguientes son bytes absolutos dentro de ese VDEX:

| Método | Offset | Evidencia observada en las instrucciones |
|---|---:|---|
| `isUserSetupComplete()` | 4544692 | Lee Secure `user_setup_complete` con valor por defecto 0; si `mHasFeatureLeanback` es verdadero, exige además el resultado de `isTvUserSetupComplete()`. |
| `isTvUserSetupComplete()` | 4544648 | Lee Secure `tv_user_setup_complete`, también con valor por defecto 0. |
| `startActivityAsUser(Intent, UserHandle)` | 4586012 | Solo llama al inicio de actividad cuando `isUserSetupComplete()` devuelve verdadero. En caso contrario registra `Not starting activity because user setup is in progress: `. |

La cadena local leída es `handleShortPressOnHome()` → `launchHomeFromHotKey()` → `startDockOrHome()` → ese `startActivityAsUser()`, con condiciones intermedias de pantalla bloqueada, sueño y dock. Esto fundamenta una hipótesis concreta: el menú puede aparecer en el arranque mientras la ruta de la tecla HOME queda inhibida por la configuración inicial. **No demuestra que esos flags estén en 0 ni que esta rama se haya ejecutado durante la pulsación comunicada.** La presencia efectiva de la característica Leanback tampoco se consultó en el TV nuevo.

## Alternativa: traducción de la tecla o resolución del destino

Se comparó el contenido de las imágenes finales con el inventario original: los **38 archivos de keylayout en system y 10 en vendor** mantienen sus SHA. Las tablas `/vendor/etc/remote.tab1`, `remote.tab2`, `remote.tab3`, `remote.cfg` y `/vendor/bin/remotecfg.sh` también son idénticas. El bloque `load_remote` continúa en `/vendor/etc/init/hw/init.amlogic.board.rc`:35–47; ese archivo completo sí tiene otras modificaciones deliberadas, por lo que no se afirma identidad de todo el init.

Hay una diferencia heredada relevante entre mapas:

| Ruta dentro de la imagen | Línea | Traducción |
|---|---:|---|
| `/vendor/usr/keylayout/Vendor_0001_Product_0001.kl` | 30 | `key 102 HOME` |
| `/vendor/usr/keylayout/Generic.kl` | 124 | `key 102 MOVE_HOME` |
| `/vendor/usr/keylayout/Generic.kl` | 194 | `key 172 HOME` |

El mapa específico tiene SHA256 `72ba4c141945ab035aba47726089043bf049cc387b0e89edb513779b567bf59a`; Generic de vendor, `7eedc56b9237b8c86345a514b09efd468f49cc624c0ba2034c5c1be28729bf50`. Las tablas IR conservadas asignan 102 a `0x11` en tab1/tab2 (:45) y a `0x95` en tab3 (:31). La captura anterior a la instalación identificaba `aml_keypad` con vendor/product `0001:0001`; no prueba qué mapa o scancode utiliza ahora la tecla pulsada.

Conservar los mapas reduce la sospecha de que la construcción haya cambiado sus bytes, pero no demuestra que Android seleccione el mapa esperado. Una resolución HOME distinta, un componente inhabilitado o una política de ventana también quedan abiertos; no se propone corregirlos sin observar el estado.

## Prueba futura mínima, solo después del OK

1. Leer, sin modificarlos, `device_provisioned`, `user_setup_complete`, `tv_user_setup_complete`, la presencia de Leanback y el componente que resuelve `MAIN` + `HOME`. Esto distingue una configuración pendiente de una selección de launcher incorrecta.
2. Si esa lectura no basta, capturar **una pulsación** de la casita: dispositivo, scancode, keycode y registro acotado del handler HOME. El mensaje de configuración pendiente respaldaría la primera hipótesis; recibir `MOVE_HOME` u otra tecla orientaría al mapa. No repetir capturas generales de radios ni BatteryStats.
3. Solo si aún hace falta, comparar una solicitud lógica de HOME con la tecla física. Que la solicitud lógica funcione y la física no delimitaría el recorrido de entrada; que ambas fallen exige revisar el handler y sus condiciones. Abrir Inicio directamente no prueba que la tecla HOME funcione.

El acceso de diagnóstico para esas lecturas debe acordarse: la plataforma desactiva ADB TCP inicial, de modo que no se presume disponible el acceso anterior. No se habilitará, instalará ni cambiará nada para efectuar estas pruebas sin la autorización solicitada por el usuario.
