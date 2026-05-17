"تسمية المجلدات "
import os
import shutil
import sys
import re

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
import importlib.util
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    import transformers
    transformers.logging.set_verbosity_error()
except ImportError:
    print("pip install sentence-transformers")
    import sys
    sys.exit(1)

try:
    import PyPDF2  # type: ignore
except ImportError:
    pass

try:
    import docx
except ImportError:
    pass

# ==========================================
#              إعداد المسارات
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "sbert_high_res")
import tempfile
CLUSTERING_DIR = os.path.join(tempfile.gettempdir(), "KiroAI_Data", "text_clusters")

print("⏳ Loading SBERT model...")
sbert_model = SentenceTransformer(MODEL_PATH)

# ==========================================
#          Stop Words العربية والإنجليزية
# ==========================================
ARABIC_STOPWORDS = {
    'في', 'من', 'على', 'إلى', 'عن', 'بين', 'مع', 'هذا', 'هذه', 'أن', 'إن', 'بها',
    'الذي', 'التي', 'كان', 'كانت', 'يكون', 'و', 'أو', 'ثم', 'حتى', 'إذا', 'منها',
    'ما', 'لا', 'لم', 'لن', 'هل', 'كيف', 'متى', 'أين', 'كل', 'بعض', 'أي', 'بينها',
    'هو', 'هي', 'هم', 'نحن', 'أنا', 'أنت', 'تم', 'يتم', 'علي', 'وقد', 'كما',
    'لقد', 'إلا', 'ذلك', 'أنه', 'عند', 'فإن', 'ولكن', 'لأن', 'حيث', 'وهو', 'وهي'
}

all_stop_words = list(ARABIC_STOPWORDS.union(ENGLISH_STOP_WORDS))


# ==========================================
#           دوال القراءة والتنظيف
# ==========================================
def clean_text(text: str) -> str:
    """تنظيف النص من الروابط والأرقام والرموز"""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s\u0600-\u06FFa-zA-Z]', ' ', text)
    return " ".join(text.split())


def read_file_content(file_path: str) -> str:
    """قراءة محتوى الملفات (بحد أقصى 15 صفحة)"""
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    MAX_CHARS = 35000

    if not os.path.exists(file_path):
        return ""

    try:
        if ext == ".pdf":
            import PyPDF2 # type: ignore
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages_to_read = min(len(reader.pages), 15)
                texts = [page.extract_text() for page in reader.pages[:pages_to_read] if page.extract_text()]
                content = " ".join(texts)

        elif ext in {".doc", ".docx"}:
            import docx
            doc = docx.Document(file_path)
            all_paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = " ".join(all_paragraphs)[:MAX_CHARS]

        else:
            # يشمل .txt و .py و .md وغيرها
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(MAX_CHARS)

    except Exception as e:
        print(f"  [!] Failed to read {os.path.basename(file_path)}: {e}")
        return ""

    return clean_text(content)


# ==========================================
#    [تحسين 1] استخراج المرشحين مع فلترة
# ==========================================
def extract_candidates(texts):
    """
    استخراج Unigram و Bigram مع فلترة الكلمات القصيرة جداً.
    الجديد: حذف أي مرشح أقل من 3 أحرف لتجنب الضوضاء.
    """
    try:
        vectorizer = CountVectorizer(
            ngram_range=(1, 2),
            stop_words=all_stop_words,
            max_features=50,
            min_df=1
        )
        vectorizer.fit(texts)
        candidates = vectorizer.get_feature_names_out()

        # [تحسين 1 - فلترة] احذف الكلمات القصيرة جداً (أقل من 3 أحرف)
        filtered = [c for c in candidates if len(c) >= 3]
        return filtered if filtered else list(candidates)

    except ValueError:
        return []


