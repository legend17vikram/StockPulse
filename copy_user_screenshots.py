import shutil
import os

src_dir = r"C:\Users\RAJ VIKRAM\Pictures\Screenshots"
dest_dir = r"c:\Users\RAJ VIKRAM\Downloads\Stalk_the_Stock-main\Stalk_the_Stock-main\images"

os.makedirs(dest_dir, exist_ok=True)

# Map user screenshots to the names the project uses
mappings = {
    "dash board.png": "dashboard.png",
    "login page.png": "loginPage.png",
    "searchBar.png": "searchBar.png",
    "searchPage.png": "searchPage.png"
}

print("Moving and renaming your screenshots...")
for src_name, dest_name in mappings.items():
    src_path = os.path.join(src_dir, src_name)
    dest_path = os.path.join(dest_dir, dest_name)
    if os.path.exists(src_path):
        try:
            shutil.copy(src_path, dest_path)
            print("SUCCESS: Copied " + src_name + " as " + dest_name)
        except Exception as e:
            print("FAILED: to copy " + src_name + ": " + str(e))
    else:
        print("WARNING: Screenshot '" + src_name + "' not found in " + src_dir)
