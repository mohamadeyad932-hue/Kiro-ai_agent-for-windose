"""
images_pipeline.py
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
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
except ImportError:
    print("pip install scikit-learn numpy")
    sys.exit(1)

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    print("pip install scipy")
    sys.exit(1)

# الاعدادات

HOME = os.path.expanduser("~")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSING_DIR = os.path.join(CURRENT_DIR, "..", "Processing image")
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

# منطق المسارات المخصصة (Custom Path)
custom_path = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else None

if custom_path:
    FOLDERS = {"custom_folder": custom_path}
else:
    FOLDERS = {
        "desktop": os.path.join(HOME, "Desktop"),
        "documents": os.path.join(HOME, "Documents"),
        "downloads": os.path.join(HOME, "Downloads"),
    }

EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".jfif"}
THRESHOLD = 12
DUPLICATES_DIR = os.path.join(HOME, "Desktop", "Kiro_Duplicates")

def dynamic_import(name):
    """استيراد الوحدات ديناميكيا لتجنب اخطاء الاستيراد الثابتة"""
    import importlib
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


# كشف العتبة تلقائيا عبر Dendrogram + Silhouette
def auto_find_best_threshold(vectors):
    """
    يبني شجرة التجميع مرة واحدة ثم يجرب 100 عتبة
    ويختار العتبة التي تعطي اعلى Silhouette Score
    بدون الحاجة لبيانات حقيقية (ground truth)
    """
    print(f"  Searching for best threshold (Dendrogram + Silhouette)...")
    
    # بناء الشجرة الهرمية بمسافة Cosine وطريقة الربط Average
    Z = linkage(vectors, method='average', metric='cosine')
    distances = Z[:, 2]
    
    min_dist = distances.min()
    max_dist = distances.max()
    
    # انشاء 100 نقطة (عتبة) محتملة بين اقل واكبر مسافة دمج
    candidates = np.linspace(min_dist, max_dist, 100)
    
    best_thr = None
    best_sil = -1
    best_n   = 0
    results  = []
    
    for thr in candidates:
        predicted = fcluster(Z, t=thr, criterion='distance')
        n_clusters = len(set(predicted))
        
        # استبعاد التجميعات غير المنطقية
        if 2 <= n_clusters <= len(vectors) / 1.5:
            try:
                sil = silhouette_score(vectors, predicted, metric='cosine')
            except:
                sil = -1.0
            
            results.append((thr, n_clusters, sil))
            
            if sil > best_sil:
                best_sil = sil
                best_thr = thr
                best_n   = n_clusters
    
    if best_thr is None:
        # fallback: اذا فشلت كل العتبات نستخدم النقطة الوسطى
        best_thr = (min_dist + max_dist) / 2
        print(f"  No optimal threshold found, using midpoint: {best_thr:.4f}")
    else:
        print(f"  Best threshold found: {best_thr:.4f} (clusters: {best_n}, Silhouette: {best_sil:.3f})")
    
    # طباعة افضل 5 نتائج
    results.sort(key=lambda x: x[2], reverse=True)
    if results:
        print(f"  {'-'*55}")
        print(f"  {'Threshold':>10} | {'Clusters':>9} | {'Silhouette':>10}")
        print(f"  {'-'*55}")
        for i, (thr, n, sil) in enumerate(results[:5]):
            marker = " *" if i == 0 else ""
            print(f"  {thr:>8.4f} | {n:>9d} | {sil:>10.3f}{marker}")
        print(f"  {'-'*55}")
    
    return round(best_thr, 4)


# المرحلة 1: كشف المكررات

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
            print(f"  No permission: {folder_path}")
    return all_images


def compute_hashes(all_images):
    """حساب البصمة الادراكية لكل صورة"""
    hashes = {}
    print(f"\nComputing hashes for {len(all_images)} images...")
    for path in all_images:
        try:
            img = Image.open(path).convert("RGB")
            hashes[path] = imagehash.phash(img)
        except Exception as e:
            print(f"  Error: {os.path.basename(path)} - {e}")
    return hashes


def find_duplicates(hashes):
    """ايجاد الصور المتشابهة بمقارنة كل الازواج"""
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
    """حفظ المكررات في قاموس موحد"""
    script_path = os.path.join(CURRENT_DIR, "duplicates_images.py")

    all_duplicates = {}
    for group in duplicate_groups:
        sorted_group = sorted(group)
        for dup_path in sorted_group[1:]:
            name, ext = os.path.splitext(os.path.basename(dup_path))
            all_duplicates[name] = ext.lower()

    lines = [
        '"""',
        "Duplicate images dictionary - auto generated",
        "Each entry: filename without extension -> extension",
        '"""',
        "",
        f"# Total duplicates: {len(all_duplicates)} images",
        "duplicates = {",
    ]
    for name, ext in all_duplicates.items():
        lines.append(f'    "{name.replace(chr(34), chr(92)+chr(34))}": "{ext}",')
    lines.append("}\n")

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [+] Saved: duplicates_images.py ({len(all_duplicates)} duplicates)")


