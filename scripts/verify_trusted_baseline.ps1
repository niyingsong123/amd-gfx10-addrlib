# Verify bytes only; this is not an algorithm correctness test.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repoRoot 'docs/TRUSTED_BASELINE.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema_version -ne 1 -or @($manifest.files).Count -ne 3) {
    throw 'Unexpected trusted baseline manifest schema or file count.'
}

$failures = @()
foreach ($entry in $manifest.files) {
    $filePath = Join-Path $repoRoot $entry.path
    if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
        $failures += "MISSING: $($entry.path)"
        continue
    }
    $actualHash = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash
    $actualBytes = (Get-Item -LiteralPath $filePath).Length
    if ($actualHash -ne $entry.sha256 -or $actualBytes -ne $entry.bytes) {
        $failures += "CHANGED: $($entry.path) (SHA256=$actualHash, bytes=$actualBytes)"
    } else {
        Write-Output "OK: $($entry.path)"
    }
}

if ($failures.Count -gt 0) {
    throw ($failures -join [Environment]::NewLine)
}
Write-Output 'PASS: all 3 trusted files match the recorded baseline. This does not validate algorithms.'
