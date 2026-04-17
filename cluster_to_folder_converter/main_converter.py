"""
cluster_to_folder_converter/main_converter.py
==============================================
يقوم هذا السكريبت بقراءة جميع ملفات التجميع (clustring_files + clustring_imge)
تلقائياً، واستخراج المتغيرات التي تمثل مجموعات ملفات متشابهة (Sets من مسارات).
ثم يولّد لكل مجموعة اسم مجلد ذكي باستخدام TF-IDF على أسماء الملفات، وينسخ
الملفات إلى مجلدات جديدة داخل المسار الأب للمجموعة.

Workflow:
  1. Auto-discover cluster variables from sibling directories.
  2. Build a master dictionary: {group_name: list[file_paths]}.
  3. For each group: clean filenames → TF-IDF → generate folder name.
  4. Create folder (with numeric suffix if needed) → copy files via shutil.copy2.
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
# يكتشف أي مسار يبدأ بـ C:\Users\<أي_اسم_مستخدم>\
_USER_PATH_PATTERN = re.compile(
    r"^[A-Za-z]:\\Users\\[^\\]+",  # يطابق X:\Users\username
    re.IGNORECASE
)


# ──────────────────────────────────────────────────────────────────────
# إعادة تعيين المسارات إلى المستخدم الحالي
# ──────────────────────────────────────────────────────────────────────

def remap_path_to_current_user(original_path: str) -> str:
    """
    تحويل مسار ملف مضمن (مثل C:\\Users\\eyad\\Desktop\\file.pdf)
    إلى مسار المستخدم الحالي (مثل C:\\Users\\HP\\Desktop\\file.pdf)
    باستخدام os.path.expanduser("~").

    إذا لم يتطابق المسار مع نمط C:\\Users\\<user>\\... يُعاد كما هو.

    Args:
        original_path: المسار الأصلي المُضمن في ملفات التجميع.

    Returns:
        المسار بعد إعادة التعيين للمستخدم الحالي.
    """
    match = _USER_PATH_PATTERN.match(original_path)
    if match:
        # نستبدل الجزء المطابق (مثل C:\Users\eyad) بـ CURRENT_HOME
        remapped = CURRENT_HOME + original_path[match.end():]
        return remapped
    return original_path


# ──────────────────────────────────────────────────────────────────────
# الخطوة 0: الاكتشاف التلقائي لملفات التجميع واستخراج المجموعات
# ──────────────────────────────────────────────────────────────────────

def _load_module_from_path(module_name: str, file_path: str):
    """تحميل موديول بايثون ديناميكياً من مسار ملف."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_cluster_groups() -> Dict[str, List[str]]:
    """
    يبحث تلقائياً في مجلدات المشروع عن ملفات التجميع
    (similar_*_files.py و similar_*_images.py و duplicates_*)
    ويستخرج كل متغير من نوع set أو list يحتوي على مسارات ملفات.

    Returns:
        قاموس حيث كل مفتاح = اسم المتغير (مثل desktop_group_1)
                  وكل قيمة = قائمة مسارات الملفات.
    """
    # ── تحديد جذر المشروع (المجلد الأب لـ cluster_to_folder_converter) ──
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── المجلدات التي تحتوي ملفات التجميع ──
    cluster_dirs = [
        os.path.join(project_root, "clustring_files"),
        os.path.join(project_root, "clustring_imge"),
    ]

    master_dict: Dict[str, List[str]] = {}

    for cluster_dir in cluster_dirs:
        if not os.path.isdir(cluster_dir):
            print(f"  [!] المجلد غير موجود: {cluster_dir}")
            continue

        # ── نبحث عن ملفات similar_*.py في المجلد ──
        for filename in sorted(os.listdir(cluster_dir)):
            if not filename.endswith(".py"):
                continue
            if not filename.startswith("similar_"):
                continue

            file_path = os.path.join(cluster_dir, filename)
            module_name = filename[:-3]  # بدون .py

            try:
                mod = _load_module_from_path(module_name, file_path)
            except Exception as e:
                print(f"  [!] فشل تحميل {filename}: {e}")
                continue

            # ── نفحص كل متغير في الموديول ──
            for attr_name in dir(mod):
                if attr_name.startswith("_"):
                    continue

                value = getattr(mod, attr_name)

                # نقبل فقط set أو list تحتوي على مسارات (strings)
                if not isinstance(value, (set, list)):
                    continue
                if not value:
                    continue

                # نتحقق أن جميع العناصر هي سلاسل نصية (مسارات ملفات)
                items = list(value)
                if not all(isinstance(item, str) for item in items):
                    continue

                # التحقق أن العناصر تبدو كمسارات ملفات فعلية
                # (تحتوي على فاصل مسار أو حرف قرص)
                looks_like_paths = all(
                    os.sep in item or "/" in item or ":" in item
                    for item in items
                )
                if not looks_like_paths:
                    continue

                # ── إعادة تعيين المسارات إلى المستخدم الحالي ──
                remapped_items = [remap_path_to_current_user(p) for p in items]

                # ── تصفية: نحتفظ فقط بالملفات الموجودة فعلياً ──
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
    """
    تنظيف اسم الملف لاستخدامه كمُدخل نصي لـ TF-IDF.

    الخطوات:
      1. استخراج اسم الملف فقط بدون المسار باستخدام os.path.basename.
      2. إزالة الامتداد (.pdf, .docx, .jpg, ...).
      3. استبدال الأرقام والرموز الخاصة (_ - ( ) وغيرها) بمسافات.
      4. تحويل النص إلى lowercase.
      5. تقسيم إلى tokens وإزالة الكلمات القصيرة جداً (حرف واحد).

    Args:
        file_path: المسار الكامل للملف.

    Returns:
        سلسلة نصية نظيفة من كلمات مفصولة بمسافات.
    """
    # الخطوة 1: استخراج اسم الملف
    basename = os.path.basename(file_path)

    # الخطوة 2: إزالة الامتداد
    name_without_ext = os.path.splitext(basename)[0]

    # الخطوة 3: استبدال الأرقام والرموز بمسافات
    # نستبدل أي حرف ليس حرفاً أبجدياً (عربي أو إنجليزي) بمسافة
    cleaned = re.sub(r"[^a-zA-Z\u0600-\u06FF]", " ", name_without_ext)

    # الخطوة 4: تحويل إلى lowercase
    cleaned = cleaned.lower()

    # الخطوة 5: تقسيم وتصفية
    tokens = cleaned.split()
    # إزالة الكلمات المكونة من حرف واحد (فقط الإنجليزية)
    tokens = [t for t in tokens if len(t) > 1 or not t.isascii()]

    return " ".join(tokens)


