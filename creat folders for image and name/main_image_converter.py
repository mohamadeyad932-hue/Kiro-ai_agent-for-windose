import os
import shutil
import sys
import importlib.util

# Force UTF-8 encoding safely
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif sys.stdout.encoding != 'UTF-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except:
        pass

import numpy as np
import torch
from PIL import Image

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
except ImportError:
    print("pip install transformers torch torchvision")
    import sys
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("pip install sentence-transformers")
    import sys
    sys.exit(1)

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
#              إعداد المسارات
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_CLUSTERING_DIR = os.path.join(BASE_DIR, "clustring_imge")
SBERT_MODEL_PATH = os.path.join(BASE_DIR, "models", "sbert_high_res")
BLIP_MODEL_PATH = os.path.join(BASE_DIR, "models", "blip-image-captioning-base")

# ==========================================
#          تحميل النماذج (Models)
# ==========================================
print(" Loading AI models... (This may take a while)")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"   [BLIP] Using device: {device}")
try:
    blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL_PATH)
    blip_model = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL_PATH).to(device)
except Exception as e:
    print(f" Failed to load BLIP model: {e}")
    import sys
    sys.exit(1)

print("   [SBERT] Loading...")
sbert_model = SentenceTransformer(SBERT_MODEL_PATH)

print(" All models loaded successfully!\n")

# ==========================================
#              دوال المعالجة
# ==========================================

def generate_image_caption(image_path: str) -> str:
    try:
        raw_image = Image.open(image_path).convert('RGB')
        inputs = blip_processor(raw_image, return_tensors="pt").to(device)
        out = blip_model.generate(**inputs, max_new_tokens=20)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        print(f"  [!] Error generating caption for {os.path.basename(image_path)}: {e}")
        return ""

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
#       دالة استخراج المسارات من المتغير
# ==========================================

HOME = os.path.expanduser("~")
FOLDERS_MAP = {
    "desktop": os.path.join(HOME, "Desktop"),
    "documents": os.path.join(HOME, "Documents"),
    "downloads": os.path.join(HOME, "Downloads"),
}

def extract_paths_from_variable(group, filename: str) -> list:
    """
     استخراج المسارات كاملة:
    - إذا كان قاموساً {name: ext} يقوم بدمجها مع المسار الأب (الذي يُستنتج من اسم ملف القاموس).
    - إذا كان قائمة/مجموعة يعيدها كما هي.
    """
    paths = []

    if isinstance(group, dict):
        base_folder_key = "desktop"
        if "documents" in filename.lower(): base_folder_key = "documents"
        elif "downloads" in filename.lower(): base_folder_key = "downloads"
        
        base_folder_path = FOLDERS_MAP.get(base_folder_key, "")
        
        for name, ext in group.items():
            if isinstance(name, str) and isinstance(ext, str):
                full_path = os.path.join(base_folder_path, name + ext)
                paths.append(full_path)

    elif isinstance(group, (list, set, tuple)):
        paths = [f for f in group if isinstance(f, str)]

    return paths

# ==========================================
#          المعالجة الرئيسية (Main)
# ==========================================

def save_metadata(group_name, folder_path, files_count):
    """حفظ معلومات المجلد المنشأ في ملف JSON للواجهة"""
    import json
    json_path = os.path.join(BASE_DIR, "created_folders.json")
    data = {"created_folders": []}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
            
    data["created_folders"].append({
        "group_name": group_name,
        "folder_path": folder_path,
        "files_count": files_count,
        "type": "image",
        "timestamp": time.time() if 'time' in globals() else 0
    })
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_image_clusters():
    if not os.path.exists(IMAGE_CLUSTERING_DIR):
        print(f" Dictionaries path not found: {IMAGE_CLUSTERING_DIR}")
        return

    print("Searching in image dictionaries...")
    
    for filename in os.listdir(IMAGE_CLUSTERING_DIR):
        if not filename.endswith(".py"):
            continue
            
        file_path = os.path.join(IMAGE_CLUSTERING_DIR, filename)
        print(f"\n{'='*50}\nProcessing image dictionary: {filename}\n{'='*50}")
        
        spec = importlib.util.spec_from_file_location("module.name", file_path)
        foo = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(foo)
        except Exception as e:
            print(f" Failed to load dictionary {filename}: {e}")
            continue
        
        processed_any = False  #  تتبع هل تمت معالجة أي مجموعة

        for var_name in dir(foo):
            if var_name.startswith("__"):
                continue
                
            # تجاهل الإعدادات العامة الموجودة في بعض القواميس لتفادي الأخطاء
            if var_name in ["EXTENSIONS", "FOLDERS", "HOME", "CURRENT_DIR"]:
                continue
                
            group = getattr(foo, var_name)
            
            #  الإصلاح: استخدام الدالة وتمرير اسم الملف لمعرفة مساره الأساسي
            paths = extract_paths_from_variable(group, filename)
            
            if not paths:
                continue

            valid_files = [f for f in paths if os.path.isfile(f)]
            
            if not valid_files:
                print(f"     Group '{var_name}': No valid files found (paths might be incorrect)")
                #  طباعة تشخيصية لمساعدتك في الكشف
                for p in paths[:3]:
                    print(f"      - Path not found: {p}")
                continue
                
            print(f"\n🔹 Group: {var_name} ({len(valid_files)} images)")
            
            parent_path = os.path.dirname(valid_files[0])
            
            # الخطوة 1: توليد الأوصاف
            captions = []
            print("   Reading images and generating captions...")
            
            files_to_caption = valid_files
            if len(valid_files) > 75:
                print(f"   [!] Large group ({len(valid_files)} images). Captioning only first 70 for naming.")
                files_to_caption = valid_files[:70]
                
            for f in files_to_caption:
                cap = generate_image_caption(f)
                if cap.strip():
                    captions.append(cap)
                    print(f"      ✔ {os.path.basename(f)}: {cap}")
            
            # الخطوة 2: التسمية الدلالية
            if not captions:
                label = f"Unknown_Images_{var_name}"
                print(f" No captions generated, using default name: {label}")
            else:
                label = get_semantic_image_label(captions)
                print(f" Chosen semantic name: {label}")
                
            target_folder = os.path.join(parent_path, label)
            
            # الخطوة 3: معالجة تكرار الأسماء
            counter = 1
            original_target = target_folder
            while os.path.exists(target_folder):
                target_folder = f"{original_target}_{counter}"
                counter += 1
                
            print(f" Creating folder: {target_folder}")
            os.makedirs(target_folder, exist_ok=True)
            
            # الخطوة 4: نقل الصور
            success = 0
            for f in valid_files:
                fname = os.path.basename(f)
                dest_path = os.path.join(target_folder, fname)
                try:
                    if os.path.exists(dest_path):
                        b, e = os.path.splitext(fname)
                        file_counter = 1
                        while os.path.exists(dest_path):
                            dest_path = os.path.join(target_folder, f"{b}_copy_{file_counter}{e}")
                            file_counter += 1
                            
                    shutil.move(f, dest_path)
                    success += 1
                except Exception as e:
                    print(f" Failed to move {fname}: {e}")
                    
            print(f" Successfully moved {success}/{len(valid_files)} images.")
            # حفظ المعلومات للداشبورد
            save_metadata(label, target_folder, success)
            processed_any = True


if __name__ == '__main__':
    import time
    process_image_clusters()
    print("\n🎉 Finished classifying and moving all images!")