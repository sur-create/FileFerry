#ifndef MyAppVersion
#define MyAppVersion "1.1.0"
#endif

#define MyAppName "FileFerry"
#define MyAppPublisher "FileFerry Team"
#define MyAppExeName "fileferry-gui.exe"
#define MyAppCliExeName "fileferry.exe"

[Setup]
AppId={{A0F8C53B-74E0-4FF7-ACD8-4D2E30339FCE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FileFerry
DefaultGroupName=FileFerry
DisableProgramGroupPage=yes
OutputDir=..\..\dist\installer
OutputBaseFilename=FileFerry-{#MyAppVersion}-windows-x64-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcuts"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\..\dist\fileferry\*"; DestDir: "{app}\cli"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\dist\fileferry-gui\*"; DestDir: "{app}\gui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "fileferry-send.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "fileferry-recv.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\FileFerry\FileFerry"; Filename: "{app}\gui\{#MyAppExeName}"; WorkingDir: "{app}\gui"
Name: "{autoprograms}\FileFerry\FileFerry Help (CLI)"; Filename: "{cmd}"; Parameters: "/k ""{app}\cli\{#MyAppCliExeName}"" --help"; WorkingDir: "{app}"
Name: "{autoprograms}\FileFerry\FileFerry Send (CLI)"; Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry-send.bat"""; WorkingDir: "{app}"
Name: "{autoprograms}\FileFerry\FileFerry Receive (CLI)"; Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry-recv.bat"""; WorkingDir: "{app}"
Name: "{autodesktop}\FileFerry"; Filename: "{app}\gui\{#MyAppExeName}"; WorkingDir: "{app}\gui"; Tasks: desktopicon

[Run]
Filename: "{app}\gui\{#MyAppExeName}"; Description: "Launch FileFerry desktop app"; Flags: nowait postinstall skipifsilent
