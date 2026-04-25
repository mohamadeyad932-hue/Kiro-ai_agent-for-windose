"""
convert gropss_image to folders names/main_image_converter.py
============================================================
هذا السكريبت مخصص لتنظيم الصور بناءً على أوصافها النصية (Captions).
1. يقرأ المجموعات من clustring_imge.
2. يقرأ أوصاف الصور من ملفات image_to_text.py في Processing image.
3. يطبق TF-IDF على أوصاف الصور لاستنتاج اسم المجلد (بحد أقصى 3 كلمات).
4. يقوم بنسخ الصور إلى المجلدات الجديدة في مساراتها المشتركة.
"""

import os
import sys
import re
import shutil
import importlib.util
from typing import Dict, List, Tuple, Optional
from collections import Counter

# إعداد الترميز ليدعم العربية في الويندوز
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    print("[!] خطأ: مكتبة scikit-learn غير مثبتة. يرجى تثبيتها عبر: pip install scikit-learn")
    sys.exit(1)

# ── إعدادات المسارات ──
CURRENT_HOME = os.path.expanduser("~")
_USER_PATH_PATTERN = re.compile(r"^[A-Za-z]:\\Users\\[^\\]+", re.IGNORECASE)

def remap_path_to_current_user(original_path: str) -> str:
    """إصلاح مسارات المستخدم لتناسب الجهاز الحالي"""
    match = _USER_PATH_PATTERN.match(original_path)
    if match:
        remapped = CURRENT_HOME + original_path[match.end():]
        return remapped
    return original_path

# ──────────────────────────────────────────────────────────────────────
# الخطوة 1: تحميل أوصاف الصور (Captions)
# ──────────────────────────────────────────────────────────────────────

def load_all_captions() -> Dict[str, str]:
    """تحميل الأوصاف من ملفات *_image_to_text.py"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processing_dir = os.path.join(project_root, "Processing image")
    
    master_captions = {}
    
    if not os.path.isdir(processing_dir):
        print(f"[!] مجلد المعالجة غير موجود: {processing_dir}")
        return master_captions

    for filename in os.listdir(processing_dir):
        if filename.endswith("_image_to_text.py"):
            file_path = os.path.join(processing_dir, filename)
            module_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                # البحث عن أي قاموس ينتهي بـ _image_captions
                for attr in dir(mod):
                    if attr.endswith("_image_captions"):
                        captions_dict = getattr(mod, attr)
                        if isinstance(captions_dict, dict):
                            master_captions.update(captions_dict)
            except Exception as e:
                print(f"[!] تعذر تحميل أوصاف من {filename}: {e}")
                
    return master_captions

# ──────────────────────────────────────────────────────────────────────
# الخطوة 2: اكتشاف المجموعات
# ──────────────────────────────────────────────────────────────────────

def discover_image_clusters() -> Dict[str, List[str]]:
    """اكتشاف مجموعات الصور من clustring_imge"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cluster_dir = os.path.join(project_root, "clustring_imge")
    
    cluster_dict = {}
    
    if not os.path.isdir(cluster_dir):
        return cluster_dict

    for filename in os.listdir(cluster_dir):
        if filename.startswith("similar_") and filename.endswith(".py"):
            file_path = os.path.join(cluster_dir, filename)
            module_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                for attr in dir(mod):
                    if attr.startswith("_"):
                        continue
                    
                    value = getattr(mod, attr)
                    if isinstance(value, (list, set)):
                        paths = [remap_path_to_current_user(p) for p in value if isinstance(p, str)]
                        # التحقق من أن العناصر تبدو كمسارات ملفات
                        if paths and all(os.sep in p or "/" in p for p in paths):
                            existing = [p for p in paths if os.path.isfile(p)]
                            if existing:
                                cluster_dict[attr] = existing
            except Exception as e:
                print(f"[!] تعذر تحميل مجموعة من {filename}: {e}")
                
    return cluster_dict

# ──────────────────────────────────────────────────────────────────────
# الخطوة 3: تحليل الأوصاف (TF-IDF) بحد أقصى 3 كلمات
# ──────────────────────────────────────────────────────────────────────

