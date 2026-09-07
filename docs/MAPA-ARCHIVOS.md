# Mapa de componentes y archivos

Generado por `herramientas/generar-mapa.py` desde [proyecto.json](proyecto.json). [Grafo visual](index.html) · [Árbol](ARBOL-ARCHIVOS.txt) · [Inventario completo](inventario.json).

La flecha expresa la relación indicada, no que se haya completado la prueba de destino. Los componentes propuestos aún no tienen archivos de implementación.

```mermaid
flowchart LR
    C_PERFIL["Perfil del equipo · observado_tv"]
    C_BASE["Android candidato · verificado_local"]
    C_CHROME["Chrome 138 · verificado_local"]
    C_INICIO["Inicio TV · construido"]
    C_ROM["ROM simplificada · verificado_local"]
    C_WEB["Proveedor WebView · construido"]
    C_ZIP["ZIP de instalación · verificado_local"]
    C_REC["Recovery externo · verificado_local"]
    C_ENTRY["Complemento USB 0.6 · verificado_local"]
    C_USB["Kingston preparado · verificado_local"]
    C_TV["P291: cierre atascado · observado_tv"]
    C_APP["APK del producto · propuesto"]
    C_GESTION["Administración propia · propuesto"]
    C_PERFIL -->|"selecciona"| C_BASE
    C_BASE -->|"aporta hardware"| C_ROM
    C_CHROME -->|"motor admitido"| C_WEB
    C_INICIO -->|"se integra"| C_ROM
    C_WEB -->|"se integra"| C_ROM
    C_ROM -->|"se empaqueta"| C_ZIP
    C_BASE -->|"recovery fuente"| C_REC
    C_ZIP -->|"se copia"| C_USB
    C_REC -->|"se copia"| C_USB
    C_ENTRY -->|"se copia"| C_USB
    C_USB -->|"completar evidencia"| C_TV
    C_TV -->|"habilita validación"| C_APP
    C_APP -->|"contrato propuesto"| C_GESTION
```

## Archivos por componente

### C-PERFIL · Perfil del equipo

**observado_tv**. Primer TV P291 identificado por ADB local; segundo P271 solo diagnóstico. Capacidades físicas de la ROM nueva pendientes.

Requisitos: REQ-02, REQ-10.

- [dossier-s905l2.html](../dossier-s905l2.html)
- [diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md](../diagnostico/primer-tv-20260906-actualizacion-local/HALLAZGOS.md)
- [diagnostico/android-20260905-142854-a8286d9a/PERFIL-SEGUNDO-TV.md](../diagnostico/android-20260905-142854-a8286d9a/PERFIL-SEGUNDO-TV.md)
- [diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md](../diagnostico/primer-tv-reportes-20260906-233826/HALLAZGOS.md)
- [diagnostico/primer-tv-reportes-20260906-233826/resumen-saneado.json](../diagnostico/primer-tv-reportes-20260906-233826/resumen-saneado.json)
- [diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md)
- [diagnostico/primer-tv-evidencia-20260907-000948/resumen-saneado.json](../diagnostico/primer-tv-evidencia-20260907-000948/resumen-saneado.json)

### C-BASE · Android candidato

**verificado_local**. Base community Android9 P291 inspeccionada; compatibilidad física no confirmada.

Requisitos: REQ-02, REQ-05.

- [analisis-rom/manifiesto.json](../analisis-rom/manifiesto.json)
- [analisis-rom/RESULTADO.md](../analisis-rom/RESULTADO.md)
- [analisis-rom/candidato-android9.img](../analisis-rom/candidato-android9.img)
- [analisis-rom/inspeccionar-rom.py](../analisis-rom/inspeccionar-rom.py)
- [analisis-rom/verificar-integridad-interna.py](../analisis-rom/verificar-integridad-interna.py)
- [analisis-rom/integridad-interna.json](../analisis-rom/integridad-interna.json)
- [rom-simplificada/inspeccion/inventariar-ext4.py](../rom-simplificada/inspeccion/inventariar-ext4.py)

### C-CHROME · Chrome 138

**verificado_local**. APK Google Monochrome ARM32. Integra navegador/motor; no demuestra proveedor efectivo en el TV.

