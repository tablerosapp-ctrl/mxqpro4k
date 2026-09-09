param([Parameter(Mandatory=$true)][string]$PackagePath,[switch]$Prepare)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskSD='USBSTOR\DISK&VEN_MASS&PROD_STORAGE_DEVICE&REV__\LECTOR-SD-LOCAL&0:PC_LOCAL'
$taskUSB='USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$taskReceipt=Join-Path $PSScriptRoot 'sd-rk3229-c-02-estado.json'
$taskBuild=Join-Path $taskRoot 'diagnostico/extractor-recovery-rk2/COMPILACION.json'
$taskEvidence=Join-Path $taskRoot 'privado/rk3229-c-sin-usb-20260909'
$taskGuide=Join-Path $taskRoot 'docs/evidencia/LEEME-SD-RK3229-C-02.txt'
$taskMarker=Join-Path $taskRoot 'privado/rk3229-c-sd02-insumos/MEDIA.json'
$taskPlan=Join-Path $taskEvidence 'RK3229-C.json'
$taskPrior=Join-Path $PSScriptRoot 'entregar-sd-rk3229-c-final.ps1'
if((Get-FileHash -LiteralPath $taskPrior -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'b89b501c0c31ba48adaaeb8383ce8cb025b7dccabb41f52268d77d25e096f9ae'){throw 'Funciones previas alteradas'}
$parseErrors=$null;$tokens=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($taskPrior,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'No se pueden leer funciones verificadas'}
# Importar funciones de consulta, no el flujo de entrega anterior.
foreach($name in @('HashFile','Media','SameMedium','CheckUSB')){
 $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst]},$false)|Where-Object Name -ceq $name)
 if($defs.Count -ne 1){throw 'Funcion previa no unica'}
 . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
