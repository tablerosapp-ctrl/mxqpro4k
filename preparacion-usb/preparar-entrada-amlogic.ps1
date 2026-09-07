# Prepare the authorized Kingston for an Amlogic update attempt; no format or disk layout changes.
[CmdletBinding()]param()
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$usbId='USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$runDir=Join-Path $PSScriptRoot ('entrada-amlogic-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $runDir|Out-Null
$state=[ordered]@{estado='comprobando';inicio=(Get-Date).ToString('o');informe=$runDir;usb_id=$usbId;tv_flasheado=$false}
function Save-State([string]$phase,[string]$detail){$state.estado=$phase;$state.detalle=$detail;$state.fecha=(Get-Date).ToString('o');$json=$state|ConvertTo-Json -Depth 8;$json|Set-Content -LiteralPath (Join-Path $runDir 'resultado.json') -Encoding UTF8;$json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'entrada-amlogic-estado.json') -Encoding UTF8}
function Get-Target {
 $candidates=@(Get-Disk|Where-Object UniqueId -eq $usbId)
 if($candidates.Count -ne 1){throw 'No hay un unico Kingston identificado'}
 $disk=$candidates[0]
 if($disk.Size -ne 30943995904 -or $disk.FriendlyName -ne 'Kingston DataTraveler 3.0' -or $disk.BusType -ne 'USB' -or $disk.IsBoot -or $disk.IsSystem -or $disk.IsOffline -or $disk.IsReadOnly){throw 'Identidad o estado de disco no permitido'}
 $parts=@($disk|Get-Partition);if($parts.Count -ne 1){throw 'Estructura USB distinta'}
 $volume=$parts[0]|Get-Volume
 if($volume.FileSystem -ne 'FAT32' -or $volume.FileSystemLabel -ne 'TVBASE' -or $volume.Size -ne 30925651968){throw 'Volumen distinto'}
 if([IO.File]::ReadAllText((Join-Path $volume.Path 'TVBASE-MEDIA.txt')).Trim() -ne 'TVBASE-P291-20260906-4dc82786'){throw 'Marcador distinto'}
 return @{disk=$disk;volume=$volume}
}
function Copy-Verified([string]$source,[string]$name,[string]$expected){
 if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw ('Fuente distinta: '+$name)}
 $target=Get-Target;if($target.volume.Path -ne $script:usbPath){throw 'Cambio el USB'}
 $dest=Join-Path $script:usbPath $name
 if(-not(Test-Path -LiteralPath $dest)){
  $inputFile=[IO.File]::OpenRead($source);$outputFile=[IO.File]::Open($dest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$inputFile.CopyTo($outputFile,524288);$outputFile.Flush($true)}finally{$inputFile.Dispose();$outputFile.Dispose()}
 }
 if((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw ('Archivo USB distinto: '+$name)}
 return @{archivo=$name;bytes=(Get-Item -LiteralPath $dest).Length;sha256=$expected;lectura_verificada=$true}
}
try{
 Save-State 'comprobando' 'Validando el recovery externo, APK 0.4, ROM existente y Kingston.'
 $target=Get-Target;$script:usbPath=$target.volume.Path
 if(@(Get-Process -Name 'rpi-imager','diskpart','rufus*' -ErrorAction SilentlyContinue).Count){throw 'Hay otro grabador activo'}
 foreach($name in @('aml_autoscript','aml_sdc_burn.ini','factory_update_param.aml','update.zip','dtb.img')){if(Test-Path -LiteralPath (Join-Path $usbPath $name)){throw ('Archivo de arranque inesperado: '+$name)}}
 Get-ChildItem -LiteralPath $usbPath -Force|Select-Object Name,Length,Attributes|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $runDir 'archivos-antes.json') -Encoding UTF8
 $recovery=Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/instalador/recovery-externo/PREPARADO.json')|ConvertFrom-Json
 if(-not $recovery.android_v1_id_verified -or -not $recovery.rom_zip_signature_verified_with_added_key -or $recovery.signature_verification_disabled -or -not $recovery.original_key_retained){throw 'Recovery sin comprobar'}
 $apk=@(Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/compilacion/acceso-usb-componente.json')|ConvertFrom-Json)[0]
 $proof=Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/compilacion/acceso-usb/firma.txt')
 if(-not $proof.Contains('d2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613')){throw 'La firma APK no coincide con la version instalada'}
 $badging=& (Join-Path $root 'tools/verificacion-apk/build-tools-37/android-37.0/aapt2.exe') dump badging (Join-Path $root $apk.path)
 if($LASTEXITCODE -ne 0 -or -not ($badging -match "versionCode='4' versionName='0.4'")){throw 'La APK no es la version 0.4'}
 $tests=@(Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/instalador/ADB-TESTS-0.4.json')|ConvertFrom-Json)
 if($tests.Count -ne 12 -or @($tests|Where-Object {-not $_.passed}).Count){throw 'Faltan pruebas ADB 0.4'}
 if(-not(Test-Path -LiteralPath (Join-Path $root 'rom-simplificada/instalador/ENTRADA-TESTS-0.4.txt'))){throw 'Faltan pruebas de condiciones previas'}
 $romName='TVBASE-P291-A9-0.1.1-RECOVERY.zip';$romHash='e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205'
 $romFile=Join-Path $usbPath $romName
 if((Get-FileHash -LiteralPath $romFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $romHash){throw 'ROM USB distinta; no se copia otra ni se reinicia automaticamente'}
 Save-State 'copiando' 'Copiando la entrada Amlogic y recovery externo. No se formatea ni se modifica el TV.'
 $written=@(@{archivo=$romName;bytes=(Get-Item -LiteralPath $romFile).Length;sha256=$romHash;lectura_verificada=$true;ya_existente=$true})
 $written+=Copy-Verified (Join-Path $root $apk.path) 'AccesoUSB-0.4.apk' $apk.sha256
 $written+=Copy-Verified (Join-Path $root $recovery.file) 'recovery.img' $recovery.sha256
 $readme=Join-Path $root 'rom-simplificada/instalador/LEEME-ENTRADA-AMLOGIC.txt'
 $written+=Copy-Verified $readme 'LEEME-AHORA.txt' (Get-FileHash -LiteralPath $readme -Algorithm SHA256).Hash.ToLowerInvariant()
 $current=Get-Target;if($current.volume.Path -ne $usbPath){throw 'Cambio el USB'}
 $old=Join-Path $usbPath 'AccesoUSB-0.3.apk'
 if(Test-Path -LiteralPath $old){
  if((Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash.ToLowerInvariant() -ne '6cba89eeae7cbd97a03360f1eba91ad689b513ab38981353839824cfa1f71877'){throw 'La APK previa cambio; se conserva sin renombrar'}
  $retired=Join-Path $usbPath 'AccesoUSB-0.3.apk.no-usar'
  if(Test-Path -LiteralPath $retired){throw 'Ya existe copia retirada; no sobrescribir'}
  Move-Item -LiteralPath $old -Destination $retired
 }
 $oldReadme=Join-Path $usbPath 'LEEME-0.1.1.txt'
 if(Test-Path -LiteralPath $oldReadme){
  if((Get-FileHash -LiteralPath $oldReadme -Algorithm SHA256).Hash.ToLowerInvariant() -eq '47e9bca4669d827099374718f8fd1dc81fba3eb19a315beb2cf4bff40bebbc68'){
   $retired=Join-Path $usbPath 'LEEME-ENTRADA-ANTERIOR.txt';if(-not(Test-Path -LiteralPath $retired)){Move-Item -LiteralPath $oldReadme -Destination $retired}
  }
 }
 $state.files=$written;$state.volume=$usbPath;$state.drive_letter=$current.volume.DriveLetter
 Save-State 'verificado' 'APK 0.4 y recovery USB listos y leidos. ROM 0.1.1 conservada. Prueba fisica pendiente.'
 exit 0
}catch{Save-State 'fallo' ($_.Exception.ToString());$_|Out-String|Set-Content -LiteralPath (Join-Path $runDir 'error.txt') -Encoding UTF8;exit 1}
