import threading
import requests
import os
import sys
import random
import time
import tempfile
from gi.repository import Gtk, Adw, GdkPixbuf, GLib, Gio, GObject, Gdk

from .catgirl import CatgirlDownloaderAPI
from .waifu import WaifuDownloaderAPI
from .danbooru import DanbooruDownloaderAPI
from .preferences import UserPreferences
from .gallery import GalleryWindow, HistoryManager
from .preferenceswindow import PreferencesWindow

def load_media_bytes(url, callback, error_callback=None, is_video=False):
    def _load():
        try:
            headers = {'User-Agent': 'CatgirlDownloader/0.5 (Windows)'}
            response = requests.get(url, stream=True, timeout=15, headers=headers)
            response.raise_for_status()
            
            if is_video:
                import time
                temp_dir = tempfile.gettempdir()
                ext = "mp4" if ".mp4" in url else "webm"
                # УНИКАЛЬНОЕ ИМЯ ФАЙЛА, чтобы не блокировать старый
                filepath = os.path.join(temp_dir, f"cat_{int(time.time() * 1000)}.{ext}")
                
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                GLib.idle_add(callback, filepath, True)
            else:
                response = requests.get(url, timeout=10, headers=headers)
                response.raise_for_status()
                GLib.idle_add(callback, response.content, False)
        except Exception as e:
            if error_callback: GLib.idle_add(error_callback, e)
    threading.Thread(target=_load, daemon=True).start()

class SourceItem(GObject.Object):
    __gtype_name__ = 'SourceItem'
    def __init__(self, id, name, description, api, icon=None):
        super().__init__()
        self.id = id; self.name = name; self.description = description; self.api = api; self.icon = icon

if getattr(sys, 'frozen', False):
    UI_FILE = os.path.join(sys._MEIPASS, 'data', 'ui', 'window.ui')
else:
    UI_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'ui', 'window.ui')

