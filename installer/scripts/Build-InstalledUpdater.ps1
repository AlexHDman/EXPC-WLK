[CmdletBinding()]
param([string]$OutputPath)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $OutputPath) { $OutputPath = Join-Path $repoRoot 'installer\work\InstalledUpdater.exe' }
$output = [IO.Path]::GetFullPath($OutputPath)
$outputDir = Split-Path -Parent $output
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$manifest = Join-Path $outputDir 'InstalledUpdater.manifest'
[IO.File]::WriteAllText($manifest, @'
<?xml version="1.0" encoding="utf-8"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security><requestedPrivileges>
      <requestedExecutionLevel level="requireAdministrator" uiAccess="false" />
    </requestedPrivileges></security>
  </trustInfo>
</assembly>
'@)
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $csc /nologo /target:winexe /optimize+ /win32manifest:$manifest `
    /reference:System.Management.dll /reference:System.dll /out:$output `
    (Join-Path $repoRoot 'installer\runtime\InstalledUpdater.cs')
if ($LASTEXITCODE -ne 0) { throw 'Installed updater compilation failed' }
Get-Item -LiteralPath $output
