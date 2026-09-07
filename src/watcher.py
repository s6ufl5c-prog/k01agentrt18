import time
import pyperclip
from typing import Callable, Set
from src.engine import GoogleAutoRedeemer


class ClipboardWatcher:
    """Monitors system clipboard for Google Service Activation links in real-time."""

    def __init__(self, callback: Callable[[str], None], poll_interval: float = 1.0):
        self.callback = callback
        self.poll_interval = poll_interval
        self.seen_urls: Set[str] = set()
        self._running = False

    def start(self):
        self._running = True
        last_paste = ""
        print(f"[*] Clipboard watcher started (polling every {self.poll_interval}s)...")
        print("[*] Copy any serviceactivation.google.com link to automatically redeem it!")
        try:
            while self._running:
                try:
                    content = pyperclip.paste()
                except Exception:
                    content = ""

                if content and content != last_paste:
                    last_paste = content
                    clean_url = GoogleAutoRedeemer.clean_url(content)
                    if clean_url and clean_url not in self.seen_urls:
                        self.seen_urls.add(clean_url)
                        print(f"\n[!] Detected new activation link in clipboard: {clean_url[:60]}...")
                        self.callback(clean_url)

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n[*] Clipboard watcher stopped by user.")

    def stop(self):
        self._running = False
