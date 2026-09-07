# Comparación de radios: P291 instalado y ROM candidata

Revisión del 7/9/2026. Compara las lecturas del primer P291 por LAN con el candidato Android9 y las imágenes preparadas en PC. **Las diferencias binarias están comprobadas; no acreditan que el candidato recupere WiFi ni que corrija el panic observado.** El segundo P271 no interviene en esta comparación.

## Procedencia y método

- **TV actual:** hashes leídos en el P291 de cuatro archivos bajo `/vendor`, identificación del kernel y pstore. Los originales privados de esta adquisición son `privado/modulos-radio-actuales.txt`, `privado/firmware-radio-actual.txt`, `privado/kernel-actual.txt` y `privado/pstore-lan.txt`. No se publican estos registros crudos.
- **Candidato:** lectura selectiva en memoria de los archivos identificados por el [inventario vendor](../../rom-simplificada/inspeccion/vendor-inventario.json), desde el contenedor local verificado. No se ejecutó firmware ni se extrajo nuevamente una partición completa.
- **ROM0.1.1:** se compararon esos archivos con `rom-simplificada/trabajo/vendor.raw.img`. Su SHA y el de `boot-original.img` coinciden con el [manifiesto verificado de0.1.1](../../rom-simplificada/salida/RECOVERY-VERIFICACION-0.1.1.json). Los archivos de radio seleccionados son idénticos entre candidato y vendor preparado.
- **ROM0.1.2:** el [recibo de preparación](../../rom-simplificada/trabajo/revision-0.1.2/revision.json) registra qué se retiró y qué se conservó. Las comprobaciones son locales; no sustituyen una prueba física.

## Módulos y firmware

SHA256 de los archivos completos. Las rutas de esta tabla son relativas a `/vendor/`.

| Archivo | P291 instalado | Candidato y ROM0.1.1 | ROM0.1.2 preparada |
| --- | --- | --- | --- |
| `lib/modules/wlan_mt7663_sdio.ko` | `efb0c9c6f518e5fa36a5ca22bc9cf6f39df146becf18f5e28c1317a8a935795b` | `1f786fb77de77860b07da863a019bad6f49b325555b1dc0953a8abe6c8697abc` | Conservado, mismo SHA del candidato |
| `lib/modules/btmtksdio.ko` | `0132022f7f9211293d5ed51605027d444f3b1825ea0009b7d88c777a6c05440c` | `7828aa5b4fa94b27db0f6070b77b0dffe45ba36f52546dde0ae9cde560e6771c` | Retirado de la imagen |
| `firmware/WIFI_RAM_CODE_MT7663.bin` | `b7d3ffcdb30400c58536a7f64fcf63279e2df06761b5bb4486c83ee596b7380f` | `223f73f17f0f986dc4e7167daa6eef14ffb41c713f22d70f9645eb049bdec80a` | Conservado, mismo SHA del candidato |
| `firmware/mt7663_patch_e2_hdr.bin` | `f85af805f48dd6f0bd873d0e72de491ba6041447e6a394a328e77f5e16ad0959` | `82e072e52c458a2d368703ac161c97fac25e0eeb18ad4788ccc9e2213dcf2490` | Conservado, mismo SHA del candidato |

Los cuatro archivos del TV difieren del candidato. No se deduce de ello cuál funciona mejor ni si la diferencia es la corrección necesaria para esta unidad.

`firmware/EEPROM_MT7663.bin` del candidato mide1536B y tiene SHA `ae482b8115d1276add2bf321d0838e342285867acea412dc2647429b26ca8d92`. Se conserva idéntico en0.1.1 y0.1.2. **No hay comparación con un hash del EEPROM instalado en el TV en esta revisión.**

## Versiones declaradas y compilación

| Elemento | P291 instalado / pstore adquirido | Candidato, conservado por0.1.1 |
| --- | --- | --- |
| Kernel | `4.9.113 #65 SMP PREEMPT Wed Feb 26 15:15:07 CST 2025`, `armv7l` | `4.9.113 #1 SMP PREEMPT Thu Oct 21 04:52:56 CST 2021` |
| Bluetooth SDIO | `v0.0.1.13_2020092401`, anunciado en pstore | La misma versión en cadenas del módulo; `srcversion=C88552082DB51FD32CE2B8F` |
| Firmware WiFi | `t-neptune-customer-mt7663.mp1.2-msz.iptv-MT7663_E2_ASIC_ROM_RAM_Mobile-20190215101937`, manifest registrado en pstore | `t-neptune-mp-mt7663.mp-1827-GEN4M_MT7663_PC-20210308205502`, cadena del archivo candidato |

