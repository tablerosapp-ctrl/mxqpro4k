param([switch]$Prepare)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskSD='USBSTOR\DISK&VEN_MASS&PROD_STORAGE_DEVICE&REV__\LECTOR-SD-LOCAL&0:PC_LOCAL'
$taskUSB='USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskReceipt=Join-Path $PSScriptRoot 'sd-rk3229-c-entrega-estado.json'
$taskFormatReceipt=Join-Path $PSScriptRoot 'sd-rk3229-c-continuacion-estado.json'
$taskZip=Join-Path $taskRoot 'privado/extractor-rk1-20260908/TVBASE-EXTRACTOR-0.1-RK1-ARM32-RECOVERY.zip'
$taskGuide=Join-Path $taskRoot 'docs/evidencia/LEEME-SD-RK3229-C.txt'
$taskZipHash='0f7fe7a5f609290f69597c599ac8c72954b4fc7e04957cd27b279a368f060c38'

function HashFile([string]$p) {
 $i=Get-Item -LiteralPath $p -Force
 if($i.PSIsContainer -or ($i.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Archivo no ordinario'}
 return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Media([string]$id,[long]$size,[string]$name,[string]$label) {
 $ds=@(Get-Disk -UniqueId $id)
 if($ds.Count -ne 1){throw 'Dispositivo no unico'}
 $d=$ds[0]
 if($d.UniqueId -cne $id -or $d.Size -ne $size -or $d.FriendlyName -cne $name -or
    [string]$d.BusType -cne 'USB' -or $d.IsSystem -or $d.IsBoot -or $d.IsReadOnly -or $d.IsOffline -or
    [string]$d.PartitionStyle -cne 'MBR'){throw 'Identidad de medio distinta'}
 $ps=@(Get-Partition -DiskNumber $d.Number)
 if($ps.Count -ne 1 -or $ps[0].Offset -ne 1048576 -or $ps[0].IsBoot -or $ps[0].IsSystem){throw 'Geometria inesperada'}
 $p=$ps[0]; $vs=@(Get-Volume -Partition $p)
 if($vs.Count -ne 1 -or [string]$vs[0].FileSystem -cne 'FAT32' -or $vs[0].FileSystemLabel -cne $label -or
    [string]$p.DriveLetter -cnotmatch '^[A-Z]$'){throw 'Volumen no coincide'}
 $mount=([string]$p.DriveLetter)+':\'
 if((Get-Item -LiteralPath $mount -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Raiz enlazada'}
 return [pscustomobject]@{number=[int]$d.Number; mount=$mount; partition_bytes=[long]$p.Size; free=[long]$vs[0].SizeRemaining}
}
function CheckUSB {
 $u=Media $taskUSB 30943995904 'Kingston DataTraveler 3.0' 'TVBASE'
 if($u.partition_bytes -ne 30942429184){throw 'Geometria Kingston distinta'}
 if([IO.File]::ReadAllText((Join-Path $u.mount 'TVBASE-MEDIA.txt')).Trim() -cne 'TVBASE-P291-20260906-4dc82786'){throw 'Marcador USB distinto'}
 foreach($name in @('update.zip','update.img')){if(Test-Path -LiteralPath (Join-Path $u.mount $name)){throw 'Actualizacion automatica presente en USB; no entregar'}}
 $plan=Join-Path $u.mount 'TVBASE-EXTRACCION/PLANES/RK3229-C.json'
 if((HashFile $plan) -cne 'f5f15963b2d8d98eb81e17b45f824f541ef2b47f7d511ac0b29e12d5a7b67311'){throw 'Plan C distinto'}
 $plans=@(Get-ChildItem -LiteralPath (Join-Path $u.mount 'TVBASE-EXTRACCION/PLANES') -Force)
 if($plans.Count -ne 2 -or @($plans | Where-Object {$_.Name -notin @('P271.json','RK3229-C.json')}).Count){throw 'Planes adicionales o faltantes'}
 if(@(Get-ChildItem -LiteralPath (Join-Path $u.mount 'TVBASE-EXTRACCION/CAPTURAS') -Force).Count){throw 'Hay capturas nuevas sin adquirir'}
 return $u
}
function SameMedium($a,$b) {
 if($a.number -ne $b.number -or $a.mount -cne $b.mount -or $a.partition_bytes -ne $b.partition_bytes){throw 'Cambio el medio durante la entrega'}
}
function SaveReceipt($state) {
 $payload=[Text.UTF8Encoding]::new($false).GetBytes(($state|ConvertTo-Json -Depth 12)+"`n")
 $taskReceiptStream.Position=0; $taskReceiptStream.SetLength(0)
 $taskReceiptStream.Write($payload,0,$payload.Length); $taskReceiptStream.Flush($true)
}
if(Test-Path -LiteralPath $taskReceipt){throw 'Entrega ya iniciada; conservar recibo, no repetir'}
$fr=Get-Content -LiteralPath $taskFormatReceipt -Raw | ConvertFrom-Json
if($fr.schema -cne 'tvbase-sd-normal-preparation-1' -or $fr.disk_identity_sha256 -cne '83e0b5dd47383a39d4b7996bdac16d9ba9b397dc87c34b5fd593ff6404f04076' -or $fr.disk_bytes -ne 8053063680 -or $fr.final_label -cne 'TVBASESD' -or $fr.state -cne 'formateada_sd_normal' -or -not $fr.normal_fat32_verified -or -not $fr.prefix_backup_verified -or
   -not $fr.prefix_zero_verified_before_new_layout){throw 'Falta preparacion SD completa'}
if((HashFile $taskZip) -cne $taskZipHash -or (Get-Item -LiteralPath $taskZip).Length -ne 1380273){throw 'Paquete distinto'}
$taskGuideHash=HashFile $taskGuide
$taskScriptHash=HashFile $PSCommandPath
$sd=Media $taskSD 8053063680 'Mass Storage Device' 'TVBASESD'
if($sd.partition_bytes -le 7952400384 -or $sd.partition_bytes+1048576 -gt 8053063680 -or 8053063680-$sd.partition_bytes-1048576 -gt 2MB){throw 'Particion SD no maxima'}
$usb=CheckUSB
if($sd.number -eq $usb.number -or $sd.mount -ceq $usb.mount){throw 'SD y Kingston no son distintos'}
$old=@(Get-ChildItem -LiteralPath $sd.mount -Force)
if(@($old|Where-Object {$_.Name -ine 'System Volume Information' -or -not $_.PSIsContainer}).Count){throw 'La SD no esta vacia'}
if($sd.free -lt 16MB){throw 'SD sin espacio'}
if(-not $Prepare){Write-Output 'Entrega SD comprobada sin escrituras';return}
$taskState=[ordered]@{schema='tvbase-sd-extractor-delivery-1';state='started';utc=[DateTime]::UtcNow.ToString('o');
 script_sha256=$taskScriptHash;format_receipt_sha256=(HashFile $taskFormatReceipt);sd_bytes=8053063680;label='TVBASESD';
 files=@();kingston_modified=$false;kingston_plan_c_sha256='f5f15963b2d8d98eb81e17b45f824f541ef2b47f7d511ac0b29e12d5a7b67311';
 usb_auto_update_names_absent=$true;tv_contacted=$false;physical_extraction=$false;
 safe_removal_pending=$true;volume_flush_verified=$false}
$taskReceiptStream=[IO.File]::Open($taskReceipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try {
 SaveReceipt $taskState
 foreach($item in @(@{source=$taskZip;name='update.zip';hash=$taskZipHash},@{source=$taskGuide;name='LEEME-SD.txt';hash=$taskGuideHash})) {
  SameMedium $sd (Media $taskSD 8053063680 'Mass Storage Device' 'TVBASESD')
  SameMedium $usb (CheckUSB)
  if((HashFile $PSCommandPath) -cne $taskScriptHash -or (HashFile $item.source) -cne $item.hash){throw 'Insumo alterado'}
  $target=[IO.Path]::GetFullPath((Join-Path $sd.mount $item.name))
  if([IO.Path]::GetDirectoryName($target).TrimEnd('\') -cne $sd.mount.TrimEnd('\')){throw 'Destino fuera de la raiz SD'}
  $inputStream=[IO.File]::OpenRead($item.source)
  try {
   $outputStream=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
   try {$inputStream.CopyTo($outputStream);$outputStream.Flush($true)}finally{$outputStream.Dispose()}
  } finally {$inputStream.Dispose()}
  if((HashFile $target) -cne $item.hash -or (Get-Item -LiteralPath $target).Length -ne (Get-Item -LiteralPath $item.source).Length){throw 'Copia SD no coincide'}
  $taskState.files+=@{name=$item.name;bytes=[long](Get-Item -LiteralPath $target).Length;sha256=$item.hash;file_flush=$true;readback_verified=$true}
  SaveReceipt $taskState
 }
 SameMedium $sd (Media $taskSD 8053063680 'Mass Storage Device' 'TVBASESD')
 SameMedium $usb (CheckUSB)
 $names=@(Get-ChildItem -LiteralPath $sd.mount -Force | Where-Object Name -ine 'System Volume Information' | Select-Object -ExpandProperty Name | Sort-Object)
 if(($names -join '|') -cne 'LEEME-SD.txt|update.zip'){throw 'Archivos extra en SD'}
 foreach($item in $taskState.files){if((HashFile (Join-Path $sd.mount $item.name)) -cne $item.sha256){throw 'Relectura final distinta'}}
 $taskState.state='copied_readback_verified';$taskState.utc=[DateTime]::UtcNow.ToString('o');SaveReceipt $taskState
 Write-Output 'SD preparada: update.zip y guia verificados. Kingston conservado. Expulsion segura pendiente.'
}catch{$taskState.state='failed_preserved';$taskState.error_type=$_.Exception.GetType().FullName;SaveReceipt $taskState;throw}
finally{$taskReceiptStream.Dispose()}
