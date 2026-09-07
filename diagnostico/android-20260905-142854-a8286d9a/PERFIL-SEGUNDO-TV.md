# Segundo TV box: perfil observado el 5/9/2026

Este es el equipo ofrecido para diagnostico con WiFi funcional. **Su DT real es `gxlx_p271_1g`; no es el identificador P291 del equipo original.** Se analizaron archivos ya recogidos: no se accedio a ADB ni se modifico el aparato durante este analisis.

## Plataforma y controladores

| Aspecto | Evidencia observada |
|---|---|
| Producto | Droidlogic TVBOX, board/device/platform `ampere` |
| Android | 9, SDK 28, ABI `armeabi-v7a,armeabi` |
| Build | `Droidlogic/ampere/ampere:9/PPR1.180610.011/20260124:userdebug/test-keys` |
| Parche declarado | 2018-08-05; la fecha de build de 2026 no equivale a un parche actualizado |
| Kernel | 4.9.113, compilacion #55 del 24/1/2026, armv7l |
| Treble | `ro.treble.enabled=true`, VNDK 28; no demuestra por si solo compatibilidad completa de una GSI |
| GPU en uso | SurfaceFlinger: ARM Mali-450 MP, OpenGL ES 2.0; modulo `mali` cargado |
| Capa grafica instalada | `libGLES_mali.so`, `gralloc.amlogic.so`, `hwcomposer.amlogic.so` |
| Video | Modulos `vpu`, `amvdec_vp9`, `amvdec_h264`, `amvdec_h265`, `decoder_common`, `stream_input` y `media_clock` cargados |
| WiFi enlazado | Modulo `8822bs`, driver SDIO `rtl88x2bs`, IDs `024c:b822`, modalias `sdio:c07v024CdB822` |
| Entrada | `aml_keypad`, `aml_vkeypad`, `cec_input`, `input_btrcu` presentes |

El nodo DT WiFi declara solamente `amlogic, aml_wifi`: no identifica el chip fisico. La identificacion del controlador anterior procede del enlace real SDIO y del modulo cargado. La presencia de otros `.ko` en vendor tampoco implica que se esten usando.

Para video, tener `amvdec_vp9` cargado no demuestra que una reproduccion WebView concreta, especialmente VP9 con transparencia, emplee ese decodificador. El XML de codecs incluye entradas VP9 comentadas y otras de actualizacion; el funcionamiento real requiere observar el codec elegido durante la reproduccion. No se hizo esa prueba aqui.

## Memoria

La captura de `/proc/meminfo` muestra **983,42 MiB de MemTotal**, 286,01 MiB disponibles, **412 MiB de CMA**, de los cuales 174,44 MiB estaban libres, y unos 256 MiB de swap. Es una captura puntual, no una medicion de rendimiento.

El DT configura estas reservas/pools principales:

| Nodo | Tamano declarado |
|---|---:|
| `linux,codec_mm_cma` | 260 MiB |
| `linux,ion-dev` | 76 MiB |
| `linux,di_cma` | 40 MiB |
| `linux,vdin1_cma` | 16 MiB |
| `linux,meson-fb` | 8 MiB |
| `linux,secmon` | 4 MiB |
| `linux,demod` | 6 MiB |
| `ramoops` | 1 MiB |
| `linux,secos` | 32 MiB, con status `disable` |

Los pools reutilizables listados suman 404 MiB; el kernel reporta 412 MiB de CMA. No se leyo `/proc/cmdline` por denegacion de permisos y no se atribuye esa diferencia a una causa no comprobada. **CMA no debe restarse otra vez de MemTotal como si fuera RAM perdida.**

Ademas, el nodo DT `memory@00000000` declara 896 MiB, menor que el MemTotal observado. Esto impide tomar ese valor aislado como capacidad fisica exacta. El perfil conserva tanto la configuracion DT como las cifras reales del kernel, sin inventar una explicacion.

## Comparacion con el candidato descargado

| Aspecto | Segundo TV real | Candidato Android descargado |
|---|---|---|
| DT | **gxlx_p271_1g** | **gxlx2_p291_1g**, mas variantes P291/P295 |
| Producto | Droidlogic/ampere | Fiberhome/p291_iptv |
| Android/ABI | 9 / SDK 28 / ARM32 | 9 / SDK 28 / ARM32 |
| GPU configurada | Mali-450 | Mali-450 |
| WiFi | `8822bs` enlazado a SDIO `024c:b822` | Funcionamiento del controlador en nuestro equipo no probado |

Las coincidencias de Android y GPU no vuelven intercambiables los cargadores, configuracion DDR, DTB ni vendor. El candidato P291 sigue siendo referencia para el primer aparato; **su compatibilidad con este segundo P271 no esta confirmada**.

## Archivos de evidencia

Perfil estructurado: `perfil-segundo-tv.json`. Fuente DT: `devicetree-del-segundo-tv.tar`, 2544 entradas y 380 nodos con propiedades; no se extrajo a rutas del sistema.

SHA-256 del TAR: `55eb57870c9aeeee74c78bcc228528b20c7f4bda99c51e9d940c5639a66c5567`.

Lecturas complementarias: `propiedades.txt`, `kernel.txt`, `memoria.txt`, `gpu.txt`, `controladores-activos.txt`, `codecs.txt` y `entrada.txt`. El lector local reproducible es `perfilar-dt-local.py`.
