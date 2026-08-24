import json
import os
from typing import Optional


DEFAULT_SETTINGS = {
    "editor": {
        "font_family": "Consolas",
        "font_size": 13,
        "background": "#FDF6E3",
        "foreground": "#3A3A3A",
        "caret_color": "#D14A4A",
        "selection_bg": "#C8E6C9",
        "selection_fg": "#2E2E2E",
        "line_numbers_bg": "#F5F0E0",
        "line_numbers_fg": "#A0A0A0",
    },
    "syntax": {
        "keyword": "#A86CB8",
        "string": "#6A9F5A",
        "char": "#6A9F5A",
        "comment": "#A0A0A0",
        "annotation": "#B8B82E",
        "number": "#5B9FC7",
        "type": "#5BBFA0",
    },
    "ui": {
        "bg": "#F5F0E0",
        "fg": "#3A3A3A",
        "input_bg": "#FFFFFF",
        "input_fg": "#2E2E2E",
        "button_bg": "#8FBC8F",
        "button_fg": "#FFFFFF",
        "tab_bg": "#E8E0CE",
        "tab_active_bg": "#FDF6E3",
        "tab_fg": "#6A6A6A",
        "tab_active_fg": "#2E2E2E",
        "output_bg": "#FDF6E3",
        "output_fg": "#4A5A4A",
        "explorer_bg": "#EDE8D8",
        "explorer_fg": "#3A3A3A",
    },
    "general": {
        "tab_size": 4,
        "show_line_numbers": True,
        "wrap_text": False,
        "auto_save": False,
    }
}


class Settings:
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.path = config_path
        else:
            self.path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        self.data = self._load()

    def _load(self) -> dict:
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
        except (json.JSONDecodeError, OSError):
            pass
        return dict(DEFAULT_SETTINGS)

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def get(self, section: str, key: str, default=None):
        return self.data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value):
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value

    def get_section(self, section: str) -> dict:
        return {**DEFAULT_SETTINGS.get(section, {}), **self.data.get(section, {})}

    def get_editor_font(self):
        return (self.get("editor", "font_family"),
                self.get("editor", "font_size"))

    def get_editor_colors(self) -> dict:
        return self.get_section("editor")

    def get_ui_colors(self) -> dict:
        return self.get_section("ui")

    def get_syntax_colors(self) -> dict:
        return self.get_section("syntax")

    def get_general(self) -> dict:
        return self.get_section("general")


settings = Settings()
