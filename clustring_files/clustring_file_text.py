import os
import sys
import numpy as np
import importlib
from collections import defaultdict

# Force UTF-8 encoding for standard output to avoid garbled Arabic in terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif sys.stdout.encoding != 'UTF-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except Exception:
        pass

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
except ImportError:
    print("Please ensure libraries are installed:\npip install scikit-learn numpy")
    sys.exit(1)

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    print("Please ensure scipy is installed:\npip install scipy")
    sys.exit(1)

# إضافة مسار مجلد المعالجة ليتمكن بايثون من استيراد القواميس منه
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
PROCESSING_DIR = os.path.join(BASE_DIR, "Processing text files")
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

def load_module_data(module_prefix):
    """دالة مساعدة لاستيراد القواميس والمتجهات ديناميكياً"""
    files_dict, vectors_dict = {}, {}
    try:
        # Import file list
        files_mod_name = f"{module_prefix}_files"
        if files_mod_name in sys.modules:
            importlib.reload(sys.modules[files_mod_name])
        files_mod = importlib.import_module(files_mod_name)
        files_dict = getattr(files_mod, f"{module_prefix}_file", {})
        
        # Import vectors
        vectors_mod_name = f"{module_prefix}_vectors"
        if vectors_mod_name in sys.modules:
            importlib.reload(sys.modules[vectors_mod_name])
        vectors_mod = importlib.import_module(vectors_mod_name)
        vectors_dict = getattr(vectors_mod, f"{module_prefix}_vectors", {})
        
    except ImportError as e:
        print(f"  [!] Could not load data for {module_prefix}: {e}")
    except Exception as e:
        print(f"  [!] Error loading {module_prefix}: {e}")
        
    return files_dict, vectors_dict

def auto_find_best_threshold(vectors):
    """
    يبني شجرة التجميع ويختار العتبة التي تعطي أعلى Silhouette Score.
    """
    print(f"  Searching for best threshold (Dendrogram + Silhouette)...")
    
    Z = linkage(vectors, method='average', metric='cosine')
    distances = Z[:, 2]
    
    min_dist, max_dist = distances.min(), distances.max()
    if min_dist == max_dist:
        return (min_dist + max_dist) / 2

    candidates = np.linspace(min_dist, max_dist, 100)
    
    best_thr = None
    best_sil = -1
    best_n = 0
    results = []
    
    for thr in candidates:
        predicted = fcluster(Z, t=thr, criterion='distance')
        n_clusters = np.unique(predicted).size
        
        if 2 <= n_clusters <= len(vectors) / 1.5:
            try:
                sil = silhouette_score(vectors, predicted, metric='cosine')
            except Exception:
                sil = -1.0
            
            results.append((thr, n_clusters, sil))
            if sil > best_sil:
                best_sil = sil
                best_thr = thr
                best_n = n_clusters
    
    if best_thr is None:
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
    
    return round(float(best_thr), 4)

def save_cluster_scripts(folder_name, folder_sets):
    script_name = f"similar_{folder_name}_files.py"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(output_dir, script_name)
    
    lines = ['"""', f"File groups: {folder_name}", '"""', ""]
    valid_groups = 0
    
    for group_name, paths_set in folder_sets.items():
        if len(paths_set) < 2:
            continue
        valid_groups += 1
        lines.append(f"{group_name} = {{")
        for path in paths_set:
            safe_path = path.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'    "{safe_path}",')
        lines.append("}\n")
        
    if valid_groups > 0:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"  [+] Saved script: {script_name} (Total valid groups: {valid_groups})")
    else:
        # Clear the file if no groups found to avoid using old results
        if os.path.exists(script_path):
            os.remove(script_path)
        print(f"  [-] No groups with 2 or more files found. Cleanup successful.")

def main():
    home = os.path.expanduser("~")
    
    # جلب البيانات بناءً على الأرجومنتات أو افتراضياً
    folders_data = []
    
    if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]):
        f_name = sys.argv[1]
        f_path = sys.argv[2]
        f_dict, v_dict = load_module_data(f_name)
        folders_data.append((f_name, f_path, f_dict, v_dict))
    else:
        for f_name, f_path_suffix in [("desktop", "Desktop"), ("documents", "Documents"), ("downloads", "Downloads")]:
            f_path = os.path.join(home, f_path_suffix)
            f_dict, v_dict = load_module_data(f_name)
            folders_data.append((f_name, f_path, f_dict, v_dict))

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
        
        for name in files_dict.keys():
            if name in vectors_dict:
                valid_names.append(name)
                valid_vectors.append(vectors_dict[name])

        if not valid_names:
            print(f"  - No valid files for clustering.\n")
            continue

        num_files = len(valid_names)
        folder_clustered_sets = {}
        
        if num_files <= 1:
            clusters = [0]
        else:
            vectors_array = np.array(valid_vectors)
            
            # PCA dimensionality reduction
            n_pca = min(384, num_files, vectors_array.shape[1])
            print(f"  PCA dimensionality reduction ({vectors_array.shape[1]} -> {n_pca})...")
            pca = PCA(n_components=n_pca, random_state=42)
            optimized_vectors = pca.fit_transform(vectors_array)
            
            # Normalize for Cosine distance after PCA
            norms = np.linalg.norm(optimized_vectors, axis=1, keepdims=True)
            optimized_vectors = np.divide(optimized_vectors, norms, out=np.zeros_like(optimized_vectors), where=norms!=0)
            
            # Find best threshold
            best_threshold = auto_find_best_threshold(optimized_vectors)
            
            # Clustering
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

        for group_counter, (c_id, names_list) in enumerate(cluster_dict.items(), start=1):
            full_paths = []
            for name in names_list:
                ext = files_dict[name]
                full_path = os.path.join(folder_path, name + ext)
                full_paths.append(full_path)
            
            set_name = f"{folder_name}_group_{group_counter}"
            folder_clustered_sets[set_name] = set(full_paths)

        print(f"  - Generated {len(cluster_dict)} total clusters.")
        save_cluster_scripts(folder_name, folder_clustered_sets)

    print("\n" + "=" * 60)
    print("Process completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()