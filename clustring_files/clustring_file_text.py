"""
cluster_to_folder_converter/main_converter.py
==============================================
يقوم هذا السكريبت بقراءة جميع ملفات التجميع (clustring_files + clustring_imge)
تلقائياً، واستخراج المتغيرات التي تمثل مجموعات ملفات متشابهة (Sets من مسارات).
ثم يولّد لكل مجموعة اسم مجلد ذكي باستخدام TF-IDF على أسماء الملفات النصية، وينسخ
الملفات إلى مجلدات جديدة داخل المسار المشترك للمجموعة. إذا كانت المجموعة صوراً، 
يحتفظ باسم المتغير الأصلي. 
*ملاحظة: تم تعطيل حذف ملفات التجميع بناءً على طلبك.*
"""

import os
import sys
import re
import shutil
import importlib.util
from typing import Dict, List, Tuple, Optional
from collections import Counter

# Force UTF-8 for Windows console (Arabic filenames)
sys.stdout.reconfigure(encoding="utf-8")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    print("خطأ: مكتبة scikit-learn غير مثبتة.")
    print("قم بتثبيتها عبر: pip install scikit-learn")
    sys.exit(1)


# ── المسار الحالي للمستخدم (يُستخدم لإعادة تعيين المسارات المضمنة) ──
CURRENT_HOME = os.path.expanduser("~")

# ── نمط regex للكشف عن مسارات مستخدم Windows مضمنة ──
_USER_PATH_PATTERN = re.compile(
    r"^[A-Za-z]:\\Users\\[^\\]+",  # يطابق X:\Users\username
    re.IGNORECASE
)

# ── قائمة بامتدادات الصور الشائعة لاستثنائها من خوارزمية التسمية ──
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.heic'}


# ──────────────────────────────────────────────────────────────────────
# إعادة تعيين المسارات إلى المستخدم الحالي
# ──────────────────────────────────────────────────────────────────────

def remap_path_to_current_user(original_path: str) -> str:
    match = _USER_PATH_PATTERN.match(original_path)
    if match:
        remapped = CURRENT_HOME + original_path[match.end():]
        return remapped
    return original_path


# ──────────────────────────────────────────────────────────────────────
# الخطوة 0: الاكتشاف التلقائي لملفات التجميع واستخراج المجموعات
# ──────────────────────────────────────────────────────────────────────

def _load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_cluster_groups() -> Dict[str, List[str]]:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # المجلدات التي تحتوي ملفات التجميع (تم إضافة مجلد الصور)
    cluster_dirs = [
        os.path.join(project_root, "clustring_files"),
        os.path.join(project_root, "clustring_imge"),
    ]

    master_dict: Dict[str, List[str]] = {}

    for cluster_dir in cluster_dirs:
        if not os.path.isdir(cluster_dir):
            print(f"  [!] المجلد غير موجود: {cluster_dir}")
            continue

        for filename in sorted(os.listdir(cluster_dir)):
            if not filename.endswith(".py"):
                continue
            if not filename.startswith("similar_"):
                continue

            file_path = os.path.join(cluster_dir, filename)
            module_name = filename[:-3]

            try:
                mod = _load_module_from_path(module_name, file_path)
            except Exception as e:
                print(f"  [!] فشل تحميل {filename}: {e}")
                continue

            for attr_name in dir(mod):
                if attr_name.startswith("_"):
                    continue

                value = getattr(mod, attr_name)

                if not isinstance(value, (set, list)):
                    continue
                if not value:
                    continue

                items = list(value)
                if not all(isinstance(item, str) for item in items):
                    continue

                looks_like_paths = all(
                    os.sep in item or "/" in item or ":" in item
                    for item in items
                )
                if not looks_like_paths:
                    continue

                remapped_items = [remap_path_to_current_user(p) for p in items]
                existing_items = [p for p in remapped_items if os.path.isfile(p)]
                skipped = len(remapped_items) - len(existing_items)

                if not existing_items:
                    print(f"  [⚠] {attr_name} → جميع الملفات ({len(remapped_items)}) غير موجودة، تم التخطي")
                    continue

                master_dict[attr_name] = existing_items
                if skipped > 0:
                    print(f"  [✓] {attr_name} → {len(existing_items)} ملف(ات) موجودة (تم تخطي {skipped} غير موجودة)")
                else:
                    print(f"  [✓] {attr_name} → {len(existing_items)} ملف(ات)")

    return master_dict


