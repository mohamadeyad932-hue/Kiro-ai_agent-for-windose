"""
clustring_image_captions.py
يقوم بتجميع الصور المتشابهة بناءً على بصمات أوصافها النصية (SBERT vectors)
باستخدام خوارزمية Agglomerative Clustering.
يتبع نفس نمط clustring/clustring_file_text.py
"""

import os
import sys
import numpy as np
from collections import defaultdict

# Force UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

try:
    from sklearn.cluster import AgglomerativeClustering
except ImportError:
    print("Please ensure libraries are installed:")
    print("pip install scikit-learn numpy")
    sys.exit(1)

# إضافة مسار مجلد imag_plip_p ليتمكن بايثون من استيراد القواميس منه
PROCESSING_DIR = r"c:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\Processing image"
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

# ─── استيراد قواميس الصور والبصمات ───

try:
    from desktop_files import desktop_image_file # type: ignore
    from desktop_vectors import desktop_image_vectors # type: ignore
    from desktop_image_to_text import desktop_image_captions # type: ignore
except ImportError:
    desktop_image_file = {}; desktop_image_vectors = {}; desktop_image_captions = {}

try:
    from documents_files import documents_image_file # type: ignore
    from documents_vectors import documents_image_vectors # type: ignore
    from documents_image_to_text import documents_image_captions # type: ignore
except ImportError:
    documents_image_file = {}; documents_image_vectors = {}; documents_image_captions = {}

try:
    from downloads_files import downloads_image_file # type: ignore
    from downloads_vectors import downloads_image_vectors # type: ignore
    from downloads_image_to_text import downloads_image_captions # type: ignore
except ImportError:
    downloads_image_file = {}; downloads_image_vectors = {}; downloads_image_captions = {}


def save_cluster_scripts(folder_name, folder_sets):
    """
    حفظ مجموعات الصور المتشابهة في سكربت بايثون.
    """
    script_name = f"similar_{folder_name}_images.py"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(output_dir, script_name)

    lines = [
        f'"""',
        f'Similar images grouped into sets for: {folder_name}',
        f'Automatically generated based on BLIP captions + SBERT embeddings clustering',
        f'"""',
        ''
    ]

    for set_name, files_set in folder_sets.items():
        lines.append(f"# Set contains {len(files_set)} similar images")
        lines.append(f"{set_name} = {{")
        for f in files_set:
            lines.append(f'    r"{f}",')
        lines.append("}\n")

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  [+] Saved script: {script_name}")


def main():
    home = os.path.expanduser("~")

    # folder_name, folder_path, files_dict, vectors_dict, captions_dict
    folders_data = [
        ("desktop",   os.path.join(home, "Desktop"),   desktop_image_file,   desktop_image_vectors,   desktop_image_captions),
        ("documents", os.path.join(home, "Documents"), documents_image_file, documents_image_vectors, documents_image_captions),
        ("downloads", os.path.join(home, "Downloads"), downloads_image_file, downloads_image_vectors, downloads_image_captions),
    ]

    print("=" * 60)
    print("بدء عملية تجميع الصور المتشابهة (BLIP + SBERT Clustering)...")
    print("=" * 60)

    for folder_name, folder_path, files_dict, vectors_dict, captions_dict in folders_data:
        if not files_dict or not vectors_dict:
            print(f"\n[{folder_name}] لم يتم العثور على بصمات صور. تم التخطي.")
            continue

        print(f"\n[{folder_name}] جاري تحليل بصمات الصور وتجميعها...")

        valid_names = []
        valid_vectors = []

        for name, ext in files_dict.items():
            if name in vectors_dict:
                valid_names.append(name)
                valid_vectors.append(vectors_dict[name])

        if not valid_names:
            print(f"  - القواميس فارغة.\n")
            continue

        num_images = len(valid_names)
        folder_clustered_sets = {}

        if num_images <= 1:
            clusters = [0]
        else:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=4#العتبة المستخدمة في تجميع النصوص
            )
            clusters = clustering.fit_predict(np.array(valid_vectors))

        cluster_dict = defaultdict(list)
        for name, c_id in zip(valid_names, clusters):
            cluster_dict[c_id].append(name)

        # إنشاء أسماء المتغيرات: foldername_image_group_1, foldername_image_group_2 ...
        group_counter = 1
        for c_id, names_list in cluster_dict.items():
            full_paths = []
            for name in names_list:
                ext = files_dict[name]
                full_path = os.path.join(folder_path, name + ext)
                full_paths.append(full_path)

            set_name = f"{folder_name}_image_group_{group_counter}"
            folder_clustered_sets[set_name] = set(full_paths)
            group_counter += 1

        # عرض المجموعات مع الأوصاف
        print(f"  - تم انشاء {len(cluster_dict)} مجموعة:")
        for set_name, paths in folder_clustered_sets.items():
            print(f"    {set_name}: {len(paths)} صورة")
            for p in paths:
                img_name = os.path.splitext(os.path.basename(p))[0]
                caption = captions_dict.get(img_name, "بدون وصف")
                print(f"      -> {img_name}: \"{caption}\"")

        save_cluster_scripts(folder_name, folder_clustered_sets)

    print("\n" + "=" * 60)
    print("تم اتمام عملية التجميع بنجاح!")
    print("=" * 60)


if __name__ == "__main__":
    main()
