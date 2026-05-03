; ════════════════════════════════════════════════════════════════
; installer.iss — Inno Setup Script
; Tạo file cài đặt Windows cho "Phần Mềm Auto SEO"
; Build: Mở file này bằng Inno Setup Compiler rồi bấm Build
; Tải Inno Setup: https://jrsoftware.org/isdl.php
; ════════════════════════════════════════════════════════════════

#define AppName      "Phần Mềm Auto SEO"
#define AppVersion   "1.0.0"
#define AppPublisher "Huỳnh Khang"
#define AppExeName   "AutoSEO.exe"
#define AppURL       "https://huynhkhang.com"
#define OutputDir    "installer_output"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Thư mục cài đặt mặc định (giống Zalo, UltraViewer)
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; File output
OutputDir={#OutputDir}
OutputBaseFilename=AutoSEO_Setup_v{#AppVersion}
SetupIconFile=icon.ico

; Nén tốt nhất (lzma = nhỏ nhất, như 7-zip)
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64

; Yêu cầu Windows 10+
MinVersion=10.0

; Giao diện hiện đại
WizardStyle=modern
WizardResizable=no

; Không cần quyền Admin (cài vào AppData thay vì Program Files)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Hiện license trước khi cài
; LicenseFile=license.txt

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"
Name: "english";    MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Tạo biểu tượng trên Desktop";   GroupDescription: "Tùy chọn bổ sung:"; Flags: checkedonce
Name: "startmenuicon";  Description: "Tạo shortcut trong Start Menu";  GroupDescription: "Tùy chọn bổ sung:"; Flags: checkedonce
Name: "autostart";      Description: "Khởi động cùng Windows";         GroupDescription: "Tùy chọn bổ sung:"; Flags: unchecked

[Files]
; Toàn bộ thư mục dist\AutoSEO\ do PyInstaller tạo ra
Source: "dist\AutoSEO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Shortcut Desktop
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
      IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

; Shortcut Start Menu
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon
Name: "{group}\Gỡ cài đặt {#AppName}"; Filename: "{uninstallexe}";      Tasks: startmenuicon

[Registry]
; Khởi động cùng Windows (nếu người dùng chọn)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
     ValueType: string; ValueName: "{#AppName}"; \
     ValueData: """{app}\{#AppExeName}"""; \
     Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Hỏi có muốn mở app sau khi cài không (giống Zalo)
Filename: "{app}\{#AppExeName}"; \
    Description: "Khởi chạy {#AppName} ngay bây giờ"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Xóa sạch khi gỡ cài đặt
Type: filesandordirs; Name: "{app}"

[Messages]
; Tuỳ chỉnh văn bản hiển thị
WelcomeLabel1=Chào mừng bạn đến với trình cài đặt của%n{#AppName}
WelcomeLabel2=Phần mềm sẽ được cài đặt vào máy tính của bạn.%n%nBấm Tiếp tục để bắt đầu cài đặt.
FinishedLabel=Cài đặt {#AppName} hoàn tất!%n%nBạn có thể khởi chạy phần mềm bằng cách bấm vào biểu tượng trên Desktop.