# ──────────────────────────────────────────────────────────────────────
# الخطوة 2: توليد اسم مجلد ذكي باستخدام TF-IDF
# ──────────────────────────────────────────────────────────────────────

def generate_folder_name_tfidf(file_paths: List[str]) -> str:
    """
    توليد اسم مجلد وصفي بناءً على أسماء الملفات في المجموعة.

    المنهجية:
      - كل اسم ملف يُعامل كـ Document مستقل.
      - نستخدم TfidfVectorizer مع stop_words='english' و ngram_range=(1,2).
      - نحسب متوسط قيمة TF-IDF لكل كلمة/عبارة عبر جميع الملفات.
      - نختار أعلى 2-4 كلمات حسب المتوسط.
      - إذا فشل TF-IDF (كلمات قليلة أو نتائج فارغة)، نستخدم
        أكثر الكلمات تكراراً كـ fallback.

    Args:
        file_paths: قائمة مسارات الملفات في المجموعة.

    Returns:
        اسم مجلد مكوّن من 2-4 كلمات مفصولة بمسافة.
    """
    # ── تنظيف جميع أسماء الملفات ──
    cleaned_names = [clean_filename(fp) for fp in file_paths]

    # ── إزالة المستندات الفارغة ──
    non_empty = [name for name in cleaned_names if name.strip()]

    if not non_empty:
        return "untitled group"

    # ── محاولة TF-IDF ──
    folder_name = _tfidf_approach(non_empty)

    if folder_name:
        return folder_name

    # ── Fallback: أكثر الكلمات تكراراً ──
    return _frequency_fallback(non_empty)


