import chromadb

# 1. الاتصال بقاعدة البيانات الموجودة في مجلدك
DB_PATH = "./my_vector_db"
chroma_client = chromadb.PersistentClient(path=DB_PATH)

# 2. جلب المجموعة (Collection) التي أنشأناها سابقاً
collection = chroma_client.get_collection(name="my_documents")

# 3. استخراج البيانات (المهم هنا هو إضافة include لطلب المتجهات)
# افتراضياً Chroma لا تعيد المتجهات لتوفير الذاكرة، لذا نطلبها بالاسم
results = collection.get(
    include=["embeddings", "metadatas", "documents"]
)

print(f" إجمالي العناصر الموجودة: {len(results['ids'])}")
print("-" * 50)

# 4. عرض المتجهات لكل ملف بشكل منظم
for i in range(len(results['ids'])):
    file_id = results['ids'][i]
    metadata = results['metadatas'][i]
    vector = results['embeddings'][i] # هنا المتجه (المصفوفة)
    
    # سنطبع أول 3 أرقام فقط من المتجه لكي لا تمتلئ الشاشة
    print(f" معرف الجزء: {file_id}")
    print(f" اسم الملف الأصلي: {metadata['filename']}")
    print(f" المتجه (أول 3 أرقام): {vector[:3]} ... (الطول الكلي: {len(vector)})")
    print("-" * 30)