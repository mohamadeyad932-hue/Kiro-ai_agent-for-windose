import subprocess
import os
import sys
import time
import argparse

# Force UTF-8 encoding safely
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif sys.stdout.encoding != 'UTF-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except:
        pass


def run_script(dir_name, script_name, description, folder_name=None, folder_path=None):
    """Executes a specific script inside its directory"""
    script_path = os.path.join(dir_name, script_name)
    
    print(f"\n{'-'*50}")
    print(f"[*] Executing: {description}")
    print(f"{'-'*50}")
    
    if not os.path.exists(script_path):
        print(f"[!] Error: File not found at: {script_path}")
        return False
    
    try:
        # Prepare command
        command = [sys.executable, "-u", script_name]
        if folder_name:
            command.append(folder_name)
        if folder_path:
            command.append(folder_path)
            print(f"[*] Targeting Folder: {folder_name} ({folder_path})")

        process = subprocess.Popen(command, 
                                   cwd=dir_name,
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.STDOUT,
                                   text=True,
                                   encoding='utf-8',
                                   errors='replace')
        
        # Read output line by line and print it to our stdout
        if process.stdout:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n[✓] Task Completed Successfully.")
            return True
        else:
            print(f"\n[✗] Execution Failed (Code: {process.returncode})")
            return False
    except Exception as e:
        print(f"\n[!] Unexpected Error: {e}")
        return False

def process_text_collection(folder_name, folder_path):
    print("\n>>> Collecting Text Data (Embedding & Clustering) <<<")
    steps = [
        ("Processing text files", "files_Embedder.py", "Text Embedding"),
        ("clustring_files", "clustring_file_text.py", "Text Clustering")
    ]
    for d, s, desc in steps:
        if not run_script(d, s, desc, folder_name, folder_path):
            return False
    return True

def process_images_collection(folder_name, folder_path):
    print("\n>>> Collecting Image Data (Captioning & Clustering) <<<")
    steps = [
        ("Processing image", "images_caption_Embedder.py", "Image Captioning"),
        ("clustring_imge", "clustring_image_captions.py", "Image Clustering")
    ]
    for d, s, desc in steps:
        if not run_script(d, s, desc, folder_name, folder_path):
            return False
    return True

def select_paths():
    """Allows the user to select multiple target paths"""
    paths = {}
    print("\n[?] Select the paths you want to process:")
    if input("    - Include Desktop? (y/n): ").strip().lower() == 'y':
        paths["desktop"] = os.path.join(os.path.expanduser('~'), 'Desktop')
    if input("    - Include Documents? (y/n): ").strip().lower() == 'y':
        paths["documents"] = os.path.join(os.path.expanduser('~'), 'Documents')
    if input("    - Include Downloads? (y/n): ").strip().lower() == 'y':
        paths["downloads"] = os.path.join(os.path.expanduser('~'), 'Downloads')
    
    if input("\n[?] Would you like to add a CUSTOM folder path manually? (y/n): ").strip().lower() == 'y':
        custom = input("    Please enter the FULL path to the folder: ").strip()
        if os.path.isdir(custom):
            paths["custom_folder"] = custom
        else:
            print(f"    [!] Invalid path or directory not found: {custom}")
            
    return paths

