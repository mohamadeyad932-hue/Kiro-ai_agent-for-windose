"""
Sub-Clustering for Images - Kiro AI
التجميع الفرعي: فحص كل مجلد بعد إنشائه وتقسيمه إلى مجلدات فرعية إذا كان يحتوي على مجموعات مختلفة
"""
import os
import sys
import shutil
import json
import numpy as np

# Force UTF-8 encoding safely
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
except ImportError:
    print("pip install scikit-learn numpy")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("pip install sentence-transformers")
    sys.exit(1)

try:
    from PIL import Image
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch
except ImportError:
    print("pip install transformers torch torchvision Pillow")
    sys.exit(1)

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
#              إعداد المسارات
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SBERT_MODEL_PATH = os.path.join(BASE_DIR, "models", "sbert_high_res")
BLIP_MODEL_PATH = os.path.join(BASE_DIR, "models", "blip-image-captioning-base")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".jfif"}

# الحد الأدنى لعدد الصور في مجلد حتى يُفحص للتقسيم الفرعي
MIN_IMAGES_FOR_SUB = 6
# عتبة Silhouette Score - إذا كانت أعلى يعني المجلد يحتاج تقسيم
SILHOUETTE_THRESHOLD = 0.15

# ==========================================
#          تحميل النماذج
# ==========================================
print("⏳ [Sub-Cluster] Loading AI models...")

device = "cuda" if torch.cuda.is_available() else "cpu"

try:
    blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL_PATH)
    blip_model = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL_PATH).to(device)
except Exception as e:
    print(f"  [!] Failed to load BLIP model: {e}")
    sys.exit(1)

sbert_model = SentenceTransformer(SBERT_MODEL_PATH)
print("  [Sub-Cluster] Models loaded successfully!\n")


# ==========================================
#              دوال المساعدة
# ==========================================

def generate_caption(image_path: str) -> str:
    """توليد وصف نصي للصورة عبر BLIP"""
    try:
        raw_image = Image.open(image_path).convert('RGB')
        inputs = blip_processor(raw_image, return_tensors="pt").to(device)
        out = blip_model.generate(**inputs, max_new_tokens=20)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        print(f"    [!] Caption error for {os.path.basename(image_path)}: {e}")
        return ""


def get_images_in_folder(folder_path: str) -> list:
    """جمع كل مسارات الصور في مجلد معين (مستوى واحد فقط)"""
    images = []
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file():
                _, ext = os.path.splitext(entry.name)
                if ext.lower() in IMAGE_EXTENSIONS:
                    images.append(entry.path)
    except PermissionError:
        pass
    return images


def find_best_k(vectors, max_k=6):
    """
    إيجاد أفضل عدد مجموعات فرعية باستخدام Silhouette Score
    يجرب k من 2 إلى max_k ويختار الأفضل
    """
    n_samples = len(vectors)
    max_k = min(max_k, n_samples - 1)

    if max_k < 2:
        return None, -1

    best_k = None
    best_sil = -1

    for k in range(2, max_k + 1):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(vectors)

            # تأكد أن كل المجموعات فيها عناصر
            unique_labels = set(labels)
            if len(unique_labels) < 2:
                continue

            sil = silhouette_score(vectors, labels, metric='cosine')

            print(f"      k={k}: Silhouette = {sil:.3f}")

            if sil > best_sil:
                best_sil = sil
                best_k = k
        except Exception:
            continue

    return best_k, best_sil


def extract_candidates_tfidf(texts):
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=list(ENGLISH_STOP_WORDS),
            max_features=50,
            min_df=1
        )
        vectorizer.fit(texts)
        candidates = vectorizer.get_feature_names_out()
        filtered = [c for c in candidates if len(c) >= 3]
        return filtered if filtered else list(candidates)
    except ValueError:
        return []

def get_semantic_image_label(captions):
    candidates = extract_candidates_tfidf(captions)
    
    if len(candidates) == 0:
        return "Image_Group"

    caption_embeddings = sbert_model.encode(captions)
    centroid = np.mean(caption_embeddings, axis=0).reshape(1, -1)
    
    candidate_embeddings = sbert_model.encode(candidates)
    similarities = cosine_similarity(candidate_embeddings, centroid).flatten()
    
    bigrams  = [(candidates[i], similarities[i]) for i in range(len(candidates)) if " " in candidates[i]]
    unigrams = [(candidates[i], similarities[i]) for i in range(len(candidates)) if " " not in candidates[i]]

    if bigrams:
        best_bigram = max(bigrams, key=lambda x: x[1])
        if best_bigram[1] > 0.3:
            return best_bigram[0].title().replace(" ", "_")
            
    unigrams_sorted = sorted(unigrams, key=lambda x: x[1], reverse=True)
    top_n = min(2, len(unigrams_sorted))
    top_words = [w.title() for w, _ in unigrams_sorted[:top_n]]
    
    label = "_".join(top_words)
    return label if label else "Image_Group"


# ==========================================
#       المعالجة الرئيسية: فحص وتقسيم
# ==========================================

