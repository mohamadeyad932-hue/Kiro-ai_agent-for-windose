"""
images_caption_Embedder.py
يقوم بجمع الصور من المجلدات المحددة (سطح المكتب، التنزيلات، المستندات)،
ويولد وصفاً نصياً لكل صورة باستخدام BLIP،
ثم يحول الوصف النصي إلى بصمة رقمية (vector) باستخدام SBERT،
ويحفظ النتائج في سكربتات بايثون منفصلة.
"""

import os
import sys
import torch
import transformers
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import AutoTokenizer, AutoModel
from pathlib import Path

# إخفاء تحذيرات مكتبة الترانزفورمرز لتنظيف مخرجات الشاشة
transformers.logging.set_verbosity_error()
sys.stdout.reconfigure(encoding='utf-8')




def scan_images(path):
    """فحص مجلد وإرجاع جميع الصور الموجودة فيه كقاموس {اسم: لاحقة}."""
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
                if ext in IMAGE_EXTENSIONS:
                    files_dict[name] = ext
    except PermissionError:
        print(f"  لا توجد صلاحية: {path}")

    return files_dict


def generate_caption(image_path):
    """توليد وصف نصي لصورة واحدة باستخدام BLIP."""
    try:
        raw_image = Image.open(image_path).convert('RGB')
    except Exception as e:
        print(f"  خطا في فتح الصورة: {e}")
        return None

    inputs = blip_processor(images=raw_image, return_tensors="pt").to(blip_device)
    with torch.no_grad():
        out = blip_model.generate(
            **inputs, 
            max_new_tokens=100,       # السماح بنص طويل
            do_sample=True,           # تفعيل أخذ العينات العشوائية لتنويع الكلمات
            top_p=0.9,                # استخدام Nucleus Sampling لاختيار الكلمات الأكثر منطقية
            temperature=0.8,          # زيادة الإبداع قليلاً لتقليل النمطية
            repetition_penalty=1.5,   # عقوبة مشددة أكثر على التكرار
            no_repeat_ngram_size=2    # منع تكرار نفس الكلمتين متتاليتين تماماً (يحل مشكلة التكرار اللانهائي)
        )
    caption = blip_processor.decode(out[0], skip_special_tokens=True)
    return caption


def get_text_embedding(text):
    """تحويل نص إلى بصمة رقمية 768 بُعد باستخدام SBERT (Mean Pooling)."""
    inputs = sbert_tokenizer(text, return_tensors="pt", truncation=True,
                              max_length=512, padding=True).to(blip_device)
    with torch.no_grad():
        outputs = sbert_model(input_ids=inputs['input_ids'],
                               attention_mask=inputs['attention_mask'])
    mask = inputs['attention_mask'].unsqueeze(-1).float()
    pooled = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1)
    return pooled.squeeze(0).cpu().numpy().tolist()


# ─────────────── دوال الحفظ ───────────────


def save_image_to_text_script(folder_name, captions_dict):
    """
    حفظ قاموس الصور وأوصافها النصية في سكربت بايثون.
    الملف الناتج: desktop_image_to_text.py مثلاً
    """
    script_path = os.path.join(OUTPUT_DIR, f"{folder_name}_image_to_text.py")
    lines = [
        f'"""',
        f'قاموس صور مجلد {folder_name} مع الوصف النصي (BLIP)',
        f'كل مفتاح هو اسم الصورة وكل قيمة هي الوصف النصي',
        f'توليد تلقائي',
        f'"""',
        ''
    ]
    var_name = f"{folder_name}_image_captions"
    lines.append(f"# صور مجلد {folder_name} ({len(captions_dict)} صورة)")
    lines.append(f"{var_name} = {{")
    for img_name, caption in sorted(captions_dict.items()):
        # تنظيف علامات الاقتباس داخل الوصف
        safe_caption = caption.replace('"', '\\"')
        lines.append(f'    "{img_name}": "{safe_caption}",')
    lines.append("}\n")

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n  تم حفظ الاوصاف: {script_path}")