def execute_pipeline(mode_choice, target_paths):
    """Executes the processing pipeline for the given mode and paths"""
    start_time = time.time()
    
    # Embedding & Clustering (Collect data from all paths)
    for name, path in target_paths.items():
        print(f"\n{'='*50}")
        print(f"[*] Processing: {name.upper()} ({path})")
        print(f"{'='*50}")
        
        if mode_choice == '1': # Full System
            process_text_collection(name, path)
            process_images_collection(name, path)
        elif mode_choice == '2': # Text Only
            process_text_collection(name, path)
        elif mode_choice == '3': # Images Only
            process_images_collection(name, path)
    
    # Organization (Run once globally)
    print(f"\n{'='*50}")
    print(f"[*] FINAL STEP: Organizing Files into Folders")
    print(f"{'='*50}")
    if mode_choice in ['1', '2']:
        run_script("creat folders for flie_text  and name", "semantic_folder_creator.py", "Final Text Organization")
    if mode_choice in ['1', '3']:
        run_script("creat folders for image and name", "main_image_converter.py", "Final Image Organization")

    elapsed = time.time() - start_time
    print(f"\n{'-'*50}")
    print(f"Total time elapsed: {elapsed:.2f} seconds")
    print(f"{'-'*50}")

    # حفظ الوقت الكلي في ملف النتائج ليظهر بدقة في الداشبورد
    import json
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "created_folders.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["total_processing_time"] = elapsed
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

def interactive_mode():
    """Runs the interactive terminal menu"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("============================================================")
        print("             KIRO AI AGENT - SMART LAUNCHER               ")
        print("                Project Management Core                   ")
        print("============================================================")
        print("\n1. Full System Processing (Text & Images)")
        print("2. Text Files Only")
        print("3. Images Only")
        print("4. Exit")
        
        mode_choice = input("\nPlease select processing mode [1-4]: ").strip()
        
        if mode_choice == '4':
            print("\nGoodbye!")
            break
        
        if mode_choice not in ['1', '2', '3']:
            print("\n[!] Invalid choice. Please select 1, 2, 3, or 4.")
            time.sleep(2)
            continue

        # Selection of Paths
        target_paths = select_paths()
        
        if not target_paths:
            print("\n[!] No valid paths selected. Returning to menu...")
            time.sleep(2)
            continue
        
        # Execute
        execute_pipeline(mode_choice, target_paths)
        
        input("\nPress Enter to return to menu...")

def cli_mode(args):
    """Runs in non-interactive CLI mode using command-line arguments"""
    target_paths = {}
    
    # Collect paths from flags
    if args.desktop:
        target_paths["desktop"] = os.path.join(os.path.expanduser('~'), 'Desktop')
    if args.documents:
        target_paths["documents"] = os.path.join(os.path.expanduser('~'), 'Documents')
    if args.downloads:
        target_paths["downloads"] = os.path.join(os.path.expanduser('~'), 'Downloads')
    if args.path:
        for i, p in enumerate(args.path):
            if os.path.isdir(p):
                target_paths[f"custom_{i+1}"] = p
            else:
                print(f"[!] Invalid path skipped: {p}")

    if not target_paths:
        print("[!] Error: No valid paths specified.")
        print("    Use --desktop, --documents, --downloads, or --path <folder>")
        sys.exit(1)

    mode_map = {'all': '1', 'text': '2', 'images': '3'}
    mode_choice = mode_map[args.mode]
    
    print(f"\n[*] Mode: {args.mode.upper()}")
    print(f"[*] Paths: {', '.join(target_paths.values())}")
    
    execute_pipeline(mode_choice, target_paths)

def main():
    parser = argparse.ArgumentParser(
        description="KIRO AI AGENT - Smart File Organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_project.py                              # Interactive mode
  python run_project.py --mode text --desktop        # Process text on Desktop
  python run_project.py --mode all --downloads       # Full processing on Downloads
  python run_project.py --mode images --path "C:\\MyFolder"  # Images in custom folder
        """
    )
    parser.add_argument('--mode', choices=['all', 'text', 'images'],
                        help='Processing mode: all, text, or images')
    parser.add_argument('--desktop', action='store_true',
                        help='Include Desktop folder')
    parser.add_argument('--documents', action='store_true',
                        help='Include Documents folder')
    parser.add_argument('--downloads', action='store_true',
                        help='Include Downloads folder')
    parser.add_argument('--path', action='append', metavar='FOLDER',
                        help='Custom folder path (can be used multiple times)')
    
    args = parser.parse_args()
    
    # If --mode is provided, run in CLI mode; otherwise interactive
    if args.mode:
        cli_mode(args)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
