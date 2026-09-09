param([switch]$Prepare)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
# Una sesion DiskPart nativa, despues del prefijo puesto a cero y verificado.
# No reejecuta los preparadores anteriores ni reutiliza sus recibos.
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\','/')
$source=Join-Path $PSScriptRoot 'preparar-sd-rk3229-c.ps1'
if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -cne '06423fbff7695413f5d5d104695b48968e898814ff5c81da25860ee075c99a08'){throw 'Fuente sellada distinta'}
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Sintaxis fuente invalida'}
$functions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
if($functions.Count -ne 18){throw 'Funciones fuente distintas'}
. ([scriptblock]::Create(($functions|ForEach-Object {$_.Extent.Text}) -join "`n"))
$taskConfig=New-SDSettings $taskRoot
$taskInitialNumber=[long]1
$taskScriptPath=$PSCommandPath
$taskScriptHash=Hash-Ordinary $taskScriptPath
$finalReceipt=Join-Path $PSScriptRoot 'sd-rk3229-c-final-estado.json'
$previous=Join-Path $taskRoot 'privado/sd-rk3229-c-continuacion-20260909-000656-f99642478381/04-failed_preserved.json'
$backup=Join-Path $taskRoot 'privado/sd-rk3229-c-20260908-220744-251246738887/sd-primeros-96MiB-original.bin'

function EmptySD {
 $ds=@(Get-Disk -UniqueId $taskConfig.UniqueId -ErrorAction Stop)
 if($ds.Count -ne 1){throw 'SD no unica'}
 $d=$ds[0];Assert-SDIdentity $d
 if($d.Number -ne 1 -or [string]$d.PartitionStyle -cne 'MBR'){throw 'Estado de SD distinto'}
 $ps=@(Get-CimInstance -Namespace root/Microsoft/Windows/Storage -ClassName MSFT_Partition -Filter 'DiskNumber = 1' -ErrorAction Stop)
 if($ps.Count -ne 1 -or $ps[0].PartitionNumber -ne 1 -or $ps[0].Offset -ne 0 -or $ps[0].Size -ne $taskConfig.Size -or
    $ps[0].IsBoot -or $ps[0].IsSystem -or ([int][char]$ps[0].DriveLetter -ne 0)){throw 'No coincide la particion de medio completo observada'}
 return $d
}
function ReadRaw([object]$disk) {
 $stream=[IO.FileStream]::new(('\\.\PhysicalDrive'+$disk.Number),[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite,1048576,[IO.FileOptions]::SequentialScan)
 try{[TVBase.SDPreparationRawV1]::AssertDevice($stream,[int]$disk.Number,$taskConfig.Size,$taskConfig.SerialNumber);return $stream}catch{$stream.Dispose();throw}
}
function SaveFinal {
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($state|ConvertTo-Json -Depth 8)+"`n")
 $receiptStream.Position=0;$receiptStream.SetLength(0);$receiptStream.Write($bytes,0,$bytes.Length);$receiptStream.Flush($true)
}
if(Test-Path -LiteralPath $finalReceipt){throw 'Finalizacion ya iniciada; revisar recibo antes de otra accion'}
if((Hash-Ordinary $previous) -cne 'd64769c8ab8bd942d316e0087aa7557009988103b692c1adfe3487d05e48fe63'){throw 'Fallo previo distinto'}
$old=Get-Content -LiteralPath $previous -Raw -Encoding UTF8|ConvertFrom-Json
if($old.state -cne 'failed_preserved' -or -not $old.prefix_zero_verified_before_new_layout){throw 'Prefijo anterior no verificado'}
if((Hash-Ordinary $backup) -cne '25b1107c216ef0c489e6075bd8bb08be5ccf454d9b99cca9285d2b5616a0e068' -or
   (Get-Item -LiteralPath $backup).Length -ne 100663296){throw 'Respaldo original distinto'}