def process_sub_clustering():
    """
    فحص كل مجلد أنشأه النظام في المرحلة الأولى
    وتقسيمه إلى مجلدات فرعية إذا احتوى على مجموعات مختلفة
    """
    json_path = os.path.join(BASE_DIR, "created_folders.json")

    if not os.path.exists(json_path):
        print("[Sub-Cluster] No created_folders.json found. Nothing to sub-cluster.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    folders = data.get("created_folders", [])
    image_folders = [f for f in folders if f.get("type") == "image"]

    if not image_folders:
        print("[Sub-Cluster] No image folders found to analyze.")
        return

    print(f"\n{'='*60}")
    print(f"[Sub-Cluster] Analyzing {len(image_folders)} image folders for sub-groups...")
    print(f"{'='*60}")

    new_sub_folders = []

    for folder_info in image_folders:
        folder_path = folder_info.get("folder_path", "")
        if not os.path.isdir(folder_path):
            print(f"\n  [!] Folder not found: {folder_path}")
            continue

        images = get_images_in_folder(folder_path)
        print(f"\n  📁 {os.path.basename(folder_path)} ({len(images)} images)")

        if len(images) < MIN_IMAGES_FOR_SUB:
            print(f"     ⏭ Too few images (need ≥ {MIN_IMAGES_FOR_SUB}), skipping.")
            continue

        # الخطوة 1: توليد الأوصاف
        print(f"     Generating captions...")
        captions_map = {}
        cap_limit = min(len(images), 70)
        for img_path in images[:cap_limit]:
            cap = generate_caption(img_path)
            if cap.strip():
                captions_map[img_path] = cap

        if len(captions_map) < MIN_IMAGES_FOR_SUB:
            print(f"     ⏭ Not enough captions generated, skipping.")
            continue

        # الخطوة 2: حساب Embeddings
        paths_list = list(captions_map.keys())
        captions_list = list(captions_map.values())

        print(f"     Computing SBERT embeddings...")
        embeddings = sbert_model.encode(captions_list)

        # PCA لتنظيف الضوضاء
        n_pca = min(64, len(paths_list), embeddings.shape[1])
        if n_pca >= 2:
            pca = PCA(n_components=n_pca, random_state=42)
            embeddings = pca.fit_transform(embeddings)

        # الخطوة 3: فحص هل يحتاج تقسيم
        print(f"     Finding optimal k...")
        best_k, best_sil = find_best_k(embeddings)

        if best_k is None or best_sil < SILHOUETTE_THRESHOLD:
            print(f"     ✅ Folder is homogeneous (Sil={best_sil:.3f}). No sub-clustering needed.")
            continue

        print(f"     🔀 Sub-clustering into {best_k} groups (Sil={best_sil:.3f})")

        # الخطوة 4: التقسيم
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        # تجميع الملفات حسب المجموعة
        groups = {}
        for idx, label in enumerate(labels):
            if label not in groups:
                groups[label] = {"paths": [], "captions": []}
            groups[label]["paths"].append(paths_list[idx])
            groups[label]["captions"].append(captions_list[idx])

        # الخطوة 5: إنشاء المجلدات الفرعية ونقل الملفات
        all_captions = captions_list  # كل الأوصاف للمجلد الأم (لحذف الكلمات المشتركة)

        for group_label, group_data in groups.items():
            sub_paths = group_data["paths"]
            sub_captions = group_data["captions"]

            if len(sub_paths) < 2:
                print(f"     ⏭ Group {group_label} has only {len(sub_paths)} image(s), skipping.")
                continue

            # تسمية المجلد الفرعي
            sub_name = get_semantic_image_label(sub_captions)
            sub_folder = os.path.join(folder_path, sub_name)

            # تفادي تكرار الأسماء
            counter = 1
            original = sub_folder
            while os.path.exists(sub_folder):
                sub_folder = f"{original}_{counter}"
                counter += 1

            os.makedirs(sub_folder, exist_ok=True)
            print(f"     📂 Created: {os.path.basename(sub_folder)} ({len(sub_paths)} images)")

            # نقل الصور
            moved = 0
            for img_path in sub_paths:
                if not os.path.exists(img_path):
                    continue
                fname = os.path.basename(img_path)
                dest = os.path.join(sub_folder, fname)
                if os.path.exists(dest):
                    b, e = os.path.splitext(fname)
                    fc = 1
                    while os.path.exists(dest):
                        dest = os.path.join(sub_folder, f"{b}_sub{fc}{e}")
                        fc += 1
                try:
                    shutil.move(img_path, dest)
                    moved += 1
                except Exception as e:
                    print(f"       [!] Failed to move {fname}: {e}")

            # تسجيل المجلد الفرعي
            new_sub_folders.append({
                "group_name": sub_name,
                "folder_path": sub_folder,
                "files_count": moved,
                "type": "image_sub",
                "parent_folder": folder_path,
                "timestamp": __import__('time').time()
            })

        # حذف الصور المتبقية التي لم تُصنف (من المجلد الأصلي ليست في مجلدات فرعية)
        # (لا نحذفها - نتركها في المجلد الأم)

    # تحديث JSON بالمجلدات الفرعية الجديدة
    if new_sub_folders:
        data["created_folders"].extend(new_sub_folders)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  [+] Added {len(new_sub_folders)} sub-folders to created_folders.json")

    print(f"\n{'='*60}")
    print(f"[Sub-Cluster] Sub-clustering completed!")
    print(f"{'='*60}")


if __name__ == '__main__':
    process_sub_clustering()