# ──────────────────────────────────────────────────────────────────────
# الخطوة 1: تنظيف أسماء الملفات
# ──────────────────────────────────────────────────────────────────────

def clean_filename(file_path: str) -> str:
    basename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(basename)[0]
    cleaned = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF]", " ", name_without_ext)
    cleaned = cleaned.lower()
    tokens = cleaned.split()
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(tokens)


# ──────────────────────────────────────────────────────────────────────
# الخطوة 2: توليد اسم مجلد ذكي باستخدام TF-IDF
# ──────────────────────────────────────────────────────────────────────

def generate_folder_name_tfidf(file_paths: List[str], default_name: str) -> str:
    files_for_naming = [
        fp for fp in file_paths
        if os.path.splitext(fp)[1].lower() not in IMAGE_EXTENSIONS
    ]

    if not files_for_naming:
        return default_name

    cleaned_names = [clean_filename(fp) for fp in files_for_naming]
    non_empty = [name for name in cleaned_names if name.strip()]

    if not non_empty:
        return default_name

    has_arabic = any(re.search(r'[\u0600-\u06FF]', name) for name in non_empty)
    stop_words = None if has_arabic else "english"

    folder_name = _tfidf_approach(non_empty, stop_words=stop_words)
    
    return folder_name or _frequency_fallback(non_empty) or default_name


def _tfidf_approach(documents: List[str], stop_words=None) -> Optional[str]:
    try:
        vectorizer = TfidfVectorizer(
            stop_words=stop_words,
            ngram_range=(1, 2),
        )
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return None

    feature_names = vectorizer.get_feature_names_out()

    if len(feature_names) == 0:
        return None

    import numpy as np
    mean_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
    sorted_indices = mean_scores.argsort()[::-1]

    top_terms = []
    for idx in sorted_indices:
        term = feature_names[idx]
        score = mean_scores[idx]

        if score <= 0:
            break

        term_words = term.split()
        if len(term_words) == 2:
            if term_words[0] in top_terms or term_words[1] in top_terms:
                continue

        top_terms.append(term)

        if len(top_terms) >= 3:
            break

    if len(top_terms) < 1:
        return None

    return " ".join(top_terms[:4])


def _frequency_fallback(documents: List[str]) -> str:
    all_words = []
    for doc in documents:
        all_words.extend(doc.split())

    if not all_words:
        return ""

    word_counts = Counter(all_words)
    most_common = word_counts.most_common(4)
    selected = [word for word, _ in most_common]

    if len(selected) < 2:
        selected.append("files")

    return " ".join(selected[:4])


# ──────────────────────────────────────────────────────────────────────
# الخطوة 3: تحديد المسار المشترك وتنسيق اسم المجلد
# ──────────────────────────────────────────────────────────────────────

def get_base_path(file_paths: List[str]) -> str:
    try:
        dirs = [os.path.dirname(p) for p in file_paths]
        return os.path.commonpath(dirs)
    except ValueError:
        return os.path.dirname(file_paths[0])


def sanitize_folder_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name or "untitled_group"


# ──────────────────────────────────────────────────────────────────────
# الخطوة 4: إنشاء المجلد ونسخ الملفات
# ──────────────────────────────────────────────────────────────────────

def create_unique_folder(base_path: str, folder_name: str) -> str:
    target_path = os.path.join(base_path, folder_name)

    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
        return target_path

    suffix = 1
    while True:
        new_path = os.path.join(base_path, f"{folder_name}_{suffix}")
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)
            return new_path
        suffix += 1


