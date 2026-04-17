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

def process_text(custom_path=None):
    print("\n>>> Starting Text Processing Pipeline <<<")
    steps = [
        ("Processing text files", "files_Embedder.py", "Text Embedding"),
        ("clustring_files", "clustring_file_text.py", "Text Clustering"),
        ("creat folders for flie_text  and name", "main_converter.py", "Text Organization")
    ]
    for d, s, desc in steps:
        if not run_script(d, s, desc, custom_path):
            return False
    return True

def process_images(custom_path=None):
    print("\n>>> Starting Image Processing Pipeline <<<")
    steps = [
        ("Processing image", "images_caption_Embedder.py", "Image Captioning"),
        ("clustring_imge", "clustring_image_captions.py", "Image Clustering"),
        ("creat folders for image and name", "main_image_converter.py", "Image Organization")
    ]
    for d, s, desc in steps:
        if not run_script(d, s, desc, custom_path):
            return False
    return True

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("╔══════════════════════════════════════════════════════════╗")
    print("║             KIRO AI AGENT - SMART LAUNCHER               ║")
    print("║                Project Management Core                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\nPlease select the processing mode:")
    print("1. Full System (Standard Folders)")
    print("2. Text Only (Standard Folders)")
    print("3. Image Only (Standard Folders)")
    print("4. Custom Path Processing (Enter your own path)")
    print("5. Exit")
    
    choice = input("\nEnter your choice [1-5]: ")
    
    custom_path = None
    if choice == '4':
        custom_path = input("\n[?] Please enter the FULL path to the folder: ").strip()
        if not os.path.isdir(custom_path):
            print(f"[!] Error: '{custom_path}' is not a valid directory.")
            input("\nPress Enter to return...")
            return main()
        
        # Ask what to process in this custom folder
        print("\nWhat do you want to process in this path?")
        print("A. Everything (Text & Images)")
        print("B. Text Files Only")
        print("C. Images Only")
        sub_choice = input("Select [A, B, C]: ").upper()
        
        start_time = time.time()
        if sub_choice == 'A':
            process_text(custom_path)
            process_images(custom_path)
        elif sub_choice == 'B':
            process_text(custom_path)
        elif sub_choice == 'C':
            process_images(custom_path)
        else:
            print("[!] Invalid Sub-choice.")
            return

    elif choice == '1':
        start_time = time.time()
        process_text()
        process_images()
    elif choice == '2':
        start_time = time.time()
        process_text()
    elif choice == '3':
        start_time = time.time()
        process_images()
    elif choice == '5':
        return
    else:
        print("[!] Invalid selection.")
        return

    print(f"\n{'-'*50}")
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds")
    print(f"{'-'*50}")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
