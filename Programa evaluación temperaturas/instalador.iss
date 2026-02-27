[Setup]
AppName=Temperatura Saídas
AppVersion=1.0
DefaultDirName={pf}\CalculadoraTemperatura
DefaultGroupName=CalculadoraTemperatura
UninstallDisplayIcon={app}\app.exe
OutputDir=.
OutputBaseFilename=Instalador_Calculadora_PT
SetupIconFile=icono.ico
Compression=lzma
SolidCompression=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Files]
Source: "dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "brasil.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "mexico.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "ComBlindagem.JPG"; DestDir: "{app}"; Flags: ignoreversion
Source: "SemBlindagem.JPG"; DestDir: "{app}"; Flags: ignoreversion
Source: "cotab.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "historial.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "icono.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Temperatura Saídas"; Filename: "{app}\app.exe"; IconFilename: "{app}\icono.ico"
Name: "{userdesktop}\Temperatura Saídas"; Filename: "{app}\app.exe"; IconFilename: "{app}\icono.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Ícones adicionais:"
