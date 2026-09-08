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
$taskSummary = Join-Path $PSScriptRoot 'extraccion-rk3229-c-estado.json'
$taskSmallLimit = [long](64MB)
# Reserva de preparación: 8 GiB principal + 128 MiB auxiliares + 128 MiB margen.
$taskReserve = [long](8GB + 128MB + 128MB)
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


function Check-PlanSource {
    $plan = Local-Path 'privado/planes-recovery-20260908/RK3229-C-58606210.json'
    $expectedPlanSHA = 'f5f15963b2d8d98eb81e17b45f824f541ef2b47f7d511ac0b29e12d5a7b67311'
    $size = [long](Get-Item -LiteralPath $plan).Length
    if ($size -le 0 -or $size -gt 16384 -or (Hash-Ordinary $plan) -cne $expectedPlanSHA) { throw 'Plan local distinto del aprobado.' }
    $report = Local-Path 'diagnostico/reconocimiento-20260908-rk3229-manual/privado/zips/TVBASE-rockchip-rk3229-1e68b708-58606210.zip'
    Check-File $report 39863 '96e18c9ae63d7aab82f0217f6e9b3f353d7b9cb1318f986e6c04fdfb2b155e03'
    $planner = Local-Path 'diagnostico/extractor-recovery-0.1/preparar-plan.py'
    $python = 'C:\Users\usuario-local\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    Assert-NoReparse $python
    # Sólo se ejecutan helpers puros de verificación; no prepare_plan ni escritura.
    $code = 'import sys,pathlib,types,json; p=pathlib.Path(sys.argv[1]); m=types.ModuleType("tvbase_plan_check"); m.__file__=str(p); exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__); v=m.load_importer(); item=v.verify_archive(sys.argv[2],emit=None); actual=json.loads(pathlib.Path(sys.argv[3]).read_bytes()); assert actual==m.make_plan(item); assert item["report"]["capture_state"]=="inventory_with_explicit_limits"; assert actual["expected_dt"]=="rockchip,rk3229"; print("plan_verified_read_only")'
    $result = @($code | & $python -X utf8 -B - $planner $report $plan)
    $nativeExit = $LASTEXITCODE
    if ($nativeExit -ne 0 -or ($result -join "`n") -cne 'plan_verified_read_only') { throw 'Verificación nativa del ZIP/plan falló; no preparar USB.' }
    Check-File $plan $size $expectedPlanSHA
    return [pscustomobject]@{Path=$plan;Bytes=$size;Sha256=$expectedPlanSHA;NativeExit=$nativeExit}
}

function Check-ExistingDelivery([string]$mount,$build,[bool]$after = $false) {
    Assert-Mount $mount
    $base = Join-Path $mount $taskDeliveryName
    Assert-NoReparse $base $true
    $media = Join-Path $base 'MEDIA.json'
    Check-File $media 84 '97fcd465e829454440a91034995f2ed00ed861e5d9b636e852aaa3c754846bbd'
    $marker = Get-Content -LiteralPath $media -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($marker.schema -cne 'tvbase-recovery-media-1' -or $marker.media_id -cne $taskMediaId) { throw 'Marcador del extractor distinto.' }
    $arm32 = @($build.Packages | Where-Object Architecture -ceq 'ARM32')
    if ($arm32.Count -ne 1) { throw 'Falta paquete ARM32 verificado.' }
    Check-File (Join-Path $base $arm32[0].Name) $arm32[0].Bytes $arm32[0].Sha256
    Assert-NoReparse (Join-Path $base 'CAPTURAS') $true
    $plans = Join-Path $base 'PLANES'
    Assert-NoReparse $plans $true
    $entries = @(Get-ChildItem -LiteralPath $plans -Force)
    $allowed = @('P271.json')
    if ($after) { $allowed += 'RK3229-C.json' }
    if ($entries.Count -ne $allowed.Count) { throw 'PLANES tiene contenido inesperado; conservar y revisar en PC.' }
    foreach ($entry in $entries) {
        Assert-NoReparse $entry.FullName
        if ($entry.Name -cnotin $allowed) { throw 'Nombre de plan inesperado; no añadir otro coincidente.' }
    }
    $oldPlan = Join-Path $plans 'P271.json'
    Check-File $oldPlan 376 '112e438c447c64257d897a7d0947cb4cf07e2884a52b5e3960e471756c9eeac3'
    $old = Get-Content -LiteralPath $oldPlan -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($old.schema -cne 'tvbase-recovery-plan-1' -or $old.operation -cne 'capture_read_only' -or $old.expected_dt -cne 'gxlx_p271_1g') { throw 'Plan P271 distinto.' }
    if ($after) {
        $new = Join-Path $plans 'RK3229-C.json'
        Check-File $new $taskPlan.Bytes $taskPlan.Sha256
        $parsed = Get-Content -LiteralPath $new -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($parsed.expected_dt -cne 'rockchip,rk3229') { throw 'Plan Rockchip diferente.' }
    }
}

