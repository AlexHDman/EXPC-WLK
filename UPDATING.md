# EXPC-WLK localization and portable updates

## UI language

`WhisperKey/app/site-packages/whisper_key/tray_i18n.py` contains RU/EN strings.
`system_tray.language` in `%APPDATA%/whisperkey/user_settings.yaml` accepts
`auto`, `ru`, `en`. Auto uses the Windows user UI language (Russian -> ru,
otherwise en). The tray Language submenu applies immediately. Startup tooltips
also read the preference. Saving the preference round-trips YAML and changes
only this field; STT hotwords/corrections are not edited. Device/model names
remain their original names.

## Canonical EXPC-WLK version and release source

`WhisperKey/config/release.json` is the canonical portable product version:

```json
{"version":"0.9.2","repository":"AlexHDman/EXPC-WLK","asset_name":"EXPC-WLK-portable.zip"}
```

The existing upstream WhisperKey package metadata remains upstream metadata.
`build_launchers.ps1` generates EXE assembly version metadata from release.json.
It produces config/EXPC-WLK.new.exe and config/PortableUpdater.exe. Replace the
root launcher with the built new EXE only while it is stopped. The build script
requires .NET Framework's compiler on the build PC, never on the destination PC.

The official source is pinned to `AlexHDman/EXPC-WLK`. Manual checks do not run
during startup, and network failure does not affect transcription. There is no
scheduled check, terminology resolver, or R2 learning.

## GitHub connection required later

1. Keep the official `owner/repository` in release.json synchronized with each
   release build.
2. Use published, non-draft, non-prerelease `vMAJOR.MINOR.PATCH` tags.
3. Attach exactly `EXPC-WLK-portable.zip` (or the configured asset_name).
4. GitHub's release asset `digest` must contain `sha256:<64 hex digits>`.
   Missing digests are rejected. Only the pinned repository's exact release
   download URL is accepted. HTTPS download redirects are restricted to GitHub
   asset hosts. Signed provenance/metadata is not implemented; SHA-256 checks
   integrity and does not independently protect against a compromised publisher.
5. Include the same version in the package's release.json. Updates retain the
   installed official repository pin.

Metadata API: `https://api.github.com/repos/{owner}/{repo}/releases/latest`.
See [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
and [release asset digest](https://docs.github.com/en/rest/releases/assets).
No repository, release, installer or publishing pipeline was created.

## Update ZIP contract (complete application, not a delta)

The initial-install download is `EXPC-WLK-portable-v0.9.0.zip`; it contains the
application and runtime, without model files. The updater uses the fixed-name
`EXPC-WLK-portable.zip` asset, also without models. Each has a SHA-256 checksum.
Build with `WhisperKey/config/build_release.py --kind full` or `--kind update`
using the bundled Python, after running `build_launchers.ps1`.

## Independent model storage

`WhisperKey/config/model-catalog.json` pins `small` and `large-v3-turbo` by public
Hugging Face repository, exact 40-character commit, required files, exact sizes
and SHA-256. Production downloads never request `main` or `latest`.

At first use, `model_store.py` verifies the complete local snapshot. A missing or
invalid model triggers confirmation, then every required file is downloaded into
a same-volume staging directory. Only a complete verified snapshot is atomically
installed under `WhisperKey/models/<model-id>`. Network interruption, size/hash
mismatch or install failure leaves the previous target untouched or restores it.
Each installed model contains `.installed-model.json` with its repository,
revision, runtime compatibility and deterministic manifest hash.

Runtime loading receives only the resolved local directory. Valid installed
models make no network request and do not consult Hugging Face cache, including
with `HF_HUB_OFFLINE=1` or after moving the portable folder. Download status
appears in the tray tooltip. Application updates preserve `WhisperKey/models`;
model files are not Release assets and their lifecycle is independent.

The ZIP has no enclosing EXPC-WLK directory. Allowed entries:

- `EXPC-WLK.exe`, optional `README.md`;
- `WhisperKey/app/**` — complete application/dependency tree;
- `WhisperKey/runtime/**` — complete runtime;
- `WhisperKey/config/**` — including release.json and PortableUpdater.exe.

Required: launcher, runtime/pythonw.exe, runtime/python312.dll,
app/portable_boot.py, config/release.json, config/model-catalog.json,
config/PortableUpdater.exe.
Do not include models, logs, user_settings.yaml, commands.yaml or databases.
The stage validator rejects those user-data names, absolute/traversal paths,
Windows device names, links and case-insensitive duplicate files.
Archive size, expanded size and file count are bounded.

## Transaction

1. Manual check runs in a background thread. Stable semantic versions are
   compared; identical/older releases do not install. Offline failure produces
   a localized notification and does not change the engine state.
2. User confirms download. A unique `.EXPC-WLK-update-*` directory is created
   beside the portable root. Download size, SHA-256, ZIP paths and embedded
   version are verified before extracting.
3. User confirms application restart. The current trusted PortableUpdater.exe
   is copied outside the live root and launched; it waits for BOTH the current
   launcher and Python child to exit. A mutex blocks competing launches/updates.
4. The helper copies preserved files, including models/logs, into the complete
   stage. It refuses reparse points. This needs free disk space for the package
   and preserved files. Any copy failure leaves the installation untouched.
5. Rename the old root to `<root>.previous-<transaction>` and stage to the
   original root. The autostart path and external shortcuts remain unchanged.
6. Launch the new EXE. The tray sends a transaction-specific Ready receipt after
   normal initialization. The helper waits up to 120 seconds. On success it
   removes the previous snapshot. Small transaction logs/helper files remain
   in `.EXPC-WLK-update-*` for diagnosis; they may be removed after the helper
   exits and success is confirmed.
7. Replacement/startup failure restores the previous complete folder and starts
   it. A failed new installation is retained as `<root>.failed-<transaction>`
   so its logs are not lost. Cleanup failure retains the snapshot and is logged.

`%APPDATA%/whisperkey` is never part of a transaction or installation target.
Models and portable logs are preserved. No HKCU values are changed by updating.
Temporary prior-version copies are permitted only for update rollback, as
explicitly authorized for this task. External X: recovery storage is untouched.

## Recovery

For ordinary errors the helper rolls back automatically. Inspect
`.EXPC-WLK-update-*/transaction.log` before manual action.
Power loss between the two directory renames, forced helper termination, or
external file locks may require manual recovery; a durable transaction service
is not claimed. A startup slower than 120 seconds also triggers rollback.

Before manual recovery, stop only this portable application's launcher/Python
and updater. Identify the exact transaction's `.previous-*` folder and failed
root in its log. Preserve failed-version logs. Rename the failed root aside
if present, then rename that exact `.previous-*` to the original root and run
EXPC-WLK.exe. Do not merge runtime directories or overwrite AppData settings.
Do not restore all external backups. Access to X: still needs explicit approval.

## Scope of verification

See LOCALIZATION_UPDATE_TEST_RESULTS.md. No real GitHub release was installed;
GitHub metadata/package checks use controlled fixtures, and native installer
success/rollback use small executable fixtures in paths with spaces. Current
CUDA STT and R1 OFF/ON were tested separately with the bundled speech sample.
