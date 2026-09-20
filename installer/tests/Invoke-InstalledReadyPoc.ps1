[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$installer = Join-Path $repoRoot 'dist\installer\1.0.0\EXPC-WLK-Setup-CUDA-v1.0.0.exe'
$installRoot = Join-Path $env:ProgramFiles 'EXPC-WLK'
$programDataRoot = Join-Path $env:PROGRAMDATA 'EXPC-WLK'
$userData = Join-Path $env:APPDATA 'whisperkey'
$work = Join-Path $repoRoot 'installer\work\ready-poc'
$backup = Join-Path $work 'backup-user-data'
$portableWasRunning = [bool](Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($repoRoot, [StringComparison]::OrdinalIgnoreCase) -and
    $_.Name -in @('EXPC-WLK.exe', 'pythonw.exe')
})

if (Test-Path -LiteralPath $installRoot) { throw 'Install root already exists' }
if (Test-Path -LiteralPath $programDataRoot) { throw 'ProgramData root already exists' }
if (Test-Path -LiteralPath $work) { throw 'POC work root already exists' }
New-Item -ItemType Directory -Path $work | Out-Null
$hadUserData = Test-Path -LiteralPath $userData
if ($hadUserData) { Copy-Item -LiteralPath $userData -Destination $backup -Recurse }

try {
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($repoRoot, [StringComparison]::OrdinalIgnoreCase) -and
        $_.Name -in @('EXPC-WLK.exe', 'pythonw.exe')
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    $install = Start-Process -FilePath $installer -ArgumentList @(
        '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/TASKS='
    ) -Wait -PassThru
    if ($install.ExitCode) { throw "Installer returned $($install.ExitCode)" }
    $models = Join-Path $programDataRoot 'Models'
    New-Item -ItemType Directory -Path $models -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repoRoot 'WhisperKey\models\large-v3-turbo') `
        -Destination (Join-Path $models 'large-v3-turbo') -Recurse

    $token = [guid]::NewGuid().ToString('N')
    $receipt = Join-Path $userData "installed-update-ready-$token.json"
    Start-Process -FilePath (Join-Path $installRoot 'EXPC-WLK.exe') -ArgumentList @(
        '--installed-update-token', $token,
        '--installed-update-receipt', ('"' + $receipt + '"')
    )
    $deadline = [DateTime]::UtcNow.AddSeconds(90)
    while ([DateTime]::UtcNow -lt $deadline -and -not (Test-Path -LiteralPath $receipt)) {
        Start-Sleep -Milliseconds 250
    }
    if (-not (Test-Path -LiteralPath $receipt)) { throw 'Ready receipt was not created' }
    $ready = Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
    if ($ready.format -ne 1 -or $ready.state -ne 'ready' -or $ready.token -ne $token) {
        throw 'Ready receipt content is invalid'
    }
    [pscustomobject]@{Status='PASS';Receipt=$receipt} | ConvertTo-Json
} finally {
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($installRoot, [StringComparison]::OrdinalIgnoreCase)
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $userData) {
        Copy-Item -LiteralPath $userData -Destination (Join-Path $work 'captured-user-data') -Recurse -Force
    }
    $uninstaller = Join-Path $installRoot 'unins000.exe'
    if (Test-Path -LiteralPath $uninstaller) {
        Start-Process -FilePath $uninstaller -ArgumentList @(
            '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/FULLCLEANUP'
        ) -Wait
    }
    if (Test-Path -LiteralPath $userData) { Remove-Item -LiteralPath $userData -Recurse -Force }
    if ($hadUserData) { Copy-Item -LiteralPath $backup -Destination $userData -Recurse }
    if ($portableWasRunning) { Start-Process -FilePath (Join-Path $repoRoot 'EXPC-WLK.exe') }
}