function Save-State {
    Assert-NoReparse ([IO.Path]::GetDirectoryName($taskPrivateReceipt)) $true
    if (Test-Path -LiteralPath $taskPrivateReceipt) { Assert-NoReparse $taskPrivateReceipt }
    $privateBytes = [Text.Encoding]::UTF8.GetBytes(($taskState | ConvertTo-Json -Depth 15))
    $file = [IO.File]::Open($taskPrivateReceipt,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($privateBytes,0,$privateBytes.Length); $file.Flush($true) } finally { $file.Dispose() }
    $public = [ordered]@{schema='tvbase-recovery-plan-usb-delivery-1';state=$taskState.state;extractor_version='0.1';target_variant='RK3229-C';
        created_at=$taskState.created_at;completed_at=$taskState.completed_at;exit_code=$taskState.exit_code;
        compilation_receipt_sha256=$taskState.compilation_receipt_sha256;source_files_checked=$taskState.source_files_checked;
        script_sha256=$taskState.script_sha256;plan_source_verified_native_exit=$taskState.plan_source_verified_native_exit;
        existing_arm32_zip_sha256='1f45405d22193b1e09cc694bc5328be6e8aa7f071e0d77323cacc15611063f08';
        files=@($taskState.files);existing_inventory_preserved=$taskState.existing_inventory_preserved;
        old_small_files_sha_verified=$taskState.old_small_files_sha_verified;old_large_files_metadata_verified=$taskState.old_large_files_metadata_verified;
        old_large_files_content_rehashed=$false;small_file_limit_bytes=$taskSmallLimit;
        before_file_bytes=$taskState.before_file_bytes;after_file_bytes=$taskState.after_file_bytes;free_bytes_after=$taskState.free_bytes_after;
        capture_space_budget_bytes=$taskReserve;capture_space_budget_is_hardware_measurement=$false;
        reports_preserved=$taskState.existing_inventory_preserved;existing_p271_plan_preserved=$taskState.existing_inventory_preserved;
        plan_files_added=@($taskState.files | Where-Object name -ceq 'RK3229-C.json').Count;
        dt_matching_scope='software_profile_not_physical_identity';recovery_signature_acceptance_tested=$false;recovery_extractor_executed=$false;
        tv_contacted=$false;format_requested=$false;repair_requested=$false;existing_files_removed=0;existing_files_replaced=0;
        safe_removal_pending=$true;volume_flush_verified=$false}
    $publicBytes = [Text.Encoding]::UTF8.GetBytes(($public | ConvertTo-Json -Depth 10))
    if (-not $taskSummaryReserved) { throw 'Recibo público no reservado por esta ejecución.' }
    Assert-NoReparse $taskSummary
    $file = [IO.File]::Open($taskSummary,[IO.FileMode]::Truncate,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($publicBytes,0,$publicBytes.Length); $file.Flush($true) } finally { $file.Dispose() }
}

