"""
IMBADING_IMAG.py — Image Clustering Accuracy Evaluation (v2.1 fixed)
======================================================================================
Improvements:
  ✅ Support --fresh to ignore cache
  ✅ Correct column reflects image accuracy within its group
  ✅ Removed false ground_truth verification
  ✅ Threshold selection using V-Measure only
  ✅ Number of real categories calculated automatically
  ✅ Unified step numbering
  ✅ Fast batch processing (batch size 16)
"""

import os
import sys
import csv
import gc
import numpy as np
from collections import defaultdict, Counter
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# ─────────────── Required Libraries ───────────────
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
    from sklearn.model_selection import train_test_split
except ImportError:
    print("  pip install scikit-learn numpy")
    sys.exit(1)

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    print("  pip install scipy")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# ─────────────── Settings — Modify These Only ───────────────
# ═══════════════════════════════════════════════════════════════

CSV_PATH = r"E:\data\ground_truth.csv"
IMAGES_ROOT = r"E:\data\archive\natural_images"
CLIP_MODEL = r"C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\models\clip_local_model"
DISTANCE_THRESHOLD = None       # None = Auto-detect
EVALUATION_MODE = 'full_data'   # 'train_test' or 'full_data'

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORS_CACHE_PATH = os.path.join(CACHE_DIR, "cached_vectors.npy")
LABELS_CACHE_PATH  = os.path.join(CACHE_DIR, "cached_labels.npy")
NAMES_CACHE_PATH   = os.path.join(CACHE_DIR, "cached_names.npy")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}

# ═══════════════════════════════════════════════════════════════
# 🔧 Function: Auto-detect CSV Settings
# ═══════════════════════════════════════════════════════════════

