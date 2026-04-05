import torch
import PIL
import transformers
import sentence_transformers
import platform


def check_kiro_system():
    print("🚀 --- فحص جاهزية محرك كيرو الذكي --- 🚀")
    print(f"💻 نظام التشغيل: {platform.system()} {platform.release()}")

    try:
        # 1. فحص المعالج الرسومي (للسرعة)
        device = (
            "GPU (CUDA) ✅"
            if torch.cuda.is_available()
            else "CPU ⚠️ (سيظهر البطء قليلاً)"
        )
        print(f"⚙️ المعالج المستخدم: {device}")

        # 2. فحص المكتبات الأساسية
        print(f"📦 نسخة Torch: {torch.__version__}")
        print(f"📦 نسخة Transformers: {transformers.__version__}")

        # 3. اختبار وهمي سريع لمحرك الصور (بدون تحميل موديل كامل)
        from PIL import Image

        print("🖼️ مكتبة الصور (Pillow): جاهزة ✅")

        # 4. فحص مكتبة الـ PDF (التي نزلتِها مؤخراً)
        import fitz

        print("📄 مكتبة PDF (PyMuPDF): جاهزة ✅")

        print("\n✨ النتيجة: بيئة العمل جاهزة للانطلاق!")

    except Exception as e:
        print(f"\n❌ يوجد نقص أو خطأ في الإعدادات: {e}")


if __name__ == "__main__":
    check_kiro_system()
