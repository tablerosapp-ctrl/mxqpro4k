$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
$planPath = Join-Path $taskRoot 'docs/evidencia/limpieza-plan.json'
$receiptPath = Join-Path $taskRoot 'docs/evidencia/limpieza-resultado.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Ya existe un recibo: no repetir la limpieza.' }
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.root -ne $taskRoot -or $plan.state -ne 'audited_not_deleted') { throw 'Plan fuera de este proyecto o no auditado.' }
$checked = @()
foreach ($entry in $plan.entries) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $taskRoot $entry.path))
    if (-not $candidate.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera del proyecto.' }
    $item = Get-Item -LiteralPath $candidate -Force
    # Rechazar enlaces en el destino y en cualquiera de sus ancestros.
    $ancestor = $item
    while ($ancestor.FullName -ne $taskRoot) {
        if ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Enlace inesperado: $($ancestor.FullName)" }
        $ancestor = if ($ancestor -is [IO.DirectoryInfo]) { $ancestor.Parent } else { $ancestor.Directory }
        if ($null -eq $ancestor) { throw 'Raiz inesperada.' }
    }
    if ($item.PSIsContainer) {
        $children = @(Get-ChildItem -LiteralPath $candidate -Recurse -Force)
        if (@($children | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Enlace en cache.' }
        $files = @($children | Where-Object { -not $_.PSIsContainer })
        $length = ($files | Measure-Object Length -Sum).Sum
        if ($files.Count -ne $entry.files -or $length -ne $entry.bytes) { throw 'Cache cambio despues del inventario.' }
    } else {
        if ($item.Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Archivo cambio despues de auditarlo.' }
    }
    foreach ($retained in $entry.retained) { if (-not (Test-Path -LiteralPath (Join-Path $taskRoot $retained))) { throw "Falta fuente conservada: $retained" } }
    $checked += [pscustomobject]@{path=$candidate; entry=$entry}
}
$removed = @()
try {
    foreach ($item in $checked) {
        Remove-Item -LiteralPath $item.path -Recurse -Force
        if (Test-Path -LiteralPath $item.path) { throw 'El destino no se elimino.' }
        $removed += $item.entry
    }
    $state = 'completed'
} catch {
    $state = 'partial_failure'
    $nativeError = $_.Exception.ToString()
} finally {
    [ordered]@{state=$state; date=(Get-Date).ToString('o'); root=$taskRoot; bytes_removed=($removed | Measure-Object bytes -Sum).Sum; removed=$removed; error=$nativeError} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
if ($state -ne 'completed') { throw $nativeError }
Get-Content -LiteralPath $receiptPath -Raw