function Contained([string]$base,[string]$path){
 $b=[IO.Path]::GetFullPath($base).TrimEnd('\')+'\';$p=[IO.Path]::GetFullPath($path)
 if(-not $p.StartsWith($b,[StringComparison]::OrdinalIgnoreCase)){throw 'Ruta fuera del destino previsto'}
 $current=$p
 while($current -and $current.Length -ge $b.TrimEnd('\').Length){
  if(Test-Path -LiteralPath $current){if((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Ruta enlazada'}}
  $current=[IO.Path]::GetDirectoryName($current)
 }
 return $p
}
function CopyNew([string]$source,[string]$target,[string]$expected){
 if((HashFile $source) -cne $expected){throw 'Insumo cambio'}
 $inputFile=[IO.File]::OpenRead($source)
 try{$out=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$inputFile.CopyTo($out);$out.Flush($true)}finally{$out.Dispose()}
 }finally{$inputFile.Dispose()}
 if((HashFile $target) -cne $expected -or (Get-Item -LiteralPath $source).Length -ne (Get-Item -LiteralPath $target).Length){throw 'Copia no coincide'}
}
function Persist{
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($taskState|ConvertTo-Json -Depth 12)+"`n")
 $taskStream.Position=0;$taskStream.SetLength(0);$taskStream.Write($bytes,0,$bytes.Length);$taskStream.Flush($true)
}
function Recheck{
 SameMedium $sd (Media $taskSD 8053063680 'Mass Storage Device' 'TVBASESD')
 SameMedium $usb (CheckUSB)
 foreach($i in $inputs){if((HashFile $i.source) -cne $i.hash){throw 'Insumo de entrega cambio'}}
 if((HashFile $PSCommandPath) -cne $taskScriptSHA -or (HashFile $taskBuild) -cne $taskBuildSHA){throw 'Fuente/recibo cambio'}
}
if(Test-Path -LiteralPath $taskReceipt){throw 'Entrega ya iniciada; revisar recibo sin repetir'}
$package=Contained (Join-Path $taskRoot 'privado') ([IO.Path]::GetFullPath((Join-Path $taskRoot $PackagePath)))
if([IO.Path]::GetFileName($package) -cne 'TVBASE-EXTRACTOR-0.2-RK2-ARM32-RECOVERY.zip'){throw 'Paquete no corresponde a SD0.2'}
$build=Get-Content -LiteralPath $taskBuild -Raw | ConvertFrom-Json
if($build.state -cne 'verified_pc' -or $build.package -cne [IO.Path]::GetFileName($package) -or
   $build.extractor_version -cne '0.2' -or -not $build.python_verified -or -not $build.openjdk_verified -or -not $build.crc_verified){throw 'Construccion no verificada'}
if((HashFile $package) -cne $build.sha256 -or (Get-Item -LiteralPath $package).Length -ne $build.bytes){throw 'Paquete no coincide con construccion'}
if((HashFile $taskPlan) -cne 'f5f15963b2d8d98eb81e17b45f824f541ef2b47f7d511ac0b29e12d5a7b67311'){throw 'Plan no es C'}
$marker=Get-Content -LiteralPath $taskMarker -Raw|ConvertFrom-Json
if($marker.schema -cne 'tvbase-recovery-media-1' -or $marker.media_id -cne 'tvbase-recovery-sd-rk3229-c-20260909' -or @($marker.PSObject.Properties).Count -ne 2){throw 'Marcador SD no corresponde'}
$sd=Media $taskSD 8053063680 'Mass Storage Device' 'TVBASESD'
$usb=CheckUSB
if($sd.partition_bytes -ne 8052015104 -or $sd.number -eq $usb.number -or $sd.mount -ceq $usb.mount){throw 'Medios/geometria no coinciden'}
$old=@(@{name='update.zip';archive='update-rk1.zip';hash='0f7fe7a5f609290f69597c599ac8c72954b4fc7e04957cd27b279a368f060c38'},
 @{name='LEEME-SD.txt';archive='LEEME-SD-rk1.txt';hash='e0f0ed9fe72f6d30cc9b18a01aa8968321b0b38845c7838d49ff812efab17e24'})
$names=@(Get-ChildItem -LiteralPath $sd.mount -Force|Where-Object Name -ine 'System Volume Information'|Select-Object -ExpandProperty Name|Sort-Object)
if(($names -join '|') -cne 'LEEME-SD.txt|update.zip'){throw 'Contenido SD distinto; conservar antes de preparar'}
foreach($i in $old){if((HashFile (Join-Path $sd.mount $i.name)) -cne $i.hash -or (HashFile (Join-Path $taskEvidence $i.archive)) -cne $i.hash){throw 'Respaldo de entrega anterior falta/difiere'}}
$inputs=@(@{source=$package;name='update.zip';stage='TVBASE-RK2-NUEVO.zip';hash=$build.sha256},
 @{source=$taskGuide;name='LEEME-SD.txt';stage='TVBASE-GUIA-NUEVA.txt';hash=(HashFile $taskGuide)},
 @{source=$taskMarker;name='TVBASE-EXTRACCION/MEDIA.json';stage='TVBASE-EXTRACCION/MEDIA.json';hash=(HashFile $taskMarker)},
 @{source=$taskPlan;name='TVBASE-EXTRACCION/PLANES/RK3229-C.json';stage='TVBASE-EXTRACCION/PLANES/RK3229-C.json';hash=(HashFile $taskPlan)})
$newBytes=($inputs|ForEach-Object{[long](Get-Item -LiteralPath $_.source).Length}|Measure-Object -Sum).Sum
# eMMC declarada + dos areas boot conservadoras de4MiB + reserva128MiB.
# Recovery recalcula las fuentes reales y no omite areas para ajustar espacio.
if($sd.free -lt (7818182656+8388608+134217728+$newBytes)){throw 'SD sin espacio suficiente estimado'}
$taskScriptSHA=HashFile $PSCommandPath;$taskBuildSHA=HashFile $taskBuild
if(-not $Prepare){Write-Output 'SD0.2: insumos, archivo anterior, identidad y espacio comprobados sin escrituras';return}
$taskState=[ordered]@{schema='tvbase-sd-extractor-delivery-2';state='started';utc=[DateTime]::UtcNow.ToString('o');
 script_sha256=$taskScriptSHA;build_receipt_sha256=$taskBuildSHA;sd_bytes=8053063680;partition_bytes=8052015104;partition_offset=1048576;label='TVBASESD';
 archived_before_removal=$old;files=@();kingston_modified=$false;sd_formatted=$false;raw_writes=$false;tv_contacted=$false;physical_extraction=$false;
 same_sd_load_and_destination=$true;profile='RK3229-C';safe_removal_pending=$true;volume_flush_verified=$false}
$taskStream=[IO.File]::Open($taskReceipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{
 Persist;Recheck
 foreach($name in @('TVBASE-EXTRACCION','TVBASE-EXTRACCION/PLANES','TVBASE-EXTRACCION/CAPTURAS')){
  $p=Contained $sd.mount (Join-Path $sd.mount $name)
  if(Test-Path -LiteralPath $p){throw 'Carpeta ya existe'}
  Recheck;New-Item -ItemType Directory -Path $p -ErrorAction Stop|Out-Null
 }
 foreach($i in $inputs){Recheck;$p=Contained $sd.mount (Join-Path $sd.mount $i.stage);CopyNew $i.source $p $i.hash}
 # Solo se retiran los dos archivos anteriores, respaldados y revalidados.
 foreach($i in $old){Recheck;$p=Contained $sd.mount (Join-Path $sd.mount $i.name)
  if((HashFile $p) -cne $i.hash -or (HashFile (Join-Path $taskEvidence $i.archive)) -cne $i.hash){throw 'Archivo antiguo cambio'}
  if([IO.Path]::GetDirectoryName($p).TrimEnd('\') -cne $sd.mount.TrimEnd('\')){throw 'Retiro fuera de raiz SD'}
  Remove-Item -LiteralPath $p -ErrorAction Stop
 }
 foreach($i in $inputs|Where-Object {$_.stage -cne $_.name}){
  Recheck;$from=Contained $sd.mount (Join-Path $sd.mount $i.stage);$to=Contained $sd.mount (Join-Path $sd.mount $i.name)
  if((HashFile $from) -cne $i.hash -or (Test-Path -LiteralPath $to)){throw 'Cambio antes del nombre final'}
  [IO.File]::Move($from,$to)
 }
 Recheck
 foreach($i in $inputs){$p=Contained $sd.mount (Join-Path $sd.mount $i.name)
  if((HashFile $p) -cne $i.hash){throw 'Lectura final difiere'}
  $taskState.files+=@{name=$i.name;bytes=[long](Get-Item -LiteralPath $p).Length;sha256=$i.hash;file_flush=$true;readback_verified=$true}
 }
 $expected=@('LEEME-SD.txt','TVBASE-EXTRACCION/MEDIA.json','TVBASE-EXTRACCION/PLANES/RK3229-C.json','update.zip')|Sort-Object
 $payloadRoots=@(Get-ChildItem -LiteralPath $sd.mount -Force|Where-Object Name -ine 'System Volume Information')
 $actual=@($payloadRoots|ForEach-Object {if($_.PSIsContainer){Get-ChildItem -LiteralPath $_.FullName -File -Recurse -Force}else{$_}}|ForEach-Object {$_.FullName.Substring($sd.mount.Length).Replace('\','/')}|Sort-Object)
 if(($actual -join '|') -cne ($expected -join '|')){throw 'Contenido final inesperado'}
 if(@(Get-ChildItem -LiteralPath (Join-Path $sd.mount 'TVBASE-EXTRACCION/CAPTURAS') -Force).Count){throw 'Capturas aparecieron durante preparacion'}
 $taskState.free_bytes_after=(Media $taskSD 8053063680 'Mass Storage Device' 'TVBASESD').free
 $taskState.state='copied_readback_verified';$taskState.utc=[DateTime]::UtcNow.ToString('o');Persist
 Write-Output 'SD0.2 entregada y releida; plan C y copias en misma SD. Kingston conservado. Expulsion pendiente.'
}catch{$taskState.state='failed_preserved';$taskState.error=$_.Exception.Message;Persist;throw}
finally{$taskStream.Dispose()}
