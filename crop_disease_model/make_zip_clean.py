import os
import zipfile

def zip_folder_clean(src_dir, zip_path):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                # Skip temporary powerpoint lock files or python cache
                if file.startswith("~$") or file.endswith(".pyc") or "__pycache__" in root:
                    continue
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, src_dir)
                zf.write(abs_file, rel_file)
    print(f"[OK] Zipped '{src_dir}' cleanly to '{zip_path}'")

if __name__ == "__main__":
    src_folder = r"C:\Users\RAJ VIKRAM\Downloads\Stalk_the_Stock-main\Stalk_the_Stock-main\crop_disease_model"
    
    # Save in Downloads folder
    zip1 = r"C:\Users\RAJ VIKRAM\Downloads\crop_disease_model_project.zip"
    zip_folder_clean(src_folder, zip1)

    # Save in Artifacts folder
    zip2 = r"C:\Users\RAJ VIKRAM\.gemini\antigravity\brain\cc32deaa-b563-4b79-9827-007853c38031\crop_disease_model_project.zip"
    zip_folder_clean(src_folder, zip2)
