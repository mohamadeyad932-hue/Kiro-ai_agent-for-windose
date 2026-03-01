import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 1. هنا نصنع "الحارس" ونعلمه ماذا يفعل عندما يرى شيئاً جديداً
class KiroGuard(FileSystemEventHandler):
    def on_created(self, event):
        # نتأكد أولاً أن الشيء الجديد هو ملف وليس مجلداً
        if not event.is_directory:
            print(f"يا وسيم! لقد التقطت ملفاً جديداً: {event.src_path}")

# 2. نخبر الحارس عن المكان الذي يجب أن يقف فيه ويراقبه
# سنستخدم مجلد التجارب الذي أنشأناه
folder_to_watch = "./Test_Downloads" 

# 3. نجهز الحارس والمراقب للعمل
event_handler = KiroGuard()
observer = Observer()
observer.schedule(event_handler, folder_to_watch, recursive=False)

# 4. نعطي أمر الانطلاق!
print("أنا Kiro.. لقد بدأت بمراقبة مجلد Test_Downloads. بانتظار ملفاتك!")
observer.start()

# هذا الجزء يجعل البرنامج يستمر بالعمل ولا يغلق فوراً
try:
    while True:
        time.sleep(1) # البرنامج يأخذ غفوة لثانية لكي لا يرهق الحاسوب
except KeyboardInterrupt:
    observer.stop() # إيقاف البرنامج إذا ضغطت على Ctrl+C

observer.join()