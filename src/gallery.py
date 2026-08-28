from gi.repository import Gtk, Adw, Gdk, GLib, GObject

class HistoryItem(GObject.Object):
    def __init__(self, url, source, artist, image_bytes):
        super().__init__()
        self.url = url
        self.source = source
        self.artist = artist or "Unknown"
        self.image_bytes = image_bytes
        self._texture = None

    def get_texture(self):
        if self._texture is None and self.image_bytes:
            try:
                g_bytes = GLib.Bytes.new(self.image_bytes)
                self._texture = Gdk.Texture.new_from_bytes(g_bytes)
            except Exception as e:
                print(e)
        return self._texture

class HistoryManager:
    def __init__(self):
        self.items = []
        self.favorites = []

    def add_item(self, url, source, artist, image_bytes):
        if any(i.url == url for i in self.items): return
        item = HistoryItem(url, source, artist, image_bytes)
        self.items.insert(0, item)
        
        if len(self.items) > 10:
            removed_item = self.items.pop()
            removed_item.image_bytes = None 
            removed_item._texture = None

    def add_favorite(self, url, source, artist, image_bytes):
        if any(i.url == url for i in self.favorites): return
        item = HistoryItem(url, source, artist, image_bytes)
        self.favorites.insert(0, item)
        
        if len(self.favorites) > 10:
            removed_item = self.favorites.pop()
            removed_item.image_bytes = None
            removed_item._texture = None

class GalleryWindow(Adw.Window):
    def __init__(self, parent_window):
        super().__init__(title="Gallery", transient_for=parent_window, default_width=800, default_height=600)
        self.parent_window = parent_window
        
        self.connect("close-request", lambda w: w.destroy())
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(box)
        header = Adw.HeaderBar()
        box.append(header)
        
        self.stack = Gtk.Stack()
        header.set_title_widget(Gtk.StackSwitcher(stack=self.stack))
        box.append(self.stack)

        self.flow_all = Gtk.FlowBox(valign=Gtk.Align.START, max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE, homogeneous=True)
        self.stack.add_titled(Gtk.ScrolledWindow(vexpand=True, child=self.flow_all), "all", "History")

        self.flow_fav = Gtk.FlowBox(valign=Gtk.Align.START, max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE, homogeneous=True)
        self.stack.add_titled(Gtk.ScrolledWindow(vexpand=True, child=self.flow_fav), "fav", "Favorites")
        
        self._populate()

    def _populate(self):
        for flow in [self.flow_all, self.flow_fav]:
            while child := flow.get_first_child():
                flow.remove(child)
        for item in self.parent_window.history.items:
            self._add_item(item, self.flow_all)
        for item in self.parent_window.history.favorites:
            self._add_item(item, self.flow_fav)

    def _add_item(self, item, flow):
        texture = item.get_texture()
        if not texture: return
        
        btn = Gtk.Button(has_frame=False, tooltip_text=f"{item.source} - {item.artist}")
        img = Gtk.Image.new_from_paintable(texture)
        img.set_pixel_size(150) 
        img.set_halign(Gtk.Align.CENTER)
        img.set_valign(Gtk.Align.CENTER)
        btn.set_child(img)
        
        btn.connect("clicked", lambda b, i=item: self._show_full(i))
        flow.append(btn)

    def _show_full(self, item):
        win = Adw.Window(title="Image Viewer", transient_for=self, modal=True, default_width=700, default_height=700)
        win.connect("close-request", lambda w: w.destroy())
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        win.set_content(box)
        
        header = Adw.HeaderBar()
        box.append(header)
        
        texture = item.get_texture()
        if texture:
            pic = Gtk.Picture.new_for_paintable(texture)
            pic.set_content_fit(Gtk.ContentFit.CONTAIN)
            pic.set_vexpand(True)
            box.append(pic)
            
        bar = Gtk.ActionBar()
        box.append(bar)
        
        save_btn = Gtk.Button(icon_name="folder-download-symbolic", label="Save")
        save_btn.connect("clicked", lambda b: self._save_item(item))
        bar.pack_start(save_btn)
        
        copy_btn = Gtk.Button(icon_name="edit-copy-symbolic", label="Copy URL")
        copy_btn.connect("clicked", lambda b: Gdk.Display.get_default().get_clipboard().set(item.url))
        bar.pack_start(copy_btn)
        
        win.present()

    def _save_item(self, item):
        dialog = Gtk.FileChooserDialog(title="Save image", transient_for=self, action=Gtk.FileChooserAction.SAVE)
        dialog.set_current_name(f"{item.source}_{item.artist}.jpg")
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)
        def on_resp(d, r):
            if r == Gtk.ResponseType.OK and item.image_bytes:
                with open(d.get_file().get_path(), "wb") as f:
                    f.write(item.image_bytes)
            d.destroy()
        dialog.connect("response", on_resp)
        dialog.show()