La versión Bluetooth anunciada coincide, pero los SHA no: **esa cadena no identifica un binario concreto ni demuestra que el defecto esté corregido.** La fecha de compilación del kernel candidato es anterior a la del instalado; no presentarlo como una actualización de kernel. Los nombres de firmware son evidencia de variantes distintas, no una evaluación de su compatibilidad.

El kernel candidato se inspeccionó descomprimiendo su contenido en memoria. SHA del campo kernel del boot: `51de4ded699adabff796fe9e363390c822f97ae8e792b6dff2c76bc64202054a`; SHA del contenido descomprimido: `a2370d65b35563c603695c2cc292fbfce55252d9b21b496db832407acbf9aa5d`. No se obtuvo un hash equivalente del kernel instalado: se comparan sus identificaciones de compilación, no sus bytes completos.

## Qué cambia la variante sin Bluetooth0.1.2

Por pedido del usuario, se retiraron aplicaciones Bluetooth, declaraciones de capacidades, arranque del HAL y carga de `btmtksdio.ko`, además del propio módulo. Se añadió `unavailable-feature` para Bluetooth y BLE. Así la preparación no depende de que una preferencia antigua `bluetooth_on` esté en cero. La [receta completa](../../rom-simplificada/instalador/preparar-sin-bluetooth-0.1.2.py) y su recibo detallan los cambios y límites.

Se conservaron el módulo WiFi, sus firmware/EEPROM, `wifi_preload`, `libwifi-hal.so`, servicios WiFi y supplicant. Las verificaciones locales comprobaron3486archivos restantes idénticos y ambos sistemas ext4 con código0. Estos controles acreditan que los componentes conservados no se modificaron durante esta revisión.

| Imagen | SHA256 |
| --- | --- |
| Vendor0.1.1 usado como fuente | `02d4e8b4cfa01feabf7be61edc8ff7f48129cb3fa5ba1a51f15aba61c687b976` |
| Vendor0.1.2 | `0882962989f38c81a99a9e623b7f1e339e45162b3f60d8e05eefd1215db20896` |
| System0.1.2 | `22bd6b617752415f13131a64f64330aa39e5a3713c05e6534322a3f72b01f45b` |
| Boot candidato, sin cambios en0.1.1/0.1.2 | `d7cfafa9b4978e72e63851a8f8f3b9eaf346bc4fb24b8bdb50ed02fcedf100ba` |

El boot todavía incluye los auxiliares `bt_device`/`input_btrcu` y sus nodos DT; esta variante no recompila el kernel ni cambia los pines compartidos del combo. **Sin Bluetooth operativo no equivale a eliminar toda referencia Bluetooth del kernel.**

## Información útil para la revisión conjunta

El panic adquirido sitúa la ejecución en `glResetTrigger.part.1` del módulo `wlan_mt7663_sdio`, con una cadena que pasa por `btmtk_main_serv` y notificación Bluetooth→WiFi. El módulo candidato también contiene los símbolos `glResetTrigger`, `BT_rst_L0_notify_WF_step1` y funciones relacionadas. La coincidencia de nombres acredita continuidad de la arquitectura; no identifica instrucciones iguales ni demuestra el mismo defecto.

El módulo WiFi candidato declara `depends=` vacío y no presenta símbolos Bluetooth externos sin resolver en su ELF. También contiene `kallsyms_on_each_symbol` y nombres de coordinación dinámica con Bluetooth. Esto favorece ensayar WiFi sin cargar el módulo Bluetooth, pero **no prueba independencia funcional del hardware ni éxito de esa configuración**.

Para profundizar en la comparación del código que falla, la siguiente lectura útil sería obtener los dos módulos `.ko` instalados como archivos normales y cotejar símbolos/instrucciones con los candidatos. No se necesita una lectura completa de particiones para esa comparación. No se han obtenido esos binarios actuales en esta revisión: sus hashes sí fueron leídos.

Esta comparación no atribuye el fallo a una actualización automática concreta, no localiza por sí sola el atasco OEM al2% y no acredita instalación, respaldo o recuperación de WiFi. Tampoco justifica reemplazar otro ZIP sin comprobar la entrada de instalación.
