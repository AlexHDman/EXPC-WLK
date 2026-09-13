# Code signing

Development builds of EXPC-WLK are unsigned and may trigger Microsoft SmartScreen.
Production signing is optional and requires a trusted Authenticode certificate held
outside this repository.

Build the final launcher, updater and installer first. Sign those exact binaries
before creating checksums or publishing a release:

```powershell
$env:EXPC_WLK_SIGNING_THUMBPRINT = '<certificate thumbprint>'
$env:EXPC_WLK_TIMESTAMP_URL = 'http://timestamp.digicert.com'
.\WhisperKey\config\sign_release.ps1 -Files .\EXPC-WLK.exe,.\WhisperKey\config\PortableUpdater.exe
```

The script uses SHA-256, an RFC 3161 timestamp and `signtool verify /pa`. It does
not read or store private keys, passwords or tokens. The certificate remains in
the Windows certificate store or external signing service configured by the
release operator.
