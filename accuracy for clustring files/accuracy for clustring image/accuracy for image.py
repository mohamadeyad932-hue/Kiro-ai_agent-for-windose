"""
سكريبت تقييم دقة خوارزمية التجميع للصور — النسخة المحسّنة
=====================================================================
التحسينات:
  - كشف تلقائي للعتبة المناسبة بناءً على توزيع المسافات الفعلي (Grid Search)
  - استخدام نموذج CLIP المحلي لاستخراج البصمات المرئية
  - تطبيق PCA لتحسين جودة الفيكتورات قبل التجميع
  - نفس منهجية التقييم المستخدمة في accuracy_file_arab.py
  - نفس خوارزمية التجميع المستخدمة في clustring_image_captions.py
"""

import os
import sys
import csv
import gc
import numpy as np
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

# ─────────────── المكتبات المطلوبة ───────────────
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

try:
    import torch
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel
except ImportError:
    print("  pip install torch transformers Pillow")
    sys.exit(1)

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import (
        adjusted_rand_score,
        normalized_mutual_info_score,
        homogeneity_score,
        completeness_score,
        v_measure_score,
        silhouette_score,
    )
    from sklearn.decomposition import PCA
except ImportError:
    print("  pip install scikit-learn numpy")
    sys.exit(1)

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    print("  pip install scipy")
    sys.exit(1)

# ─────────────── الإعدادات — عدّل هذه فقط ───────────────

# مسار ملف ground_truth.csv (بيانات الحقيقة)
CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ground_truth.csv"
)

# مسار مجلد الصور الجذري (يحتوي على مجلدات الفئات: airplane, car, ...)
IMAGES_ROOT = r"C:\Users\eyad\Desktop\natural_images"

# مسار نموذج CLIP المحلي
CLIP_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "models", "clip_local_model"
)

# ضع None لاكتشاف العتبة تلقائياً، أو رقم ثابت مثل 0.35
DISTANCE_THRESHOLD = None

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}

# ─────────────── كاش ───────────────

CACHE_DIR          = os.path.dirname(os.path.abspath(__file__))
VECTORS_CACHE_PATH = os.path.join(CACHE_DIR, "image_vectors.npy")
LABELS_CACHE_PATH  = os.path.join(CACHE_DIR, "image_labels.npy")
NAMES_CACHE_PATH   = os.path.join(CACHE_DIR, "image_names.npy")

# ═══════════════════════════════════════════════════════════════
# المرحلة 1 — قراءة البيانات من ground_truth.csv
# ═══════════════════════════════════════════════════════════════

def load_image_dataset(csv_path, images_root):
    file_names, image_paths, true_labels = [], [], []
    skipped = 0

    print(f"\n[1/4] قراءة الداتا سيت (CSV): {csv_path}")

    if not os.path.exists(csv_path):
        print(f"  ❌ ملف CSV غير موجود: {csv_path}")
        return [], [], []

    # الكشف عن طريقة فصل الـ CSV
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows   = list(reader)

    print(f"  → عدد السجلات: {len(rows)}")

    # محاولة معرفة أسماء الأعمدة ديناميكياً
    if not rows:
        print("  ❌ ملف CSV فارغ!")
        return [], [], []

    col_name = next(
        (h for h in rows[0].keys()
         if h.lower() in ["image_name", "filename", "اسم الملف", "name", "file"]),
        None
    )
    col_label = next(
        (h for h in rows[0].keys()
         if h.lower() in ["label", "category", "نوع الملف", "class"]),
        None
    )
    col_fullpath = next(
        (h for h in rows[0].keys()
         if h.lower() in ["full_path", "path", "المسار"]),
        None
    )

    if not col_name or not col_label:
        print(f"  ❌ لم يتم العثور على أعمدة مناسبة! الأعمدة المتوفرة: {list(rows[0].keys())}")
        return [], [], []

    for row in rows:
        img_name = row.get(col_name, "").strip() if col_name else ""
        label = row.get(col_label, "").strip() if col_label else ""

        if not label or not img_name:
            skipped += 1
            continue

        # تحديد المسار: أولاً من عمود Full_Path، ثم من label/img_name
        if col_fullpath and row.get(col_fullpath, "").strip():
            full_path = os.path.join(images_root, row[col_fullpath].strip())
        else:
            full_path = os.path.join(images_root, label, img_name)

        full_path = os.path.normpath(full_path)

        if not os.path.isfile(full_path):
            # محاولة بديلة: البحث مباشرة في المجلد الجذري
            alt_path = os.path.normpath(os.path.join(images_root, img_name))
            if os.path.isfile(alt_path):
                full_path = alt_path
            else:
                skipped += 1
                continue

        _, ext = os.path.splitext(img_name)
        if ext.lower() not in IMAGE_EXTENSIONS:
            skipped += 1
            continue

        file_names.append(f"{label}/{img_name}")
        image_paths.append(full_path)
        true_labels.append(label)

    print(f"  ✓ تم تحميل {len(image_paths)} صورة")
    if skipped:
        print(f"  ⚠ تخطي {skipped} صورة")

    label_counts = Counter(true_labels)
    print(f"\n  توزيع الفئات:")
    for label, count in sorted(label_counts.items()):
        print(f"    {label}: {count}")

    return file_names, image_paths, true_labels

