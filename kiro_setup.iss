; تشغيل سكربت التشفير تلقائياً قبل بناء ملف التثبيت
#expr Exec("cmd.exe", "/c python hide_code.py", SourcePath, 1)

[Setup]
; معلومات التطبيق
AppName=Kiro AI Agent
AppVersion=1.0
AppPublisher=Kiro AI
DefaultDirName={autopf}\Kiro AI Agent
DefaultGroupName=Kiro AI Agent

; مسار حفظ ملف الـ Setup.exe النهائي واسمه
OutputDir=C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\Output_Installer
OutputBaseFilename=KiroAI_Setup_v1

; إعدادات الضغط (لتقليل حجم الـ Setup قدر الإمكان)
Compression=lzma2
SolidCompression=yes

; السماح بتثبيت 64 بت
ArchitecturesInstallIn64BitMode=x64compatible

; أيقونة ملف الـ Setup نفسه (اختياري، استخدمت أيقونة التطبيق)
SetupIconFile=C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\dist\KiroAI\_internal\uiux_kiro_pyqt\icons\homeregular_106344.ico

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "أيقونات إضافية:"

[Files]
; تحديد المجلد الذي يحتوي على كل ملفات التطبيق (المجلد الذي استخرجه PyInstaller)
Source: "C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\dist\KiroAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; اختصار في قائمة ابدأ
Name: "{group}\Kiro AI Agent"; Filename: "{app}\KiroAI.exe"
; اختصار على سطح المكتب
Name: "{commondesktop}\Kiro AI Agent"; Filename: "{app}\KiroAI.exe"; Tasks: desktopicon

[Run]
; تشغيل التطبيق فوراً بعد انتهاء التثبيت
Filename: "{app}\KiroAI.exe"; Description: "تشغيل Kiro AI Agent"; Flags: nowait postinstall skipifsilent
