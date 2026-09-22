# EXPC-WLK v1.0.2

Stabilization release before dictionary/GVP work.

- Fresh configurations now use hold `Ctrl+Win` push-to-talk by default; release
  stops recording immediately and starts transcription.
- Fixed installed autostart so the selected setup task creates the real per-user
  HKCU Run entry, while unchecked setup and uninstall remove it.
- Installer language now follows Windows UI language: Russian for Russian Windows,
  English otherwise.
- Added offline import of existing `small` and `large-v3-turbo` model directories
  from portable, installed, removable, Desktop, or arbitrary local locations.
- Imported models are checked against pinned file sizes and SHA-256, copied
  atomically to `%ProgramData%\EXPC-WLK\Models`, and registered without deleting
  the source.
- Preserved CUDA FP16, CPU INT8 fallback, updater rollback/Ready handshake,
  notifications, benchmark, clipboard/paste, RU/EN tray UI, and portable mode.

Models remain separate from all distributables. Builds are unsigned and Windows
SmartScreen may show a warning.
