param(
    [Parameter(Mandatory=$true)][string[]]$Files,
    [string]$CertificateThumbprint = $env:EXPC_WLK_SIGNING_THUMBPRINT,
    [string]$TimestampUrl = $(if ($env:EXPC_WLK_TIMESTAMP_URL) { $env:EXPC_WLK_TIMESTAMP_URL } else { 'http://timestamp.digicert.com' })
)
$ErrorActionPreference = 'Stop'
if (-not $CertificateThumbprint) { throw 'Certificate thumbprint is required.' }
$signtool = (Get-Command signtool.exe -ErrorAction Stop).Source
foreach ($file in $Files) {
    $resolved = (Resolve-Path -LiteralPath $file).Path
    & $signtool sign /sha1 $CertificateThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $resolved
    if ($LASTEXITCODE) { throw "Signing failed: $resolved" }
    & $signtool verify /pa /all $resolved
    if ($LASTEXITCODE) { throw "Signature verification failed: $resolved" }
}
