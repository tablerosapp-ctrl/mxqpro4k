$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskResult = Join-Path $PSScriptRoot 'rom-012-estado.json'
# This guard stays outside catch: an earlier receipt must never be rewritten.
if (Test-Path -LiteralPath $taskResult) { throw 'Ya existe rom-012-estado.json; revisar el resultado previo, no repetir automaticamente.' }
$taskArchive = Join-Path $taskRoot ('privado/usb-retirados-rom012-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
$taskState = [ordered]@{estado='comprobando';version='0.1.2';fecha=(Get-Date).ToString('o');archivo_local=$taskArchive;tv_flasheado=$false;reboot_requested=$false;update_requested=$false;files=@();retirados=@();bytes_retirados=0;codigo_nativo=$null}
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
# CreateNew also closes the race between Test-Path and receipt creation.
$taskReceipt = [IO.File]::Open($taskResult,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
$taskReceipt.Dispose()
try {
    Save-State
    # Every build check precedes USB discovery and mutation. The consolidated
    # 0.1.2 receipt replaces the separate COMPROBACION file used by 0.1.1.
    $proofPath = Local-Path 'rom-simplificada/salida/RECOVERY-VERIFICACION-0.1.2.json'
    $proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
    if ($proof.version -ne '0.1.2' -or $proof.package_id -ne 'TVBASE-P291-A9-0.1.2' -or $proof.file -ne 'rom-simplificada/salida/TVBASE-P291-A9-0.1.2-RECOVERY.zip') { throw 'Recibo ROM de otra version/ruta' }
    if ($proof.bytes -ne 573082917 -or $proof.sha256 -ne '6c0c4307208c8d0e1a958a3fc6c790fa94021a850599985b0a41b340b821bb99') { throw 'ROM distinta de la entrega 0.1.2 revisada' }
    foreach ($name in @('bluetooth_disabled','inherited_recovery_replacement_disabled','whole_file_signature_verified','openjdk_whole_file_signature_verified','payload_sha256_verified','windows_installer_accepts_new_payload','windows_installer_rejects_previous_package','original_partition_backup_required')) { Require-True $proof.$name $name }
    if ($proof.manifest.id -ne 'TVBASE-P291-A9-0.1.2' -or $proof.manifest.dt_id -ne 'gxlx2_p291_1g' -or $proof.manifest.media_id -ne 'TVBASE-P291-20260906-4dc82786') { throw 'Perfil de manifiesto distinto' }
    $images = @($proof.manifest.images)
    if ($images.Count -ne 5 -or (($images | ForEach-Object name) -join ',') -ne 'system,vendor,product,odm,boot') { throw 'Lista/orden de particiones distinto' }
    foreach ($entry in $images) {
        if (($entry.size -isnot [int] -and $entry.size -isnot [long]) -or $entry.size -le 0 -or $entry.sha256 -cnotmatch '^[0-9a-f]{64}$' -or $entry.entry -ne ('tvbase/'+$entry.name+'.img')) { throw 'Entrada del manifiesto invalida' }
    }
    $revisionPath = Local-Path $proof.revision_report
    if ($proof.revision_report_sha256 -cnotmatch '^[0-9a-f]{64}$' -or (Hash-File $revisionPath) -ne $proof.revision_report_sha256) { throw 'Reporte de revision distinto' }
    $revision = Get-Content -LiteralPath $revisionPath -Raw | ConvertFrom-Json
    if ($revision.version -ne '0.1.2' -or $revision.package_id -ne 'TVBASE-P291-A9-0.1.2') { throw 'Revision ext4 de otra version' }
    Require-Zero $revision.fsck_exit 'revision.fsck_exit'
    Require-Zero $proof.reviewed_revision.fsck_exit 'reviewed_revision.fsck_exit'
    foreach ($name in @('bluetooth_disabled','inherited_recovery_replacement_disabled','boot_unchanged')) { Require-True $revision.$name $name }
    foreach ($partition in @('system','vendor')) {
        $entry = @($images | Where-Object name -eq $partition)[0]
        Require-Zero $revision.partitions.$partition.fsck_exit ($partition+'.fsck_exit')
        if ($revision.($partition+'_sha256') -ne $entry.sha256 -or $proof.reviewed_revision.($partition+'_sha256') -ne $entry.sha256 -or $revision.partitions.$partition.sha256 -ne $entry.sha256) { throw 'Imagen ext4 no corresponde al ZIP' }
    }
    if ($revision.boot_sha256 -ne $images[4].sha256) { throw 'Boot no corresponde al ZIP' }
    $rom = Local-Path $proof.file
    Check-File $rom $proof.bytes $proof.sha256
    $taskState.rom_proof_sha256 = Hash-File $proofPath
    $taskState.revision_report_sha256 = $proof.revision_report_sha256

    $apk = Local-Path 'rom-simplificada/compilacion/control-bluetooth-0.1/ControlBluetooth-0.1.apk'
    $apkHash = '6d7c866478c859ac3948a1132aa75ceebc13d059c32098aaecc0cbb82dbf031f'
    $apkSize = 24979
    $release = Get-Content -LiteralPath (Local-Path 'rom-simplificada/compilacion/control-bluetooth-0.1/componente.json') -Raw | ConvertFrom-Json
    if ($release.version -ne '0.1' -or $release.version_code -ne 1 -or $release.package -ne 'com.tvbase.bluetoothcontrol' -or $release.sha256 -ne $apkHash -or $release.bytes -ne $apkSize -or $release.min_sdk -ne 28 -or $release.target_sdk -ne 28) { throw 'Release auxiliar distinta' }
    foreach ($name in @('compiled_api28','signed_verified_api28','permissions_exact','zipalign','zip_crc','bounded_static_dex_scan')) { Require-True $release.validation.$name $name }
    Check-File $apk $apkSize $apkHash
    $java = Local-Path 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
    $bt = Local-Path 'tools/verificacion-apk/build-tools-37/android-37.0'
    $signature = & $java -jar (Join-Path $bt 'lib/apksigner.jar') verify --verbose --print-certs --min-sdk-version 28 --max-sdk-version 28 $apk 2>&1
    $signatureCode = $LASTEXITCODE
    if ($signatureCode -ne 0 -or ($signature -join "`n") -notmatch 'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613') { throw 'Firma auxiliar distinta/invalida' }
    $badging = & (Join-Path $bt 'aapt2.exe') dump badging $apk 2>&1
    $badgingCode = $LASTEXITCODE
    if ($badgingCode -ne 0 -or ($badging -join "`n") -notmatch "package: name='com.tvbase.bluetoothcontrol' versionCode='1' versionName='0.1'") { throw 'Paquete auxiliar distinto' }
    $guide = Local-Path 'rom-simplificada/instalador/LEEME-ROM-0.1.2.txt'
    $guideHash = Hash-File $guide
    $guideSize = (Get-Item -LiteralPath $guide).Length
    if ($guideSize -le 0) { throw 'Guia vacia' }

    $mount = Check-USB
    $taskState.drive_letter = $mount.Substring(0,1)
    $recovery = Usb-Root-File $mount 'recovery.img'
    $recoveryHash = 'e59ef077378f8b1ba644bcfbef2a0f55e9914258696f203e813392e0a9fed01b'
    Check-File $recovery 25165824 $recoveryHash
    $markerHash = Hash-File (Usb-Root-File $mount 'TVBASE-MEDIA.txt')
    # Explicit, immutable retirement allowlist. No wildcard, directory or report.
    $retire = @(
        [ordered]@{archivo='TVBASE-P291-A9-0.1.1-RECOVERY.zip';bytes=573089164;sha256='e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205'},
        [ordered]@{archivo='AccesoUSB-0.8.apk';bytes=53651;sha256='e103db68fb4deea3479db9a72844eea6e69c5d9beb66403b5673a9636377a148'},
        [ordered]@{archivo='LEEME-AHORA.txt';bytes=1460;sha256='7cc05f9b24e7c6df8b7b8a4de6e675c48df02cb80077a5a3958dd5c821ab4eb7'}
    )
    $rows = @()
    foreach ($row in $retire) {
        $path = Usb-Root-File $mount $row.archivo
        if (-not (Test-Path -LiteralPath $path)) { continue }
        if ($row.archivo -eq 'LEEME-AHORA.txt' -and (Hash-File $path) -eq $guideHash) { continue }
        Check-File $path $row.bytes $row.sha256
        $rows += [ordered]@{archivo=$row.archivo;bytes=$row.bytes;sha256=$row.sha256;copia_pc_verificada=$false;retirado=$false}
    }
    $deliver = @(
        [ordered]@{archivo='TVBASE-P291-A9-0.1.2-RECOVERY.zip';source=$rom;bytes=$proof.bytes;sha256=$proof.sha256},
        [ordered]@{archivo='ControlBluetooth-0.1.apk';source=$apk;bytes=$apkSize;sha256=$apkHash}
    )
    foreach ($row in $deliver) {
        $path = Usb-Root-File $mount $row.archivo
        if (Test-Path -LiteralPath $path) { Check-File $path $row.bytes $row.sha256 }
    }
    $free = (Get-Volume -DriveLetter $mount.Substring(0,1)).SizeRemaining
    if ($free -lt ($proof.bytes+$apkSize+$guideSize+10485760)) { throw 'Espacio insuficiente para copiar antes de retirar' }
    if (-not [IO.Path]::GetFullPath($taskArchive).StartsWith($taskRoot+'\privado\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Archivo local fuera del proyecto' }
    New-Item -ItemType Directory -Path $taskArchive | Out-Null
    Get-ChildItem -LiteralPath $mount -Force | Select-Object Name,Length | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskArchive 'antes.json') -Encoding UTF8
    foreach ($row in $rows) {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de archivar' }
        Copy-Checked (Usb-Root-File $mount $row.archivo) (Join-Path $taskArchive $row.archivo) $row.bytes $row.sha256
        $row.copia_pc_verificada = $true
    }
    $taskState.retirados = $rows
    Save-State
    foreach ($row in $deliver) {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de copiar' }
        Copy-Checked $row.source (Usb-Root-File $mount $row.archivo) $row.bytes $row.sha256
        $taskState.files += [ordered]@{archivo=$row.archivo;bytes=$row.bytes;sha256=$row.sha256;lectura_verificada=$true}
        Save-State
    }
    # Both new artifacts are copied/read and every old file has a verified PC copy.
    foreach ($row in $rows) {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de retirar' }
        $path = Usb-Root-File $mount $row.archivo
        Check-File $path $row.bytes $row.sha256
        Check-File (Join-Path $taskArchive $row.archivo) $row.bytes $row.sha256
        Remove-Item -LiteralPath $path
        if (Test-Path -LiteralPath $path) { throw 'Retiro no confirmado' }
        $row.retirado = $true
        $taskState.bytes_retirados += $row.bytes
        Save-State
    }
    if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de copiar guia' }
    Copy-Checked $guide (Usb-Root-File $mount 'LEEME-AHORA.txt') $guideSize $guideHash
    $taskState.files += [ordered]@{archivo='LEEME-AHORA.txt';bytes=$guideSize;sha256=$guideHash;lectura_verificada=$true}
    foreach ($row in $taskState.files) { Check-File (Usb-Root-File $mount $row.archivo) $row.bytes $row.sha256 }
    Check-File $recovery 25165824 $recoveryHash
    if ((Check-USB) -ne $mount -or (Hash-File (Usb-Root-File $mount 'TVBASE-MEDIA.txt')) -ne $markerHash) { throw 'Cambio el medio/marcador al terminar' }
    $taskState.estado = 'verificado'
    $taskState.fecha = (Get-Date).ToString('o')
    $taskState.codigo_nativo = 0
    $taskState.detalle = 'ROM0.1.2 sin Bluetooth, auxiliar y guia copiados/leidos. Solo tres nombres viejos admisibles archivados/verificados antes de retirarlos. Recovery, marcador, informes y respaldos conservados. Sin formato, Update ni reinicio. Instalacion fisica pendiente.'
    Save-State
    Copy-Checked $taskResult (Join-Path $taskArchive 'resultado.json') (Get-Item -LiteralPath $taskResult).Length (Hash-File $taskResult)
    Get-Content -LiteralPath $taskResult -Raw
} catch {
    $taskState.estado = 'fallo'
    $taskState.codigo_nativo = 1
    $taskState.error_nativo = $_.Exception.ToString()
    Save-State
    throw
}
