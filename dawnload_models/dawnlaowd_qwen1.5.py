import os
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

# ─────────────── 1. إعداد مسار الحفظ والنموذج ───────────────

# إنشاء مجلد models بجانب السكربت الحالي
MODEL_DIR = os.path.join(os.getcwd(), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

print(f"جاري تجهيز وتحميل النموذج: {MODEL_ID}...")
print(f"سيتم حفظ الملفات في المجلد: {MODEL_DIR}")
print("يرجى الانتظار، سيتم التحميل من الإنترنت... (قد يستغرق وقتاً حسب سرعة الاتصال)")

# ─────────────── 2. تحميل النموذج من الإنترنت ───────────────

# نحمل النموذج بشكله الأصلي (بدون ضغط 4-bit) لضمان حفظ الملفات الأساسية سليمة
model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_ID,
    device_map="auto"
)

processor = AutoProcessor.from_pretrained(MODEL_ID)

print("تم التحميل من الإنترنت بنجاح! جاري حفظ الملفات محلياً...")

# ─────────────── 3. حفظ النموذج في المجلد ───────────────

# حفظ النموذج والمعالج بشكل نهائي في مجلد models
model.save_pretrained(MODEL_DIR)
processor.save_pretrained(MODEL_DIR)

print("\n✅ تم حفظ النموذج بنجاح!")
print(f"الملفات الآن موجودة وجاهزة في: {MODEL_DIR}")
print("ملاحظة: عند كتابة كود التشغيل لاحقاً، اجعل مسار النموذج هو المتغير MODEL_DIR بدلاً من MODEL_ID.")