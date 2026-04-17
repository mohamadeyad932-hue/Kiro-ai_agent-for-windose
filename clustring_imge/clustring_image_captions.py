import os
import sys
import numpy as np
import importlib
from collections import defaultdict

# Force UTF-8 encoding for standard output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from sklearn.cluster import AgglomerativeClustering
except ImportError:
    print("Please ensure libraries are installed: pip install scikit-learn numpy")
    sys.exit(1)

# Path to processing directory
PROCESSING_DIR = r"c:\Users\eyad\Desktop\Kiro-ai_agent-for-windose\Processing image"
if PROCESSING_DIR not in sys.path:
    sys.path.append(PROCESSING_DIR)

def dynamic_import(name):
    """Safely import a module by name"""
    try:
        return importlib.import_module(name)
    except ImportError:
        return None

def save_cluster_scripts(folder_name, folder_sets):
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
    
    # Check for custom path argument
    custom_path = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else None
    
    if custom_path:
        print(f"[*] Custom image path clustering: {custom_path}")
        mod_files = dynamic_import("custom_folder_files")
        mod_vecs = dynamic_import("custom_folder_vectors")
        mod_caps = dynamic_import("custom_folder_image_to_text")
        
        if not mod_files or not mod_vecs:
            print("[!] Error: Could not find custom_folder_files or vectors.")
            return

        folders_data = [
            ("custom_folder", custom_path, getattr(mod_files, "custom_folder_image_file", {}), 
             getattr(mod_vecs, "custom_folder_image_vectors", {}), 
             getattr(mod_caps, "custom_folder_image_captions", {}))
        ]
    else:
        # Standard folders
        import desktop_files, desktop_vectors, desktop_image_to_text
        import documents_files, documents_vectors, documents_image_to_text
        import downloads_files, downloads_vectors, downloads_image_to_text
        
        folders_data = [
            ("desktop",   os.path.join(home, "Desktop"),   desktop_files.desktop_image_file,   desktop_vectors.desktop_image_vectors,   desktop_image_to_text.desktop_image_captions),
            ("documents", os.path.join(home, "Documents"), documents_files.documents_image_file, documents_vectors.documents_image_vectors, documents_image_to_text.documents_image_captions),
            ("downloads", os.path.join(home, "Downloads"), downloads_files.downloads_image_file, downloads_vectors.downloads_image_vectors, downloads_image_to_text.downloads_image_captions),
        ]

    print("=" * 60)
    print("Starting Image Clustering (BLIP + SBERT)...")
    print("=" * 60)

    for folder_name, folder_path, files_dict, vectors_dict, captions_dict in folders_data:
        if not files_dict or not vectors_dict:
            print(f"\n[{folder_name}] No images found. Skipping.")
            continue
            
        print(f"\n[{folder_name}] Analyzing {len(files_dict)} images...")
        
        valid_names = []
        valid_vectors = []
        for name in files_dict:
            if name in vectors_dict:
                valid_names.append(name)
                valid_vectors.append(vectors_dict[name])
                
        if not valid_names:
            print(f"  - No valid vectors.\n")
            continue
            
        num_images = len(valid_names)
        if num_images <= 1:
            clusters = [0]
        else:
            clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=4.0)
            clusters = clustering.fit_predict(np.array(valid_vectors))
            
        cluster_dict = defaultdict(list)
        for name, c_id in zip(valid_names, clusters):
            cluster_dict[c_id].append(name)
            
        group_counter = 1
        folder_clustered_sets = {}
        for c_id, names_list in cluster_dict.items():
            full_paths = []
            for name in names_list:
                ext = files_dict[name]
                full_paths.append(os.path.join(folder_path, name + ext))
                
            set_name = f"{folder_name}_image_group_{group_counter}"
            folder_clustered_sets[set_name] = set(full_paths)
            group_counter += 1
            
        save_cluster_scripts(folder_name, folder_clustered_sets)

    print("\n" + "=" * 60)
    print("Image Clustering Finished!")
    print("=" * 60)

if __name__ == "__main__":
    main()
