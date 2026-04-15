"""
clustring_file_images.py
الخط الكامل لمعالجة الصور في مشروع Kiro
المرحلة 1: كشف المكررات ونقلها (Perceptual Hashing)
المرحلة 2: تجميع الصور المتبقية (CLIP + Clustering)
"""

import os
import sys
import shutil
import numpy as np
from itertools import combinations
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

try:
    import imagehash
    from PIL import Image
except ImportError:
    print("pip install imagehash Pillow")
    sys.exit(1)

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import pairwise_distances
except ImportError:
    print("pip install scikit-learn numpy")
    sys.exit(1)

# ─────────────── الإعدادات ───────────────

HOME = os.path.expanduser("~")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSING_DIR = os.path.join(CURRENT_DIR, "..", "image_file_prossing")
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

FOLDERS = {
    "desktop":   os.path.join(HOME, "Desktop"),
    "documents": os.path.join(HOME, "Documents"),
    "downloads": os.path.join(HOME, "Downloads"),
}

EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
THRESHOLD = 10
DUPLICATES_DIR = os.path.join(HOME, "Desktop", "Kiro_Duplicates")

# استيراد البصمات والقواميس
try:
    from desktop_images_files import desktop_images
    from desktop_images_vectors import desktop_images_vectors
    from documents_images_files import documents_images
    from documents_images_vectors import documents_images_vectors
    from downloads_images_files import downloads_images
    from downloads_images_vectors import downloads_images_vectors
except ImportError:
    print("⚠ تنبيه: تعذر استيراد بعض ملفات البصمات.")
    desktop_images, desktop_images_vectors = {}, {}
    documents_images, documents_images_vectors = {}, {}
    downloads_images, downloads_images_vectors = {}, {}


# ═══════════════════════════════════════════════
# المرحلة 1: كشف المكررات
# ═══════════════════════════════════════════════

def get_all_images(folders):
    """جمع كل الصور من المجلدات الثلاثة"""
    all_images = {}
    for folder_name, folder_path in folders.items():
        if not os.path.isdir(folder_path):
            continue
        try:
            with os.scandir(folder_path) as entries:
                for entry in entries:
                    if not entry.is_file():
                        continue
                    _, ext = os.path.splitext(entry.name)
                    if ext.lower() in EXTENSIONS:
                        all_images[entry.path] = entry.name
        except PermissionError:
            print(f"  ⚠ لا توجد صلاحية: {folder_path}")
    return all_images


def compute_hashes(all_images):
    """حساب البصمة الإدراكية لكل صورة"""
    hashes = {}
    print(f"\nجاري حساب البصمات لـ {len(all_images)} صورة...")
    for path in all_images:
        try:
            img = Image.open(path).convert("RGB")
            hashes[path] = imagehash.phash(img)
        except PermissionError:
            print(f"  ⚠ الصورة قيد الاستخدام (مقفولة). تم التخطي: {os.path.basename(path)}")
        except FileNotFoundError:
            print(f"  ⚠ اختفت الصورة (ربما نُقلت الآن): {os.path.basename(path)}")
        except Exception as e:
            print(f"  ⚠ خطأ: {os.path.basename(path)} → {e}")
    return hashes


def find_duplicates(hashes):
    """إيجاد الصور المتشابهة بمقارنة كل الأزواج"""
    paths = list(hashes.keys())
    duplicate_groups = []

    for path1, path2 in combinations(paths, 2):
        distance = hashes[path1] - hashes[path2]
        if distance <= THRESHOLD:
            found = False
            for group in duplicate_groups:
                if path1 in group or path2 in group:
                    group.add(path1)
                    group.add(path2)
                    found = True
                    break
            if not found:
                duplicate_groups.append({path1, path2})

    return duplicate_groups


