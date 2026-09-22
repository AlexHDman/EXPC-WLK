[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$installer = (Resolve-Path (Join-Path $repoRoot 'dist\installer\1.0.2\EXPC-WLK-Setup-CUDA-v1.0.2.exe')).Path
$stage102 = (Resolve-Path (Join-Path $repoRoot 'installer\work\stage-cuda-1.0.2')).Path
$installRoot = Join-Path $env:ProgramFiles 'EXPC-WLK'
$userData = Join-Path $env:APPDATA 'whisperkey'
$programDataRoot = Join-Path $env:PROGRAMDATA 'EXPC-WLK'
$models = Join-Path $programDataRoot 'Models'
$work = Join-Path $repoRoot 'installer\work\live-smoke-1.0.2-cuda'
$backup = Join-Path $work 'backup'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$checks = [Collections.Generic.List[string]]::new()

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
    $checks.Add($Message)
}
function Run-Process([string]$Path, [string[]]$Arguments, [int]$Expected = 0) {
    $process = Start-Process -FilePath $Path -ArgumentList $Arguments -Wait -PassThru
    if ($process.ExitCode -ne $Expected) {
        throw "$Path returned $($process.ExitCode), expected $Expected"
    }
}
function Stop-Tree([string]$Prefix) {
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase) -and
        $_.Name -in @('EXPC-WLK.exe', 'pythonw.exe')
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
function Uninstaller {
    $path = Join-Path $installRoot 'unins000.exe'
    if (-not (Test-Path -LiteralPath $path)) { throw 'Uninstaller missing' }
    return $path
}
function Invoke-Update([string[]]$ExtraArgs, [int]$Expected, [string]$ReceiptCase = 'fresh') {
    $token = [guid]::NewGuid().ToString('N')
    $expectedReceipt = Join-Path $userData ("installed-update-ready-$token.json")
    $receipt = if ($ReceiptCase -eq 'invalid-path') {
        Join-Path $work ("invalid-ready-$token.json")
    } else { $expectedReceipt }
    if ($ReceiptCase -eq 'stale-valid') {
        $payload = [ordered]@{format=1;state='ready';token=$token} | ConvertTo-Json -Compress
        [IO.File]::WriteAllText($expectedReceipt, $payload + "`n", [Text.Encoding]::ASCII)
    }
    $helper = Join-Path $work ("InstalledUpdater-$token.exe")
    Copy-Item -LiteralPath (Join-Path $installRoot 'updater\InstalledUpdater.exe') -Destination $helper
    $arguments = @(
        ('"' + $installRoot + '"'), ('"' + $stage102 + '"'), ('"' + $receipt + '"'),
        '0', '0', $token, '--quiet', '--keep-stage', '--test-instance'
    ) + $ExtraArgs
    Run-Process $helper $arguments $Expected
    return [pscustomobject]@{Token=$token;Receipt=$receipt}
}

if (Test-Path -LiteralPath $installRoot) { throw 'Install root already exists' }
if (Test-Path -LiteralPath $work) { throw 'CUDA smoke work directory already exists' }
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$portableWasRunning = [bool](Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($repoRoot, [StringComparison]::OrdinalIgnoreCase) -and
    $_.Name -in @('EXPC-WLK.exe', 'pythonw.exe')
})
$originalUserData = Test-Path -LiteralPath $userData
if ($originalUserData) { Copy-Item -LiteralPath $userData -Destination (Join-Path $backup 'user-data') -Recurse }
$originalProgramData = Test-Path -LiteralPath $programDataRoot
if ($originalProgramData) {
    Copy-Item -LiteralPath $programDataRoot -Destination (Join-Path $backup 'program-data') -Recurse
}
$originalRunValue = $null
try { $originalRunValue = Get-ItemPropertyValue -LiteralPath $runKey -Name 'EXPC-WLK' } catch {}

if (Test-Path -LiteralPath $userData) { Remove-Item -LiteralPath $userData -Recurse -Force }
if (Test-Path -LiteralPath $programDataRoot) { Remove-Item -LiteralPath $programDataRoot -Recurse -Force }

