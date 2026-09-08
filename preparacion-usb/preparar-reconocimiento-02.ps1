param(
    [switch]$Prepare,
    [switch]$CheckOnly,
    [Parameter(Mandatory=$true)][string]$PlanSource
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($Prepare -and $CheckOnly) { throw 'Elegir -Prepare o -CheckOnly, no ambos.' }
# Sin argumentos se comprueba solamente. No crear recibos ni directorios en ese modo.
$taskReadOnly = -not $Prepare
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskDeliveryName = 'TVBASE-RECONOCIMIENTO'
$taskMediaId = 'tvbase-recognition-kingston-20260908-c73d9a14'
$taskSummary = Join-Path $PSScriptRoot 'reconocimiento-02-estado.json'
$taskSmallLimit = [long](64MB)
$taskReserve = [long](1GB)
$taskState = $null
$taskPrivateReceipt = $null
$taskSummaryReserved = $false

function Assert-NoReparse([string]$path, [bool]$directory = $false) {
    $full = [IO.Path]::GetFullPath($path)
    $current = $full
    $first = $true
    while (-not [string]::IsNullOrEmpty($current)) {
        $item = Get-Item -LiteralPath $current -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Ruta con enlace o reparse point.' }
        if ($first -and -not $directory) {
            if ($item.PSIsContainer) { throw 'Se esperaba archivo ordinario.' }
        } elseif (-not $item.PSIsContainer) { throw 'Se esperaba directorio ordinario.' }
        $first = $false
        $next = [IO.Path]::GetDirectoryName($current.TrimEnd('\'))
        if ([string]::IsNullOrEmpty($next) -or $next -eq $current) { break }
        # C:\ termina aquí: no consultar C: relativo al directorio de la unidad.
        if ($next -match '^[A-Za-z]:$') { $next += '\' }
        if ($next -eq $current) { break }
        $current = $next
    }
}

function Local-Path([string]$relative) {
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or
        @($relative -split '[\\/]' | Where-Object { $_ -in @('.', '..', '') }).Count -gt 0) { throw 'Ruta local relativa ambigua.' }
    $full = [IO.Path]::GetFullPath((Join-Path $taskRoot $relative))
    if (-not $full.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta fuera del proyecto.' }
    Assert-NoReparse $full
    return $full
}

function Hash-Ordinary([string]$path) {
    Assert-NoReparse $path
    $before = Get-Item -LiteralPath $path -Force
    $length = [long]$before.Length
    $writeTime = $before.LastWriteTimeUtc.Ticks
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    $after = Get-Item -LiteralPath $path -Force
    if ($after.Length -ne $length -or $after.LastWriteTimeUtc.Ticks -ne $writeTime -or
        ($after.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $hash -cnotmatch '^[0-9a-f]{64}$') { throw 'Archivo cambió o SHA256 inválido.' }
    return $hash
}

function Check-File([string]$path, $size, [string]$sha256) {
    if (($size -isnot [int] -and $size -isnot [long]) -or $size -le 0 -or $sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Tamaño o SHA256 inválido.' }
    Assert-NoReparse $path
    if ((Get-Item -LiteralPath $path -Force).Length -ne $size -or (Hash-Ordinary $path) -cne $sha256) { throw 'Archivo distinto del esperado.' }
}

function Require-Bool($value, [bool]$expected, [string]$label) {
    if ($value -isnot [bool] -or $value -ne $expected) { throw ('Validación ausente o distinta: '+$label) }
}

function Check-Kingston {
    # Identidad y geometría iguales a adquirir-usb.ps1; no seleccionar por letra.
    $disks = @(Get-Disk | Where-Object UniqueId -eq $taskUsbId)
    if ($disks.Count -ne 1 -or $disks[0].FriendlyName -ne 'Kingston DataTraveler 3.0' -or
        $disks[0].Size -ne 30943995904 -or $disks[0].BusType -ne 'USB' -or
        $disks[0].IsSystem -or $disks[0].IsBoot) { throw 'No coincide el Kingston autorizado.' }
    $parts = @(Get-Partition -DiskNumber $disks[0].Number | Where-Object DriveLetter)
    if ($parts.Count -ne 1) { throw 'Montaje ambiguo.' }
    $volumes = @($parts[0] | Get-Volume)
    if ($volumes.Count -ne 1 -or $volumes[0].FileSystem -ne 'FAT32' -or
        $volumes[0].FileSystemLabel -ne 'TVBASE' -or $volumes[0].Size -ne 30925651968) { throw 'Volumen distinto.' }
    $mount = "$($parts[0].DriveLetter):\"
    Assert-NoReparse $mount $true
    $marker = Join-Path $mount 'TVBASE-MEDIA.txt'
    Assert-NoReparse $marker
    if ((Get-Item -LiteralPath $marker).Length -gt 4096 -or
        (Get-Content -LiteralPath $marker -Raw).Trim() -cne 'TVBASE-P291-20260906-4dc82786') { throw 'Marcador diferente.' }
    return $mount
}

function Assert-Mount([string]$mount) {
    if ((Check-Kingston) -cne $mount) { throw 'Cambió el montaje del Kingston.' }
}

function Enumerate-Tree([string]$base) {
    # Recorrer cada directorio después de verificarlo evita seguir junctions
    # accidentalmente con un -Recurse amplio.
    Assert-NoReparse $base $true
    $queue = New-Object 'Collections.Generic.Queue[string]'
    $queue.Enqueue($base)
    $items = New-Object 'Collections.Generic.List[object]'
    while ($queue.Count -gt 0) {
        $directory = $queue.Dequeue()
        Assert-NoReparse $directory $true
        foreach ($item in @(Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop)) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Enlace dentro del árbol; no continuar.' }
            $full = [IO.Path]::GetFullPath($item.FullName)
            if (-not $full.StartsWith($base.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Elemento fuera del árbol.' }
            $items.Add($item)
            if ($item.PSIsContainer) { $queue.Enqueue($full) }
        }
    }
    return @($items.ToArray() | Sort-Object FullName)
}

function Check-Build([string]$expectedReceiptHash = '') {
    $receiptPath = Local-Path 'diagnostico/reconocedor-0.2/COMPILACION.json'
    $receiptHash = Hash-Ordinary $receiptPath
    if ($expectedReceiptHash -ne '' -and $receiptHash -cne $expectedReceiptHash) { throw 'Cambió el recibo de compilación durante la preparación.' }
    if ((Get-Item -LiteralPath $receiptPath).Length -gt 1MB) { throw 'Recibo de compilación excesivo.' }
    $build = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($build.state -cne 'built_verified_pc' -or $build.version -cne '0.2' -or
        $build.package -cne 'com.tvbase.reconocimiento' -or $build.min_api -ne 21 -or $build.target_api -ne 28) { throw 'Compilación no corresponde al reconocedor.' }
    Require-Bool $build.signing_inputs_unchanged $true 'firma conservada'
    Require-Bool $build.network_permission $false 'sin permiso de red'
    Require-Bool $build.root_or_adb $false 'sin root ni ADB'
    if ($build.signer_sha256 -cne 'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613') { throw 'Firmante distinto del componente aprobado.' }
    $properties = @($build.source_sha256.PSObject.Properties)
    if ($properties.Count -lt 2) { throw 'Faltan hashes de fuentes.' }
    $sourceDir = Join-Path $taskRoot 'diagnostico/reconocedor-0.2/src'
    $actual = @(Enumerate-Tree $sourceDir | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
        $_.FullName.Substring($taskRoot.Length+1).Replace('\','/')
    } | Sort-Object)
    $expected = @($properties | ForEach-Object Name | Sort-Object)
    if (($actual -join "`n") -cne ($expected -join "`n")) { throw 'El conjunto de fuentes cambió desde la compilación.' }
    foreach ($property in $properties) {
        if (-not $property.Name.StartsWith('diagnostico/reconocedor-0.2/src/',[StringComparison]::Ordinal) -or
            $property.Value -isnot [string] -or $property.Value -cnotmatch '^[0-9a-f]{64}$') { throw 'Entrada de fuente inválida.' }
        if ((Hash-Ordinary (Local-Path $property.Name)) -cne $property.Value) { throw 'Una fuente cambió desde la compilación.' }
    }
    $apk = Local-Path $build.apk
    $allowedBase = Join-Path $taskRoot 'diagnostico/reconocedor-0.2/privado'
    if (-not $apk.StartsWith($allowedBase+'\',[StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($apk) -cne 'Reconocimiento-TVBase-0.2.apk' -or $build.bytes -gt 512MB) { throw 'Ruta de APK fuera de la salida autorizada.' }
    Check-File $apk $build.bytes $build.sha256
    return [pscustomobject]@{ReceiptHash=$receiptHash;Apk=$apk;Bytes=$build.bytes;Sha256=$build.sha256;SourceCount=$properties.Count}
}

function Snapshot-USB([string]$mount) {
    Assert-Mount $mount
    $rows = New-Object 'Collections.Generic.List[object]'
    [long]$total = 0
    [long]$small = 0
    [long]$large = 0
    foreach ($item in @(Enumerate-Tree $mount)) {
        $relative = $item.FullName.Substring($mount.Length).Replace('\','/')
        if ($item.PSIsContainer) {
            $rows.Add([ordered]@{path=$relative;kind='directory'})
        } else {
            [long]$length = $item.Length
            $hash = $null
            if ($length -le $taskSmallLimit) { $hash = Hash-Ordinary $item.FullName; $small++ } else { $large++ }
            $rows.Add([ordered]@{path=$relative;kind='file';bytes=$length;write_ticks=$item.LastWriteTimeUtc.Ticks;sha256=$hash})
            $total += $length
        }
    }
    Assert-Mount $mount
    return [pscustomobject]@{Rows=@($rows.ToArray() | Sort-Object { $_.path });FileBytes=$total;SmallCount=$small;LargeCount=$large}
}

function Bytes-SHA([byte[]]$bytes) {
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
    finally { $hash.Dispose() }
}

function Write-NewBytes([string]$target, [byte[]]$bytes) {
    Assert-NoReparse ([IO.Path]::GetDirectoryName($target)) $true
    $file = [IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($bytes,0,$bytes.Length); $file.Flush($true) } finally { $file.Dispose() }
    $expected = Bytes-SHA $bytes
    Check-File $target ([long]$bytes.Length) $expected
    return [ordered]@{name=[IO.Path]::GetFileName($target);bytes=[long]$bytes.Length;sha256=$expected;file_flush_verified=$true;readback_verified=$true}
}

function Copy-NewFile([string]$source,[string]$target,$size,[string]$expected) {
    Check-File $source $size $expected
    Assert-NoReparse ([IO.Path]::GetDirectoryName($target)) $true
    $inputFile = [IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        $outputFile = [IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $inputFile.CopyTo($outputFile); $outputFile.Flush($true) } finally { $outputFile.Dispose() }
    } finally { $inputFile.Dispose() }
    Check-File $source $size $expected
    Check-File $target $size $expected
    return [ordered]@{name=[IO.Path]::GetFileName($target);bytes=$size;sha256=$expected;file_flush_verified=$true;readback_verified=$true}
}

function Save-State {
    Assert-NoReparse ([IO.Path]::GetDirectoryName($taskPrivateReceipt)) $true
    if (Test-Path -LiteralPath $taskPrivateReceipt) { Assert-NoReparse $taskPrivateReceipt }
    $privateBytes = [Text.Encoding]::UTF8.GetBytes(($taskState | ConvertTo-Json -Depth 15))
    $file = [IO.File]::Open($taskPrivateReceipt,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($privateBytes,0,$privateBytes.Length); $file.Flush($true) } finally { $file.Dispose() }
    $public = [ordered]@{schema='tvbase-recognition-usb-delivery-1';state=$taskState.state;version='0.2';
        created_at=$taskState.created_at;completed_at=$taskState.completed_at;exit_code=$taskState.exit_code;
        compilation_receipt_sha256=$taskState.compilation_receipt_sha256;source_files_checked=$taskState.source_files_checked;
        files=@($taskState.files);existing_inventory_preserved=$taskState.existing_inventory_preserved;
        old_small_files_sha_verified=$taskState.old_small_files_sha_verified;old_large_files_metadata_verified=$taskState.old_large_files_metadata_verified;
        old_large_files_content_rehashed=$false;small_file_limit_bytes=$taskSmallLimit;
        before_file_bytes=$taskState.before_file_bytes;after_file_bytes=$taskState.after_file_bytes;
        free_bytes_after=$taskState.free_bytes_after;reports_preserved=$true;plan_operation="capture_read_only";
        android_tested=$false;android_usb_export_tested=$false;tv_contacted=$false;
        format_requested=$false;repair_requested=$false;existing_files_removed=0;
        safe_removal_pending=$true;volume_flush_verified=$false}
    $publicBytes = [Text.Encoding]::UTF8.GetBytes(($public | ConvertTo-Json -Depth 10))
    if (-not $taskSummaryReserved) { throw 'Recibo público no reservado por esta ejecución.' }
    Assert-NoReparse $taskSummary
    $file = [IO.File]::Open($taskSummary,[IO.FileMode]::Truncate,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($publicBytes,0,$publicBytes.Length); $file.Flush($true) } finally { $file.Dispose() }
}


if (Test-Path -LiteralPath $taskSummary) { throw 'Ya existe recibo02; no repetir preparación.' }
$taskBuild = Check-Build
$taskGuide = Local-Path 'diagnostico/reconocedor-0.2/LEEME-USB.txt'
$taskGuideSize = [long](Get-Item -LiteralPath $taskGuide).Length
$taskGuideHash = Hash-Ordinary $taskGuide
if ($taskGuideSize -le 0 -or $taskGuideSize -gt 1MB) { throw 'Guía inválida.' }
$taskPlan = Local-Path $PlanSource
if (-not $taskPlan.StartsWith((Join-Path $taskRoot 'privado')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'El plan local debe ser privado.' }
$taskPlanSize = [long](Get-Item -LiteralPath $taskPlan).Length
$taskPlanHash = '112e438c447c64257d897a7d0947cb4cf07e2884a52b5e3960e471756c9eeac3'
Check-File $taskPlan $taskPlanSize $taskPlanHash
if ($taskPlanSize -gt 16384) { throw 'Plan excesivo.' }
$taskPlanObject = Get-Content -LiteralPath $taskPlan -Raw -Encoding UTF8 | ConvertFrom-Json
if ($taskPlanObject.schema -cne 'tvbase-recovery-plan-1' -or $taskPlanObject.operation -cne 'capture_read_only' -or $taskPlanObject.profile -cne 'p271') { throw 'Plan distinto.' }
$taskMount = Check-Kingston
$taskDestination = Join-Path $taskMount $taskDeliveryName
Assert-NoReparse $taskDestination $true
$taskMedia = Get-Content -LiteralPath (Join-Path $taskDestination 'MEDIA.json') -Raw | ConvertFrom-Json
if ($taskMedia.schema -cne 'tvbase-recognition-media-1' -or $taskMedia.media_id -cne $taskMediaId) { throw 'Marcador de reconocimiento distinto.' }
$taskPlanDir = Join-Path $taskMount 'TVBASE-EXTRACCION\PLANES'
Assert-NoReparse $taskPlanDir $true
$taskRecoveryMedia = Get-Content -LiteralPath (Join-Path $taskMount 'TVBASE-EXTRACCION\MEDIA.json') -Raw | ConvertFrom-Json
if ($taskRecoveryMedia.schema -cne 'tvbase-recovery-media-1' -or $taskRecoveryMedia.media_id -cne 'tvbase-recovery-kingston-20260908') { throw 'Marcador de extracción distinto.' }
if (@(Get-ChildItem -LiteralPath $taskPlanDir -Force).Count -ne 0) { throw 'PLANES ya contiene datos; no duplicar coincidencias.' }
$taskNew = @(
    [pscustomobject]@{Source=$taskBuild.Apk;Relative='TVBASE-RECONOCIMIENTO/Reconocimiento-TVBase-0.2.apk';Bytes=$taskBuild.Bytes;Hash=$taskBuild.Sha256},
    [pscustomobject]@{Source=$taskGuide;Relative='TVBASE-RECONOCIMIENTO/LEEME-0.2.txt';Bytes=$taskGuideSize;Hash=$taskGuideHash},
    [pscustomobject]@{Source=$taskPlan;Relative='TVBASE-EXTRACCION/PLANES/P271.json';Bytes=$taskPlanSize;Hash=$taskPlanHash}
)
foreach ($item in $taskNew) { if (Test-Path -LiteralPath (Join-Path $taskMount $item.Relative)) { throw 'Un destino nuevo ya existe.' } }
$taskBefore = Snapshot-USB $taskMount
[long]$taskNewBytes = $taskBuild.Bytes+$taskGuideSize+$taskPlanSize
if ((Get-Volume -DriveLetter $taskMount.Substring(0,1)).SizeRemaining -lt $taskNewBytes+$taskReserve) { throw 'Espacio insuficiente.' }
if ($taskReadOnly) {
    [ordered]@{state='checked_only';usb_written=$false;new_files=3;source_files_checked=$taskBuild.SourceCount;
        existing_small_files_checked=$taskBefore.SmallCount;existing_large_files_metadata_checked=$taskBefore.LargeCount;
        planned_new_bytes=$taskNewBytes;old_files_removed=0;plan_installation_authorized=$false} | ConvertTo-Json
    return
}
$taskPrivateBase = Join-Path $taskRoot 'privado'
Assert-NoReparse $taskPrivateBase $true
$taskPrivate = Join-Path $taskPrivateBase ('reconocimiento-usb02-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $taskPrivate -ErrorAction Stop | Out-Null
$taskPrivateReceipt = Join-Path $taskPrivate 'estado.json'
$reservation = [IO.File]::Open($taskSummary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
$reservation.Dispose();$taskSummaryReserved=$true
$taskState = [ordered]@{state='preparing';created_at=(Get-Date).ToString('o');completed_at=$null;exit_code=$null;
    private_directory=$taskPrivate;usb_unique_id=$taskUsbId;drive_letter=$taskMount.Substring(0,1);
    compilation_receipt_sha256=$taskBuild.ReceiptHash;source_files_checked=$taskBuild.SourceCount;
    script_sha256=(Hash-Ordinary $PSCommandPath);files=@();before_inventory=$taskBefore.Rows;after_inventory=@();
    before_file_bytes=$taskBefore.FileBytes;after_file_bytes=$null;free_bytes_after=$null;
    existing_inventory_preserved=$false;old_small_files_sha_verified=0;old_large_files_metadata_verified=0;error=$null}
try {
    Save-State
    foreach ($item in $taskNew) {
        Assert-Mount $taskMount
        $null=Check-Build $taskBuild.ReceiptHash
        $record=Copy-NewFile $item.Source (Join-Path $taskMount $item.Relative) $item.Bytes $item.Hash
        $record['relative_path']=$item.Relative
        $taskState.files+=$record
        Save-State
    }
    $taskAfter=Snapshot-USB $taskMount
    $taskState.after_inventory=$taskAfter.Rows;$taskState.after_file_bytes=$taskAfter.FileBytes
    $newPaths=@($taskNew | ForEach-Object Relative)
    $oldAfter=@($taskAfter.Rows | Where-Object { $_.path -cnotin $newPaths })
    if (($taskBefore.Rows | ConvertTo-Json -Depth 6 -Compress) -cne ($oldAfter | ConvertTo-Json -Depth 6 -Compress)) { throw 'Cambió un elemento anterior.' }
    if ($taskAfter.FileBytes -ne $taskBefore.FileBytes+$taskNewBytes -or $taskAfter.Rows.Count -ne $taskBefore.Rows.Count+3) { throw 'Inventario final distinto.' }
    foreach ($item in $taskNew) {Assert-Mount $taskMount;Check-File (Join-Path $taskMount $item.Relative) $item.Bytes $item.Hash}
    $taskState.free_bytes_after=[long](Get-Volume -DriveLetter $taskMount.Substring(0,1)).SizeRemaining
    $taskState.existing_inventory_preserved=$true
    $taskState.old_small_files_sha_verified=$taskBefore.SmallCount;$taskState.old_large_files_metadata_verified=$taskBefore.LargeCount
    $taskState.state='verified';$taskState.exit_code=0;$taskState.completed_at=(Get-Date).ToString('o')
    Save-State
    [ordered]@{state='verified';files_verified=3;existing_inventory_preserved=$true;format=$false;removed=0;exit_code=0;safe_removal_pending=$true;volume_flush_verified=$false} | ConvertTo-Json
} catch {
    $taskState.state='failed';$taskState.exit_code=1;$taskState.completed_at=(Get-Date).ToString('o');$taskState.error=$_.Exception.ToString();Save-State;throw
}
