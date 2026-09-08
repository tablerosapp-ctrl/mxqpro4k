# Capturas Rockchip recibidas y corrección de guardado 0.3

El Kingston regresó con el ZIP P271 anterior y cuatro ZIP nuevos: dos fichas iniciales y sus dos inventarios, enlazados correctamente. Los cinco ZIP, sus cinco recibos de exportación y dos fotos del equipo que falló quedaron conservados y verificados en un directorio privado nuevo. [Comparación RK3229-A/B y límites](../../diagnostico/reconocimiento-20260908-rk3229-usb/HALLAZGOS.md). El volumen total de los cinco ZIP es 69.545.179 bytes; los cuatro nuevos suman 84.222 bytes. No se recibieron imágenes de particiones ni informe del Rockchip que mostró los errores.

Las fotos de 0.2 muestran ausencia de una actividad para seleccionar carpetas y una ficha inicial local conservada. El usuario identifica ese equipo como Rockchip, distinto de P291/P271, con carcasa MXQ Pro 4K 5G igual a otros. Su DT y modelo exacto siguen pendientes. No se atribuye a ese aparato el mapa USB de los otros dos ni se afirma que cambiar rutas resuelva permisos desconocidos.

## Corrección y pruebas

[Reconocedor 0.3](../../diagnostico/reconocedor-0.3/README.md) incorpora selector propio de USB marcado, búsqueda acotada de rutas anidadas y alternativa explícita en Descargas para traslado manual. Reutiliza la ficha 0.2, conserva el inventario acotado y no agrega red, root, ADB, reinicio o instalación de ROM. El modo local nunca anuncia guardado en USB; sus recibos `.local.json` declaran ese límite.

APK **123.283 bytes**, SHA256 `41e40007de8f14b37119b7335a4541a4c64d5a325e225a42d706195472047869`, versión3/0.3, API21+/target28 y firmante anterior. [Compilación](../../diagnostico/reconocedor-0.3/COMPILACION.json). Once grupos de pruebas del localizador y trece casos de copia local pasaron; una prueba real de symlink se omitió por permisos de Windows. [Recibo PC](../../diagnostico/reconocedor-0.3/PRUEBAS-PC.json). También se revisaron integración/reanudación/mensajes y se compiló contra Android28. No acreditan UI Android, permisos del equipo desconocido o exportación física0.3. Los ocho segundos limitan descubrimiento, no toda revalidación/copia/sincronización.

## Entrega USB

[Preparador nuevo](../../preparacion-usb/preparar-reconocimiento-03.ps1), [recibo](../../preparacion-usb/reconocimiento-03-estado.json). Kingston identificado por identidad, modelo, capacidad, bus, condición no sistema/no boot y marcadores. CheckOnly seguido de una Prepare, ambos con código0. Dos archivos nuevos, 125.331 bytes, con Flush(true) y SHA por relectura:

- `TVBASE-RECONOCIMIENTO/Reconocimiento-TVBase-0.3.apk`.
- `TVBASE-RECONOCIMIENTO/LEEME-0.3.txt`.

Los 216 archivos anteriores pequeños conservaron SHA; ocho grandes conservaron metadatos. Los cinco ZIP recibidos tuvieron además adquisición íntegra previa. Inventario anterior conservado, sin formato, reparación, borrado ni planes añadidos. Quedaron 23.271.063.552 bytes libres. No se acredita flush de volumen ni expulsión física de Windows. No repetir el preparador ni modificar esta entrega sellada.

## Próximo paso

Actualizar a0.3 únicamente el Rockchip que falló, sin desinstalar. Elegir pendrive con el selector propio y completar desde la ficha inicial. Si Android impide acceso, usar **Guardar en Descargas para copiar al USB** y trasladar `TVBASE-PARA-COPIAR` completa con Archivos a la raíz USB. En la próxima devolución revisar tanto esa carpeta como `TVBASE-RECONOCIMIENTO/INFORMES`, preservando la distinción de los recibos locales.

No repetir los equipos ya capturados. Tampoco cargar dos planes RK3229 simultáneos: ambos declaran el mismo DT y aún no tienen perfiles de instalación intercambiables. Entrada, firma y ejecución de recovery por variante siguen pendientes; no se usaron Update ni paquetes del P291.
