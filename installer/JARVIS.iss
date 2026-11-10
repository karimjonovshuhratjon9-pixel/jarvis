#define MyAppName "JARVIS OS V2"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "JARVIS"
#define MyAppExeName "JARVIS.exe"

[Setup]
AppId={{A7B1A4B7-3C7F-4F2D-9A1A-5A22D6B7C901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\JARVIS OS V2
DefaultGroupName=JARVIS OS V2
OutputDir=..\dist\installer
OutputBaseFilename=JARVIS-OS-V2-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\dist\JARVIS\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\JARVIS OS V2"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\JARVIS OS V2"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch JARVIS OS V2"; Flags: postinstall nowait skipifsilent
