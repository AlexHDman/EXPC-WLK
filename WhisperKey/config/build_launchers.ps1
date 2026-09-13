$ErrorActionPreference = 'Stop'
$portableRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$release = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'release.json') -Raw | ConvertFrom-Json
if ($release.version -notmatch '^\d+\.\d+\.\d+$') { throw 'Stable X.Y.Z version required for EXE metadata' }
$infoPath = Join-Path $PSScriptRoot 'PortableVersion.generated.cs'
[IO.File]::WriteAllText($infoPath, '[assembly: System.Reflection.AssemblyVersion("' + $release.version + '.0")]')
$icon = Join-Path $portableRoot 'WhisperKey\app\site-packages\whisper_key\platform\windows\assets\whisperkey-icon.ico'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
Push-Location $portableRoot
try {
    & $csc /nologo /target:winexe /optimize+ /win32icon:$icon /reference:System.Windows.Forms.dll /out:WhisperKey\config\EXPC-WLK.new.exe WhisperKey\config\PortableLauncher.cs WhisperKey\config\PortableVersion.generated.cs
    if ($LASTEXITCODE) { throw 'Launcher compilation failed' }
    & $csc /nologo /target:winexe /optimize+ /win32icon:$icon /reference:System.Windows.Forms.dll /reference:System.Management.dll /out:WhisperKey\config\PortableUpdater.exe WhisperKey\config\PortableUpdater.cs WhisperKey\config\PortableVersion.generated.cs
    if ($LASTEXITCODE) { throw 'Updater compilation failed' }
} finally { Pop-Location }
