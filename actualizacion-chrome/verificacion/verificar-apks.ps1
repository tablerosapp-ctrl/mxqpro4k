[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$ApkPath,
    [string]$ExpectedCertificateSha256 = 'f0fd6c5b410f25cb25c3b53346c8972fae30f8ee7411df910480ad6b2d60db83'
)

# Solo lectura de APK: no instala, modifica ni firma ningun paquete.
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$java = Join-Path $projectRoot 'tools\verificacion-apk\java21\jdk-21.0.12.1+1-jre\bin\java.exe'
$jar = Join-Path $projectRoot 'tools\verificacion-apk\build-tools-37\android-37.0\lib\apksigner.jar'
if (-not (Test-Path -LiteralPath $java) -or -not (Test-Path -LiteralPath $jar)) {
    throw 'Faltan las herramientas locales documentadas en herramientas.json.'
}
if ($ExpectedCertificateSha256 -notmatch '^[0-9a-fA-F]{64}$') {
    throw 'Se necesita un SHA256 de certificado valido.'
}
$expected = $ExpectedCertificateSha256.ToLowerInvariant()
$runName = 'ejecucion-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$runDir = Join-Path $PSScriptRoot $runName
New-Item -ItemType Directory -Path $runDir | Out-Null
$results = @()

foreach ($apk in $ApkPath) {
    $fullPath = (Resolve-Path -LiteralPath $apk).Path
    if ([IO.Path]::GetExtension($fullPath) -ne '.apk') { throw "Se esperaba un archivo APK: $fullPath" }
    $file = Get-Item -LiteralPath $fullPath
    if ($file.PSIsContainer) { throw "Se esperaba un archivo: $fullPath" }
    $hashBefore = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $index = $results.Count + 1
    $label = '{0:D2}-{1}' -f $index, [IO.Path]::GetFileNameWithoutExtension($file.Name)
    $checks = @()

    foreach ($mode in @('general', 'android-9-api28')) {
        $arguments = '-jar "' + $jar + '" verify --verbose --print-certs'
        if ($mode -eq 'android-9-api28') { $arguments += ' --min-sdk-version 28 --max-sdk-version 28' }
        $arguments += ' "' + $fullPath + '"'
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $java
        $startInfo.Arguments = $arguments
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        try {
            if (-not $process.Start()) { throw 'No se pudo iniciar apksigner.' }
            $stdoutTask = $process.StandardOutput.ReadToEndAsync()
            $stderrTask = $process.StandardError.ReadToEndAsync()
            $process.WaitForExit()
            $stdout = $stdoutTask.GetAwaiter().GetResult()
            $stderr = $stderrTask.GetAwaiter().GetResult()
            $exitCode = $process.ExitCode
        } finally {
            $process.Dispose()
        }
        $logPath = Join-Path $runDir ($label + '.' + $mode + '.txt')
        [IO.File]::WriteAllText($logPath, $stdout + [Environment]::NewLine + $stderr, (New-Object Text.UTF8Encoding($false)))
        # El sello de distribucion Source Stamp tiene su propia clave; no es un firmante del APK.
        $digests = @([regex]::Matches($stdout, '(?m)^(?:Signer #\d+|V\d+(?:\.\d+)? Signer(?: #\d+)?): certificate SHA-256 digest:\s*([a-fA-F0-9]{64})') | ForEach-Object { $_.Groups[1].Value.ToLowerInvariant() } | Select-Object -Unique)
        $stampDigests = @([regex]::Matches($stdout, '(?m)^Source Stamp Signer: certificate SHA-256 digest:\s*([a-fA-F0-9]{64})') | ForEach-Object { $_.Groups[1].Value.ToLowerInvariant() } | Select-Object -Unique)
        $signerCountMatch = [regex]::Match($stdout, '(?m)^Number of signers:\s*(\d+)')
        $signerCount = if ($signerCountMatch.Success) { [int]$signerCountMatch.Groups[1].Value } else { $null }
        $certificateMatches = ($signerCount -eq 1 -and $digests.Count -eq 1 -and $digests[0] -eq $expected)
        $checks += [pscustomobject]@{
            modo = $mode
            codigo_salida = $exitCode
            firma_verificada = ($exitCode -eq 0)
            certificados_sha256 = $digests
            cantidad_firmantes_apk = $signerCount
            sellos_distribucion_sha256 = $stampDigests
            certificado_coincide = $certificateMatches
            registro = $logPath
            argumentos = $arguments
        }
    }

    $hashAfter = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $passed = $hashBefore -eq $hashAfter
    foreach ($check in $checks) { if (-not $check.firma_verificada -or -not $check.certificado_coincide) { $passed = $false } }
    $results += [pscustomobject]@{
        archivo = $fullPath
        bytes = $file.Length
        sha256 = $hashBefore
        archivo_sin_cambios = ($hashBefore -eq $hashAfter)
        certificado_esperado_sha256 = $expected
        comprobaciones = $checks
        aprobado = $passed
    }
}

$allPassed = @($results | Where-Object { -not $_.aprobado }).Count -eq 0
$report = [pscustomobject]@{
    fecha = (Get-Date).ToString('o')
    java = $java
    apksigner = $jar
    apksigner_sha256 = (Get-FileHash -LiteralPath $jar -Algorithm SHA256).Hash.ToLowerInvariant()
    resultados = $results
    todos_aprobados = $allPassed
}
$reportPath = Join-Path $runDir 'resultado.json'
[IO.File]::WriteAllText($reportPath, ($report | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
$report | ConvertTo-Json -Depth 8
if (-not $allPassed) { throw "No todos los APK aprobaron la verificacion. Informe: $reportPath" }
