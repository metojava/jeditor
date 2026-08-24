import tkinter as tk
from tkinter import ttk, font as tkfont, colorchooser
from .settings import settings


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, apply_callback=None):
        super().__init__(parent)
        self.apply_callback = apply_callback
        self.title("Settings")
        self.geometry("650x500")
        self.configure(bg=settings.get("ui", "bg"))
        self.transient(parent)
        self.grab_set()

        self._backup = {s: dict(d) for s, d in settings.data.items()}

        self._create_widgets()
        self.bind("<Escape>", lambda e: self.destroy())

    def _create_widgets(self):
        bg = settings.get("ui", "bg")
        fg = settings.get("ui", "fg")
        btn_bg = settings.get("ui", "button_bg")
        btn_fg = settings.get("ui", "button_fg")

        main = tk.Frame(self, bg=bg)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self._create_editor_tab()
        self._create_syntax_tab()
        self._create_ui_tab()
        self._create_general_tab()

        btn_frame = tk.Frame(main, bg=bg)
        btn_frame.pack(fill="x", pady=(8, 0))
        tk.Button(btn_frame, text="Apply", command=self._apply,
                  bg=btn_bg, fg=btn_fg, relief="flat",
                  activebackground="#5A5A5A").pack(side="right", padx=3)
        tk.Button(btn_frame, text="OK", command=self._ok,
                  bg=btn_bg, fg=btn_fg, relief="flat",
                  activebackground="#5A5A5A").pack(side="right", padx=3)
        tk.Button(btn_frame, text="Cancel", command=self._cancel,
                  bg=btn_bg, fg=btn_fg, relief="flat",
                  activebackground="#5A5A5A").pack(side="right", padx=3)

    def _make_tab(self):
        bg = settings.get("ui", "bg")
        frame = tk.Frame(self.notebook, bg=bg, padx=12, pady=12)
        return frame

    def _create_editor_tab(self):
        frame = self._make_tab()
        self.notebook.add(frame, text="Editor")

        fg = settings.get("ui", "fg")
        input_bg = settings.get("ui", "input_bg")
        input_fg = settings.get("ui", "input_fg")

        row = 0
        tk.Label(frame, text="Font Family:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self.font_family_var = tk.StringVar(value=settings.get("editor", "font_family"))
        families = sorted(tkfont.families())
        filtered = [f for f in families if any(name in f.lower()
                    for name in ["consolas", "monaco", "courier", "mono", "dejavu",
                                 "source code", "fira", "jetbrains", "hack"])]
        if not filtered:
            filtered = ["Consolas", "Courier New", "Monaco"] + families[:20]
        else:
            filtered = filtered[:20]
        self.font_family_combo = ttk.Combobox(frame, textvariable=self.font_family_var,
                                               values=filtered, width=25)
        self.font_family_combo.grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        tk.Label(frame, text="Font Size:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self.font_size_var = tk.IntVar(value=settings.get("editor", "font_size"))
        tk.Spinbox(frame, from_=8, to=36, textvariable=self.font_size_var,
                   width=8, bg=input_bg, fg=input_fg,
                   insertbackground="white", relief="flat").grid(row=row, column=1, sticky="w", pady=3)

        row += 1
        tk.Label(frame, text="Background:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self._color_picker(frame, row, "editor", "background")

        row += 1
        tk.Label(frame, text="Foreground:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self._color_picker(frame, row, "editor", "foreground")

        row += 1
        tk.Label(frame, text="Caret Color:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self._color_picker(frame, row, "editor", "caret_color")

        row += 1
        tk.Label(frame, text="Selection BG:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self._color_picker(frame, row, "editor", "selection_bg")

        row += 1
        tk.Label(frame, text="Line # BG:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self._color_picker(frame, row, "editor", "line_numbers_bg")

        row += 1
        tk.Label(frame, text="Line # FG:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self._color_picker(frame, row, "editor", "line_numbers_fg")

    def _create_syntax_tab(self):
        frame = self._make_tab()
        self.notebook.add(frame, text="Syntax Colors")

        fg = settings.get("ui", "fg")

        labels = [
            ("keyword", "Keywords"),
            ("string", "Strings"),
            ("char", "Characters"),
            ("comment", "Comments"),
            ("annotation", "Annotations"),
            ("number", "Numbers"),
            ("type", "Types"),
        ]
        for i, (key, label) in enumerate(labels):
            tk.Label(frame, text=f"{label}:", bg=frame["bg"], fg=fg,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=3)
            self._color_picker(frame, i, "syntax", key)

    def _create_ui_tab(self):
        frame = self._make_tab()
        self.notebook.add(frame, text="UI Colors")

        fg = settings.get("ui", "fg")

        labels = [
            ("bg", "Background"),
            ("fg", "Foreground"),
            ("input_bg", "Input BG"),
            ("input_fg", "Input FG"),
            ("button_bg", "Button BG"),
            ("button_fg", "Button FG"),
            ("tab_bg", "Tab BG"),
            ("tab_active_bg", "Active Tab BG"),
            ("tab_fg", "Tab FG"),
            ("tab_active_fg", "Active Tab FG"),
            ("output_bg", "Output BG"),
            ("output_fg", "Output FG"),
            ("explorer_bg", "Explorer BG"),
            ("explorer_fg", "Explorer FG"),
        ]
        for i, (key, label) in enumerate(labels):
            tk.Label(frame, text=f"{label}:", bg=frame["bg"], fg=fg,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=2)
            self._color_picker(frame, i, "ui", key)

    def _create_general_tab(self):
        frame = self._make_tab()
        self.notebook.add(frame, text="General")

        fg = settings.get("ui", "fg")

        row = 0
        tk.Label(frame, text="Tab Size:", bg=frame["bg"], fg=fg,
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=3)
        self.tab_size_var = tk.IntVar(value=settings.get("general", "tab_size"))
        tk.Spinbox(frame, from_=2, to=8, textvariable=self.tab_size_var,
                   width=8, bg=settings.get("ui", "input_bg"),
                   fg=settings.get("ui", "input_fg"),
                   insertbackground="white", relief="flat").grid(row=row, column=1, sticky="w", pady=3)

        row += 1
        self.show_line_numbers_var = tk.BooleanVar(value=settings.get("general", "show_line_numbers"))
        tk.Checkbutton(frame, text="Show Line Numbers", variable=self.show_line_numbers_var,
                       bg=frame["bg"], fg=fg, selectcolor=frame["bg"],
                       activebackground=frame["bg"], activeforeground=fg,
                       font=("Segoe UI", 10)).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)

        row += 1
        self.wrap_text_var = tk.BooleanVar(value=settings.get("general", "wrap_text"))
        tk.Checkbutton(frame, text="Wrap Text", variable=self.wrap_text_var,
                       bg=frame["bg"], fg=fg, selectcolor=frame["bg"],
                       activebackground=frame["bg"], activeforeground=fg,
                       font=("Segoe UI", 10)).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)

        row += 1
        self.auto_save_var = tk.BooleanVar(value=settings.get("general", "auto_save"))
        tk.Checkbutton(frame, text="Auto-Save on Run", variable=self.auto_save_var,
                       bg=frame["bg"], fg=fg, selectcolor=frame["bg"],
                       activebackground=frame["bg"], activeforeground=fg,
                       font=("Segoe UI", 10)).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)

    def _color_picker(self, parent, row, section, key):
        frame = tk.Frame(parent, bg=parent["bg"])
        frame.grid(row=row, column=1, sticky="w", pady=3)

        color = settings.get(section, key)
        btn = tk.Button(frame, text="    ", bg=color, width=3,
                        relief="flat", cursor="hand2",
                        command=lambda: self._pick_color(btn, section, key))
        btn.pack(side="left")

        entry = tk.Entry(frame, width=12,
                         bg=settings.get("ui", "input_bg"),
                         fg=settings.get("ui", "input_fg"),
                         insertbackground="white", relief="flat")
        entry.insert(0, color)
        entry.pack(side="left", padx=(6, 0))

        if section not in self._color_widgets:
            self._color_widgets[section] = {}
        self._color_widgets[section][key] = (btn, entry)

        entry.bind("<KeyRelease>", lambda e: self._update_color_btn(btn, entry))
        entry.bind("<FocusOut>", lambda e: self._update_color_btn(btn, entry))

    def _pick_color(self, btn, section, key):
        current = btn.cget("bg")
        result = colorchooser.askcolor(current, title=f"Choose color for {key}")
        if result and result[1]:
            btn.configure(bg=result[1])
            _, entry = self._color_widgets.get(section, {}).get(key, (None, None))
            if entry:
                entry.delete(0, "end")
                entry.insert(0, result[1])

    def _update_color_btn(self, btn, entry):
        color = entry.get().strip()
        if color and len(color) == 7 and color[0] == "#":
            try:
                int(color[1:], 16)
                btn.configure(bg=color)
            except ValueError:
                pass

    def _collect_values(self):
        settings.set("editor", "font_family", self.font_family_var.get())
        settings.set("editor", "font_size", self.font_size_var.get())

        for section in ["editor", "syntax", "ui"]:
            if section in self._color_widgets:
                for key, (_, entry) in self._color_widgets[section].items():
                    val = entry.get().strip()
                    if val:
                        settings.set(section, key, val)

        settings.set("general", "tab_size", self.tab_size_var.get())
        settings.set("general", "show_line_numbers", self.show_line_numbers_var.get())
        settings.set("general", "wrap_text", self.wrap_text_var.get())
        settings.set("general", "auto_save", self.auto_save_var.get())

    def _apply(self):
        self._collect_values()
        settings.save()
        if self.apply_callback:
            self.apply_callback()

    def _ok(self):
        self._apply()
        self.destroy()

    def _cancel(self):
        settings.data = self._backup
        self.destroy()

    _color_widgets = {}
