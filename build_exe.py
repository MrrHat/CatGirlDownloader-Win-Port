import os
import shutil
import subprocess
import sys

MSYS2_MINGW64 = r"C:\msys64\mingw64"
INNO_SETUP = r"C:\Program Files\Inno Setup 7\ISCC.exe"

def copy_tree(src, dst):
    if not os.path.exists(src): return
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copy_tree(s, d)
        else:
            shutil.copy2(s, d)

def main():
    print("=== 1/4 Запуск PyInstaller ===")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "CatgirlDownloader",
        "--icon", "icon.ico",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--hidden-import=gi",
        "--hidden-import=requests",
        "--collect-all", "gi",
        "--add-data", "src;src",
        "--add-data", "data;data",
        "run.py"
    ]
    subprocess.run(cmd, check=True)

    dist_dir = os.path.join("dist", "CatgirlDownloader")
    internal_dir = os.path.join(dist_dir, "_internal")
    
    if not os.path.exists(internal_dir):
        os.makedirs(internal_dir, exist_ok=True)

    dirs_to_copy = [
        (os.path.join(MSYS2_MINGW64, "lib", "girepository-1.0"), os.path.join(internal_dir, "lib", "girepository-1.0")),
        (os.path.join(MSYS2_MINGW64, "lib", "gdk-pixbuf-2.0"), os.path.join(internal_dir, "lib", "gdk-pixbuf-2.0")),
        (os.path.join(MSYS2_MINGW64, "lib", "gstreamer-1.0"), os.path.join(internal_dir, "lib", "gstreamer-1.0")),
        (os.path.join(MSYS2_MINGW64, "share", "icons"), os.path.join(internal_dir, "share", "icons")),
        (os.path.join(MSYS2_MINGW64, "share", "glib-2.0"), os.path.join(internal_dir, "share", "glib-2.0")),
    ]
    
    for src, dst in dirs_to_copy:
        copy_tree(src, dst)

    bin_dir = os.path.join(MSYS2_MINGW64, "bin")
    for file in os.listdir(bin_dir):
        if file.endswith(".dll"):
            shutil.copy2(os.path.join(bin_dir, file), os.path.join(internal_dir, file))

    d3d_path_sys = r"C:\Windows\System32\d3dcompiler_47.dll"
    if os.path.exists(d3d_path_sys):
        shutil.copy2(d3d_path_sys, os.path.join(internal_dir, "d3dcompiler_47.dll"))


    if os.path.exists(INNO_SETUP):
        subprocess.run([INNO_SETUP, "installer.iss"], check=True)


if __name__ == "__main__":
    main()
