# Escribe exclusivamente la primera imagen de prueba en el Kingston identificado.
# Ejecutar elevado; revalida el dispositivo, su contenido y la imagen antes de escribir.
param([switch]$Reintentar)

throw 'Grabador 1.8.5 retirado tras dos fallos sin registro detallado. El reemplazo autorizado de imagen directa es grabar-kingston-actual.ps1, con identidad estable, registro completo y verificacion.'

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$statusPath = Join-Path $PSScriptRoot 'estado-grabacion.json'
$expectedId = 'USBSTOR\DISK&VEN_KINGSTON&PROD_DATATRAVELER_3.0&REV_\KINGSTON_SERIAL_LOCAL&0:PC_LOCAL'
$expectedSize = [long]30943995904
$expectedHash = '4479B09374D92FFE4BE625B5DDED96C5D7D7A0E8C6BCB0A7D2894A839214A2F8'
$imagePath = Join-Path $projectRoot 'images\Armbian_26.05.0_amlogic_s905l2_noble_6.12.91_server_2026.06.01.img'
$imagerPath = Join-Path $projectRoot 'tools\imager-portable\rpi-imager.exe'
$previousState = if (Test-Path -LiteralPath $statusPath) {
    Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
} else { $null }

function Write-Status([string]$state, [string]$detail) {
    [ordered]@{
        estado = $state
        detalle = $detail
        fecha = (Get-Date).ToString('o')
        imagen = $imagePath
        destino_id = $expectedId
    } | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
}

function Get-ValidatedDisk {
    $matches = @(Get-Disk | Where-Object { $_.UniqueId -eq $expectedId })
    if ($matches.Count -ne 1) { throw 'El Kingston esperado no esta conectado de forma inequivoca.' }
    $target = $matches[0]
    if ($target.BusType -ne 'USB' -or $target.Size -ne $expectedSize -or
        $target.FriendlyName -ne 'Kingston DataTraveler 3.0' -or
        $target.IsBoot -or $target.IsSystem -or $target.IsReadOnly -or $target.IsOffline) {
        throw 'El destino no cumple las condiciones de la prueba.'
    }
    if ($Reintentar) {
        if (-not $previousState -or $previousState.estado -ne 'error' -or
            $previousState.destino_id -ne $expectedId -or $previousState.imagen -ne $imagePath) {
            throw 'No hay una grabacion fallida de esta imagen en este Kingston que justifique reintentar.'
        }
        # El escritor deja sin tabla utilizable una imagen incompleta.
        # El reintento conserva las comprobaciones de identidad, capacidad y disco de sistema.
        return $target
    }
    $partitions = @(Get-Partition -DiskNumber $target.Number)
    if ($partitions.Count -ne 1 -or $partitions[0].DriveLetter -ne 'D') {
        throw 'Cambio la particion del pendrive. Revisar antes de continuar.'
    }
    $files = @(Get-ChildItem -LiteralPath 'D:\' -Force | Where-Object {
        $_.Name -ne 'System Volume Information'
    })
    if ($files.Count -gt 0) { throw 'D: contiene archivos. No se sobrescribe.' }
    return $target
}

try {
    Write-Status 'comprobando' 'Verificando imagen y el Kingston seleccionado.'
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Se necesitan permisos de administrador de Windows.'
    }
    $null = Get-ValidatedDisk
    if ((Get-Item -LiteralPath $imagePath).Length -ne 3686793216) { throw 'Tamano de imagen inesperado.' }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $imagePath).Hash -ne $expectedHash) {
        throw 'El SHA256 de la imagen no coincide.'
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $imagerPath
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Raspberry Pi Limited') {
        throw 'La firma de la herramienta de grabacion no es valida.'
    }
    $targetDisk = Get-ValidatedDisk
    $devicePath = '\\.\PhysicalDrive' + $targetDisk.Number
    Write-Status 'grabando-y-verificando' ('Kingston seleccionado, disco ' + $targetDisk.Number + '. Verificacion habilitada.')
    $imagerArguments = @('--cli', '--sha256', $expectedHash, ('"' + $imagePath + '"'), $devicePath)
    $writer = Start-Process -FilePath $imagerPath -ArgumentList $imagerArguments -WindowStyle Hidden -Wait -PassThru
    if ($writer.ExitCode -ne 0) { throw ('La herramienta termino con codigo ' + $writer.ExitCode + '.') }
    Write-Status 'completado' 'Imagen grabada y verificada por Raspberry Pi Imager. Sin personalizaciones.'
} catch {
    Write-Status 'error' $_.Exception.Message
    exit 1
}
