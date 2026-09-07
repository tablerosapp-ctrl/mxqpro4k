# Solo lectura del Android conectado. No instala, reinicia ni solicita root.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.:-]+$')][string]$Serial)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$adb=Join-Path $projectRoot 'tools\platform-tools\adb.exe'
if(-not (Test-Path -LiteralPath $adb)){throw 'No se encuentra ADB del proyecto.'}
$runDir=Join-Path $PSScriptRoot ('android-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
$null=New-Item -ItemType Directory -Path $runDir
$results=New-Object Collections.Generic.List[object]

function Invoke-Read([string]$Name,[string]$Command,[switch]$Transport) {
    # Las ordenes son literales de este archivo; ninguna incluye comillas dobles.
    if($Command.Contains('"')){throw 'Orden no admitida por el serializador acotado.'}
    $psi=New-Object Diagnostics.ProcessStartInfo
    $psi.FileName=$adb
    $psi.Arguments='-s ' + $Serial + $(if($Transport){' ' + $Command}else{' shell "' + $Command + '"'})
    $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $process=New-Object Diagnostics.Process
    $process.StartInfo=$psi
    if(-not $process.Start()){throw 'No se pudo iniciar la consulta ADB.'}
    $outTask=$process.StandardOutput.ReadToEndAsync(); $errTask=$process.StandardError.ReadToEndAsync()
    $expired=-not $process.WaitForExit(20000)
    if($expired){$process.Kill(); $process.WaitForExit()}
    $output=$outTask.GetAwaiter().GetResult(); $errorOutput=$errTask.GetAwaiter().GetResult()
    [IO.File]::WriteAllText((Join-Path $runDir ($Name + '.txt')),('Orden: ' + $Command + "`r`n`r`n" + $output + "`r`nSTDERR:`r`n" + $errorOutput),[Text.UTF8Encoding]::new($false))
    $result=[pscustomobject]@{consulta=$Name;codigo=$process.ExitCode;tiempo_agotado=$expired;salida=$output.Trim()}
    $results.Add([pscustomobject]@{consulta=$Name;codigo=$process.ExitCode;tiempo_agotado=$expired})
    return $result
}

$connection=Invoke-Read 'conexion' 'get-state' -Transport
if($connection.codigo -ne 0 -or $connection.salida -ne 'device'){throw ('El destino indicado no esta conectado y autorizado. Informe: ' + $runDir)}
$null=Invoke-Read 'permisos' 'id'
$null=Invoke-Read 'propiedades' 'for p in ro.product.model ro.product.manufacturer ro.product.brand ro.product.board ro.product.device ro.board.platform ro.hardware ro.boot.hardware ro.bootloader ro.build.fingerprint ro.build.description ro.build.version.release ro.build.version.sdk ro.build.version.security_patch ro.product.cpu.abilist ro.product.cpu.abilist32 ro.product.cpu.abilist64 ro.treble.enabled ro.vndk.version ro.build.ab_update ro.boot.slot_suffix ro.boot.verifiedbootstate ro.boot.flash.locked ro.boot.vbmeta.device_state; do printf ''%s='' $p; getprop $p; done'
$null=Invoke-Read 'cpu' 'cat /proc/cpuinfo'
$null=Invoke-Read 'memoria' 'cat /proc/meminfo'
$null=Invoke-Read 'kernel' 'uname -a; cat /proc/cmdline'
$null=Invoke-Read 'dt-identidad' 'for p in /proc/device-tree/amlogic-dt-id /proc/device-tree/model /proc/device-tree/compatible /sys/devices/soc0/soc_id /sys/devices/soc0/revision /sys/devices/soc0/family; do echo $p; cat $p 2>/dev/null; echo; done'
$null=Invoke-Read 'particiones' 'cat /proc/partitions; ls -l /dev/block/by-name /dev/block/platform/*/by-name 2>/dev/null; df -h /system /vendor /data'
$null=Invoke-Read 'vintf' 'for p in /vendor/etc/vintf/manifest.xml /vendor/manifest.xml /system/etc/vintf/manifest.xml; do echo $p; cat $p 2>/dev/null; done'
$null=Invoke-Read 'funciones' 'pm list features'
$null=Invoke-Read 'aplicaciones-sistema' 'pm list packages -s'
$null=Invoke-Read 'webview' 'dumpsys webviewupdate'
$null=Invoke-Read 'gpu' 'dumpsys SurfaceFlinger | grep -E ''GLES:|EGL_VERSION|GL_RENDERER|GL_VERSION'''
$null=Invoke-Read 'codecs' 'for p in /vendor/etc/media_codecs.xml /vendor/etc/media_codecs_performance.xml /system/etc/media_codecs.xml; do echo $p; cat $p 2>/dev/null; done'
$null=Invoke-Read 'entrada' 'cat /proc/bus/input/devices'
$null=Invoke-Read 'actualizador-local' 'cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER'

[ordered]@{
    fecha=(Get-Date).ToString('o');destino_adb=$Serial;modo='solo lectura';
    advertencia='Este informe pertenece exclusivamente al dispositivo consultado. No demuestra que su placa o firmware coincidan con el TV box original.';
    root_solicitado=$false;reinicio_solicitado=$false;firmware_modificado=$false;
    consultas=$results.ToArray()
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runDir 'informe.json') -Encoding UTF8
Write-Output $runDir
