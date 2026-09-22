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
#define ProductDisplayName "EXPC WhisperKey Local (EXPC-WLK)"
#define ProductExe "EXPC-WLK.exe"
#define ProductAppId "{{2E801B1E-38AA-47AE-A9CC-AC43AB1E60BA}"

[Setup]
AppId={#ProductAppId}
AppName={#ProductDisplayName}
AppVersion={#AppVersion}
AppVerName={#ProductDisplayName} {#AppVersion} ({#Profile})
AppPublisher=EXPC
AppPublisherURL=https://github.com/AlexHDman/EXPC-WLK
VersionInfoCompany=EXPC
VersionInfoDescription=EXPC WhisperKey Local Installer
VersionInfoProductName=EXPC-WLK
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
DisableWelcomePage=no
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
english.AdditionalShortcuts=Additional shortcuts:
russian.AdditionalShortcuts=Дополнительные ярлыки:
english.DesktopTask=Create a Desktop shortcut
russian.DesktopTask=Создать ярлык на рабочем столе
english.StartupGroup=Startup:
russian.StartupGroup=Автозапуск:
english.AutostartTask=Start EXPC-WLK with Windows
russian.AutostartTask=Запускать EXPC-WLK вместе с Windows
english.KeepDataPrompt=Keep EXPC-WLK user settings and downloaded models?%n%nChoose Yes to keep them (recommended).%nChoose No to remove all settings and models.%n%nDesign by EXPC
russian.KeepDataPrompt=Сохранить настройки EXPC-WLK и загруженные модели?%n%nНажмите «Да», чтобы сохранить их (рекомендуется).%nНажмите «Нет», чтобы удалить настройки и модели.%n%nDesign by EXPC

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopTask}"; GroupDescription: "{cm:AdditionalShortcuts}"; Flags: unchecked
Name: "autostart"; Description: "{cm:AutostartTask}"; GroupDescription: "{cm:StartupGroup}"; Flags: unchecked

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

[Run]
Filename: "{app}\{#ProductExe}"; Parameters: "--enable-autostart --quiet"; Flags: runhidden waituntilterminated runasoriginaluser; Check: AutostartSelected
Filename: "{app}\{#ProductExe}"; Parameters: "--disable-autostart --quiet"; Flags: runhidden waituntilterminated runasoriginaluser; Check: AutostartNotSelected

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

function AutostartSelected(): Boolean;
begin
  Result := WizardIsTaskSelected('autostart');
end;

function AutostartNotSelected(): Boolean;
begin
  Result := not WizardIsTaskSelected('autostart');
end;

function InitializeUninstall(): Boolean;
begin
  if UninstallSilent then
    RemoveAllData := FullCleanupParameter()
  else
    RemoveAllData := MsgBox(CustomMessage('KeepDataPrompt'), mbConfirmation, MB_YESNO) = IDNO;
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
