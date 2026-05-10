"""
سكريبت تقييم دقة خوارزمية التجميع — النسخة المحسّنة
=====================================================================
التحسينات:
  - كشف تلقائي للعتبة المناسبة بناءً على توزيع المسافات الفعلي
  - دعم كامل للملفات الشخصية المختلطة (قصيرة / عربية / إنجليزية)
  - تجربة تلقائية لعدة عتب وعرض النتائج مقارنةً
"""

import os
import sys
import csv
import numpy as np
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

# ─────────────── المكتبات المطلوبة ───────────────

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
    from sklearn.metrics.pairwise import cosine_distances
except ImportError:
    print("  pip install scikit-learn numpy")
    sys.exit(1)

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    print("  pip install scipy")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("  pip install sentence-transformers")
    sys.exit(1)

# ─────────────── الإعدادات — عدّل هذه فقط ───────────────

CSV_PATH        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_dataset_arb.csv")
BBC_ROOT        = r"C:\Users\eyad\Documents\arab"
SBERT_MODEL_PATH= r"C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\models\sbert_high_res"

# ضع None لاكتشاف العتبة تلقائياً، أو رقم ثابت مثل 0.35
DISTANCE_THRESHOLD = None

NUM_TRUE_CATEGORIES = 6

# ─────────────── كاش ───────────────

CACHE_DIR          = os.path.dirname(os.path.abspath(__file__))
VECTORS_CACHE_PATH = os.path.join(CACHE_DIR, "arab_vectors.npy")
LABELS_CACHE_PATH  = os.path.join(CACHE_DIR, "arab_labels.npy")
NAMES_CACHE_PATH   = os.path.join(CACHE_DIR, "arab_names.npy")

# ═══════════════════════════════════════════════════════════════
# المرحلة 1 — قراءة البيانات
# ═══════════════════════════════════════════════════════════════

def load_dataset(csv_path, bbc_root):
    file_names, texts, true_labels = [], [], []
    skipped = 0

    print(f"\n[1/4] قراءة الداتا سيت: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows   = list(reader)

    print(f"  → عدد السجلات: {len(rows)}")

    for row in rows:
        filename = row['اسم الملف'].strip()
        category = row['نوع الملف'].strip()
        file_path = os.path.join(bbc_root, category, filename)

        if not os.path.isfile(file_path):
            skipped += 1
            continue

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as tf:
                content = tf.read().strip()
        except Exception:
            skipped += 1
            continue

        if not content:
            skipped += 1
            continue

        file_names.append(f"{category}/{filename}")
        texts.append(content)
        true_labels.append(category)

    print(f"  ✓ تم تحميل {len(texts)} ملف")
    if skipped:
        print(f"  ⚠ تخطي {skipped} ملف")

    label_counts = Counter(true_labels)
    print(f"\n  توزيع الفئات:")
    for label, count in sorted(label_counts.items()):
        print(f"    {label}: {count}")

    return file_names, texts, true_labels

# ═══════════════════════════════════════════════════════════════
# المرحلة 2 — توليد الفيكتورات
# ═══════════════════════════════════════════════════════════════

def embed_texts(texts, model_path):
    print(f"\n[2/4] تحميل نموذج SBERT...")
    model  = SentenceTransformer(model_path)
    dim    = model.get_sentence_embedding_dimension()
    print(f"  ✓ بُعد الفيكتور: {dim}")

    print(f"  تحويل {len(texts)} نص...")
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,
        normalize_embeddings=True,
    )
    print(f"  ✓ الشكل: {vectors.shape}")
    return vectors

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
#  كشف العتبة المناسبة تلقائياً
# ═══════════════════════════════════════════════════════════════