# ==========================================
#  [تحسين 2 + 3] الخوارزمية الدلالية المحسّنة
# ==========================================
def get_semantic_label(texts):
    """
    بناء اسم المجلد بثلاث طبقات:

    الطبقة 1 — أفضل 3 كلمات بدلاً من 1 (مع دمجهم في اسم واحد)
    الطبقة 2 — فلترة المرشحين القصار (داخل extract_candidates)
    الطبقة 3 — تفضيل Bigram إذا كانت جودته فوق عتبة 0.3،
               وإلا دمج أفضل Unigrams
    """
    candidates = extract_candidates(texts)

    if len(candidates) == 0:
        return "new folder"

    # --- الخطوات المشتركة ---
    text_embeddings = sbert_model.encode(texts)
    centroid = np.mean(text_embeddings, axis=0).reshape(1, -1)
    candidate_embeddings = sbert_model.encode(candidates)
    similarities = cosine_similarity(candidate_embeddings, centroid).flatten()

    # --- [طبقة 3] فصل Bigram عن Unigram ---
    bigrams  = [(candidates[i], similarities[i]) for i in range(len(candidates)) if " " in candidates[i]]
    unigrams = [(candidates[i], similarities[i]) for i in range(len(candidates)) if " " not in candidates[i]]

    # إذا يوجد bigram بجودة كافية، استخدمه مباشرةً (أوصف واكتفي به)
    if bigrams:
        best_bigram = max(bigrams, key=lambda x: x[1])
        if best_bigram[1] > 0.3:
            clean_name = best_bigram[0].replace(" ", "_")
            print(f" Folder name (bigram): {clean_name}")
            return clean_name

    # --- [طبقة 1] ادمج أفضل 3 Unigrams ---
    unigrams_sorted = sorted(unigrams, key=lambda x: x[1], reverse=True)
    top_n = min(3, len(unigrams_sorted))
    top_words = [w for w, _ in unigrams_sorted[:top_n]]
    label = "_".join(top_words)

    print(f"     Folder name (unigrams): {label}")
    return label


# ==========================================
#        معالجة القواميس وإنشاء المجلدات
# ==========================================
def save_metadata(group_name, folder_path, files_count):
    """حفظ معلومات المجلد المنشأ في ملف JSON للواجهة"""
    import json
    import tempfile
    import time
    json_path = os.path.join(tempfile.gettempdir(), "KiroAI_Data", "created_folders.json")
    data = {"created_folders": []}
    
    if os.path.exists(json_path):
        for _ in range(5):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                break
            except Exception as e:
                print(f" [!] Failed to read report file (maybe locked), retrying... ({e})")
                time.sleep(0.5)
        else:
            print(" [!] Could not read report file after 5 attempts. Starting fresh.")
            
    data["created_folders"].append({
        "group_name": group_name,
        "folder_path": folder_path,
        "files_count": files_count,
        "type": "text",
        "timestamp": time.time()
    })
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_dictionaries(clustering_dir):
    """المرور على ملفات القواميس وتحويل المجموعات لمجلدات فعلية"""
    if not os.path.exists(clustering_dir):
        print(f" Dictionaries path not found: {clustering_dir}")
        return

    print("\n Searching in dictionaries...")
    for filename in os.listdir(clustering_dir):
        if not filename.startswith("similar_") or not filename.endswith("_files.py"):
            continue

        file_path = os.path.join(clustering_dir, filename)
        print(f"\n{'='*50}\n Processing dictionary: {filename}\n{'='*50}")

        spec = importlib.util.spec_from_file_location("module.name", file_path)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)

        for var_name in dir(foo):
            if var_name.startswith("__"):
                continue

            group = getattr(foo, var_name)
            if not isinstance(group, (set, list, tuple)):
                continue

            group = list(group)
            if not group:
                continue

            valid_files = [f for f in group if os.path.exists(f)]
            if not valid_files:
                continue

            print(f"\n🔹 Group: {var_name} ({len(valid_files)} files)")

            parent_path = os.path.dirname(valid_files[0])

            texts = []
            for f in valid_files:
                txt = read_file_content(f)
                if txt.strip():
                    texts.append(txt)

            if not texts:
                label = f"مجلد_غير_مقروء_{var_name}"
            else:
                label = get_semantic_label(texts)

            target_folder = os.path.join(parent_path, label)

            # تفادي تكرار أسماء المجلدات في نفس المسار الأب
            counter = 1
            original_target = target_folder
            while os.path.exists(target_folder):
                target_folder = f"{original_target}_{counter}"
                counter += 1

            print(f" Creating folder: {target_folder}")
            os.makedirs(target_folder, exist_ok=True)

            for f in valid_files:
                fname = os.path.basename(f)
                dest_path = os.path.join(target_folder, fname)
                try:
                    shutil.move(f, dest_path)
                    print(f"  Moved: {fname}")
                except Exception as e:
                    print(f"  Failed to move {fname}: {e}")
            
            # حفظ المعلومات للداشبورد
            save_metadata(label, target_folder, len(valid_files))


if __name__ == '__main__':
    import time
    process_dictionaries(CLUSTERING_DIR)
    print("\n Finished all dictionaries!")