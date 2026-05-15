"""
Kiro AI - Script Compiler
يحوّل جميع سكربتات المعالجة من .py إلى .pyc لحماية الكود المصدري
═══════════════════════════════════════════════
الاستخدام: python compile_scripts.py
"""
import py_compile
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# المجلدات التي تحتوي سكربتات تُشغَّل كعمليات فرعية
SCRIPT_DIRS = [
    "Processing text files",
    "Processing image",
    "clustring_files",
    "clustring_imge",
    "creat folders for flie_text  and name",
    "creat folders for image and name",
    "dawnload_models",
]

# سكربتات في المجلد الرئيسي
ROOT_SCRIPTS = ["run_project.py"]

# ملفات البيانات المُولَّدة تلقائياً (لا نحتاج تجميعها)
SKIP_PATTERNS = [
    "_files.py", "_vectors.py", "similar_",
    "_images_files.py", "_images_vectors.py",
]


def should_skip(filename):
    """تخطي ملفات البيانات المُولَّدة تلقائياً"""
    for pattern in SKIP_PATTERNS:
        if pattern in filename:
            return True
    return False


def compile_file(py_path):
    """تجميع ملف .py واحد إلى .pyc"""
    pyc_path = py_path + "c"  # file.py → file.pyc
    try:
        py_compile.compile(py_path, cfile=pyc_path, doraise=True)
        print(f"  OK  {os.path.relpath(py_path, PROJECT_ROOT)}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ERR {os.path.relpath(py_path, PROJECT_ROOT)}: {e}")
        return False


def main():
    print("=" * 50)
    print("  Compiling scripts to .pyc bytecode")
    print("=" * 50)

    compiled, failed = 0, 0

    # تجميع السكربتات الرئيسية
    for script in ROOT_SCRIPTS:
        path = os.path.join(PROJECT_ROOT, script)
        if os.path.exists(path):
            if compile_file(path):
                compiled += 1
            else:
                failed += 1

    # تجميع سكربتات المجلدات الفرعية
    for dir_name in SCRIPT_DIRS:
        dir_path = os.path.join(PROJECT_ROOT, dir_name)
        if not os.path.isdir(dir_path):
            continue
        for fname in os.listdir(dir_path):
            if not fname.endswith(".py") or should_skip(fname):
                continue
            if compile_file(os.path.join(dir_path, fname)):
                compiled += 1
            else:
                failed += 1

    print(f"\nDone: {compiled} compiled, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
