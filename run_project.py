import subprocess
import os
import sys
import time

def run_script(dir_name, script_name, description, custom_path=None):
    """Executes a specific script inside its directory"""
    script_path = os.path.join(dir_name, script_name)
    
    print(f"\n{'─'*50}")
    print(f"[*] Executing: {description}")
    print(f"{'─'*50}")
    
    if not os.path.exists(script_path):
        print(f"[!] Error: File not found at: {script_path}")
        return False
    
    try:
        # Prepare command
        command = [sys.executable, script_name]
        if custom_path:
            command.append(custom_path) # Pass custom path as argument
            print(f"[*] Targeting Custom Path: {custom_path}")

        process = subprocess.Popen(command, 
                                   cwd=dir_name,
                                   stdout=sys.stdout, 
                                   stderr=sys.stderr,
                                   text=True)
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

def process_text_collection(custom_path=None):
    print("\n>>> Collecting Text Data (Embedding & Clustering) <<<")
    steps = [
        ("Processing text files", "files_Embedder.py", "Text Embedding"),
        ("clustring_files", "clustring_file_text.py", "Text Clustering")
    ]
    for d, s, desc in steps:
        if not run_script(d, s, desc, custom_path):
            return False
    return True

def process_images_collection(custom_path=None):
    print("\n>>> Collecting Image Data (Captioning & Clustering) <<<")
    steps = [
        ("Processing image", "images_caption_Embedder.py", "Image Captioning"),
        ("clustring_imge", "clustring_image_captions.py", "Image Clustering")
    ]
    for d, s, desc in steps:
        if not run_script(d, s, desc, custom_path):
            return False
    return True

def select_paths():
    """Allows the user to select multiple target paths"""
    paths = {}
    print("\n[?] Select the paths you want to process:")
    if input("    - Include Desktop? (y/n): ").lower() == 'y':
        paths["desktop"] = os.path.join(os.path.expanduser('~'), 'Desktop')
    if input("    - Include Documents? (y/n): ").lower() == 'y':
        paths["documents"] = os.path.join(os.path.expanduser('~'), 'Documents')
    if input("    - Include Downloads? (y/n): ").lower() == 'y':
        paths["downloads"] = os.path.join(os.path.expanduser('~'), 'Downloads')
    
    if input("\n[?] Would you like to add a CUSTOM folder path manually? (y/n): ").lower() == 'y':
        custom = input("    Please enter the FULL path to the folder: ").strip()
        if os.path.isdir(custom):
            paths["custom_folder"] = custom
        else:
            print(f"    [!] Invalid path or directory not found: {custom}")
            
    return paths

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("╔══════════════════════════════════════════════════════════╗")
    print("║             KIRO AI AGENT - SMART LAUNCHER               ║")
    print("║                Project Management Core                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\n1. Full System Processing (Text & Images)")
    print("2. Text Files Only")
    print("3. Images Only")
    print("4. Exit")
    
    mode_choice = input("\nPlease select processing mode [1-4]: ")
    
    if mode_choice == '4':
        print("Goodbye!")
        return

    if mode_choice in ['1', '2', '3']:
        # Phase 2: Selection of Paths
        target_paths = select_paths()
        
        if not target_paths:
            print("\n[!] No valid paths selected. Returning to menu...")
            time.sleep(2)
            return main()
            
        # Phase 2: Execution
        start_time = time.time()
        
        # 2a. Embedding & Clustering (Collect data from all paths)
        for name, path in target_paths.items():
            print(f"\n{'='*50}")
            print(f"[*] Processing: {name.upper()} ({path})")
            print(f"{'='*50}")
            
            if mode_choice == '1': # Full System
                process_text_collection(path)
                process_images_collection(path)
            elif mode_choice == '2': # Text Only
                process_text_collection(path)
            elif mode_choice == '3': # Images Only
                process_images_collection(path)
        
        # 2b. Organization (Run once globally)
        print(f"\n{'='*50}")
        print(f"[*] FINAL STEP: Organizing Files into Folders")
        print(f"{'='*50}")
        if mode_choice in ['1', '2']:
            run_script("creat folders for flie_text  and name", "main_converter.py", "Final Text Organization")
        if mode_choice in ['1', '3']:
            run_script("creat folders for image and name", "main_image_converter.py", "Final Image Organization")

    print(f"\n{'-'*50}")
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds")
    print(f"{'-'*50}")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