def save_duplicates_script(duplicate_groups):
    """حفظ المكررات في قاموس وحد"""
    script_path = os.path.join(CURRENT_DIR, "duplicates_images.py")

    all_duplicates = {}
    for group in duplicate_groups:
        sorted_group = sorted(group)
        for dup_path in sorted_group[1:]:
            name, ext = os.path.splitext(os.path.basename(dup_path))
            all_duplicates[name] = ext.lower()

    lines = [
        '"""',
        "قاموس الصور المكررة — توليد تلقائي",
        "كل عنصر: اسم الملف بدون امتداد → الامتداد",
        '"""',
        "",
        f"# إجمالي المكررات: {len(all_duplicates)} صورة",
        "duplicates = {",
    ]
    for name, ext in all_duplicates.items():
        lines.append(f'    "{name.replace(chr(34), chr(92)+chr(34))}": "{ext}",')
    lines.append("}\n")

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [+] تم حفظ: duplicates_images.py ({len(all_duplicates)} مكرر)")


def move_duplicates(duplicate_groups):
    """نقل المكررات لمجلد خاص وإرجاع مسارات الصور المنقولة"""
    moved_paths = set()

    if not duplicate_groups:
        print("\n✅ لم يتم العثور على صور مكررة.")
        return moved_paths

    os.makedirs(DUPLICATES_DIR, exist_ok=True)
    print(f"\nتم العثور على {len(duplicate_groups)} مجموعة مكررة:")
    print(f"سيتم نقل المكررات إلى: {DUPLICATES_DIR}\n")

    for i, group in enumerate(duplicate_groups, 1):
        sorted_group = sorted(group)
        original = sorted_group[0]
        duplicates = sorted_group[1:]

        print(f"  المجموعة {i}:")
        print(f"    ✅ يبقى: {os.path.basename(original)}")

        for dup in duplicates:
            dest = os.path.join(DUPLICATES_DIR, os.path.basename(dup))
            if os.path.exists(dest):
                name, ext = os.path.splitext(os.path.basename(dup))
                dest = os.path.join(DUPLICATES_DIR, f"{name}_dup{i}{ext}")
            try:
                shutil.move(dup, dest)
                moved_paths.add(dup)
                print(f"    🔁 نُقل: {os.path.basename(dup)}")
            except PermissionError:
                print(f"    ⚠ فشل النقل، الصورة قيد الاستخدام (مقفولة): {os.path.basename(dup)}")
            except FileNotFoundError:
                print(f"    ⚠ اختفت الصورة قبل نقلها بلحظات: {os.path.basename(dup)}")
            except Exception as e:
                print(f"    ⚠ خطأ في النقل: {e}")

    return moved_paths


def run_duplicate_detection():
    """تشغيل المرحلة الأولى كاملة وإرجاع مسارات المكررات المنقولة"""
    print("=" * 60)
    print("المرحلة 1: كشف المكررات — مشروع Kiro")
    print("=" * 60)

    all_images = get_all_images(FOLDERS)
    if not all_images:
        print("لم يتم العثور على أي صور.")
        return set()

    hashes = compute_hashes(all_images)
    duplicate_groups = find_duplicates(hashes)
    save_duplicates_script(duplicate_groups)
    moved_paths = move_duplicates(duplicate_groups)

    remaining = len(all_images) - len(moved_paths)
    print(f"\n✅ الصور المتبقية بعد إزالة المكررات: {remaining}")
    return moved_paths


# ═══════════════════════════════════════════════
# المرحلة 2: التجميع
# ═══════════════════════════════════════════════

def find_best_threshold(vectors):
    """
    حساب العتبة المثلى تلقائياً بناءً على البيانات
    بتحسب المسافات بين كل الصور وتاخد ربع الأقرب لبعض
    هيك كل مجلد بيحسب عتبته الخاصة بناءً على صوره
    """
    if len(vectors) < 3:
        return 0.3  # قيمة افتراضية لو البيانات قليلة

    distances = pairwise_distances(vectors, metric="cosine")
    # خذ المسافات الفريدة من المثلث العلوي بس (بدون تكرار)
    upper = distances[np.triu_indices_from(distances, k=1)]
    # ربع المسافات الأقرب — يضمن تجميع المتشابه فقط
    threshold = np.percentile(upper, 25)
    return round(float(threshold), 3)


