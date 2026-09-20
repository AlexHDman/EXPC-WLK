[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$layoutPath = Join-Path $repoRoot 'installer\config\installer-layout.json'
$issPath = Join-Path $repoRoot 'installer\inno\EXPC-WLK.iss'
$layout = Get-Content -LiteralPath $layoutPath -Raw | ConvertFrom-Json
$release = Get-Content -LiteralPath (Join-Path $repoRoot 'WhisperKey\config\release.json') -Raw | ConvertFrom-Json
$iss = Get-Content -LiteralPath $issPath -Raw
$checks = [System.Collections.Generic.List[string]]::new()

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
    $checks.Add($Message)
}

Assert-True ($layout.install_root -eq '{autopf}/EXPC-WLK') 'Program Files install root'
Assert-True ($layout.user_data_root -eq '{userappdata}/whisperkey') 'Per-user data root'
Assert-True ($layout.model_root -eq '{commonappdata}/EXPC-WLK/Models') 'Machine-wide model root'
Assert-True ($layout.download_models_during_install -eq $false) 'No model download during setup'
Assert-True (($layout.payload -join ',') -eq 'EXPC-WLK.exe,runtime,app,updater') 'Installed payload layout'
Assert-True ($layout.profiles.cpu -match 'CPU') 'CPU profile mapping'
Assert-True ($layout.profiles.cuda -match 'CUDA') 'CUDA profile mapping'
Assert-True (Test-Path -LiteralPath (Join-Path $repoRoot 'assets\WLKMic.ico')) 'Installer icon exists'
Assert-True ($iss.Contains('Flags: unchecked') -and $iss.Contains('desktopicon')) 'Optional Desktop shortcut'
Assert-True ($iss.Contains("WizardIsTaskSelected('autostart')")) 'Optional autostart reconciliation'
Assert-True ($iss.Contains('Check: FullCleanupSelected')) 'Optional full cleanup'
Assert-True ($iss.Contains('{commonappdata}\EXPC-WLK\Models')) 'ProgramData model directory'
Assert-True (-not $iss.Contains('DownloadTemporaryFile')) 'No installer model download code'
Assert-True (Test-Path -LiteralPath (Join-Path $repoRoot 'installer\runtime\installed_boot.py')) 'Installed bootstrap source'
Assert-True (Test-Path -LiteralPath (Join-Path $repoRoot 'installer\runtime\InstalledLauncher.cs')) 'Installed launcher source'
Assert-True ($iss.Contains('EXPC-WLK-Setup-{#ProfileLabel}-v{#AppVersion}')) 'Installer filename contract'

foreach ($profile in @('cpu', 'cuda')) {
    $metadata = & (Join-Path $repoRoot 'installer\scripts\Get-InstallerMetadata.ps1') -Profile $profile
    $escapedVersion = [regex]::Escape($release.version)
    Assert-True ($metadata.Version -eq $release.version) "$profile version from release.json"
    Assert-True ($metadata.ArchiveName -match "-$($profile.ToUpper())-v$escapedVersion\.zip$") "$profile archive selection"
}

[pscustomobject]@{
    Status = 'PASS'
    Checks = $checks.Count
    Version = $release.version
    Profiles = @('cpu', 'cuda')
} | ConvertTo-Json