def move_duplicates(duplicate_groups):
    """نقل المكررات لمجلد خاص وارجاع مسارات الصور المنقولة"""
    moved_paths = set()

    if not duplicate_groups:
        print("\nNo duplicate images found.")
        return moved_paths

    os.makedirs(DUPLICATES_DIR, exist_ok=True)
    print(f"\nFound {len(duplicate_groups)} duplicate groups:")
    print(f"Moving duplicates to: {DUPLICATES_DIR}\n")

    for i, group in enumerate(duplicate_groups, 1):
        sorted_group = sorted(group)
        original = sorted_group[0]
        duplicates = sorted_group[1:]

        print(f"  Group {i}:")
        print(f"    Keep: {os.path.basename(original)}")

        for dup in duplicates:
            dest = os.path.join(DUPLICATES_DIR, os.path.basename(dup))
            if os.path.exists(dest):
                name, ext = os.path.splitext(os.path.basename(dup))
                dest = os.path.join(DUPLICATES_DIR, f"{name}_dup{i}{ext}")
            try:
                shutil.move(dup, dest)
                moved_paths.add(dup)
                print(f"    Moved: {os.path.basename(dup)}")
            except Exception as e:
                print(f"    Error moving: {e}")

    return moved_paths


def run_duplicate_detection():
    """تشغيل المرحلة الاولى كاملة وارجاع مسارات المكررات المنقولة"""
    print("=" * 60)
    print("Phase 1: Duplicate Detection - Kiro Project")
    print("=" * 60)

    all_images = get_all_images(FOLDERS)
    if not all_images:
        print("No images found.")
        return set()

    hashes = compute_hashes(all_images)
    duplicate_groups = find_duplicates(hashes)
    save_duplicates_script(duplicate_groups)
    moved_paths = move_duplicates(duplicate_groups)

    remaining = len(all_images) - len(moved_paths)
    print(f"\nRemaining images after removing duplicates: {remaining}")
    return moved_paths


# المرحلة 2: التجميع

def save_image_cluster_scripts(folder_name, folder_groups):
    """حفظ المجموعات في ملفات .py"""
    script_path = os.path.join(CURRENT_DIR, f"similar_{folder_name}_images.py")

    lines = ['"""', f"Similar image groups: {folder_name}", '"""', ""]
    saved_groups = 0

    for group_name, files_dict in folder_groups.items():
        if len(files_dict) < 2:
            continue
        lines.append(f"# {len(files_dict)} similar images")
        lines.append(f"{group_name} = {{")
        for name, ext in files_dict.items():
            lines.append(f'    "{name.replace(chr(34), chr(92)+chr(34))}": "{ext}",')
        lines.append("}\n")
        saved_groups += 1

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [+] Saved: similar_{folder_name}_images.py ({saved_groups} groups)")


def run_clustering(moved_paths):
    """تشغيل المرحلة الثانية مع تجاهل الصور المنقولة كمكررات"""
    print("\n" + "=" * 60)
    print("Phase 2: Image Clustering - Kiro Project")
    print("Techniques: PCA + Cosine Distance + Auto Threshold")
    print("=" * 60)

    for folder_name, folder_path in FOLDERS.items():
        # تحميل البيانات ديناميكيا لكل مجلد
        mod_files = dynamic_import(f"{folder_name}_images_files")
        mod_vectors = dynamic_import(f"{folder_name}_images_vectors")
        
        files_dict = getattr(mod_files, f"{folder_name}_images", {}) if mod_files else {}
        vectors_dict = getattr(mod_vectors, f"{folder_name}_images_vectors", {}) if mod_vectors else {}

        if not files_dict or not vectors_dict:
            print(f"  [!] No embeddings found for {folder_name}, skipping.")
            continue

        print(f"\n[{folder_name}] Analyzing embeddings...")

        valid_paths = []
        valid_vectors = []

        for name, ext in files_dict.items():
            full_path = os.path.normpath(os.path.join(folder_path, name + ext))

            # تجاهل الصور المنقولة كمكررات + التحقق من الوجود
            if full_path in moved_paths:
                continue
            if not os.path.exists(full_path):
                print(f"  Not found, skipping: {name}{ext}")
                continue
            if name not in vectors_dict:
                continue

            valid_paths.append(full_path)
            valid_vectors.append(vectors_dict[name])

        if len(valid_paths) < 2:
            print("  - Not enough images for clustering.")
            continue

        print(f"  - Valid images for clustering: {len(valid_paths)}")

        vectors_array = np.array(valid_vectors)

        # خفض الابعاد PCA - تنظيف الفيكتورات من الضوضاء
        n_pca = min(386, len(valid_paths), vectors_array.shape[1])
        print(f"  PCA dimensionality reduction ({vectors_array.shape[1]} -> {n_pca})...")
        pca = PCA(n_components=n_pca, random_state=42)
        optimized_vectors = pca.fit_transform(vectors_array)

        # كشف العتبة تلقائيا
        best_threshold = auto_find_best_threshold(optimized_vectors)

        # التجميع بمسافة Cosine
        print(f"  Clustering with optimal threshold: {best_threshold}...")
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="cosine",
            distance_threshold=best_threshold,
            linkage="average",
        )
        clusters = clustering.fit_predict(optimized_vectors)

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
    print("Clustering completed successfully!")
    print("=" * 60)


# التشغيل الرئيسي

if __name__ == "__main__":
    # المرحلة 1: كشف المكررات ونقلها
    moved_paths = run_duplicate_detection()

    # المرحلة 2: تجميع الصور النظيفة فقط
    run_clustering(moved_paths)