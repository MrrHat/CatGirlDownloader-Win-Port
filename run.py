import os
import sys
import importlib.util

def setup_environment():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        os.environ['PATH'] = base_path + os.pathsep + os.path.join(base_path, 'bin') + os.pathsep + os.environ.get('PATH', '')
        os.environ['GI_TYPELIB_PATH'] = os.path.join(base_path, 'lib', 'girepository-1.0')
        os.environ['GDK_PIXBUF_MODULE_FILE'] = os.path.join(base_path, 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')
        os.environ['XDG_DATA_DIRS'] = os.path.join(base_path, 'share') + os.pathsep + os.environ.get('XDG_DATA_DIRS', '')
        os.environ['GTK_EXE_PREFIX'] = base_path

    os.environ['GST_REGISTRY_UPDATE'] = 'yes'
    

    os.environ['GST_PLUGIN_FEATURE_RANK'] = 'd3d11h264dec:300;d3d11vp9dec:300;d3d11av1dec:300;avdec_h264:-1;vp9dec:-1'

def load_app_package():
    if getattr(sys, 'frozen', False):
        src_dir = os.path.join(sys._MEIPASS, 'src')
    else:
        src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
        
    init_file = os.path.join(src_dir, "__init__.py")
    spec = importlib.util.spec_from_file_location(
        "catgirldownloader",
        init_file,
        submodule_search_locations=[src_dir],
    )
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["catgirldownloader"] = pkg
    spec.loader.exec_module(pkg)
    return pkg

def main():
    setup_environment()
    
    try:
        import gi
    except ImportError:
        sys.exit("ERROR: PyGObject ('gi') is not installed.")
        
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")

    if not getattr(sys, 'frozen', False):
        import shutil
        import subprocess
        from gi.repository import Gio
        
        build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_runbuild")
        os.makedirs(build_dir, exist_ok=True)
        gresource_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "catgirldownloader.gresource.xml")
        out_path = os.path.join(build_dir, "catgirldownloader.gresource")
        compiler = shutil.which("glib-compile-resources")
        if compiler:
            subprocess.run([compiler, f"--sourcedir={os.path.dirname(gresource_xml)}", f"--target={out_path}", gresource_xml], check=True)
            resource = Gio.Resource.load(out_path)
            resource._register()

    load_app_package()
    from catgirldownloader import main as app_main
    sys.exit(app_main.main("0.5-windows"))

if __name__ == "__main__":
    main()
