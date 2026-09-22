[CmdletBinding()]
param(
    [string]$InstallerPath = 'dist\installer\1.0.2\EXPC-WLK-Setup-CPU-v1.0.2.exe'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$installer = (Resolve-Path -LiteralPath (Join-Path $repoRoot $InstallerPath)).Path
$stage102 = (Resolve-Path (Join-Path $repoRoot 'installer\work\stage-cpu-1.0.2')).Path
$installRoot = Join-Path $env:ProgramFiles 'EXPC-WLK'
$userData = Join-Path $env:APPDATA 'whisperkey'
$programDataRoot = Join-Path $env:PROGRAMDATA 'EXPC-WLK'
$models = Join-Path $programDataRoot 'Models'
$work = Join-Path $repoRoot 'installer\work\live-smoke-1.0.2-cpu'
$backup = Join-Path $work 'backup'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$valueName = 'EXPC-WLK'
$checks = [System.Collections.Generic.List[string]]::new()
$portableWasRunning = $false

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
    $checks.Add($Message)
}

function Run-Process([string]$Path, [string[]]$Arguments, [int]$Expected = 0) {
    $process = Start-Process -FilePath $Path -ArgumentList $Arguments -Wait -PassThru
    if ($process.ExitCode -ne $Expected) { throw "$Path returned $($process.ExitCode), expected $Expected" }
}

function Invoke-Update {
    $token = [guid]::NewGuid().ToString('N')
    $receipt = Join-Path $userData ("installed-update-ready-$token.json")
    $helper = Join-Path $work ("InstalledUpdater-$token.exe")
    Copy-Item -LiteralPath (Join-Path $installRoot 'updater\InstalledUpdater.exe') -Destination $helper
    Run-Process $helper @(
        ('"' + $installRoot + '"'), ('"' + $stage102 + '"'), ('"' + $receipt + '"'),
        '0', '0', $token, '--quiet', '--keep-stage', '--test-instance'
    )
}

function Find-Uninstaller {
    $path = Join-Path $installRoot 'unins000.exe'
    if (-not (Test-Path -LiteralPath $path)) { throw 'Inno uninstaller is missing' }
    return $path
}

function Stop-EXPCProcesses([string]$PathPrefix) {
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($PathPrefix, [StringComparison]::OrdinalIgnoreCase) -and
        $_.Name -in @('EXPC-WLK.exe', 'pythonw.exe')
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if (Test-Path -LiteralPath $installRoot) { throw "Install target already exists: $installRoot" }
if (Test-Path -LiteralPath $work) { throw "Smoke work directory already exists: $work" }
New-Item -ItemType Directory -Path $backup -Force | Out-Null

$originalUserData = Test-Path -LiteralPath $userData
$originalProgramData = Test-Path -LiteralPath $programDataRoot
$originalRunValue = $null
try { $originalRunValue = Get-ItemPropertyValue -LiteralPath $runKey -Name $valueName } catch {}
$portableWasRunning = [bool](Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($repoRoot, [StringComparison]::OrdinalIgnoreCase) -and
    $_.Name -in @('EXPC-WLK.exe', 'pythonw.exe')
})

if ($originalUserData) {
    Copy-Item -LiteralPath $userData -Destination (Join-Path $backup 'user-data') -Recurse
}
if ($originalProgramData) {
    Copy-Item -LiteralPath $programDataRoot -Destination (Join-Path $backup 'program-data') -Recurse
}
[IO.File]::WriteAllText((Join-Path $backup 'original-state.json'),
    (@{ user_data=$originalUserData; program_data=$originalProgramData;
        run_value=$originalRunValue } | ConvertTo-Json))

if (Test-Path -LiteralPath $userData) { Remove-Item -LiteralPath $userData -Recurse -Force }
if (Test-Path -LiteralPath $programDataRoot) { Remove-Item -LiteralPath $programDataRoot -Recurse -Force }

