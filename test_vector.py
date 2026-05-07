from sentence_transformers import SentenceTransformer

# تحميل النموذج المحفوظ محلياً
model_path = r'C:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\models\sbert_high_res'
model = SentenceTransformer(model_path)

# قائمة تحتوي على عدة جمل باللغة العربية
arabic_sentences = [
    "الذكاء الاصطناعي يغير مستقبل التكنولوجيا.",
    "تعلم الآلة هو فرع من فروع الذكاء الاصطناعي.",
    "يتميز نموذج بيرت بفهمه العميق لسياق الكلمات.",
    "اللغة العربية من أجمل اللغات وأكثرها تعقيداً."
]

print("جاري حساب المتجهات (Vectors) للجمل...\n")

# استخراج المتجهات (Embeddings)
# هذه الدالة ترجع مصفوفة numpy تحتوي على المتجهات لكل جملة
embeddings = model.encode(arabic_sentences)

# طباعة كل جملة مع بعض المعلومات عن المتجه الخاص بها
for sentence, embedding in zip(arabic_sentences, embeddings):
    print(f"الجملة: {sentence}")
    print(f"حجم المتجه (أبعاد الفيكتور): {embedding.shape}")
    # طباعة أول 5 قيم فقط من الفيكتور كعينة لتوضيح شكل البيانات
    print(f"عينة من قيم الفيكتور (أول 5 أرقام): {embedding[:5]}//5") 
    print("-" * 60)

print("تم استخراج المتجهات بنجاح!")
