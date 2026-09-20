#ifndef SourceDir
  #error SourceDir is required
#endif
#ifndef RepoRoot
  #error RepoRoot is required
#endif
#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef Profile
  #error Profile is required
#endif
#ifndef ProfileLabel
  #error ProfileLabel is required
#endif

#define ProductName "EXPC-WLK"
#define ProductExe "EXPC-WLK.exe"
#define ProductAppId "{{2E801B1E-38AA-47AE-A9CC-AC43AB1E60BA}"

[Setup]
AppId={#ProductAppId}
AppName={#ProductName}
AppVersion={#AppVersion}
AppVerName={#ProductName} {#AppVersion} ({#Profile})
DefaultDirName={autopf}\EXPC-WLK
DefaultGroupName=EXPC-WLK
DisableProgramGroupPage=yes
PrivilegesRequired=admin
UsedUserAreasWarning=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#RepoRoot}\assets\WLKMic.ico
UninstallDisplayIcon={app}\{#ProductExe}
OutputDir={#RepoRoot}\dist\installer\{#AppVersion}
OutputBaseFilename=EXPC-WLK-Setup-{#ProfileLabel}-v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "autostart"; Description: "Start EXPC-WLK with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Dirs]
Name: "{userappdata}\whisperkey"
Name: "{commonappdata}\EXPC-WLK\Models"; Permissions: users-modify

[Files]
Source: "{#SourceDir}\EXPC-WLK.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\updater\*"; DestDir: "{app}\updater"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EXPC-WLK"; Filename: "{app}\{#ProductExe}"
Name: "{autodesktop}\EXPC-WLK"; Filename: "{app}\{#ProductExe}"; Tasks: desktopicon

[UninstallDelete]
Type: filesandordirs; Name: "{app}\app"
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\updater"
Type: dirifempty; Name: "{app}"
Type: filesandordirs; Name: "{userappdata}\whisperkey"; Check: FullCleanupSelected
Type: filesandordirs; Name: "{commonappdata}\EXPC-WLK"; Check: FullCleanupSelected

[Code]
var
  RemoveAllData: Boolean;

function FullCleanupParameter(): Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/FULLCLEANUP') = 0 then
      Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('autostart') then
      RegWriteStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run',
        'EXPC-WLK', '"' + ExpandConstant('{app}\EXPC-WLK.exe') + '"')
    else
      RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'EXPC-WLK');
  end;
end;

function InitializeUninstall(): Boolean;
begin
  if UninstallSilent then
    RemoveAllData := FullCleanupParameter()
  else
    RemoveAllData := MsgBox(
      'Keep EXPC-WLK user settings and downloaded models?' + #13#10 + #13#10 +
      'Choose Yes to keep them (recommended).' + #13#10 +
      'Choose No to remove all settings and models.',
      mbConfirmation, MB_YESNO) = IDNO;
  Result := True;
end;

function FullCleanupSelected(): Boolean;
begin
  Result := RemoveAllData;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'EXPC-WLK');
  if (CurUninstallStep = usPostUninstall) and RemoveAllData then
  begin
    DelTree(ExpandConstant('{userappdata}\whisperkey'), True, True, True);
    DelTree(ExpandConstant('{commonappdata}\EXPC-WLK'), True, True, True);
  end;
end;
