#ifndef MyAppVersion
#define MyAppVersion "1.1.0"
#endif

#define MyAppName "FileFerry"
#define MyAppPublisher "FileFerry Team"
#define MyAppExeName "fileferry.exe"

[Setup]
AppId={{A0F8C53B-74E0-4FF7-ACD8-4D2E30339FCE}
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
Source: "..\..\dist\fileferry\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "fileferry-send.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "fileferry-recv.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\FileFerry\FileFerry Help"; Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry.exe"" --help"; WorkingDir: "{app}"
Name: "{autoprograms}\FileFerry\FileFerry Send"; Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry-send.bat"""; WorkingDir: "{app}"
Name: "{autoprograms}\FileFerry\FileFerry Receive"; Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry-recv.bat"""; WorkingDir: "{app}"
Name: "{autodesktop}\FileFerry"; Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry.exe"" --help"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{cmd}"; Parameters: "/k ""{app}\fileferry.exe"" --help"; Description: "Open FileFerry command help"; Flags: nowait postinstall skipifsilent
