"""
merged_bert_pipeline.py
يقوم بجمع الملفات النصية من المجلدات المحددة، 
ويستخرج نصوصها، ثم يولد بصماتها الرقمية باستخدام BERT، 
ويحفظ قوائم الملفات والبصمات في سكربتات منفصلة.
"""

import os
import sys
import torch
import fitz
import docx
import transformers
from transformers import AutoTokenizer, AutoModel

# إخفاء تحذيرات مكتبة الترانزفورمرز لتنظيف مخرجات الشاشة
transformers.logging.set_verbosity_error()
sys.stdout.reconfigure(encoding='utf-8')

# ─────────────── الإعدادات ───────────────

EXTENSIONS = {'.txt', '.pdf', '.docx'}
MODEL_PATH = r"c:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\models\sbert_high_res"
HOME       = os.path.expanduser('~')
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

FOLDERS = {
    "desktop":   os.path.join(HOME, 'Desktop'),
    "documents": os.path.join(HOME, 'Documents'),
    "downloads": os.path.join(HOME, 'Downloads'),
}

# ─────────────── تحميل BERT ───────────────

print("جاري تحميل نموذج BERT...")
device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
model     = AutoModel.from_pretrained(MODEL_PATH, local_files_only=True).to(device)
model.eval()
print(f"تم التحميل على: {device}\n")

# ─────────────── دوال القراءة ───────────────

READERS = {
    ".txt":  lambda p: open(p, 'r', encoding='utf-8', errors='ignore').read(),
    ".pdf":  lambda p: "".join(page.get_text() for page in fitz.open(p)),
    ".docx": lambda p: "\n".join(par.text for par in docx.Document(p).paragraphs if par.text.strip()),
}

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

def get_embedding(text):
    """إرسال النص إلى BERT والحصول على بصمة 768 بُعد."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    mask   = inputs['attention_mask'].unsqueeze(-1).float()
    pooled = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1)
    return pooled.squeeze().cpu().numpy().tolist()

def save_file_list_script(folder_name, files_dict):
    """حفظ قائمة الملفات في سكربت."""
    path = os.path.join(OUTPUT_DIR, f"{folder_name}_files.py")
    lines = [
        f'"""\nقاموس ملفات مجلد {folder_name}\nتوليد تلقائي\n"""\n'
    ]
    dict_name = f"{folder_name}_file"
    lines.append(f"# جميع الملفات ذات اللواحق المستهدفة ({len(files_dict)} ملف)")
    lines.append(f"{dict_name} = {{")
    for name, ext in sorted(files_dict.items()):
        lines.append(f'    "{name}": "{ext}",')
    lines.append("}\n")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def save_vectors_script(folder_name, vectors):
    """حفظ قواميس البصمات في سكربت."""
    script_path = os.path.join(OUTPUT_DIR, f"{folder_name}_vectors.py")
    lines = [
        f'"""',
        f'قاموس بصمات ملفات مجلد {folder_name}',
        f'كل بصمة عبارة عن متجه 768 بُعد من نموذج BERT',
        f'توليد تلقائي',
        f'"""',
        f''
    ]
    var_name = f"{folder_name}_vectors"
    lines.append(f"# بصمات تشمل جميع الملفات في {folder_name} ({len(vectors)} ملف)")
    lines.append(f"{var_name} = {{")

    for name, vec in vectors.items():
        rounded = [round(v, 6) for v in vec]
        lines.append(f'    "{name}":')
        lines.append(f'        {rounded},')

    lines.append("}\n")

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n  تم حفظ البصمات: {script_path}")

# ─────────────── دورة التشغيل الرئيسية ───────────────

if __name__ == "__main__":
    vector_dicts = {}
    total_vectors = 0

    for folder_name, folder_path in FOLDERS.items():
        print(f"\n{'='*50}")
        print(f"جاري فحص ومعالجة: {folder_name}")
        print(f"{'='*50}")

        # 1. فحص المجلد وجمع الملفات
        files_dict = scan_folder(folder_path)
        if not files_dict:
            continue
        
        # حفظ قاموس أسماء الملفات (كما كان يفعل السكربت الأول)
        save_file_list_script(folder_name, files_dict)
        print(f"📁 تم العثور على {len(files_dict)} ملف، جاري توليد البصمات...\n")

        # 2. توليد البصمات
        folder_vectors = {}
        for file_name, ext in files_dict.items():
            full_path = os.path.join(folder_path, file_name + ext)
            
            try:
                text = READERS[ext](full_path)
            except Exception as e:
                print(f"  ⚠ خطأ في القراءة: {file_name}{ext} → {e}")
                continue
            
            if not text.strip():
                print(f"  ⚠ فارغ: {file_name}{ext}")
                continue
            
            # استخراج المتجه
            vector = get_embedding(text)
            folder_vectors[file_name] = vector
            
            short = [round(v, 4) for v in vector[:5]]
            print(f"  ✓ {file_name}{ext} → {short} ...")

        # 3. حفظ قواميس البصمات (كما كان يفعل السكربت الثاني)
        if folder_vectors:
            save_vectors_script(folder_name, folder_vectors)
            vector_dicts[folder_name] = folder_vectors
            total_vectors += len(folder_vectors)

    # ─────────────── ملخص نهائي ───────────────
    print(f"\n{'='*50}")
    print(f"تم الانتهاء بنجاح! إجمالي البصمات المولّدة: {total_vectors}")
    print("\nالقواميس المنشأة:")
    for key, vectors in vector_dicts.items():
        print(f"  {key}_vectors → {len(vectors)} بصمة")