Requisitos: REQ-04.

- [actualizacion-chrome/chrome-138.0.7204.179-arm32.apk](../actualizacion-chrome/chrome-138.0.7204.179-arm32.apk)
- [actualizacion-chrome/verificacion/LEEME.md](../actualizacion-chrome/verificacion/LEEME.md)

### C-INICIO · Inicio TV

**construido**. Launcher propio y ajustes; recorrido físico con control pendiente.

Requisitos: REQ-03, REQ-10.

- [rom-simplificada/componentes/inicio/Inicio.java](../rom-simplificada/componentes/inicio/Inicio.java)
- [rom-simplificada/componentes/inicio/AndroidManifest.xml](../rom-simplificada/componentes/inicio/AndroidManifest.xml)
- [rom-simplificada/compilar-componentes.py](../rom-simplificada/compilar-componentes.py)

### C-ROM · ROM simplificada

**verificado_local**. Limpieza del integrador y revisión0.1.1 que neutraliza reemplazo heredado de recovery. Conserva APIs y hardware del candidato.

Requisitos: REQ-01, REQ-03.

- [rom-simplificada/LEEME.md](../rom-simplificada/LEEME.md)
- [rom-simplificada/preparar-copias.py](../rom-simplificada/preparar-copias.py)
- [rom-simplificada/simplificar.py](../rom-simplificada/simplificar.py)
- [rom-simplificada/verificar-y-empaquetar.py](../rom-simplificada/verificar-y-empaquetar.py)
- [rom-simplificada/trabajo/cambios.json](../rom-simplificada/trabajo/cambios.json)
- [rom-simplificada/instalador/corregir-recovery-0.1.1.py](../rom-simplificada/instalador/corregir-recovery-0.1.1.py)
- [rom-simplificada/trabajo/revision-0.1.1/revision.json](../rom-simplificada/trabajo/revision-0.1.1/revision.json)
- [rom-simplificada/trabajo/revision-0.1.1/system.raw.img](../rom-simplificada/trabajo/revision-0.1.1/system.raw.img)

### C-WEB · Proveedor WebView

**construido**. Overlay permite Chrome como proveedor; WebView66 queda de respaldo. Motor efectivo y composición por comprobar.

Requisitos: REQ-04, REQ-05, REQ-06.

- [rom-simplificada/componentes/webview-overlay/AndroidManifest.xml](../rom-simplificada/componentes/webview-overlay/AndroidManifest.xml)
- [rom-simplificada/componentes/webview-overlay/res/xml/config_webview_packages.xml](../rom-simplificada/componentes/webview-overlay/res/xml/config_webview_packages.xml)
- [rom-simplificada/INTEGRACION-WEBVIEW.md](../rom-simplificada/INTEGRACION-WEBVIEW.md)
- [rom-simplificada/fuentes-webview/fuentes.json](../rom-simplificada/fuentes-webview/fuentes.json)

### C-ZIP · ZIP de instalación

**verificado_local**. Cinco particiones, controles, respaldo completo previo y hashes de lectura. No A/B ni rollback automático.

Requisitos: REQ-01, REQ-09, REQ-11.

- [rom-simplificada/instalador/README.md](../rom-simplificada/instalador/README.md)
- [rom-simplificada/instalador/main_linux.go](../rom-simplificada/instalador/main_linux.go)
- [rom-simplificada/instalador/package.go](../rom-simplificada/instalador/package.go)
- [rom-simplificada/instalador/package_test.go](../rom-simplificada/instalador/package_test.go)
- [rom-simplificada/instalador/main_windows.go](../rom-simplificada/instalador/main_windows.go)
- [rom-simplificada/instalador/empaquetar.py](../rom-simplificada/instalador/empaquetar.py)
- [rom-simplificada/instalador/manifest-0.1.1.json](../rom-simplificada/instalador/manifest-0.1.1.json)
- [rom-simplificada/salida/TVBASE-P291-A9-0.1.1-RECOVERY.zip](../rom-simplificada/salida/TVBASE-P291-A9-0.1.1-RECOVERY.zip)
- [rom-simplificada/salida/RECOVERY-VERIFICACION-0.1.1.json](../rom-simplificada/salida/RECOVERY-VERIFICACION-0.1.1.json)
- [rom-simplificada/salida/RECOVERY-COMPROBACION-0.1.1.json](../rom-simplificada/salida/RECOVERY-COMPROBACION-0.1.1.json)

