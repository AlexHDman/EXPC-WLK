[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('cpu','cuda')][string]$Profile
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$version = '1.0.0'
$profileUpper = $Profile.ToUpperInvariant()
$installer = Join-Path $repoRoot "dist\installer\$version\EXPC-WLK-Setup-$profileUpper-v$version.exe"
$stage = Join-Path $repoRoot "installer\work\stage-$Profile-1.0.1"
$root = Join-Path $env:ProgramFiles 'EXPC-WLK'
$userData = Join-Path $env:APPDATA 'whisperkey'
$modelName = if ($Profile -eq 'cpu') { 'small' } else { 'large-v3-turbo' }
$modelFile = Join-Path $env:ProgramData "EXPC-WLK\Models\$modelName\model.bin"
$work = Join-Path $repoRoot "installer\work\updater-matrix-$Profile"
$checks = [Collections.Generic.List[string]]::new()

function Assert-True([bool]$condition, [string]$message) {
    if (-not $condition) { throw $message }
    $checks.Add($message)
}
function Run([string]$path, [string[]]$arguments, [int]$expected = 0) {
    $process = Start-Process -FilePath $path -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne $expected) {
        throw "$path returned $($process.ExitCode), expected $expected"
    }
}
function Stop-Installed {
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
function Update([string[]]$extra, [int]$expected, [string]$receiptCase = 'fresh') {
    $token = [guid]::NewGuid().ToString('N')
    $expectedReceipt = Join-Path $userData "installed-update-ready-$token.json"
    $receipt = if ($receiptCase -eq 'invalid') { Join-Path $work "invalid-$token.json" } else { $expectedReceipt }
    if ($receiptCase -eq 'stale') {
        [IO.File]::WriteAllText($receipt,
            '{"format":1,"state":"ready","token":"' + $token + '"}' + "`n",
            [Text.Encoding]::ASCII)
    }
    $helper = Join-Path $work "InstalledUpdater-$token.exe"
    Copy-Item -LiteralPath (Join-Path $root 'updater\InstalledUpdater.exe') -Destination $helper
    Run $helper ((@(('"' + $root + '"'), ('"' + $stage + '"'), ('"' + $receipt + '"'),
        '0', '0', $token, '--quiet', '--keep-stage', '--test-instance') + $extra)) $expected
}

if (Test-Path $root) { throw "Install root already exists: $root" }
if (Test-Path $work) { throw "Matrix work root already exists: $work" }
if (-not (Test-Path $modelFile)) { throw "Required model fixture is missing: $modelFile" }
New-Item -ItemType Directory -Path $work | Out-Null
$modelHash = (Get-FileHash -Algorithm SHA256 $modelFile).Hash
$settings = Join-Path $userData 'user_settings.yaml'
$settingsHash = if (Test-Path $settings) { (Get-FileHash -Algorithm SHA256 $settings).Hash } else { $null }

try {
    Run $installer @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/TASKS=')

    if ($Profile -eq 'cuda') {
        $inference = & (Join-Path $root 'runtime\python.exe') -I `
            (Join-Path $repoRoot 'installer\tests\installed_inference_smoke.py') | ConvertFrom-Json
        Assert-True ($inference.pass -and $inference.device -eq 'cuda' -and
            $inference.compute_type -eq 'float16' -and $inference.model -eq 'large-v3-turbo') `
            'CUDA large-v3-turbo FP16 inference'
        Assert-True ($inference.hotkey_bindings -eq 5) 'CUDA installed hotkeys'
        Assert-True ([bool]$inference.paste) 'CUDA installed clipboard/paste'
    }

    $token = [guid]::NewGuid().ToString('N')
    $receipt = Join-Path $userData "installed-update-ready-$token.json"
    Start-Process (Join-Path $root 'EXPC-WLK.exe') -ArgumentList @(
        '--installed-update-token', $token, '--installed-update-receipt', ('"' + $receipt + '"'), '--test')
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    while ([DateTime]::UtcNow -lt $deadline -and -not (Test-Path $receipt)) { Start-Sleep -Milliseconds 200 }
    Assert-True (Test-Path $receipt) "$profileUpper installed Ready"
    $ready = Get-Content $receipt -Raw | ConvertFrom-Json
    Assert-True ($ready.format -eq 1 -and $ready.state -eq 'ready' -and $ready.token -eq $token) "$profileUpper structured Ready"
    Remove-Item $receipt -Force
    Stop-Installed

    Update @() 0
    $release = Get-Content (Join-Path $root 'updater\config\release.json') -Raw | ConvertFrom-Json
    Assert-True ($release.version -eq '1.0.1') "$profileUpper v1.0.0 to v1.0.1 commit"
    $stableHash = (Get-FileHash -Algorithm SHA256 (Join-Path $root 'EXPC-WLK.exe')).Hash

    Update @() 2 'invalid'
    Assert-True ((Get-FileHash -Algorithm SHA256 (Join-Path $root 'EXPC-WLK.exe')).Hash -eq $stableHash) 'invalid receipt path rejected before swap'
    Update @('--simulate-timeout') 1 'stale'
    Assert-True ((Get-FileHash -Algorithm SHA256 (Join-Path $root 'EXPC-WLK.exe')).Hash -eq $stableHash) 'stale receipt rollback'
    Update @('--simulate-malformed-receipt') 1
    Assert-True ((Get-FileHash -Algorithm SHA256 (Join-Path $root 'EXPC-WLK.exe')).Hash -eq $stableHash) 'malformed receipt rollback'
    Update @('--simulate-timeout') 1
    Assert-True ((Get-FileHash -Algorithm SHA256 (Join-Path $root 'EXPC-WLK.exe')).Hash -eq $stableHash) 'timeout rollback'
    Update @('--simulate-failure') 1
    Assert-True ((Get-FileHash -Algorithm SHA256 (Join-Path $root 'EXPC-WLK.exe')).Hash -eq $stableHash) 'post-swap failure rollback'
    Assert-True ((Get-FileHash -Algorithm SHA256 $modelFile).Hash -eq $modelHash) 'model preserved'
    if ($settingsHash) { Assert-True ((Get-FileHash -Algorithm SHA256 $settings).Hash -eq $settingsHash) 'settings preserved' }

    Stop-Installed
    Run (Join-Path $root 'unins000.exe') @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART')
    Assert-True (-not (Test-Path $root)) 'default uninstall removes app'
    Assert-True ((Get-FileHash -Algorithm SHA256 $modelFile).Hash -eq $modelHash) 'default uninstall keeps model'
    if ($settingsHash) { Assert-True ((Get-FileHash -Algorithm SHA256 $settings).Hash -eq $settingsHash) 'default uninstall keeps settings' }
    [pscustomobject]@{Status='PASS';Profile=$Profile;Checks=$checks.Count;Results=$checks} | ConvertTo-Json
} finally {
    Stop-Installed
    if (Test-Path (Join-Path $root 'unins000.exe')) {
        Start-Process (Join-Path $root 'unins000.exe') -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait
    }
}
