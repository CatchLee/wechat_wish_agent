"""Centralized configuration loader and writer for config.json.

Provides a single shared instance so UI pages read/write through the same
in-memory copy while keeping the file on disk in sync.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from threading import RLock
from typing import Any, Dict


class ConfigManager:
    """Thread-safe helper for reading and writing the app config."""

    def __init__(self, config_path: Path) -> None:
        self._path = config_path
        self._lock = RLock()
        self._data: Dict[str, Any] = {}
        self.reload()

    @property
    def path(self) -> Path:
        return self._path

    def reload(self) -> Dict[str, Any]:
        """Reload config from disk and return a snapshot."""
        with self._lock:
            if not self._path.exists():
                self._data = {}
                return dict(self._data)

            raw = self._path.read_text(encoding="utf-8")
            clean = self._strip_comments(raw)
            try:
                self._data = json.loads(clean)
            except Exception:
                self._data = {}
            return dict(self._data)

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of current config without touching disk."""
        with self._lock:
            return dict(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, *, persist: bool = True) -> None:
        with self._lock:
            self._data[key] = value
        if persist:
            self.save()

    def update(self, values: Dict[str, Any], *, persist: bool = True) -> None:
        with self._lock:
            self._data.update(values)
        if persist:
            self.save()

    def save(self) -> None:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            json_text = json.dumps(self._data, ensure_ascii=False, indent=4)
            self._path.write_text(json_text, encoding="utf-8")

    @staticmethod
    def _strip_comments(text: str) -> str:
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//.*?$", "", text, flags=re.M)
        return text


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"
app_config = ConfigManager(CONFIG_PATH)


def reload_config() -> Dict[str, Any]:
    """Force reload from disk and return a snapshot."""
    return app_config.reload()


def current_config() -> Dict[str, Any]:
    """Return in-memory snapshot without disk I/O."""
    return app_config.snapshot()
