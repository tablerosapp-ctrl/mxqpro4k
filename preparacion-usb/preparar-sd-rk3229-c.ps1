param(
    [switch]$Prepare,
    [switch]$CheckOnly
)

# SD concreta autorizada para borrar. No usa letras fijas ni ejecuta herramientas Rockchip.
# Sin argumentos: SOLO comprobacion. No reanuda preparaciones ni reutiliza recibos.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($Prepare -and $CheckOnly) { throw 'Elegir -Prepare o -CheckOnly, no ambos.' }

function New-SDSettings([string]$root) {
    return [pscustomobject]@{
        Root = [IO.Path]::GetFullPath($root).TrimEnd('\','/')
        UniqueId = 'USBSTOR\DISK&VEN_MASS&PROD_STORAGE_DEVICE&REV__\LECTOR-SD-LOCAL&0:PC_LOCAL'
        FriendlyName = 'Mass Storage Device'
        SerialNumber = 'LECTOR-SD-LOCAL'
        Size = [long]8053063680
        PrefixBytes = [long]100663296
        OriginalPartitionBytes = [long]7952400384
        NewOffset = [long]1048576
        FirmwareRelative = 'Rockchip Create Upgrade Disk Tool v1.53/D-RK3228-ssv6256-CNV8b-11.1-1G8-0725_21.img'
        FirmwareBytes = [long]907946456
        FirmwareSHA256 = '8728cf503b79f22000110c41a1d7b1f3b10a975bc15e8256461f6ef72285c89e'
        Label = 'TVBASESD'
    }
}

function Assert-NoReparse([string]$path, [bool]$directory = $false) {
    $current = [IO.Path]::GetFullPath($path)
    $first = $true
    while (-not [string]::IsNullOrEmpty($current)) {
        $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Ruta con reparse point.' }
        if ($first -and -not $directory) {
            if ($item.PSIsContainer) { throw 'Se esperaba archivo ordinario.' }
        } elseif (-not $item.PSIsContainer) { throw 'Se esperaba directorio ordinario.' }
        $first = $false
        $next = [IO.Path]::GetDirectoryName($current.TrimEnd('\'))
        if ([string]::IsNullOrEmpty($next) -or $next -eq $current) { break }
        if ($next -match '^[A-Za-z]:$') { $next += '\' }
        if ($next -eq $current) { break }
        $current = $next
    }
}

function Assert-ProjectPath([string]$path) {
    $full = [IO.Path]::GetFullPath($path)
    if (-not $full.StartsWith($taskConfig.Root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera del proyecto.' }
    return $full
}

function Hash-Ordinary([string]$path) {
    Assert-NoReparse $path
    $before = Get-Item -LiteralPath $path -Force
    $size = [long]$before.Length
    $ticks = $before.LastWriteTimeUtc.Ticks
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    $after = Get-Item -LiteralPath $path -Force
    if ($after.Length -ne $size -or $after.LastWriteTimeUtc.Ticks -ne $ticks -or
        ($after.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $hash -cnotmatch '^[0-9a-f]{64}$') { throw 'Archivo cambio durante su lectura.' }
    return $hash
}

function Hash-Text([string]$value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($value)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Check-PCFirmware {
    $path = Assert-ProjectPath (Join-Path $taskConfig.Root $taskConfig.FirmwareRelative)
    Assert-NoReparse $path
    if ((Get-Item -LiteralPath $path).Length -ne $taskConfig.FirmwareBytes -or
        (Hash-Ordinary $path) -cne $taskConfig.FirmwareSHA256) { throw 'La imagen original en PC no coincide.' }
    return $path
}

function Assert-SDIdentity($disk) {
    if ($null -eq $disk -or $disk.UniqueId -cne $taskConfig.UniqueId -or
        $disk.FriendlyName -cne $taskConfig.FriendlyName -or
        ([string]$disk.SerialNumber).Trim() -cne $taskConfig.SerialNumber -or
        [long]$disk.Size -ne $taskConfig.Size -or [string]$disk.BusType -cne 'USB' -or
        $disk.IsSystem -ne $false -or $disk.IsBoot -ne $false -or
        $disk.IsOffline -ne $false -or $disk.IsReadOnly -ne $false -or
        [long]$disk.LogicalSectorSize -ne 512 -or
        [long]$disk.PhysicalSectorSize -lt 512 -or ([long]$disk.PhysicalSectorSize % 512) -ne 0 -or
        [long]$disk.Number -lt 0 -or [long]$disk.Number -gt [int]::MaxValue) { throw 'No coincide la SD fisica autorizada y escribible.' }
}

function Assert-SDLayout($disk, [object[]]$parts, [string]$stage) {
    Assert-SDIdentity $disk
    foreach ($part in $parts) {
        if ([long]$part.DiskNumber -ne [long]$disk.Number -or $part.IsSystem -ne $false -or $part.IsBoot -ne $false) { throw 'Particion ajena o protegida.' }
    }
    if ($stage -eq 'Original') {
        if ([string]$disk.PartitionStyle -cne 'MBR' -or $parts.Count -ne 1 -or
            [long]$parts[0].PartitionNumber -ne 1 -or [long]$parts[0].Offset -ne $taskConfig.PrefixBytes -or
            [long]$parts[0].Size -ne $taskConfig.OriginalPartitionBytes) { throw 'Geometria original de la SD distinta.' }
    } elseif ($stage -eq 'Cleared') {
        if ([string]$disk.PartitionStyle -cne 'RAW' -or $parts.Count -ne 0) { throw 'La SD no esta RAW y sin particiones.' }
    } elseif ($stage -eq 'Initialized') {
        if ([string]$disk.PartitionStyle -cne 'MBR' -or $parts.Count -ne 0) { throw 'La SD no esta MBR vacia.' }
    } elseif ($stage -in @('Partitioned','Final')) {
        if ([string]$disk.PartitionStyle -cne 'MBR' -or $parts.Count -ne 1) { throw 'No hay una sola particion nueva.' }
        $part = $parts[0]
        $end = [long]$part.Offset + [long]$part.Size
        if ([long]$part.PartitionNumber -ne 1 -or [long]$part.Offset -ne $taskConfig.NewOffset -or
            [long]$part.Size -le $taskConfig.OriginalPartitionBytes -or $end -gt $taskConfig.Size -or
            ($taskConfig.Size-$end) -gt 2MB -or ([long]$part.Size % 512) -ne 0) { throw 'Geometria nueva no corresponde al maximo de la SD.' }
    } else { throw 'Etapa de comprobacion desconocida.' }
}

function Get-CheckedSD([string]$stage) {
    # Consulta exclusivamente la identidad fijada; ninguna seleccion por D:, E: o numero recordado.
    $disks = @(Get-Disk -UniqueId $taskConfig.UniqueId -ErrorAction Stop)
    if ($disks.Count -ne 1) { throw 'SD ausente o identidad ambigua.' }
    $disk = $disks[0]
    Assert-SDIdentity $disk
    if ($null -ne $taskInitialNumber -and [long]$disk.Number -ne $taskInitialNumber) { throw 'Cambio el numero fisico de la SD durante esta ejecucion.' }
    # Enumeracion CIM permite distinguir cero particiones de un fallo de Get-Partition.
    $parts = @(Get-CimInstance -Namespace 'root/Microsoft/Windows/Storage' -ClassName MSFT_Partition `
        -Filter ('DiskNumber = '+[int]$disk.Number) -ErrorAction Stop)
    Assert-SDLayout $disk $parts $stage
    $part = $null
    $volume = $null
    $mount = $null
    if ($parts.Count -eq 1) {
        $actualParts = @(Get-Partition -DiskNumber ([int]$disk.Number) -PartitionNumber 1 -ErrorAction Stop)
        if ($actualParts.Count -ne 1) { throw 'Particion no resoluble de forma unica.' }
        $part = $actualParts[0]
        Assert-SDLayout $disk @($part) $stage
        if ($stage -in @('Original','Final')) {
            if ([string]$part.DriveLetter -cnotmatch '^[A-Z]$') { throw 'La SD no tiene un punto de montaje unico por letra.' }
            $volumes = @(Get-Volume -Partition $part -ErrorAction Stop)
            if ($volumes.Count -ne 1 -or [string]$volumes[0].FileSystem -cne 'FAT32') { throw 'Volumen FAT32 no resuelto.' }
            $volume = $volumes[0]
            $expectedLabel = ''
            if ($stage -eq 'Final') { $expectedLabel = $taskConfig.Label }
            if ([string]$volume.FileSystemLabel -cne $expectedLabel -or
                [long]$volume.Size -le 0 -or [long]$volume.Size -gt [long]$part.Size) { throw 'Etiqueta o tamano del volumen distintos.' }
            $mount = ([string]$part.DriveLetter)+':\'
            Assert-NoReparse $mount $true
        }
    }
    return [pscustomobject]@{ Disk=$disk; Partition=$part; Volume=$volume; Mount=$mount; Stage=$stage }
}

function Get-SDRecord($checked) {
    $disk = $checked.Disk
    $record = [ordered]@{
        unique_id=[string]$disk.UniqueId; serial=([string]$disk.SerialNumber).Trim(); friendly_name=[string]$disk.FriendlyName
        number=[int]$disk.Number; bytes=[long]$disk.Size; bus=[string]$disk.BusType
        logical_sector_bytes=[long]$disk.LogicalSectorSize; physical_sector_bytes=[long]$disk.PhysicalSectorSize
        partition_style=[string]$disk.PartitionStyle; is_system=[bool]$disk.IsSystem; is_boot=[bool]$disk.IsBoot
    }
    if ($null -ne $checked.Partition) {
        $record.partition = [ordered]@{ number=[int]$checked.Partition.PartitionNumber; offset=[long]$checked.Partition.Offset; bytes=[long]$checked.Partition.Size }
    }
    if ($null -ne $checked.Volume) {
        $record.volume = [ordered]@{ mount=$checked.Mount; filesystem=[string]$checked.Volume.FileSystem; label=[string]$checked.Volume.FileSystemLabel; bytes=[long]$checked.Volume.Size }
    }
    return $record
}

function Get-RootSnapshot([string]$mount, [bool]$emptyExpected = $false) {
    Assert-NoReparse $mount $true
    $entries = @(Get-ChildItem -LiteralPath $mount -Force -ErrorAction Stop)
    $files = @()
    $systemDirectoryPresent = $false
    foreach ($item in $entries) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Enlace inesperado en la SD.' }
        if ($item.Name -ieq 'System Volume Information') {
            if (-not $item.PSIsContainer) { throw 'System Volume Information no es un directorio.' }
            # Metadatos de Windows permitidos; no se recorre ni se afirma haberlos respaldado.
            $systemDirectoryPresent = $true
            continue
        }
        if ($emptyExpected -or $item.PSIsContainer -or $item.Name -inotmatch '^(sdupdate\.img|rksdfw\.tag|sd_boot_config\.config)$') { throw 'Contenido inesperado en la raiz de la SD.' }
        if ($item.Name -ieq 'sdupdate.img') {
            if ([long]$item.Length -ne $taskConfig.FirmwareBytes) { throw 'Tamano de sdupdate.img distinto.' }
        } elseif ([long]$item.Length -gt 1MB) { throw 'Configuracion o etiqueta demasiado grande.' }
        $hash = Hash-Ordinary $item.FullName
        if ($item.Name -ieq 'sdupdate.img' -and $hash -cne $taskConfig.FirmwareSHA256) { throw 'La imagen SD no es identica a la imagen preservada en PC.' }
        $files += [pscustomobject]@{ name=$item.Name.ToLowerInvariant(); bytes=[long]$item.Length; sha256=$hash; modified_utc=$item.LastWriteTimeUtc.ToString('o') }
    }
    if (-not $emptyExpected -and ($files.Count -ne 3 -or @($files.name | Sort-Object -Unique).Count -ne 3)) { throw 'Falta imagen, etiqueta o configuracion original.' }
    return [pscustomobject]@{ files=@($files | Sort-Object name); system_volume_information_present=$systemDirectoryPresent; system_volume_information_contents_inspected=$false }
}

function Assert-SameSnapshot($a, $b) {
    if (($a.files | ConvertTo-Json -Depth 5 -Compress) -cne ($b.files | ConvertTo-Json -Depth 5 -Compress)) { throw 'Archivos originales cambiaron antes de borrar.' }
}

function Write-NewBytes([string]$path, [byte[]]$bytes) {
    $full = Assert-ProjectPath $path
    Assert-NoReparse ([IO.Path]::GetDirectoryName($full)) $true
    $stream = New-Object IO.FileStream($full,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}

function Copy-SmallFile([string]$source, [string]$destination, $expected) {
    Assert-NoReparse $source
    if ([long](Get-Item -LiteralPath $source).Length -ne [long]$expected.bytes -or (Hash-Ordinary $source) -cne $expected.sha256) { throw 'Auxiliar SD cambio antes de copiar.' }
    $bytes = [IO.File]::ReadAllBytes($source)
    Write-NewBytes $destination $bytes
    if ([long](Get-Item -LiteralPath $destination).Length -ne [long]$expected.bytes -or
        (Hash-Ordinary $destination) -cne $expected.sha256 -or (Hash-Ordinary $source) -cne $expected.sha256) { throw 'Copia auxiliar no verificada.' }
    return [ordered]@{ source_name=$expected.name; copy_path=$destination; bytes=[long]$expected.bytes; sha256=$expected.sha256; flush_file_verified=$true; reread_verified=$true }
}

function Ensure-SDRawType {
    if ('TVBase.SDPreparationRawV1' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using Microsoft.Win32.SafeHandles;
namespace TVBase {
    public sealed class SDPrefixResult {
        public long Bytes;
        public string SHA256;
        public bool SourceRereadVerified;
        public bool FileRereadVerified;
        public bool FlushFileVerified;
    }
    public static class SDPreparationRawV1 {
        const int Chunk = 1024 * 1024;
        [DllImport("kernel32.dll", SetLastError=true)]
        static extern bool DeviceIoControl(SafeFileHandle h, uint code, byte[] input, int inSize,
            byte[] output, int outSize, out int returned, IntPtr overlapped);
        static byte[] Query(FileStream stream, uint code, byte[] input, int outputLength, int minimum) {
            byte[] output = new byte[outputLength]; int returned;
            if (!DeviceIoControl(stream.SafeFileHandle,code,input,input==null?0:input.Length,
                output,output.Length,out returned,IntPtr.Zero))
                throw new IOException("No se pudo identificar el handle fisico.",new Win32Exception(Marshal.GetLastWin32Error()));
            if (returned < minimum || returned > output.Length) throw new IOException("Descriptor fisico incompleto.");
            Array.Resize(ref output,returned); return output;
        }
        public static void AssertDevice(FileStream stream, int number, long size, string serial) {
            byte[] dev = Query(stream,0x002D1080,null,12,12);
            if (BitConverter.ToUInt32(dev,0)!=7 || BitConverter.ToUInt32(dev,4)!=(uint)number)
                throw new IOException("El handle no pertenece al disco seleccionado.");
            byte[] len = Query(stream,0x0007405C,null,8,8);
            if (BitConverter.ToInt64(len,0)!=size) throw new IOException("Longitud fisica distinta.");
            byte[] desc = Query(stream,0x002D1400,new byte[12],4096,36);
            uint declared = BitConverter.ToUInt32(desc,4);
            uint serialOffset = BitConverter.ToUInt32(desc,24);
            if (declared > desc.Length || declared < 36 || serialOffset < 36 || serialOffset >= declared ||
                BitConverter.ToUInt32(desc,28)!=7) throw new IOException("Identidad USB del handle no disponible.");
            int end=(int)serialOffset;
            while (end < declared && desc[end]!=0) end++;
            if (end==declared || Encoding.ASCII.GetString(desc,(int)serialOffset,end-(int)serialOffset).Trim()!=serial)
                throw new IOException("Numero de serie fisico distinto o no verificable.");
        }
        static void ValidateLength(long length) {
            if (length<=0 || length%Chunk!=0 || length>96L*Chunk) throw new IOException("Prefijo fuera del limite de 96 MiB o sin alineacion.");
        }
        static void ReadChunk(Stream stream, byte[] buffer) {
            // Cada peticion es de 1 MiB; no se reintentan lecturas cortas con offsets sin alineacion.
            if (stream.Read(buffer,0,buffer.Length)!=buffer.Length) throw new EndOfStreamException("Lectura corta del prefijo.");
        }
        static string FinishHash(SHA256 sha) {
            sha.TransformFinalBlock(new byte[0],0,0);
            return BitConverter.ToString(sha.Hash).Replace("-","").ToLowerInvariant();
        }
        public static string HashPrefix(Stream stream, long length, bool requireZero) {
            ValidateLength(length); stream.Position=0; byte[] buffer=new byte[Chunk];
            using (SHA256 sha=SHA256.Create()) {
                for (long offset=0;offset<length;offset+=Chunk) {
                    ReadChunk(stream,buffer);
                    if (requireZero) for (int n=0;n<buffer.Length;n++)
                        if (buffer[n]!=0) throw new IOException("El prefijo releido no contiene solo ceros.");
                    sha.TransformBlock(buffer,0,buffer.Length,buffer,0);
                }
                return FinishHash(sha);
            }
        }
        // Primitivas acotadas tambien probadas con archivos regulares: no abren dispositivos por si mismas.
        public static SDPrefixResult BackupPrefix(Stream source, string destination, long length) {
            ValidateLength(length); source.Position=0; byte[] buffer=new byte[Chunk]; string hash;
            using (FileStream target=new FileStream(destination,FileMode.CreateNew,FileAccess.Write,FileShare.None,Chunk,FileOptions.WriteThrough)) {
                using (SHA256 sha=SHA256.Create()) {
                    for (long offset=0;offset<length;offset+=Chunk) {
                        ReadChunk(source,buffer); target.Write(buffer,0,buffer.Length);
                        sha.TransformBlock(buffer,0,buffer.Length,buffer,0);
                    }
                    hash=FinishHash(sha);
                }
                target.Flush(true);
            }
            using (FileStream copy=new FileStream(destination,FileMode.Open,FileAccess.Read,FileShare.Read)) {
                if (copy.Length!=length || HashPrefix(copy,length,false)!=hash) throw new IOException("Relectura del respaldo PC distinta.");
            }
            if (HashPrefix(source,length,false)!=hash) throw new IOException("El prefijo SD cambio durante el respaldo.");
            return new SDPrefixResult { Bytes=length,SHA256=hash,SourceRereadVerified=true,FileRereadVerified=true,FlushFileVerified=true };
        }
        public static string ZeroPrefix(FileStream target, long length) {
            ValidateLength(length); target.Position=0; byte[] buffer=new byte[Chunk];
            for (long offset=0;offset<length;offset+=Chunk) target.Write(buffer,0,buffer.Length);
            target.Flush(true);
            return HashPrefix(target,length,true);
        }
    }
}
'@ -ErrorAction Stop
}

function Open-CheckedRaw([string]$stage, [bool]$writeAccess) {
    if ($writeAccess -and $stage -cne 'Cleared') { throw 'Escritura raw permitida solo sin particiones y despues del respaldo.' }
    $checked = Get-CheckedSD $stage
    $path = '\\.\PhysicalDrive'+[int]$checked.Disk.Number
    $access = [IO.FileAccess]::Read
    $options = [IO.FileOptions]::SequentialScan
    if ($writeAccess) { $access = [IO.FileAccess]::ReadWrite; $options = [IO.FileOptions]::WriteThrough }
    $stream = New-Object IO.FileStream($path,[IO.FileMode]::Open,$access,[IO.FileShare]::ReadWrite,1048576,$options)
    try {
        [TVBase.SDPreparationRawV1]::AssertDevice($stream,[int]$checked.Disk.Number,$taskConfig.Size,$taskConfig.SerialNumber)
        $again = Get-CheckedSD $stage
        if ([int]$again.Disk.Number -ne [int]$checked.Disk.Number) { throw 'Cambio el dispositivo al abrirlo.' }
        return $stream
    } catch { $stream.Dispose(); throw }
}

function Assert-ScriptUnchanged {
    if ((Hash-Ordinary $taskScriptPath) -cne $taskScriptHash) { throw 'Cambio el script durante la preparacion.' }
}

function Save-SDCheckpoint([string]$phase, [string]$state) {
    if ($phase -cnotmatch '^[a-z0-9_]+$') { throw 'Nombre de fase invalido.' }
    $taskState.phase = $phase
    $taskState.state = $state
    $taskState.updated_utc = [DateTime]::UtcNow.ToString('o')
    $script:taskCheckpointNumber++
    $receipt = Join-Path $taskPrivate ('{0:D2}-{1}.json' -f $taskCheckpointNumber,$phase)
    $json = ($taskState | ConvertTo-Json -Depth 30)+"`n"
    Write-NewBytes $receipt ([Text.UTF8Encoding]::new($false).GetBytes($json))
    $public = [ordered]@{
        schema='tvbase-sd-normal-preparation-1'; state=$state; phase=$phase
        updated_utc=$taskState.updated_utc; target='SD RK3229-C autorizada'; disk_bytes=$taskConfig.Size
        disk_identity_sha256=$taskIdentityHash; script_sha256=$taskScriptHash
        firmware_preserved_pc_sha256=$taskConfig.FirmwareSHA256; firmware_bytes=$taskConfig.FirmwareBytes
        prefix_backup_bytes=$taskConfig.PrefixBytes; prefix_backup_verified=[bool]$taskState.prefix_backup_verified
        prefix_zero_verified_before_new_layout=[bool]$taskState.prefix_zero_verified_before_new_layout
        sd_mutation_attempted=[bool]$taskState.sd_mutation_attempted; normal_fat32_verified=[bool]$taskState.normal_fat32_verified
        final_label=$taskConfig.Label; extractor_copied=$false; tv_contacted=$false; kingston_modified=$false
        full_disk_backup=$false; raw_zero_limited_bytes=$taskConfig.PrefixBytes; full_format=$false
        private_checkpoint_sha256=(Hash-Ordinary $receipt)
        safe_removal_pending=$true; windows_volume_flush_verified=$false
    }
    if ($taskState.prefix_backup_verified) { $public.prefix_backup_sha256=$taskState.prefix_backup.sha256 }
    $payload = [Text.UTF8Encoding]::new($false).GetBytes(($public | ConvertTo-Json -Depth 8)+"`n")
    # Handle CreateNew retenido desde la reserva: solo se actualiza nuestro propio recibo.
    $taskPublicStream.Position = 0
    $taskPublicStream.SetLength(0)
    $taskPublicStream.Write($payload,0,$payload.Length)
    $taskPublicStream.Flush($true)
}

$taskConfig = New-SDSettings (Join-Path $PSScriptRoot '..')
$taskScriptPath = [IO.Path]::GetFullPath($PSCommandPath)
$taskScriptHash = Hash-Ordinary $taskScriptPath
$taskIdentityHash = Hash-Text ($taskConfig.UniqueId+"`n"+$taskConfig.SerialNumber+"`n"+$taskConfig.Size)
$taskInitialNumber = $null
$taskPrivate = $null
$taskPublicStream = $null
$taskCheckpointNumber = 0
$taskState = $null
$taskSummary = Assert-ProjectPath (Join-Path $PSScriptRoot 'sd-rk3229-c-formato-estado.json')

try {
    Assert-NoReparse $taskConfig.Root $true
    if (Test-Path -LiteralPath $taskSummary) { throw 'Ya existe recibo de esta preparacion; no se reanuda ni se sobrescribe.' }
    $pcFirmware = Check-PCFirmware
    $initial = Get-CheckedSD 'Original'
    $taskInitialNumber = [long]$initial.Disk.Number
    $snapshot = Get-RootSnapshot $initial.Mount
    $initialRecord = Get-SDRecord $initial
    Ensure-SDRawType

    if (-not $Prepare) {
        # Una apertura de lectura confirma permisos e identidad raw. No crea recibos ni escribe SD/PC.
        $probe = Open-CheckedRaw 'Original' $false
        $probe.Dispose()
        [pscustomobject]@{
            state='check_only_verified'; target='SD RK3229-C autorizada'; disk_bytes=$taskConfig.Size
            firmware_sha256=$taskConfig.FirmwareSHA256; original_partition_offset=$taskConfig.PrefixBytes
            prefix_backup_required_bytes=$taskConfig.PrefixBytes; prepare_executed=$false; extractor_copied=$false
        } | ConvertTo-Json -Depth 4
        return
    }

    # Reserva PC antes de cualquier mutacion SD. Si el proceso cae, el recibo impide reintento automatico.
    $privateRoot = Assert-ProjectPath (Join-Path $taskConfig.Root 'privado')
    Assert-NoReparse $privateRoot $true
    $taskPrivate = Assert-ProjectPath (Join-Path $privateRoot ('sd-rk3229-c-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,12)))
    if (Test-Path -LiteralPath $taskPrivate) { throw 'Directorio privado ya existente.' }
    Assert-NoReparse $PSScriptRoot $true
    $taskPublicStream = New-Object IO.FileStream($taskSummary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $null = New-Item -ItemType Directory -Path $taskPrivate -ErrorAction Stop
    Assert-NoReparse $taskPrivate $true
    $taskState = [ordered]@{
        schema='tvbase-sd-normal-preparation-private-1'; state='reserved'; phase='reserved'
        created_utc=[DateTime]::UtcNow.ToString('o'); updated_utc=[DateTime]::UtcNow.ToString('o')
        script_path=$taskScriptPath; script_sha256=$taskScriptHash; initial_disk=$initialRecord
        pc_firmware_path=$pcFirmware; pc_firmware_sha256=$taskConfig.FirmwareSHA256
        original_root=$snapshot; auxiliary_backups=@(); prefix_backup=$null
        prefix_backup_verified=$false; prefix_zero_verified_before_new_layout=$false
        sd_mutation_attempted=$false; normal_fat32_verified=$false; actions=@()
        error=$null; final_disk=$null; final_root=$null
        scope='Borrado autorizado solo de esta SD. Respaldo del prefijo de 96 MiB y auxiliares; imagen SD identica a imagen ya preservada en PC. No respaldo integral.'
    }
    Save-SDCheckpoint 'reserved_before_sd_write' 'preparing'

    foreach ($name in @('sd_boot_config.config','rksdfw.tag')) {
        $expected = @($snapshot.files | Where-Object name -eq $name)
        if ($expected.Count -ne 1) { throw 'Auxiliar no unico.' }
        $taskState.auxiliary_backups += Copy-SmallFile (Join-Path $initial.Mount $name) (Join-Path $taskPrivate $name) $expected[0]
    }
    $prefixPath = Assert-ProjectPath (Join-Path $taskPrivate 'sd-primeros-96MiB-original.bin')
    Assert-NoReparse $taskPrivate $true
    $raw = Open-CheckedRaw 'Original' $false
    try {
        $backup = [TVBase.SDPreparationRawV1]::BackupPrefix($raw,$prefixPath,$taskConfig.PrefixBytes)
        [TVBase.SDPreparationRawV1]::AssertDevice($raw,[int]$taskInitialNumber,$taskConfig.Size,$taskConfig.SerialNumber)
    } finally { $raw.Dispose() }
    $null = Get-CheckedSD 'Original'
    $taskState.prefix_backup = [ordered]@{
        path=$prefixPath; bytes=[long]$backup.Bytes; sha256=$backup.SHA256
        source_reread_verified=$backup.SourceRereadVerified; file_reread_verified=$backup.FileRereadVerified
        file_flush_verified=$backup.FlushFileVerified; raw_handle_identity_verified=$true
    }
    $taskState.prefix_backup_verified = $true
    Save-SDCheckpoint 'backup_verified' 'preparing'

    # Ultima relectura de entradas y respaldos ANTES de Clear-Disk.
    Assert-ScriptUnchanged
    $null = Check-PCFirmware
    $beforeClear = Get-CheckedSD 'Original'
    if ((Get-SDRecord $beforeClear | ConvertTo-Json -Depth 8 -Compress) -cne ($initialRecord | ConvertTo-Json -Depth 8 -Compress)) { throw 'Cambio la geometria o montaje inicial.' }
    Assert-SameSnapshot $snapshot (Get-RootSnapshot $beforeClear.Mount)
    if ((Hash-Ordinary $prefixPath) -cne $backup.SHA256 -or [long](Get-Item -LiteralPath $prefixPath).Length -ne $taskConfig.PrefixBytes) { throw 'Respaldo del prefijo PC no valido.' }
    foreach ($copy in $taskState.auxiliary_backups) {
        if ((Hash-Ordinary $copy.copy_path) -cne $copy.sha256) { throw 'Respaldo auxiliar PC alterado.' }
    }
    # Revalidar tambien identidad y prefijo justo antes de la primera mutacion.
    $raw = Open-CheckedRaw 'Original' $false
    try {
        if ([TVBase.SDPreparationRawV1]::HashPrefix($raw,$taskConfig.PrefixBytes,$false) -cne $backup.SHA256) { throw 'Prefijo SD cambio desde su respaldo.' }
    } finally { $raw.Dispose() }
    $taskState.actions += 'Clear-Disk RemoveData RemoveOEM solicitado solo para la identidad validada'
    Save-SDCheckpoint 'clear_disk_requested' 'preparing'
    $beforeClear = Get-CheckedSD 'Original'
    $taskState.sd_mutation_attempted = $true
    Clear-Disk -InputObject $beforeClear.Disk -RemoveData -RemoveOEM -Confirm:$false -ErrorAction Stop
    $null = Get-CheckedSD 'Cleared'
    Save-SDCheckpoint 'partitions_removed_verified' 'preparing'

    Assert-ScriptUnchanged
    if (-not $taskState.prefix_backup_verified -or (Hash-Ordinary $prefixPath) -cne $backup.SHA256) { throw 'Falta respaldo verificado para eliminar loader antiguo.' }
    $taskState.actions += 'Puesta a cero limitada a primeros 96 MiB, con SD RAW sin particiones'
    Save-SDCheckpoint 'zero_prefix_requested' 'preparing'
    $raw = Open-CheckedRaw 'Cleared' $true
    try {
        $zeroHash = [TVBase.SDPreparationRawV1]::ZeroPrefix($raw,$taskConfig.PrefixBytes)
        [TVBase.SDPreparationRawV1]::AssertDevice($raw,[int]$taskInitialNumber,$taskConfig.Size,$taskConfig.SerialNumber)
    } finally { $raw.Dispose() }
    $null = Get-CheckedSD 'Cleared'
    $taskState.prefix_zero_verified_before_new_layout = $true
    $taskState.zero_prefix_sha256 = $zeroHash
    $taskState.zero_prefix_bytes = $taskConfig.PrefixBytes
    $taskState.zero_prefix_file_flush_verified = $true
    Save-SDCheckpoint 'zero_prefix_reread_verified' 'preparing'

    Assert-ScriptUnchanged
    Save-SDCheckpoint 'initialize_mbr_requested' 'preparing'
    $cleared = Get-CheckedSD 'Cleared'
    Initialize-Disk -InputObject $cleared.Disk -PartitionStyle MBR -ErrorAction Stop
    $null = Get-CheckedSD 'Initialized'
    Save-SDCheckpoint 'new_partition_requested' 'preparing'
    $initialized = Get-CheckedSD 'Initialized'
    $null = New-Partition -InputObject $initialized.Disk -Offset $taskConfig.NewOffset -UseMaximumSize -AssignDriveLetter -ErrorAction Stop
    $null = Get-CheckedSD 'Partitioned'

    Assert-ScriptUnchanged
    Save-SDCheckpoint 'quick_fat32_format_requested' 'preparing'
    $partitioned = Get-CheckedSD 'Partitioned'
    # Sin -Full: formato rapido, sin puesta a cero de toda la SD.
    $null = Format-Volume -Partition $partitioned.Partition -FileSystem FAT32 -NewFileSystemLabel $taskConfig.Label -Force -Confirm:$false -ErrorAction Stop
    $final = Get-CheckedSD 'Final'
    $empty = Get-RootSnapshot $final.Mount $true
    $taskState.final_disk = Get-SDRecord $final
    $taskState.final_root = $empty
    $taskState.normal_fat32_verified = $true
    $taskState.actions += 'MBR nueva, una particion maxima desde 1 MiB y FAT32 TVBASESD vacia verificados; sin ZIP'
    Save-SDCheckpoint 'normal_sd_verified' 'formateada_sd_normal'
    Write-Output 'SD normal FAT32 TVBASESD verificada. Sin extractor ni otros archivos copiados. Expulsion segura pendiente.'
} catch {
    if ($null -ne $taskState -and $null -ne $taskPublicStream -and $null -ne $taskPrivate) {
        $taskState.error = [ordered]@{ message=$_.Exception.Message; type=$_.Exception.GetType().FullName; phase=$taskState.phase; utc=[DateTime]::UtcNow.ToString('o') }
        try { Save-SDCheckpoint 'failed_preserved' 'failed_preserved' }
        catch { Write-Warning 'No se pudo completar el recibo de fallo; conservar todos los archivos y el recibo reservado.' }
    }
    throw
} finally {
    if ($null -ne $taskPublicStream) { $taskPublicStream.Dispose() }
}