def _tfidf_approach(documents: List[str]) -> Optional[str]:
    """
    محاولة توليد اسم مجلد باستخدام TF-IDF.

    منطق اختيار كلمات TF-IDF:
      - نستخدم TfidfVectorizer مع stop_words='english' لإزالة الكلمات الشائعة.
      - ngram_range=(1,2) للسماح بعبارات من كلمة أو كلمتين.
      - نحسب متوسط TF-IDF لكل مصطلح عبر جميع المستندات.
      - نرتب تنازلياً ونختار أعلى 2-4 مصطلحات.

    Args:
        documents: قائمة النصوص النظيفة (كل عنصر = اسم ملف منظف).

    Returns:
        اسم المجلد أو None إذا فشل.
    """
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        # يحدث عندما تكون جميع المستندات فارغة بعد إزالة stop words
        return None

    feature_names = vectorizer.get_feature_names_out()

    if len(feature_names) == 0:
        return None

    # ── حساب متوسط TF-IDF لكل مصطلح عبر جميع المستندات ──
    # tfidf_matrix: sparse matrix (n_docs × n_features)
    import numpy as np
    mean_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

    # ── ترتيب تنازلي ──
    sorted_indices = mean_scores.argsort()[::-1]

    # ── اختيار أعلى 2-4 كلمات ──
    top_terms = []
    for idx in sorted_indices:
        term = feature_names[idx]
        score = mean_scores[idx]

        if score <= 0:
            break

        # تجنب إضافة bigram إذا كانت كلماته موجودة بالفعل
        term_words = term.split()
        if len(term_words) == 2:
            if term_words[0] in top_terms or term_words[1] in top_terms:
                continue

        top_terms.append(term)

        if len(top_terms) >= 4:
            break

    if len(top_terms) < 2:
        return None

    return " ".join(top_terms[:4])


def _frequency_fallback(documents: List[str]) -> str:
    """
    Fallback: إذا فشل TF-IDF، نستخدم أكثر الكلمات تكراراً.

    Args:
        documents: قائمة النصوص النظيفة.

    Returns:
        اسم مجلد من 2-4 كلمات.
    """
    all_words = []
    for doc in documents:
        all_words.extend(doc.split())

    if not all_words:
        return "untitled group"

    word_counts = Counter(all_words)
    # نختار أعلى 4 كلمات تكراراً
    most_common = word_counts.most_common(4)

    # نضمن حد أدنى 2 كلمات
    selected = [word for word, _ in most_common]

    if len(selected) < 2:
        # إذا كلمة واحدة فقط، نكررها مع "files"
        selected.append("files")

    return " ".join(selected[:4])


# ──────────────────────────────────────────────────────────────────────
# الخطوة 3: تحديد المسار الأساسي (Base Path)
# ──────────────────────────────────────────────────────────────────────

def get_base_path(file_paths: List[str]) -> str:
    """
    تحديد المسار الأب الذي سيتم إنشاء المجلد الجديد فيه.

    سبب اختيار Base Path:
      نستخدم أول ملف في المجموعة لأن جميع ملفات المجموعة الواحدة
      عادةً ما تكون في نفس المجلد (Desktop أو Documents أو Downloads).
      المسار الأب لأول ملف يمثل المجلد الأصلي للمجموعة، وهو المكان
      الطبيعي والمنطقي لإنشاء المجلد الفرعي الجديد.

    Args:
        file_paths: قائمة مسارات الملفات في المجموعة.

    Returns:
        المسار الأب لأول ملف في القائمة.
    """
    first_file = file_paths[0]
    base_path = os.path.dirname(first_file)
    return base_path


# ──────────────────────────────────────────────────────────────────────
# الخطوة 4: إنشاء المجلد ونسخ الملفات
# ──────────────────────────────────────────────────────────────────────

def create_unique_folder(base_path: str, folder_name: str) -> str:
    """
    إنشاء مجلد باسم فريد.
    إذا كان الاسم موجوداً مسبقاً، نضيف suffix رقمي (_1, _2, ...).

    Args:
        base_path: المسار الأب لإنشاء المجلد فيه.
        folder_name: الاسم المُقترح للمجلد.

    Returns:
        المسار الكامل للمجلد الذي تم إنشاؤه.
    """
    target_path = os.path.join(base_path, folder_name)

    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
        return target_path

    # إضافة suffix رقمي لتجنب التعارض
    suffix = 1
    while True:
        new_path = os.path.join(base_path, f"{folder_name}_{suffix}")
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)
            return new_path
        suffix += 1