def save_vectors_script(folder_name, vectors):
    """حفظ قاموس البصمات (vectors) في سكربت بايثون."""
    script_path = os.path.join(OUTPUT_DIR, f"{folder_name}_vectors.py")
    lines = [
        f'"""',
        f'قاموس بصمات صور مجلد {folder_name}',
        f'كل بصمة عبارة عن متجه 768 بُعد من نموذج SBERT (محول من وصف BLIP)',
        f'توليد تلقائي',
        f'"""',
        ''
    ]
    var_name = f"{folder_name}_image_vectors"
    lines.append(f"# بصمات صور {folder_name} ({len(vectors)} صورة)")
    lines.append(f"{var_name} = {{")

    for name, vec in vectors.items():
        rounded = [round(v, 6) for v in vec]
        lines.append(f'    "{name}":')
        lines.append(f'        {rounded},')

    lines.append("}\n")

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  تم حفظ البصمات: {script_path}")


def save_file_list_script(folder_name, files_dict):
    """حفظ قائمة أسماء الصور ولواحقها في سكربت."""
    path = os.path.join(OUTPUT_DIR, f"{folder_name}_files.py")
    lines = [
        f'"""',
        f'قاموس صور مجلد {folder_name}',
        f'توليد تلقائي',
        f'"""',
        ''
    ]
    dict_name = f"{folder_name}_image_file"
    lines.append(f"# جميع الصور ({len(files_dict)} صورة)")
    lines.append(f"{dict_name} = {{")
    for name, ext in sorted(files_dict.items()):
        lines.append(f'    "{name}": "{ext}",')
    lines.append("}\n")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ─────────────── دورة التشغيل الرئيسية ───────────────

if __name__ == "__main__":
    vector_dicts = {}
    total_images = 0

    for folder_name, folder_path in FOLDERS.items():
        print(f"\n{'='*60}")
        print(f"جاري فحص ومعالجة الصور في: {folder_name}")
        print(f"{'='*60}")

        # 1. فحص المجلد وجمع الصور
        files_dict = scan_images(folder_path)
        if not files_dict:
            print(f"  لا توجد صور في {folder_name}")
            continue

        # حفظ قاموس أسماء الصور
        save_file_list_script(folder_name, files_dict)
        print(f"  تم العثور على {len(files_dict)} صورة، جاري التحليل...\n")

        # 2. توليد الأوصاف النصية (BLIP)
        captions_dict = {}
        for img_name, ext in files_dict.items():
            full_path = os.path.join(folder_path, img_name + ext)

            try:
                caption = generate_caption(full_path)
            except PermissionError:
                print(f"  الصورة مقفولة، تم تخطيها: {img_name}{ext}")
                continue
            except Exception as e:
                print(f"  خطا في معالجة: {img_name}{ext} -> {e}")
                continue

            if caption:
                captions_dict[img_name] = caption
                print(f"  [BLIP] {img_name}{ext} -> \"{caption}\"")

        if not captions_dict:
            print(f"  لم يتم توليد اي وصف لمجلد {folder_name}")
            continue

        # حفظ سكربت الأوصاف النصية
        save_image_to_text_script(folder_name, captions_dict)

        # 3. تحويل الأوصاف النصية إلى بصمات رقمية (SBERT)
        print(f"\n  جاري توليد بصمات SBERT من الاوصاف النصية...")
        folder_vectors = {}
        for img_name, caption in captions_dict.items():
            vector = get_text_embedding(caption)
            folder_vectors[img_name] = vector

            short = [round(v, 4) for v in vector[:5]]
            print(f"  [SBERT] {img_name} -> {short} ...")

        # 4. حفظ سكربت البصمات
        if folder_vectors:
            save_vectors_script(folder_name, folder_vectors)
            vector_dicts[folder_name] = folder_vectors
            total_images += len(folder_vectors)

    # ─────────────── ملخص نهائي ───────────────
    print(f"\n{'='*60}")
    print(f"تم الانتهاء بنجاح! اجمالي الصور المعالجة: {total_images}")
    print(f"\nالملفات المنشاة:")
    for key, vectors in vector_dicts.items():
        print(f"  {key}_image_to_text.py  -> {len(vectors)} وصف نصي")
        print(f"  {key}_vectors.py        -> {len(vectors)} بصمة رقمية")
        print(f"  {key}_files.py          -> قائمة اسماء الصور")
    print("=" * 60)
