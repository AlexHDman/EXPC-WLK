[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('cpu', 'cuda')]
    [string]$Profile
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$layoutPath = Join-Path $repoRoot 'installer\config\installer-layout.json'
$releasePath = Join-Path $repoRoot 'WhisperKey\config\release.json'
$layout = Get-Content -LiteralPath $layoutPath -Raw | ConvertFrom-Json
$release = Get-Content -LiteralPath $releasePath -Raw | ConvertFrom-Json

if ($release.version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Invalid semantic version in release.json: $($release.version)"
}
if ($layout.download_models_during_install -ne $false) {
    throw 'Installer must not download models during setup.'
}

$archivePattern = $layout.profiles.$Profile
if (-not $archivePattern) {
    throw "No archive mapping for profile: $Profile"
}
$archiveName = $archivePattern.Replace('{version}', $release.version)

[pscustomobject]@{
    Product = $layout.product
    Version = $release.version
    Profile = $Profile
    ArchiveName = $archiveName
    AppId = $layout.app_id
    InstallRoot = $layout.install_root
    UserDataRoot = $layout.user_data_root
    ModelRoot = $layout.model_root
    IconPath = (Join-Path $repoRoot $layout.icon_source.Replace('/', '\'))
    RepoRoot = $repoRoot
}
