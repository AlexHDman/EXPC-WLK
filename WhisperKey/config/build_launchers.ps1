$ErrorActionPreference = 'Stop'
$portableRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$release = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'release.json') -Raw | ConvertFrom-Json
if ($release.version -notmatch '^\d+\.\d+\.\d+$') { throw 'Stable X.Y.Z version required for EXE metadata' }
$infoPath = Join-Path $PSScriptRoot 'PortableVersion.generated.cs'
[IO.File]::WriteAllText($infoPath, '[assembly: System.Reflection.AssemblyVersion("' + $release.version + '.0")]')
$icon = Join-Path $portableRoot 'WhisperKey\app\site-packages\whisper_key\platform\windows\assets\whisperkey-icon.ico'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$rc = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\rc.exe' |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $rc) { throw 'Windows SDK rc.exe is required to build EXE resources' }

function New-VersionResource([string]$Name, [string]$Description, [string]$Original, [string]$Internal) {
    $rcPath = Join-Path $PSScriptRoot ($Name + '.generated.rc')
    $resPath = Join-Path $PSScriptRoot ($Name + '.generated.res')
    $numeric = $release.version.Replace('.', ',') + ',0'
    $display = $release.version + '.0'
    $escapedIcon = $icon.Replace('\', '\\')
    $lines = @(
        '1 ICON "' + $escapedIcon + '"',
        '1 VERSIONINFO',
        ' FILEVERSION ' + $numeric,
        ' PRODUCTVERSION ' + $numeric,
        ' FILEFLAGSMASK 0x3fL',
        ' FILEFLAGS 0x0L',
        ' FILEOS 0x40004L',
        ' FILETYPE 0x1L',
        'BEGIN',
        '  BLOCK "StringFileInfo"',
        '  BEGIN',
        '    BLOCK "040904b0"',
        '    BEGIN',
        '      VALUE "CompanyName", "EXPC-WLK\0"',
        '      VALUE "FileDescription", "' + $Description + '\0"',
        '      VALUE "FileVersion", "' + $display + '\0"',
        '      VALUE "InternalName", "' + $Internal + '\0"',
        '      VALUE "OriginalFilename", "' + $Original + '\0"',
        '      VALUE "ProductName", "EXPC-WLK\0"',
        '      VALUE "ProductVersion", "' + $display + '\0"',
        '    END',
        '  END',
        '  BLOCK "VarFileInfo"',
        '  BEGIN',
        '    VALUE "Translation", 0x409, 1200',
        '  END',
        'END'
    )
    [IO.File]::WriteAllLines($rcPath, $lines, [Text.Encoding]::Unicode)
    & $rc /nologo /fo $resPath $rcPath
    if ($LASTEXITCODE) { throw "Resource compilation failed: $Name" }
    return $resPath
}

$launcherRes = New-VersionResource 'Launcher' 'EXPC-WLK' 'EXPC-WLK.exe' 'EXPC-WLK'
$updaterRes = New-VersionResource 'Updater' 'EXPC-WLK Updater' 'PortableUpdater.exe' 'EXPC-WLK Updater'
Push-Location $portableRoot
try {
    & $csc /nologo /target:winexe /optimize+ /win32res:$launcherRes /reference:System.Windows.Forms.dll /out:WhisperKey\config\EXPC-WLK.new.exe WhisperKey\config\PortableLauncher.cs WhisperKey\config\PortableVersion.generated.cs
    if ($LASTEXITCODE) { throw 'Launcher compilation failed' }
    & $csc /nologo /target:winexe /optimize+ /win32res:$updaterRes /reference:System.Windows.Forms.dll /reference:System.Management.dll /out:WhisperKey\config\PortableUpdater.exe WhisperKey\config\PortableUpdater.cs WhisperKey\config\PortableVersion.generated.cs
    if ($LASTEXITCODE) { throw 'Updater compilation failed' }
} finally {
    Pop-Location
    Remove-Item -LiteralPath $launcherRes,$updaterRes,
        (Join-Path $PSScriptRoot 'Launcher.generated.rc'),
        (Join-Path $PSScriptRoot 'Updater.generated.rc') -Force -ErrorAction SilentlyContinue
}