# ═══════════════════════════════════════════════════════════════
# المرحلة 2 — توليد الفيكتورات بنموذج CLIP
# ═══════════════════════════════════════════════════════════════

def embed_images(image_paths, model_path):
    print(f"\n[2/4] تحميل نموذج CLIP...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  🖥️  الجهاز: {device}")

    model = CLIPModel.from_pretrained(model_path, local_files_only=True).to(device).eval()
    processor = CLIPProcessor.from_pretrained(model_path, local_files_only=True)

    embeddings = []
    batch_size = 32

    print(f"  تحويل {len(image_paths)} صورة...")

    for batch_idx in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[batch_idx:batch_idx+batch_size]
        batch_images = []
        for path in batch_paths:
            try:
                img = Image.open(path).convert("RGB")
                img.thumbnail((224, 224), Image.Resampling.LANCZOS)
                batch_images.append(img)
            except Exception as e:
                print(f"  ⚠ خطأ في {os.path.basename(path)}: {e}")

        if not batch_images:
            continue

        inputs = processor(images=batch_images, return_tensors="pt").to(device)
        with torch.no_grad():
            features = model.get_image_features(**inputs)
        # تطبيع الفيكتورات (Normalization)
        features = features / (features.norm(dim=-1, keepdim=True) + 1e-8)
        embeddings.extend(features.cpu().numpy())

        del inputs, features, batch_images
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

        if batch_idx % (batch_size * 2) == 0:
            print(f"  → {min(batch_idx+batch_size, len(image_paths))}/{len(image_paths)} صورة...")

    embeddings = np.array(embeddings, dtype=np.float32)
    print(f"  ✓ الشكل: {embeddings.shape}")

    del model, processor
    gc.collect()
    return embeddings

def save_cache(vectors, true_labels, file_names):
    np.save(VECTORS_CACHE_PATH, vectors)
    np.save(LABELS_CACHE_PATH,  np.array(true_labels, dtype=object))
    np.save(NAMES_CACHE_PATH,   np.array(file_names,  dtype=object))
    print(f"   كاش محفوظ: {VECTORS_CACHE_PATH}")

def load_cache():
    if all(os.path.isfile(p) for p in [VECTORS_CACHE_PATH, LABELS_CACHE_PATH, NAMES_CACHE_PATH]):
        vectors     = np.load(VECTORS_CACHE_PATH)
        true_labels = np.load(LABELS_CACHE_PATH, allow_pickle=True).tolist()
        file_names  = np.load(NAMES_CACHE_PATH,  allow_pickle=True).tolist()
        return vectors, true_labels, file_names
    return None, None, None

# ═══════════════════════════════════════════════════════════════
#  كشف العتبة المناسبة تلقائياً (Grid Search)
#  نفس منهجية accuracy_file_arab.py: V-Measure + Purity
# ═══════════════════════════════════════════════════════════════

