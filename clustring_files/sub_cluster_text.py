"""
Sub-Clustering for Text Files - Kiro AI
التجميع الفرعي للملفات النصية: فحص كل مجلد بعد إنشائه وتقسيمه إلى مجلدات فرعية
إذا كان يحتوي على مجموعات مواضيع مختلفة
"""
import os
import sys
import shutil
import json
import re
import numpy as np

# Force UTF-8 encoding safely
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif sys.stdout.encoding != 'UTF-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except:
        pass

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
    import PyPDF2  # type: ignore
except ImportError:
    pass

try:
    import docx
except ImportError:
    pass

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
#              إعداد المسارات
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "sbert_high_res")

# امتدادات الملفات النصية المدعومة
TEXT_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx", ".md", ".py", ".java",
                   ".cpp", ".c", ".h", ".js", ".html", ".css", ".csv", ".rtf"}

# الحد الأدنى لعدد الملفات في مجلد حتى يُفحص للتقسيم الفرعي
MIN_FILES_FOR_SUB = 6
# عتبة Silhouette Score
SILHOUETTE_THRESHOLD = 0.15

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
#          تحميل النموذج
# ==========================================
import transformers
transformers.logging.set_verbosity_error()

print("⏳ [Sub-Cluster Text] Loading SBERT model...")
sbert_model = SentenceTransformer(MODEL_PATH)
print("  [Sub-Cluster Text] Model loaded successfully!\n")


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
#    استخراج المرشحين (نفس طريقة المجلد الأب)
# ==========================================
def extract_candidates(texts):
    """
    استخراج Unigram و Bigram مع فلترة الكلمات القصيرة جداً.
    نفس الدالة المستخدمة في semantic_folder_creator.py
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

        # حذف الكلمات القصيرة جداً (أقل من 3 أحرف)
        filtered = [c for c in candidates if len(c) >= 3]
        return filtered if filtered else list(candidates)

    except ValueError:
        return []


# ==========================================
#  الخوارزمية الدلالية (نفس طريقة المجلد الأب)
# ==========================================
def get_semantic_label(texts):
    """
    بناء اسم المجلد بثلاث طبقات:
    نفس الدالة المستخدمة في semantic_folder_creator.py

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

    # --- فصل Bigram عن Unigram ---
    bigrams  = [(candidates[i], similarities[i]) for i in range(len(candidates)) if " " in candidates[i]]
    unigrams = [(candidates[i], similarities[i]) for i in range(len(candidates)) if " " not in candidates[i]]

    # إذا يوجد bigram بجودة كافية، استخدمه مباشرةً
    if bigrams:
        best_bigram = max(bigrams, key=lambda x: x[1])
        if best_bigram[1] > 0.3:
            clean_name = best_bigram[0].replace(" ", "_")
            print(f"     Folder name (bigram): {clean_name}")
            return clean_name

    # ادمج أفضل 3 Unigrams
    unigrams_sorted = sorted(unigrams, key=lambda x: x[1], reverse=True)
    top_n = min(3, len(unigrams_sorted))
    top_words = [w for w, _ in unigrams_sorted[:top_n]]
    label = "_".join(top_words)

    print(f"     Folder name (unigrams): {label}")
    return label


# ==========================================
#       دوال التجميع الفرعي
# ==========================================

def get_text_files_in_folder(folder_path: str) -> list:
    """جمع كل مسارات الملفات النصية في مجلد معين (مستوى واحد فقط)"""
    files = []
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file():
                _, ext = os.path.splitext(entry.name)
                if ext.lower() in TEXT_EXTENSIONS:
                    files.append(entry.path)
    except PermissionError:
        pass
    return files


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


# ==========================================
#       المعالجة الرئيسية: فحص وتقسيم
# ==========================================

