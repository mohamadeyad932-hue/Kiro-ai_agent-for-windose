import os
import torch
import PyPDF2
import docx
from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer

# ─────────────── 1. إعداد مسار الحفظ ───────────────
MODEL_DIR = os.path.join(os.getcwd(), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

print(f"⏳ جاري تجهيز النماذج من: {MODEL_DIR}")

# ─────────────── 2. تحميل نموذج Moondream2 (عيون النظام) ───────────────
# سيتم تحميله في المرة الأولى فقط إذا لم يكن موجوداً
print("🔍 جاري فحص/تحميل Moondream2...")
moondream_id = "vikhyatk/moondream2"
moondream_revision = "2024-08-26" 
moondream_model = AutoModelForCausalLM.from_pretrained(
    moondream_id, trust_remote_code=True, revision=moondream_revision, cache_dir=MODEL_DIR
)
moondream_tokenizer = AutoTokenizer.from_pretrained(
    moondream_id, revision=moondream_revision, cache_dir=MODEL_DIR
)

# ─────────────── 3. تحميل نموذج Qwen (عقل النظام) ───────────────
# بما أنك حملته مسبقاً، سيقوم بقراءته من المجلد فوراً
print("🧠 جاري تحميل Qwen2.5-0.5B من المجلد المحلي...")
qwen_id = "Qwen/Qwen2.5-0.5B-Instruct"
qwen_tokenizer = AutoTokenizer.from_pretrained(qwen_id, cache_dir=MODEL_DIR)
qwen_model = AutoModelForCausalLM.from_pretrained(
    qwen_id, device_map="auto", cache_dir=MODEL_DIR, torch_dtype="auto"
)

print("✅ تم تحميل جميع النماذج بنجاح! النظام جاهز للعمل.\n")

# ─────────────── 4. دوال الاستخراج والتحليل ───────────────

def get_text_from_pdf(path):
    try:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return " ".join([page.extract_text() for page in reader.pages[:1]])
    except: return ""

def get_text_from_word(path):
    try:
        doc = docx.Document(path)
        return " ".join([p.text for p in doc.paragraphs[:10]])
    except: return ""

def get_images_description(image_paths):
    """إرسال الصور لـ Moondream ليصفها بالإنجليزية"""
    descriptions = []
    for path in image_paths:
        try:
            image = Image.open(path).convert("RGB")
            enc_image = moondream_model.encode_image(image)
            # نطلب منه وصفاً مختصراً جداً للصورة
            answer = moondream_model.answer_question(enc_image, "Describe this image in one short sentence.", moondream_tokenizer)
            descriptions.append(answer)
        except Exception as e:
            continue
    return descriptions

def generate_folder_name(image_descriptions, extracted_text):
    """إرسال المعطيات لـ Qwen ليقترح الاسم النهائي بالعربية"""
    
    prompt = "أنت مساعد ذكي لتنظيم الملفات. فحصنا عينة من مجلد ووجدنا التالي:\n"
    if image_descriptions:
        prompt += f"- وصف لبعض الصور في المجلد: {', '.join(image_descriptions)}\n"
    if extracted_text:
        prompt += f"- نصوص من الملفات: {extracted_text[:400]}\n"
        
    prompt += "\nاستنتج الرابط المشترك واقترح اسماً واحداً فقط للمجلد باللغة العربية (من 1 إلى 3 كلمات). اطبع الاسم فقط بدون أي شرح أو علامات."

    messages = [
        {"role": "system", "content": "أنت مساعد دقيق ومختصر جداً."},
        {"role": "user", "content": prompt}
    ]
    
    text = qwen_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = qwen_tokenizer([text], return_tensors="pt").to(qwen_model.device)

    generated_ids = qwen_model.generate(**model_inputs, max_new_tokens=15)
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    
    response = qwen_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response.strip()

# ─────────────── 5. الدالة الرئيسية (دورة العمل) ───────────────

def analyze_folder(folder_path):
    all_text = []
    image_paths = []
    valid_images = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    
    # مسح المجلد
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)
            
            # جمع مسارات الصور (بحد أقصى 3 صور عشوائية كعينة)
            if ext in valid_images and len(image_paths) < 3:
                image_paths.append(full_path)
            
            # استخراج النصوص
            elif ext == ".pdf":
                all_text.append(get_text_from_pdf(full_path))
            elif ext in {".docx", ".doc"}:
                all_text.append(get_text_from_word(full_path))
            elif ext == ".txt":
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        all_text.append(f.read()[:200])
                except: pass

    combined_text = " ".join(all_text).strip()
    
    # تحليل الصور المجمعة
    image_descriptions = []
    if image_paths:
        image_descriptions = get_images_description(image_paths)
    
    if not image_descriptions and not combined_text:
        return "مجلد_غير_معروف"
        
    return generate_folder_name(image_descriptions, combined_text)

if __name__ == "__main__":
    while True:
        target_folder = input("\nأدخل مسار المجلد الذي تريد فحصه (أو اكتب exit للخروج): ").strip()
        if target_folder.lower() == 'exit':
            break
            
        target_folder = target_folder.strip('"').strip("'")
        
        if os.path.isdir(target_folder):
            print("⏳ جاري تحليل العينات (الصور والنصوص)...")
            folder_name = analyze_folder(target_folder)
            print(f"📁 الاسم المقترح: {folder_name}")
            print("-" * 50)
        else:
            print("❌ المسار غير صحيح أو المجلد غير موجود.")