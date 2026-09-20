# EXPC-WLK installer architecture (Phase 1)

This folder defines the installed-mode contract for EXPC-WLK v1.x. It does not
alter or rebuild the v1.0.0 portable release.

## Technology

Use **Inno Setup**. It provides a small signed-ready EXE installer, reliable
upgrade/uninstall behavior, native Start Menu/Desktop tasks, and concise Pascal
hooks for the optional full-cleanup prompt. NSIS can do the same but needs more
custom scripting; WiX is stronger for enterprise MSI deployment but adds XML,
toolchain, and upgrade complexity that EXPC-WLK does not currently need.

## Installed-mode contract

```text
%ProgramFiles%\EXPC-WLK\
  EXPC-WLK.exe
  runtime\
  app\
  updater\

%APPDATA%\whisperkey\
  user_settings.yaml
  vocabulary.db
  corrections and language preferences

%ProgramData%\EXPC-WLK\Models\
  small\
  large-v3-turbo\
```

Program Files contains immutable application payload only. Per-user settings
stay in `%APPDATA%`; downloaded models stay in the machine-wide writable model
directory. Models are never embedded in the installer and are not downloaded
during setup.

CPU and CUDA are separate installer builds selected at build time. The selected
portable archive supplies the matching runtime, and its `package-profile.json`
must match the requested profile.

## Upgrade and uninstall

- The stable Inno `AppId` upgrades the existing installation in place.
- Setup never deletes or replaces `%APPDATA%\whisperkey` or the model directory.
- Start Menu shortcut is always installed; Desktop and per-user autostart are
  optional tasks.
- Uninstall keeps settings and models by default. A separate confirmation allows
  full cleanup.

## Installed runtime

Phase 2 adds a separate installed launcher and bootstrap. The stage builder
starts from the checksum-verified CPU portable archive, flattens `runtime` and
`app`, overlays only the installed-path compatibility modules, and keeps model
files out of the payload. `Build-Installer.ps1` rejects a stage without the
installed bootstrap or with a root model directory.

The CPU installer has a repeatable live smoke test covering install, launch,
ProgramData model discovery and ACLs, AppData settings, shortcuts, autostart,
in-place upgrade, keep-data uninstall, and `/FULLCLEANUP` uninstall. CUDA is not
built in Phase 2. The installed updater directory currently carries trusted
metadata only; an installed-mode update transaction is a later phase.

No installer is published by this phase.
