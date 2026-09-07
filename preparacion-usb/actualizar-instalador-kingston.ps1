# Copy the reviewed recovery-preservation revision without formatting or changing partitions.
[CmdletBinding()]param()
$ErrorActionPreference='Stop'
throw 'Preparador APK0.3 retirado tras el fallo de entrada a recovery. Usar preparar-entrada-amlogic.ps1 para APK0.4 y recovery externo, sin formatear.'
$root=Split-Path $PSScriptRoot -Parent
$expectedId='USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$expectedSize=[long]30943995904
$runDir=Join-Path $PSScriptRoot ('revision-011-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $runDir | Out-Null
$state=[ordered]@{estado='comprobando';inicio=(Get-Date).ToString('o');usb_id=$expectedId;informe=$runDir;tv_flasheado=$false}
function Save-State([string]$phase,[string]$detail){$state.estado=$phase;$state.detalle=$detail;$state.fecha=(Get-Date).ToString('o');$j=$state|ConvertTo-Json -Depth 8;$j|Set-Content -LiteralPath (Join-Path $runDir 'resultado.json') -Encoding UTF8;$j|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'revision-011-estado.json') -Encoding UTF8}
function Get-Target {
 $candidates=@(Get-Disk | Where-Object UniqueId -eq $expectedId)
 if($candidates.Count -ne 1){throw 'No hay un unico Kingston identificado'}
 $disk=$candidates[0]
 if($disk.Size -ne $expectedSize -or $disk.FriendlyName -ne 'Kingston DataTraveler 3.0' -or $disk.BusType -ne 'USB' -or $disk.IsBoot -or $disk.IsSystem -or $disk.IsOffline -or $disk.IsReadOnly){throw 'Identidad o estado de disco no permitido'}
 $parts=@($disk|Get-Partition)
 if($parts.Count -ne 1){throw 'La estructura del USB cambio; no se modifica'}
 $volume=$parts[0]|Get-Volume
 if($volume.FileSystem -ne 'FAT32' -or $volume.FileSystemLabel -ne 'TVBASE' -or $volume.Size -ne 30925651968){throw 'Volumen TVBASE distinto del esperado'}
 if([IO.File]::ReadAllText((Join-Path $volume.Path 'TVBASE-MEDIA.txt')).Trim() -ne 'TVBASE-P291-20260906-4dc82786'){throw 'Marcador USB distinto'}
 return @{disk=$disk;volume=$volume}
}
function Copy-Verified([string]$source,[string]$name,[string]$expected){
 $current=Get-Target
 if($current.volume.Path -ne $script:targetPath){throw 'Cambio el volumen durante la copia'}
 $dest=Join-Path $script:targetPath $name
 if(Test-Path -LiteralPath $dest){
  if((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw ('Ya existe un archivo distinto: '+$name)}
 }else{
  $inputFile=[IO.File]::OpenRead($source);$outputFile=[IO.File]::Open($dest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$inputFile.CopyTo($outputFile,524288);$outputFile.Flush($true)}finally{$inputFile.Dispose();$outputFile.Dispose()}
  if((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw ('Lectura distinta al origen: '+$name)}
 }
 return @{archivo=$name;sha256=$expected;bytes=(Get-Item -LiteralPath $dest).Length;lectura_verificada=$true}
}
try{
 Save-State 'comprobando' 'Comprobando revision 0.1.1 y Kingston; se conservan particiones y respaldos.'
 $report=Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/salida/RECOVERY-VERIFICACION-0.1.1.json')|ConvertFrom-Json
 $proof=Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/salida/RECOVERY-COMPROBACION-0.1.1.json')|ConvertFrom-Json
 if(-not $report.whole_file_signature_verified -or -not $report.payload_sha256_verified -or -not $report.recovery_preservation_revision.inherited_recovery_replacement_disabled){throw 'Revision no verificada'}
 if($proof.sha256 -ne $report.sha256 -or -not $proof.openjdk_signature_verified -or -not $proof.go_payload_verified -or -not $proof.old_version_rejected){throw 'Faltan comprobaciones independientes de la revision'}
 $rom=Join-Path $root $report.file
 if((Get-FileHash -LiteralPath $rom -Algorithm SHA256).Hash.ToLowerInvariant() -ne $report.sha256){throw 'Cambio la ROM local'}
 $apkReport=@(Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/compilacion/acceso-usb-componente.json')|ConvertFrom-Json)[0]
 $apk=Join-Path $root $apkReport.path
 if((Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLowerInvariant() -ne $apkReport.sha256){throw 'Cambio la APK local'}
 $apkProof=Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/compilacion/acceso-usb/firma.txt')
 if(-not $apkProof.Contains('d2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613')){throw 'Firmante APK distinto de la version instalada'}
 $adbTests=@(Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/instalador/ADB-TESTS-0.3.json')|ConvertFrom-Json)
 if($adbTests.Count -ne 9 -or @($adbTests|Where-Object {-not $_.passed}).Count){throw 'Faltan pruebas ADB 0.3'}
 if(@(Get-Process -Name 'rpi-imager','diskpart','rufus*' -ErrorAction SilentlyContinue).Count){throw 'Hay otra herramienta de disco activa'}
 $target=Get-Target;$script:targetPath=$target.volume.Path
 Get-ChildItem -LiteralPath $targetPath -Force | Select-Object Name,Length,Attributes | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDir 'archivos-antes.json') -Encoding UTF8
 # Archive small recovery logs/manifests on the PC. Every backup image remains untouched on USB.
 $backupNames=@()
 foreach($folder in @(Get-ChildItem -LiteralPath $targetPath -Directory -Filter 'TVBASE-respaldo-*')){
  $backupNames+=$folder.Name
  $localFolder=Join-Path $runDir $folder.Name;New-Item -ItemType Directory -Path $localFolder|Out-Null
  foreach($name in @('respaldo.json','instalacion.log')){
   $item=Join-Path $folder.FullName $name
   if(Test-Path -LiteralPath $item){Copy-Item -LiteralPath $item -Destination (Join-Path $localFolder $name)}
  }
 }
 $state.respaldos_tv_conservados=$backupNames
 Save-State 'copiando' 'Copiando y leyendo la ROM corregida, sin borrar los respaldos del TV.'
 $written=@(Copy-Verified $rom 'TVBASE-P291-A9-0.1.1-RECOVERY.zip' $report.sha256)
 $written+=Copy-Verified $apk 'AccesoUSB-0.3.apk' $apkReport.sha256
 $readme=Join-Path $root 'rom-simplificada/instalador/LEEME-0.1.1.txt'
 $written+=Copy-Verified $readme 'LEEME-0.1.1.txt' (Get-FileHash -LiteralPath $readme -Algorithm SHA256).Hash.ToLowerInvariant()
 # Only withdraw the exact known old package after the new package was verified.
 $current=Get-Target;if($current.volume.Path -ne $targetPath){throw 'Cambio el USB antes de retirar la version antigua'}
 $old=Join-Path $targetPath 'TVBASE-P291-A9-0.1-RECOVERY.zip'
 if(Test-Path -LiteralPath $old){
  if((Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'f4faca862a920d306d760e0f0da29751d1f322fb1fc72dade7a0f63657f19b07'){throw 'El ZIP anterior no coincide; se conserva sin renombrar'}
  $retired=Join-Path $targetPath 'TVBASE-P291-A9-0.1-RECOVERY.zip.no-usar'
  if(Test-Path -LiteralPath $retired){throw 'Ya existe archivo retirado; revisar sin sobrescribir'}
  Move-Item -LiteralPath $old -Destination $retired
 }
 $oldReadme=Join-Path $targetPath 'LEEME.txt'
 if(Test-Path -LiteralPath $oldReadme){
  if((Get-FileHash -LiteralPath $oldReadme -Algorithm SHA256).Hash.ToLowerInvariant() -eq 'd01dd61bb2aa1992145666fb5bda2203e76c4586e26809ca8abf4db0e27fad64'){
   $retiredReadme=Join-Path $targetPath 'LEEME-0.1-retirado.txt'
   if(-not(Test-Path -LiteralPath $retiredReadme)){Move-Item -LiteralPath $oldReadme -Destination $retiredReadme}
  }
 }
 $oldApk=Join-Path $targetPath 'AccesoUSB.apk'
 if(Test-Path -LiteralPath $oldApk){
  if((Get-FileHash -LiteralPath $oldApk -Algorithm SHA256).Hash.ToLowerInvariant() -ne '328e0420124afcd6874d904956ae715467b1e95d0f99828ea1402992e8980fce'){throw 'APK anterior distinto; se conserva sin renombrar'}
  $retiredApk=Join-Path $targetPath 'AccesoUSB-0.2.apk.no-usar'
  if(Test-Path -LiteralPath $retiredApk){throw 'Ya existe APK retirada; revisar sin sobrescribir'}
  Move-Item -LiteralPath $oldApk -Destination $retiredApk
 }
 $state.files=$written;$state.drive_letter=$current.volume.DriveLetter;$state.volume=$targetPath
 Save-State 'verificado' 'Revision 0.1.1 copiada y leida correctamente; falta aplicarla en el TV.'
 exit 0
}catch{Save-State 'fallo' ($_.Exception.ToString());$_|Out-String|Set-Content -LiteralPath (Join-Path $runDir 'error.txt') -Encoding UTF8;exit 1}