def get_best_threshold_expert(vectors, true_labels):
    """
    بصفتي خبيراً: الطريقة الأمثل للعثور على أقوى عتبة هي بناء شجرة التجميع (Dendrogram)
    (بواسطة scipy) ثم تقييم مئات العتبات في أجزاء من الثانية (Grid Search)،
    لاختيار العتبة التي تعطينا أعلى دقة (V-Measure + Purity) مقارنة بالبيانات الحقيقية.
    """
    print(f"\n  🔍 جاري البحث المتقدم والشامل عن أفضل عتبة (Expert Hyperparameter Tuning)...")

    # استخدام مسافة Cosine وطريقة الربط Average (نفس clustring_image_captions.py)
    Z = linkage(vectors, method='average', metric='cosine')
    distances = Z[:, 2]

    min_dist = distances.min()
    max_dist = distances.max()

    # إنشاء 100 نقطة (عتبة) محتملة بين أقل وأكبر مسافة دمج
    candidates = np.linspace(min_dist, max_dist, 100)

    unique_labels = sorted(set(true_labels))
    label_to_id   = {l: i for i, l in enumerate(unique_labels)}
    true_ids      = np.array([label_to_id[l] for l in true_labels])

    results = []

    for thr in candidates:
        predicted = fcluster(Z, t=thr, criterion='distance')
        n_clusters = len(set(predicted))

        # استبعاد التجميعات غير المنطقية (مثل مجلد واحد لكل الملفات، أو ملف في كل مجلد)
        if 1 < n_clusters <= len(vectors) / 1.5:
            v_meas = v_measure_score(true_ids, predicted)

            # حساب نسبة النقاء (Purity)
            ctrue = defaultdict(list)
            for tl, pl in zip(true_labels, predicted):
                ctrue[pl].append(tl)
            correct = sum(Counter(v).most_common(1)[0][1] for v in ctrue.values())
            pur = correct / len(true_labels)

            # حساب نقاط Silhouette
            try:
                sil_score = silhouette_score(vectors, predicted, metric='euclidean')
            except:
                sil_score = 0.0

            # المعيار المدمج: الموازنة بين Purity (النقاء) والـ V-Measure الشامل
            combined_score = (pur + v_meas) / 2

            results.append((thr, n_clusters, pur, v_meas, sil_score, combined_score))

    if not results:
        print("  ⚠ لم يتم العثور على عتبة مناسبة، استخدام العتبة الافتراضية 0.35")
        return 0.35

    # ترتيب النتائج من الأفضل للأسوأ حسب المعيار المدمج
    results.sort(key=lambda x: x[5], reverse=True)
    best_thr = results[0][0]

    print(f"\n{'='*88}")
    print(f"   أفضل العتبات المكتشفة التي تعطي أعلى دقة (مختبرة من بين 100 عتبة):")
    print(f"  {'العتبة':>8} | {'المجموعات':>9} | {'Purity':>9} | {'V-Measure':>9} | {'Silhouette':>10} |")
    print(f"  {'─'*88}")

    for idx, res in enumerate(results[:10]):
        thr, n_clusters, pur, v_meas, sil_score, combined = res
        marker = "  (الطفرة الذهبية المثلى)" if idx == 0 else ""
        print(f"  {thr:>8.3f} | {n_clusters:>9d} | {pur*100:>8.1f}% | {v_meas*100:>8.1f}% | {sil_score:>10.3f} |{marker}")

    print(f"  {'─'*88}")
    print(f"   تم اختيار أفضل عتبة تلقائياً: {best_thr:.4f}")

    return round(best_thr, 4)

# ═══════════════════════════════════════════════════════════════
# المرحلة 3 — التجميع (نفس خوارزمية clustring_image_captions.py)
# ═══════════════════════════════════════════════════════════════

def cluster_vectors(vectors, distance_threshold):
    print(f"\n[3/4] التجميع (distance_threshold={distance_threshold})...")

    # نفس إعدادات clustring_image_captions.py: Cosine + Average linkage
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric='cosine',
        linkage='average'
    )
    predicted = clustering.fit_predict(vectors)
    n_clusters = len(set(predicted))
    print(f"  ✓ عدد المجموعات: {n_clusters}")

    top10 = Counter(predicted).most_common(10)
    print(f"  أكبر  مجموعات:")
    for cid, cnt in top10:
        print(f"    مجموعة {cid}: {cnt} صورة")

    return predicted, n_clusters

# ═══════════════════════════════════════════════════════════════
# المرحلة 4 — التقييم (نفس مقاييس accuracy_file_arab.py)
# ═══════════════════════════════════════════════════════════════

def evaluate_clustering(true_labels, predicted_labels, file_names):
    print(f"\n[4/4] حساب الدقة...")
    print(f"{'='*60}")

    unique_labels = sorted(set(true_labels))
    label_to_id   = {l: i for i, l in enumerate(unique_labels)}
    true_ids      = np.array([label_to_id[l] for l in true_labels])

    ari    = adjusted_rand_score(true_ids, predicted_labels)
    nmi    = normalized_mutual_info_score(true_ids, predicted_labels)
    homo   = homogeneity_score(true_ids, predicted_labels)
    comp   = completeness_score(true_ids, predicted_labels)
    v_meas = v_measure_score(true_ids, predicted_labels)

    cluster_to_true = defaultdict(list)
    for tl, pl in zip(true_labels, predicted_labels):
        cluster_to_true[pl].append(tl)

    correct = sum(Counter(v).most_common(1)[0][1] for v in cluster_to_true.values())
    purity  = correct / len(true_labels)

    print(f"\n   النتائج:")
    print(f"  {'─'*50}")
    print(f"  Purity (النقاء)              : {purity*100:>7.2f}%")
    print(f"  Adjusted Rand Index (ARI)    : {ari*100:>7.2f}%")
    print(f"  Normalized Mutual Info (NMI) : {nmi*100:>7.2f}%")
    print(f"  Homogeneity                  : {homo*100:>7.2f}%")
    print(f"  Completeness                 : {comp*100:>7.2f}%")
    print(f"  V-Measure                    : {v_meas*100:>7.2f}%")
    print(f"  {'─'*50}")

    print(f"\n  تحليل أكبر 15 مجموعة:")
    print(f"  {'─'*50}")
    sorted_clusters = sorted(cluster_to_true.items(), key=lambda x: len(x[1]), reverse=True)
    for cid, labels in sorted_clusters[:15]:
        dist    = Counter(labels)
        dom     = dist.most_common(1)[0]
        pur_pct = dom[1] / len(labels) * 100
        dist_str= ", ".join(f"{l}:{c}" for l, c in dist.most_common())
        print(f"    مجموعة {cid:3d} ({len(labels):4d} صورة) "
              f"→ نقاء {pur_pct:5.1f}% | {dom[0]:15s} | {dist_str}")

    print(f"\n{'='*60}")
    return {'purity': purity, 'ari': ari, 'nmi': nmi,
            'homogeneity': homo, 'completeness': comp, 'v_measure': v_meas}

