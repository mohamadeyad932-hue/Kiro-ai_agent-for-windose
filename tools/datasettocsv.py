import os
import pandas as pd

# مسار المجلد الرئيسي للداتا سيت
dataset_path = r'C:\Kiro-Project\archive\natural_images'
data = []
image_id = 1

# فحص كل مجلد فرعي (Category)
for category in os.listdir(dataset_path):
    category_path = os.path.join(dataset_path, category)
    
    if os.path.isdir(category_path):
        # سحب كل الملفات داخل المجلد
        for img_name in os.listdir(category_path):
            # التأكد أن الملف صورة (jpg, png, jpeg)
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                data.append({
                    "ID": image_id,
                    "Image_Name": img_name,
                    "Label": category,
                    "Full_Path": os.path.join(category, img_name)
                })
                image_id += 1

# حفظ الملف بترميز يدعم العربي والإكسيل
df = pd.DataFrame(data)
df.to_csv('final_dataset_index.csv', index=False, encoding='utf-8-sig')

print(f"✅ تم بنجاح! تم فهرسة {len(data)} صورة في ملف CSV.")