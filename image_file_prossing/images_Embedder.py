"""
merged_clip_pipeline.py
يقوم بجمع ملفات الصور من المجلدات المحددة،
ويستخرج ميزاتها، ثم يولد بصماتها الرقمية باستخدام CLIP،
ويحفظ قوائم الملفات والبصمات في سكربتات منفصلة.
"""

import os
import sys
import torch
from PIL import Image
import transformers
from transformers import CLIPProcessor, CLIPModel

# إخفاء تحذيرات مكتبة الترانزفورمرز لتنظيف مخرجات الشاشة
transformers.logging.set_verbosity_error()
sys.stdout.reconfigure(encoding="utf-8")

# ─────────────── الإعدادات ───────────────

EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
# تحديد مسار الموديل المحلي الخاص بكِ ليعمل بدون إنترنت
MODEL_PATH = r"C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\models\clip_local_model"
HOME = os.path.expanduser("~")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

FOLDERS = {
    "desktop": os.path.join(HOME, "Desktop"),
    "documents": os.path.join(HOME, "Documents"),
    "downloads": os.path.join(HOME, "Downloads"),
}

# ─────────────── تحميل CLIP ───────────────

print("جاري تحميل نموذج CLIP للصور...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
try:
    processor = CLIPProcessor.from_pretrained(MODEL_PATH, local_files_only=True)
    model = CLIPModel.from_pretrained(MODEL_PATH, local_files_only=True).to(device)
    model.eval()
    print(f"تم التحميل بنجاح على: {device}\n")
except Exception as e:
    print(f"❌ خطأ في تحميل الموديل، تأكدي من مسار clip_local_model:\n{e}")
    sys.exit()

# ─────────────── الدوال الأساسية ───────────────


def scan_folder(path):
    """فحص مجلد وإرجاع جميع ملفاته باللواحق المحددة في قاموس."""
    files_dict = {}
    if not os.path.isdir(path):
        print(f"  المسار غير موجود: {path}")
        return files_dict

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                name, ext = os.path.splitext(entry.name)
                ext = ext.lower()
                if ext in EXTENSIONS:
                    files_dict[name] = ext
    except PermissionError:
        print(f"  لا توجد صلاحية: {path}")

    return files_dict


def get_embedding(image_path):
    """إرسال الصورة إلى CLIP والحصول على بصمة 512 بُعد."""
    with Image.open(image_path) as img:
        image = img.convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.get_image_features(**inputs)

    # تسوية البصمة وتجهيزها
    return outputs.squeeze().cpu().numpy().tolist()


def save_file_list_script(folder_name, files_dict):
    """حفظ قائمة الملفات في سكربت."""
    path = os.path.join(OUTPUT_DIR, f"{folder_name}_images_files.py")
    lines = [f'"""\nقاموس ملفات الصور في مجلد {folder_name}\nتوليد تلقائي\n"""\n']
    dict_name = f"{folder_name}_images"
    lines.append(f"# جميع الصور ذات اللواحق المستهدفة ({len(files_dict)} ملف)")
    lines.append(f"{dict_name} = {{")
    for name, ext in sorted(files_dict.items()):
        # تجنب مشاكل المسافات في أسماء الملفات
        clean_name = name.replace('"', '\\"')
        lines.append(f'    "{clean_name}": "{ext}",')
    lines.append("}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def save_vectors_script(folder_name, vectors):
    """حفظ قواميس البصمات في سكربت."""
    script_path = os.path.join(OUTPUT_DIR, f"{folder_name}_images_vectors.py")
    lines = [
        f'"""',
        f"قاموس بصمات صور مجلد {folder_name}",
        f"كل بصمة عبارة عن متجه 512 بُعد من نموذج CLIP",
        f"توليد تلقائي",
        f'"""',
        f"",
    ]
    var_name = f"{folder_name}_images_vectors"
    lines.append(f"# بصمات تشمل جميع الصور في {folder_name} ({len(vectors)} صورة)")
    lines.append(f"{var_name} = {{")

    for name, vec in vectors.items():
        clean_name = name.replace('"', '\\"')
        rounded = [round(v, 6) for v in vec]
        lines.append(f'    "{clean_name}":')
        lines.append(f"        {rounded},")

    lines.append("}\n")

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  تم حفظ البصمات: {script_path}")


# ─────────────── دورة التشغيل الرئيسية ───────────────

if __name__ == "__main__":
    vector_dicts = {}
    total_vectors = 0

    for folder_name, folder_path in FOLDERS.items():
        print(f"\n{'='*50}")
        print(f"جاري فحص ومعالجة الصور في: {folder_name}")
        print(f"{'='*50}")

        # 1. فحص المجلد وجمع الصور
        files_dict = scan_folder(folder_path)
        if not files_dict:
            continue

        # حفظ قاموس أسماء الصور
        save_file_list_script(folder_name, files_dict)
        print(f"📁 تم العثور على {len(files_dict)} صورة، جاري توليد البصمات...\n")

        # 2. توليد البصمات
        folder_vectors = {}
        for file_name, ext in files_dict.items():
            full_path = os.path.join(folder_path, file_name + ext)

            try:
                # استخراج المتجه
                vector = get_embedding(full_path)
                folder_vectors[file_name] = vector

                # طباعة أول 5 قيم للتأكد (نفس شكل كود إياد)
                short = [round(v, 4) for v in vector[:5]]
                print(f"  ✓ {file_name}{ext} → {short} ...")

            except Exception as e:
                print(f"  ⚠ خطأ في معالجة الصورة: {file_name}{ext} → {e}")
                continue

        # 3. حفظ قواميس البصمات
        if folder_vectors:
            save_vectors_script(folder_name, folder_vectors)
            vector_dicts[folder_name] = folder_vectors
            total_vectors += len(folder_vectors)

    # ─────────────── ملخص نهائي ───────────────
    print(f"\n{'='*50}")
    print(f"تم الانتهاء بنجاح! إجمالي بصمات الصور المولّدة: {total_vectors}")
    print("\nالقواميس المنشأة:")
    for key, vectors in vector_dicts.items():
        print(f"  {key}_images_vectors → {len(vectors)} بصمة")
