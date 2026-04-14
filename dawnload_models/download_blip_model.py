import os
from transformers import BlipProcessor, BlipForConditionalGeneration

def download_blip_model():
    """
    تقوم هذه الدالة بتحميل نموذج BLIP من HuggingFace
    والذي يستخدم لتوليد وصف نصي (Caption) للصور المرفوعة.
    وسيتم حفظ النموذج محلياً في مجلد 'model'.
    """
    model_id = "Salesforce/blip-image-captioning-base"
    
    # تحديد مسار الحفظ ليكون داخل مجلد "model" في مسار المشروع الرئيسي
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_directory = os.path.join(current_dir, "model", "blip-image-captioning-base")

    print(f"بدء تحميل النموذج (BLIP) لتوصيف الصور...")
    print(f"المعرف: {model_id}")
    print("يرجى الانتظار، قد يستغرق التحميل بضع دقائق حسب سرعة الإنترنت...\n")
    
    try:
        # تحميل المعالج (Processor) والنموذج (Model) من الأنترنت
        processor = BlipProcessor.from_pretrained(model_id)
        model = BlipForConditionalGeneration.from_pretrained(model_id)

        print(f"جاري حفظ النموذج في المجلد المحلي:\n{save_directory}")
        os.makedirs(save_directory, exist_ok=True)
        
        # حفظ المعالج والنموذج محلياً
        processor.save_pretrained(save_directory)
        model.save_pretrained(save_directory)

        print("\nتم التحميل والحفظ بنجاح!")
        print("يمكنك الآن استخدام النموذج محلياً (Offline) في مشروعك.")
        
    except Exception as e:
        print(f"\nحدث خطأ أثناء التحميل: {e}")

if __name__ == "__main__":
    download_blip_model()
