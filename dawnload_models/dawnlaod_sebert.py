import os
import sys

# إصلاح مشكلة الرموز التعبيرية في الويندوز
sys.stdout.reconfigure(encoding="utf-8")

from transformers import AutoTokenizer, AutoModel

def download_and_setup():
    # 1. تحديد المجلد الرئيسي للمشروع وإنشاء مجلد فرعي باسم models/sbert_high_res
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "models", "sbert_high_res")
    os.makedirs(target_dir, exist_ok=True)

    print("=" * 50)
    print(f"🚀 بدء تجهيز محرك النصوص كيرو (Kiro SBERT Text Engine)")
    print(f"📁 مسار الحفظ المحلي: {target_dir}")
    print("=" * 50)

    # اسم الموديل العالمي (يدعم اللغة العربية بدقة عالية)
    model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    try:
        # 2. تحميل الموديل والتوكنايزر من الإنترنت
        print(f"📥 جاري الاتصال بالسيرفر لتحميل {model_name}...")
        print("💡 ملاحظة: الحجم قد يصل إلى جيجابايت تقريباً، يرجى عدم إغلاق الواجهة...")

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)

        # 3. حفظ الملفات في المجلد الحالي لتعمل بدون إنترنت لاحقاً
        print("💾 جاري حفظ الأوزان والإعدادات محلياً...")
        tokenizer.save_pretrained(target_dir)
        model.save_pretrained(target_dir)

        print("=" * 50)
        print("✅ تم بنجاح! نموذج SBERT جاهز الآن للعمل Offline.")
        print(f"📂 تأكد من وجود ملف 'pytorch_model.bin' أو الأوزان داخل مجلد models/sbert_high_res.")
        print("=" * 50)

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")
        print("⚠️ تأكد من اتصال الإنترنت ومن تفعيل البيئة الافتراضية (venv).")

if __name__ == "__main__":
    download_and_setup()
