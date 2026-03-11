import time
import os  # أضفنا هذه المكتبة الجديدة للتعامل مع مسارات الملفات
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class KiroGuard(FileSystemEventHandler):
    def on_created(self, event):
        # 1. نتأكد أن الشيء الجديد هو ملف وليس مجلداً
        if not event.is_directory:
            file_path = event.src_path
            
            # 2. فصل اسم الملف عن لاحقته
            _, extension = os.path.splitext(file_path)
            
            # 3. القائمة السوداء: اللواحق المؤقتة التي يجب تجاهلها
            ignored_extensions = ['.crdownload', '.tmp', '.part']
            
            # 4. نسأل الحارس: هل لاحقة الملف موجودة في القائمة المزعجة؟
            if extension.lower() in ignored_extensions:
                pass # كلمة pass تعني: "تجاهل الأمر وابق صامتاً"
            else:
                # 5. رسالة احترافية للفريق تخلو من الأسماء
                print(f"[+] Kiro Agent: Detected a new file -> {file_path}")

# المكان الذي نراقبه
folder_to_watch = "./Test_Downloads" 

# تجهيز الحارس
event_handler = KiroGuard()
observer = Observer()
observer.schedule(event_handler, folder_to_watch, recursive=False)

# رسالة الانطلاق الاحترافية
print("Kiro System is running... Monitoring 'Test_Downloads' folder.")
observer.start()

# هذا الجزء يجعل البرنامج يستمر بالعمل
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()