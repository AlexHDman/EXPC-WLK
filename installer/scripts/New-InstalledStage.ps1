[CmdletBinding()]
param(
    [ValidateSet('cpu', 'cuda')]
    [string]$Profile = 'cpu',
    [string]$ArchivePath,
    [string]$StageDir,
    [string]$VersionOverride
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$metadata = & (Join-Path $PSScriptRoot 'Get-InstallerMetadata.ps1') -Profile $Profile
$targetVersion = if ($VersionOverride) { $VersionOverride } else { $metadata.Version }
if ($targetVersion -notmatch '^\d+\.\d+\.\d+$') { throw 'VersionOverride must be X.Y.Z' }
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $repoRoot "dist\$($metadata.Version)\application\$($metadata.ArchiveName)"
}
$archive = (Resolve-Path -LiteralPath $ArchivePath).Path
$sidecar = $archive + '.sha256'
if (-not (Test-Path -LiteralPath $sidecar)) { throw "Missing checksum: $sidecar" }
$expectedHash = ((Get-Content -LiteralPath $sidecar -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
if ($expectedHash -ne $actualHash) { throw 'Portable archive SHA-256 mismatch' }

if (-not $StageDir) {
    $StageDir = Join-Path $repoRoot "installer\work\stage-$Profile-$targetVersion"
}
$stage = [IO.Path]::GetFullPath($StageDir)
if (Test-Path -LiteralPath $stage) { throw "Stage must not already exist: $stage" }
$extract = Join-Path ([IO.Path]::GetTempPath()) ("expc-wlk-installed-stage-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $extract | Out-Null

try {
    Expand-Archive -LiteralPath $archive -DestinationPath $extract
    $portableRoot = $extract
    $portable = Join-Path $portableRoot 'WhisperKey'
    $profileData = Get-Content -LiteralPath (Join-Path $portable 'config\package-profile.json') -Raw | ConvertFrom-Json
    $releaseData = Get-Content -LiteralPath (Join-Path $portable 'config\release.json') -Raw | ConvertFrom-Json
    if ($profileData.variant -ne $Profile) { throw 'Portable archive profile mismatch' }
    if ($releaseData.version -ne $metadata.Version) { throw 'Portable archive version mismatch' }

    $launcher = (& (Join-Path $PSScriptRoot 'Build-InstalledLauncher.ps1') `
        -VersionOverride $targetVersion).FullName
    $updater = (& (Join-Path $PSScriptRoot 'Build-InstalledUpdater.ps1')).FullName
    New-Item -ItemType Directory -Path $stage | Out-Null
    Copy-Item -LiteralPath $launcher -Destination (Join-Path $stage 'EXPC-WLK.exe')
    Copy-Item -LiteralPath (Join-Path $portable 'runtime') -Destination (Join-Path $stage 'runtime') -Recurse
    Copy-Item -LiteralPath (Join-Path $portable 'app') -Destination (Join-Path $stage 'app') -Recurse
    Copy-Item -LiteralPath (Join-Path $repoRoot 'installer\runtime\installed_boot.py') `
        -Destination (Join-Path $stage 'app\installed_boot.py')
    $packageSource = Join-Path $repoRoot 'WhisperKey\app\site-packages\whisper_key'
    $packageTarget = Join-Path $stage 'app\site-packages\whisper_key'
    foreach ($name in @('diagnostics.py', 'model_store.py', 'portable_tray_actions.py',
                         'system_tray.py', 'utils.py', 'installed_updater.py')) {
        Copy-Item -LiteralPath (Join-Path $packageSource $name) -Destination $packageTarget
    }

    $configTarget = Join-Path $stage 'updater\config'
    New-Item -ItemType Directory -Path $configTarget -Force | Out-Null
    foreach ($name in @('release.json', 'package-profile.json', 'model-catalog.json',
                         'model-manifest.json', 'native-model-manifest.json')) {
        Copy-Item -LiteralPath (Join-Path $portable "config\$name") -Destination $configTarget
    }
    Copy-Item -LiteralPath $updater -Destination (Join-Path $stage 'updater\InstalledUpdater.exe')
    $installedReleasePath = Join-Path $configTarget 'release.json'
    $installedRelease = Get-Content -LiteralPath $installedReleasePath -Raw | ConvertFrom-Json
    $installedRelease.version = $targetVersion
    $installedRelease.asset_name = "EXPC-WLK-installed-$($Profile.ToUpperInvariant())-v$targetVersion.zip"
    $installedRelease | Add-Member -NotePropertyName package_variant -NotePropertyValue $Profile -Force
    [IO.File]::WriteAllText($installedReleasePath, ($installedRelease | ConvertTo-Json) + "`n")
    [IO.File]::WriteAllText((Join-Path $stage 'installed-layout.json'),
        (@{ format=1; mode='installed'; version=$targetVersion; profile=$Profile;
            model_root='%ProgramData%\EXPC-WLK\Models';
            user_data_root='%APPDATA%\whisperkey' } | ConvertTo-Json))

    if (Test-Path -LiteralPath (Join-Path $stage 'models')) {
        throw 'Stage unexpectedly contains models'
    }
    Get-Item -LiteralPath $stage
} catch {
    if (Test-Path -LiteralPath $stage) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
    throw
} finally {
    Remove-Item -LiteralPath $extract -Recurse -Force -ErrorAction SilentlyContinue
}
