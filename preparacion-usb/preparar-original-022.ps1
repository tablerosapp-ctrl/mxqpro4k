$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskResult = Join-Path $PSScriptRoot 'original-022-estado.json'
# This guard stays outside catch: an earlier receipt must never be rewritten.
if (Test-Path -LiteralPath $taskResult) { throw 'Ya existe original-022-estado.json; revisar el resultado previo, no repetir automaticamente.' }
$taskArchive = Join-Path $taskRoot ('privado/usb-retirados-original022-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
$taskState = [ordered]@{estado='comprobando';version='0.2.2';fecha=(Get-Date).ToString('o');archivo_local=$taskArchive;tv_flasheado=$false;reboot_requested=$false;update_requested=$false;files=@();retirados=@();bytes_retirados=0;codigo_nativo=$null}
function Save-State {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($taskState | ConvertTo-Json -Depth 12))
    $file = [IO.File]::Open($taskResult,[IO.FileMode]::Truncate,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($bytes,0,$bytes.Length); $file.Flush($true) } finally { $file.Dispose() }
}
function Hash-File([string]$path) {
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Se esperaba un archivo ordinario' }
    $h = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($h -cnotmatch '^[0-9a-f]{64}$') { throw 'SHA256 invalido' }
    return $h
}
function Require-True($value,[string]$name) {
    if ($value -isnot [bool] -or $value -ne $true) { throw "Validacion ausente/fallida: $name" }
}
function Require-Zero($value,[string]$name) {
    if (($value -isnot [int] -and $value -isnot [long]) -or $value -ne 0) { throw "Codigo ausente/no cero: $name" }
}
function Local-Path([string]$relative) {
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative)) { throw 'Ruta local no relativa' }
    $path = [IO.Path]::GetFullPath((Join-Path $taskRoot $relative))
    if (-not $path.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta fuera del proyecto' }
    return $path
}
function Check-File([string]$path,$size,[string]$expected) {
    if (($size -isnot [int] -and $size -isnot [long]) -or $size -le 0 -or $expected -cnotmatch '^[0-9a-f]{64}$') { throw 'Tamano/SHA ausente o invalido' }
    if ((Get-Item -LiteralPath $path -Force).Length -ne $size -or (Hash-File $path) -ne $expected) { throw "Archivo distinto: $path" }
}
function Check-USB {
    $disks = @(Get-Disk | Where-Object UniqueId -eq $taskUsbId)
    if ($disks.Count -ne 1 -or $disks[0].FriendlyName -ne 'Kingston DataTraveler 3.0' -or $disks[0].Size -ne 30943995904 -or $disks[0].BusType -ne 'USB' -or $disks[0].IsBoot -or $disks[0].IsSystem) { throw 'No coincide el Kingston autorizado' }
    $parts = @(Get-Partition -DiskNumber $disks[0].Number | Where-Object DriveLetter)
    if ($parts.Count -ne 1) { throw 'Montaje ambiguo' }
    $volumes = @($parts[0] | Get-Volume)
    if ($volumes.Count -ne 1 -or $volumes[0].FileSystem -ne 'FAT32' -or $volumes[0].FileSystemLabel -ne 'TVBASE' -or $volumes[0].Size -ne 30925651968) { throw 'Estructura distinta' }
    $mount = "$($parts[0].DriveLetter):\"
    if ((Get-Content -LiteralPath (Join-Path $mount 'TVBASE-MEDIA.txt') -Raw).Trim() -ne 'TVBASE-P291-20260906-4dc82786') { throw 'Marcador incorrecto' }
    return $mount
}
# Read and pin existing TVBASE reports/backups before touching delivery files.
function Snapshot-Reports([string]$mount) {
    $snapshot = @()
    $deliveryZips = @('TVBASE-P291-A9-0.2.1-RECOVERY.zip','TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-RECOVERY.zip','TVBASE-P291-A9-0.2.2-RECOVERY.zip','TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.2-RECOVERY.zip')
    foreach ($dir in @(Get-ChildItem -LiteralPath $mount -Directory -Force | Where-Object Name -like 'TVBASE-*' | Sort-Object Name)) {
        if ($dir.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Directorio de informes enlazado' }
        $base = [IO.Path]::GetFullPath($dir.FullName)
        if (-not $base.StartsWith($mount,[StringComparison]::OrdinalIgnoreCase)) { throw 'Informe fuera del USB' }
        $snapshot += [ordered]@{path=$dir.Name;kind='directory'}
        foreach ($item in @(Get-ChildItem -LiteralPath $base -Recurse -Force | Sort-Object FullName)) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Enlace inesperado dentro de informes' }
            $full = [IO.Path]::GetFullPath($item.FullName)
            if (-not $full.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Elemento fuera de informe' }
            if ($item.PSIsContainer) {
                $snapshot += [ordered]@{path=$full.Substring($mount.Length);kind='directory'}
            } else {
                $snapshot += [ordered]@{path=$full.Substring($mount.Length);kind='file';bytes=$item.Length;sha256=(Hash-File $full)}
            }
        }
    }
    foreach ($item in @(Get-ChildItem -LiteralPath $mount -File -Force | Where-Object { ($_.Name -like 'TVBASE-*' -and $_.Name -notin $deliveryZips) -or $_.Name -eq 'AccesoUSB-0.9.apk' } | Sort-Object Name)) {
        $snapshot += [ordered]@{path=$item.Name;kind='file';bytes=$item.Length;sha256=(Hash-File $item.FullName)}
    }
    return @($snapshot | Sort-Object { $_.path }, { $_.kind })
}
function Usb-Root-File([string]$mount,[string]$name) {
    if ([string]::IsNullOrWhiteSpace($name) -or [IO.Path]::GetFileName($name) -ne $name -or $name -in @('.','..') -or $name.Contains(':')) { throw 'Se requiere un nombre simple en raiz USB' }
    $path = [IO.Path]::GetFullPath((Join-Path $mount $name))
    if (([IO.Path]::GetDirectoryName($path).TrimEnd('\')+'\') -ne $mount) { throw 'Destino fuera de raiz USB' }
    return $path
}
function Copy-Checked([string]$source,[string]$target,$size,[string]$expected) {
    Check-File $source $size $expected
    if (Test-Path -LiteralPath $target) {
        Check-File $target $size $expected
    } else {
        $inputFile = [IO.File]::OpenRead($source)
        try {
            $outputFile = [IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $inputFile.CopyTo($outputFile); $outputFile.Flush($true) } finally { $outputFile.Dispose() }
        } finally { $inputFile.Dispose() }
    }
    Check-File $target $size $expected
}
# The delivery contract is generated only after final package and independent022 review. Its
# hashes pin both bytes and verification receipts; no TV action is performed.
$taskContractPath = Local-Path 'preparacion-usb/entrega-original-022.json'
if (-not (Test-Path -LiteralPath $taskContractPath)) { throw 'Falta el contrato final revisado; no preparar una entrega parcial.' }
$taskContract = Get-Content -LiteralPath $taskContractPath -Raw | ConvertFrom-Json
if ($taskContract.version -ne '0.2.2' -or $taskContract.profile -ne 'gxlx2_p291_1g' -or $taskContract.state -ne 'reviewed_for_usb_copy') { throw 'Contrato no liberado para copia' }
$taskAllowed = @('TVBASE-P291-A9-0.2.2-RECOVERY.zip','TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.2-RECOVERY.zip','LEEME-AHORA.txt')
$taskFiles = @($taskContract.files)
if ($taskFiles.Count -ne $taskAllowed.Count -or (($taskFiles | ForEach-Object name) -join ',') -ne ($taskAllowed -join ',')) { throw 'La lista de entrega difiere de la revisada' }
foreach ($row in $taskFiles) {
    Check-File (Local-Path $row.source) $row.bytes $row.sha256
}
foreach ($proof in @($taskContract.proofs)) {
    Check-File (Local-Path $proof.source) $proof.bytes $proof.sha256
}
if (@($taskContract.proofs).Count -lt 3) { throw 'Faltan recibos de paquetes y revision independiente022' }

$taskReceipt = [IO.File]::Open($taskResult,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
$taskReceipt.Dispose()
try {
    $taskState.contract_sha256 = Hash-File $taskContractPath
    Save-State
    $mount = Check-USB
    $taskState.drive_letter = $mount.Substring(0,1)
    $taskState.volume_health_before = [string](Get-Volume -DriveLetter $mount.Substring(0,1)).HealthStatus
    $taskState.format_requested = $false
    $taskState.repair_requested = $false
    $taskState.safe_removal_pending = $true
    $taskState.volume_flush_verified = $false
    $markerHash = Hash-File (Usb-Root-File $mount 'TVBASE-MEDIA.txt')
    Check-File (Usb-Root-File $mount 'AccesoUSB-0.9.apk') 61843 '1d0f267e818acca5562048f9961c7c234f36b8cc81f827cb3eac9e3fcd2505a4'
    # Exact old delivery only. Reports, backups and directories never match.
    $retire = @(
        [ordered]@{archivo='TVBASE-P291-A9-0.2.1-RECOVERY.zip';bytes=573688933;sha256='dcb152c77e55cb067d6e88a8144990a3edb5d06568ea8cdfdc414a0fa21aac58'},
        [ordered]@{archivo='TVBASE-P291-A9-ORIGINAL-RESTORE-0.2.1-RECOVERY.zip';bytes=913294443;sha256='42580206f254fab0a2280cd263a48882677e7ddf5cfd609382a840c8d0fb103a'},
        [ordered]@{archivo='LEEME-AHORA.txt';bytes=4412;sha256='4c4d6586285b36415f0dd7eb12499d9c8970d4f1b21d85647726c85dd1784320'}
    )
    $taskState.preserved_reports = @(Snapshot-Reports $mount)
    Save-State
    $rows = @()
    foreach ($entry in $retire) {
        $path = Usb-Root-File $mount $entry.archivo
        Check-File $path $entry.bytes $entry.sha256
        $rows += [ordered]@{archivo=$entry.archivo;bytes=$entry.bytes;sha256=$entry.sha256;copia_pc_verificada=$false;retirado=$false}
    }
    [long]$copyBytes = 0
    foreach ($entry in $taskFiles) {
        $copyBytes += $entry.bytes
        if ($entry.name -ne 'LEEME-AHORA.txt' -and (Test-Path -LiteralPath (Usb-Root-File $mount $entry.name))) { throw 'Ya existe un archivo de entrega nueva: revisar, no sobrescribir' }
    }
    # Preserve enough for six raw backups AFTER copying the delivery.
    if ((Get-Volume -DriveLetter $mount.Substring(0,1)).SizeRemaining -lt ($copyBytes + 6603931648)) { throw 'Espacio insuficiente para entrega y respaldo completo de las seis particiones' }
    $archiveFull = [IO.Path]::GetFullPath($taskArchive)
    if (-not $archiveFull.StartsWith($taskRoot+'\privado\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Archivo local fuera del proyecto' }
    New-Item -ItemType Directory -Path $archiveFull | Out-Null
    Get-ChildItem -LiteralPath $mount -Force | Select-Object Name,Length,Attributes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $archiveFull 'antes.json') -Encoding UTF8
    foreach ($entry in $rows) {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes del archivo' }
        Copy-Checked (Usb-Root-File $mount $entry.archivo) (Join-Path $archiveFull $entry.archivo) $entry.bytes $entry.sha256
        $entry.copia_pc_verificada = $true
    }
    $taskState.retirados = $rows
    Save-State
    foreach ($entry in $taskFiles | Where-Object name -ne 'LEEME-AHORA.txt') {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de copiar' }
        Copy-Checked (Local-Path $entry.source) (Usb-Root-File $mount $entry.name) $entry.bytes $entry.sha256
        $taskState.files += [ordered]@{archivo=$entry.name;bytes=$entry.bytes;sha256=$entry.sha256;lectura_verificada=$true}
        Save-State
    }
    foreach ($entry in $rows) {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de retirar' }
        $path = Usb-Root-File $mount $entry.archivo
        Check-File $path $entry.bytes $entry.sha256
        Check-File (Join-Path $archiveFull $entry.archivo) $entry.bytes $entry.sha256
        # Usb-Root-File already verifies the absolute path is one root file.
        Remove-Item -LiteralPath $path
        if (Test-Path -LiteralPath $path) { throw 'Retiro no confirmado' }
        $entry.retirado = $true
        $taskState.bytes_retirados += $entry.bytes
        Save-State
    }
    $guide = @($taskFiles | Where-Object name -eq 'LEEME-AHORA.txt')[0]
    if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de la guia' }
    Copy-Checked (Local-Path $guide.source) (Usb-Root-File $mount $guide.name) $guide.bytes $guide.sha256
    $taskState.files += [ordered]@{archivo=$guide.name;bytes=$guide.bytes;sha256=$guide.sha256;lectura_verificada=$true}
    foreach ($entry in $taskState.files) { Check-File (Usb-Root-File $mount $entry.archivo) $entry.bytes $entry.sha256 }
    if ((Check-USB) -ne $mount -or (Hash-File (Usb-Root-File $mount 'TVBASE-MEDIA.txt')) -ne $markerHash) { throw 'Cambio el Kingston o su marcador' }
    if (Test-Path -LiteralPath (Usb-Root-File $mount 'recovery.img')) { throw 'Recovery externo antiguo sigue activo' }
    $afterReports = @(Snapshot-Reports $mount)
    if (($afterReports | ConvertTo-Json -Depth 5 -Compress) -cne ($taskState.preserved_reports | ConvertTo-Json -Depth 5 -Compress)) { throw 'Cambio el inventario o contenido de informes/respaldos' }
    $taskState.reports_unchanged_verified = $true
    $taskState.free_bytes_after = (Get-Volume -DriveLetter $mount.Substring(0,1)).SizeRemaining
    if ($taskState.free_bytes_after -lt 6603931648) { throw 'No quedo el espacio requerido para respaldo' }
    $taskState.estado = 'verificado'
    $taskState.fecha = (Get-Date).ToString('o')
    $taskState.codigo_nativo = 0
    $taskState.detalle = 'Entrega original P291 copiada y leida; tres archivos021 archivados en PC antes de retirarlos. Informes y respaldos conservados. Sin formato ni modificacion del TV por este preparador. Falta expulsion segura: Flush de archivos y relectura no acreditan persistencia de metadatos FAT tras desconectar. Recovery ya observado; instalador022 y restaurador022 todavia sin prueba fisica. No usar de nuevo la preparacion AccesoUSB09.'
    Save-State
    Copy-Checked $taskResult (Join-Path $archiveFull 'resultado.json') (Get-Item -LiteralPath $taskResult).Length (Hash-File $taskResult)
    Get-Content -LiteralPath $taskResult -Raw
} catch {
    $taskState.estado = 'fallo'
    $taskState.codigo_nativo = 1
    $taskState.error_nativo = $_.Exception.ToString()
    Save-State
    throw
}