def detect_csv_config(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()

    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    headers = [h.strip().strip('"') for h in first_line.strip().split(delimiter)]

    def find_col(candidates):
        for c in candidates:
            if c in headers:
                return c
        for c in candidates:
            for h in headers:
                if c.lower() in h.lower():
                    return h
        return None

    col_name = find_col(["Image_Name", "image_name", "filename", "File Name", "name", "file"])
    col_label = find_col(["Label", "label", "category", "Category", "File Type", "class", "Class"])
    col_fullpath = find_col(["Full_Path", "full_path", "path", "Path", "Path"])

    return delimiter, col_name, col_label, col_fullpath

# ═══════════════════════════════════════════════════════════════
# Phase 1 — Read CSV and Build Image List
# ═══════════════════════════════════════════════════════════════

def load_image_paths(csv_path, images_root):
    print(f"\n[1/4] Reading Dataset: {csv_path}")
    delimiter, col_name, col_label, col_fullpath = detect_csv_config(csv_path)

    if col_name is None or col_label is None:
        print("❌ Could not identify columns.")
        sys.exit(1)

    image_paths, true_labels, file_names = [], [], []
    skipped = 0

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

    print(f"  → Number of records: {len(rows)}")

    for row in rows:
        label = row.get(col_label, "").strip()
        img_name = row.get(col_name, "").strip()
        if not label or not img_name:
            skipped += 1
            continue

        if col_fullpath and row.get(col_fullpath, "").strip():
            relative_path = row[col_fullpath].strip()
            full_path = os.path.join(images_root, relative_path)
        else:
            full_path = os.path.join(images_root, label, img_name)

        full_path = os.path.normpath(full_path)
        if not os.path.isfile(full_path):
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

        image_paths.append(full_path)
        true_labels.append(label)
        file_names.append(f"{label}/{img_name}")

    print(f"  ✓ Images loaded: {len(image_paths)}")
    if skipped:
        print(f"  ⚠ Records skipped: {skipped}")
    if not image_paths:
        print("❌ No images found!")
        sys.exit(1)

    counts = Counter(true_labels)
    print(f"\n  Category Distribution:")
    for lbl, cnt in sorted(counts.items()):
        print(f"    {lbl}: {cnt} images")
    return image_paths, true_labels, file_names

# ═══════════════════════════════════════════════════════════════
# Phase 2 — Extract CLIP Embeddings
# ═══════════════════════════════════════════════════════════════

def extract_clip_embeddings(image_paths, clip_model_name):
    print(f"\n[2/4] Loading CLIP: {clip_model_name}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  🖥️  Device: {device}")

    model = CLIPModel.from_pretrained(clip_model_name)
    processor = CLIPProcessor.from_pretrained(clip_model_name)
    model = model.to(device).eval()

    embeddings, valid_paths = [], []
    batch_size = 16

    for batch_idx in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[batch_idx:batch_idx+batch_size]
        batch_images, batch_valid = [], []
        for path in batch_paths:
            try:
                img = Image.open(path).convert("RGB")
                img.thumbnail((224, 224), Image.Resampling.LANCZOS)
                batch_images.append(img)
                batch_valid.append(path)
            except Exception as e:
                print(f"  ⚠ Error in {os.path.basename(path)}: {e}")

        if not batch_images:
            continue

        inputs = processor(images=batch_images, return_tensors="pt").to(device)  # type: ignore
        with torch.no_grad():
            features = model.get_image_features(**inputs)
        features = features / (features.norm(dim=-1, keepdim=True) + 1e-8)
        embeddings.extend(features.cpu().numpy())
        valid_paths.extend(batch_valid)

        del inputs, features, batch_images
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

        if batch_idx % (batch_size * 10) == 0:
            print(f"  → {min(batch_idx+batch_size, len(image_paths))}/{len(image_paths)} images...")

    embeddings = np.array(embeddings, dtype=np.float32)
    print(f"  ✓ Embeddings: {embeddings.shape}")
    del model, processor
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    return embeddings, valid_paths

# ═══════════════════════════════════════════════════════════════
# Cache
# ═══════════════════════════════════════════════════════════════

def save_cache(vectors, true_labels, file_names):
    np.save(VECTORS_CACHE_PATH, vectors)
    np.save(LABELS_CACHE_PATH, np.array(true_labels, dtype=object))
    np.save(NAMES_CACHE_PATH, np.array(file_names, dtype=object))
    print(f"  💾 Cache saved ({len(true_labels)} items)")

def load_cache(skip_cache=False):
    if skip_cache:
        print("  ⚠️  Cache ignored (--fresh)")
        return None, None, None
    if all(os.path.isfile(p) for p in [VECTORS_CACHE_PATH, LABELS_CACHE_PATH, NAMES_CACHE_PATH]):
        vectors = np.load(VECTORS_CACHE_PATH)
        true_labels = np.load(LABELS_CACHE_PATH, allow_pickle=True).tolist()
        file_names = np.load(NAMES_CACHE_PATH, allow_pickle=True).tolist()
        print(f"  ✅ Cache loaded ({len(true_labels)} images)")
        return vectors, true_labels, file_names
    return None, None, None

# ═══════════════════════════════════════════════════════════════
# Best Threshold Selection (V-Measure only)
# ═══════════════════════════════════════════════════════════════

def get_best_threshold(vectors_train, true_labels_train):
    print(f"\n  🔍 Searching for best threshold (V-Measure) on training set...")
    Z = linkage(vectors_train, method="average", metric="cosine")
    distances = Z[:, 2]
    candidates = np.linspace(distances.min(), distances.max(), 50)

    label_to_id = {l: i for i, l in enumerate(sorted(set(true_labels_train)))}
    true_ids = np.array([label_to_id[l] for l in true_labels_train])

    results = []
    for thr in candidates:
        predicted = fcluster(Z, t=thr, criterion="distance")
        n_clusters = len(set(predicted))
        if 1 < n_clusters <= len(vectors_train) / 1.5:
            v_meas = v_measure_score(true_ids, predicted)
            results.append((thr, n_clusters, v_meas))

    if not results:
        print("  ⚠ Using default threshold 0.35")
        return 0.35

    results.sort(key=lambda x: x[2], reverse=True)  # Sort descending by V-Measure
    best_thr = results[0][0]
    print(f"  ✅ Best threshold: {best_thr:.4f} (V-Measure={results[0][2]*100:.1f}%)")
    return round(best_thr, 4)

# ═══════════════════════════════════════════════════════════════
# Clustering
# ═══════════════════════════════════════════════════════════════

def cluster_vectors(vectors, distance_threshold):
    print(f"  → Hierarchical clustering (threshold={distance_threshold})...")
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    predicted = clustering.fit_predict(vectors)
    n_clusters = len(set(predicted))
    print(f"  ✓ Number of clusters: {n_clusters}")
    return predicted, n_clusters

# ═══════════════════════════════════════════════════════════════
# Evaluation
# ═══════════════════════════════════════════════════════════════

def evaluate_clustering(true_labels, predicted_labels, file_names):
    print(f"\n  📊 Calculating clustering metrics...")
    label_to_id = {l: i for i, l in enumerate(sorted(set(true_labels)))}
    true_ids = np.array([label_to_id[l] for l in true_labels])

    ari = adjusted_rand_score(true_ids, predicted_labels)
    nm = normalized_mutual_info_score(true_ids, predicted_labels)
    homo = homogeneity_score(true_ids, predicted_labels)
    comp = completeness_score(true_ids, predicted_labels)
    v_meas = v_measure_score(true_ids, predicted_labels)

    # Purity calculation
    cluster_to_true = defaultdict(list)
    for tl, pl in zip(true_labels, predicted_labels):
        cluster_to_true[pl].append(tl)

    correct = sum(Counter(v).most_common(1)[0][1] for v in cluster_to_true.values())
    purity = correct / len(true_labels)

    print(f"    Purity           : {purity*100:.2f}%")
    print(f"    ARI              : {ari*100:.2f}%")
    print(f"    NMI              : {nm*100:.2f}%")
    print(f"    Homogeneity      : {homo*100:.2f}%")
    print(f"    Completeness     : {comp*100:.2f}%")
    print(f"    V-Measure        : {v_meas*100:.2f}%")

    # Save results with correct Correct column
    save_results_to_csv(true_labels, predicted_labels, file_names, cluster_to_true)

    return {"purity": purity, "ari": ari, "nmi": nm,
            "homogeneity": homo, "completeness": comp, "v_measure": v_meas}

# ═══════════════════════════════════════════════════════════════
# 💾 Save Results with Corrected "Correct" Column
# ═══════════════════════════════════════════════════════════════

def save_results_to_csv(true_labels, predicted_labels, file_names, cluster_to_true):
    # Create mapping: cluster_id → majority label
    cluster_majority = {}
    for cluster_id, labels in cluster_to_true.items():
        majority_label = Counter(labels).most_common(1)[0][0]
        cluster_majority[cluster_id] = majority_label

    # For each image: is its true label equal to the cluster's majority label?
    correct_flags = [
        true_labels[i] == cluster_majority[predicted_labels[i]]
        for i in range(len(true_labels))
    ]

    output_csv = os.path.join(os.path.dirname(__file__), "metadata", "clustered_results.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df = pd.DataFrame({
        "File_Name": file_names,
        "True_Label": true_labels,
        "Predicted_Cluster": predicted_labels,
        "Cluster_Majority_Label": [cluster_majority[p] for p in predicted_labels],
        "Correct": correct_flags
    })
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  💾 Details saved to: {output_csv}")

