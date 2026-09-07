# Prueba acotada de escritura y lectura por archivo, sin cambiar particiones.
# Robocopy /J usa E/S sin buffer; /R:0 evita repetir un fallo automaticamente.
$ErrorActionPreference = 'Stop'
$expectedId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$expectedSize = [long]30943995904
$expectedHash = '4479B09374D92FFE4BE625B5DDED96C5D7D7A0E8C6BCB0A7D2894A839214A2F8'
$imageName = 'Armbian_26.05.0_amlogic_s905l2_noble_6.12.91_server_2026.06.01.img'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $projectRoot 'images'
$imagePath = Join-Path $sourceDir $imageName
$runId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$runDir = Join-Path $PSScriptRoot ('prueba-archivo-' + $runId)
$null = New-Item -ItemType Directory -Path $runDir
$statusPath = Join-Path $PSScriptRoot 'prueba-archivo-estado.json'
$state = [ordered]@{estado='comprobando'; fecha_inicio=(Get-Date).ToString('o'); destino_id=$expectedId; directorio_informe=$runDir; archivo=$imageName; bytes=[long]3686793216}

function Write-State([string]$phase, [string]$detail) {
    $state.estado = $phase
    $state.detalle = $detail
    $state.fecha = (Get-Date).ToString('o')
    $json = $state | ConvertTo-Json -Depth 5
    $json | Set-Content -LiteralPath (Join-Path $runDir 'resultado.json') -Encoding UTF8
    $tempStatus = $statusPath + '.tmp'
    $json | Set-Content -LiteralPath $tempStatus -Encoding UTF8
    Move-Item -LiteralPath $tempStatus -Destination $statusPath -Force
    Write-Output ($phase + ': ' + $detail)
}