Ensure-SDRawType
$d=EmptySD
$raw=ReadRaw $d
try{$zeroHash=[TVBase.SDPreparationRawV1]::HashPrefix($raw,100663296,$true)}finally{$raw.Dispose()}
$d=EmptySD
if(-not $Prepare){Write-Output 'SD exacta, respaldo y prefijo cero comprobados; sin escrituras';return}
$privateRoot=Assert-ProjectPath (Join-Path $taskRoot 'privado')
Assert-NoReparse $privateRoot $true
$private=Assert-ProjectPath (Join-Path $privateRoot ('sd-rk3229-c-final-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,12)))
$null=New-Item -ItemType Directory -Path $private -ErrorAction Stop
$commandFile=Join-Path $private 'diskpart.txt'
Write-NewBytes $commandFile ([Text.Encoding]::ASCII.GetBytes("select disk 1`r`nclean`r`ncreate partition primary offset=1024`r`nformat fs=fat32 quick label=TVBASESD`r`nassign`r`nexit`r`n"))
$state=[ordered]@{schema='tvbase-sd-normal-preparation-1';state='preparing';phase='diskpart_pending';
 utc=[DateTime]::UtcNow.ToString('o');disk_bytes=8053063680;final_label='TVBASESD';
 disk_identity_sha256='83e0b5dd47383a39d4b7996bdac16d9ba9b397dc87c34b5fd593ff6404f04076';
 script_sha256=$taskScriptHash;previous_private_failure_sha256='d64769c8ab8bd942d316e0087aa7557009988103b692c1adfe3487d05e48fe63';
 prefix_backup_verified=$true;prefix_backup_bytes=100663296;prefix_backup_sha256='25b1107c216ef0c489e6075bd8bb08be5ccf454d9b99cca9285d2b5616a0e068';
 prefix_zero_verified_before_new_layout=$true;prefix_zero_sha256=$zeroHash;normal_fat32_verified=$false;
 diskpart_executed=$false;full_format=$false;tv_contacted=$false;kingston_modified=$false;
 safe_removal_pending=$true;windows_volume_flush_verified=$false}
$receiptStream=[IO.File]::Open($finalReceipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try {
 SaveFinal
 Assert-ScriptUnchanged
 $null=EmptySD
 $state.diskpart_executed=$true;SaveFinal
 $log=Join-Path $private 'diskpart.log'
 $native=Join-Path ([Environment]::GetFolderPath('Windows')) 'System32/diskpart.exe'
 & $native /s $commandFile 2>&1 | Out-File -LiteralPath $log -Encoding utf8
 $state.diskpart_exit=$LASTEXITCODE;$state.diskpart_log_sha256=Hash-Ordinary $log
 if($LASTEXITCODE -ne 0){throw 'DiskPart devolvio error'}
 # El codigo nativo no acredita exito: comprobar disco, tabla, volumen y contenido.
 $final=Get-CheckedSD 'Final'
 $empty=Get-RootSnapshot $final.Mount $true
 $raw=Open-CheckedRaw 'Final' $false
 try {
  $bytes=New-Object byte[] 1048576
  if($raw.Read($bytes,0,$bytes.Length) -ne $bytes.Length){throw 'Lectura MBR corta'}
  if($bytes[510] -ne 85 -or $bytes[511] -ne 170 -or $bytes[446] -ne 0 -or $bytes[450] -notin @(11,12) -or
     [BitConverter]::ToUInt32($bytes,454) -ne 2048 -or
     ([long][BitConverter]::ToUInt32($bytes,458)*512) -ne $final.Partition.Size){throw 'Tabla MBR no coincide con geometria final'}
  for($i=462;$i -lt 510;$i++){if($bytes[$i] -ne 0){throw 'Hay otra entrada MBR'}}
  for($i=512;$i -lt 1048576;$i++){if($bytes[$i] -ne 0){throw 'Prefijo anterior conserva datos'}}
 }finally{$raw.Dispose()}
 $state.partition_offset=[long]$final.Partition.Offset;$state.partition_bytes=[long]$final.Partition.Size
 $state.filesystem=[string]$final.Volume.FileSystem;$state.free_bytes=[long]$final.Volume.SizeRemaining
 $state.mbr_read_verified=$true;$state.gap_512_to_1m_zero_verified=$true;$state.normal_fat32_verified=$true
 $state.state='formateada_sd_normal';$state.phase='final_verified';$state.utc=[DateTime]::UtcNow.ToString('o');SaveFinal
 Write-Output 'SD FAT32 normal, MBR y espacio previo verificados. Lista para copiar extractor.'
}catch{$state.state='failed_preserved';$state.error_type=$_.Exception.GetType().FullName;SaveFinal;throw}
finally{$receiptStream.Dispose()}