### C-REC · Recovery externo

**verificado_local**. Archivo para RAM preparado del candidato. Clave del ZIP agregada con verificación activa; bootloader real sin probar.

Requisitos: REQ-11.

- [rom-simplificada/instalador/preparar-recovery-externo.py](../rom-simplificada/instalador/preparar-recovery-externo.py)
- [rom-simplificada/instalador/inspeccionar-recovery-externo.py](../rom-simplificada/instalador/inspeccionar-recovery-externo.py)
- [rom-simplificada/inspeccion/recovery-original.img](../rom-simplificada/inspeccion/recovery-original.img)
- [rom-simplificada/instalador/recovery-externo/recovery.img](../rom-simplificada/instalador/recovery-externo/recovery.img)
- [rom-simplificada/instalador/recovery-externo/PREPARADO.json](../rom-simplificada/instalador/recovery-externo/PREPARADO.json)
- [rom-simplificada/instalador/gxl_p271_v1-referencia.h](../rom-simplificada/instalador/gxl_p271_v1-referencia.h)

### C-ENTRY · Complemento USB 0.6

**verificado_local**. Captura solo certificados OTA, APK OTAUpgrade P291 y configuración faltante. SHA estricto y autocontrol, mksh real. Sin reinicio ni GMS; prueba física pendiente.

Requisitos: REQ-11.

- [rom-simplificada/componentes/acceso-usb-0.6/Acceso.java](../rom-simplificada/componentes/acceso-usb-0.6/Acceso.java)
- [rom-simplificada/componentes/acceso-usb-0.6/AdbLocal.java](../rom-simplificada/componentes/acceso-usb-0.6/AdbLocal.java)
- [rom-simplificada/componentes/acceso-usb-0.6/Evidencia.java](../rom-simplificada/componentes/acceso-usb-0.6/Evidencia.java)
- [rom-simplificada/componentes/acceso-usb-0.6/EvidenciaScripts.java](../rom-simplificada/componentes/acceso-usb-0.6/EvidenciaScripts.java)
- [rom-simplificada/componentes/acceso-usb-0.6/generar-scripts.py](../rom-simplificada/componentes/acceso-usb-0.6/generar-scripts.py)
- [rom-simplificada/componentes/acceso-usb-0.6/AndroidManifest.xml](../rom-simplificada/componentes/acceso-usb-0.6/AndroidManifest.xml)
- [rom-simplificada/compilacion/acceso-usb-0.6/acceso-usb.apk](../rom-simplificada/compilacion/acceso-usb-0.6/acceso-usb.apk)
- [rom-simplificada/compilacion/acceso-usb-0.6/componente.json](../rom-simplificada/compilacion/acceso-usb-0.6/componente.json)
- [rom-simplificada/instalador/compilar-evidencia06.py](../rom-simplificada/instalador/compilar-evidencia06.py)
- [rom-simplificada/instalador/test_evidencia06.py](../rom-simplificada/instalador/test_evidencia06.py)
- [rom-simplificada/instalador/EvidenciaHarness06.java](../rom-simplificada/instalador/EvidenciaHarness06.java)
- [rom-simplificada/instalador/EVIDENCIA-TESTS-0.6.json](../rom-simplificada/instalador/EVIDENCIA-TESTS-0.6.json)
- [rom-simplificada/instalador/MKSH-HALLAZGO-0.5.md](../rom-simplificada/instalador/MKSH-HALLAZGO-0.5.md)

### C-USB · Kingston preparado

**verificado_local**. Copia por archivos con identidad estable. ROM/recovery y capturas0.5 preservados. APK0.6 complementa lo faltante sin reiniciar.

Requisitos: REQ-01.

