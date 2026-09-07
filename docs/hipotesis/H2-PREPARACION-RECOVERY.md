# H2 · Preparación persistente y acceso a recovery

Responsable previsto: Fable5.1 desde Claude Desktop. Estado: **hipótesis abierta; todavía sin revisión de Fable recibida**.

## Enunciado

La copia interna, el mapa de bloques, BCB o la aceptación del recovery no quedan en un estado válido. Aunque se supere el cierre de Android, la orden de actualización podría no alcanzar un instalador capaz de ejecutar el ZIP.

## Material principal

- [Análisis del APK real P291](../../diagnostico/primer-tv-complemento-20260907-003114/analisis-actualizador/ANALISIS.md).
- [Firma integral contra certificados del P291](../../diagnostico/primer-tv-complemento-20260907-003114/certificados-ota.json).
- [Captura completa y límites de configuración](../../diagnostico/primer-tv-complemento-20260907-003114/HALLAZGOS.md).
- [Contrato del instalador](../../rom-simplificada/instalador/README.md), main_linux.go, package.go y manifest-0.1.1.json en ese directorio.
- [Intento OEM real detenido](../../diagnostico/primer-tv-update-20260907-1326/HALLAZGOS.md).

## Preguntas separadas

1. ¿El APK acredita copia íntegra a /data/cache/update.zip o continúa después de errores? ¿Su interacción con command/uncrypt_file/BCB es válida en API28?
2. ¿Qué componente debería crear block.map y en qué momento? ¿Qué ocurriría si se corta la alimentación antes de ese trabajo? No asumir que el mapa existe.
3. ¿Qué prueba acredita que setupBcb persistió y que el bootloader instalado lo consulta? La referencia P271 no certifica la implementación P291.
4. ¿La ruta conduce al recovery interno o al recovery.img USB? La referencia BCB apunta al interno; no confundir con el ensayo anterior reboot:update.
5. ¿Qué puede afirmarse de la confianza del ZIP? otacerts del Android instalado no prueba las claves /res/keys del recovery. No proponer desactivar firmas para omitir esta distinción.
6. ¿El instalador0.1.1 interpreta correctamente el entorno recovery y exige los respaldos antes de escribir? No atribuir al payload un error ocurrido antes de ejecutarlo.

## Confirmación y refutación

Confirmaría una variante de H2: dato del mismo intento que demuestre copia incompleta, mapa ausente/inválido, orden BCB incorrecta, rechazo del bootloader o rechazo explícito de recovery. Refutaría esas variantes: hashes de copia/mapa/orden válidos y ejecución identificada del recovery que verifica y entra al instalador. La firma comprobada en PC, el nombre del ZIP o un arranque Android posterior no resuelven por sí solos la cadena.

Devolver la conclusión por eslabón: comprobado, inferido o no leído. Señalar el menor dato faltante que cambie una decisión. Priorizar una revisión reproducible; no ejecutar escrituras de partición, BCB, wipes ni nuevos reinicios. Coordinar con H1, porque ambas causas pueden coexistir.
