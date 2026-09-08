# Primera captura del P271 y bloqueo informado del MX9

El usuario devolvió Kingston tras una captura completada del P271 y un intento del equipo comercializado como MX9 5G. El USB contenía un ZIP P271 y su recibo; no había ZIP MX9 ni captura de recovery. Los originales, el recibo y la foto se copiaron en una carpeta privada nueva, con verificación de contenido y sin modificar el origen.

## P271 observado

ZIP de 69.460.957 bytes, SHA256 `3824c4355ec7f75d25dd09a5ca406c90cc017ceab3d45b14732c94f62a7e073f`. Se verificaron 2464 entradas ZIP y los 2463 archivos declarados en el manifiesto, 159.952.029 bytes expandidos. El recibo de exportación coincide con el ZIP y declara sincronización de archivo, pero no de directorio, mediante document provider. La adquisición íntegra en PC no convierte esa limitación histórica en sincronización acreditada.

El colector informa 53.698 ms: 466 archivos de plataforma (157.152.153 bytes) y 1985 propiedades DT (22.570 bytes), 2451 copias y 157.174.723 bytes. Registra 778 omisiones de política y 15 fuentes ausentes, sin errores/denegaciones/límites en esa fase. El inventario sysfs registra 714 observaciones, tres exclusiones y 1570 no disponibles; 1569 son ENOENT y una fuente no ordinaria. No son 1570 denegaciones de permisos.

| Observación | Resultado y alcance |
| --- | --- |
| Perfil | DT `gxlx_p271_1g`, Android 9/API 28, ABI ARM32. No identidad física certificada. |
| RAM visible | 1.031.192.576 bytes declarados por Android. |
| Memoria interna | MMC DG4008, 7.820.083.200 bytes por sysfs; P291 tiene 7.650.410.496 bytes. |
| Data | 3.665.625.088 bytes; P291 tiene 3.495.952.384 bytes. No trasladar geometría. |
| WiFi | Binding rtl88x2bs, SDIO 024c:b822 y módulo 8822bs Live. No prueba asociación ni tráfico. |
| Gráficos | Mali-450 MP/GLES 2 observados en proceso de reconocimiento. No benchmark. |
| WebView | Chrome 70.0.3538.80 cargado por reconocimiento 0.1; no por la APK del usuario. |
| Video | Lista Android de 50 codecs no anuncia VP9/AV1; módulo amvdec_vp9 Live presente. La discrepancia requiere prueba, no afirmar ausencia física ni reproducción. |

Esta captura agrega rutas canónicas, nombres lógicos, rdev declarado, número, inicio y tamaño de 20 particiones sin solapamiento. Supera la ausencia histórica de estos datos en Android; no acredita ioctl, descriptores o ejecución desde recovery. El plan privado se derivó del ZIP íntegro, sin offsets ni órdenes de escritura. Firma/entrada del recovery P271 siguen pendientes.

## MX9: corrección del reconocedor

El usuario confirmó más de 15 minutos sin cambiar los contadores antes de retirar el USB, por encima del límite cooperativo de 12 minutos. No identifica la llamada bloqueada. La foto muestra 1410 entradas y 1246 copias verificadas con 0 MB, resultado posible con propiedades pequeñas y división entera. 0.1 recorría todo el DT primero y sincronizaba/releía cada archivo. El mensaje de pantalla era el último progreso publicado, no la operación actual. Su límite cooperativo de 12 minutos no interrumpía llamadas de archivos bloqueadas; no podía exportar hasta acabar. No se obtuvo informe MX9 ni se conoce su SoC por la foto.

[Reconocedor 0.2](../reconocedor-0.2/README.md) separa ficha inicial sellada/exportada e inventario posterior, omite copia masiva y conserva límites explícitos. La copia profunda se prepara con el extractor por recovery compatible. No repetir captura P271 ni usar ROM P291 en él. No se ejecutó Update, reinicio, cambio de seguridad o instalación de ROM durante esta revisión.
