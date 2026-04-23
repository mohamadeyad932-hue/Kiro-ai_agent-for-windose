import os
import sys
import numpy as np
import importlib
from collections import defaultdict

# Force UTF-8 encoding for standard output to avoid garbled Arabic in terminal
sys.stdout.reconfigure(encoding='utf-8')

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
except ImportError:
    print("Please ensure libraries are installed:")
    print("pip install scikit-learn numpy")
    sys.exit(1)

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    print("pip install scipy")
    sys.exit(1)

# إضافة مسار مجلد text_file_prossing ليتمكن بايثون من استيراد القواميس منه
PROCESSING_DIR = r"c:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\Processing text files"
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

# Import dictionaries and BERT vectors (768 dimensions)
try:
    from desktop_files import desktop_file # type: ignore
    from desktop_vectors import desktop_vectors # type: ignore
except ImportError:
    desktop_file = {}; desktop_vectors = {}

try:
    from documents_files import documents_file # type: ignore
    from documents_vectors import documents_vectors # type: ignore
except ImportError:
    documents_file = {}; documents_vectors = {}

try:
    from downloads_files import downloads_file # type: ignore
    from downloads_vectors import downloads_vectors # type: ignore
except ImportError:
    downloads_file = {}; downloads_vectors = {}


# كشف العتبة تلقائيا عبر Dendrogram + Silhouette (بدون بيانات حقيقية)

def auto_find_best_threshold(vectors):
    """
    يبني شجرة التجميع (Dendrogram) مرة واحدة ثم يجرب 100 عتبة
    ويختار العتبة التي تعطي أعلى Silhouette Score.
    
    ملاحظة مهمة: هذه الوظيفة لا تحتاج بيانات حقيقية (ground truth)
    لأنها تستخدم Silhouette Score الذي يقيّم جودة التجميع ذاتياً.
    """
    print(f"  Searching for best threshold (Dendrogram + Silhouette)...")
    
    # بناء الشجرة الهرمية بمسافة Cosine وطريقة الربط Average (الأفضل للنصوص)
    Z = linkage(vectors, method='average', metric='cosine')
    distances = Z[:, 2]  # مسافات الدمج
    
    min_dist = distances.min()
    max_dist = distances.max()
    
    # إنشاء 100 نقطة (عتبة) محتملة بين أقل وأكبر مسافة دمج
    candidates = np.linspace(min_dist, max_dist, 100)
    
    best_thr = None
    best_sil = -1
    best_n   = 0
    results  = []
    
    for thr in candidates:
        predicted = fcluster(Z, t=thr, criterion='distance')
        n_clusters = len(set(predicted))
        
        # استبعاد التجميعات غير المنطقية
        if 2 <= n_clusters <= len(vectors) / 1.5:
            try:
                sil = silhouette_score(vectors, predicted, metric='cosine')
            except:
                sil = -1.0
            
            results.append((thr, n_clusters, sil))
            
            if sil > best_sil:
                best_sil = sil
                best_thr = thr
                best_n   = n_clusters
    
    if best_thr is None:
        # fallback: إذا فشلت كل العتبات، نستخدم النقطة الوسطى
        best_thr = (min_dist + max_dist) / 2
        print(f"  No optimal threshold found, using midpoint: {best_thr:.4f}")
    else:
        print(f"  Best threshold found: {best_thr:.4f} (clusters: {best_n}, Silhouette: {best_sil:.3f})")
    
    # طباعة أفضل 5 نتائج
    results.sort(key=lambda x: x[2], reverse=True)
    if results:
        print(f"  {'-'*55}")
        print(f"  {'Threshold':>10} | {'Clusters':>9} | {'Silhouette':>10}")
        print(f"  {'-'*55}")
        for i, (thr, n, sil) in enumerate(results[:5]):
            marker = " *" if i == 0 else ""
            print(f"  {thr:>8.4f} | {n:>9d} | {sil:>10.3f}{marker}")
        print(f"  {'-'*55}")
    
    return round(best_thr, 4)


def save_cluster_scripts(folder_name, folder_sets):
    script_name = f"similar_{folder_name}_files.py"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(output_dir, script_name)
    
    lines = ['"""', f"File groups: {folder_name}", '"""', ""]
    for group_name, paths_set in folder_sets.items():
        if len(paths_set) < 2:
            continue
        lines.append(f"{group_name} = {{")
        for path in paths_set:
            safe_path = path.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'    "{safe_path}",')
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
    print("Starting clustering using BERT embeddings...")
    print("Techniques: PCA + Cosine Distance + Auto Threshold")
    print("=" * 60)

    for folder_name, folder_path, files_dict, vectors_dict in folders_data:
        if not files_dict or not vectors_dict:
            print(f"\n[{folder_name}] No embeddings found. Skipping.")
            continue

        print(f"\n[{folder_name}] Analyzing embeddings and clustering files...")
        valid_names = []
        valid_vectors = []
        
        for name, ext in files_dict.items():
            if name in vectors_dict:
                valid_names.append(name)
                valid_vectors.append(vectors_dict[name])

        if not valid_names:
            print(f"  - Dictionaries are empty.\n")
            continue

        num_files = len(valid_names)
        folder_clustered_sets = {}
        
        if num_files <= 1:
            clusters = [0]
        else:
            vectors_array = np.array(valid_vectors)
            
            # خفض الابعاد PCA - تنظيف الفيكتورات من الضوضاء
            n_pca = min(386, num_files, vectors_array.shape[1])
            print(f"  PCA dimensionality reduction ({vectors_array.shape[1]} -> {n_pca})...")
            pca = PCA(n_components=n_pca, random_state=42)
            optimized_vectors = pca.fit_transform(vectors_array)
            
            # كشف العتبة تلقائيا
            best_threshold = auto_find_best_threshold(optimized_vectors)
            
            # التجميع بمسافة Cosine
            print(f"  Clustering with optimal threshold: {best_threshold}...")
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=best_threshold,
                metric='cosine',
                linkage='average'
            )
            clusters = clustering.fit_predict(optimized_vectors)

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

        print(f"  - Created {len(cluster_dict)} groups (Sets).")
        save_cluster_scripts(folder_name, folder_clustered_sets)

    print("\n" + "=" * 60)
    print("Process completed successfully!")
    print("=" * 60)
        

if __name__ == "__main__":
    main()    