@Gtk.Template.from_file(UI_FILE)
class CatgirldownloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'CatgirldownloaderWindow'

    refresh_button = Gtk.Template.Child("refresh_button")
    spinner = Gtk.Template.Child("spinner")
    image = Gtk.Template.Child("image")
    video_player = Gtk.Template.Child("video_player")
    save_button = Gtk.Template.Child("savebutton")
    auto_reload_switch = Gtk.Template.Child("auto_reload_switch")
    source_selector = Gtk.Template.Child("source_selector")
    tags_box = Gtk.Template.Child("tags_box")
    tags_entry = Gtk.Template.Child("tags_entry")
    anti_tags_entry = Gtk.Template.Child("anti_tags_entry")
    apply_tags_button = Gtk.Template.Child("apply_tags_button")
    favorite_button = Gtk.Template.Child("favorite_button")
    gallery_button = Gtk.Template.Child("gallery_button")
    copy_url_button = Gtk.Template.Child("copy_url_button")
    copy_image_button = Gtk.Template.Child("copy_image_button")
    open_source_button = Gtk.Template.Child("open_source_button")
    toast_overlay = Gtk.Template.Child("toast_overlay")
    settings_button = Gtk.Template.Child("settings_button")
    slideshow_button = Gtk.Template.Child("slideshow_button")
    info_revealer = Gtk.Template.Child("info_revealer")
    info_label = Gtk.Template.Child("info_label")
    similar_button = Gtk.Template.Child("similar_button")
    surprise_button = Gtk.Template.Child("surprise_button")

    AVAILABLE_SOURCES = {
        "catgirl": {"name": "Catgirl", "description": "nekos.moe", "class": CatgirlDownloaderAPI, "icon": None},
        "waifu": {"name": "Waifu", "description": "waifu.im", "class": WaifuDownloaderAPI, "icon": None},
        "danbooru": {"name": "Danbooru", "description": "danbooru.donmai.us", "class": DanbooruDownloaderAPI, "icon": None}
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = UserPreferences()
        self.history = HistoryManager()
        self._gallery_window = None
        self.downloaders = {}
        self.source_store = Gio.ListStore(item_type=SourceItem)
        self._zoom_level = 1.0
        self._slideshow_id = None
        self._temp_video_file = None
        
        saved_source = self.settings.get_preference("source")
        default_index = 0

        for i, (key, value) in enumerate(self.AVAILABLE_SOURCES.items()):
            api = value["class"](settings=self.settings)
            self.downloaders[key] = api
            item = SourceItem(key, value["name"], value.get("description", ""), api, value.get("icon"))
            self.source_store.append(item)
            if key == saved_source: default_index = i
        
        self.source_selector.set_model(self.source_store)
        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect("setup", self.setup_source_item)
        list_factory.connect("bind", self.bind_source_item)
        self.source_selector.set_list_factory(list_factory)
        
        button_factory = Gtk.SignalListItemFactory()
        button_factory.connect("setup", self.setup_source_button_item)
        button_factory.connect("bind", self.bind_source_button_item)
        self.source_selector.set_factory(button_factory)
        
        self.source_selector.set_selected(default_index)
        self.source_selector.connect("notify::selected-item", self.on_source_changed)

        self.info = None
        self.image_bytes = None
        self.current_url = None
        self._is_loading = False

        self.auto_reload_switch.connect("notify::active", self.on_auto_reload_toggle)
        self.refresh_button.connect("clicked", self.async_reloadimage)
        self.save_button.connect("clicked", self.file_chooser_dialog)
        self.favorite_button.connect("clicked", self.on_favorite_clicked)
        self.gallery_button.connect("clicked", self.on_gallery_clicked)
        self.copy_url_button.connect("clicked", self.on_copy_url_clicked)
        self.copy_image_button.connect("clicked", self.on_copy_image_clicked)
        self.open_source_button.connect("clicked", self.on_open_source_clicked)
        self.apply_tags_button.connect("clicked", self.on_apply_tags_clicked)
        self.settings_button.connect("clicked", self.on_settings_clicked)
        self.slideshow_button.connect("toggled", self.on_slideshow_toggle)
        self.similar_button.connect("clicked", self.on_find_similar)
        self.surprise_button.connect("clicked", self.on_surprise_clicked)
        
        self.tag_store = Gtk.ListStore(str)
        completion = Gtk.EntryCompletion()
        completion.set_model(self.tag_store)
        completion.set_text_column(0)
        completion.connect("match-selected", self.on_tag_match)
        self.tags_entry.set_completion(completion)
        self.tags_entry.connect("changed", self.on_tags_changed)

        scroll_controller = Gtk.EventControllerScroll()
        scroll_controller.set_flags(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll_controller.connect("scroll", self.on_image_scroll)
        self.image.add_controller(scroll_controller)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        click_controller = Gtk.GestureClick()
        click_controller.set_button(1)
        click_controller.connect("pressed", self.on_image_click)
        self.image.add_controller(click_controller)

        self._update_tags_visibility()
        self.async_reloadimage()

    def setup_source_button_item(self, factory, list_item):
        list_item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_source_button_item(self, factory, list_item):
        list_item.get_child().set_label(list_item.get_item().name)

    def setup_source_item(self, factory, list_item):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_valign(Gtk.Align.CENTER); vbox.set_hexpand(True)
        title_label = Gtk.Label(halign=Gtk.Align.START); title_label.add_css_class("heading")
        vbox.append(title_label)
        desc_label = Gtk.Label(halign=Gtk.Align.START); desc_label.add_css_class("caption"); desc_label.set_wrap(True)
        vbox.append(desc_label)
        box.append(vbox)
        list_item.set_child(box)

    def bind_source_item(self, factory, list_item):
        vbox = list_item.get_child().get_first_child()
        vbox.get_first_child().set_label(list_item.get_item().name)
        vbox.get_first_child().get_next_sibling().set_label(list_item.get_item().description)

    def show_toast(self, message):
        self.toast_overlay.add_toast(Adw.Toast.new(message))

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_space: self.async_reloadimage(); return True
        if keyval == Gdk.KEY_s: self.file_chooser_dialog(None); return True
        if keyval == Gdk.KEY_f: self.on_favorite_clicked(None); return True
        if keyval == Gdk.KEY_g: self.on_gallery_clicked(None); return True
        if keyval == Gdk.KEY_Escape: self.info_revealer.set_reveal_child(False); return True
        return False

    def on_image_scroll(self, controller, dx, dy):
        if not (controller.get_current_event_state() & Gdk.ModifierType.CONTROL_MASK): return False
        self._zoom_level -= dy * 0.1
        self._zoom_level = max(1.0, min(self._zoom_level, 5.0))
        texture = self.image.get_paintable()
        if texture:
            w = texture.get_width(); h = texture.get_height()
            self.image.set_size_request(int(w * self._zoom_level), int(h * self._zoom_level))
            self.image.set_can_shrink(self._zoom_level == 1.0)
        return True

    def on_image_click(self, ctrl, n_press, x, y):
        if n_press == 2:
            is_revealed = self.info_revealer.get_reveal_child()
            if not is_revealed and self.info:
                item = self.source_selector.get_selected_item()
                artist = item.api.get_artist(self.info) if item else "Unknown"
                
                tags_str = "No tags"
                if item and item.id == "danbooru":
                    tags_str = self.info.get("tag_string", "No tags")
                elif item and item.id == "waifu":
                    tags_list = self.info.get("images", [{}])[0].get("tags", [])
                    tags_str = " ".join(tags_list)
                
                self.info_label.set_markup(f"<b>Artist:</b> {artist or 'Unknown'}\n<b>Tags:</b> {tags_str[:200]}...")
            self.info_revealer.set_reveal_child(not is_revealed)

    def on_find_similar(self, _):
        if self.info:
            item = self.source_selector.get_selected_item()
            tags_str = ""
            
            if item and item.id == "danbooru":
                tags_str = self.info.get("tag_string", "")
            elif item and item.id == "waifu":
                tags_list = self.info.get("images", [{}])[0].get("tags", [])
                tags_str = " ".join(tags_list)
                
            tags = tags_str.split()
            if tags:
                self.tags_entry.set_text(" ".join(tags[:3]))
                self.on_apply_tags_clicked()
                self.info_revealer.set_reveal_child(False)
                self.show_toast("Searching for similar...")

    def on_slideshow_toggle(self, btn):
        if btn.get_active():
            self._slideshow_id = GLib.timeout_add_seconds(5, self._slideshow_tick)
            btn.set_icon_name("media-playback-pause-symbolic")
        else:
            if self._slideshow_id: GLib.source_remove(self._slideshow_id)
            btn.set_icon_name("media-playback-start-symbolic")

    def _slideshow_tick(self):
        self.async_reloadimage()
        return True

    def _fetch_tags(self, prefix):
        self._tag_timeout_id = None
        item = self.source_selector.get_selected_item()
        if item and item.id == "danbooru":
            threading.Thread(target=self.fetch_tags, args=(prefix,), daemon=True).start()
        return False

    def on_tags_changed(self, entry):
        # Удаляем старый таймер, если пользователь печатает быстро
        if hasattr(self, "_tag_timeout_id") and self._tag_timeout_id is not None:
            GLib.source_remove(self._tag_timeout_id)
            
        text = entry.get_text()
        parts = text.split(" ")
        last_word = parts[-1] if parts else ""
        
        if len(last_word) > 2:
            # Ждем 300 мс перед отправкой запроса
            self._tag_timeout_id = GLib.timeout_add(300, self._fetch_tags, last_word)

    def fetch_tags(self, prefix):
        tags = self.downloaders["danbooru"].get_tag_suggestions(prefix)
        GLib.idle_add(self.update_tag_store, tags)

    def update_tag_store(self, tags):
        self.tag_store.clear()
        for tag, count in tags:
            self.tag_store.append([f"{tag} ({count} arts)"])

    def on_tag_match(self, completion, model, iter):
        selected = model.get_value(iter, 0)
        tag = selected.split(" ")[0]
        text = self.tags_entry.get_text()
        parts = text.split(" ")
        parts[-1] = tag
        self.tags_entry.set_text(" ".join(parts) + " ")
        self.tags_entry.set_position(-1)
        return True

    def on_surprise_clicked(self, _):
        cool_tags = [
            "cat_ears", "maid", "thighhighs", "kemonomimi_mode", "horns", 
            "wings", "school_uniform", "gothic_lolita", "swimsuit", 
            "looking_at_viewer", "twintails", "cyberpunk", "ponytail",
            "heterochromia", "kimono", "alternate_costume"
        ]
        random_tag = random.choice(cool_tags)
        
        item = self.source_selector.get_selected_item()
        if item and getattr(item.api, "supports_tags", False):
            self.tags_entry.set_text(random_tag)
            self.anti_tags_entry.set_text("")
            self.on_apply_tags_clicked()
            self.show_toast(f"Surprise! Searching: {random_tag}")
        else:
            self.async_reloadimage()
            self.show_toast("Surprise!")

    def on_source_changed(self, dropdown, _pspec):
        item = dropdown.get_selected_item()
        if item:
            self.settings.set_preference("source", item.id)
            self._update_tags_visibility()
            self.async_reloadimage()

    def _update_tags_visibility(self):
        item = self.source_selector.get_selected_item()
        if not item: return
        self.tags_box.set_visible(getattr(item.api, "supports_tags", False))
        if self.tags_box.get_visible():
            self.tags_entry.set_text(getattr(item.api, "get_tags", lambda: "")() or "")
            self.anti_tags_entry.set_text(getattr(item.api, "get_anti_tags", lambda: "")() or "")

    def on_apply_tags_clicked(self, _=None):
        item = self.source_selector.get_selected_item()
        if item and getattr(item.api, "supports_tags", False):
            item.api.set_tags(self.tags_entry.get_text().strip())
            item.api.set_anti_tags(self.anti_tags_entry.get_text().strip())
            self.async_reloadimage()

    def on_settings_clicked(self, _): PreferencesWindow(self).present()
    
    def on_auto_reload_toggle(self, switch, _):
        if switch.get_active() and not self._is_loading: self.async_reloadimage()

    def async_reloadimage(self, _=None):
        if self._is_loading:
            self.show_toast("Already loading, please wait...")
            return
        
        # ПРАВИЛЬНО СБРАСЫВАЕМ ВИДЕО
        try:
            # Очищаем поток
            self.video_player.set_file(None)
            self.video_player.set_visible(False)
        except:
            pass
            
        self._is_loading = True
        self.spinner.set_visible(True)
        self.spinner.start()
        item = self.source_selector.get_selected_item()
        t = threading.Thread(target=self._fetch_url_thread, args=[item.id if item else None], daemon=True)
        t.start()

    def _fetch_url_thread(self, source_id=None):
        try:
            ct = self.downloaders.get(source_id)
            nsfw = self.settings.get_preference("nsfw_mode")
            url = ct.get_image_url(nsfw)
            self.current_url = url
            self.info = getattr(ct, "info", None)
            
            if url:
                is_video = ".mp4" in url or ".webm" in url
                load_media_bytes(url, self._on_image_loaded, self._on_image_error, is_video)
            else:
                GLib.idle_add(self._on_image_error, Exception("No URL"))
        except Exception as e:
            GLib.idle_add(self._on_image_error, e)

    def _on_image_loaded(self, data, is_video):
        try:
            self.spinner.stop()
            self.spinner.set_visible(False)
            self._is_loading = False

            if is_video:
                self.image_bytes = None
                self.image.set_visible(False)
                self.video_player.set_visible(True)
                
                # БЕЗОПАСНОЕ УДАЛЕНИЕ СТАРОГО ВИДЕО
                old_file = getattr(self, '_temp_video_file', None)
                if old_file and os.path.exists(old_file):
                    try:
                        os.remove(old_file) # Удаляем старый файл, когда он уже не нужен
                    except:
                        pass # Если Windows все еще держит файл, просто игнорируем
                        
                self._temp_video_file = data
                
                from gi.repository import Gio
                g_file = Gio.File.new_for_path(self._temp_video_file)
                self.video_player.set_file(g_file)
                
                # ТРЮК ДЛЯ GTK4: Принудительно запускаем и сразу ставим на паузу.
                # Это заставляет GStreamer отрисовать первый кадр (пропадает черный экран).
                self.video_player.play()
                GLib.timeout_add(100, self._force_pause_video)
            else:
                self.image_bytes = data
                self.video_player.set_visible(False)
                self.video_player.set_file(None)
                self._temp_video_file = None
                
                # Оптимизация картинок для процессора (сжатие до 1080p)
                loader = GdkPixbuf.PixbufLoader()
                loader.write(data)
                loader.close()
                pixbuf = loader.get_pixbuf()
                
                max_w, max_h = 1920, 1080
                w, h = pixbuf.get_width(), pixbuf.get_height()
                if w > max_w or h > max_h:
                    scale = min(max_w / w, max_h / h)
                    pixbuf = pixbuf.scale_simple(int(w * scale), int(h * scale), GdkPixbuf.InterpType.BILINEAR)
                
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.image.set_paintable(texture)
                self.image.set_visible(True)
                self._zoom_level = 1.0
                self.image.set_size_request(-1, -1)
                self.image.set_can_shrink(True)
                
            item = self.source_selector.get_selected_item()
            artist = item.api.get_artist(self.info) if item else "Unknown"
            self.history.add_item(self.current_url, item.id, artist, data if not is_video else b"")
        except Exception as e:
            print(f"Error displaying media: {e}")

    def _force_pause_video(self):
        try:
            self.video_player.pause()
        except:
            pass
        return False

    def _on_image_error(self, error):
        self.show_toast("Failed to load media")
        self.spinner.stop()
        self.spinner.set_visible(False)
        self._is_loading = False

    def _finish_loading(self):
        self.spinner.stop(); self.spinner.set_visible(False); self._is_loading = False

    def on_favorite_clicked(self, _):
        if self.current_url and self.image_bytes:
            item = self.source_selector.get_selected_item()
            artist = item.api.get_artist(self.info) if item else "Unknown"
            self.history.add_favorite(self.current_url, item.id, artist, self.image_bytes)
            self.show_toast("Added to favorites (In-Memory)")

    def on_gallery_clicked(self, _):
        if self._gallery_window is None:
            self._gallery_window = GalleryWindow(self)
            self._gallery_window.connect("destroy", lambda w: setattr(self, '_gallery_window', None))
        self._gallery_window.present()

    def on_copy_url_clicked(self, _):
        if self.current_url:
            Gdk.Display.get_default().get_clipboard().set(self.current_url)
            self.show_toast("URL copied")

    def on_copy_image_clicked(self, _):
        texture = self.image.get_paintable()
        if texture:
            clipboard = Gdk.Display.get_default().get_clipboard()
            clipboard.set_content(Gdk.ContentProvider.new_for_texture(texture))
            self.show_toast("Image copied to clipboard")

    def on_open_source_clicked(self, _):
        item = self.source_selector.get_selected_item()
        if item and self.info:
            link = item.api.get_link(self.info)
            if link: import webbrowser; webbrowser.open(link)

    def file_chooser_dialog(self, _):
        if not self.image_bytes and not self._temp_video_file: return
        
        quick_folder = self.settings.get_preference("quick_save_folder")
        if quick_folder and os.path.exists(quick_folder):
            item = self.source_selector.get_selected_item()
            artist = item.api.get_artist(self.info) if item else "unknown"
            
            if self._temp_video_file:
                ext = "mp4" if ".mp4" in self.current_url else "webm"
                with open(self._temp_video_file, "rb") as f_in:
                    with open(os.path.join(quick_folder, f"{item.id}_{artist or 'unknown'}.{ext}".replace(" ", "_")), "wb") as f_out:
                        f_out.write(f_in.read())
            else:
                ext = "jpg"
                filename = f"{item.id}_{artist or 'unknown'}.{ext}".replace(" ", "_")
                path = os.path.join(quick_folder, filename)
                with open(path, "wb") as f: f.write(self.image_bytes)
            self.show_toast(f"Saved to {quick_folder}")
            return

        dialog = Gtk.FileChooserDialog(title="Save file", parent=self, action=Gtk.FileChooserAction.SAVE)
        ext = "mp4" if (self.current_url and ".mp4" in self.current_url) else "jpg"
        dialog.set_current_name(f"image.{ext}")
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Save', Gtk.ResponseType.OK)
        dialog.connect('response', self._on_save_response)
        dialog.show()

    def _on_save_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            path = dialog.get_file().get_path()
            if self._temp_video_file:
                with open(self._temp_video_file, "rb") as f_in:
                    with open(path, "wb") as f_out: f_out.write(f_in.read())
            elif self.image_bytes:
                with open(path, "wb") as f: f.write(self.image_bytes)
            self.show_toast("Saved")
        dialog.destroy()