import os
import sys

# إصلاح مشكلة الرموز التعبيرية في الويندوز
sys.stdout.reconfigure(encoding="utf-8")

from transformers import CLIPProcessor, CLIPModel


def download_and_setup():
    # 1. تحديد المجلد الرئيسي للمشروع وإنشاء مجلد فرعي باسم models/clip_local_model
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "models", "clip_local_model")
    os.makedirs(target_dir, exist_ok=True)

    print("=" * 50)
    print(f"🚀 بدء تجهيز محرك الصور كيرو (Kiro Image Engine)")
    print(f"📁 مسار الحفظ المحلي: {target_dir}")
    print("=" * 50)

    # اسم الموديل العالمي من OpenAI
    model_name = "openai/clip-vit-base-patch32"

    try:
        # 2. تحميل الموديل والبروسيسور من الإنترنت
        print(f"📥 جاري الاتصال بالسيرفر لتحميل {model_name}...")
        print("💡 ملاحظة: الحجم حوالي 600MB، يرجى عدم إغلاق الواجهة...")

        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)

        # 3. حفظ الملفات في المجلد الحالي لتعمل بدون إنترنت لاحقاً
        print("💾 جاري حفظ الأوزان والإعدادات محلياً...")
        model.save_pretrained(target_dir)
        processor.save_pretrained(target_dir)

        print("=" * 50)
        print("✅ تم بنجاح! الموديل جاهز الآن للعمل Offline.")
        print(f"📂 تأكدي من وجود ملف 'pytorch_model.bin' داخل المجلد الآن.")
        print("=" * 50)

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")
        print("⚠️ تأكدي من اتصال الإنترنت ومن تفعيل البيئة الافتراضية (venv).")


if __name__ == "__main__":
    download_and_setup()
