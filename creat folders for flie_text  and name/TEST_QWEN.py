import os
import re
import torch
import PyPDF2
import docx
from transformers import AutoModelForCausalLM, AutoTokenizer

# ─────────────── 1. تحميل النموذج ───────────────

CACHE_DIR = os.path.join(os.getcwd(), "models")
MODEL_ID  = "Qwen/Qwen2.5-0.5B-Instruct"

print("⏳ جاري تحميل النموذج...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    cache_dir=CACHE_DIR,
    local_files_only=True,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID,
    cache_dir=CACHE_DIR,
    local_files_only=False
)

print("✅ النموذج جاهز!\n")

# ─────────────── 2. استخراج النصوص ───────────────

def get_text_from_pdf(path):
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            texts = []
            for page in reader.pages[:4]:
                t = page.extract_text()
                if t:
                    texts.append(t)
            return " ".join(texts)
    except:
        return ""

def get_text_from_word(path):
    try:
        doc = docx.Document(path)
        return " ".join(p.text for p in doc.paragraphs[:20] if p.text.strip())
    except:
        return ""

def get_text_from_txt(path):
    for enc in ["utf-8", "utf-8-sig", "windows-1256", "cp1256"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(1000)
        except:
            continue
    return ""

# ─────────────── 3. تنقية النص (الأهم) ───────────────

def clean_text(text: str) -> str:
    """
    يزيل الضجيج من النص قبل إرساله للنموذج.
    النموذج الصغير يتشتت بسهولة من الرموز والأرقام العشوائية.
    """
    text = re.sub(r'https?://\S+', '', text)           # URLs
    text = re.sub(r'\S+@\S+', '', text)                # emails
    text = re.sub(r'\b\d{4,}\b', '', text)             # أرقام طويلة
    text = re.sub(r'[^\w\s\u0600-\u06FF.,،؟?!]', ' ', text)  # رموز غير نصية
    text = re.sub(r'\s+', ' ', text)                   # مسافات متعددة
    return text.strip()


def extract_keywords(text: str, max_words: int = 40) -> str:
    """
    يستخرج الكلمات الجوهرية فقط ويتجاهل كلمات الربط والحشو.
    النموذج الصغير يحتاج نصاً مركّزاً وقصيراً لينتج نتيجة جيدة.
    """
    stopwords = {
        # عربي
        "في", "من", "إلى", "على", "أن", "هذا", "هذه", "التي", "الذي",
        "وفي", "كان", "كانت", "يتم", "تتم", "أو", "مع", "عند", "بعد",
        "قبل", "لا", "ما", "هو", "هي", "لقد", "قد", "وقد", "ثم", "حتى",
        "عن", "بين", "لكن", "ذلك", "تلك", "له", "لها", "لهم", "نحو",
        # إنجليزي
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "to", "of", "and", "or", "in", "on", "at", "for", "with",
        "this", "that", "it", "its", "by", "from", "as", "but", "not",
        "have", "has", "had", "will", "would", "can", "could", "should",
        "which", "who", "what", "when", "where", "how", "if", "then"
    }

    words = text.split()
    keywords = [w for w in words if len(w) > 2 and w.lower() not in stopwords]
    return " ".join(keywords[:max_words])


# ─────────────── 4. توليد الاسم (التحديث الجديد) ───────────────

def suggest_folder_name(keywords: str, file_names: list) -> str:
    """
    استخدام نظام المحادثة (Chat Template) لأن نماذج Instruct تتطلب هذا الهيكل لتعمل بشكل صحيح
    وليس نصوصاً خاماً.
    """
    files_str = ", ".join(file_names[:10]) if file_names else "غير معروف"
    
    # تحديد الهوية الشاملة للنموذج ليكون حاسماً في إجابته
    system_prompt = (
        "أنت مساعد ذكي متخصص في تصنيف الملفات. "
        "مهمتك الوحيدة هي قراءة الملفات وبناء على محتوى الملفات والكلمات المفتاحية المأخوذة منها، "
        "ثم اقتراح اسم مجلد قصير جداً (من 1 إلى 3 كلمات كحد أقصى) باللغة العربية. "
        "مهم جداً: أطبع الاسم النهائي فقط ولا تقم بإضافة أي شرح أو علامات ترقيم."
    )
    
    # النص الذي سيحصل عليه
    user_prompt = f"أسماء الملفات: {files_str}\nالكلمات المفتاحية: {keywords}\n\nما هو الاسم المقترح للمجلد؟"

    # تجهيز قالب المحادثة
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # تطبيق قالب المحادثة الخاص بالنموذج
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt", add_special_tokens=False).to(model.device)
    input_len = inputs.input_ids.shape[1]

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=10,         # لا نحتاج أكثر من 10 توكنز لاسم قصير
            temperature=0.2,           # تقليل الإبداع والعشوائية (إجابة دقيقة وثابتة)
            do_sample=True,            # تفعيل أخذ العينات بحرارة منخفضة جداً
            pad_token_id=tokenizer.eos_token_id,
        )

    # استخراج الإجابة الجديدة فقط المولدة من النموذج
    new_tokens = generated_ids[0][input_len:]
    output = tokenizer.decode(new_tokens, skip_special_tokens=True)

    # تنظيف الناتج
    name = output.split("\n")[0].strip()
    name = name.strip('"\'«»()[]{}.:;,،').strip()

    # fallback في حالة حدوث مشكلة
    if not name or len(name) < 2:
        name = " ".join(keywords.split()[:2]) or "مجلد جديد"

    return name


# ─────────────── 6. فحص المجلد ───────────────

def analyze_folder(folder_path: str) -> str:
    all_text   = []
    file_names = []

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            ext       = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)
            file_names.append(file)

            raw = ""
            if ext == ".pdf":
                raw = get_text_from_pdf(full_path)
            elif ext in {".docx", ".doc"}:
                raw = get_text_from_word(full_path)
            elif ext == ".txt":
                raw = get_text_from_txt(full_path)

            if raw:
                all_text.append(clean_text(raw))

        if len(all_text) >= 10:
            break

    combined = " ".join(all_text)
    keywords = extract_keywords(combined, max_words=40)

    # fallback: إذا لم يجد نصوصاً، يستخدم أسماء الملفات
    if not keywords:
        fallback = clean_text(" ".join(file_names))
        keywords = extract_keywords(fallback, max_words=20)

    if not keywords:
        return "مجلد جديد"

    print(f"🔑 الكلمات المستخرجة: {keywords[:80]}...")
    return suggest_folder_name(keywords, file_names)


# ─────────────── 7. الواجهة ───────────────

if __name__ == "__main__":
    print("=" * 55)
    print("   🗂️  محلل المجلدات الذكي")
    print("=" * 55)

    while True:
        target = input("\n📂 أدخل مسار المجلد (أو exit للخروج): ").strip()

        if target.lower() == "exit":
            print("👋 إلى اللقاء!")
            break

        target = target.strip('"').strip("'")

        if not os.path.isdir(target):
            print("❌ المسار غير صحيح.")
            continue

        print("🔍 جاري التحليل...")
        name = analyze_folder(target)
        print(f"\n✨ الاسم المقترح: {name}")
        print("-" * 55)