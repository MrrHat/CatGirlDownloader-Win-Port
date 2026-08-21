# Running / building Catgirl Downloader on Windows

## Why this isn't a "rewrite"

The app's actual code (`src/*.py`) has **no Linux-only dependencies**:

- UI: pure GTK4 + libadwaita via PyGObject (`Gtk.Template` + `.ui` files)
- Settings: a plain JSON file in `GLib.get_user_config_dir()` (which on
  Windows resolves to `%LOCALAPPDATA%`) — **not** GSettings/dconf
- Networking: `requests`
- File saving: `Gtk.FileChooserDialog`, which is a real native-ish dialog
  on Windows too

The only Linux-specific parts of the repo are the *packaging* files
(`meson.build`, the `.desktop`/`.appdata.xml` files, the `nfpm.yaml`
`.deb`/`.rpm` packaging, the nekos.moe icon install into
`/usr/share/icons`). None of that is needed to run the app — it's only
needed to install it the "Linux distro" way, and we replace it with the
`run.py` launcher included in this repo.

So porting to Windows is really "get GTK4 + libadwaita + PyGObject
working on Windows", which is a solved problem via **MSYS2**.

## Option A — Run it (recommended, works today)

1. Install [MSYS2](https://www.msys2.org/) and follow its first-run
   `pacman -Syu` update steps.
2. Open the **"MSYS2 MinGW64"** shell specifically (not the plain MSYS2
   shell — that one gives you POSIX-emulated binaries, not native
   Windows ones).
3. Install the toolchain and libraries:

   ```bash
   pacman -S \
     mingw-w64-x86_64-python \
     mingw-w64-x86_64-python-gobject \
     mingw-w64-x86_64-python-requests \
     mingw-w64-x86_64-gtk4 \
     mingw-w64-x86_64-libadwaita \
     mingw-w64-x86_64-gobject-introspection \
     mingw-w64-x86_64-glib2 \
     git
   ```

4. Get the source and run it:

   ```bash
   git clone https://github.com/NyarchLinux/CatgirlDownloader.git
   cd CatgirlDownloader
   # copy/add run.py + WINDOWS.md from this port if you cloned upstream directly
   python run.py
   ```

That's it — this launches the real app, same window, same features
(source picker, NSFW filter, auto-reload, save dialog), using native
Windows GTK4 widgets. You can also launch it from a regular `cmd.exe`/
PowerShell afterwards, as long as `C:\msys64\mingw64\bin` is on `PATH`
(that's where the GTK4/glib DLLs and `python.exe` from step 3 live).

## Option B — Package it as a standalone .exe

This is the harder part, because it means bundling the GTK4/libadwaita
DLLs, GDK-Pixbuf loaders (needed to decode the PNG/JPG the API returns),
icon theme, and typelibs into a folder a user can double-click without
installing MSYS2. There's no fully automatic tool for this the way
PyInstaller alone handles a plain Tk or Qt app, because PyInstaller's
dependency scanner doesn't understand GI typelibs or GTK's runtime
module loading.

The practical path (used by real GTK4 Windows ports like Rnote, Newsflash,
Workbench):

1. Do everything in Option A first, from the **MinGW64** shell (this
   matters — the DLLs must all come from the same MSYS2 environment).
2. Install PyInstaller into that same environment:
   ```bash
   pacman -S mingw-w64-x86_64-python-pip
   pip install pyinstaller
   ```
3. Run PyInstaller against `run.py`, then **manually copy** into the
   output `dist/` folder:
   - `C:\msys64\mingw64\bin\*.dll` (or better, use `ldd`/`objdump -p` on
     the built `.exe` and your `.pyd`s to find the actual DLL closure —
     copying the whole `bin` folder works but is heavy, ~200 MB)
   - `C:\msys64\mingw64\lib\gdk-pixbuf-2.0` (image format loaders — without
     this, images will fail to decode)
   - `C:\msys64\mingw64\lib\girepository-1.0` (typelibs: `Gtk-4.0`,
     `Adw-1`, `Gio-2.0`, `GLib-2.0`, `GObject-2.0`, `Gdk-4.0`,
     `GdkPixbuf-2.0`, `cairo-1.0`, `Pango*`, `HarfBuzz*`)
   - `C:\msys64\mingw64\share\glib-2.0\schemas` (only needed if you later
     re-introduce GSettings; this fork doesn't use it)
   - `C:\msys64\mingw64\share\icons\Adwaita` (symbolic icons used by the
     UI, e.g. `emblem-system-symbolic`)
   - this repo's `data/icons/` for the app icon
4. Set environment variables before launching the packaged exe (or set
   them in a small launcher `.bat`/via `os.environ` at the very top of
   `run.py` before `import gi`):
   ```
   GI_TYPELIB_PATH=<dist>\girepository-1.0
   GSETTINGS_SCHEMA_DIR=<dist>\schemas   (optional, unused here)
   ```

Given the size and fragility of this (~150–250 MB, and easy to break on
a Windows update), **Option A is what I'd actually recommend** unless
you specifically need a single-file installer for non-technical users.
If that's the goal, say so and I can build out a proper PyInstaller spec
file and an Inno Setup installer script instead of hand-waving the DLL
list above.

## What I changed vs. upstream

- Added `run.py` — a launcher that compiles the `.gresource` bundle on
  the fly and imports `src/` as the `catgirldownloader` package, so you
  never need `meson install`. Nothing in `src/*.py` was modified.
- Added this file.

No application code was touched, since none of it was actually
Linux-specific.
