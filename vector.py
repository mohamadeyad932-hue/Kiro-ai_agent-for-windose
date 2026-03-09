import os
import fitz  # PyMuPDF
import docx  
import torch
import chromadb
import numpy as np
from transformers import AutoTokenizer, AutoModel

# ─── 1. إعداد النموذج المحلي ──────────────────────────────────────────
MODEL_NAME = r"c:\Users\eyad\Desktop\bert_local_model"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"جاري تحميل نموذج BERT من المسار المحلي على ({device})...\n" + "-"*40)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(device)
model.eval() 
print(" تم تحميل النموذج بنجاح!")

# ─── 2. إعداد ChromaDB ──────────────────────────────────────────────
DB_PATH = "./my_vector_db"
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection = chroma_client.get_or_create_collection(
    name="my_documents",
    metadata={"hnsw:space": "cosine"}
)

# ─── 3. دوال استخراج النصوص ──────────────────────────────────────────
def extract_text_from_file(file_path: str) -> str:
    ext = file_path.lower().split('.')[-1]
    text = ""
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()
        elif ext == 'docx':
            doc = docx.Document(file_path)
            text = "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])
        elif ext == 'pdf':
            with fitz.open(file_path) as pdf:
                for page in pdf: text += page.get_text()
    except: pass
    return text

# ─── 4. المعالجة والطباعة والتخزين ──────────────────────────────────────
# ─── 4. المعالجة والطباعة والتخزين (نسخة بدون إيموجي لتجنب أخطاء الويندوز) ───
def process_and_store_in_chroma(directory_path: str):
    if not os.path.exists(directory_path):
        print(f"[X] Path not found: {directory_path}")
        return

    supported_exts = ['txt', 'docx', 'pdf']
    files = [f for f in os.listdir(directory_path) if f.lower().split('.')[-1] in supported_exts]
    
    # استبدلنا الصاروخ بكلمة START
    print(f"\n[START] Processing {len(files)} files...\n" + "="*50)

    for filename in files:
        file_path = os.path.join(directory_path, filename)
        text = extract_text_from_file(file_path)
        
        if not text.strip(): continue

        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, 
                           stride=50, return_overflowing_tokens=True, padding=True).to(device)
        
        chunk_texts = tokenizer.batch_decode(inputs['input_ids'], skip_special_tokens=True)
        
        embeddings, ids, metadatas, documents = [], [], [], []

        # استبدلنا إيموجي الورقة بكلمة FILE
        print(f"\n--- FILE: {filename} ---")

        with torch.no_grad():
            for i in range(len(chunk_texts)):
                outputs = model(input_ids=inputs['input_ids'][i].unsqueeze(0), 
                                attention_mask=inputs['attention_mask'][i].unsqueeze(0))
                
                token_embeddings = outputs.last_hidden_state[0]
                mask = inputs['attention_mask'][i].unsqueeze(-1).float()
                vector = (torch.sum(token_embeddings * mask, dim=0) / torch.clamp(mask.sum(dim=0), min=1e-9))
                vector_list = vector.cpu().numpy().tolist()

                # طباعة المتجه بشكل نظيف
                short_vector = [round(num, 4) for num in vector_list[:5]]
                print(f"   Part {i+1} Vector: {short_vector} ... (768 dim)")

                embeddings.append(vector_list)
                documents.append(chunk_texts[i])
                metadatas.append({"filename": filename, "chunk_index": i})
                ids.append(f"{filename}_chunk_{i}")

        collection.upsert(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids)
        print(f"[OK] Saved {len(chunk_texts)} chunks.")

    print("\n" + "="*50)
    print(f"[DONE] Total items in DB: {collection.count()}")
# ─── 5. التشغيل ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # نصيحة: جرب على مجلد صغير به ملفين أو ثلاثة في البداية
    MY_DIRECTORY = r"c:\Users\eyad\Desktop" 
    process_and_store_in_chroma(MY_DIRECTORY)