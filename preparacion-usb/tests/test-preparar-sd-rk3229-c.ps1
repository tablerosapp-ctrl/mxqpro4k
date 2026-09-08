# Pruebas locales: carga SOLO definiciones de funciones por AST, nunca el flujo principal.
# Ninguna llamada a Get-Disk/Get-Partition/Get-Volume, Clear-Disk ni PhysicalDrive.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$testProject = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\','/')
$testSource = Join-Path $testProject 'preparacion-usb/preparar-sd-rk3229-c.ps1'
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($testSource,[ref]$tokens,[ref]$errors)
if (@($errors).Count -ne 0) { throw ($errors | Out-String) }
$functions = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
. ([scriptblock]::Create(($functions | ForEach-Object { $_.Extent.Text }) -join "`n"))
$taskConfig = New-SDSettings $testProject
$taskInitialNumber = $null
$testDirectory = Join-Path $testProject ('privado/pruebas-sd-rk3229-c-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,12))
$null = Assert-ProjectPath $testDirectory
Assert-NoReparse (Join-Path $testProject 'privado') $true
if (Test-Path -LiteralPath $testDirectory) { throw 'Destino de prueba ya existente.' }
$null = New-Item -ItemType Directory -Path $testDirectory
$results = New-Object 'Collections.Generic.List[object]'

function Test-Case([string]$name,[scriptblock]$action) {
    try { & $action; $results.Add([pscustomobject]@{name=$name;passed=$true}) }
    catch { $results.Add([pscustomobject]@{name=$name;passed=$false;error=$_.Exception.Message}) }
}
function Must-Fail([scriptblock]$action) {
    $failed = $false
    try { & $action | Out-Null } catch { $failed = $true }
    if (-not $failed) { throw 'La operacion insegura no fue rechazada.' }
}
function Mock-Disk {
    return [pscustomobject]@{
        UniqueId=$taskConfig.UniqueId; FriendlyName=$taskConfig.FriendlyName; SerialNumber=$taskConfig.SerialNumber
        Size=$taskConfig.Size; BusType='USB'; IsSystem=$false; IsBoot=$false; IsOffline=$false; IsReadOnly=$false
        LogicalSectorSize=512; PhysicalSectorSize=512; Number=91; PartitionStyle='MBR'
    }
}
function Mock-Part {
    return [pscustomobject]@{
        DiskNumber=91; PartitionNumber=1; Offset=$taskConfig.PrefixBytes; Size=$taskConfig.OriginalPartitionBytes
        IsSystem=$false; IsBoot=$false
    }
}

Test-Case 'identidad_original_exacta' { Assert-SDLayout (Mock-Disk) @((Mock-Part)) 'Original' }
Test-Case 'rechaza_kingston' { $d=Mock-Disk; $d.UniqueId='KINGSTON'; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_serial_distinto' { $d=Mock-Disk; $d.SerialNumber='OTRO'; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_tamano_distinto' { $d=Mock-Disk; $d.Size++; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_disco_sistema' { $d=Mock-Disk; $d.IsSystem=$true; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_disco_boot' { $d=Mock-Disk; $d.IsBoot=$true; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_sector_4k' { $d=Mock-Disk; $d.LogicalSectorSize=4096; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_disco_readonly' { $d=Mock-Disk; $d.IsReadOnly=$true; Must-Fail { Assert-SDIdentity $d } }
Test-Case 'rechaza_particion_ajena' { $p=Mock-Part; $p.DiskNumber=90; Must-Fail { Assert-SDLayout (Mock-Disk) @($p) 'Original' } }
Test-Case 'rechaza_offset_original_distinto' { $p=Mock-Part; $p.Offset=1MB; Must-Fail { Assert-SDLayout (Mock-Disk) @($p) 'Original' } }
Test-Case 'rechaza_segunda_particion' { Must-Fail { Assert-SDLayout (Mock-Disk) @((Mock-Part),(Mock-Part)) 'Original' } }
Test-Case 'raw_vacio_valido' { $d=Mock-Disk; $d.PartitionStyle='RAW'; Assert-SDLayout $d @() 'Cleared' }
Test-Case 'rechaza_raw_con_particion' { $d=Mock-Disk; $d.PartitionStyle='RAW'; Must-Fail { Assert-SDLayout $d @((Mock-Part)) 'Cleared' } }
Test-Case 'mbr_vacio_valido' { Assert-SDLayout (Mock-Disk) @() 'Initialized' }
Test-Case 'particion_maxima_nueva_valida' { $p=Mock-Part; $p.Offset=1MB; $p.Size=$taskConfig.Size-1MB; Assert-SDLayout (Mock-Disk) @($p) 'Final' }
Test-Case 'rechaza_particion_fuera_disco' { $p=Mock-Part; $p.Offset=1MB; $p.Size=$taskConfig.Size; Must-Fail { Assert-SDLayout (Mock-Disk) @($p) 'Final' } }
Test-Case 'rechaza_nueva_particion_reducida' { $p=Mock-Part; $p.Offset=1MB; $p.Size=4GB; Must-Fail { Assert-SDLayout (Mock-Disk) @($p) 'Final' } }
Test-Case 'rechaza_destino_fuera_proyecto' { Must-Fail { Assert-ProjectPath (Join-Path $testProject '../fuera.bin') } }
Test-Case 'compila_helper_csharp_sin_abrir_dispositivos' { Ensure-SDRawType }

$fixture = Join-Path $testDirectory 'origen-regular-3MiB.bin'
$backupPath = Join-Path $testDirectory 'respaldo-regular-2MiB.bin'
$fixtureBytes = New-Object byte[] (3MB)
for ($i=0;$i -lt $fixtureBytes.Length;$i++) { $fixtureBytes[$i]=[byte](($i % 251)+1) }
Write-NewBytes $fixture $fixtureBytes
$originalFixtureSHA = Hash-Ordinary $fixture
$backupResult = $null
Test-Case 'backup_flush_y_dos_relecturas_regular' {
    $s = New-Object IO.FileStream($fixture,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try { $script:backupResult=[TVBase.SDPreparationRawV1]::BackupPrefix($s,$backupPath,2MB) } finally { $s.Dispose() }
    if (-not $backupResult.SourceRereadVerified -or -not $backupResult.FileRereadVerified -or -not $backupResult.FlushFileVerified -or
        $backupResult.Bytes -ne 2MB -or (Hash-Ordinary $backupPath) -cne $backupResult.SHA256 -or (Hash-Ordinary $fixture) -cne $originalFixtureSHA) { throw 'Respaldo de fixture no coincide.' }
}
Test-Case 'backup_no_sobrescribe' {
    $s = New-Object IO.FileStream($fixture,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try { Must-Fail { [TVBase.SDPreparationRawV1]::BackupPrefix($s,$backupPath,2MB) } } finally { $s.Dispose() }
}
Test-Case 'zero_solo_prefijo_y_cola_conservada_regular' {
    $s = New-Object IO.FileStream($fixture,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try { $null=[TVBase.SDPreparationRawV1]::ZeroPrefix($s,2MB) } finally { $s.Dispose() }
    $read = [IO.File]::ReadAllBytes($fixture)
    if ($read.Length -ne $fixtureBytes.Length) { throw 'Tamano cambiado.' }
    for ($i=0;$i -lt $read.Length;$i++) {
        if ($i -lt 2MB) { if ($read[$i] -ne 0) { throw 'Prefijo no cero.' } }
        elseif ($read[$i] -ne $fixtureBytes[$i]) { throw 'Se modifico la cola fuera del prefijo.' }
    }
    if ((Hash-Ordinary $backupPath) -cne $backupResult.SHA256) { throw 'Respaldo cambiado durante zero.' }
}
Test-Case 'rechaza_longitud_raw_no_alineada' {
    $s = New-Object IO.FileStream($fixture,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try { Must-Fail { [TVBase.SDPreparationRawV1]::ZeroPrefix($s,513) } } finally { $s.Dispose() }
}
Test-Case 'rechaza_zero_superior_a_96MiB' {
    $s = New-Object IO.FileStream($fixture,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try { Must-Fail { [TVBase.SDPreparationRawV1]::ZeroPrefix($s,97MB) } } finally { $s.Dispose() }
}
Test-Case 'rechaza_lectura_corta' {
    $s = New-Object IO.FileStream($fixture,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try { Must-Fail { [TVBase.SDPreparationRawV1]::HashPrefix($s,4MB,$false) } } finally { $s.Dispose() }
}

# Volumen simulado: root de directorio ordinario PC, firmware miniatura con hash fijado para esta prueba.
$rootFixture = Join-Path $testDirectory 'raiz-simulada'
$null = New-Item -ItemType Directory -Path $rootFixture
Write-NewBytes (Join-Path $rootFixture 'sdupdate.img') ([byte[]](1,2,3,4))
Write-NewBytes (Join-Path $rootFixture 'rksdfw.tag') ([byte[]]@())
Write-NewBytes (Join-Path $rootFixture 'sd_boot_config.config') ([Text.Encoding]::ASCII.GetBytes('fw_update=0'))
$taskConfig.FirmwareBytes = 4
$taskConfig.FirmwareSHA256 = Hash-Ordinary (Join-Path $rootFixture 'sdupdate.img')
$rootSnapshot = $null
Test-Case 'snapshot_permite_tag_vacio' { $script:rootSnapshot=Get-RootSnapshot $rootFixture; if ($rootSnapshot.files.Count -ne 3) { throw 'Numero de archivos distinto.' } }
Test-Case 'respalda_tag_vacio_relee_flush' {
    $e=@($rootSnapshot.files | Where-Object name -eq 'rksdfw.tag')[0]
    $r=Copy-SmallFile (Join-Path $rootFixture 'rksdfw.tag') (Join-Path $testDirectory 'tag-vacio-copia') $e
    if ($r.bytes -ne 0 -or -not $r.reread_verified -or -not $r.flush_file_verified) { throw 'Etiqueta vacia no respaldada.' }
}
Test-Case 'snapshot_deteccion_cambio' {
    $b=Get-RootSnapshot $rootFixture
    $b.files[0].sha256='f'*64
    Must-Fail { Assert-SameSnapshot $rootSnapshot $b }
}
Test-Case 'root_final_rechaza_imagen_antigua' { Must-Fail { Get-RootSnapshot $rootFixture $true } }
Test-Case 'root_final_vacio_con_system_volume_information' {
    $emptyRoot=Join-Path $testDirectory 'final-vacia'
    $null=New-Item -ItemType Directory -Path $emptyRoot
    $null=New-Item -ItemType Directory -Path (Join-Path $emptyRoot 'System Volume Information')
    $r=Get-RootSnapshot $emptyRoot $true
    if ($r.files.Count -ne 0 -or -not $r.system_volume_information_present) { throw 'Vacio no reconocido.' }
}
Test-Case 'root_rechaza_archivo_inesperado' {
    Write-NewBytes (Join-Path $rootFixture 'foto.jpg') ([byte[]](9))
    Must-Fail { Get-RootSnapshot $rootFixture }
}

$failed = @($results | Where-Object { -not $_.passed })
$report = [ordered]@{
    schema='tvbase-sd-normal-local-tests-1'; passed=($failed.Count -eq 0)
    tests=$results.Count; failures=$failed.Count; powershell_version=$PSVersionTable.PSVersion.ToString()
    script_sha256=(Hash-Ordinary $testSource); parse_errors=@($errors).Count
    sd_accessed=$false; kingston_accessed=$false; main_script_executed=$false
    raw_windows_ioctl_executed=$false; storage_cmdlets_executed=$false
    limits='Pruebas de funciones puras y streams en archivos PC ordinarios. No prueban IOCTL real, clear, montaje, particionado ni formato fisico.'
    cases=@($results.ToArray())
}
$reportPath = Join-Path $testDirectory 'RESULTADO.json'
Write-NewBytes $reportPath ([Text.UTF8Encoding]::new($false).GetBytes(($report | ConvertTo-Json -Depth 8)+"`n"))
[pscustomobject]@{passed=$report.passed; tests=$report.tests; failures=$report.failures; powershell_version=$report.powershell_version; script_sha256=$report.script_sha256; report=$reportPath} | ConvertTo-Json
if ($failed.Count -ne 0) { $failed | Format-List; exit 1 }