def process_sub_clustering():
    """
    فحص كل مجلد نصي أنشأه النظام في المرحلة الأولى
    وتقسيمه إلى مجلدات فرعية إذا احتوى على مجموعات مواضيع مختلفة
    """
    json_path = os.path.join(BASE_DIR, "created_folders.json")

    if not os.path.exists(json_path):
        print("[Sub-Cluster Text] No created_folders.json found. Nothing to sub-cluster.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    folders = data.get("created_folders", [])
    text_folders = [f for f in folders if f.get("type") == "text"]

    if not text_folders:
        print("[Sub-Cluster Text] No text folders found to analyze.")
        return

    print(f"\n{'='*60}")
    print(f"[Sub-Cluster Text] Analyzing {len(text_folders)} text folders for sub-groups...")
    print(f"{'='*60}")

    new_sub_folders = []

    for folder_info in text_folders:
        folder_path = folder_info.get("folder_path", "")
        if not os.path.isdir(folder_path):
            print(f"\n  [!] Folder not found: {folder_path}")
            continue

        text_files = get_text_files_in_folder(folder_path)
        print(f"\n  📁 {os.path.basename(folder_path)} ({len(text_files)} files)")

        if len(text_files) < MIN_FILES_FOR_SUB:
            print(f"     ⏭ Too few files (need ≥ {MIN_FILES_FOR_SUB}), skipping.")
            continue

        # الخطوة 1: قراءة محتوى الملفات
        print(f"     Reading file contents...")
        content_map = {}
        for file_path in text_files:
            txt = read_file_content(file_path)
            if txt.strip():
                content_map[file_path] = txt

        if len(content_map) < MIN_FILES_FOR_SUB:
            print(f"     ⏭ Not enough readable files ({len(content_map)}), skipping.")
            continue

        # الخطوة 2: حساب Embeddings
        paths_list = list(content_map.keys())
        texts_list = list(content_map.values())

        print(f"     Computing SBERT embeddings for {len(texts_list)} files...")
        embeddings = sbert_model.encode(texts_list)

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
                groups[label] = {"paths": [], "texts": []}
            groups[label]["paths"].append(paths_list[idx])
            groups[label]["texts"].append(texts_list[idx])

        # الخطوة 5: إنشاء المجلدات الفرعية ونقل الملفات
        for group_label, group_data in groups.items():
            sub_paths = group_data["paths"]
            sub_texts = group_data["texts"]

            if len(sub_paths) < 2:
                print(f"     ⏭ Group {group_label} has only {len(sub_paths)} file(s), skipping.")
                continue

            # تسمية المجلد الفرعي (نفس طريقة المجلد الأب بالضبط)
            sub_name = get_semantic_label(sub_texts)
            sub_folder = os.path.join(folder_path, sub_name)

            # تفادي تكرار الأسماء
            counter = 1
            original = sub_folder
            while os.path.exists(sub_folder):
                sub_folder = f"{original}_{counter}"
                counter += 1

            os.makedirs(sub_folder, exist_ok=True)
            print(f"     📂 Created: {os.path.basename(sub_folder)} ({len(sub_paths)} files)")

            # نقل الملفات
            moved = 0
            for file_path in sub_paths:
                if not os.path.exists(file_path):
                    continue
                fname = os.path.basename(file_path)
                dest = os.path.join(sub_folder, fname)
                if os.path.exists(dest):
                    b, e = os.path.splitext(fname)
                    fc = 1
                    while os.path.exists(dest):
                        dest = os.path.join(sub_folder, f"{b}_sub{fc}{e}")
                        fc += 1
                try:
                    shutil.move(file_path, dest)
                    moved += 1
                except Exception as e:
                    print(f"       [!] Failed to move {fname}: {e}")

            # تسجيل المجلد الفرعي
            new_sub_folders.append({
                "group_name": sub_name,
                "folder_path": sub_folder,
                "files_count": moved,
                "type": "text_sub",
                "parent_folder": folder_path,
                "timestamp": __import__('time').time()
            })

    # تحديث JSON بالمجلدات الفرعية الجديدة
    if new_sub_folders:
        data["created_folders"].extend(new_sub_folders)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  [+] Added {len(new_sub_folders)} text sub-folders to created_folders.json")

    print(f"\n{'='*60}")
    print(f"[Sub-Cluster Text] Text sub-clustering completed!")
    print(f"{'='*60}")


if __name__ == '__main__':
    process_sub_clustering()
