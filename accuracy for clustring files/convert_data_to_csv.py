import os
import pandas as pd

def process_nested_folders(root_path):
    data = []
    file_count = 1
    
    # التأكد من وجود المجلد الرئيسي
    if not os.path.exists(root_path):
        print(f"❌ المسار '{root_path}' غير موجود! تأكد من كتابة اسم المجلد بشكل صحيح.")
        return
    
    print(f"🔍 جاري البحث في المجلد الرئيسي: {os.path.abspath(root_path)}")

    # 1. المرور على كل المجلدات الفرعية داخل المجلد الرئيسي
    for folder_name in os.listdir(root_path):
        folder_path = os.path.join(root_path, folder_name)
        
        # نتحقق إذا كان هذا العنصر هو "مجلد" (ليتم اعتباره تصنيفاً/نوعاً)
        if os.path.isdir(folder_path):
            print(f"📂 جاري معالجة النوع: [{folder_name}]")
            
            # 2. المرور على الملفات داخل هذا المجلد الفرعي
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                # التأكد أنه ملف نصي (وليس مجلداً فرعياً آخر)
                if os.path.isfile(file_path):
                    data.append({
                        'رقم الملف': file_count,
                        'اسم الملف': filename,
                        'نوع الملف': folder_name  # النوع هنا هو اسم المجلد الفرعي
                    })
                    file_count += 1
    
    # تحويل البيانات المجموعة إلى جدول (DataFrame)
    df = pd.DataFrame(data)
    
    if not df.empty:
        output_file = 'my_dataset_arb_and_english.csv'
        try:
            # محاولة حفظ الملف
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n✅ تم بنجاح! تم جمع {len(df)} ملف من كافة المجلدات.")
            print(f"💾 تم حفظ البيانات في الملف: {output_file}")
        except PermissionError:
            # حل مشكلة ملف الإكسل المفتوح
            print(f"\n❌ خطأ: لا يمكن حفظ الملف '{output_file}' لأنك تفتحه حالياً في برنامج آخر (مثل Excel).")
            print("💡 يرجى إغلاق ملف الإكسل ثم أعد تشغيل الكود.")
    else:
        print("\n لم يتم العثور على أي مجلدات فرعية تحتوي على ملفات.")

# ---------- تشغيل البرنامج ----------
# تأكد أن مجلد 'cv' يحتوي بداخله على مجلدات (مثل 'sport', 'politics', إلخ)
path = r"C:\Users\eyad\Documents\arabic and english data set" 
process_nested_folders(path)