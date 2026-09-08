param(
    [switch]$Prepare,
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($Prepare -and $CheckOnly) { throw 'Elegir -Prepare o -CheckOnly, no ambos.' }
# Sin argumentos se comprueba solamente. No crear recibos ni directorios en ese modo.
$taskReadOnly = -not $Prepare
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskDeliveryName = 'TVBASE-EXTRACCION'
$taskMediaId = 'tvbase-recovery-kingston-20260908'
$taskSummary = Join-Path $PSScriptRoot 'extractor-01-estado.json'
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
    $receiptPath = Local-Path 'diagnostico/extractor-recovery-0.1/COMPILACION.json'
    $receiptHash = Hash-Ordinary $receiptPath
    if ($expectedReceiptHash -ne '' -and $receiptHash -cne $expectedReceiptHash) { throw 'Cambió el recibo de compilación durante la preparación.' }
    if ((Get-Item -LiteralPath $receiptPath).Length -gt 2MB) { throw 'Recibo de compilación excesivo.' }
    $build = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($build.schema -cne 'tvbase-recovery-extractor-build-1' -or $build.state -cne 'built_verified_pc' -or $build.version -cne '0.1') { throw 'Compilación no corresponde al extractor.' }
    Require-Bool $build.signing_inputs_unchanged $true 'firma conservada'
    Require-Bool $build.sources_unchanged $true 'fuentes conservadas'
    Require-Bool $build.tv_contacted $false 'construcción sin contacto al TV'
    Require-Bool $build.physical_recovery_tested $false 'sin prueba física atribuida a compilación'
    $certSHA = 'a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc'
    $keySHA = 'cd0788004cfa998c7bbede4811b791187139504a01415b9d30df5609458398df'
    $trust = $build.recovery_v1_trust
    if ($trust.key_version -ne 1 -or $trust.rsa_exponent -ne 3 -or $trust.rsa_bits -ne 2048 -or
        $trust.digest -cne 'SHA1' -or $trust.certificate_sha256 -cne $certSHA -or $trust.keyfile_sha256 -cne $keySHA) { throw 'Confianza recovery distinta del original P291.' }
    $properties = @($build.source_sha256.PSObject.Properties)
    $sourceDir = Join-Path $taskRoot 'diagnostico/extractor-recovery-0.1'
    Assert-NoReparse $sourceDir $true
    $actual = @(@(Get-ChildItem -LiteralPath $sourceDir -File -Filter '*.go' | ForEach-Object {
        $_.FullName.Substring($taskRoot.Length+1).Replace('\','/')
    }) + @('diagnostico/extractor-recovery-0.1/go.mod','diagnostico/extractor-recovery-0.1/compilar.py'))
    if (Test-Path -LiteralPath (Join-Path $sourceDir 'go.sum')) { $actual += 'diagnostico/extractor-recovery-0.1/go.sum' }
    $actual = @($actual | Sort-Object)
    $expected = @($properties | ForEach-Object Name | Sort-Object)
    if ($properties.Count -lt 5 -or ($actual -join "`n") -cne ($expected -join "`n")) { throw 'El conjunto de fuentes Go/mod/builder cambió desde la compilación.' }
    foreach ($property in $properties) {
        if (-not $property.Name.StartsWith('diagnostico/extractor-recovery-0.1/',[StringComparison]::Ordinal) -or
            $property.Value -isnot [string] -or $property.Value -cnotmatch '^[0-9a-f]{64}$') { throw 'Entrada de fuente inválida.' }
        if ((Hash-Ordinary (Local-Path $property.Name)) -cne $property.Value) { throw 'Una fuente cambió desde la compilación.' }
    }
    $logs = @($build.command_logs)
    if ($logs.Count -lt 10 -or $build.go_host_tests.count -lt 1 -or $build.go_host_tests.os -cne 'windows') { throw 'Faltan pruebas o registros de construcción.' }
    foreach ($log in $logs) {
        if (($log.exit -isnot [int] -and $log.exit -isnot [long]) -or $log.exit -ne 0 -or $log.sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Un comando nativo no terminó con código cero.' }
        if ((Hash-Ordinary (Local-Path $log.file)) -cne $log.sha256) { throw 'Cambió un registro nativo de construcción.' }
    }
    $packages = @($build.packages)
    if ($packages.Count -ne 2 -or ((@($packages | ForEach-Object architecture | Sort-Object)) -join ',') -cne 'ARM32,ARM64') { throw 'Se requieren exactamente ARM32 y ARM64 independientes.' }
    $checked = New-Object 'Collections.Generic.List[object]'
    [long]$total = 0
    foreach ($package in $packages) {
        $name = 'TVBASE-EXTRACTOR-0.1-'+$package.architecture+'-RECOVERY.zip'
        $zip = Local-Path $package.file
        $allowedBase = Join-Path $taskRoot 'privado'
        $extractorPrivate = Join-Path $taskRoot 'diagnostico/extractor-recovery-0.1/privado'
        if ((-not $zip.StartsWith($allowedBase+'\',[StringComparison]::OrdinalIgnoreCase) -and
             -not $zip.StartsWith($extractorPrivate+'\',[StringComparison]::OrdinalIgnoreCase)) -or
            [IO.Path]::GetFileName($zip) -cne $name -or $package.bytes -gt 64MB) { throw 'Ruta de ZIP fuera de la salida privada autorizada.' }
        Check-File $zip $package.bytes $package.sha256
        foreach ($flag in @('python_signature_verified','openjdk_signature_verified','zip_crc_verified','zip_member_content_verified','linux_tests_compiled')) {
            Require-Bool $package.$flag $true $flag
        }
        Require-Bool $package.linux_tests_executed $false 'pruebas Linux solo compiladas'
        Require-Bool $package.elf.pt_interp_absent $true 'sin intérprete ELF'
        Require-Bool $package.elf.pt_dynamic_absent $true 'sin segmento dinámico'
        if ($package.elf.type -cne 'ET_EXEC' -or ($package.architecture -ceq 'ARM32' -and ($package.elf.elf_class_bits -ne 32 -or $package.elf.machine -ne 40)) -or
            ($package.architecture -ceq 'ARM64' -and ($package.elf.elf_class_bits -ne 64 -or $package.elf.machine -ne 183))) { throw 'ELF no corresponde a la arquitectura.' }
        if ($package.signature.signature_algorithm -cne 'RSA-PKCS1v1.5/SHA1' -or $package.signature.certificate_sha256 -cne $certSHA) { throw 'Firma del ZIP no corresponde.' }
        Require-Bool $package.signature.sha1_policy_replay_verified $true 'firma SHA1 verificada'
        Require-Bool $package.signature.oem_recovery_executed $false 'sin ejecución OEM atribuida'
        $meta = $package.metadata
        if ($meta.schema -cne 'tvbase-recovery-extractor-1' -or $meta.version -cne '0.1' -or $meta.operation -cne 'capture_read_only' -or
            $meta.package_id -cne ('TVBASE-EXTRACTOR-0.1-'+$package.architecture) -or $meta.architecture -cne $package.architecture -or
            $meta.media_directory -cne 'TVBASE-EXTRACCION' -or $meta.media_config -cne 'MEDIA.json' -or $meta.media_schema -cne 'tvbase-recovery-media-1' -or
            $meta.default_capture -cne 'inventory_only' -or $meta.plans_directory -cne 'PLANES' -or $meta.plan_schema -cne 'tvbase-recovery-plan-1' -or
            $meta.plan_match -cne 'exact_dt_identity' -or $meta.plan_source -cne 'validated_android_recognition_capture' -or $meta.goos -cne 'linux' -or
            ($package.architecture -ceq 'ARM32' -and ($meta.goarch -cne 'arm' -or $meta.goarm -cne '5')) -or
            ($package.architecture -ceq 'ARM64' -and ($meta.goarch -cne 'arm64' -or $meta.goarm64 -cne 'v8.0'))) { throw 'Metadatos o política de plan distintos.' }
        Require-Bool $meta.image_capture_requires_matching_apk_plan $true 'imágenes requieren plan APK'
        Require-Bool $meta.device_images_in_package $false 'sin imágenes del TV en el paquete'
        Require-Bool $meta.cgo_enabled $false 'ejecutable estático'
        if ($meta.extractor_sha256 -cne $package.binary_sha256) { throw 'Hash del ejecutable no coincide con metadatos.' }
        $metaSources = @($meta.source_sha256.PSObject.Properties | Sort-Object Name | ForEach-Object { $_.Name+'='+$_.Value })
        $buildSources = @($properties | Sort-Object Name | ForEach-Object { $_.Name+'='+$_.Value })
        if (($metaSources -join "`n") -cne ($buildSources -join "`n")) { throw 'Fuentes de metadatos y recibo difieren.' }
        $checked.Add([pscustomobject]@{Path=$zip;Name=$name;Bytes=$package.bytes;Sha256=$package.sha256;Architecture=$package.architecture})
        $total += [long]$package.bytes
    }
    return [pscustomobject]@{ReceiptHash=$receiptHash;Packages=@($checked.ToArray());Bytes=$total;SourceCount=$properties.Count}
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
    $public = [ordered]@{schema='tvbase-recovery-usb-delivery-1';state=$taskState.state;version='0.1';
        created_at=$taskState.created_at;completed_at=$taskState.completed_at;exit_code=$taskState.exit_code;
        compilation_receipt_sha256=$taskState.compilation_receipt_sha256;source_files_checked=$taskState.source_files_checked;
        files=@($taskState.files);existing_inventory_preserved=$taskState.existing_inventory_preserved;
        old_small_files_sha_verified=$taskState.old_small_files_sha_verified;old_large_files_metadata_verified=$taskState.old_large_files_metadata_verified;
        old_large_files_content_rehashed=$false;small_file_limit_bytes=$taskSmallLimit;
        before_file_bytes=$taskState.before_file_bytes;after_file_bytes=$taskState.after_file_bytes;
        free_bytes_after=$taskState.free_bytes_after;captures_directory_empty=$taskState.captures_directory_empty;plans_directory_empty=$taskState.plans_directory_empty;
        physical_recovery_tested=$false;tv_contacted=$false;default_capture='inventory_only';images_require_matching_apk_plan=$true;
        format_requested=$false;repair_requested=$false;existing_files_removed=0;
        safe_removal_pending=$true;volume_flush_verified=$false}
    $publicBytes = [Text.Encoding]::UTF8.GetBytes(($public | ConvertTo-Json -Depth 10))
    if (-not $taskSummaryReserved) { throw 'Recibo público no reservado por esta ejecución.' }
    Assert-NoReparse $taskSummary
    $file = [IO.File]::Open($taskSummary,[IO.FileMode]::Truncate,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($publicBytes,0,$publicBytes.Length); $file.Flush($true) } finally { $file.Dispose() }
}

# Todo este preflight es de lectura. Un recibo anterior, incluso de fallo,
# impide repetir la preparación y conserva la evidencia de esa ejecución.
if (Test-Path -LiteralPath $taskSummary) { throw 'Ya existe extractor-01-estado.json; revisar la entrega anterior, no repetir.' }
$taskBuild = Check-Build
$taskGuide = Local-Path 'diagnostico/extractor-recovery-0.1/LEEME-USB.txt'
$taskGuideSize = [long](Get-Item -LiteralPath $taskGuide).Length
if ($taskGuideSize -le 0 -or $taskGuideSize -gt 1MB) { throw 'Guía ausente o de tamaño inválido.' }
$taskGuideHash = Hash-Ordinary $taskGuide
$taskMediaBytes = [Text.Encoding]::UTF8.GetBytes((([ordered]@{schema='tvbase-recovery-media-1';media_id=$taskMediaId} | ConvertTo-Json -Compress)+"`n"))
$taskMount = Check-Kingston
$taskDestination = Join-Path $taskMount $taskDeliveryName
if (Test-Path -LiteralPath $taskDestination) { throw 'La carpeta del extractor ya existe; no sobrescribir ni limpiar.' }
$taskBefore = Snapshot-USB $taskMount
[long]$taskNewBytes = $taskBuild.Bytes + $taskGuideSize + $taskMediaBytes.Length
if ((Get-Volume -DriveLetter $taskMount.Substring(0,1)).SizeRemaining -lt $taskNewBytes+$taskReserve) { throw 'Debe quedar al menos 1 GiB libre tras copiar.' }
if ($taskReadOnly) {
    [ordered]@{state='checked_only';usb_written=$false;pc_receipt_written=$false;zip_bytes=$taskBuild.Bytes;
        packages=@($taskBuild.Packages | Select-Object Name,Bytes,Sha256,Architecture);source_files_checked=$taskBuild.SourceCount;existing_file_bytes=$taskBefore.FileBytes;
        existing_small_files_checked=$taskBefore.SmallCount;existing_large_files_metadata_checked=$taskBefore.LargeCount;
        planned_new_bytes=$taskNewBytes;reserved_free_bytes=$taskReserve;physical_recovery_tested=$false} | ConvertTo-Json
    return
}

$taskPrivateBase = Join-Path $taskRoot 'privado'
Assert-NoReparse $taskPrivateBase $true
$taskPrivate = Join-Path $taskPrivateBase ('extractor-usb01-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
if (Test-Path -LiteralPath $taskPrivate) { throw 'Carpeta privada de recibo ya existe.' }
New-Item -ItemType Directory -Path $taskPrivate | Out-Null
$taskPrivateReceipt = Join-Path $taskPrivate 'estado.json'
$reservation = [IO.File]::Open($taskSummary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
$reservation.Dispose()
$taskSummaryReserved = $true
$taskState = [ordered]@{state='preparing';created_at=(Get-Date).ToString('o');completed_at=$null;exit_code=$null;
    private_directory=$taskPrivate;usb_unique_id=$taskUsbId;drive_letter=$taskMount.Substring(0,1);
    compilation_receipt_sha256=$taskBuild.ReceiptHash;source_files_checked=$taskBuild.SourceCount;
    script_sha256=(Hash-Ordinary $PSCommandPath);files=@();before_inventory=$taskBefore.Rows;after_inventory=@();
    before_file_bytes=$taskBefore.FileBytes;after_file_bytes=$null;free_bytes_after=$null;
    existing_inventory_preserved=$false;old_small_files_sha_verified=0;old_large_files_metadata_verified=0;
    captures_directory_empty=$false;plans_directory_empty=$false;error=$null}
try {
    Save-State
    Assert-Mount $taskMount
    $null = Check-Build $taskBuild.ReceiptHash
    Check-File $taskGuide $taskGuideSize $taskGuideHash
    if (Test-Path -LiteralPath $taskDestination) { throw 'Apareció la carpeta destino; detener.' }
    New-Item -ItemType Directory -Path $taskDestination | Out-Null
    Assert-NoReparse $taskDestination $true
    New-Item -ItemType Directory -Path (Join-Path $taskDestination 'CAPTURAS') | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $taskDestination 'PLANES') | Out-Null
    Assert-Mount $taskMount
    $taskState.files += Write-NewBytes (Join-Path $taskDestination 'MEDIA.json') $taskMediaBytes
    Save-State
    Assert-Mount $taskMount
    $null = Check-Build $taskBuild.ReceiptHash
    foreach ($package in @($taskBuild.Packages)) {
        Assert-Mount $taskMount
        $taskState.files += Copy-NewFile $package.Path (Join-Path $taskDestination $package.Name) $package.Bytes $package.Sha256
        Save-State
    }
    Assert-Mount $taskMount
    $taskState.files += Copy-NewFile $taskGuide (Join-Path $taskDestination 'LEEME.txt') $taskGuideSize $taskGuideHash
    Save-State
    $null = Check-Build $taskBuild.ReceiptHash
    $taskAfter = Snapshot-USB $taskMount
    $taskState.after_inventory = $taskAfter.Rows
    $taskState.after_file_bytes = $taskAfter.FileBytes
    $oldAfter = @($taskAfter.Rows | Where-Object { $_.path -cne $taskDeliveryName -and -not $_.path.StartsWith($taskDeliveryName+'/',[StringComparison]::Ordinal) })
    if (($taskBefore.Rows | ConvertTo-Json -Depth 6 -Compress) -cne ($oldAfter | ConvertTo-Json -Depth 6 -Compress)) { throw 'Cambió el inventario o un archivo anterior.' }
    $newAfter = @($taskAfter.Rows | Where-Object { $_.path -ceq $taskDeliveryName -or $_.path.StartsWith($taskDeliveryName+'/',[StringComparison]::Ordinal) })
    $expectedPaths = @($taskDeliveryName,($taskDeliveryName+'/CAPTURAS'),($taskDeliveryName+'/PLANES'),($taskDeliveryName+'/MEDIA.json'),
        ($taskDeliveryName+'/TVBASE-EXTRACTOR-0.1-ARM32-RECOVERY.zip'),($taskDeliveryName+'/TVBASE-EXTRACTOR-0.1-ARM64-RECOVERY.zip'),($taskDeliveryName+'/LEEME.txt')) | Sort-Object
    if ((($newAfter.path | Sort-Object) -join "`n") -cne ($expectedPaths -join "`n")) { throw 'Contenido nuevo inesperado en la entrega.' }
    if ($taskAfter.FileBytes -ne $taskBefore.FileBytes+$taskNewBytes -or @($taskState.files).Count -ne 4) { throw 'Inventario total o archivos nuevos no coinciden.' }
    foreach ($newFile in @($taskState.files)) {
        Assert-Mount $taskMount
        Check-File (Join-Path $taskDestination $newFile.name) $newFile.bytes $newFile.sha256
    }
    foreach ($emptyDir in @('CAPTURAS','PLANES')) {
        Assert-NoReparse (Join-Path $taskDestination $emptyDir) $true
        if (@(Get-ChildItem -LiteralPath (Join-Path $taskDestination $emptyDir) -Force).Count -ne 0) { throw ($emptyDir+' no está vacío.') }
    }
    Assert-Mount $taskMount
    [long]$taskFree = (Get-Volume -DriveLetter $taskMount.Substring(0,1)).SizeRemaining
    if ($taskFree -lt $taskReserve) { throw 'No quedó la reserva mínima de 1 GiB.' }
    $taskState.free_bytes_after = $taskFree
    $taskState.existing_inventory_preserved = $true
    $taskState.old_small_files_sha_verified = $taskBefore.SmallCount
    $taskState.old_large_files_metadata_verified = $taskBefore.LargeCount
    $taskState.captures_directory_empty = $true
    $taskState.plans_directory_empty = $true
    $taskState.state = 'verified'
    $taskState.completed_at = (Get-Date).ToString('o')
    $taskState.exit_code = 0
    Save-State
    [ordered]@{state='verified';files_verified=4;existing_inventory_preserved=$true;physical_recovery_tested=$false;
        volume_flush_verified=$false;safe_removal_pending=$true;exit_code=0} | ConvertTo-Json
} catch {
    $taskState.state='failed';$taskState.exit_code=1;$taskState.completed_at=(Get-Date).ToString('o')
    $taskState.error=$_.Exception.ToString()
    Save-State
    throw
}