- [preparacion-usb/preparar-evidencia-06.ps1](../preparacion-usb/preparar-evidencia-06.ps1)
- [preparacion-usb/evidencia-06-estado.json](../preparacion-usb/evidencia-06-estado.json)
- [rom-simplificada/instalador/LEEME-EVIDENCIA-0.6.txt](../rom-simplificada/instalador/LEEME-EVIDENCIA-0.6.txt)
- [rom-simplificada/INSTALACION-USB.md](../rom-simplificada/INSTALACION-USB.md)

### C-TV · P291: cierre atascado

**observado_tv**. Dos capturas0.5 parciales analizadas: pstore conserva517s de actividad tras aviso de reinicio. Sugiere atasco antes de reset, función desconocida. OTAUpgrade identificado, binario pendiente.

Requisitos: .

- [docs/ESTADO.md](../docs/ESTADO.md)
- [diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md)
- [diagnostico/primer-tv-evidencia-20260907-000948/resumen-saneado.json](../diagnostico/primer-tv-evidencia-20260907-000948/resumen-saneado.json)

### C-APP · APK del producto

**propuesto**. Flutter más sistema web, videos persistentes y detección de capacidades. La app final no bloquea la plataforma.

Requisitos: REQ-07, REQ-08, REQ-12.

Implementación pendiente; especificación en [ESPECIFICACION](ESPECIFICACION.md) y propuestas en [ROADMAP](ROADMAP.md).

### C-GESTION · Administración propia

**propuesto**. Actualizaciones independientes, catálogo, limpieza selectiva y despliegues por grupos. Aún sin implementación.

Requisitos: REQ-07, REQ-09.

Implementación pendiente; especificación en [ESPECIFICACION](ESPECIFICACION.md) y propuestas en [ROADMAP](ROADMAP.md).

## Directorios y cuidado

| Ruta | Función | Regla |
| --- | --- | --- |
| `analisis-rom/` | Fuente community e inspección | Conservar original y manifiesto |
| `rom-simplificada/componentes/` | Fuente de APK propias | Versionar cambios y conservar firma |
| `rom-simplificada/trabajo/` | RAW activos y recetas aplicadas | No son respaldo original del TV |
| `rom-simplificada/instalador/` | ZIP, recovery externo y pruebas | Revisar versión antes de reconstruir |
| `rom-simplificada/salida/` | Releases y evidencias | 0.1 retirada; 0.1.1 vigente |
| `preparacion-usb/` | Preparadores y recibos de operaciones | Usar identidad estable; no repetir por rutina |
| `diagnostico/` | Evidencia de ambos equipos | No mezclar perfiles P291 y P271 |
| `actualizacion-chrome/` | Chrome fuente y firmas | Conservar APK integrado y evidencia |
| `images/` | Armbian histórico comprimido | No es ROM Android ni ruta activa |
| `tools/` | Compiladores e inspección locales | Dependencias; no están instaladas en USB |
| `docs/` | Especificación, estado, grafo y roadmap | Regenerar mapa al cambiar relaciones |
| `rom-simplificada/claves-desarrollo/` | Firma local de APK | Privado; no mostrar contenidos |

## Inventario de tamaño

| Grupo | Archivos | GB decimales |
| --- | ---: | ---: |
| .gitattributes | 1 | 0.000 |
| .gitignore | 1 | 0.000 |
| AGENTS.md | 1 | 0.000 |
| ARQUITECTURA-ANDROID-TV.md | 1 | 0.000 |
| PRUEBA-USB.md | 1 | 0.000 |
| README.md | 1 | 0.000 |
| actualizacion-chrome | 51 | 0.417 |
| analisis-rom | 15 | 1.822 |
| diagnostico | 102 | 0.012 |
| docs | 21 | 0.000 |
| dossier-s905l2.html | 1 | 0.000 |
| images | 1 | 1.352 |
| platform-tools-latest-windows.zip | 1 | 0.008 |
| preparacion-usb | 74 | 3.688 |
| rom-simplificada | 1260 | 7.083 |
| tools | 18058 | 1.139 |

El inventario excluye derivados documentales y contenido de claves; los tamaños son de archivos, no bloques físicos ocupados. Los temporales retirados se detallan en [LIMPIEZA](LIMPIEZA.md).
