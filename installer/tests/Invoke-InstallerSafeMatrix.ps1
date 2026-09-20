[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('cpu','cuda')][string]$Profile)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$upper = $Profile.ToUpperInvariant()
$installer = Join-Path $repoRoot "dist\installer\1.0.0\EXPC-WLK-Setup-$upper-v1.0.0.exe"
$root = Join-Path $env:ProgramFiles 'EXPC-WLK'
$userData = Join-Path $env:APPDATA 'whisperkey'
$models = Join-Path $env:ProgramData 'EXPC-WLK\Models'
$marker = Join-Path $models ".installer-safe-matrix-$Profile"
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$checks = [Collections.Generic.List[string]]::new()

function Assert-True([bool]$condition, [string]$message) {
    if (-not $condition) { throw $message }
    $checks.Add($message)
}
function Run([string]$path, [string[]]$arguments) {
    $p = Start-Process $path -ArgumentList $arguments -Wait -PassThru
    if ($p.ExitCode) { throw "$path returned $($p.ExitCode)" }
}

if (Test-Path $root) { throw "Install root already exists: $root" }
$settings = Join-Path $userData 'user_settings.yaml'
$settingsHash = if (Test-Path $settings) { (Get-FileHash -Algorithm SHA256 $settings).Hash } else { $null }
$oldRun = $null
try { $oldRun = Get-ItemPropertyValue $runKey -Name 'EXPC-WLK' } catch {}
New-Item -ItemType Directory -Path $models -Force | Out-Null
[IO.File]::WriteAllText($marker, 'preserve')

try {
    Run $installer @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/TASKS=desktopicon,autostart')
    Assert-True (Test-Path (Join-Path $root 'EXPC-WLK.exe')) "$upper install layout"
    Assert-True (Test-Path (Join-Path $root 'app\installed_boot.py')) "$upper installed bootstrap"
    Assert-True ((Get-ItemPropertyValue $runKey -Name 'EXPC-WLK') -eq ('"' + (Join-Path $root 'EXPC-WLK.exe') + '"')) "$upper autostart"
    $start = @(
        (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs\EXPC-WLK\EXPC-WLK.lnk'),
        (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\EXPC-WLK\EXPC-WLK.lnk')
    ) | Where-Object { Test-Path $_ }
    $desktop = @((Join-Path $env:PUBLIC 'Desktop\EXPC-WLK.lnk'),
        (Join-Path ([Environment]::GetFolderPath('Desktop')) 'EXPC-WLK.lnk')) | Where-Object { Test-Path $_ }
    Assert-True ($start.Count -eq 1) "$upper Start Menu shortcut"
    Assert-True ($desktop.Count -eq 1) "$upper Desktop shortcut"

    Run $installer @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/TASKS=desktopicon,autostart')
    Assert-True (Test-Path $marker) "$upper in-place upgrade preserves ProgramData"
    if ($settingsHash) { Assert-True ((Get-FileHash -Algorithm SHA256 $settings).Hash -eq $settingsHash) "$upper in-place upgrade preserves settings" }

    Run (Join-Path $root 'unins000.exe') @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART')
    Assert-True (-not (Test-Path $root)) "$upper uninstall removes app"
    Assert-True (Test-Path $marker) "$upper uninstall keeps ProgramData"
    if ($settingsHash) { Assert-True ((Get-FileHash -Algorithm SHA256 $settings).Hash -eq $settingsHash) "$upper uninstall keeps settings" }
    [pscustomobject]@{Status='PASS';Profile=$Profile;Checks=$checks.Count;Results=$checks} | ConvertTo-Json
} finally {
    Remove-Item $marker -Force -ErrorAction SilentlyContinue
    if (Test-Path (Join-Path $root 'unins000.exe')) {
        Start-Process (Join-Path $root 'unins000.exe') -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait
    }
    if ($null -ne $oldRun) {
        New-Item $runKey -Force | Out-Null
        Set-ItemProperty $runKey -Name 'EXPC-WLK' -Value $oldRun
    } else {
        Remove-ItemProperty $runKey -Name 'EXPC-WLK' -ErrorAction SilentlyContinue
    }
}
