[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('cpu', 'cuda')]
    [string]$Profile,

    [Parameter(Mandatory)]
    [string]$StageDir,

    [string]$IsccPath = 'ISCC.exe'
)

$ErrorActionPreference = 'Stop'
$metadata = & (Join-Path $PSScriptRoot 'Get-InstallerMetadata.ps1') -Profile $Profile
$stage = (Resolve-Path -LiteralPath $StageDir).Path

foreach ($required in @('EXPC-WLK.exe', 'runtime', 'app', 'updater')) {
    if (-not (Test-Path -LiteralPath (Join-Path $stage $required))) {
        throw "Installed-mode stage is incomplete: missing $required"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $stage 'app\installed_boot.py'))) {
    throw 'Installed-mode bootstrap is missing; refusing to package the portable bootstrap.'
}
if (Test-Path -LiteralPath (Join-Path $stage 'models')) {
    throw 'Models must not be stored in the installer payload.'
}

$stageRelease = Get-Content -LiteralPath (Join-Path $stage 'updater\config\release.json') -Raw | ConvertFrom-Json
$stageProfile = Get-Content -LiteralPath (Join-Path $stage 'updater\config\package-profile.json') -Raw | ConvertFrom-Json
if ($stageRelease.version -ne $metadata.Version) {
    throw "Stage version $($stageRelease.version) does not match $($metadata.Version)."
}
if ($stageProfile.variant -ne $Profile) {
    throw "Stage profile $($stageProfile.variant) does not match $Profile."
}

$iscc = Get-Command $IsccPath -ErrorAction SilentlyContinue
if (-not $iscc) {
    throw 'Inno Setup compiler (ISCC.exe) is not installed or was not provided.'
}

$script = Join-Path $metadata.RepoRoot 'installer\inno\EXPC-WLK.iss'
& $iscc.Source /Qp "/DSourceDir=$stage" "/DRepoRoot=$($metadata.RepoRoot)" `
    "/DAppVersion=$($metadata.Version)" "/DProfile=$Profile" `
    "/DProfileLabel=$($Profile.ToUpperInvariant())" $script
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}
