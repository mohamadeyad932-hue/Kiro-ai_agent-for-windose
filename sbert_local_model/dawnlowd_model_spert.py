import os
from huggingface_hub import snapshot_download

# إعدادات الموديل والمسار
repo_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
local_dir = r"C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\sbert_local_model"

# مسارات الملفات الضخمة التي تثبت أن التحميل قد اكتمل سابقاً
safetensors_file = os.path.join(local_dir, "model.safetensors")
bin_file = os.path.join(local_dir, "pytorch_model.bin")

# التحقق: هل المجلد يحتوي على ملفات الأوزان الحقيقية؟
if os.path.exists(safetensors_file) or os.path.exists(bin_file):
    print("الموديل موجود بالفعل!")
else:
    print("جاري تحميل الموديل، يرجى الانتظار (قد يستغرق بعض الوقت حسب سرعة الإنترنت)...")
    
    # أمر التحميل
    snapshot_download(
        repo_id=repo_id, 
        local_dir=local_dir
    )
    
    print("لقد انتهيت من التحميل!")