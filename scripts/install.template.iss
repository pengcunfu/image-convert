; ===============================================
; Generic Inno Setup Installation Script Template
; Replace placeholders using Python script to generate actual .iss file
; ===============================================

[Setup]
; Installer basic settings
AppId={{__APP_GUID__}}
AppName=__PRODUCT_NAME__
AppVersion=__PRODUCT_VERSION__
AppPublisher=__COMPANY_NAME__
AppPublisherURL=__PRODUCT_WEB_SITE__
AppSupportURL=__PRODUCT_WEB_SITE__
AppUpdatesURL=__PRODUCT_WEB_SITE__
AppCopyright=Copyright (C) __YEAR__ __AUTHOR__

; Default installation directory
DefaultDirName={autopf}\__PRODUCT_NAME__
DefaultGroupName=__PRODUCT_NAME__

; Output files
OutputDir=..\output
OutputBaseFilename=__OUTPUT_FILENAME__-__PRODUCT_VERSION__

; Compression settings
Compression=lzma2/max
SolidCompression=yes

; Installer appearance
WizardStyle=modern

; Privilege requirements
PrivilegesRequired=admin

; Other settings
DisableDirPage=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableFinishedPage=no
AllowNoIcons=yes
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes

; Uninstall settings
UninstallDisplayIcon={app}\__EXE_NAME__
UninstallFilesDir={app}\uninstall
AppendDefaultDirName=yes
AppendDefaultGroupName=yes

; ------------------- Language Settings -------------------

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ------------------- Task Settings -------------------

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create a quick launch icon"; GroupDescription: "Additional icons:"; Flags: unchecked; OnlyBelowVersion: 6.1

; ------------------- File Installation -------------------

[Files]
; Install main program and all dependency files
Source: "..\dist\__DIST_DIR__\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Note: The above flags mean:
; ignoreversion - Overwrite existing files without checking version
; recursesubdirs - Recursively copy all subdirectories
; createallsubdirs - Create all source directory structure in target directory

; ------------------- Shortcuts -------------------

[Icons]
; Start menu shortcut
Name: "{group}\__PRODUCT_NAME__"; Filename: "{app}\__EXE_NAME__"; IconFilename: "{app}\__EXE_NAME__"; Comment: "__DESCRIPTION__"

; Desktop shortcut (based on task selection)
Name: "{autodesktop}\__PRODUCT_NAME__"; Filename: "{app}\__EXE_NAME__"; Tasks: desktopicon; IconFilename: "{app}\__EXE_NAME__"; Comment: "__DESCRIPTION__"

; Quick launch shortcut (based on task selection)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\__PRODUCT_NAME__"; Filename: "{app}\__EXE_NAME__"; Tasks: quicklaunchicon

; ------------------- Registry Settings -------------------

[Registry]
; Create entry in "Add/Remove Programs" (additional information)
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\__EXE_NAME__"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: string; ValueName: "DisplayName"; ValueData: "__PRODUCT_NAME__"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "__PRODUCT_VERSION__"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: string; ValueName: "Publisher"; ValueData: "__COMPANY_NAME__"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "__PRODUCT_WEB_SITE__"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: dword; ValueName: "NoModify"; ValueData: "1"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\__REG_KEY_ID__"; ValueType: dword; ValueName: "NoRepair"; ValueData: "1"; Flags: uninsdeletekey

; Application registry entries (save configuration)
Root: HKCU; Subkey: "Software\__REG_KEY_ID__"; ValueType: string; ValueName: "Install_Dir"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\__REG_KEY_ID__"; ValueType: string; ValueName: "Version"; ValueData: "__PRODUCT_VERSION__"; Flags: uninsdeletekey

; ------------------- Run Settings -------------------

[Run]
; Run program after installation (optional)
Filename: "{app}\__EXE_NAME__"; Description: "Launch __PRODUCT_NAME__"; Flags: nowait postinstall skipifsilent

; ------------------- Uninstall Settings -------------------

[UninstallDelete]
; Delete uninstall directory
Type: filesandordirs; Name: "{app}\uninstall"

; ------------------- Installer Code -------------------

[Code]
// Pre-installation check
function InitializeSetup(): Boolean;
var
  PrevVersion: String;
begin
  Result := True;

  // Check if already installed
  if RegQueryStringValue(HKCU, 'Software\__REG_KEY_ID__', 'Install_Dir', PrevVersion) then
  begin
    if MsgBox('__PRODUCT_NAME__ is already installed.' + #13#10 + #13#10 +
              'Do you want to overwrite the installation?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

// Post-installation prompt
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssDone then
  begin
    // Can add additional post-installation operations here
  end;
end;

// Uninstall confirmation
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Are you sure you want to uninstall __PRODUCT_NAME__ and all its components?',
            mbConfirmation, MB_YESNO) = IDNO then
  begin
    Result := False;
  end;
end;

// Post-installation cleanup
procedure DeinitializeSetup();
begin
  // Operations when installation wizard closes
end;

procedure DeinitializeUninstall();
begin
  // Operations when uninstall wizard closes
end;
