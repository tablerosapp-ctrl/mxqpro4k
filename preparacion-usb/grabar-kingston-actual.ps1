# Graba la imagen directamente desde la PC. No instala herramientas en el USB.
[CmdletBinding()]
param([switch]$ContinuarTrasFallo)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$expectedId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$expectedSize = [long]30943995904
$expectedHash = '4479b09374d92ffe4be625b5dded96c5d7d7a0e8c6bcb0a7d2894a839214a2f8'
$imagePath = Join-Path $projectRoot 'images\Armbian_26.05.0_amlogic_s905l2_noble_6.12.91_server_2026.06.01.img'
$imagerPath = Join-Path $projectRoot 'tools\imager-2.0.11.1\rpi-imager.exe'
$statusPath = Join-Path $PSScriptRoot 'estado-grabacion.json'
$previousState = if (Test-Path -LiteralPath $statusPath) { Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json } else { $null }
$runId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$runDir = Join-Path $PSScriptRoot ('grabacion-' + $runId)
$null = New-Item -ItemType Directory -Path $runDir
if (Test-Path -LiteralPath $statusPath) {
    Copy-Item -LiteralPath $statusPath -Destination (Join-Path $runDir 'estado-anterior.json')
}
$state = [ordered]@{estado='comprobando'; inicio=(Get-Date).ToString('o'); destino_id=$expectedId; imagen=$imagePath; herramienta=$imagerPath; version_herramienta='2.0.11.1'; directorio_informe=$runDir; verificacion=$true}

function Write-State([string]$phase, [string]$detail) {
    $state.estado = $phase
    $state.detalle = $detail
    $state.fecha = (Get-Date).ToString('o')
    $json = $state | ConvertTo-Json -Depth 5
    $json | Set-Content -LiteralPath (Join-Path $runDir 'resultado.json') -Encoding UTF8
    $tempPath = $statusPath + '.tmp'
    $json | Set-Content -LiteralPath $tempPath -Encoding UTF8
    Move-Item -LiteralPath $tempPath -Destination $statusPath -Force
}

function Get-ValidatedTarget {
    $disks = @(Get-Disk | Where-Object { $_.UniqueId -eq $expectedId })
    if ($disks.Count -ne 1) { throw 'No se encontro un unico Kingston con el identificador esperado.' }
    $disk = $disks[0]
    if ($disk.BusType -ne 'USB' -or $disk.Size -ne $expectedSize -or
        $disk.FriendlyName -ne 'Kingston DataTraveler 3.0' -or
        $disk.IsBoot -or $disk.IsSystem -or $disk.IsOffline -or $disk.IsReadOnly) {
        throw 'El destino no es un Kingston USB disponible y ajeno al disco del sistema.'
    }
    $parts = @(Get-Partition -DiskNumber $disk.Number)
    $accessibleParts = @($parts | Where-Object { [string]$_.DriveLetter -match '^[A-Za-z]$' })
    if ($accessibleParts.Count -eq 0 -and $ContinuarTrasFallo) {
        if (-not $previousState -or $previousState.estado -ne 'error' -or
            $previousState.destino_id -ne $expectedId -or $previousState.imagen -ne $imagePath -or
            $previousState.version_herramienta -ne '2.0.11.1') {
            throw 'La continuacion exige un fallo documentado de esta misma imagen y dispositivo.'
        }
        foreach ($part in $parts) {
            $rawVolume = $part | Get-Volume
            if ($rawVolume.FileSystem -or $rawVolume.Size -gt 0) {
                throw 'Hay un sistema de archivos sin letra; se requiere revisar su contenido antes de sobrescribir.'
            }
        }
        return [pscustomobject]@{Disk=$disk; Root='sin letra (imagen incompleta documentada)'; VolumeId=('incompleto:' + $expectedId)}
    }
    if ($parts.Count -ne 1 -or $accessibleParts.Count -ne 1) {
        throw 'El Kingston debe tener un volumen accesible para comprobar su contenido antes de grabar.'
    }
    $volume = $parts[0] | Get-Volume
    $root = [string]$parts[0].DriveLetter + ':\'
    $items = @(Get-ChildItem -LiteralPath $root -Force | Where-Object { $_.Name -notin @('System Volume Information','$RECYCLE.BIN') })
    if ($items.Count -ne 0) { throw ('El Kingston contiene archivos en ' + $root + '. Se detiene sin escribir.') }
    [pscustomobject]@{Disk=$disk; Root=$root; VolumeId=$volume.UniqueId}
}