def copy_files_to_folder(file_paths: List[str], folder_path: str) -> Tuple[int, int]:
    """
    نسخ جميع الملفات إلى المجلد المُحدد باستخدام shutil.copy2.

    ملاحظة: نستخدم shutil.copy2 (وليس shutil.move أو os.rename) للحفاظ
    على الملفات الأصلية في مكانها. copy2 ينسخ أيضاً metadata الملف.

    Args:
        file_paths: قائمة مسارات الملفات المراد نسخها.
        folder_path: مسار المجلد الهدف.

    Returns:
        Tuple[عدد الملفات المنسوخة بنجاح, عدد الملفات التي فشل نسخها].
    """
    success_count = 0
    fail_count = 0

    for file_path in file_paths:
        try:
            if os.path.isfile(file_path):
                shutil.copy2(file_path, folder_path)
                success_count += 1
            else:
                print(f"    [!] الملف غير موجود: {os.path.basename(file_path)}")
                fail_count += 1
        except Exception as e:
            print(f"    [✗] فشل نسخ {os.path.basename(file_path)}: {e}")
            fail_count += 1

    return success_count, fail_count


# ──────────────────────────────────────────────────────────────────────
# الخطوة 5: التنفيذ الرئيسي
# ──────────────────────────────────────────────────────────────────────

def process_all_clusters(cluster_dict: Dict[str, List[str]]) -> None:
    """
    معالجة جميع المجموعات: توليد أسماء مجلدات → إنشاء مجلدات → نسخ ملفات.

    Args:
        cluster_dict: القاموس الرئيسي {اسم_المجموعة: [قائمة_المسارات]}.
    """
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

        # ── توليد اسم المجلد ──
        folder_name = generate_folder_name_tfidf(file_paths)
        print(f"  اسم المجلد المُقترح: \"{folder_name}\"")

        # ── تحديد المسار الأساسي ──
        base_path = get_base_path(file_paths)
        print(f"  المسار الأساسي: {base_path}")

        # ── التحقق من وجود المسار الأساسي ──
        if not os.path.isdir(base_path):
            print(f"  [!] المسار الأساسي غير موجود: {base_path} — تم التخطي.")
            continue

        # ── إنشاء المجلد ──
        try:
            created_path = create_unique_folder(base_path, folder_name)
            print(f"  تم إنشاء المجلد: {created_path}")
            total_folders += 1
        except Exception as e:
            print(f"  [✗] فشل إنشاء المجلد: {e}")
            continue

        # ── نسخ الملفات ──
        copied, failed = copy_files_to_folder(file_paths, created_path)
        total_copied += copied
        total_failed += failed
        print(f"  النتيجة: {copied} ملف تم نسخه ✓ | {failed} فشل ✗")

    # ── ملخص نهائي ──
    print(f"\n{'='*60}")
    print(f"  ✅ تمت العملية بنجاح!")
    print(f"  المجلدات المُنشأة: {total_folders}")
    print(f"  الملفات المنسوخة: {total_copied}")
    if total_failed > 0:
        print(f"  ⚠ ملفات فشلت: {total_failed}")
    print(f"{'='*60}")


def main() -> None:
    """نقطة الدخول الرئيسية للبرنامج."""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Cluster → Folder Converter                           ║")
    print("║   تحويل مجموعات الملفات المتشابهة إلى مجلدات منظمة    ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # ── الخطوة 1: اكتشاف المجموعات تلقائياً ──
    print("\n[1/2] جاري البحث عن مجموعات الملفات...")
    cluster_dict = discover_cluster_groups()

    if not cluster_dict:
        print("\n[!] لم يتم العثور على أي مجموعات.")
        print("    تأكد من وجود ملفات similar_*.py في مجلدات:")
        print("    - clustring_files/")
        print("    - clustring_imge/")
        return

    print(f"\n  → تم العثور على {len(cluster_dict)} مجموعة إجمالاً.\n")

    # ── الخطوة 2: المعالجة والنسخ ──
    print("[2/2] جاري إنشاء المجلدات ونسخ الملفات...")
    process_all_clusters(cluster_dict)


if __name__ == "__main__":
    main()