try {
    New-Item -ItemType Directory -Path $userData -Force | Out-Null
    $marker = Join-Path $userData '.installer-phase2-preserve'
    [IO.File]::WriteAllText($marker, 'preserve')

    Run-Process $installer @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
        '/TASKS=desktopicon,autostart', "/LOG=$(Join-Path $work 'install.log')")
    Assert-True (Test-Path -LiteralPath (Join-Path $installRoot 'EXPC-WLK.exe')) 'install layout'
    Assert-True (Test-Path -LiteralPath (Join-Path $installRoot 'runtime\python.exe')) 'installed runtime'
    Assert-True (Test-Path -LiteralPath (Join-Path $installRoot 'app\installed_boot.py')) 'installed bootstrap'
    Assert-True (Test-Path -LiteralPath (Join-Path $installRoot 'updater\config\release.json')) 'installed metadata'
    Assert-True (Test-Path -LiteralPath $marker) 'settings preserved on install'

    $usersSid = [Security.Principal.SecurityIdentifier]::new(
        [Security.Principal.WellKnownSidType]::BuiltinUsersSid, $null)
    $acl = Get-Acl -LiteralPath $models
    $usersModify = $acl.Access | Where-Object {
        try { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]) -eq $usersSid -and
              ($_.FileSystemRights -band [Security.AccessControl.FileSystemRights]::Modify) } catch { $false }
    }
    Assert-True ([bool]$usersModify) 'normal Users have Modify permission on ProgramData models'

    $import = & (Join-Path $installRoot 'runtime\python.exe') -I `
        (Join-Path $repoRoot 'installer\tests\installed_model_import_smoke.py') `
        --metadata-root (Join-Path $installRoot 'updater') --model-root $models `
        --source (Join-Path $repoRoot 'WhisperKey\models\small') --model small | ConvertFrom-Json
    Assert-True ($import.status -eq 'valid' -and $import.copied -and
        $import.source_unchanged -and $import.metadata) 'offline small model import'
    $selftest = & (Join-Path $installRoot 'runtime\python.exe') -I `
        (Join-Path $installRoot 'app\installed_boot.py') --selftest | ConvertFrom-Json
    Assert-True ($selftest.mode -eq 'installed') 'installed bootstrap mode'
    Assert-True ($selftest.variant -eq 'cpu') 'CPU profile discovery'
    Assert-True ($selftest.small_status -eq 'valid') 'ProgramData model discovery'
    Assert-True ($selftest.settings -eq $userData) 'AppData settings path'

    $startMenu = @(
        (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs\EXPC-WLK\EXPC-WLK.lnk'),
        (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\EXPC-WLK\EXPC-WLK.lnk')
    ) | Where-Object { Test-Path -LiteralPath $_ }
    $desktop = @(
        (Join-Path $env:PUBLIC 'Desktop\EXPC-WLK.lnk'),
        (Join-Path ([Environment]::GetFolderPath('Desktop')) 'EXPC-WLK.lnk')
    ) | Where-Object { Test-Path -LiteralPath $_ }
    Assert-True ($startMenu.Count -eq 1) 'Start Menu shortcut'
    Assert-True ($desktop.Count -eq 1) 'optional Desktop shortcut'
    $runValue = Get-ItemPropertyValue -LiteralPath $runKey -Name $valueName
    Assert-True ($runValue -eq ('"' + (Join-Path $installRoot 'EXPC-WLK.exe') + '"')) 'optional autostart'

    Stop-EXPCProcesses $repoRoot
    Start-Sleep -Seconds 1
    $readyToken = [guid]::NewGuid().ToString('N')
    $readyReceipt = Join-Path $userData ("installed-update-ready-$readyToken.json")
    Start-Process -FilePath (Join-Path $installRoot 'EXPC-WLK.exe') -ArgumentList @(
        '--installed-update-token', $readyToken,
        '--installed-update-receipt', ('"' + $readyReceipt + '"'), '--test'
    )
    $readyDeadline = [DateTime]::UtcNow.AddSeconds(90)
    while ([DateTime]::UtcNow -lt $readyDeadline -and -not (Test-Path -LiteralPath $readyReceipt)) {
        Start-Sleep -Milliseconds 250
    }
    Assert-True (Test-Path -LiteralPath $readyReceipt) 'CPU installed Ready receipt'
    $ready = Get-Content -LiteralPath $readyReceipt -Raw | ConvertFrom-Json
    Assert-True ($ready.format -eq 1 -and $ready.state -eq 'ready' -and
        $ready.token -eq $readyToken) 'CPU structured Ready state'
    Remove-Item -LiteralPath $readyReceipt -Force
    Assert-True ((Get-Content -LiteralPath (Join-Path $userData 'user_settings.yaml') -Raw) -match
        'recording_mode:\s*push_to_talk') 'fresh installed config defaults to push-to-talk'
    Stop-EXPCProcesses $installRoot
    Start-Sleep -Seconds 1

    Start-Process -FilePath (Join-Path $installRoot 'EXPC-WLK.exe') -ArgumentList '--test'
    Start-Sleep -Seconds 10
    $installedPython = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'pythonw.exe' -and $_.ExecutablePath -and
        $_.ExecutablePath.StartsWith($installRoot, [StringComparison]::OrdinalIgnoreCase)
    }
    Assert-True ([bool]$installedPython) 'installed launcher starts installed runtime'
    Stop-EXPCProcesses $installRoot
    Start-Sleep -Seconds 1

    Invoke-Update
    $release102 = Get-Content -LiteralPath (Join-Path $installRoot 'updater\config\release.json') -Raw | ConvertFrom-Json
    Assert-True ($release102.version -eq '1.0.2') 'CPU installed update transaction v1.0.2'
    Assert-True (Test-Path -LiteralPath $marker) 'CPU updater preserves AppData settings'
    Assert-True (Test-Path -LiteralPath (Join-Path $models 'small\model.bin')) 'CPU updater preserves ProgramData model'
    Stop-EXPCProcesses $installRoot
    Start-Sleep -Seconds 1

    Run-Process $installer @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
        '/TASKS=desktopicon,autostart', "/LOG=$(Join-Path $work 'upgrade.log')")
    Assert-True (Test-Path -LiteralPath $marker) 'settings preserved on in-place upgrade'
    Assert-True (Test-Path -LiteralPath (Join-Path $models 'small\model.bin')) 'models preserved on in-place upgrade'

    Run-Process (Find-Uninstaller) @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART')
    Assert-True (-not (Test-Path -LiteralPath $installRoot)) 'uninstall removes application'
    Assert-True (Test-Path -LiteralPath $marker) 'default uninstall keeps settings'
    Assert-True (Test-Path -LiteralPath (Join-Path $models 'small\model.bin')) 'default uninstall keeps models'

    Run-Process $installer @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/TASKS=',
        "/LOG=$(Join-Path $work 'cleanup-install.log')")
    $uncheckedRunValue = $null
    try { $uncheckedRunValue = Get-ItemPropertyValue -LiteralPath $runKey -Name $valueName } catch {}
    Assert-True ($null -eq $uncheckedRunValue) 'unchecked setup removes autostart'
    Run-Process (Find-Uninstaller) @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/FULLCLEANUP')
    Assert-True (-not (Test-Path -LiteralPath $installRoot)) 'full-cleanup uninstall removes application'
    Assert-True (-not (Test-Path -LiteralPath $userData)) 'full cleanup removes settings'
    Assert-True (-not (Test-Path -LiteralPath $programDataRoot)) 'full cleanup removes models'

    [pscustomobject]@{ Status='PASS'; Checks=$checks.Count; Results=$checks } | ConvertTo-Json
} finally {
    Stop-EXPCProcesses $installRoot
    Stop-EXPCProcesses $repoRoot
    if ((Test-Path -LiteralPath $work) -and (Test-Path -LiteralPath $userData)) {
        Copy-Item -LiteralPath $userData -Destination (Join-Path $work 'captured-user-data') -Recurse -Force
    }
    if (Test-Path -LiteralPath $installRoot) {
        $uninstaller = Join-Path $installRoot 'unins000.exe'
        if (Test-Path -LiteralPath $uninstaller) {
            Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait
        }
    }
    try {
        if (Test-Path -LiteralPath $userData) { Remove-Item -LiteralPath $userData -Recurse -Force }
        if ($originalUserData) { Copy-Item -LiteralPath (Join-Path $backup 'user-data') -Destination $userData -Recurse }
    } catch { Write-Warning "User data restore failed: $_" }
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
        Set-ItemProperty -LiteralPath $runKey -Name $valueName -Value $originalRunValue
    } else {
        Remove-ItemProperty -LiteralPath $runKey -Name $valueName -ErrorAction SilentlyContinue
    }
    if ($portableWasRunning -and -not (Get-Process EXPC-WLK -ErrorAction SilentlyContinue)) {
        Start-Process -FilePath (Join-Path $repoRoot 'EXPC-WLK.exe')
    }
}