try {
    New-Item -ItemType Directory -Path $userData -Force | Out-Null
    $marker = Join-Path $userData '.installer-phase3-preserve'
    [IO.File]::WriteAllText($marker, 'preserve')
    Run-Process $installer @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',
        '/TASKS=desktopicon,autostart', "/LOG=$(Join-Path $work 'cuda-install.log')")
    Assert-True (Test-Path -LiteralPath (Join-Path $installRoot 'runtime\native\cublas64_12.dll')) 'CUDA runtime installed'
    Assert-True (Test-Path -LiteralPath (Join-Path $installRoot 'updater\InstalledUpdater.exe')) 'installed updater helper'
    $runValue = Get-ItemPropertyValue -LiteralPath $runKey -Name 'EXPC-WLK'
    Assert-True ($runValue -eq ('"' + (Join-Path $installRoot 'EXPC-WLK.exe') + '"')) 'optional autostart'

    $import = & (Join-Path $installRoot 'runtime\python.exe') -I `
        (Join-Path $repoRoot 'installer\tests\installed_model_import_smoke.py') `
        --metadata-root (Join-Path $installRoot 'updater') --model-root $models `
        --source (Join-Path $repoRoot 'WhisperKey\models\large-v3-turbo') `
        --model large-v3-turbo | ConvertFrom-Json
    Assert-True ($import.status -eq 'valid' -and $import.copied -and
        $import.source_unchanged -and $import.metadata) 'offline large-v3-turbo import'
    $modelFile = Join-Path $models 'large-v3-turbo\model.bin'
    $modelHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $modelFile).Hash
    $selftest = & (Join-Path $installRoot 'runtime\python.exe') -I `
        (Join-Path $installRoot 'app\installed_boot.py') --selftest | ConvertFrom-Json
    Assert-True ($selftest.cuda_devices -gt 0 -and $selftest.cuda_fp16) 'CUDA FP16 detection'
    Assert-True ($selftest.large_status -eq 'valid') 'large-v3-turbo ProgramData discovery'

    $inference = & (Join-Path $installRoot 'runtime\python.exe') -I `
        (Join-Path $repoRoot 'installer\tests\installed_inference_smoke.py') | ConvertFrom-Json
    Assert-True ($inference.pass -and $inference.device -eq 'cuda' -and $inference.model -eq 'large-v3-turbo') 'CUDA large-v3-turbo inference'
    Assert-True ($inference.hotkey_bindings -eq 5) 'installed hotkeys'
    Assert-True ($inference.paste) 'installed clipboard/paste'

    Stop-Tree $repoRoot
    Start-Process -FilePath (Join-Path $installRoot 'EXPC-WLK.exe') -ArgumentList '--test'
    Start-Sleep -Seconds 15
    $installedPython = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'pythonw.exe' -and $_.ExecutablePath -and
        $_.ExecutablePath.StartsWith($installRoot, [StringComparison]::OrdinalIgnoreCase)
    }
    Assert-True ([bool]$installedPython) 'installed CUDA launcher'
    Stop-Tree $installRoot

    $directToken = [guid]::NewGuid().ToString('N')
    $directReceipt = Join-Path $userData ("installed-update-ready-$directToken.json")
    Start-Process -FilePath (Join-Path $installRoot 'EXPC-WLK.exe') -ArgumentList @(
        '--installed-update-token', $directToken,
        '--installed-update-receipt', ('"' + $directReceipt + '"'), '--test'
    )
    $directDeadline = [DateTime]::UtcNow.AddSeconds(90)
    while ([DateTime]::UtcNow -lt $directDeadline -and -not (Test-Path -LiteralPath $directReceipt)) {
        Start-Sleep -Milliseconds 250
    }
    Assert-True (Test-Path -LiteralPath $directReceipt) 'launcher propagates updater Ready token'
    $directReady = Get-Content -LiteralPath $directReceipt -Raw | ConvertFrom-Json
    Assert-True ($directReady.format -eq 1 -and $directReady.state -eq 'ready' -and
        $directReady.token -eq $directToken) 'launcher writes structured Ready receipt'
    Remove-Item -LiteralPath $directReceipt -Force
    Stop-Tree $installRoot

    $null = Invoke-Update @() 0
    $release102 = Get-Content -LiteralPath (Join-Path $installRoot 'updater\config\release.json') -Raw | ConvertFrom-Json
    Assert-True ($release102.version -eq '1.0.2') 'installed update transaction v1.0.2'
    Assert-True ((Get-Item (Join-Path $installRoot 'EXPC-WLK.exe')).VersionInfo.FileVersion -eq '1.0.2.0') 'updated launcher version'
    Assert-True (Test-Path -LiteralPath $marker) 'updater preserves AppData settings'
    Assert-True ((Get-FileHash -Algorithm SHA256 -LiteralPath $modelFile).Hash -eq $modelHash) 'updater preserves ProgramData model'
    $registeredVersion = Get-ItemPropertyValue `
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{2E801B1E-38AA-47AE-A9CC-AC43AB1E60BA}_is1' `
        -Name DisplayVersion
    Assert-True ($registeredVersion -eq '1.0.2') 'Apps and Features version updated'
    Stop-Tree $installRoot

    $beforeRollback = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')).Hash
    $null = Invoke-Update @() 2 'invalid-path'
    Assert-True ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')).Hash -eq $beforeRollback) 'invalid receipt path rejected before swap'

    $null = Invoke-Update @('--simulate-timeout') 1 'stale-valid'
    Assert-True ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')).Hash -eq $beforeRollback) 'stale Ready receipt rejected with rollback'

    $null = Invoke-Update @('--simulate-malformed-receipt') 1
    Assert-True ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')).Hash -eq $beforeRollback) 'malformed Ready receipt rejected with rollback'

    $null = Invoke-Update @('--simulate-timeout') 1
    Assert-True ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')).Hash -eq $beforeRollback) 'Ready timeout rolls back application'

    $null = Invoke-Update @('--simulate-failure') 1
    $afterRollback = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')).Hash
    $releaseAfterRollback = Get-Content -LiteralPath (Join-Path $installRoot 'updater\config\release.json') -Raw | ConvertFrom-Json
    Assert-True ($beforeRollback -eq $afterRollback -and $releaseAfterRollback.version -eq '1.0.2') 'post-swap rollback restores application'
    Assert-True (Test-Path -LiteralPath $marker) 'rollback preserves AppData settings'
    Assert-True ((Get-FileHash -Algorithm SHA256 -LiteralPath $modelFile).Hash -eq $modelHash) 'rollback preserves ProgramData model'

    Run-Process (Uninstaller) @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART')
    Assert-True (-not (Test-Path -LiteralPath $installRoot)) 'CUDA uninstall removes application'
    Assert-True (Test-Path -LiteralPath $marker) 'CUDA uninstall keeps settings'
    Assert-True (Test-Path -LiteralPath $modelFile) 'CUDA uninstall keeps model'

    Run-Process $installer @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/TASKS=')
    Run-Process (Uninstaller) @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/FULLCLEANUP')
    Assert-True (-not (Test-Path -LiteralPath $programDataRoot)) 'full cleanup removes CUDA model data'
    Assert-True (-not (Test-Path -LiteralPath $userData)) 'full cleanup removes test settings'
    [pscustomobject]@{Status='PASS';Checks=$checks.Count;Results=$checks} | ConvertTo-Json
} finally {
    Stop-Tree $installRoot
    Stop-Tree $repoRoot
    if ((Test-Path -LiteralPath $work) -and (Test-Path -LiteralPath $userData)) {
        Copy-Item -LiteralPath $userData -Destination (Join-Path $work 'captured-user-data') -Recurse -Force
    }
    if (Test-Path -LiteralPath $installRoot) {
        $uninstaller = Join-Path $installRoot 'unins000.exe'
        if (Test-Path -LiteralPath $uninstaller) {
            Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/FULLCLEANUP') -Wait
        }
    }
    if (Test-Path -LiteralPath $userData) { Remove-Item -LiteralPath $userData -Recurse -Force }
    if ($originalUserData) { Copy-Item -LiteralPath (Join-Path $backup 'user-data') -Destination $userData -Recurse }
    try {
        if (Test-Path -LiteralPath $programDataRoot) {
            Get-ChildItem -LiteralPath $programDataRoot -Force | Remove-Item -Recurse -Force
        }
        if ($originalProgramData) {
            New-Item -ItemType Directory -Path $programDataRoot -Force | Out-Null
            Get-ChildItem -LiteralPath (Join-Path $backup 'program-data') -Force | ForEach-Object {
                Copy-Item -LiteralPath $_.FullName -Destination $programDataRoot -Recurse -Force
            }
        } elseif (Test-Path -LiteralPath $programDataRoot) {
            Remove-Item -LiteralPath $programDataRoot -Force
        }
    } catch { Write-Warning "ProgramData restore failed: $_" }
    if ($null -ne $originalRunValue) {
        New-Item -Path $runKey -Force | Out-Null
        Set-ItemProperty -LiteralPath $runKey -Name 'EXPC-WLK' -Value $originalRunValue
    } else {
        Remove-ItemProperty -LiteralPath $runKey -Name 'EXPC-WLK' -ErrorAction SilentlyContinue
    }
    if ($portableWasRunning) { Start-Process -FilePath (Join-Path $repoRoot 'EXPC-WLK.exe') }
}
