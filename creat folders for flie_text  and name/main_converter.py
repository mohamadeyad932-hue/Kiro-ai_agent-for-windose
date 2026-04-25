import os
import re
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT

# ── تحميل النموذج المحلي ──
MODEL_PATH = r"C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\models\sbert_high_res"
sentence_model = SentenceTransformer(MODEL_PATH)
kw_model = KeyBERT(model=sentence_model)

# ── امتدادات الصور (نتجاهلها) ──
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.heic'}

def clean_text(text: str) -> str:
    """تنظيف النص من الروابط والأرقام والرموز المزعجة"""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    return " ".join(text.split())

def detect_language(text: str) -> str:
    """اكتشاف لغة النص بناءً على عدد الحروف"""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return "ar" if arabic_chars > english_chars else "en"

def read_file_content(file_path: str) -> str:
    """
    قراءة الملف بالكامل إذا كان صغيراً، أو حتى 15 صفحة كحد أقصى
    """
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    # حد تقريبي لحجم 15 صفحة نصية (حوالي 35-40 ألف حرف)
    MAX_CHARS = 35000 
    
    try:
        if ext == ".pdf":
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                
                # قراءة كل الصفحات إذا كانت أقل من 15، وإلا قراءة 15 صفحة فقط
                pages_to_read = min(total_pages, 15)
                texts = [page.extract_text() for page in reader.pages[:pages_to_read] if page.extract_text()]
                content = " ".join(texts)
                
        elif ext in {".doc", ".docx"}:
            import docx
            doc = docx.Document(file_path)
            # نقرأ كل الفقرات ونقص النص عند الحد الأقصى (MAX_CHARS)
            all_paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = " ".join(all_paragraphs)[:MAX_CHARS]
            
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # قراءة الملف بحد أقصى يعادل 15 صفحة
                content = f.read(MAX_CHARS)
                
    except Exception as e:
        print(f"  [!] خطأ في قراءة الملف: {e}")
        return ""
        
    return clean_text(content)

def suggest_folder_name(folder_path: str) -> str:
    folder = Path(folder_path)
    
    if not folder.is_dir():
        print(f"[!] المجلد غير موجود: {folder_path}")
        return ""
    
    files = [f for f in folder.iterdir() if f.is_file()]
    print(f"\n📂 المجلد: {folder_path}")
    
    text_files = [f for f in files if f.suffix.lower() not in IMAGE_EXTENSIONS]
    
    if not text_files:
        print("[!] لا توجد ملفات نصية قابلة للقراءة")
        return ""
    
    # جمع المحتوى (نركز على أول 3 ملفات لتجنب انهيار الذاكرة واستهلاك وقت طويل جداً)
    combined = ""
    for fp in text_files[:3]:
        content = read_file_content(str(fp))
        if content.strip():
            combined += content + " "
    
    if not combined.strip():
        print("[!] لم يتم استخراج أي محتوى نصي")
        return ""
        
    # اكتشاف اللغة
    lang = detect_language(combined)
    print(f"🌐 اللغة المكتشفة: {'العربية' if lang == 'ar' else 'الإنجليزية'}")
    
    # ضبط إعدادات KeyBERT
    stop_words_setting = 'english' if lang == 'en' else None
    
    print("⏳ جاري تحليل النص واستخراج أفضل اسم (قد يستغرق بعض الوقت بسبب حجم النص)...")
    
    keywords = kw_model.extract_keywords(
        combined,
        keyphrase_ngram_range=(1, 3), 
        stop_words=stop_words_setting, 
        use_mmr=True,         
        diversity=0.7,        
        top_n=3
    )
    
    if keywords:
        best_candidate = keywords[0][0].strip()
        
        # تنسيق الاسم بناءً على اللغة
        if lang == 'ar':
            clean_name = best_candidate.replace(" ", "_")
            folder_name = f"مجلد_{clean_name}"
        else:
            clean_name = best_candidate.title().replace(" ", "_")
            folder_name = f"Project_{clean_name}"
    else:
        folder_name = "مجلد_غير_معروف" if lang == 'ar' else "Unknown_Folder"
    
    print(f"\n✅ الاسم المقترح: \"{folder_name}\"")
    return folder_name

# ── التشغيل ──
if __name__ == "__main__":
    TEST_FOLDER = r"C:\Users\eyad\Desktop\lec_1"  
    suggest_folder_name(TEST_FOLDER)