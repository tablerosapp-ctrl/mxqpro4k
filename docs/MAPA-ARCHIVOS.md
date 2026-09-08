# Mapa de componentes y archivos

Generado por `herramientas/generar-mapa.py` desde [proyecto.json](proyecto.json). [Grafo visual](index.html) · [Árbol](ARBOL-ARCHIVOS.txt) · [Inventario completo](inventario.json).

La flecha expresa la relación indicada, no que se haya completado la prueba de destino. Los componentes propuestos aún no tienen archivos de implementación.

```mermaid
flowchart LR
    C_PERFIL["Perfil del equipo · observado_tv"]
    C_BASE["Candidato anterior · verificado_local"]
    C_CHROME["Chrome 138 · verificado_local"]
    C_INICIO["Inicio TV 0.2.0 · verificado_local"]
    C_ROM["ROM original P291 0.2.0 · verificado_local"]
    C_WEB["Proveedor WebView · verificado_local"]
    C_ZIP["ZIP instalación y restauración · verificado_local"]
    C_REC["Recovery original: entrada pendiente · verificado_local"]
    C_ENTRY["Diagnóstico USB0.8 · observado_tv"]
    C_USB["Kingston: entrega 0.1.2 histórica · verificado_local"]
    C_TV["P291: root y bloqueo WiFi confirmados · observado_tv"]
    C_APP["APK del producto · propuesto"]
    C_GESTION["Gestor propio 0.1 · verificado_local"]
    C_BTCTRL["Control Bluetooth normal · observado_tv"]
    C_ORIG["Originales del P291 · observado_tv"]
    C_PERFIL -->|"selecciona"| C_BASE
    C_CHROME -->|"motor admitido"| C_WEB
    C_INICIO -->|"se integra"| C_ROM
    C_WEB -->|"se integra"| C_ROM
    C_ROM -->|"se empaqueta"| C_ZIP
    C_ZIP -->|"copia 0.2.0 pendiente"| C_USB
    C_ENTRY -->|"se copia"| C_USB
    C_USB -->|"completar evidencia"| C_TV
    C_TV -->|"habilita validación"| C_APP
    C_APP -->|"actualización por contrato"| C_GESTION
    C_BTCTRL -->|"inhabilita Bluetooth actual"| C_TV
    C_TV -->|"respaldo por root"| C_ORIG
    C_ORIG -->|"fuente original verificada"| C_ROM
    C_GESTION -->|"gestor integrado"| C_ROM
    C_ORIG -->|"recovery adquirido"| C_REC
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
- [diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md)
- [diagnostico/primer-tv-complemento-20260907-003114/resumen-saneado.json](../diagnostico/primer-tv-complemento-20260907-003114/resumen-saneado.json)

### C-BASE · Candidato anterior

**verificado_local**. Fuente comunitaria histórica. Sus diferencias con los originales P291 impiden usarla como base de la revisión 0.2.0; se conserva para análisis.

Requisitos: REQ-02, REQ-05.

- [analisis-rom/manifiesto.json](../analisis-rom/manifiesto.json)
- [analisis-rom/RESULTADO.md](../analisis-rom/RESULTADO.md)
- [analisis-rom/candidato-android9.img](../analisis-rom/candidato-android9.img)
- [analisis-rom/inspeccionar-rom.py](../analisis-rom/inspeccionar-rom.py)
- [analisis-rom/verificar-integridad-interna.py](../analisis-rom/verificar-integridad-interna.py)
- [analisis-rom/integridad-interna.json](../analisis-rom/integridad-interna.json)
- [rom-simplificada/inspeccion/inventariar-ext4.py](../rom-simplificada/inspeccion/inventariar-ext4.py)
- [diagnostico/primer-tv-lan-20260907-184926/COMPARACION-RADIOS.md](../diagnostico/primer-tv-lan-20260907-184926/COMPARACION-RADIOS.md)

### C-CHROME · Chrome 138

**verificado_local**. APK Google Monochrome ARM32. Integra navegador/motor; no demuestra proveedor efectivo en el TV.

Requisitos: REQ-04.

- [actualizacion-chrome/chrome-138.0.7204.179-arm32.apk](../actualizacion-chrome/chrome-138.0.7204.179-arm32.apk)
- [actualizacion-chrome/verificacion/LEEME.md](../actualizacion-chrome/verificacion/LEEME.md)

### C-INICIO · Inicio TV 0.2.0

**verificado_local**. Inicio propio con Ajustes TV y selección de APK por documentos/USB. Firma API28 comprobada; recorrido con mando pendiente.

Requisitos: REQ-03, REQ-10.

- [rom-simplificada/original-p291/componentes/inicio/Inicio.java](../rom-simplificada/original-p291/componentes/inicio/Inicio.java)
- [rom-simplificada/original-p291/componentes/inicio/AndroidManifest.xml](../rom-simplificada/original-p291/componentes/inicio/AndroidManifest.xml)
- [rom-simplificada/original-p291/compilar-componentes.py](../rom-simplificada/original-p291/compilar-componentes.py)
- [rom-simplificada/original-p291/COMPONENTES.json](../rom-simplificada/original-p291/COMPONENTES.json)

### C-ROM · ROM original P291 0.2.0

**verificado_local**. Cinco imágenes derivadas del P291 real: 34 APK conservadas, 51 retiradas y 5 agregadas. Kernel/DTB y drivers ajenos al recorte preservados. Android original depurado, no AOSP reconstruido.

Requisitos: REQ-01, REQ-03, REQ-13, REQ-14.

- [rom-simplificada/original-p291/README.md](../rom-simplificada/original-p291/README.md)
- [rom-simplificada/original-p291/construir.py](../rom-simplificada/original-p291/construir.py)
- [rom-simplificada/original-p291/product_ea.py](../rom-simplificada/original-p291/product_ea.py)
- [rom-simplificada/original-p291/boot.py](../rom-simplificada/original-p291/boot.py)
- [rom-simplificada/original-p291/inventariar-originales.py](../rom-simplificada/original-p291/inventariar-originales.py)
- [rom-simplificada/original-p291/politica-paquetes.json](../rom-simplificada/original-p291/politica-paquetes.json)
- [rom-simplificada/original-p291/AUDITORIA-SERVICIOS.md](../rom-simplificada/original-p291/AUDITORIA-SERVICIOS.md)
- [rom-simplificada/original-p291/seleccion-servicios.json](../rom-simplificada/original-p291/seleccion-servicios.json)
- [rom-simplificada/original-p291/IMAGENES-0.2.0.json](../rom-simplificada/original-p291/IMAGENES-0.2.0.json)
- [docs/evidencia/ROM-ORIGINAL-P291-020.md](../docs/evidencia/ROM-ORIGINAL-P291-020.md)
- [rom-simplificada/original-p291/verificar-composicion.py](../rom-simplificada/original-p291/verificar-composicion.py)
- [rom-simplificada/original-p291/COMPOSICION-VERIFICADA.json](../rom-simplificada/original-p291/COMPOSICION-VERIFICADA.json)
- [rom-simplificada/original-p291/INCIDENTES-CONSTRUCCION.md](../rom-simplificada/original-p291/INCIDENTES-CONSTRUCCION.md)

### C-WEB · Proveedor WebView

**verificado_local**. Chrome138 declarado como único proveedor; WebView66 retirado. Overlays compilados y presentes en imagen; proveedor efectivo, dos VP9/alfa/canvas y rendimiento pendientes.

Requisitos: REQ-04, REQ-05, REQ-06.

- [rom-simplificada/original-p291/componentes/webview-overlay/AndroidManifest.xml](../rom-simplificada/original-p291/componentes/webview-overlay/AndroidManifest.xml)
- [rom-simplificada/original-p291/componentes/webview-overlay/res/xml/config_webview_packages.xml](../rom-simplificada/original-p291/componentes/webview-overlay/res/xml/config_webview_packages.xml)
- [rom-simplificada/original-p291/componentes/defaults/AndroidManifest.xml](../rom-simplificada/original-p291/componentes/defaults/AndroidManifest.xml)
- [rom-simplificada/original-p291/componentes/defaults/res/values/defaults.xml](../rom-simplificada/original-p291/componentes/defaults/res/values/defaults.xml)
- [rom-simplificada/original-p291/COMPONENTES.json](../rom-simplificada/original-p291/COMPONENTES.json)

### C-ZIP · ZIP instalación y restauración

**verificado_local**. Dos paquetes 0.2.0 con geometría original y firma SHA1 acorde a la clave v1. Payloads SHA256, CRC y firma Python/OpenJDK verificados; aceptación física pendiente. Instalación exige userdata limpia, sin borrarla.

Requisitos: REQ-01, REQ-09, REQ-11.

- [rom-simplificada/original-p291/empaquetado/README.md](../rom-simplificada/original-p291/empaquetado/README.md)
- [rom-simplificada/original-p291/empaquetado/main_linux.go](../rom-simplificada/original-p291/empaquetado/main_linux.go)
- [rom-simplificada/original-p291/empaquetado/package.go](../rom-simplificada/original-p291/empaquetado/package.go)
- [rom-simplificada/original-p291/empaquetado/data_policy.go](../rom-simplificada/original-p291/empaquetado/data_policy.go)
- [rom-simplificada/original-p291/empaquetado/package_test.go](../rom-simplificada/original-p291/empaquetado/package_test.go)
- [rom-simplificada/original-p291/empaquetado/empaquetar_original.py](../rom-simplificada/original-p291/empaquetado/empaquetar_original.py)
- [rom-simplificada/original-p291/empaquetado/firma_ota_v1.py](../rom-simplificada/original-p291/empaquetado/firma_ota_v1.py)
- [rom-simplificada/original-p291/empaquetado/EVIDENCIA-TESTS.json](../rom-simplificada/original-p291/empaquetado/EVIDENCIA-TESTS.json)
- [rom-simplificada/original-p291/empaquetado/salida/TVBASE-P291-A9-0.2.0-VERIFICACION.json](../rom-simplificada/original-p291/empaquetado/salida/TVBASE-P291-A9-0.2.0-VERIFICACION.json)
- [rom-simplificada/original-p291/empaquetado/salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.0-VERIFICACION.json](../rom-simplificada/original-p291/empaquetado/salida/TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.0-VERIFICACION.json)

### C-REC · Recovery original: entrada pendiente

**verificado_local**. Recovery real adquirido: clave v1 y geometría conocidas. ZIP nuevos compatibles con esa política en pruebas PC; entrada/aceptación física sin demostrar. Recovery externo anterior es histórico.

Requisitos: REQ-11.

- [diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md](../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md)
- [diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md](../diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md)
- [rom-simplificada/original-p291/empaquetado/EVIDENCIA-TESTS.json](../rom-simplificada/original-p291/empaquetado/EVIDENCIA-TESTS.json)

### C-ENTRY · Diagnóstico USB0.8

**observado_tv**. 0.8 ejecutada:25sellos de datos válidos; cierre vacío pese al aviso de fin. Corrección de persistencia pendiente, no repetir captura.

Requisitos: REQ-11.

- [rom-simplificada/componentes/acceso-usb-0.8/Acceso.java](../rom-simplificada/componentes/acceso-usb-0.8/Acceso.java)
- [rom-simplificada/componentes/acceso-usb-0.8/AdbLocal.java](../rom-simplificada/componentes/acceso-usb-0.8/AdbLocal.java)
- [rom-simplificada/componentes/acceso-usb-0.8/AndroidManifest.xml](../rom-simplificada/componentes/acceso-usb-0.8/AndroidManifest.xml)
- [rom-simplificada/componentes/acceso-usb-0.8/Evidencia.java](../rom-simplificada/componentes/acceso-usb-0.8/Evidencia.java)
- [rom-simplificada/componentes/acceso-usb-0.8/EvidenciaScripts.java](../rom-simplificada/componentes/acceso-usb-0.8/EvidenciaScripts.java)
- [rom-simplificada/componentes/acceso-usb-0.8/generar-scripts.py](../rom-simplificada/componentes/acceso-usb-0.8/generar-scripts.py)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-0.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-0.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-1.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-1.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-10.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-10.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-2.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-2.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-3.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-3.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-4.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-4.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-5.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-5.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-6.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-6.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-7.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-7.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-8.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-8.sh)
- [rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-9.sh](../rom-simplificada/componentes/acceso-usb-0.8/scripts/etapa-9.sh)
- [rom-simplificada/compilacion/acceso-usb-0.8/componente.json](../rom-simplificada/compilacion/acceso-usb-0.8/componente.json)
- [rom-simplificada/instalador/compilar-evidencia08.py](../rom-simplificada/instalador/compilar-evidencia08.py)
- [rom-simplificada/instalador/test_evidencia08.py](../rom-simplificada/instalador/test_evidencia08.py)
- [rom-simplificada/instalador/EvidenciaHarness08.java](../rom-simplificada/instalador/EvidenciaHarness08.java)
- [rom-simplificada/instalador/EVIDENCIA-TESTS-0.8.json](../rom-simplificada/instalador/EVIDENCIA-TESTS-0.8.json)

### C-USB · Kingston: entrega 0.1.2 histórica

**verificado_local**. La última copia comprobada conserva 0.1.2; no repetir Update. No se copió 0.2.0 ni se formateó el USB en esta construcción.

Requisitos: REQ-01.

- [preparacion-usb/preparar-postintento-08.ps1](../preparacion-usb/preparar-postintento-08.ps1)
- [preparacion-usb/postintento-08-estado.json](../preparacion-usb/postintento-08-estado.json)
- [rom-simplificada/instalador/LEEME-POSTINTENTO-0.8.txt](../rom-simplificada/instalador/LEEME-POSTINTENTO-0.8.txt)
- [rom-simplificada/INSTALACION-USB.md](../rom-simplificada/INSTALACION-USB.md)
- [preparacion-usb/preparar-rom-012.ps1](../preparacion-usb/preparar-rom-012.ps1)
- [preparacion-usb/rom-012-estado.json](../preparacion-usb/rom-012-estado.json)
- [rom-simplificada/instalador/LEEME-ROM-0.1.2.txt](../rom-simplificada/instalador/LEEME-ROM-0.1.2.txt)

### C-TV · P291: root y bloqueo WiFi confirmados

**observado_tv**. P291: root incorporado confirmado. Cierre espera estadísticasWiFi cuyo hilo espera arranqueHAL; ZIPinterno íntegro yblock.map ausente.

Requisitos: REQ-13.

- [docs/ESTADO.md](../docs/ESTADO.md)
- [diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md](../diagnostico/primer-tv-evidencia-20260907-000948/HALLAZGOS.md)
- [diagnostico/primer-tv-evidencia-20260907-000948/resumen-saneado.json](../diagnostico/primer-tv-evidencia-20260907-000948/resumen-saneado.json)
- [diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md](../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md)
- [diagnostico/primer-tv-complemento-20260907-003114/resumen-saneado.json](../diagnostico/primer-tv-complemento-20260907-003114/resumen-saneado.json)
- [diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json](../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json)
- [diagnostico/primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md](../diagnostico/primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md)
- [rom-simplificada/instalador/EVIDENCIA-TESTS-0.6.json](../rom-simplificada/instalador/EVIDENCIA-TESTS-0.6.json)
- [diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md](../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md)
- [diagnostico/primer-tv-update-20260907-1326/resumen-saneado.json](../diagnostico/primer-tv-update-20260907-1326/resumen-saneado.json)
- [docs/COLABORACION.md](../docs/COLABORACION.md)
- [docs/ENTREGA-FABLE.md](../docs/ENTREGA-FABLE.md)
- [docs/hipotesis/H1-CIERRE-ANDROID.md](../docs/hipotesis/H1-CIERRE-ANDROID.md)
- [docs/hipotesis/H2-PREPARACION-RECOVERY.md](../docs/hipotesis/H2-PREPARACION-RECOVERY.md)
- [docs/hipotesis/H1-RESULTADO-CODEX.md](../docs/hipotesis/H1-RESULTADO-CODEX.md)
- [diagnostico/h1-cierre-android/resumen-saneado.json](../diagnostico/h1-cierre-android/resumen-saneado.json)
- [diagnostico/h1-cierre-android/analizar-registro.py](../diagnostico/h1-cierre-android/analizar-registro.py)
- [diagnostico/h1-cierre-android/test_analizar_registro.py](../diagnostico/h1-cierre-android/test_analizar_registro.py)
- [docs/hipotesis/REVISION-CONJUNTA-FABLE.md](../docs/hipotesis/REVISION-CONJUNTA-FABLE.md)
- [diagnostico/fable-20260907/resumen-saneado.json](../diagnostico/fable-20260907/resumen-saneado.json)
- [diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md](../diagnostico/primer-tv-postintento-20260907-183025/HALLAZGOS.md)
- [diagnostico/primer-tv-postintento-20260907-183025/resumen-saneado.json](../diagnostico/primer-tv-postintento-20260907-183025/resumen-saneado.json)
- [diagnostico/revision-postintento/analizar-captura08.py](../diagnostico/revision-postintento/analizar-captura08.py)
- [diagnostico/revision-postintento/test_captura08.py](../diagnostico/revision-postintento/test_captura08.py)
- [diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md](../diagnostico/primer-tv-lan-20260907-184926/HALLAZGOS.md)
- [diagnostico/primer-tv-lan-20260907-184926/resumen-saneado.json](../diagnostico/primer-tv-lan-20260907-184926/resumen-saneado.json)
- [diagnostico/primer-tv-lan-20260907-184926/COMPARACION-RADIOS.md](../diagnostico/primer-tv-lan-20260907-184926/COMPARACION-RADIOS.md)
- [diagnostico/observacion-lan/capturar-log.py](../diagnostico/observacion-lan/capturar-log.py)
- [diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md](../diagnostico/primer-tv-lan-20260907-184926/ROOT-RESULTADO.md)
- [diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md](../diagnostico/primer-tv-lan-20260907-184926/ANALISIS-UPDATE-012.md)
- [diagnostico/respaldar-p291-lan.py](../diagnostico/respaldar-p291-lan.py)
- [diagnostico/primer-tv-lan-20260907-184926/RESPALDO-resumen-saneado.json](../diagnostico/primer-tv-lan-20260907-184926/RESPALDO-resumen-saneado.json)
- [diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md](../diagnostico/primer-tv-lan-20260907-184926/OPCIONES-INSTALACION-ROOT.md)

### C-APP · APK del producto

**propuesto**. Flutter más sistema web, videos persistentes y detección de capacidades. La app final no bloquea la plataforma.

Requisitos: REQ-07, REQ-08, REQ-12.

Implementación pendiente; especificación en [ESPECIFICACION](ESPECIFICACION.md) y propuestas en [ROADMAP](ROADMAP.md).

### C-GESTION · Gestor propio 0.1

**verificado_local**. APK para actualizaciones de aplicaciones y Chrome, 38 pruebas host y revisión independiente. Integrado como priv-app con permiso acotado. Desactivado, sin endpoint; no hay prueba Android ni OTA completa.

Requisitos: REQ-07, REQ-09, REQ-14.

- [rom-simplificada/componentes/gestion-tvbase/README.md](../rom-simplificada/componentes/gestion-tvbase/README.md)
- [rom-simplificada/componentes/gestion-tvbase/AndroidManifest.xml](../rom-simplificada/componentes/gestion-tvbase/AndroidManifest.xml)
- [rom-simplificada/componentes/gestion-tvbase/ManagerEngine.java](../rom-simplificada/componentes/gestion-tvbase/ManagerEngine.java)
- [rom-simplificada/componentes/gestion-tvbase/UpdateCore.java](../rom-simplificada/componentes/gestion-tvbase/UpdateCore.java)
- [rom-simplificada/componentes/gestion-tvbase/UpdateJob.java](../rom-simplificada/componentes/gestion-tvbase/UpdateJob.java)
- [rom-simplificada/componentes/gestion-tvbase/MainActivity.java](../rom-simplificada/componentes/gestion-tvbase/MainActivity.java)
- [rom-simplificada/original-p291/gestion/README.md](../rom-simplificada/original-p291/gestion/README.md)
- [rom-simplificada/original-p291/gestion/manifest_tool.py](../rom-simplificada/original-p291/gestion/manifest_tool.py)
- [rom-simplificada/original-p291/gestion/LIBERACION.json](../rom-simplificada/original-p291/gestion/LIBERACION.json)
- [rom-simplificada/original-p291/gestion/pruebas-resultado.json](../rom-simplificada/original-p291/gestion/pruebas-resultado.json)
- [rom-simplificada/original-p291/REVISION-GESTOR.md](../rom-simplificada/original-p291/REVISION-GESTOR.md)

### C-BTCTRL · Control Bluetooth normal

**observado_tv**. API normal guardaOFF; paquete de fábrica inhabilitado por operador y ajuste persistente tras apagado. No es instaladorROM.

Requisitos: REQ-13.

- [rom-simplificada/componentes/control-bluetooth-0.1/README.md](../rom-simplificada/componentes/control-bluetooth-0.1/README.md)
- [rom-simplificada/componentes/control-bluetooth-0.1/AndroidManifest.xml](../rom-simplificada/componentes/control-bluetooth-0.1/AndroidManifest.xml)
- [rom-simplificada/componentes/control-bluetooth-0.1/ControlActivity.java](../rom-simplificada/componentes/control-bluetooth-0.1/ControlActivity.java)
- [rom-simplificada/instalador/compilar-control-bluetooth.py](../rom-simplificada/instalador/compilar-control-bluetooth.py)
- [rom-simplificada/compilacion/control-bluetooth-0.1/componente.json](../rom-simplificada/compilacion/control-bluetooth-0.1/componente.json)

### C-ORIG · Originales del P291

**observado_tv**. Doce particiones seleccionadas (2538 MiB) verificadas; fuente de la ROM y ZIP de restauración. No incluye userdata/cache ni toda eMMC; restauración física pendiente.

Requisitos: REQ-02, REQ-09, REQ-11.

- [diagnostico/primer-tv-lan-20260907-184926/RESPALDO-resumen-saneado.json](../diagnostico/primer-tv-lan-20260907-184926/RESPALDO-resumen-saneado.json)
- [diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md](../diagnostico/primer-tv-lan-20260907-184926/RECOVERY-ORIGINAL.md)
- [diagnostico/respaldar-p291-lan.py](../diagnostico/respaldar-p291-lan.py)
- [diagnostico/test_respaldo_p291_lan.py](../diagnostico/test_respaldo_p291_lan.py)
- [diagnostico/respaldo-p291-lan/EVIDENCIA-SANEADA.json](../diagnostico/respaldo-p291-lan/EVIDENCIA-SANEADA.json)

## Directorios y cuidado

| Ruta | Función | Regla |
| --- | --- | --- |
| `analisis-rom/` | Fuente community e inspección | Conservar original y manifiesto |
| `rom-simplificada/componentes/` | Fuente de APK propias | Versionar cambios y conservar firma |
| `rom-simplificada/trabajo/` | RAW activos y recetas aplicadas | No son respaldo original del TV |
| `rom-simplificada/instalador/` | ZIP, recovery externo y pruebas | Revisar versión antes de reconstruir |
| `rom-simplificada/salida/` | Releases históricas 0.1.x | Conservar; no repetir su instalación |
| `rom-simplificada/original-p291/` | ROM 0.2.0, selección, gestor y empaquetado | Fuentes y recibos versionados; privados excluidos |
| `rom-simplificada/original-p291/empaquetado/salida/` | ZIP de instalación y restauración | Locales, no sustituyen una recuperación probada |
| `privado/TVBASE-respaldo-*/` | Adquisiciones originales P291 | Inmutables; no publicar ni confundir con userdata |
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
| diagnostico | 173 | 0.018 |
| docs | 32 | 0.000 |
| dossier-s905l2.html | 1 | 0.000 |
| images | 1 | 1.352 |
| platform-tools-latest-windows.zip | 1 | 0.008 |
| preparacion-usb | 83 | 3.688 |
| rom-simplificada | 4480 | 11.567 |
| tools | 18081 | 1.141 |

El inventario excluye derivados documentales y contenido de claves; los tamaños son de archivos, no bloques físicos ocupados. Los temporales retirados se detallan en [LIMPIEZA](LIMPIEZA.md).
