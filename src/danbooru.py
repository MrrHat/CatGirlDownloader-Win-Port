import requests
import json
import time
import base64
from typing import Optional, Any
from .types import NSFWOption
from .api_base import BaseDownloaderAPI

_FORBIDDEN_TAG_1 = base64.b64decode('c2hvdGE='.encode('utf-8')).decode('utf-8')
_FORBIDDEN_TAG_2 = base64.b64decode('bG9saQ=='.encode('utf-8')).decode('utf-8')

class DanbooruDownloaderAPI(BaseDownloaderAPI):
    supports_tags = True
    supports_anti_tags = True

    def __init__(self, settings=None) -> None:
        super().__init__()
        self.endpoint = "https://danbooru.donmai.us"
        self._settings = settings
        self._load_tags()
        self._settings_window = None

    def _load_tags(self) -> None:
        if self._settings:
            self.tags = self._settings.get_preference("danbooru_tags") or ""
            self.anti_tags = self._settings.get_preference("danbooru_anti_tags") or ""

    def set_tags(self, tags: str) -> None:
        self.tags = tags
        if self._settings:
            self._settings.set_preference("danbooru_tags", tags)

    def set_anti_tags(self, tags: str) -> None:
        self.anti_tags = tags
        if self._settings:
            self._settings.set_preference("danbooru_anti_tags", tags)

    def _build_tags_query(self, nsfw_mode: NSFWOption) -> str:
        tags = self.tags.strip() if self.tags else ""
        anti = self.anti_tags.strip() if self.anti_tags else ""

        parts = []
        if tags: parts.append(tags)
        for t in anti.split():
            if t: parts.append(f"-{t}")

        media_filter = self._settings.get_preference("media_filter") if self._settings else "all"
        if media_filter == "images": parts.append("-animated")
        elif media_filter == "videos": parts.append("animated")

        if nsfw_mode == NSFWOption.BLOCK_NSFW or nsfw_mode == NSFWOption.BLOCK_NSFW.value: parts.append("rating:general")
        elif nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value: parts.append("rating:explicit")

        return " ".join(parts)

    def get_random_post(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW, max_retries: int = 3) -> Optional[dict]:
        login = self._settings.get_preference("danbooru_login") if self._settings else None
        api_key = self._settings.get_preference("danbooru_api_key") if self._settings else None

        for attempt in range(max_retries):
            try:
                tags = self._build_tags_query(nsfw_mode)
                params = { "limit": 1, "random": "true" }
                if tags: params["tags"] = tags
                
                if login and api_key:
                    params["login"] = login
                    params["api_key"] = api_key

                headers = {'User-Agent': 'CatgirlDownloader/0.5 (by NyarchLinux)'}
                r = requests.get(f"{self.endpoint}/posts.json", params=params, headers=headers, timeout=5)
                if r.status_code != 200: return None
            except Exception as e:
                return None
            try:
                data = json.loads(r.text)
                if isinstance(data, list) and len(data) > 0:
                    post = data[0]
                    
                    if not post.get("file_url"):
                        continue
                        
                    post_tags = post.get('tag_string', '').split()
                    if _FORBIDDEN_TAG_1 in post_tags or _FORBIDDEN_TAG_2 in post_tags:
                        continue
                        
                    self.info = post
                    return post
                return None
            except Exception:
                return None
        return None

    def get_tag_suggestions(self, prefix: str) -> list:
        login = self._settings.get_preference("danbooru_login") if self._settings else None
        api_key = self._settings.get_preference("danbooru_api_key") if self._settings else None

        try:
            url = f"{self.endpoint}/tags.json"
            params = {"search[name_matches]": f"{prefix}*", "limit": 5}
            
            if login and api_key:
                params["login"] = login
                params["api_key"] = api_key

            headers = {'User-Agent': 'CatgirlDownloader/0.5 (by NyarchLinux)'}
            r = requests.get(url, params=params, headers=headers, timeout=5)
            if r.status_code == 200:
                data = json.loads(r.text)
                return [(tag["name"], tag["post_count"]) for tag in data]
        except Exception as e:
            print(f"Autocomplete error: {e}")
        return []

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        post = self.get_random_post(nsfw_mode)
        if post:
            return post.get("file_url")
        return None

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            artist_tags = data.get("tag_string_artist", "")
            if artist_tags:
                return artist_tags.split(" ")[0]
            return None
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            post_id = data.get("id")
            if post_id:
                return f"{self.endpoint}/posts/{post_id}"
            return None
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        if not data:
            post_id = str(int(time.time()))
        else:
            try:
                post_id = str(data.get("id", int(time.time())))
            except Exception:
                post_id = str(int(time.time()))
        if extension:
            return f"danbooru_{post_id}.{extension}"
        return f"danbooru_{post_id}"

    def open_settings_window(self, parent: Any) -> None:
        from gi.repository import Gtk, Adw
        window = Adw.PreferencesWindow()
        window.set_title("Danbooru Settings")
        window.set_modal(True)
        if isinstance(parent, Gtk.Window):
            window.set_transient_for(parent)
        else:
            toplevel = parent.get_ancestor(Gtk.Window)
            if toplevel:
                window.set_transient_for(toplevel)
        page = Adw.PreferencesPage()
        window.add(page)
        group = Adw.PreferencesGroup()
        group.set_title("Tags")
        page.add(group)
        
        row_inc = Adw.ActionRow(title="Search Tags")
        entry_inc = Gtk.Entry()
        entry_inc.set_text(self.tags)
        entry_inc.set_placeholder_text("e.g., cat_ears solo")
        entry_inc.set_hexpand(True)
        entry_inc.connect("changed", lambda e: self._on_tags_changed(e.get_text()))
        row_inc.add_suffix(entry_inc)
        group.add(row_inc)
        
        row_exc = Adw.ActionRow(title="Exclude Tags")
        entry_exc = Gtk.Entry()
        entry_exc.set_text(self.anti_tags)
        entry_exc.set_placeholder_text("e.g., 1boy lowres")
        entry_exc.set_hexpand(True)
        entry_exc.connect("changed", lambda e: self._on_anti_tags_changed(e.get_text()))
        row_exc.add_suffix(entry_exc)
        group.add(row_exc)
        
        window.connect("close-request", lambda e: self._on_prefs_close(parent))
        self._settings_window = window
        window.present()

    def _on_tags_changed(self, text: str) -> None:
        tagcheck = text.lower().split()
        while _FORBIDDEN_TAG_1 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_1)
        while _FORBIDDEN_TAG_2 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_2)
        self.tags = ' '.join(tagcheck)
        if self._settings:
            self._settings.set_preference("danbooru_tags", self.tags)

    def _on_anti_tags_changed(self, text: str) -> None:
        tagcheck = text.lower().split()
        while _FORBIDDEN_TAG_1 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_1)
        while _FORBIDDEN_TAG_2 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_2)
        self.anti_tags = ' '.join(tagcheck)
        if self._settings:
            self._settings.set_preference("danbooru_anti_tags", self.anti_tags)

    def _on_prefs_close(self, parent: Any) -> None:
        all_tags = (self.tags + " " + self.anti_tags).lower().split()
        if _FORBIDDEN_TAG_1 in all_tags or _FORBIDDEN_TAG_2 in all_tags:
            self.open_forbid_tag_notif(parent)

    def open_forbid_tag_notif(self, parent: Any) -> None:
        from gi.repository import Gtk, Adw
        dialog = Adw.MessageDialog(modal=True, heading="Danbooru Settings")
        dialog.set_body_use_markup(True)
        dialog.set_body('Due to a limitation of Danbooru, certain tags have been automatically removed from your settings. For more information, please visit <a href="https://danbooru.donmai.us/wiki_pages/help:censored_tags">Danbooru\'s "censored tags" help page</a>.')
        if isinstance(parent, Gtk.Window):
            dialog.set_transient_for(parent)
        else:
            toplevel = parent.get_ancestor(Gtk.Window)
            if toplevel:
                dialog.set_transient_for(toplevel)
        dialog.add_response("ok", "OK")
        dialog.present()
