[Setup]
AppName=Invoice Generator
AppVersion=1.0
DefaultDirName={autopf}\Invoice Generator
DefaultGroupName=Invoice Generator
OutputDir=installer
OutputBaseFilename=InvoiceGeneratorSetup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\InvoiceGenerator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Invoice Generator"; Filename: "{app}\InvoiceGenerator.exe"
Name: "{autodesktop}\Invoice Generator"; Filename: "{app}\InvoiceGenerator.exe"

[Run]
Filename: "{app}\InvoiceGenerator.exe"; Description: "{cm:LaunchProgram,Invoice Generator}"; Flags: nowait postinstall skipifsilent