function Start-LoggedProcess([string]$executable, [string]$arguments) {
    $startInfo = New-Object Diagnostics.ProcessStartInfo
    $startInfo.FileName = $executable
    $startInfo.Arguments = $arguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $startInfo
    if (-not $process.Start()) { throw 'No se pudo iniciar el proceso.' }
    # Conservar el objeto nativo y drenar ambas salidas evita perder ExitCode
    # con Start-Process -PassThru seguido de WaitForExit en Windows PowerShell.
    [pscustomobject]@{Process=$process; OutTask=$process.StandardOutput.ReadToEndAsync(); ErrorTask=$process.StandardError.ReadToEndAsync()}
}

try {
    Write-State 'comprobando' 'Verificando identidad estable del USB, contenido, imagen y herramienta actual.'
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'El grabador necesita permisos de administrador de Windows.' }
    if (@(Get-Process -Name 'rpi-imager','rufus*','robocopy' -ErrorAction SilentlyContinue).Count -ne 0) { throw 'Ya hay otra herramienta de escritura o copia abierta.' }
    $initial = Get-ValidatedTarget
    $signature = Get-AuthenticodeSignature -LiteralPath $imagerPath
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Raspberry Pi') {
        throw 'La firma del grabador actual no es valida.'
    }
    if ((Get-Item -LiteralPath $imagerPath).VersionInfo.ProductVersion -notmatch '^v?2\.0\.11\.1$') { throw 'Version de grabador inesperada.' }
    if ((Get-Item -LiteralPath $imagePath).Length -ne 3686793216 -or
        (Get-FileHash -LiteralPath $imagePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        throw 'La imagen no coincide con el archivo validado.'
    }
    $target = Get-ValidatedTarget
    if ($target.VolumeId -ne $initial.VolumeId) { throw 'Cambio el volumen mientras se verificaba la imagen.' }
    $state.letra_antes_de_grabar = $target.Root
    $state.disco = $target.Disk.Number
    $connection = @(Get-PnpDeviceProperty -InstanceId 'USB\VID_0951&PID_1666\KINGSTON_SERIAL_LOCAL' -KeyName DEVPKEY_Device_LocationPaths,DEVPKEY_Device_LastArrivalDate -ErrorAction Stop | Select-Object KeyName,Data)
    $connection | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDir 'conexion-antes.json') -Encoding UTF8
    $state.conexion_usb = @($connection | Where-Object KeyName -eq 'DEVPKEY_Device_LocationPaths' | ForEach-Object Data)
    $state.verificacion_completada = $false
    $state.registro_detallado = Join-Path $runDir 'imager.log'
    $devicePath = '\\.\PhysicalDrive' + $target.Disk.Number
    $toolArgs = @('--cli','--debug','--log-file',('"' + $state.registro_detallado + '"'),'--sha256',$expectedHash,('"' + $imagePath + '"'),$devicePath)
    Write-State 'grabando-y-verificando' ('Imagen directa al Kingston ' + $target.Root + ', disco ' + $target.Disk.Number + '. Registro detallado y verificacion habilitados.')
    $launchedWriter = Start-LoggedProcess $imagerPath ($toolArgs -join ' ')
    $writer = $launchedWriter.Process
    $state.proceso_grabador = $writer.Id
    Write-State 'grabando-y-verificando' ('Grabador actual iniciado, proceso ' + $writer.Id + '. Verificacion habilitada.')
    $writer.WaitForExit()
    [IO.File]::WriteAllText((Join-Path $runDir 'salida.log'), $launchedWriter.OutTask.Result)
    [IO.File]::WriteAllText((Join-Path $runDir 'error.log'), $launchedWriter.ErrorTask.Result)
    $state.codigo_salida = $writer.ExitCode
    if ($writer.ExitCode -ne 0) { throw ('El grabador termino con codigo ' + $writer.ExitCode + '. Revisar los registros de ' + $runDir) }
    $state.verificacion_completada = $true
    Write-State 'completado' 'Imagen directa grabada y verificada por Raspberry Pi Imager 2.0.11.1. Sin personalizaciones ni herramientas adicionales en el pendrive.'
} catch {
    $state.error_tipo = $_.Exception.GetType().FullName
    $state.error_hresult = $_.Exception.HResult
    Write-State 'error' $_.Exception.Message
    exit 1
}
