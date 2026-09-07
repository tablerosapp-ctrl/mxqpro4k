# Colisión del nombre hash en Acceso USB0.5

7/9/2026. Los informes físicos0.5 mostraron campos SHA vacíos en las copias de pstore/APK. La comparación aceptó esos campos iguales; **aquella comprobación no verificó la integridad de las copias**. Un resultado de lectura en PC tiene que documentarse por separado, sin corregir retroactivamente los registros originales.

## Mecanismo identificado

Android9 mksh define automáticamente un alias `hash` que invoca `builtin alias -t`, para mantener la caché de rutas de ejecutables. No calcula un digest. El lexer permite definir `hash() { ... }` porque distingue el nombre seguido de `()`, pero expande el alias al invocar `hash archivo`. La función que calculaba y validaba el SHA nunca llega a ejecutarse.

La operación `alias -t` puede terminar con código0 y sin salida incluso si no encuentra el supuesto ejecutable. Por eso `tv_before`, `tv_after` y `tv_copyhash` quedaron vacíos, los tres códigos de salida fueron0 y la comparación entre los tres textos aceptó la copia. Las comprobaciones de longitud y hexadecimal estaban dentro de la función eludida; faltaba verificarlas también al recibir su resultado.

Fuentes primarias de **Android9, etiqueta `android-9.0.0_r1`**:

- [main.c](https://android.googlesource.com/platform/external/mksh/+/android-9.0.0_r1/src/main.c), línea74: inicialización del alias.
- [lex.c](https://android.googlesource.com/platform/external/mksh/+/android-9.0.0_r1/src/lex.c), líneas1032–1060: expansión del alias salvo la posición de definición de función.
- [funcs.c](https://android.googlesource.com/platform/external/mksh/+/android-9.0.0_r1/src/funcs.c), `c_alias`: tratamiento de alias rastreados; ausencia de salida/error cuando no se obtiene una ruta ejecutable.
- [check.t](https://android.googlesource.com/platform/external/mksh/+/android-9.0.0_r1/src/check.t), casos `aliases-funcdef-1` y `aliases-funcdef-2`: la salida esperada es el alias. La descripción histórica de esos casos dice lo contrario; prevalecen el código y la salida esperada.

## Reproducción local

Se obtuvo el [paquete oficial Cygwin mksh56c-1](https://cygwin.com/pub/cygwin/x86_64/release/mksh/mksh-56c-1.tar.xz), comprobado contra su [SHA512 publicado](https://cygwin.com/pub/cygwin/x86_64/release/mksh/sha512.sum). El ejecutable informa `MIRBSD KSH R56 2018/01/14`. Está únicamente en `tools/mksh-audit/`, con la biblioteca Cygwin local; no se instaló en Windows ni en el pendrive.

SHA256 del paquete: `40aebbc4b573c364815b907f857d3c2197b2a41c5518b3ee695ca0a3fb118506`.

Prueba mínima desde PowerShell, sin acceso al TV ni al USB:

```powershell
@'
hash() { print -r -- FUNCTION_WAS_CALLED; }
a=$(hash /missing-source); ra=$?
b=$(hash /missing-source); rb=$?
c=$(hash /missing-copy); rc=$?
if [ "$a" = "$b" ] && [ "$a" = "$c" ]; then accepted=yes; else accepted=no; fi
print -r -- "lengths=${#a},${#b},${#c};statuses=$ra,$rb,$rc;accepted=$accepted"
'@ | & './tools/mksh-audit/mksh.exe' -s
```

Salida observada: `lengths=0,0,0;statuses=0,0,0;accepted=yes`. No aparece `FUNCTION_WAS_CALLED`.

La regresión local `tools/mksh-audit/REGRESION-ALIAS.json` conserva seis casos: reproduce la aceptación errónea, confirma que una función con prefijo propio se ejecuta con el alias predeterminado y con `hash=':'`, y comprueba rechazo de digest vacío, no hexadecimal y comando fallido desde el código que recibe el resultado. Los valores de prueba son sintéticos: esta regresión aísla el mecanismo y **no valida los scripts finales0.6 ni sus copias físicas**. Las versiones R56 de Cygwin y Android9 respaldan el comportamiento; no se extrajo ni identificó el binario de shell instalado en el P291.

## Corrección y prueba exigida

Usar nombres propios `tvbase_*`, evitar el nombre `hash` y verificar explícitamente64 caracteres hexadecimales antes de comparar o escribir el manifiesto. El código que recibe cada digest también debe rechazar vacío, formato inválido y error del proveedor. Un autocontrol SHA conocido antes de copiar permite detectar un proveedor inesperado.

La versión corregida debe ejecutar sus funciones reales bajo este mksh con el alias predeterminado activo, además de los casos vacío/malformado/fallo. Los tests previos basados en MinGit y adaptadores no reproducían este comportamiento de mksh; aprobarlos no probaba la compatibilidad del shell Android. Registrar por separado compilación, prueba de shell, copia USB y resultado físico.