function Get-Target {
    $found = @(Get-Disk | Where-Object { $_.UniqueId -eq $expectedId })
    if ($found.Count -ne 1) { throw 'El Kingston no esta identificado de forma inequivoca.' }
    $disk = $found[0]
    if ($disk.BusType -ne 'USB' -or $disk.Size -ne $expectedSize -or
        $disk.FriendlyName -ne 'Kingston DataTraveler 3.0' -or
        $disk.IsBoot -or $disk.IsSystem -or $disk.IsOffline -or $disk.IsReadOnly) {
        throw 'El disco no cumple las condiciones de la prueba.'
    }
    $parts = @(Get-Partition -DiskNumber $disk.Number)
    if ($parts.Count -ne 1 -or -not $parts[0].DriveLetter) { throw 'Se requiere un unico volumen accesible en el Kingston.' }
    $volume = $parts[0] | Get-Volume
    if ($volume.FileSystem -notin @('FAT32','NTFS','exFAT')) { throw 'El volumen no tiene un sistema de archivos utilizable.' }
    [pscustomobject]@{Disk=$disk; Volume=$volume; Root=([string]$parts[0].DriveLetter + ':\')}
}

function Assert-SameTarget {
    $now = Get-Target
    if ($now.Root -ne $state.raiz -or $now.Volume.UniqueId -ne $state.volumen_id) {
        throw 'Cambio la asignacion o el volumen durante la prueba. Se detiene.'
    }
}

function Copy-Once([string]$source, [string]$destination, [string]$label) {
    $logPath = Join-Path $runDir ($label + '.log')
    $arguments = @(('"' + $source + '"'), ('"' + $destination + '"'), $imageName,
        '/J','/NOOFFLOAD','/R:0','/W:0','/COPY:DAT','/DCOPY:DAT','/NP','/BYTES',
        ('/UNILOG:"' + $logPath + '"'))
    $copy = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\robocopy.exe') -ArgumentList $arguments -WindowStyle Hidden -PassThru
    $state.proceso_copia = $copy.Id
    $state.registro_copia = $logPath
    Write-State $label ('Proceso de copia ' + $copy.Id + ', sin reintentos automaticos.')
    $copy.WaitForExit()
    $state[$label + '_codigo'] = $copy.ExitCode
    if ($copy.ExitCode -ge 8) { throw ('Fallo de ' + $label + ', codigo Robocopy ' + $copy.ExitCode + '. Ver ' + $logPath) }
}

try {
    Write-State 'comprobando' 'Validando dispositivo y archivo fuente.'
    if (@(Get-Process -Name 'rpi-imager','rufus*','robocopy' -ErrorAction SilentlyContinue).Count -gt 0) {
        throw 'Hay otra herramienta de copia o grabacion activa.'
    }
    $target = Get-Target
    $state.raiz = $target.Root
    $state.volumen_id = $target.Volume.UniqueId
    $state.disco = $target.Disk.Number
    $userItems = @(Get-ChildItem -LiteralPath $target.Root -Force | Where-Object { $_.Name -notin @('System Volume Information','$RECYCLE.BIN') })
    if ($userItems.Count -ne 0) { throw 'El pendrive contiene archivos; esta prueba exige el volumen vacio ya acordado.' }
    if ($target.Volume.SizeRemaining -lt ([long]3686793216 + 64MB)) { throw 'Espacio libre insuficiente.' }
    if ((Get-Item -LiteralPath $imagePath).Length -ne 3686793216 -or
        (Get-FileHash -LiteralPath $imagePath -Algorithm SHA256).Hash -ne $expectedHash) {
        throw 'La imagen fuente no coincide con la validada.'
    }
    Assert-SameTarget
    $usbDir = Join-Path $target.Root ('codex-prueba-' + $runId)
    if (Test-Path -LiteralPath $usbDir) { throw 'El directorio temporal ya existe.' }
    $null = New-Item -ItemType Directory -Path $usbDir
    $state.directorio_usb = $usbDir
    Copy-Once $sourceDir $usbDir 'escritura'
    Assert-SameTarget
    $usbFile = Join-Path $usbDir $imageName
    if ((Get-Item -LiteralPath $usbFile).Length -ne 3686793216) { throw 'El archivo escrito no tiene el tamano esperado.' }
    $returnDir = Join-Path $runDir 'retorno'
    $null = New-Item -ItemType Directory -Path $returnDir
    Copy-Once $usbDir $returnDir 'lectura'
    Assert-SameTarget
    Write-State 'comparando' 'Comparando SHA-256 de los datos leidos del pendrive con el original.'
    $returnFile = Join-Path $returnDir $imageName
    $state.sha256_leido = (Get-FileHash -LiteralPath $returnFile -Algorithm SHA256).Hash
    if ((Get-Item -LiteralPath $returnFile).Length -ne 3686793216 -or $state.sha256_leido -ne $expectedHash) {
        throw 'Los datos leidos del pendrive no coinciden con el original.'
    }
    # Eliminar solo los archivos creados por esta prueba, con el destino revalidado.
    Assert-SameTarget
    $resolvedUsbDir = [IO.Path]::GetFullPath($usbDir)
    $resolvedUsbFile = [IO.Path]::GetFullPath($usbFile)
    if (-not $resolvedUsbDir.StartsWith($state.raiz,[StringComparison]::OrdinalIgnoreCase) -or
        -not $resolvedUsbFile.StartsWith($resolvedUsbDir + '\',[StringComparison]::OrdinalIgnoreCase)) {
        throw 'La ruta de limpieza no pertenece al directorio de esta prueba.'
    }
    Remove-Item -LiteralPath $resolvedUsbFile -Force
    [IO.Directory]::Delete($resolvedUsbDir, $false)
    Remove-Item -LiteralPath $returnFile -Force
    [IO.Directory]::Delete($returnDir, $false)
    Write-State 'completado' 'Escritura y lectura de 3686793216 bytes con SHA-256 coincidente. Archivos temporales eliminados. Particiones sin modificar.'
} catch {
    $state.error_tipo = $_.Exception.GetType().FullName
    $state.error_hresult = $_.Exception.HResult
    Write-State 'error' $_.Exception.Message
    exit 1
}