if (Test-Path -LiteralPath $taskSummary) { throw 'Ya existe recibo RK3229-C; no repetir preparación.' }
$taskBuild = Check-Build '2e07c944881cd8a0debcc9247798f87c695aa6646f8b1d43cf0d62885decb338'
$taskPlan = Check-PlanSource
$taskGuide = Local-Path 'docs/evidencia/LEEME-EXTRACCION-RK3229-C.txt'
$taskGuideSize = [long](Get-Item -LiteralPath $taskGuide).Length
$taskGuideHash = Hash-Ordinary $taskGuide
if ($taskGuideSize -le 0 -or $taskGuideSize -gt 1MB) { throw 'Guía inválida.' }
$taskMount = Check-Kingston
Check-ExistingDelivery $taskMount $taskBuild
$taskNew = @(
    [pscustomobject]@{Source=$taskPlan.Path;Relative='TVBASE-EXTRACCION/PLANES/RK3229-C.json';Bytes=$taskPlan.Bytes;Hash=$taskPlan.Sha256},
    [pscustomobject]@{Source=$taskGuide;Relative='TVBASE-EXTRACCION/LEEME-RK3229-C.txt';Bytes=$taskGuideSize;Hash=$taskGuideHash}
)
foreach ($item in $taskNew) { if (Test-Path -LiteralPath (Join-Path $taskMount $item.Relative)) { throw 'Un destino nuevo ya existe; no sobrescribir.' } }
$taskBefore = Snapshot-USB $taskMount
[long]$taskNewBytes = $taskPlan.Bytes+$taskGuideSize
$taskFree = [long](Get-Volume -DriveLetter $taskMount.Substring(0,1)).SizeRemaining
if ($taskFree -lt $taskNewBytes+$taskReserve) { throw 'Espacio insuficiente para entrega y reserva de captura.' }
if ($taskReadOnly) {
    [ordered]@{state='checked_only';usb_written=$false;new_files=2;source_files_checked=$taskBuild.SourceCount;
        plan_source_verified_native_exit=$taskPlan.NativeExit;existing_arm32_zip_verified=$true;existing_p271_plan_verified=$true;
        matching_rk_plans_before=0;matching_rk_plans_after_prepare=1;
        existing_small_files_checked=$taskBefore.SmallCount;existing_large_files_metadata_checked=$taskBefore.LargeCount;
        planned_new_bytes=$taskNewBytes;capture_space_budget_bytes=$taskReserve;free_bytes=$taskFree;
        old_files_removed=0;tv_modified=$false} | ConvertTo-Json
    return
}
$taskPrivateBase = Join-Path $taskRoot 'privado'
Assert-NoReparse $taskPrivateBase $true
$taskPrivate = Join-Path $taskPrivateBase ('extraccion-rk3229-c-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $taskPrivate -ErrorAction Stop | Out-Null
$taskPrivateReceipt = Join-Path $taskPrivate 'estado.json'
$reservation = [IO.File]::Open($taskSummary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
$reservation.Dispose();$taskSummaryReserved=$true
$taskState = [ordered]@{state='preparing';created_at=(Get-Date).ToString('o');completed_at=$null;exit_code=$null;
    private_directory=$taskPrivate;usb_unique_id=$taskUsbId;drive_letter=$taskMount.Substring(0,1);
    compilation_receipt_sha256=$taskBuild.ReceiptHash;source_files_checked=$taskBuild.SourceCount;
    plan_source=$taskPlan.Path;plan_source_sha256=$taskPlan.Sha256;plan_source_verified_native_exit=$taskPlan.NativeExit;
    script_sha256=(Hash-Ordinary $PSCommandPath);files=@();before_inventory=$taskBefore.Rows;after_inventory=@();
    before_file_bytes=$taskBefore.FileBytes;after_file_bytes=$null;free_bytes_after=$null;
    existing_inventory_preserved=$false;old_small_files_sha_verified=0;old_large_files_metadata_verified=0;error=$null}
try {
    Save-State
    foreach ($item in $taskNew) {
        Assert-Mount $taskMount
        $null=Check-Build $taskBuild.ReceiptHash
        $null=Check-PlanSource
        Check-ExistingDelivery $taskMount $taskBuild ($taskState.files.Count -gt 0)
        $record=Copy-NewFile $item.Source (Join-Path $taskMount $item.Relative) $item.Bytes $item.Hash
        $record['relative_path']=$item.Relative
        $taskState.files+=$record
        Save-State
    }
    Check-ExistingDelivery $taskMount $taskBuild $true
    $taskAfter=Snapshot-USB $taskMount
    $taskState.after_inventory=$taskAfter.Rows;$taskState.after_file_bytes=$taskAfter.FileBytes
    $newPaths=@($taskNew | ForEach-Object Relative)
    $oldAfter=@($taskAfter.Rows | Where-Object { $_.path -cnotin $newPaths })
    if (($taskBefore.Rows | ConvertTo-Json -Depth 6 -Compress) -cne ($oldAfter | ConvertTo-Json -Depth 6 -Compress)) { throw 'Cambió un elemento anterior.' }
    if ($taskAfter.FileBytes -ne $taskBefore.FileBytes+$taskNewBytes -or $taskAfter.Rows.Count -ne $taskBefore.Rows.Count+2) { throw 'Inventario final distinto.' }
    foreach ($item in $taskNew) {Assert-Mount $taskMount;Check-File (Join-Path $taskMount $item.Relative) $item.Bytes $item.Hash}
    $taskState.free_bytes_after=[long](Get-Volume -DriveLetter $taskMount.Substring(0,1)).SizeRemaining
    if ($taskState.free_bytes_after -lt $taskReserve) { throw 'La reserva de captura no se mantiene al cierre.' }
    $taskState.existing_inventory_preserved=$true
    $taskState.old_small_files_sha_verified=$taskBefore.SmallCount;$taskState.old_large_files_metadata_verified=$taskBefore.LargeCount
    $taskState.state='verified';$taskState.exit_code=0;$taskState.completed_at=(Get-Date).ToString('o')
    Save-State
    [ordered]@{state='verified';files_verified=2;existing_inventory_preserved=$true;format=$false;removed=0;exit_code=0;safe_removal_pending=$true;volume_flush_verified=$false} | ConvertTo-Json
} catch {
    $taskState.state='failed';$taskState.exit_code=1;$taskState.completed_at=(Get-Date).ToString('o');$taskState.error=$_.Exception.ToString();Save-State;throw
}
