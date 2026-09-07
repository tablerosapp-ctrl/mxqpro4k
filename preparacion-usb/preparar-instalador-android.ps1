# Prepares the specifically authorized Kingston for the real recovery ROM.
# Run elevated. No TV connection, no flashing on the PC, no blind retry.
[CmdletBinding()]param()
$ErrorActionPreference='Stop'
throw 'Preparador 0.1 retirado: la revision 0.1.1 desactiva el reemplazo heredado del recovery. El Kingston ya esta preparado; actualizar solo los archivos y conservar TVBASE-respaldo-*.'
$root=Split-Path $PSScriptRoot -Parent
$expectedId='USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$expectedSize=[long]30943995904
$runDir=Join-Path $PSScriptRoot ('instalador-android-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $runDir | Out-Null
$state=[ordered]@{estado='comprobando';inicio=(Get-Date).ToString('o');usb_id=$expectedId;informe=$runDir;tv_flasheado=$false}
function Save-State([string]$phase,[string]$detail){$state.estado=$phase;$state.detalle=$detail;$state.fecha=(Get-Date).ToString('o');$j=$state|ConvertTo-Json -Depth 8;$j|Set-Content -LiteralPath (Join-Path $runDir 'resultado.json') -Encoding UTF8;$j|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'instalador-android-estado.json') -Encoding UTF8}
function Get-Target {
 $matches=@(Get-Disk|Where-Object UniqueId -eq $expectedId)
 if($matches.Count -ne 1){throw 'No hay un unico Kingston identificado'}
 $d=$matches[0]
 if($d.Size -ne $expectedSize -or $d.FriendlyName -ne 'Kingston DataTraveler 3.0' -or $d.BusType -ne 'USB' -or $d.IsBoot -or $d.IsSystem -or $d.IsOffline -or $d.IsReadOnly){throw 'Identidad o estado de disco no permitido'}
 return $d
}
try {
 Save-State 'comprobando' 'Validando los archivos finales y el Kingston autorizado.'
 $principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
 if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Requiere elevacion de Windows'}
 $romReport=Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/salida/RECOVERY-VERIFICACION.json')|ConvertFrom-Json
 $apkReport=@(Get-Content -Raw -LiteralPath (Join-Path $root 'rom-simplificada/compilacion/acceso-usb-componente.json')|ConvertFrom-Json)[0]
 if(-not $romReport.whole_file_signature_verified -or -not $romReport.payload_sha256_verified){throw 'ROM sin verificar'}
 if(-not (Test-Path -LiteralPath (Join-Path $root 'rom-simplificada/instalador/FIRMA-OPENJDK-OK.txt'))){throw 'Falta verificacion independiente de firma'}
 $rom=Join-Path $root $romReport.file;$apk=Join-Path $root $apkReport.path
 foreach($pair in @(@($rom,$romReport.sha256),@($apk,$apkReport.sha256))){if((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]){throw 'Cambio un archivo de instalacion'}}
 if(@(Get-Process -Name 'rpi-imager','diskpart','rufus*' -ErrorAction SilentlyContinue).Count){throw 'Hay otra herramienta de disco activa'}
 $d=Get-Target;$parts=@($d|Get-Partition|Sort-Object Offset)
 if($parts.Count -ne 2 -or $parts[0].Offset -ne 4194304 -or $parts[0].Size -ne 535822336 -or $parts[1].Offset -ne 541065216 -or $parts[1].Size -ne 3145728000){throw 'Estructura USB distinta de la Armbian conocida; revisar antes de escribir'}
 $boot=$parts[0]|Get-Volume
 if($boot.FileSystem -ne 'FAT32' -or $boot.FileSystemLabel -ne 'BOOT'){throw 'Volumen BOOT distinto del previsto'}
 $inventory=@(Get-ChildItem -LiteralPath $boot.Path -Force -Recurse|Select-Object FullName,Length,Attributes)
 $inventory|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $runDir 'archivos-antes.json') -Encoding UTF8
 [ordered]@{disk=($d|Select-Object Number,UniqueId,FriendlyName,Size,IsBoot,IsSystem);partitions=($parts|Select-Object PartitionNumber,Offset,Size,DriveLetter)}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $runDir 'antes.json') -Encoding UTF8
 # Preserve every byte up to the end of the last existing partition before replacing this layout.
 $end=[long]($parts[-1].Offset+$parts[-1].Size);$physical='\\.\PhysicalDrive'+$d.Number
 Save-State 'respaldando_usb' 'Guardando los 3,69 GB ocupados de la preparacion anterior en la PC.'
 $src=[IO.File]::Open($physical,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
 $backup=Join-Path $runDir 'usb-antes.img';$dst=[IO.File]::Open($backup,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 $hash=[Security.Cryptography.SHA256]::Create();$buffer=New-Object byte[] (4MB);$left=$end
 try {while($left -gt 0){$n=$src.Read($buffer,0,[int][Math]::Min($left,$buffer.Length));if($n -le 0){throw 'Lectura incompleta del USB'};$dst.Write($buffer,0,$n);$null=$hash.TransformBlock($buffer,0,$n,$buffer,0);$left-=$n};$null=$hash.TransformFinalBlock([byte[]]@(),0,0);$dst.Flush($true)}finally{$src.Dispose();$dst.Dispose()}
 $backupHash=([BitConverter]::ToString($hash.Hash)).Replace('-','').ToLowerInvariant();$hash.Dispose()
 if((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $backupHash){throw 'Respaldo USB no verificado'}
 $state.respaldo_usb=$backup;$state.respaldo_bytes=$end;$state.respaldo_sha256=$backupHash
 $check=Get-Target;if($check.Number -ne $d.Number){throw 'El disco cambio durante el respaldo'}
 Save-State 'preparando_fat32' 'Reemplazando Armbian por un volumen FAT32 para el instalador Android.'
 Clear-Disk -InputObject $check -RemoveData -RemoveOEM -Confirm:$false
 $fresh=Get-Target
 if($fresh.PartitionStyle -eq 'RAW'){Initialize-Disk -Number $fresh.Number -PartitionStyle MBR | Out-Null}
 $fresh=Get-Target
 $part=New-Partition -DiskNumber $fresh.Number -UseMaximumSize -AssignDriveLetter
 $vol=$part|Format-Volume -FileSystem FAT32 -NewFileSystemLabel TVBASE -AllocationUnitSize 16384 -Force -Confirm:$false
 $target=($part|Get-Volume).Path
 if(-not $target){throw 'No se obtuvo ruta del volumen nuevo'}
 Save-State 'copiando' 'Copiando ROM real y acceso directo al recovery.'
 $files=@(@{source=$rom;name='TVBASE-P291-A9-0.1-RECOVERY.zip';hash=$romReport.sha256},@{source=$apk;name='AccesoUSB.apk';hash=$apkReport.sha256},@{source=(Join-Path $root 'rom-simplificada/instalador/LEEME-USB.txt');name='LEEME.txt';hash=$null})
 $written=@()
 foreach($item in $files){
  $current=Get-Target;if($current.Number -ne $fresh.Number){throw 'Cambio el USB durante la copia'}
  $to=Join-Path $target $item.name;$a=[IO.File]::OpenRead($item.source);$b=[IO.File]::Open($to,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$a.CopyTo($b,524288);$b.Flush($true)}finally{$a.Dispose();$b.Dispose()}
  $actual=(Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant();$expected=$item.hash;if(-not $expected){$expected=(Get-FileHash -LiteralPath $item.source -Algorithm SHA256).Hash.ToLowerInvariant()}
  if($actual -ne $expected){throw ('Lectura distinta del origen: '+$item.name)}
  $written+=@{archivo=$item.name;bytes=(Get-Item -LiteralPath $to).Length;sha256=$actual;lectura_verificada=$true}
 }
 $marker=Join-Path $target 'TVBASE-MEDIA.txt';$markerBytes=[Text.Encoding]::ASCII.GetBytes("TVBASE-P291-20260906-4dc82786`n");$m=[IO.File]::Open($marker,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$m.Write($markerBytes,0,$markerBytes.Length);$m.Flush($true)}finally{$m.Dispose()}
 if([IO.File]::ReadAllText($marker).Trim() -ne 'TVBASE-P291-20260906-4dc82786'){throw 'Marcador USB incorrecto'}
 $final=Get-Target;$state.files=$written;$state.volume=$target;$state.drive_letter=($part|Get-Volume).DriveLetter;$state.label='TVBASE';$state.capacity=$expectedSize
 Save-State 'verificado' 'Instalador Android completo copiado y verificado. Aun no instalado en el TV.'
 exit 0
}catch{Save-State 'fallo' ($_.Exception.ToString());$_|Out-String|Set-Content -LiteralPath (Join-Path $runDir 'error.txt') -Encoding UTF8;exit 1}
