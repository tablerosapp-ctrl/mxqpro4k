$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskResult = Join-Path $PSScriptRoot 'entrada-oem-07-estado.json'
$taskRun = Join-Path $PSScriptRoot ('entrada-oem-07-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $taskRun | Out-Null
$taskState = [ordered]@{estado='comprobando';fecha=(Get-Date).ToString('o');informe=$taskRun;tv_flasheado=$false;reboot_requested=$false;files=@()}
function Save-State { $taskState | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskResult -Encoding UTF8 }
function Hash-File([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Check-USB {
    $disks = @(Get-Disk | Where-Object UniqueId -eq $taskUsbId)
    if ($disks.Count -ne 1 -or $disks[0].FriendlyName -ne 'Kingston DataTraveler 3.0' -or $disks[0].Size -ne 30943995904 -or $disks[0].BusType -ne 'USB' -or $disks[0].IsBoot -or $disks[0].IsSystem) { throw 'No coincide el Kingston autorizado' }
    $partitions = @(Get-Partition -DiskNumber $disks[0].Number | Where-Object DriveLetter)
    if ($partitions.Count -ne 1) { throw 'Particion con letra ambigua' }
    $volume = $partitions[0] | Get-Volume
    if ($volume.FileSystem -ne 'FAT32' -or $volume.FileSystemLabel -ne 'TVBASE' -or $volume.Size -ne 30925651968) { throw 'Estructura USB distinta de la esperada' }
    $mount = "$($partitions[0].DriveLetter):\"
    if ((Get-Content -LiteralPath (Join-Path $mount 'TVBASE-MEDIA.txt') -Raw).Trim() -ne 'TVBASE-P291-20260906-4dc82786') { throw 'Marcador USB incorrecto' }
    return $mount
}
function Copy-Checked([string]$source,[string]$target,[string]$expected) {
    if ((Hash-File $source) -ne $expected) { throw 'La fuente cambio' }
    if (Test-Path -LiteralPath $target) {
        if ((Hash-File $target) -ne $expected) { throw "Ya existe otro archivo: $target" }
    } else {
        $inputFile = [IO.File]::OpenRead($source)
        try {
            $outputFile = [IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $inputFile.CopyTo($outputFile); $outputFile.Flush($true) } finally { $outputFile.Dispose() }
        } finally { $inputFile.Dispose() }
    }
    if ((Hash-File $target) -ne $expected) { throw "Lectura diferente tras copiar: $target" }
    $taskState.files += [ordered]@{archivo=[IO.Path]::GetFileName($target);bytes=(Get-Item -LiteralPath $target).Length;sha256=$expected;lectura_verificada=$true}
    Save-State
}
try {
    Save-State
    $mount = Check-USB
    $taskState.usb_id=$taskUsbId
    $taskState.drive_letter=$mount.Substring(0,1)
    Get-ChildItem -LiteralPath $mount -Force | Select-Object Name,Length,LastWriteTime | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRun 'archivos-antes.json') -Encoding UTF8
    $apk = Join-Path $taskRoot 'rom-simplificada/compilacion/acceso-usb-0.7/acceso-usb.apk'
    $proof = Join-Path $taskRoot 'rom-simplificada/instalador/ENTRADA-TESTS-0.7.json'
    if (-not (Test-Path -LiteralPath $proof)) { throw 'Falta evidencia de pruebas 0.7' }
    $tests = Get-Content -LiteralPath $proof -Raw | ConvertFrom-Json
    if ($tests.version -ne '0.7' -or $tests.state -ne 'passed' -or @($tests.adb).Count -lt 12 -or @($tests.shell_syntax).Count -ne 2 -or @($tests.shell_fixtures).Count -lt 10 -or @(@($tests.adb) + @($tests.shell_syntax) + @($tests.shell_fixtures) | Where-Object passed -ne $true).Count -ne 0 -or -not $tests.external_host_rejected -or $tests.guard_result -notmatch '^GUARDS_OK:' -or $tests.max_actual_open_bytes -gt 4096) { throw 'Pruebas 0.7 incompletas o fallidas' }
    $release = Get-Content -LiteralPath (Join-Path $taskRoot 'rom-simplificada/compilacion/acceso-usb-0.7/componente.json') -Raw | ConvertFrom-Json
    if (@($tests.mksh_syntax).Count -ne 2 -or @($tests.mksh_syntax | Where-Object passed -ne $true).Count -ne 0 -or $tests.mksh_default_hash_alias -notmatch 'alias -t') { throw 'Falta prueba representativa de mksh con su alias activo' }
    if (@($tests.tested_source_sha256.PSObject.Properties).Count -ne 4 -or @($tests.shell_fixtures).Count -ne 23) { throw 'Fuentes o casos incompletos' }
    foreach ($requiredCase in @('preflight_then_single_menu_open','raw_sha_empty_success','helper_empty_external_guard','rom_digest_wrong','ota_digest_wrong','pm_unexpected_path','rom_changed_during_hash','marker_changed_after_hash','am_zero_without_status','am_wrong_activity')) {
        if (@($tests.shell_fixtures | Where-Object { $_.case -eq $requiredCase -and $_.passed -eq $true }).Count -ne 1) { throw "Falta regresion: $requiredCase" }
    }
    foreach ($sourceHash in $tests.tested_source_sha256.PSObject.Properties) {
        $sourcePath = [IO.Path]::GetFullPath((Join-Path $taskRoot $sourceHash.Name))
        if (-not $sourcePath.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Fuente fuera del proyecto' }
        if ((Hash-File $sourcePath) -ne $sourceHash.Value) { throw "Fuente diferente de la probada: $($sourceHash.Name)" }
    }
    if ($release.version -ne '0.7' -or $release.purpose -ne 'entrada_actualizador_oem' -or (Hash-File $apk) -ne $release.sha256 -or $tests.apk_sha256 -ne $release.sha256 -or (Get-Item -LiteralPath $apk).Length -ne $release.bytes) { throw 'APK no coincide con release comprobada' }
    $taskState.pruebas_sha256 = Hash-File $proof
    $taskState.release_sha256 = $release.sha256
    $java = Join-Path $taskRoot 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
    $buildTools = Join-Path $taskRoot 'tools/verificacion-apk/build-tools-37/android-37.0'
    $signer = & $java -jar (Join-Path $buildTools 'lib/apksigner.jar') verify --verbose --print-certs --min-sdk-version 28 --max-sdk-version 28 $apk 2>&1
    if ($LASTEXITCODE -ne 0 -or ($signer -join "`n") -notmatch 'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613') { throw 'Firma APK distinta o invalida' }
    $signer | Set-Content -LiteralPath (Join-Path $taskRun 'firma-apk.txt') -Encoding UTF8
    $badging = & (Join-Path $buildTools 'aapt2.exe') dump badging $apk 2>&1
    if ($LASTEXITCODE -ne 0 -or ($badging -join "`n") -notmatch "versionCode='7' versionName='0.7'") { throw 'No es APK0.7' }
    if ((Hash-File (Join-Path $mount 'TVBASE-P291-A9-0.1.1-RECOVERY.zip')) -ne 'e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205') { throw 'ROM distinta: detener preparacion' }
    if ((Hash-File (Join-Path $mount 'recovery.img')) -ne 'e59ef077378f8b1ba644bcfbef2a0f55e9914258696f203e813392e0a9fed01b') { throw 'Recovery distinto: detener preparacion' }
    if ((Check-USB) -ne $mount) { throw 'Cambio el montaje antes de copiar' }
    Copy-Checked $apk (Join-Path $mount 'AccesoUSB-0.7.apk') (Hash-File $apk)
    $readme = Join-Path $taskRoot 'rom-simplificada/instalador/LEEME-ENTRADA-0.7.txt'
    $now = Join-Path $mount 'LEEME-AHORA.txt'
    if ((Test-Path -LiteralPath $now) -and (Hash-File $now) -ne (Hash-File $readme)) {
        if ((Hash-File $now) -ne '8939b00748b608a0ab2f822bc39fd6c348f1ae1eb1158e9be51715fd0fdfe897') { throw 'LEEME actual desconocido' }
        $old = Join-Path $mount 'LEEME-0.6-retirado.txt'
        if (Test-Path -LiteralPath $old) { throw 'Destino historico LEEME ya existe' }
        Move-Item -LiteralPath $now -Destination $old
    }
    Copy-Checked $readme $now (Hash-File $readme)
    $oldApk = Join-Path $mount 'AccesoUSB-0.6.apk'
    if (Test-Path -LiteralPath $oldApk) {
        if ((Hash-File $oldApk) -ne '7664b019051ed4e042a64e4e987501bbf3823224a839793a5811545991c1acd6') { throw 'APK0.6 distinta' }
        $retired = $oldApk + '.no-usar'
        if (Test-Path -LiteralPath $retired) { throw 'Destino APK retirada ya existe' }
        Move-Item -LiteralPath $oldApk -Destination $retired
    }
    $taskState.estado='verificado'
    $taskState.fecha=(Get-Date).ToString('o')
    $taskState.detalle='Acceso USB0.7 copiado y leido. Verifica el ZIP y abre el menu OEM; no inicia Update ni reinicio propio. ROM/recovery y capturas conservados.'
    Save-State
    Copy-Item -LiteralPath $taskResult -Destination (Join-Path $taskRun 'resultado.json')
    Get-Content -LiteralPath $taskResult -Raw
} catch {
    $taskState.estado='fallo'
    $taskState.error_nativo=$_.Exception.ToString()
    Save-State
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $taskRun 'error.txt') -Encoding UTF8
    throw
}
