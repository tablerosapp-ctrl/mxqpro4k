param([switch]$Prepare,[switch]$CheckOnly)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($Prepare -and $CheckOnly){throw 'Elegir -Prepare o -CheckOnly.'}

# Continuacion EXPLICITA del fallo posterior a Clear-Disk. No vuelve a borrar particiones.
# Carga solo funciones del preparador sellado; no ejecuta su flujo principal ni altera su recibo.
$continueRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$continueSource=Join-Path $PSScriptRoot 'preparar-sd-rk3229-c.ps1'
$continueSourceHash='06423fbff7695413f5d5d104695b48968e898814ff5c81da25860ee075c99a08'
if((Get-FileHash -LiteralPath $continueSource -Algorithm SHA256).Hash.ToLowerInvariant() -cne $continueSourceHash){throw 'Preparador fuente distinto.'}
$continueTokens=$null;$continueErrors=$null
$continueAst=[Management.Automation.Language.Parser]::ParseFile($continueSource,[ref]$continueTokens,[ref]$continueErrors)
if(@($continueErrors).Count){throw 'Error de sintaxis en fuente sellada.'}
$continueFunctions=@($continueAst.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
if($continueFunctions.Count -ne 18){throw 'Funciones fuente inesperadas.'}
$continueDefinitions=($continueFunctions|ForEach-Object {
    if($_.Name -ceq 'Get-CheckedSD'){$_.Extent.Text.Replace('function Get-CheckedSD(', 'function Get-SourceCheckedSD(')}else{$_.Extent.Text}
}) -join "`n"
. ([scriptblock]::Create($continueDefinitions))

function Get-CheckedSD([string]$stage) {
    if($stage -cne 'Cleared'){return Get-SourceCheckedSD $stage}
    $disks=@(Get-Disk -UniqueId $taskConfig.UniqueId -ErrorAction Stop)
    if($disks.Count -ne 1){throw 'SD no unica.'}
    $disk=$disks[0]
    Assert-SDIdentity $disk
    if([long]$disk.Number -ne $taskInitialNumber){throw 'Cambio el numero fisico de la SD.'}
    $parts=@(Get-CimInstance -Namespace 'root/Microsoft/Windows/Storage' -ClassName MSFT_Partition -Filter ('DiskNumber = '+[int]$disk.Number) -ErrorAction Stop)
    if($parts.Count -ne 0 -or [string]$disk.PartitionStyle -cnotin @('MBR','RAW')){throw 'La continuacion exige cero particiones y estilo MBR o RAW.'}
    return [pscustomobject]@{Disk=$disk;Partition=$null;Volume=$null;Mount=$null;Stage=$stage}
}

function Check-ContinuationInputs {
    Assert-ScriptUnchanged
    if((Hash-Ordinary $continueSource) -cne $continueSourceHash){throw 'Cambio el preparador fuente sellado.'}
    if((Hash-Ordinary $continueFailedReceipt) -cne '0d49bf06c4ceaa2a890e96feed095f1876878aec8dda17a25379eb67d14f02b5'){throw 'Recibo privado de fallo distinto.'}
    if((Hash-Ordinary $continuePrefix) -cne $continuePrefixHash -or
        [long](Get-Item -LiteralPath $continuePrefix).Length -ne $taskConfig.PrefixBytes){throw 'Respaldo previo de 96 MiB no coincide.'}
    foreach($file in @(
        @{name='sd_boot_config.config';bytes=144;sha='a73257d8d73a1ebc31cdf235223b2d3f5762500aace01a1d6674c75d74cb0f30'},
        @{name='rksdfw.tag';bytes=0;sha='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'})){
        $path=Join-Path $continueBackupRoot $file.name
        if((Hash-Ordinary $path) -cne $file.sha -or [long](Get-Item -LiteralPath $path).Length -ne $file.bytes){throw 'Respaldo auxiliar previo distinto.'}
    }
}

function Check-PostFormatGap {
    # Sector MBR nuevo permitido. Los otros 2047 sectores antes de la particion deben seguir en cero.
    $raw=Open-CheckedRaw 'Final' $false
    try{
        $buffer=New-Object byte[] (1MB)
        $raw.Position=0
        if($raw.Read($buffer,0,$buffer.Length) -ne $buffer.Length){throw 'Lectura corta del espacio previo a la particion.'}
        for($n=512;$n -lt $buffer.Length;$n++){if($buffer[$n] -ne 0){throw 'Datos inesperados en el espacio reservado previo a FAT32.'}}
        [TVBase.SDPreparationRawV1]::AssertDevice($raw,[int]$taskInitialNumber,$taskConfig.Size,$taskConfig.SerialNumber)
        $sha=[Security.Cryptography.SHA256]::Create()
        try{return ([BitConverter]::ToString($sha.ComputeHash($buffer,512,$buffer.Length-512))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
    }finally{$raw.Dispose()}
}

$taskConfig=New-SDSettings $continueRoot
$taskScriptPath=[IO.Path]::GetFullPath($PSCommandPath)
$taskScriptHash=Hash-Ordinary $taskScriptPath
$taskIdentityHash=Hash-Text ($taskConfig.UniqueId+"`n"+$taskConfig.SerialNumber+"`n"+$taskConfig.Size)
$taskInitialNumber=[long]1
$continueBackupRoot=Assert-ProjectPath (Join-Path $continueRoot 'privado/sd-rk3229-c-20260908-220744-251246738887')
$continueFailedReceipt=Join-Path $continueBackupRoot '04-failed_preserved.json'
$continuePrefix=Join-Path $continueBackupRoot 'sd-primeros-96MiB-original.bin'
$continuePrefixHash='25b1107c216ef0c489e6075bd8bb08be5ccf454d9b99cca9285d2b5616a0e068'
$taskSummary=Assert-ProjectPath (Join-Path $PSScriptRoot 'sd-rk3229-c-continuacion-estado.json')
$taskPrivate=$null;$taskPublicStream=$null;$taskCheckpointNumber=0;$taskState=$null
try{
    if(Test-Path -LiteralPath $taskSummary){throw 'Continuacion ya iniciada; conservar recibo y no repetir.'}
    Assert-NoReparse $continueRoot $true
    Assert-NoReparse $continueBackupRoot $true
    Check-ContinuationInputs
    $failed=Get-Content -LiteralPath $continueFailedReceipt -Raw -Encoding UTF8|ConvertFrom-Json
    if($failed.schema -cne 'tvbase-sd-normal-preparation-private-1' -or $failed.state -cne 'failed_preserved' -or
        $failed.error.phase -cne 'clear_disk_requested' -or -not $failed.prefix_backup_verified -or
        $failed.prefix_zero_verified_before_new_layout -or $failed.normal_fat32_verified -or
        $failed.initial_disk.unique_id -cne $taskConfig.UniqueId){throw 'El fallo previo no es el autorizado para continuar.'}
    $null=Check-PCFirmware
    $empty=Get-CheckedSD 'Cleared'
    Ensure-SDRawType
    $probe=Open-CheckedRaw 'Cleared' $false
    $probe.Dispose()
    if(-not $Prepare){Write-Output 'Continuacion comprobada: identidad, cero particiones, handle fisico y respaldos previos validos; sin escrituras.';return}

    $privateRoot=Assert-ProjectPath (Join-Path $continueRoot 'privado')
    Assert-NoReparse $privateRoot $true
    $taskPrivate=Assert-ProjectPath (Join-Path $privateRoot ('sd-rk3229-c-continuacion-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,12)))
    if(Test-Path -LiteralPath $taskPrivate){throw 'Destino privado existente.'}
    Assert-NoReparse $PSScriptRoot $true
    $taskPublicStream=New-Object IO.FileStream($taskSummary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $null=New-Item -ItemType Directory -Path $taskPrivate -ErrorAction Stop
    $taskState=[ordered]@{
        schema='tvbase-sd-normal-preparation-private-1';state='preparing';phase='continuation_reserved'
        created_utc=[DateTime]::UtcNow.ToString('o');updated_utc=[DateTime]::UtcNow.ToString('o')
        script_path=$taskScriptPath;script_sha256=$taskScriptHash;source_script_sha256=$continueSourceHash
        previous_failed_receipt_path=$continueFailedReceipt;previous_failed_receipt_sha256='0d49bf06c4ceaa2a890e96feed095f1876878aec8dda17a25379eb67d14f02b5'
        initial_disk=(Get-SDRecord $empty);prefix_backup=$failed.prefix_backup;auxiliary_backups=$failed.auxiliary_backups
        prefix_backup_verified=$true;prefix_zero_verified_before_new_layout=$false;sd_mutation_attempted=$false
        normal_fat32_verified=$false;clear_disk_repeated=$false;backup_repeated=$false;actions=@();error=$null
        final_disk=$null;final_root=$null;post_format_gap_zero_verified=$false
    }
    Save-SDCheckpoint 'continuation_reserved' 'preparing'
    Check-ContinuationInputs
    Save-SDCheckpoint 'zero_prefix_requested' 'preparing'
    $raw=Open-CheckedRaw 'Cleared' $true
    try{
        $taskState.sd_mutation_attempted=$true
        $zeroHash=[TVBase.SDPreparationRawV1]::ZeroPrefix($raw,$taskConfig.PrefixBytes)
        [TVBase.SDPreparationRawV1]::AssertDevice($raw,[int]$taskInitialNumber,$taskConfig.Size,$taskConfig.SerialNumber)
    }finally{$raw.Dispose()}
    $taskState.prefix_zero_verified_before_new_layout=$true
    $taskState.zero_prefix_sha256=$zeroHash
    $taskState.zero_prefix_bytes=$taskConfig.PrefixBytes
    $taskState.zero_prefix_file_flush_verified=$true
    Save-SDCheckpoint 'zero_prefix_reread_verified' 'preparing'

    $empty=Get-CheckedSD 'Cleared'
    Update-Disk -InputObject $empty.Disk -ErrorAction Stop
    $empty=Get-CheckedSD 'Cleared'
    $taskState.partition_style_after_refresh=[string]$empty.Disk.PartitionStyle
    Check-ContinuationInputs
    if([string]$empty.Disk.PartitionStyle -ceq 'RAW'){
        Save-SDCheckpoint 'initialize_mbr_requested' 'preparing'
        $empty=Get-CheckedSD 'Cleared'
        Initialize-Disk -InputObject $empty.Disk -PartitionStyle MBR -ErrorAction Stop
    }
    # Si Windows conserva MBR sin particiones, el prefijo raw ya fue puesto a cero y releido.
    $null=Get-CheckedSD 'Initialized'
    Save-SDCheckpoint 'new_partition_requested' 'preparing'
    $initialized=Get-CheckedSD 'Initialized'
    $null=New-Partition -InputObject $initialized.Disk -Offset $taskConfig.NewOffset -UseMaximumSize -AssignDriveLetter -ErrorAction Stop
    $null=Get-CheckedSD 'Partitioned'
    Check-ContinuationInputs
    Save-SDCheckpoint 'quick_fat32_format_requested' 'preparing'
    $partitioned=Get-CheckedSD 'Partitioned'
    $null=Format-Volume -Partition $partitioned.Partition -FileSystem FAT32 -NewFileSystemLabel $taskConfig.Label -Force -Confirm:$false -ErrorAction Stop
    $final=Get-CheckedSD 'Final'
    $taskState.final_disk=Get-SDRecord $final
    $taskState.final_root=Get-RootSnapshot $final.Mount $true
    $taskState.post_format_gap_sha256=Check-PostFormatGap
    $taskState.post_format_gap_offset=512
    $taskState.post_format_gap_bytes=1048064
    $taskState.post_format_gap_zero_verified=$true
    $null=Get-CheckedSD 'Final'
    $taskState.normal_fat32_verified=$true
    $taskState.actions+= 'Sin otro Clear-Disk: cero 96 MiB verificado, MBR y FAT32 TVBASESD vacia; espacio 512..1048575 releido en cero.'
    Save-SDCheckpoint 'normal_sd_verified' 'formateada_sd_normal'
    Write-Output 'SD normal FAT32 TVBASESD verificada, sin ZIP; respaldo original y fallo anterior conservados. Expulsion segura pendiente.'
}catch{
    if($null -ne $taskState -and $null -ne $taskPublicStream -and $null -ne $taskPrivate){
        $taskState.error=[ordered]@{message=$_.Exception.Message;type=$_.Exception.GetType().FullName;phase=$taskState.phase;utc=[DateTime]::UtcNow.ToString('o')}
        try{Save-SDCheckpoint 'failed_preserved' 'failed_preserved'}catch{Write-Warning 'Conservar recibo reservado y archivos privados; fallo al registrar error.'}
    }
    throw
}finally{if($null -ne $taskPublicStream){$taskPublicStream.Dispose()}}