def copy_files_to_folder(file_paths: List[str], folder_path: str) -> Tuple[int, int]:
    success_count = 0
    fail_count = 0

    for file_path in file_paths:
        try:
            if not os.path.isfile(file_path):
                print(f"    [!] الملف غير موجود: {os.path.basename(file_path)}")
                fail_count += 1
                continue
                
            dest = os.path.join(folder_path, os.path.basename(file_path))
            
            if os.path.exists(dest):
                base, ext = os.path.splitext(os.path.basename(file_path))
                counter = 1
                while os.path.exists(dest):
                    dest = os.path.join(folder_path, f"{base}_{counter}{ext}")
                    counter += 1
                    
            shutil.copy2(file_path, dest)
            success_count += 1
        except Exception as e:
            print(f"    [✗] فشل نسخ {os.path.basename(file_path)}: {e}")
            fail_count += 1

    return success_count, fail_count


# ──────────────────────────────────────────────────────────────────────
# الخطوة 5: التنفيذ الرئيسي
# ──────────────────────────────────────────────────────────────────────

def process_all_clusters(cluster_dict: Dict[str, List[str]]) -> None:
    if not cluster_dict:
        print("\n[!] لم يتم العثور على أي مجموعات للمعالجة.")
        return

    print(f"\n{'='*60}")
    print(f"  بدء تحويل المجموعات إلى مجلدات...")
    print(f"  إجمالي المجموعات: {len(cluster_dict)}")
    print(f"{'='*60}")

    total_copied = 0
    total_failed = 0
    total_folders = 0

    for group_name, file_paths in cluster_dict.items():
        print(f"\n── المجموعة: {group_name} ({len(file_paths)} ملف) ──")

        if not file_paths:
            print("  [!] المجموعة فارغة، تم التخطي.")
            continue

        raw_folder_name = generate_folder_name_tfidf(file_paths, default_name=group_name)
        folder_name = sanitize_folder_name(raw_folder_name)
        print(f"  اسم المجلد المُقترح: \"{folder_name}\"")

        base_path = get_base_path(file_paths)
        print(f"  المسار الأساسي: {base_path}")

        if not os.path.isdir(base_path):
            print(f"  [!] المسار الأساسي غير موجود: {base_path} — تم التخطي.")
            continue

        try:
            created_path = create_unique_folder(base_path, folder_name)
            print(f"  تم إنشاء المجلد: {created_path}")
            total_folders += 1
        except Exception as e:
            print(f"  [✗] فشل إنشاء المجلد: {e}")
            continue

        copied, failed = copy_files_to_folder(file_paths, created_path)
        total_copied += copied
        total_failed += failed
        print(f"  النتيجة: {copied} ملف تم نسخه ✓ | {failed} فشل ✗")

    print(f"\n{'='*60}")
    print(f"  ✅ تمت العملية بنجاح!")
    print(f"  المجلدات المُنشأة: {total_folders}")
    print(f"  الملفات المنسوخة: {total_copied}")
    if total_failed > 0:
        print(f"  ⚠ ملفات فشلت: {total_failed}")
    print(f"{'='*60}")


def main() -> None:
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Cluster → Folder Converter                             ║")
    print("║   تحويل مجموعات الملفات المتشابهة إلى مجلدات منظمة      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    print("\n[1/2] جاري البحث عن مجموعات الملفات...")
    cluster_dict = discover_cluster_groups()

    if not cluster_dict:
        print("\n[!] لم يتم العثور على أي مجموعات.")
        print("    تأكد من وجود ملفات similar_*.py في مجلدات:")
        print("    - clustring_files/")
        print("    - clustring_imge/")
        return

    print(f"\n  → تم العثور على {len(cluster_dict)} مجموعة إجمالاً.\n")

    print("[2/2] جاري إنشاء المجلدات ونسخ الملفات...")
    process_all_clusters(cluster_dict)

    # تمت إزالة خطوة حذف الملفات للحفاظ على ملفات التجميع (similar_*.py)
    print("\n[✓] اكتملت العملية وتم الاحتفاظ بملفات التجميع.")

if __name__ == "__main__":
    main()