def save_image_cluster_scripts(folder_name, folder_groups):
    """حفظ المجموعات في ملفات .py"""
    script_path = os.path.join(CURRENT_DIR, f"similar_{folder_name}_images.py")

    lines = ['"""', f"مجموعات الصور المتشابهة: {folder_name}", '"""', ""]
    saved_groups = 0

    for group_name, files_dict in folder_groups.items():
        if len(files_dict) < 2:
            continue
        lines.append(f"# {len(files_dict)} صور متشابهة")
        lines.append(f"{group_name} = {{")
        for name, ext in files_dict.items():
            lines.append(f'    "{name.replace(chr(34), chr(92)+chr(34))}": "{ext}",')
        lines.append("}\n")
        saved_groups += 1

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [+] تم حفظ: similar_{folder_name}_images.py ({saved_groups} مجموعة)")


def run_clustering(moved_paths):
    """تشغيل المرحلة الثانية — بتتجاهل الصور المنقولة كمكررات"""
    print("\n" + "=" * 60)
    print("المرحلة 2: تجميع الصور — مشروع Kiro")
    print("=" * 60)

    folders_data = [
        ("desktop",   os.path.join(HOME, "Desktop"),   desktop_images,   desktop_images_vectors),
        ("documents", os.path.join(HOME, "Documents"), documents_images, documents_images_vectors),
        ("downloads", os.path.join(HOME, "Downloads"), downloads_images, downloads_images_vectors),
    ]

    for folder_name, folder_path, files_dict, vectors_dict in folders_data:
        if not files_dict or not vectors_dict:
            continue

        print(f"\n[{folder_name}] جاري تحليل البصمات...")

        valid_paths = []
        valid_vectors = []

        for name, ext in files_dict.items():
            full_path = os.path.normpath(os.path.join(folder_path, name + ext))

            if full_path in moved_paths:
                continue
            if not os.path.exists(full_path):
                print(f"  ⚠ غير موجود، تم تخطيه: {name}{ext}")
                continue
            if name not in vectors_dict:
                continue

            valid_paths.append(full_path)
            valid_vectors.append(vectors_dict[name])

        if len(valid_paths) < 2:
            print("  - لا توجد صور كافية للتجميع.")
            continue

        print(f"  - عدد الصور الصالحة للتجميع: {len(valid_paths)}")

        # ← حساب العتبة تلقائياً بناءً على صور هاد المجلد تحديداً
        threshold = find_best_threshold(valid_vectors)
        print(f"  - العتبة المحسوبة تلقائياً: {threshold}")

        clustering = AgglomerativeClustering(
            n_clusters=None,
<<<<<<< HEAD:clustring/clustring_file_images.py
            metric="cosine",
            distance_threshold=threshold,
            linkage="average",
=======
            distance_threshold=5.0  # مناسب لمتجهات CLIP (المسافات بين 2.77 و 11.91)
>>>>>>> 5ff352f0c0d7ee93308fb17d91d4238d61f86149:clustring_imge/clustring_file_images.py
        )
        clusters = clustering.fit_predict(np.array(valid_vectors))

        cluster_dict = defaultdict(list)
        for path, c_id in zip(valid_paths, clusters):
            cluster_dict[c_id].append(path)

        folder_groups = {}
        group_idx = 1
        for paths_list in cluster_dict.values():
            group_dict = {}
            for p in paths_list:
                if os.path.exists(p):
                    name_only, ext_only = os.path.splitext(os.path.basename(p))
                    group_dict[name_only] = ext_only
            if len(group_dict) >= 2:
                folder_groups[f"{folder_name}_img_group_{group_idx}"] = group_dict
                group_idx += 1

        save_image_cluster_scripts(folder_name, folder_groups)

    print("\n" + "=" * 60)
    print("تم إتمام التجميع بنجاح!")
    print("=" * 60)


# ═══════════════════════════════════════════════
# التشغيل الرئيسي
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    # المرحلة 1: كشف المكررات ونقلها
    moved_paths = run_duplicate_detection()

    # المرحلة 2: تجميع الصور النظيفة فقط
    run_clustering(moved_paths)