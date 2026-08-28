import requests
import json
from typing import Optional
from .types import NSFWOption
from .api_base import BaseDownloaderAPI

class WaifuDownloaderAPI(BaseDownloaderAPI):
    supports_tags = True
    supports_anti_tags = True

    def __init__(self, settings=None) -> None:
        super().__init__()
        self.endpoint = "https://api.waifu.im/images"
        self._settings = settings
        if settings:
            self.tags = settings.get_preference("waifu_tags") or ""
            self.anti_tags = settings.get_preference("waifu_anti_tags") or ""

    def get_page(self, nsfw: Optional[bool] = None) -> Optional[str]:
        try:
            params = {}
            if nsfw is None: params["is_nsfw"] = "true"
            elif nsfw: params["is_nsfw"] = "true"
            else: params["is_nsfw"] = "false"
            
            # Собираем теги
            included_tags = self.tags.split() if self.tags else []
            excluded_tags = self.anti_tags.split() if self.anti_tags else []
            
            # Применяем фильтр медиа
            media_filter = self._settings.get_preference("media_filter") if self._settings else "all"
            if media_filter == "videos":
                included_tags.append("animated")
            elif media_filter == "images":
                excluded_tags.append("animated")
                
            if included_tags: params["included_tags"] = " ".join(included_tags)
            if excluded_tags: params["excluded_tags"] = " ".join(excluded_tags)
                
            headers = {'User-Agent': 'CatgirlDownloader/0.5 (by NyarchLinux)'}
            r = requests.get(self.endpoint, params=params, headers=headers, timeout=10)
            
            if r.status_code == 200: return r.text
            else: print(f"Waifu.im error: {r.status_code}"); return None
        except Exception as e:
            print(e); return None

    def get_page_url(self, response: Optional[str]) -> Optional[str]:
        if not response:
            return None
        try:
            data = json.loads(response)
            self.info = data
            return data["images"][0]['url']
        except Exception as e:
            print(e)
            return None

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        nsfw = False
        if nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
            nsfw = True
        elif nsfw_mode == NSFWOption.SHOW_EVERYTHING or nsfw_mode == NSFWOption.SHOW_EVERYTHING.value:
            nsfw = None
        return self.get_page_url(self.get_page(nsfw))

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            image_info = data['images'][0]
            artists = image_info.get('artists')
            if isinstance(artists, list) and artists:
                return artists[0].get('name')
            return None
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data['images'][0].get('source')
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        try:
            if data:
                image_id = data['images'][0].get('id', 'unknown')
            else:
                raise Exception("No info")
        except Exception:
            import time
            image_id = str(int(time.time()))
        if extension:
            return f"waifu.im_{image_id}.{extension}"
        return f"waifu.im_{image_id}"

    def set_tags(self, tags: str) -> None:
        super().set_tags(tags)
        if self._settings:
            self._settings.set_preference("waifu_tags", tags)

    def set_anti_tags(self, tags: str) -> None:
        super().set_anti_tags(tags)
        if self._settings:
            self._settings.set_preference("waifu_anti_tags", tags)
