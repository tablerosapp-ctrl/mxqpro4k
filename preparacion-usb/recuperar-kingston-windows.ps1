# Restauracion del Kingston vaciado y autorizado por el usuario. No graba Armbian.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$expectedId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$expectedSize = [long]30943995904
$runDir = Join-Path $PSScriptRoot ('recuperacion-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$null = New-Item -ItemType Directory -Path $runDir
$statePath = Join-Path $PSScriptRoot 'estado-recuperacion.json'
$state = [ordered]@{estado='comprobando'; inicio=(Get-Date).ToString('o'); destino_id=$expectedId; informe=$runDir; proceso=$PID}
function Save-State([string]$phase, [string]$detail) {
    $state.estado=$phase; $state.detalle=$detail; $state.fecha=(Get-Date).ToString('o')
    $json=$state | ConvertTo-Json -Depth 6
    $json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $json | Set-Content -LiteralPath (Join-Path $runDir 'resultado.json') -Encoding UTF8
}
function Get-Target {
    $matches=@(Get-Disk | Where-Object UniqueId -eq $expectedId)
    if($matches.Count -ne 1){throw 'No hay un unico Kingston con la identidad prevista.'}
    $disk=$matches[0]
    if($disk.Size -ne $expectedSize -or $disk.BusType -ne 'USB' -or
       $disk.FriendlyName -ne 'Kingston DataTraveler 3.0' -or
       $disk.IsSystem -or $disk.IsBoot -or $disk.IsReadOnly -or $disk.IsOffline){
        throw 'El disco no cumple las condiciones del Kingston autorizado.'
    }
    return $disk
}
try {
    Save-State 'comprobando' 'Comprobando el Kingston y su contenido antes de restaurarlo.'
    $principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Se necesitan permisos de administrador de Windows.'}
    if(@(Get-Process -Name 'rpi-imager','rufus*','diskpart','robocopy' -ErrorAction SilentlyContinue).Count){throw 'Otra herramienta de disco esta activa.'}
    $disk=Get-Target
    $parts=@(Get-Partition -DiskNumber $disk.Number)
    $volumes=@($parts | Get-Volume -ErrorAction SilentlyContinue)
    foreach($volume in $volumes){
        if($volume.FileSystem -and $volume.Size -gt 0){
            # Si hay un sistema reconocible, un error al listar tambien detiene la restauracion.
            $files=@([IO.Directory]::GetFileSystemEntries($volume.Path) | Where-Object {
                [IO.Path]::GetFileName($_) -notin @('System Volume Information','$RECYCLE.BIN')
            })
            if($files.Count){throw 'Hay archivos en el USB; se detiene para no borrar contenido nuevo.'}
        }
    }
    [ordered]@{disco=($disk | Select-Object Number,UniqueId,FriendlyName,Size,PartitionStyle,IsSystem,IsBoot);
        particiones=($parts | Select-Object DiskNumber,PartitionNumber,Offset,Size,DriveLetter,Type);
        volumenes=($volumes | Select-Object FileSystem,FileSystemLabel,Size,SizeRemaining,Path)
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDir 'antes.json') -Encoding UTF8
    $physicalPath='\\.\PhysicalDrive' + $disk.Number
    $header=New-Object byte[] 4096
    $stream=[IO.File]::Open($physicalPath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
    try {if($stream.Read($header,0,$header.Length) -ne $header.Length){throw 'No se pudo leer la cabecera completa.'}} finally {$stream.Dispose()}
    [IO.File]::WriteAllBytes((Join-Path $runDir 'cabecera-antes.bin'),$header)
    $check=Get-Target
    if($check.Number -ne $disk.Number){throw 'El disco cambio durante la comprobacion.'}
    $assign=if(Get-Volume -DriveLetter E -ErrorAction SilentlyContinue){'assign'}else{'assign letter=E'}
    # clean borra la estructura; NO se utiliza clean all ni se escribe toda la memoria.
    $commands=@(('select disk ' + $disk.Number),'clean','create partition primary','format fs=exfat quick label=KINGSTON',$assign,'exit')
    $scriptPath=Join-Path $runDir 'restaurar.txt'
    [IO.File]::WriteAllLines($scriptPath,$commands,[Text.Encoding]::ASCII)
    $state.disco=$disk.Number
    Save-State 'restaurando' 'Recreando una particion exFAT de capacidad completa con la herramienta de Windows.'
    $psi=New-Object Diagnostics.ProcessStartInfo
    $psi.FileName=Join-Path $env:WINDIR 'System32\diskpart.exe'
    $psi.Arguments='/s "' + $scriptPath + '"'
    $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $process=New-Object Diagnostics.Process
    $process.StartInfo=$psi
    if(-not $process.Start()){throw 'No se pudo iniciar la herramienta de Windows.'}
    $outTask=$process.StandardOutput.ReadToEndAsync(); $errTask=$process.StandardError.ReadToEndAsync()
    $state.proceso_diskpart=$process.Id
    Save-State 'restaurando' 'Windows esta restaurando el volumen del Kingston.'
    $process.WaitForExit()
    $outTask.GetAwaiter().GetResult() | Set-Content -LiteralPath (Join-Path $runDir 'diskpart.log') -Encoding UTF8
    $errTask.GetAwaiter().GetResult() | Set-Content -LiteralPath (Join-Path $runDir 'diskpart-error.log') -Encoding UTF8
    $state.codigo_salida=$process.ExitCode
    if($process.ExitCode -ne 0){throw ('Windows no pudo restaurar el volumen. Codigo: ' + $process.ExitCode)}
    Update-HostStorageCache
    $disk=Get-Target
    $parts=@(Get-Partition -DiskNumber $disk.Number)
    if($parts.Count -ne 1 -or [string]$parts[0].DriveLetter -notmatch '^[A-Za-z]$'){throw 'No quedo una unica particion con letra.'}
    $volume=$parts[0] | Get-Volume
    if($volume.FileSystem -ne 'exFAT' -or $volume.Size -lt ($expectedSize - 64MB)){throw 'El formato o la capacidad final no coinciden con lo esperado.'}
    $root=[string]$parts[0].DriveLetter + ':\'
    $state.letra=$root; $state.capacidad=$volume.Size; $state.formato=$volume.FileSystem
    Save-State 'verificando' 'Comprobando una escritura pequena y su lectura en el volumen restaurado.'
    $testPath=Join-Path $root ('verificacion-' + [guid]::NewGuid().ToString('N') + '.tmp')
    $sample=New-Object byte[] (1MB)
    $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
    try {$rng.GetBytes($sample)} finally {$rng.Dispose()}
    $sha=[Security.Cryptography.SHA256]::Create()
    try {$expected=[BitConverter]::ToString($sha.ComputeHash($sample)).Replace('-','')} finally {$sha.Dispose()}
    $file=New-Object IO.FileStream($testPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None,65536,[IO.FileOptions]::WriteThrough)
    try {$file.Write($sample,0,$sample.Length); $file.Flush($true)} finally {$file.Dispose()}
    $actual=(Get-FileHash -LiteralPath $testPath -Algorithm SHA256).Hash
    if($actual -ne $expected){throw 'La lectura de verificacion no coincide con la escritura.'}
    Remove-Item -LiteralPath $testPath
    $state.verificacion_bytes=1MB
    Save-State 'recuperado' ('Kingston disponible en ' + $root + ' con exFAT; verificacion basica de 1 MiB correcta. No acredita toda la capacidad ni una grabacion de imagen.')
} catch {
    $state.error_tipo=$_.Exception.GetType().FullName
    $state.error_hresult=$_.Exception.HResult
    Save-State 'error' $_.Exception.Message
    exit 1
}
