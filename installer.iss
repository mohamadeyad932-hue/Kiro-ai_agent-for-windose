; ═══════════════════════════════════════════════════════
; Kiro AI - Inno Setup Installer Script
; ينشئ مثبّت Windows احترافي (.exe) للتوزيع
; ═══════════════════════════════════════════════════════
; المتطلبات: Inno Setup 6+ (https://jrsoftware.org/isdl.php)
; الاستخدام: افتح هذا الملف في Inno Setup > Compile (F9)
; ═══════════════════════════════════════════════════════

#define MyAppName "Kiro AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Kiro AI Team"
#define MyAppURL "https://github.com/mohamadeyad932-hue/Kiro-ai_agent-for-windose"
#define MyAppExeName "KiroAI.exe"

[Setup]
; معرف فريد للتطبيق (لا تغيّره بعد أول إصدار)
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; مسار المخرجات
OutputDir=output
OutputBaseFilename=KiroAI_Setup_v{#MyAppVersion}
; أيقونة المثبّت
SetupIconFile=uiux_kiro_pyqt\icons\kiro_icon.ico
; ضغط عالي
Compression=lzma2/ultra64
SolidCompression=yes
; متطلبات الصلاحيات
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; إعدادات النمط
WizardStyle=modern
WizardSizePercent=120
; السماح بتغيير مسار التثبيت
AllowNoIcons=yes
; إعادة تشغيل - لا تطلب إعادة تشغيل
RestartIfNeededByRun=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu"; Description: "Create Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; نسخ كل محتويات مجلد dist/KiroAI
Source: "dist\KiroAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; تشغيل التطبيق بعد التثبيت (اختياري)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; حذف الملفات المؤقتة عند إلغاء التثبيت
Type: filesandordirs; Name: "{app}\_internal\__pycache__"
Type: filesandordirs; Name: "{tmp}\KiroAI_Data"
