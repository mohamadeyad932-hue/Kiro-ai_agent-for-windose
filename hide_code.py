import os
import py_compile

# هذا السكربت يعمل فقط على مجلد dist ولن يمس أكوادك الأصلية أبداً!
DIST_DIR = os.path.join(os.path.dirname(__file__), "dist", "KiroAI")

def secure_code():
    if not os.path.exists(DIST_DIR):
        print("[!] خطأ: مجلد dist\\KiroAI غير موجود. يرجى تشغيل PyInstaller أولاً.")
        return

    print("=== بدء تشفير الأكواد إلى صيغة الآلة (.pyc) ===")
    
    count = 0
    for root, dirs, files in os.walk(DIST_DIR):
        for file in files:
            if file.endswith(".py"):
                py_path = os.path.join(root, file)
                pyc_path = py_path + "c" # run_project.py -> run_project.pyc
                
                try:
                    # تحويل الكود إلى صيغة الآلة
                    py_compile.compile(py_path, cfile=pyc_path)
                    
                    # حذف الملف الأصلي المكشوف من مجلد dist
                    os.remove(py_path)
                    print(f"[+] تم التشفير: {file}")
                    count += 1
                except Exception as e:
                    print(f"[-] فشل تشفير {file}: {e}")
                    
    print(f"=== اكتملت العملية! تم تشفير وإخفاء {count} ملف ===")

if __name__ == "__main__":
    secure_code()
    input("اضغط Enter للخروج...")
