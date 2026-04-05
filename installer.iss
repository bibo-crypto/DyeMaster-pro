#define ProjectRoot AddBackslash(SourcePath)
#define MyAppName "DyeMaster Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "DyeMaster Pro"
#define MyAppExeName "DyeMasterPro.exe"
#define MyDistDir ProjectRoot + "dist\\DyeMasterPro"

[Setup]
AppId={{E2A5D7B8-2F77-49D5-9B7D-5D7E706D4E91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#ProjectRoot}installer_output
OutputBaseFilename=DyeMasterPro_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Files]
; Copy the FULL PyInstaller onedir output, including _internal.
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional: bundle VC++ redistributable next to this script and include it.
; Download and place next to installer.iss as: vc_redist.x64.exe
Source: "{#ProjectRoot}vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ runtime if bundled.
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; \
    Flags: runhidden waituntilterminated skipifsilent; Check: FileExists(ExpandConstant('{tmp}\vc_redist.x64.exe'))

; Launch app after install.
; Note: The app has single-instance protection to prevent database conflicts.
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  SerialPage: TInputQueryWizardPage;
  CustomerSerial: String;

procedure InitializeWizard;
begin
  CustomerSerial := Trim(ExpandConstant('{param:SERIAL|}'));
  SerialPage :=
    CreateInputQueryPage(
      wpSelectTasks,
      'Activation Serial',
      'Enter your activation serial code',
      'Paste the serial from customer_serials.txt exactly as received. Example format: xxxxx.yyyyy'
    );
  SerialPage.Add('Serial Code:', False);
  if CustomerSerial <> '' then
    SerialPage.Values[0] := CustomerSerial;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = SerialPage.ID then
  begin
    if Trim(CustomerSerial) = '' then
      CustomerSerial := Trim(SerialPage.Values[0]);
    if CustomerSerial = '' then
    begin
      MsgBox('Please paste your activation serial code to continue.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LicenseDir: String;
  SerialFile: String;
begin
  if CurStep = ssInstall then
  begin
    LicenseDir := ExpandConstant('{localappdata}\DyeMasterPro\license');
    SerialFile := LicenseDir + '\serial.txt';
    if not DirExists(LicenseDir) then
      ForceDirectories(LicenseDir);
    SaveStringToFile(SerialFile, CustomerSerial, False);
  end;
end;
