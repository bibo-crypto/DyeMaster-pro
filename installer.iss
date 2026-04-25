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
; Copy the full PyInstaller onedir output including _internal
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional: bundle VC++ redistributable (place vc_redist.x64.exe next to installer.iss)
Source: "{#ProjectRoot}vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ runtime if bundled
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; \
    Flags: runhidden waituntilterminated skipifsilent; \
    Check: FileExists(ExpandConstant('{tmp}\vc_redist.x64.exe'))

; Launch app after install
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; \
    Flags: nowait postinstall skipifsilent
