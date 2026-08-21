[Setup]
AppName=Catgirl Downloader
AppVersion=0.5
AppPublisher=NyarchLinux
DefaultDirName={pf}\CatgirlDownloader
DefaultGroupName=Catgirl Downloader
OutputDir=installer_output
OutputBaseFilename=CatgirlDownloader_Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=icon.ico
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\CatgirlDownloader.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Берем ВСЁ из собранной папки dist\CatgirlDownloader
Source: "dist\CatgirlDownloader\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Ярлык в меню Пуск
Name: "{group}\Catgirl Downloader"; Filename: "{app}\CatgirlDownloader.exe"; IconFilename: "{app}\CatgirlDownloader.exe"
; Ярлык на Рабочий стол (если пользователь поставит галочку)
Name: "{commondesktop}\Catgirl Downloader"; Filename: "{app}\CatgirlDownloader.exe"; IconFilename: "{app}\CatgirlDownloader.exe"; Tasks: desktopicon

[Run]
; Предложить запустить программу после установки
Filename: "{app}\CatgirlDownloader.exe"; Description: "{cm:LaunchProgram, Catgirl Downloader}"; Flags: nowait postinstall skipifsilent