import os
import sys
import numpy as np
from collections import defaultdict

# Force UTF-8 encoding for standard output to avoid garbled Arabic in terminal
sys.stdout.reconfigure(encoding='utf-8')

try:
    from sklearn.cluster import AgglomerativeClustering
except ImportError:
    print("Please ensure libraries are installed:")
    print("pip install scikit-learn numpy")
    sys.exit(1)

# إضافة مسار مجلد text_file_prossing ليتمكن بايثون من استيراد القواميس منه
PROCESSING_DIR = r"c:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\text_file_prossing"
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

# Import dictionaries and BERT vectors (768 dimensions)
try:
    from desktop_files import desktop_file
    from desktop_vectors import desktop_vectors
except ImportError:
    desktop_file = {}; desktop_vectors = {}

try:
    from documents_files import documents_file
    from documents_vectors import documents_vectors
except ImportError:
    documents_file = {}; documents_vectors = {}

try:
    from downloads_files import downloads_file
    from downloads_vectors import downloads_vectors
except ImportError:
    downloads_file = {}; downloads_vectors = {}


def save_cluster_scripts(folder_name, folder_sets):
    """
    دالة لحفظ المجموعات في سكريبتات بأسماء ومتغيرات باللغة الإنجليزية حصراً.
    """
    script_name = f"similar_{folder_name}_files.py"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(output_dir, script_name)
    
    lines = [
        f'"""',
        f'Similar files grouped into sets for: {folder_name}',
        f'Automatically generated based on BERT embeddings clustering',
        f'"""',
        ''
    ]
    
    for set_name, files_set in folder_sets.items():
        lines.append(f"# Set contains {len(files_set)} highly similar files")
        lines.append(f"{set_name} = {{")
        for f in files_set:
            lines.append(f'    r"{f}",')
        lines.append("}\n")
        
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    print(f"  [+] Saved script: {script_name}")


def main():
    home = os.path.expanduser("~")
    
    # folder_name (English), folder_path, files_dict, vectors_dict
    folders_data = [
        ("desktop", os.path.join(home, "Desktop"), desktop_file, desktop_vectors),
        ("documents", os.path.join(home, "Documents"), documents_file, documents_vectors),
        ("downloads", os.path.join(home, "Downloads"), downloads_file, downloads_vectors)
    ]

    print("=" * 60)
    print("بدء عملية التجميع (بدقة عالية) بالاعتماد على بصمات BERT...")
    print("=" * 60)

    for folder_name, folder_path, files_dict, vectors_dict in folders_data:
        if not files_dict or not vectors_dict:
            print(f"\n[{folder_name}] لم يتم العثور على بصمات. تم التخطي.")
            continue
            
        print(f"\n[{folder_name}] جاري تحليل البصمات وتجميع الملفات...")
        
        valid_names = []
        valid_vectors = []
        
        for name, ext in files_dict.items():
            if name in vectors_dict:
                valid_names.append(name)
                valid_vectors.append(vectors_dict[name])
                
        if not valid_names:
            print(f"  - القواميس فارغة.\n")
            continue
            
        num_files = len(valid_names)
        folder_clustered_sets = {}
        
        if num_files <= 1:
            clusters = [0]
        else:
            # هنا تم تقليل distance_threshold إلى 0.15 لزيادة الدقة بشكل كبير جداً
            # (الملفات يجب أن تكون متطابقة جداً للولوج لنفس المجموعة)
            clustering = AgglomerativeClustering(
                n_clusters=None, 
                metric='cosine', 
                distance_threshold=0.40,
                linkage='average'
            )
            clusters = clustering.fit_predict(np.array(valid_vectors))
            
        cluster_dict = defaultdict(list)
        for name, c_id in zip(valid_names, clusters):
            cluster_dict[c_id].append(name)
            
        # إنشاء أسماء المتغيرات بالإنجليزية: foldername_group_1, foldername_group_2 وهكذا
        group_counter = 1
        for c_id, names_list in cluster_dict.items():
            full_paths = []
            for name in names_list:
                ext = files_dict[name]
                full_path = os.path.join(folder_path, name + ext)
                full_paths.append(full_path)
                
            set_name = f"{folder_name}_group_{group_counter}"
            folder_clustered_sets[set_name] = set(full_paths)
            group_counter += 1
            
        print(f"  - تم إنشاء {len(cluster_dict)} مجموعة (Sets) بأسماء إنجليزية.")
        
        save_cluster_scripts(folder_name, folder_clustered_sets)

    print("\n" + "=" * 60)
    print("تم إتمام العملية بنجاح!")
    print("=" * 60)
        
if __name__ == "__main__":
    main()