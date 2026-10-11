; Compile with Inno Setup 6 on Windows after the PyInstaller build.
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
[Setup]
AppId={{55B2D4E5-5D5B-4623-BD03-588865B0128C}
AppName=forNMA (CPU)
AppVersion={#AppVersion}
AppPublisher=Luiza Cherobini Pereira
DefaultDirName={localappdata}\Programs\forNMA
DefaultGroupName=forNMA
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\release
OutputBaseFilename=forNMA-Setup-{#AppVersion}-cpu-windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\forNMA.exe
[Files]
Source: "..\..\build\desktop-dist\forNMA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\forNMA (CPU)"; Filename: "{app}\forNMA.exe"
Name: "{autodesktop}\forNMA (CPU)"; Filename: "{app}\forNMA.exe"
[Run]
Filename: "{app}\forNMA.exe"; Description: "Open forNMA"; Flags: nowait postinstall skipifsilent
