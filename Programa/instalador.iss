[Setup]
AppName=Temperatura Salidas
AppVersion=1.0
DefaultDirName={pf}\CalculadoraTemperatura
DefaultGroupName=CalculadoraTemperatura
UninstallDisplayIcon={app}\app.exe
OutputDir=.
OutputBaseFilename=Instalador_Calculadora
SetupIconFile=icono.ico
Compression=lzma
SolidCompression=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

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
Name: "{group}\Temperatura Salidas"; Filename: "{app}\app.exe"; IconFilename: "{app}\icono.ico"
Name: "{userdesktop}\Temperatura Salidas"; Filename: "{app}\app.exe"; IconFilename: "{app}\icono.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Iconos adicionales:"
