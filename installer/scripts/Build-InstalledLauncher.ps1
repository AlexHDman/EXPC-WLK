[CmdletBinding()]
param(
    [string]$OutputPath,
    [string]$VersionOverride
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$release = Get-Content -LiteralPath (Join-Path $repoRoot 'WhisperKey\config\release.json') -Raw | ConvertFrom-Json
$version = if ($VersionOverride) { $VersionOverride } else { $release.version }
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Stable X.Y.Z version required' }
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoRoot 'installer\work\InstalledLauncher.exe'
}
$output = [IO.Path]::GetFullPath($OutputPath)
$outputDir = Split-Path -Parent $output
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$rc = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\rc.exe' |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not (Test-Path -LiteralPath $csc) -or -not $rc) {
    throw 'Windows .NET compiler and SDK rc.exe are required'
}

$work = Join-Path $outputDir 'launcher-resource'
New-Item -ItemType Directory -Path $work -Force | Out-Null
$versionSource = Join-Path $work 'InstalledVersion.generated.cs'
$rcPath = Join-Path $work 'InstalledLauncher.generated.rc'
$resPath = Join-Path $work 'InstalledLauncher.generated.res'
$icon = (Resolve-Path (Join-Path $repoRoot 'assets\WLKMic.ico')).Path.Replace('\', '\\')
$numeric = $version.Replace('.', ',') + ',0'
$display = $version + '.0'
[IO.File]::WriteAllText($versionSource,
    '[assembly: System.Reflection.AssemblyVersion("' + $display + '")]')
[IO.File]::WriteAllLines($rcPath, @(
    '1 ICON "' + $icon + '"',
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
    '      VALUE "FileDescription", "EXPC-WLK installed launcher\0"',
    '      VALUE "FileVersion", "' + $display + '\0"',
    '      VALUE "OriginalFilename", "EXPC-WLK.exe\0"',
    '      VALUE "ProductName", "EXPC-WLK\0"',
    '      VALUE "ProductVersion", "' + $display + '\0"',
    '    END',
    '  END',
    '  BLOCK "VarFileInfo"',
    '  BEGIN',
    '    VALUE "Translation", 0x409, 1200',
    '  END',
    'END'
), [Text.Encoding]::Unicode)

& $rc /nologo /fo $resPath $rcPath
if ($LASTEXITCODE -ne 0) { throw 'Installed launcher resource compilation failed' }
& $csc /nologo /target:winexe /optimize+ /win32res:$resPath `
    /reference:System.Windows.Forms.dll /out:$output `
    (Join-Path $repoRoot 'installer\runtime\InstalledLauncher.cs') $versionSource
if ($LASTEXITCODE -ne 0) { throw 'Installed launcher compilation failed' }

Get-Item -LiteralPath $output
