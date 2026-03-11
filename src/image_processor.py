"""
image_processor.py
------------------
وحدة معالجة الصور لمشروع الوكيل الذكي (Kiro) - المرحلة الأولى.
المهام المنجزة: استخراج البيانات الوصفية، التحويل لتدرج رمادي،
استخراج البصمة (pHash)، ومقارنة الصور للكشف عن التكرار.
"""

import cv2
import os
from PIL import Image
import imagehash

def get_image_metadata(image_path):
    """استخراج البيانات الوصفية للصورة (الأبعاد، الصيغة، القنوات)."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"Success": False, "Error": "فشل في قراءة الصورة"}
        
        height, width = img.shape[:2]
        channels = img.shape[2] if len(img.shape) == 3 else 1
        _, extension = os.path.splitext(image_path)
        
        return {
            "Success": True,
            "Dimensions": f"{width}x{height}",
            "Format": extension.upper(),
            "Channels": channels
        }
    except Exception as e:
        return {"Success": False, "Error": str(e)}

def convert_to_grayscale(image_path, output_path=None):
    """تحويل الصورة إلى تدرج رمادي لحفظ مساحة التخزين وتوحيد المعالجة."""
    try:
        img = cv2.imread(image_path)
        if img is None: return None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if output_path:
            cv2.imwrite(output_path, gray)
        return gray
    except:
        return None

def get_image_phash(image_path):
    """توليد بصمة فريدة للصورة باستخدام خوارزمية pHash."""
    try:
        return imagehash.phash(Image.open(image_path))
    except:
        return None

def compare_phashes(phash1, phash2):
    """حساب مسافة هامنج (Hamming Distance) بين بصمتين."""
    if phash1 is None or phash2 is None: return None
    return phash1 - phash2

def similarity_percentage(phash1, phash2):
    """حساب نسبة التشابه المئوية بين صورتين."""
    distance = compare_phashes(phash1, phash2)
    if distance is None: return 0.0
    
    max_distance = phash1.hash.size
    similarity = (1 - distance / max_distance) * 100
    return round(similarity, 2)

def process_image_pair(image_path1, image_path2, threshold=95):
    """دالة شاملة لمقارنة صورتين وإرجاع النتائج التفصيلية."""
    result = {"comparison": {}}
    phash1 = get_image_phash(image_path1)
    phash2 = get_image_phash(image_path2)

    if phash1 and phash2:
        sim_percent = similarity_percentage(phash1, phash2)
        result["comparison"] = {
            "similarity_percent": sim_percent,
            "is_duplicate": sim_percent >= threshold
        }
    else:
        result["comparison"]["error"] = "فشل استخراج البصمة"
        
    return result

# =====================================================================
# قسم التشغيل الأساسي (Main) مع المسارات الذكية التلقائية
# =====================================================================
if __name__ == "__main__":
    
    # تحديد مسار المجلد الرئيسي للمشروع (Kiro-Project) برمجياً
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # تحديد مسارات مجلدات البيانات
    raw_path = os.path.join(project_root, "data", "raw")
    processed_path = os.path.join(project_root, "data", "processed")
    
    # إنشاء مجلد المعالجة إذا لم يكن موجوداً
    os.makedirs(processed_path, exist_ok=True)

    # تحديد مسارات الصور الاختبارية بناءً على تسمياتك
    img_base = os.path.join(raw_path, "sample1.jpg")
    img_dup = os.path.join(raw_path, "duplicate_sample1.jpg")
    img_diff = os.path.join(raw_path, "sample2.jpg")
    img_png = os.path.join(raw_path, "sample3.png")

    print("\n" + "="*40)
    print("🤖 بدء تشغيل الوكيل الذكي Kiro - المرحلة الأولى")
    print("="*40)

    # 1. اختبار استخراج البيانات الوصفية (لملف PNG)
    print("\n[1] فحص البيانات الوصفية (Metadata):")
    meta = get_image_metadata(img_png)
    if meta.get("Success"):
        print(f"✅ الصورة: sample3.png | الأبعاد: {meta['Dimensions']} | الصيغة: {meta['Format']}")
    else:
        print("❌ تأكدي من وجود الصورة sample3.png في مجلد data/raw")

    # 2. اختبار التحويل إلى تدرج رمادي
    print("\n[2] التحويل إلى تدرج رمادي (Grayscale):")
    gray_out = os.path.join(processed_path, "sample1_gray.jpg")
    if convert_to_grayscale(img_base, gray_out) is not None:
        print(f"✅ تم تحويل الصورة بنجاح وحفظها في: مجلد data/processed")

    # 3. اختبار التكرار (صور متطابقة)
    print("\n[3] اختبار المطابقة (التكرار): sample1.jpg مع النسخة المكررة")
    res_dup = process_image_pair(img_base, img_dup)
    if "similarity_percent" in res_dup.get("comparison", {}):
        print(f"   نسبة التشابه: {res_dup['comparison']['similarity_percent']}%")
        print(f"   النتيجة: {'مكررة (Duplicate) ⚠️' if res_dup['comparison']['is_duplicate'] else 'غير مكررة 🟢'}")

    # 4. اختبار الاختلاف (صور مختلفة)
    print("\n[4] اختبار المطابقة (اختلاف): sample1.jpg مع sample2.jpg")
    res_diff = process_image_pair(img_base, img_diff)
    if "similarity_percent" in res_diff.get("comparison", {}):
        print(f"   نسبة التشابه: {res_diff['comparison']['similarity_percent']}%")
        print(f"   النتيجة: {'مكررة (Duplicate) ⚠️' if res_diff['comparison']['is_duplicate'] else 'غير مكررة 🟢'}")

    print("\n" + "="*40)
    print("🏁 اكتملت المرحلة بنجاح!")
    print("="*40 + "\n")