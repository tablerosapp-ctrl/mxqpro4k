# Incidencias funcionales

## ISSUE-HOME-01 · La casita del control no vuelve al inicio

- **Estado:** informado por el usuario el 8/9/2026; sin corregir.
- **Equipo/base:** primer P291, plataforma TV Base 0.2.0 instalada mediante el ZIP 0.2.2.
- **Comportamiento esperado:** al pulsar Home desde una aplicación, volver al menú principal de TV Base.
- **Comportamiento observado:** el usuario informa que ese botón no lo lleva al menú. No se ha capturado todavía el evento del control ni la aplicación de inicio resuelta por Android.
- **Prioridad:** primer problema funcional a revisar después del OK del usuario. La instalación y el WiFi funcionan según la evidencia y el reporte recibidos; la prueba de la APK continúa a cargo del usuario.

El [manifiesto de Inicio TV](../rom-simplificada/original-p291/componentes/inicio/AndroidManifest.xml) ya declara `MAIN`, `HOME` y `DEFAULT`. Esto permite registrarlo como aplicación de inicio, pero no prueba qué evento entrega la tecla física, qué aplicación selecciona Android ni si una política heredada intercepta el botón. No atribuir el problema solamente a la APK o al driver sin comprobar esa cadena.

La [revisión local de HOME](hipotesis/HOME-P291.md) encontró una hipótesis prioritaria en el framework original conservado: la ruta del botón puede bloquear el inicio de la actividad si Android considera pendiente la configuración inicial del usuario. El overlay establece `device_provisioned`, pero falta comprobar los valores efectivos de `user_setup_complete` y `tv_user_setup_complete` en el TV. Los 48 mapas de teclas conservan sus bytes originales; todavía se desconoce cuál usa esta pulsación. Es una hipótesis documentada, sin causa confirmada ni corrección aplicada.

La próxima revisión propuesta debe distinguir entrada del control → política de Android → selección de Home → apertura del launcher. Comparar el botón físico con la apertura normal de Home, consultar la selección efectiva y observar un evento del control requiere acceso y prueba física posteriores. No se implementa ni ejecuta ahora, por pedido del usuario.

Criterio de cierre: volver al inicio con el botón físico desde Ajustes, Chrome y la APK del producto, tanto tras iniciar el equipo como después de usarlo; conservar evidencia de la corrección y comprobar que Back/flechas/Aceptar siguen funcionando. No cerrar la incidencia porque el launcher aparezca durante el arranque.

Relaciona REQ-02/03/10, C-INICIO/C-PERFIL/C-TV, VAL-08 y M3. [Estado](ESTADO.md) · [Plan de lotes y actualizaciones, pendiente de OK](PROPUESTA-LOTES-Y-ACTUALIZACIONES.md).
