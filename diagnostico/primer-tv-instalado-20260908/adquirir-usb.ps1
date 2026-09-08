$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskDestination = Join-Path $taskRoot ('privado/instalacion022-adquisicion-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
if (-not ([IO.Path]::GetFullPath($taskDestination)).StartsWith($taskRoot+'\privado\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera de privado del proyecto' }
if (Test-Path -LiteralPath $taskDestination) { throw 'Adquisicion ya existe; no sobrescribir' }
New-Item -ItemType Directory -Path $taskDestination | Out-Null
$taskReceipt = Join-Path $taskDestination 'adquisicion.json'
$taskState = [ordered]@{state='acquiring';created_at=(Get-Date).ToString('o');private_directory=$taskDestination;usb_written=$false;tv_contacted=$false;files=@();bytes_copied=0;exit_code=$null}
function Save-Acquisition {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($taskState | ConvertTo-Json -Depth 12))
    $f = [IO.File]::Open($taskReceipt,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try { $f.Write($bytes,0,$bytes.Length); $f.Flush($true) } finally { $f.Dispose() }
}
function Check-Kingston {
    $disks = @(Get-Disk | Where-Object UniqueId -eq $taskUsbId)
    if ($disks.Count -ne 1 -or $disks[0].FriendlyName -ne 'Kingston DataTraveler 3.0' -or $disks[0].Size -ne 30943995904 -or $disks[0].BusType -ne 'USB' -or $disks[0].IsSystem -or $disks[0].IsBoot) { throw 'No coincide el Kingston autorizado' }
    $parts = @(Get-Partition -DiskNumber $disks[0].Number | Where-Object DriveLetter)
    if ($parts.Count -ne 1) { throw 'Montaje ambiguo' }
    $volumes = @($parts[0] | Get-Volume)
    if ($volumes.Count -ne 1 -or $volumes[0].FileSystem -ne 'FAT32' -or $volumes[0].FileSystemLabel -ne 'TVBASE' -or $volumes[0].Size -ne 30925651968) { throw 'Volumen distinto' }
    $mount = "$($parts[0].DriveLetter):\"
    if ((Get-Content -LiteralPath (Join-Path $mount 'TVBASE-MEDIA.txt') -Raw).Trim() -ne 'TVBASE-P291-20260906-4dc82786') { throw 'Marcador diferente' }
    return $mount
}
function Hash-Ordinary([string]$path) {
    $item=Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Archivo no ordinario' }
    $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -cnotmatch '^[0-9a-f]{64}$') { throw 'SHA256 invalido' }
    return $hash
}
function Copy-Evidence([string]$source,[string]$relative,[string]$expectedHash='',[long]$expectedSize=-1) {
    if ([IO.Path]::IsPathRooted($relative)) { throw 'Ruta relativa requerida' }
    $target=[IO.Path]::GetFullPath((Join-Path $taskDestination $relative))
    if (-not $target.StartsWith($taskDestination+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera de adquisicion' }
    $item=Get-Item -LiteralPath $source -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Fuente no ordinaria' }
    if ($expectedSize -ge 0 -and $item.Length -ne $expectedSize) { throw 'Tamano difiere del recibo del TV' }
    if (Test-Path -LiteralPath $target) { throw 'No sobrescribir copia anterior' }
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
    $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
    $inputFile=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    [long]$total=0
    try {
        $outputFile=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try {
            $buffer=New-Object byte[] (4MB)
            while (($n=$inputFile.Read($buffer,0,$buffer.Length)) -gt 0) {
                $hash.AppendData($buffer,0,$n)
                $outputFile.Write($buffer,0,$n)
                $total += $n
            }
            $outputFile.Flush($true)
        } finally { $outputFile.Dispose() }
        if ($total -ne $item.Length -or $inputFile.Length -ne $total) { throw 'Lectura incompleta o fuente cambiada' }
        $sourceHash=([BitConverter]::ToString($hash.GetHashAndReset())).Replace('-','').ToLowerInvariant()
    } finally { $inputFile.Dispose(); $hash.Dispose() }
    $copyHash=Hash-Ordinary $target
    if ($copyHash -ne $sourceHash -or ($expectedHash -ne '' -and $copyHash -ne $expectedHash)) { throw 'SHA de copia/USB/recibo no coincide' }
    if ((Get-Item -LiteralPath $target).Length -ne $total) { throw 'Copia con tamano distinto' }
    $taskState.files += [ordered]@{relative_path=$relative;bytes=$total;sha256=$sourceHash;pc_read_sha256=$copyHash;matches_tv_receipt=($expectedHash -ne '');verified=$true}
    $taskState.bytes_copied += $total
    Save-Acquisition
}
try {
    $mount=Check-Kingston
    $taskState.drive_letter=$mount.Substring(0,1)
    $taskState.script_sha256=Hash-Ordinary $PSCommandPath
    Save-Acquisition
    $backupName='TVBASE-respaldo-022-773306709'
    $backupPath=Join-Path $mount $backupName
    $backup=Get-Content -LiteralPath (Join-Path $backupPath '00-backup-verified.json') -Raw | ConvertFrom-Json
    if ($backup.state -ne 'backup_verified' -or $backup.package_id -ne 'TVBASE-P291-A9-0.2.2' -or $backup.dt_id -ne 'gxlx2_p291_1g') { throw 'Recibo de respaldo inesperado' }
    $expected=@{}
    foreach ($record in @($backup.records)) {
        if ($record.name -notin @('system','vendor','product','odm','boot','data') -or $record.file -ne ($record.name+'.img') -or $expected.ContainsKey($record.name) -or $record.sha256 -cnotmatch '^[0-9a-f]{64}$' -or $record.sha256 -ne $record.usb_read_sha256 -or $record.sha256 -ne $record.source_after_sha256 -or $record.state -ne 'verified') { throw 'Registro de respaldo invalido' }
        $expected[$record.name]=$record
    }
    if ($expected.Count -ne 6 -or ($backup.records | Measure-Object -Property bytes -Sum).Sum -ne 6067060736) { throw 'Conjunto de respaldo distinto' }
    if ((Get-Volume -DriveLetter ([IO.Path]::GetPathRoot($taskDestination).Substring(0,1))).SizeRemaining -lt 7GB) { throw 'Espacio local insuficiente' }
    $taskState.usb_inventory=@(Get-ChildItem -LiteralPath $mount -Force | Select-Object Name,Length,Attributes)
    $directories=@(Get-ChildItem -LiteralPath $mount -Directory -Filter 'TVBASE-*' | Sort-Object Name)
    # Preserve the new installation's small receipts first, then its images.
    $directories=@($directories | Sort-Object @{Expression={if ($_.Name -eq $backupName) {0} else {1}}},Name)
    foreach ($dir in $directories) {
        if ((Check-Kingston) -ne $mount) { throw 'Cambio de USB' }
        if ($dir.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Directorio enlazado no admitido' }
        $items=@(Get-ChildItem -LiteralPath $dir.FullName -Recurse -Force | Sort-Object @{Expression={if ($_.Extension -eq '.img') {1} else {0}}},FullName)
        foreach ($item in $items) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Elemento enlazado no admitido' }
            $full=[IO.Path]::GetFullPath($item.FullName)
            if (-not $full.StartsWith($mount,[StringComparison]::OrdinalIgnoreCase)) { throw 'Fuente fuera del USB' }
            $relative='usb/'+$full.Substring($mount.Length)
            if ($item.PSIsContainer) { New-Item -ItemType Directory -Path (Join-Path $taskDestination $relative) -Force | Out-Null; continue }
            if ($dir.Name -eq $backupName -and $item.Extension -eq '.img') {
                if ((Check-Kingston) -ne $mount) { throw 'Cambio de USB antes de respaldo' }
                $record=$expected[$item.BaseName]
                if ($null -eq $record) { throw 'Imagen de respaldo desconocida' }
                Write-Output ('Conservando y verificando respaldo '+$item.Name)
                Copy-Evidence $full $relative $record.sha256 $record.bytes
            } else { Copy-Evidence $full $relative }
        }
    }
    foreach ($item in @(Get-ChildItem -LiteralPath $mount -File -Force | Where-Object {$_.Name -like 'TVBASE-*.txt' -or $_.Name -eq 'LEEME-AHORA.txt'} | Sort-Object Name)) {
        Copy-Evidence $item.FullName ('usb/'+$item.Name)
    }
    Copy-Evidence 'C:\Users\usuario-local\AppData\Local\Temp\codex-clipboard-a2fd23b3-8724-4f19-b1c3-3146000ece32.png' 'foto-inicio-tvbase.png'
    if ((Check-Kingston) -ne $mount) { throw 'Cambio final de USB' }
    $verifiedImages=@($taskState.files | Where-Object matches_tv_receipt)
    if ($verifiedImages.Count -ne 6) { throw 'Falta un respaldo verificado' }
    $taskState.state='verified'
    $taskState.completed_at=(Get-Date).ToString('o')
    $taskState.exit_code=0
    $taskState.backup_images_verified=6
    $taskState.backup_bytes_verified=6067060736
    Save-Acquisition
    [ordered]@{state=$taskState.state;private_directory=$taskDestination;files=$taskState.files.Count;bytes=$taskState.bytes_copied;backup_images_verified=6;usb_written=$false;tv_contacted=$false;exit_code=0} | ConvertTo-Json
} catch {
    $taskState.state='failed'; $taskState.exit_code=1; $taskState.error=$_.Exception.ToString(); Save-Acquisition; throw
}
