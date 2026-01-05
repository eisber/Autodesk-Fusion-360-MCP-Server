import os
import shutil

userdir = os.path.expanduser("~")
addin_path = os.path.join(
    userdir, "AppData", "Roaming", "Autodesk", "Autodesk Fusion 360", "API", "AddIns"
)

# Get the MCP folder relative to this script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
source_folder = os.path.join(script_dir, "MCP")

print(f"Source folder: {source_folder}")
print(f"Add-ins directory: {addin_path}")

if not os.path.exists(source_folder):
    raise FileNotFoundError(
        f"Source folder not found: {source_folder}\nMake sure you run this script from the repository root."
    )

name = os.path.basename(source_folder)
destination_folder = os.path.join(addin_path, name)

# Remove existing installation (whether it's a copy or symlink)
if os.path.islink(destination_folder):
    print(f"Removing existing symlink: {destination_folder}")
    os.unlink(destination_folder)
elif os.path.exists(destination_folder):
    print(f"Removing existing folder: {destination_folder}")
    shutil.rmtree(destination_folder)

# Create symbolic link so changes to source are immediately reflected
# This requires admin privileges on Windows
print(f"Creating symbolic link: {destination_folder} -> {source_folder}")

try:
    os.symlink(source_folder, destination_folder, target_is_directory=True)
    print("✅ Add-in installed successfully (symlink created)")
    print("   Changes to the source will be reflected immediately in Fusion 360.")
    print("   Just restart Fusion 360 to see updates.")
except OSError as e:
    if "privilege" in str(e).lower() or e.winerror == 1314:
        print("\n⚠️  Symlink creation requires administrator privileges on Windows.")
        print("   Falling back to copy mode...")
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        print("✅ Add-in installed (copied)")
        print("   Note: Re-run Install_Addin.py after making changes to update.")
        print("\n   To enable symlink mode (recommended), either:")
        print("   1. Run this script as Administrator, OR")
        print(
            "   2. Enable Developer Mode in Windows Settings > Privacy & Security > For developers"
        )
    else:
        raise