# ═══════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════

def main():
    # ── Detect --fresh from command line arguments ──
    skip_cache = '--fresh' in sys.argv
    if skip_cache:
        sys.argv.remove('--fresh')  # Avoid conflict with other arguments

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   Clustering Accuracy Evaluation — Kiro AI Project (v2.1)    ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    images_root = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else IMAGES_ROOT

    # ── Load Cache or Process ──
    vectors, true_labels, file_names = load_cache(skip_cache)

    if vectors is None:
        image_paths, true_labels, file_names = load_image_paths(CSV_PATH, images_root)
        vectors, valid_paths = extract_clip_embeddings(image_paths, CLIP_MODEL)

        if len(vectors) == 0:
            print("❌ Failed to extract embeddings")
            sys.exit(1)

        path_to_label = dict(zip(image_paths, true_labels))
        path_to_name = dict(zip(image_paths, file_names))
        true_labels = [path_to_label[p] for p in valid_paths]
        file_names = [path_to_name[p] for p in valid_paths]
        save_cache(vectors, true_labels, file_names)

    # Number of real categories
    num_true_categories = len(set(true_labels))
    print(f"  📊 Number of real categories: {num_true_categories}")

    # ── Select MODE ──
    if EVALUATION_MODE == 'full_data':
        print("\n═══ MODE: FULL DATA (Direct Evaluation) ═══")
        vectors_all = vectors
        labels_all = true_labels
        names_all = file_names

        # [3/4] PCA
        n_pca = min(128, len(vectors_all), vectors_all.shape[1])
        print(f"\n[3/4] Dimensionality Reduction (PCA): {vectors_all.shape[1]} → {n_pca}")
        pca = PCA(n_components=n_pca, random_state=42)
        vectors_all = pca.fit_transform(vectors_all)
        print(f"  ✓ Shape after PCA: {vectors_all.shape}")

        # [4/4] Threshold selection and clustering
        print(f"\n[4/4] Threshold selection and clustering:")
        if DISTANCE_THRESHOLD is None:
            final_thr = get_best_threshold(vectors_all, labels_all)
        else:
            final_thr = DISTANCE_THRESHOLD

        predicted_labels, n_clusters = cluster_vectors(vectors_all, final_thr)
        results = evaluate_clustering(labels_all, predicted_labels, names_all)

        accuracy = results["purity"] * 100
        print("\n" + "─"*50)
        print("  📈 Final Result (Full Data):")
        print(f"  Number of images: {len(labels_all)}")
        print(f"  Number of clusters: {n_clusters}")
        print(f"  Threshold: {final_thr:.4f}")
        print(f"  ╔════════════════════════════════╗")
        print(f"  ║   Clustering Accuracy (Purity): {accuracy:.2f}%   ║")
        print(f"  ╚════════════════════════════════╝")

    else:   # train_test
        print("\n═══ MODE: TRAIN/TEST SPLIT (Training and Testing) ═══")
        indices = np.arange(len(vectors))
        train_idx, test_idx = train_test_split(
            indices, test_size=0.2, random_state=42, stratify=true_labels
        )
        vectors_train = vectors[train_idx]
        vectors_test = vectors[test_idx]
        labels_train = [true_labels[i] for i in train_idx]
        labels_test = [true_labels[i] for i in test_idx]
        names_test = [file_names[i] for i in test_idx]

        # PCA
        n_pca = min(128, len(vectors_train), vectors_train.shape[1])
        print(f"\n[3/4] PCA on Training: {vectors_train.shape[1]} → {n_pca}")
        pca = PCA(n_components=n_pca, random_state=42)
        vectors_train = pca.fit_transform(vectors_train)
        vectors_test = pca.transform(vectors_test)

        # Threshold
        if DISTANCE_THRESHOLD is None:
            final_thr = get_best_threshold(vectors_train, labels_train)
        else:
            final_thr = DISTANCE_THRESHOLD

        # [4/4] Clustering on test data
        print(f"\n[4/4] Clustering test data:")
        predicted_test, n_clusters = cluster_vectors(vectors_test, final_thr)
        results = evaluate_clustering(labels_test, predicted_test, names_test)

        accuracy = results["purity"] * 100
        print("\n" + "─"*50)
        print("  📈 Final Result (Test Set):")
        print(f"  Number of images: {len(labels_test)}")
        print(f"  Number of clusters: {n_clusters}")
        print(f"  Threshold: {final_thr:.4f}")
        print(f"  ╔════════════════════════════════╗")
        print(f"  ║   Clustering Accuracy (Purity): {accuracy:.2f}%   ║")
        print(f"  ╚════════════════════════════════╝")

    gc.collect()
    print("\n✅ Processing completed successfully!")

if __name__ == "__main__":
    main()