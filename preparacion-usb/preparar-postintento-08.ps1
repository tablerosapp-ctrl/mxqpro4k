$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$taskUsbId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskResult = Join-Path $PSScriptRoot 'postintento-08-estado.json'
$taskArchive = Join-Path $taskRoot ('privado/usb-retirados-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$taskState = [ordered]@{estado='comprobando';fecha=(Get-Date).ToString('o');archivo_local=$taskArchive;tv_flasheado=$false;reboot_requested=$false;files=@();retirados=@();bytes_retirados=0;codigo_nativo=$null}
function Save-State { $taskState | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskResult -Encoding UTF8 }
function Hash-File([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Check-USB {
    $disks = @(Get-Disk | Where-Object UniqueId -eq $taskUsbId)
    if ($disks.Count -ne 1 -or $disks[0].FriendlyName -ne 'Kingston DataTraveler 3.0' -or $disks[0].Size -ne 30943995904 -or $disks[0].BusType -ne 'USB' -or $disks[0].IsBoot -or $disks[0].IsSystem) { throw 'No coincide el Kingston autorizado' }
    $parts = @(Get-Partition -DiskNumber $disks[0].Number | Where-Object DriveLetter)
    if ($parts.Count -ne 1) { throw 'Montaje ambiguo' }
    $volume = $parts[0] | Get-Volume
    if ($volume.FileSystem -ne 'FAT32' -or $volume.FileSystemLabel -ne 'TVBASE' -or $volume.Size -ne 30925651968) { throw 'Estructura distinta' }
    $mount = "$($parts[0].DriveLetter):\"
    if ((Get-Content -LiteralPath (Join-Path $mount 'TVBASE-MEDIA.txt') -Raw).Trim() -ne 'TVBASE-P291-20260906-4dc82786') { throw 'Marcador incorrecto' }
    return $mount
}
function Copy-Checked([string]$source,[string]$target,[string]$expected) {
    if ((Hash-File $source) -ne $expected) { throw 'Fuente modificada' }
    if (Test-Path -LiteralPath $target) {
        if ((Hash-File $target) -ne $expected) { throw 'Destino preexistente diferente' }
    } else {
        $inputFile = [IO.File]::OpenRead($source)
        try {
            $outputFile = [IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $inputFile.CopyTo($outputFile); $outputFile.Flush($true) } finally { $outputFile.Dispose() }
        } finally { $inputFile.Dispose() }
    }
    if ((Hash-File $target) -ne $expected) { throw 'Copia leida distinta' }
}
try {
    Save-State
    $mount = Check-USB
    $taskState.drive_letter=$mount.Substring(0,1)
    $proof = Get-Content -LiteralPath (Join-Path $taskRoot 'rom-simplificada/instalador/EVIDENCIA-TESTS-0.8.json') -Raw | ConvertFrom-Json
    if ($proof.version -ne '0.8' -or $proof.state -ne 'passed' -or @($proof.adb).Count -ne 12 -or @($proof.shell_fixtures).Count -ne 21 -or @($proof.shell_syntax).Count -ne 11 -or @($proof.mksh_syntax).Count -ne 11 -or -not $proof.external_host_rejected -or $proof.max_actual_open_bytes -gt 4096 -or $proof.guard_result -notmatch '^GUARDS_OK:' -or $proof.mksh_default_hash_alias -notmatch 'alias -t') { throw 'Pruebas incompletas' }
    if (@(@($proof.adb)+@($proof.shell_fixtures)+@($proof.shell_syntax)+@($proof.mksh_syntax) | Where-Object passed -ne $true).Count) { throw 'Prueba fallida' }
    if (@($proof.tested_source_sha256.PSObject.Properties).Count -ne 17) { throw 'Inventario de fuentes incompleto' }
    foreach ($h in $proof.tested_source_sha256.PSObject.Properties) {
        $p = [IO.Path]::GetFullPath((Join-Path $taskRoot $h.Name))
        if (-not $p.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or (Hash-File $p) -ne $h.Value) { throw 'Fuente no coincide con pruebas' }
    }
    $apk = Join-Path $taskRoot 'rom-simplificada/compilacion/acceso-usb-0.8/acceso-usb.apk'
    $release = Get-Content -LiteralPath (Join-Path $taskRoot 'rom-simplificada/compilacion/acceso-usb-0.8/componente.json') -Raw | ConvertFrom-Json
    if ($release.version -ne '0.8' -or $release.purpose -ne 'diagnostico_sin_reinicio' -or $proof.apk_sha256 -ne $release.sha256 -or (Hash-File $apk) -ne $release.sha256 -or (Get-Item -LiteralPath $apk).Length -ne $release.bytes) { throw 'Release distinta' }
    $java = Join-Path $taskRoot 'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
    $bt = Join-Path $taskRoot 'tools/verificacion-apk/build-tools-37/android-37.0'
    $signature = & $java -jar (Join-Path $bt 'lib/apksigner.jar') verify --verbose --print-certs --min-sdk-version 28 --max-sdk-version 28 $apk 2>&1
    if ($LASTEXITCODE -ne 0 -or ($signature -join "`n") -notmatch 'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613') { throw 'Firma distinta/invalida' }
    $badging = & (Join-Path $bt 'aapt2.exe') dump badging $apk 2>&1
    if ($LASTEXITCODE -ne 0 -or ($badging -join "`n") -notmatch "versionCode='8' versionName='0.8'") { throw 'Version distinta' }
    $fixed = @{'TVBASE-P291-A9-0.1.1-RECOVERY.zip'='e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205';'recovery.img'='e59ef077378f8b1ba644bcfbef2a0f55e9914258696f203e813392e0a9fed01b'}
    foreach ($name in $fixed.Keys) { if ((Hash-File (Join-Path $mount $name)) -ne $fixed[$name]) { throw 'ROM/recovery distinto' } }
    $guide = Join-Path $taskRoot 'rom-simplificada/instalador/LEEME-POSTINTENTO-0.8.txt'
    $guideHash = Hash-File $guide
    $names = @('AccesoUSB-0.2.apk.no-usar','AccesoUSB-0.3.apk.no-usar','AccesoUSB-0.4.apk.no-usar','AccesoUSB-0.5.apk.no-usar','AccesoUSB-0.6.apk.no-usar','AccesoUSB-0.7.apk','LEEME-0.1-retirado.txt','LEEME-0.4-retirado.txt','LEEME-0.5-retirado.txt','LEEME-0.6-retirado.txt','LEEME-ENTRADA-ANTERIOR.txt','TVBASE-P291-A9-0.1-RECOVERY.zip.no-usar','mxqpro4kpropuestasastra.zip')
    $oldGuide = Join-Path $mount 'LEEME-AHORA.txt'
    if ((Test-Path -LiteralPath $oldGuide) -and (Hash-File $oldGuide) -ne $guideHash) {
        if ((Hash-File $oldGuide) -ne 'ec8297fca66a5c9f9604ce46afc6048eff1187af49a3351b232c065c43aaadc5') { throw 'Guia actual desconocida' }
        $names += 'LEEME-AHORA.txt'
    }
    if (-not [IO.Path]::GetFullPath($taskArchive).StartsWith($taskRoot+'\privado\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Archivo local fuera del proyecto' }
    New-Item -ItemType Directory -Path $taskArchive | Out-Null
    Get-ChildItem -LiteralPath $mount -Force | Select-Object Name,Length | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskArchive 'antes.json') -Encoding UTF8
    $rows = @()
    foreach ($name in $names) {
        $p = [IO.Path]::GetFullPath((Join-Path $mount $name))
        if ([IO.Path]::GetDirectoryName($p).TrimEnd('\')+'\' -ne $mount) { throw 'Destino de retiro fuera de raiz USB' }
        if (-not (Test-Path -LiteralPath $p)) { continue }
        $item = Get-Item -LiteralPath $p -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'No es archivo ordinario' }
        $h = Hash-File $p
        Copy-Checked $p (Join-Path $taskArchive $name) $h
        $rows += [ordered]@{archivo=$name;bytes=$item.Length;sha256=$h;copia_pc_verificada=$true;retirado=$false}
    }
    $taskState.retirados=$rows
    Save-State
    if ((Check-USB) -ne $mount) { throw 'Cambio el montaje' }
    Copy-Checked $apk (Join-Path $mount 'AccesoUSB-0.8.apk') $release.sha256
    # Todas las copias retiradas ya estan verificadas. Solo se elimina esta lista explicita, sin recursividad.
    foreach ($row in $rows) {
        if ((Check-USB) -ne $mount) { throw 'Cambio el USB antes de retirar' }
        $p = [IO.Path]::GetFullPath((Join-Path $mount $row.archivo))
        if ([IO.Path]::GetDirectoryName($p).TrimEnd('\')+'\' -ne $mount -or (Hash-File $p) -ne $row.sha256 -or (Hash-File (Join-Path $taskArchive $row.archivo)) -ne $row.sha256) { throw 'Cambio antes de retirar' }
        Remove-Item -LiteralPath $p
        if (Test-Path -LiteralPath $p) { throw 'Retiro no confirmado' }
        $row.retirado=$true
        $taskState.bytes_retirados += $row.bytes
        Save-State
    }
    Copy-Checked $guide $oldGuide $guideHash
    foreach ($pair in @(@('AccesoUSB-0.8.apk',$release.sha256),@('LEEME-AHORA.txt',$guideHash))) {
        $p=Join-Path $mount $pair[0]
        if ((Hash-File $p) -ne $pair[1]) { throw 'Lectura final distinta' }
        $taskState.files += [ordered]@{archivo=$pair[0];bytes=(Get-Item -LiteralPath $p).Length;sha256=$pair[1];lectura_verificada=$true}
    }
    foreach ($name in $fixed.Keys) { if ((Hash-File (Join-Path $mount $name)) -ne $fixed[$name]) { throw 'Artefacto conservado cambio' } }
    $taskState.estado='verificado'
    $taskState.fecha=(Get-Date).ToString('o')
    $taskState.codigo_nativo=0
    $taskState.detalle='0.8 copiado/leido; versiones viejas archivadas en PC antes de retirarlas del USB. ROM0.1.1, recovery, marcador, informes y respaldos conservados. Sin formato/reinicio.'
    Save-State
    Copy-Item -LiteralPath $taskResult -Destination (Join-Path $taskArchive 'resultado.json')
    Get-Content -LiteralPath $taskResult -Raw
} catch {
    $taskState.estado='fallo';$taskState.codigo_nativo=1;$taskState.error_nativo=$_.Exception.ToString()
    Save-State
    throw
}
