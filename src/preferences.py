from gi.repository import GLib
import os
import json

class UserPreferences:
    def __init__(self):
        self._defaults = {
            "nsfw_mode": "Block NSFW",
            "auto_reload_enabled": False,
            "auto_reload_interval": 5,
            "danbooru_tags": "",
            "danbooru_anti_tags": "",
            "waifu_tags": "",
            "waifu_anti_tags": "",
            "danbooru_login": "",
            "danbooru_api_key": "",
            "quick_save_folder": "",
            "media_filter": "all",
        }
        self.preferences = dict(self._defaults)
        self.directory = os.path.join(GLib.get_user_config_dir(), "catgirldownloader")
        os.makedirs(self.directory, exist_ok=True)
        self.file = os.path.join(self.directory, "config.json")
        if not os.path.exists(self.file):
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f)
        try:
            with open(self.file, 'r', encoding="utf-8") as f:
                self.preferences = json.load(f)
            changed = False
            for k, v in self._defaults.items():
                if k not in self.preferences:
                    self.preferences[k] = v
                    changed = True
            if changed:
                self.set_preference_batch(self.preferences)
        except Exception as e:
            print(e)

    def reload_preferences(self):
        try:
            with open(self.file, 'r', encoding="utf-8") as f:
                self.preferences = json.load(f)
            for k, v in self._defaults.items():
                if k not in self.preferences:
                    self.preferences[k] = v
        except Exception as e:
            print(e)

    def get_preference(self, key):
        self.reload_preferences()
        return self.preferences.get(key)

    def set_preference(self, key, value):
        self.preferences[key] = value
        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f)
        except Exception as e:
            print(e)

    def set_preference_batch(self, prefs: dict):
        self.preferences = prefs
        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f)
        except Exception as e:
            print(e)
