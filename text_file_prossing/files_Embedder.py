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


def _read_txt(path):
    """قراءة ملف نصي مع إغلاق الملف بشكل صحيح."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def _read_pdf(path):
    """قراءة ملف PDF مع إغلاق الملف بشكل صحيح."""
    with fitz.open(path) as doc:
        return "".join(page.get_text() for page in doc)


def _read_docx(path):
    """قراءة ملف Word."""
    return "\n".join(par.text for par in docx.Document(path).paragraphs if par.text.strip())


READERS = {
    ".txt":  _read_txt,
    ".pdf":  _read_pdf,
    ".docx": _read_docx,
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

def _embed_single_chunk(input_ids, attention_mask):
    """تمرير chunk واحد عبر BERT وإرجاع vector بعد Mean Pooling."""
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    mask = attention_mask.unsqueeze(-1).float()
    pooled = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1)
    return pooled.squeeze(0)  # شكل: (768,)


def get_embedding(text, chunk_size=512, overlap=50):
    """
    تقسيم النص إلى أجزاء (chunks) وتوليد بصمة 768 بُعد تمثل الملف كاملاً.

    - chunk_size: حجم كل جزء بالـ tokens (الحد الأقصى لـ BERT = 512)
    - overlap: عدد tokens المتداخلة بين الأجزاء لضمان عدم ضياع السياق
    """
    # تقطيع النص كاملاً بدون قطع
    all_tokens = tokenizer(text, add_special_tokens=False)['input_ids']

    # إذا النص قصير بما يكفي، نعالجه مباشرة
    usable_size = chunk_size - 2  # خصم 2 لـ [CLS] و [SEP]
    if len(all_tokens) <= usable_size:
        inputs = tokenizer(text, return_tensors="pt", truncation=True,
                           max_length=chunk_size, padding=True).to(device)
        return _embed_single_chunk(inputs['input_ids'], inputs['attention_mask']).cpu().numpy().tolist()

    # تقسيم النص الطويل إلى أجزاء متداخلة
    cls_id = tokenizer.cls_token_id
    sep_id = tokenizer.sep_token_id
    step = usable_size - overlap
    chunk_vectors = []

    for start in range(0, len(all_tokens), step):
        chunk_ids = all_tokens[start:start + usable_size]

        # إضافة [CLS] في البداية و [SEP] في النهاية
        chunk_ids = [cls_id] + chunk_ids + [sep_id]
        attn_mask = [1] * len(chunk_ids)

        # padding إذا كان الجزء الأخير أقصر
        pad_len = chunk_size - len(chunk_ids)
        if pad_len > 0:
            chunk_ids += [tokenizer.pad_token_id] * pad_len
            attn_mask += [0] * pad_len

        input_ids = torch.tensor([chunk_ids], device=device)
        attention_mask = torch.tensor([attn_mask], device=device)

        vec = _embed_single_chunk(input_ids, attention_mask)
        chunk_vectors.append(vec)

    # حساب معدل بصمات كل الأجزاء → vector واحد يمثل الملف كاملاً
    final_vector = torch.stack(chunk_vectors).mean(dim=0)
    return final_vector.cpu().numpy().tolist()

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
            except PermissionError:
                print(f"  ⚠ الملف قيد الاستخدام (مقفول)، تم تخطيه تلقائياً: {file_name}{ext}")
                continue
            except FileNotFoundError:
                print(f"  ⚠ اختفى الملف فجأة (ربما قمت بنقله أو حذفه للتو): {file_name}{ext}")
                continue
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