def generate_name_from_captions(file_paths: List[str], master_captions: Dict[str, str], fallback_name: str) -> str:
    """استنتاج اسم المجلد بناءً على أوصاف الصور (لا يتجاوز 3 كلمات)"""
    captions = []
    for fp in file_paths:
        basename_no_ext = os.path.splitext(os.path.basename(fp))[0]
        if basename_no_ext in master_captions:
            captions.append(master_captions[basename_no_ext])
    
    if not captions:
        return fallback_name

    # التحقق من وجود لغة عربية لتعطيل الـ stop_words الإنجليزية
    has_arabic = any(re.search(r'[\u0600-\u06FF]', cap) for cap in captions)
    stop_words_opt = None if has_arabic else 'english'

    try:
        vectorizer = TfidfVectorizer(stop_words=stop_words_opt, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(captions)
        feature_names = vectorizer.get_feature_names_out()
        
        import numpy as np
        mean_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
        sorted_indices = mean_scores.argsort()[::-1]
        
        top_terms = []
        for idx in sorted_indices:
            term = feature_names[idx]
            if mean_scores[idx] <= 0: break
            
            # تجنب التكرار في العبارات المركبة
            words = term.split()
            if len(words) == 2:
                if words[0] in top_terms or words[1] in top_terms: continue
            
            top_terms.append(term)
            
            # إيقاف البحث إذا وصلنا لـ 3 كلمات أو أكثر
            current_words = " ".join(top_terms).split()
            if len(current_words) >= 2: 
                break
            
        if top_terms:
            raw_name = " ".join(top_terms)
            # قطع صارم لأول 3 كلمات فقط
            final_words = raw_name.split()[:3]
            return " ".join(final_words).title()
            
    except ValueError:
        # يتم تجاهل الخطأ واللجوء للطريقة البديلة (الكلمات الأكثر تكراراً)
        pass
    
    # Fallback to most common words in captions
    all_words = " ".join(captions).lower().split()
    stops = {'a', 'an', 'the', 'with', 'on', 'in', 'of', 'and', 'at', 'is'}
    filtered = [w for w in all_words if w not in stops and len(w) > 2]
    most_common = [w for w, c in Counter(filtered).most_common(3)]
    
    if most_common:
        # قطع صارم لأول 3 كلمات فقط
        return " ".join(most_common[:3]).title()
        
    return fallback_name

# ──────────────────────────────────────────────────────────────────────
# الخطوة 4: التنفيذ والنسخ
# ──────────────────────────────────────────────────────────────────────

def get_base_path(file_paths: List[str]) -> str:
    """إرجاع المسار المشترك لمجموعة الملفات"""
    try:
        dirs = [os.path.dirname(p) for p in file_paths]
        return os.path.commonpath(dirs)
    except ValueError:
        # في حال كانت الملفات على أقراص (Drives) مختلفة
        return os.path.dirname(file_paths[0])

def sanitize_name(name: str) -> str:
    """تنظيف اسم المجلد من الرموز الممنوعة"""
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    return cleaned.replace(" ", "_")[:50] or "image_group"

def main():
    print("      --- محول مجموعات الصور الذكي ---")
    
    # تحميل البيانات
    print("[*] جاري تحميل أوصاف الصور...")
    all_captions = load_all_captions()
    print(f"    تم تحميل {len(all_captions)} وصف.")
    
    print("[*] جاري البحث عن مجموعات الصور...")
    clusters = discover_image_clusters()
    print(f"    تم العثور على {len(clusters)} مجموعة.\n")
    
    if not clusters:
        print("[!] لم يتم العثور على عمل للقيام به.")
        return

    for group_name, file_paths in clusters.items():
        print(f"--- معالجة: {group_name} ({len(file_paths)} صورة) ---")
        
        # استنتاج الاسم
        suggested_name = generate_name_from_captions(file_paths, all_captions, group_name)
        folder_name = sanitize_name(suggested_name)
        print(f"    الاسم المستنتج: {folder_name}")
        
        # تحديد المسار (أخذ المسار المشترك)
        try:
            base_path = get_base_path(file_paths)
            target_dir = os.path.join(base_path, folder_name)
            
            # معالجة تكرار اسم المجلد
            counter = 1
            original_target = target_dir
            while os.path.exists(target_dir):
                target_dir = f"{original_target}_{counter}"
                counter += 1
                
            os.makedirs(target_dir, exist_ok=True)
            print(f"    المجلد الوجهة: {target_dir}")
            
            # النسخ
            success = 0
            for fp in file_paths:
                try:
                    dest = os.path.join(target_dir, os.path.basename(fp))
                    
                    # فحص إذا كان الملف موجود مسبقاً في الوجهة مع ترقيم ذكي
                    if os.path.exists(dest):
                        b, e = os.path.splitext(os.path.basename(fp))
                        file_counter = 1
                        while os.path.exists(dest):
                            dest = os.path.join(target_dir, f"{b}_copy_{file_counter}{e}")
                            file_counter += 1
                            
                    shutil.copy2(fp, dest)
                    success += 1
                except Exception as e:
                    print(f"    [!] فشل نسخ {os.path.basename(fp)}: {e}")
            
            print(f"    تم نسخ {success} من أصل {len(file_paths)} بنجاح.")
            
        except Exception as e:
            print(f"    [!] خطأ في معالجة المجموعة: {e}")
            
    # Cleanup: Delete the cluster files after successful processing
    print("\n[*] جاري تنظيف ملفات التجميع المؤقتة...")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cluster_dir = os.path.join(project_root, "clustring_imge")
    if os.path.isdir(cluster_dir):
        for filename in os.listdir(cluster_dir):
            if filename.startswith("similar_") and filename.endswith(".py"):
                try:
                    os.remove(os.path.join(cluster_dir, filename))
                    print(f"  [✓] تم حذف: {filename}")
                except Exception as e:
                    print(f"  [!] فشل حذف {filename}: {e}")

    print("\n--- تمت العملية بنجاح! ---")

if __name__ == "__main__":
    main()