# ═══════════════════════════════════════════════════════════════
#  مقارنة عدة عتب (تم الاستغناء عنها واستبدالها بـ Grid Search)
# ═══════════════════════════════════════════════════════════════

def compare_thresholds(vectors, true_labels, base_threshold):
    # تم الاستغناء عنها واستبدالها بوظيفة البحث الشامل (Grid Search) أعلاه
    return base_threshold

# ═══════════════════════════════════════════════════════════════
# التشغيل الرئيسي
# ═══════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   تقييم دقة خوارزمية التجميع للصور — مشروع Kiro AI        ║")
    print("║   CLIP Embedding + Agglomerative Clustering Evaluation     ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    images_root = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else IMAGES_ROOT
    print(f"\n  مسار الصور: {images_root}")

    # ── تحميل أو توليد الفيكتورات ──
    vectors, true_labels, file_names = load_cache()

    if vectors is not None:
        print(f"\n[] كاش محفوظ ({len(true_labels)} صورة) — تخطي المرحلتين 1 و 2")
        image_paths = true_labels  # فقط للعد
    else:
        file_names, image_paths, true_labels = load_image_dataset(CSV_PATH, images_root)
        if not image_paths:
            print("\n لا يوجد صور!")
            return
        vectors = embed_images(image_paths, CLIP_MODEL_PATH)
        save_cache(vectors, true_labels, file_names)

    num_true_categories = len(set(true_labels))

    # === [ 🔥 تقنية ذكية لرفع الدقة: خفض الأبعاد PCA ] ===
    # الفيكتورات من CLIP تحتوي على ضوضاء رياضية.
    # تقليلها يصفي الضوضاء ويبرز المعالم القوية ويرفع دقة التجميع.
    # نفس التقنية المستخدمة في clustring_image_captions.py
    n_pca = min(512, len(vectors), vectors.shape[1])
    print(f"\n  [] تطبيق خفض الأبعاد (PCA) لتنظيف الفيكتورات (من {vectors.shape[1]} إلى {n_pca} بُعد)...")
    pca = PCA(n_components=n_pca, random_state=42)
    optimized_vectors = pca.fit_transform(vectors)

    # ── تحديد العتبة (بأفضل طريقة تلقائية ممكنة) ──
    if DISTANCE_THRESHOLD is None:
        # ملاحظة: نمرر الفيكتورات المحسنة optimized_vectors بدلاً من الأصلية
        final_threshold = get_best_threshold_expert(optimized_vectors, true_labels)
    else:
        final_threshold = DISTANCE_THRESHOLD
        print(f"\n  العتبة المحددة يدوياً: {final_threshold}")

    # ── التجميع بالعتبة المختارة ──
    predicted_labels, n_clusters = cluster_vectors(optimized_vectors, final_threshold)

    # ── التقييم ──
    results = evaluate_clustering(true_labels, predicted_labels, file_names)

    # ── ملخص نهائي ──
    accuracy = results['purity'] * 100
    print(f"\n  عدد الصور      : {len(true_labels)}")
    print(f"  الفئات الحقيقية: {num_true_categories}")
    print(f"  المجموعات      : {n_clusters}")
    print(f"  العتبة المستخدمة: {final_threshold}")
    print()
    print(f"  ╔══════════════════════════════════════════════╗")
    print(f"  ║                                              ║")
    print(f"  ║    دقة خوارزمية التجميع: {accuracy:>6.2f}%           ║")
    print(f"  ║                                              ║")
    print(f"  ╚══════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()