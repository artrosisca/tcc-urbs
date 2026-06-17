import os
import shutil

def main():
    print("Starting python reorganization script...")
    root_dir = "c:\\GIT\\tcc-urbs"
    data_dir = os.path.join(root_dir, "data")
    
    # 1. Create data directory if not exists
    if not os.path.exists(data_dir):
        print("Creating data/ directory...")
        os.makedirs(data_dir)
        
    # 2. Move folders if they exist in root
    folders_to_move = ["dados_c3sl", "dados_em_tempo_real_2026", "dados_processados"]
    for folder in folders_to_move:
        src = os.path.join(root_dir, folder)
        dst = os.path.join(data_dir, folder)
        if os.path.exists(src):
            print(f"Moving {folder} to data/{folder}...")
            # If destination already exists, delete it first to avoid nested/merge issues
            if os.path.exists(dst):
                print(f"Destination {dst} already exists, removing it first.")
                shutil.rmtree(dst)
            shutil.move(src, dst)
        else:
            print(f"Source {folder} does not exist in root, skipping.")
            
    # 3. Remove old download_c3sl.py from root
    old_script = os.path.join(root_dir, "download_c3sl.py")
    if os.path.exists(old_script):
        print("Removing old download_c3sl.py from root...")
        os.remove(old_script)
        
    print("Reorganization script finished successfully.")

if __name__ == "__main__":
    main()