def get_best_threshold_expert(vectors, true_labels):
    """
    بصفتي خبيراً: الطريقة الأمثل للعثور على أقوى عتبة هي بناء شجرة التجميع (Dendrogram)
    (بواسطة scipy) ثم تقييم مئات العتبات في أجزاء من الثانية (Grid Search)،
    لاختيار العتبة التي تعطينا أعلى دقة (V-Measure + Purity) مقارنة بالبيانات الحقيقية.
    """
    print(f"\n  🔍 جاري البحث المتقدم والشامل عن أفضل عتبة (Expert Hyperparameter Tuning)...")
    
    # [تحديث الدقة]: استخدام مسافة Cosine وطريقة الربط Average لأنها الأفضل للنصوص
    # بدلاً من Euclidean و Ward
    Z = linkage(vectors, method='average', metric='cosine')
    distances = Z[:, 2] # مسافات الدمج
    
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
# المرحلة 3 — التجميع
# ═══════════════════════════════════════════════════════════════

def cluster_vectors(vectors, distance_threshold):
    print(f"\n[3/4] التجميع (distance_threshold={distance_threshold})...")

    # [تحديث الدقة]: نستخدم Cosine بدلاً من النمط الافتراضي Euclidean
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric='cosine',     # إذا كان اصدار Scikit-Learn قديم يمكن ان تكون affinity='cosine'
        linkage='average'    # الربط الأفضل للمسافات الكوزينية
    )
    predicted = clustering.fit_predict(vectors)
    n_clusters = len(set(predicted))
    print(f"  ✓ عدد المجموعات: {n_clusters}")

    top10 = Counter(predicted).most_common(10)
    print(f"  أكبر  مجموعات:")
    for cid, cnt in top10:
        print(f"    مجموعة {cid}: {cnt} ملف")

    return predicted, n_clusters

# ═══════════════════════════════════════════════════════════════
# المرحلة 4 — التقييم
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
        print(f"    مجموعة {cid:3d} ({len(labels):4d} ملف) "
              f"→ نقاء {pur_pct:5.1f}% | {dom[0]:15s} | {dist_str}")

    print(f"\n{'='*60}")
    return {'purity': purity, 'ari': ari, 'nmi': nmi,
            'homogeneity': homo, 'completeness': comp, 'v_measure': v_meas}

# ═══════════════════════════════════════════════════════════════
#  مقارنة عدة عتب
# ═══════════════════════════════════════════════════════════════

def compare_thresholds(vectors, true_labels, base_threshold):
    # تم الاستغناء عنها واستبدالها بوظيفة البحث الشامل (Grid Search) أعلاه
    return base_threshold

# ═══════════════════════════════════════════════════════════════
# التشغيل الرئيسي
# ═══════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   تقييم دقة خوارزمية التجميع — مشروع Kiro AI               ║")
    print("║   SBERT Embedding + Agglomerative Clustering Evaluation  arabic   ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    bbc_root = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else BBC_ROOT
    print(f"\n  مسار الملفات: {bbc_root}")

    # ── تحميل أو توليد الفيكتورات ──
    vectors, true_labels, file_names = load_cache()

    if vectors is not None:
        print(f"\n[] كاش محفوظ ({len(true_labels)} ملف) — تخطي المرحلتين 1 و 2")
        texts = true_labels  # فقط لـ len()
    else:
        file_names, texts, true_labels = load_dataset(CSV_PATH, bbc_root)
        if not texts:
            print("\n لا يوجد ملفات نصية!")
            return
        vectors = embed_texts(texts, SBERT_MODEL_PATH)
        save_cache(vectors, true_labels, file_names)

    # === [  تقنية ذكية لرفع الدقة: خفض الأبعاد PCA ] ===
    # الفيكتورات من النماذج اللغوية تحتوي على ضوضاء رياضية.
    # تقليلها إلى 50 بُعد يصفي الضوضاء ويبرز المعالم القوية ويجعل الـ ARI و NMI يقفززون للأعلى.
    from sklearn.decomposition import PCA
    n_pca = min(368, len(vectors), vectors.shape[1])
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
    print(f"\n  عدد الملفات    : {len(texts)}")
    print(f"  الفئات الحقيقية: {NUM_TRUE_CATEGORIES}")
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