# Identificación desde el arranque temporal

`recoger-hardware-linux.sh` está preparado para cuando el TV box logre arrancar Linux desde el pendrive. No se ejecuta en Windows y todavía no se ha ejecutado en el TV box.

Una vez que tengamos consola o acceso por Ethernet, copiar el archivo al sistema temporal y ejecutarlo con `sh recoger-hardware-linux.sh`. Con permisos de administrador podrá incluir más información del kernel; si falta una herramienta o permiso, lo registra y continúa.

El informe reúne identificadores de placa, CPU y memoria, controladores cargados, dispositivos de video, red y entrada, montajes y registros de ese arranque Linux. Solo escribe su informe en `/tmp`; no instala software, monta particiones, cambia el arranque ni modifica Android o la eMMC. Hay que copiar el informe a la PC antes de apagar.

Los datos ayudarán a identificar soporte para una base Android. El DTB de Linux utilizado y los controladores que cargue no prueban por sí solos el modelo de placa ni la compatibilidad de los componentes de Android. La decodificación y las funciones WebView se probarán después desde Android con una batería general, sin esperar a la APK terminada del producto.
