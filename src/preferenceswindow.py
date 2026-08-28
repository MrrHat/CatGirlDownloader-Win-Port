import os
from gi.repository import Gtk, Adw, Gio
from .preferences import UserPreferences

class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, parent_window):
        super().__init__(title="Settings", transient_for=parent_window, modal=True, default_width=450)
        self.parent = parent_window
        self.settings = parent_window.settings
        
        # Флаг: были ли изменения?
        self._changed = False
        
        item = parent_window.source_selector.get_selected_item()
        self.source_id = item.id if item else "danbooru"
        self.tags_key = f"{self.source_id}_tags"
        self.anti_tags_key = f"{self.source_id}_anti_tags"
        
        page = Adw.PreferencesPage()
        self.add(page)
        
        # 1. Папка быстрого сохранения
        group_save = Adw.PreferencesGroup(title="Quick Save")
        page.add(group_save)
        row_save = Adw.ActionRow(title="Folder", subtitle="If set, pressing 'S' saves instantly here")
        self.btn_choose_folder = Gtk.Button(label="Choose...")
        self.btn_choose_folder.set_valign(Gtk.Align.CENTER)
        self.btn_choose_folder.connect("clicked", self.on_choose_folder)
        row_save.add_suffix(self.btn_choose_folder)
        self.lbl_folder = Gtk.Label(label="Not set", ellipsize="end", max_width_chars=20)
        self.lbl_folder.set_valign(Gtk.Align.CENTER)
        row_save.add_suffix(self.lbl_folder)
        group_save.add(row_save)
        current_folder = self.settings.get_preference("quick_save_folder")
        if current_folder: self.lbl_folder.set_label(os.path.basename(current_folder))

        # 2. Настройки контента (NSFW и Медиа)
        group_nsfw = Adw.PreferencesGroup(title="Content Filter")
        page.add(group_nsfw)
        
        row_nsfw = Adw.ActionRow(title="NSFW Mode", subtitle="Select content type")
        string_list = Gtk.StringList()
        string_list.append("Block NSFW (Safe)")
        string_list.append("Show Everything")
        string_list.append("Only NSFW (Explicit)")
        self.dropdown_nsfw = Gtk.DropDown(model=string_list)
        current_nsfw = self.settings.get_preference("nsfw_mode") or "Block NSFW"
        if current_nsfw == "ONLY_NSFW": self.dropdown_nsfw.set_selected(2)
        elif current_nsfw == "SHOW_EVERYTHING": self.dropdown_nsfw.set_selected(1)
        else: self.dropdown_nsfw.set_selected(0)
        self.dropdown_nsfw.connect("notify::selected", self.on_media_or_nsfw_changed)
        row_nsfw.add_suffix(self.dropdown_nsfw)
        group_nsfw.add(row_nsfw)
        
        row_media = Adw.ActionRow(title="Media Type", subtitle="Images, Videos or All")
        media_list = Gtk.StringList()
        media_list.append("All Media (Images & Videos)")
        media_list.append("Images Only (No Videos)")
        media_list.append("Videos Only (MP4/WebM)")
        self.dropdown_media = Gtk.DropDown(model=media_list)
        current_media = self.settings.get_preference("media_filter") or "all"
        if current_media == "images": self.dropdown_media.set_selected(1)
        elif current_media == "videos": self.dropdown_media.set_selected(2)
        else: self.dropdown_media.set_selected(0)
        self.dropdown_media.connect("notify::selected", self.on_media_or_nsfw_changed)
        row_media.add_suffix(self.dropdown_media)
        group_nsfw.add(row_media)
        
        # 3. Настройки тегов
        group_tags = Adw.PreferencesGroup(title=f"Tags for {item.name if item else 'Source'}")
        page.add(group_tags)
        row_tags = Adw.ActionRow(title="Tags", subtitle="Separate with space")
        self.entry_tags = Gtk.Entry()
        self.entry_tags.set_text(self.settings.get_preference(self.tags_key) or "")
        self.entry_tags.set_hexpand(True); self.entry_tags.set_valign(Gtk.Align.CENTER)
        self.entry_tags.connect("changed", lambda e: setattr(self, "_changed", True))
        row_tags.add_suffix(self.entry_tags)
        group_tags.add(row_tags)
        
        row_anti = Adw.ActionRow(title="Anti-Tags", subtitle="Exclude these tags")
        self.entry_anti = Gtk.Entry()
        self.entry_anti.set_text(self.settings.get_preference(self.anti_tags_key) or "")
        self.entry_anti.set_hexpand(True); self.entry_anti.set_valign(Gtk.Align.CENTER)
        self.entry_anti.connect("changed", lambda e: setattr(self, "_changed", True))
        row_anti.add_suffix(self.entry_anti)
        group_tags.add(row_anti)
        
        # 4. Аккаунт Danbooru
        group_acc = Adw.PreferencesGroup(title="Danbooru Account")
        page.add(group_acc)
        row_login = Adw.ActionRow(title="Login")
        self.entry_login = Gtk.Entry()
        self.entry_login.set_text(self.settings.get_preference("danbooru_login") or "")
        self.entry_login.set_valign(Gtk.Align.CENTER)
        self.entry_login.connect("changed", lambda e: setattr(self, "_changed", True))
        row_login.add_suffix(self.entry_login)
        group_acc.add(row_login)
        
        row_key = Adw.ActionRow(title="API Key")
        self.entry_api_key = Gtk.Entry()
        self.entry_api_key.set_text(self.settings.get_preference("danbooru_api_key") or "")
        self.entry_api_key.set_visibility(False)
        self.entry_api_key.set_valign(Gtk.Align.CENTER)
        self.entry_api_key.connect("changed", lambda e: setattr(self, "_changed", True))
        row_key.add_suffix(self.entry_api_key)
        group_acc.add(row_key)
        
        self.connect("close-request", self.on_close)

    def on_choose_folder(self, _):
        dialog = Gtk.FileChooserDialog(title="Select folder", transient_for=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Select", Gtk.ResponseType.OK)
        def on_resp(d, r):
            if r == Gtk.ResponseType.OK:
                path = d.get_file().get_path()
                self.settings.set_preference("quick_save_folder", path)
                self.lbl_folder.set_label(os.path.basename(path))
                self._changed = True
            d.destroy()
        dialog.connect("response", on_resp)
        dialog.show()

    def on_media_or_nsfw_changed(self, dropdown, _):
        self._changed = True
        sel = dropdown.get_selected()
        # Сохраняем сразу
        if dropdown == self.dropdown_nsfw:
            if sel == 0: self.settings.set_preference("nsfw_mode", "Block NSFW")
            elif sel == 1: self.settings.set_preference("nsfw_mode", "SHOW_EVERYTHING")
            else: self.settings.set_preference("nsfw_mode", "ONLY_NSFW")
        elif dropdown == self.dropdown_media:
            if sel == 1: self.settings.set_preference("media_filter", "images")
            elif sel == 2: self.settings.set_preference("media_filter", "videos")
            else: self.settings.set_preference("media_filter", "all")

    def on_close(self, _):
        # Сохраняем теги
        self.settings.set_preference(self.tags_key, self.entry_tags.get_text())
        self.settings.set_preference(self.anti_tags_key, self.entry_anti.get_text())
        self.settings.set_preference("danbooru_login", self.entry_login.get_text())
        self.settings.set_preference("danbooru_api_key", self.entry_api_key.get_text())
        
        item = self.parent.source_selector.get_selected_item()
        if item and getattr(item.api, "supports_tags", False):
            item.api.set_tags(self.entry_tags.get_text())
            item.api.set_anti_tags(self.entry_anti.get_text())
            self.parent.tags_entry.set_text(self.entry_tags.get_text())
            self.parent.anti_tags_entry.set_text(self.entry_anti.get_text())
        
        # Перезагружаем картинку ТОЛЬКО если что-то изменилось
        if self._changed:
            self.parent.async_reloadimage()
        self.destroy()