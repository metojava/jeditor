import tkinter as tk
from .settings import settings


class FindReplaceDialog(tk.Toplevel):
    def __init__(self, parent, editor_panel):
        super().__init__(parent)
        self.editor = editor_panel
        self.title("Find/Replace")
        self.geometry("420x160")
        self.configure(bg=settings.get("ui", "bg"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.bind("<Escape>", lambda e: self.destroy())

        self.find_entry.focus_set()

    def _create_widgets(self):
        bg = settings.get("ui", "bg")
        fg = settings.get("ui", "fg")
        input_bg = settings.get("ui", "input_bg")
        input_fg = settings.get("ui", "input_fg")
        btn_bg = settings.get("ui", "button_bg")
        btn_fg = settings.get("ui", "button_fg")

        main_frame = tk.Frame(self, bg=bg, padx=12, pady=12)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Find:", bg=bg, fg=fg,
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.find_var = tk.StringVar()
        self.find_entry = tk.Entry(main_frame, textvariable=self.find_var,
                                    width=40, bg=input_bg, fg=input_fg,
                                    insertbackground="white", relief="flat")
        self.find_entry.grid(row=0, column=1, pady=(0, 6), sticky="ew")
        self.find_entry.bind("<Return>", lambda e: self._find())

        tk.Label(main_frame, text="Replace:", bg=bg, fg=fg,
                 font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(0, 2))
        self.replace_var = tk.StringVar()
        replace_entry = tk.Entry(main_frame, textvariable=self.replace_var,
                                  width=40, bg=input_bg, fg=input_fg,
                                  insertbackground="white", relief="flat")
        replace_entry.grid(row=1, column=1, pady=(0, 12), sticky="ew")
        replace_entry.bind("<Return>", lambda e: self._replace())

        btn_frame = tk.Frame(main_frame, bg=bg)
        btn_frame.grid(row=2, column=0, columnspan=2)

        buttons = [
            ("Find Next", self._find),
            ("Replace", self._replace),
            ("Replace All", self._replace_all),
            ("Close", self.destroy),
        ]
        for text, cmd in buttons:
            tk.Button(btn_frame, text=text, command=cmd,
                      bg=btn_bg, fg=btn_fg, relief="flat",
                      activebackground="#5A5A5A",
                      font=("Segoe UI", 9)).pack(side="left", padx=3)

        main_frame.columnconfigure(1, weight=1)

    def _find(self):
        text = self.find_var.get()
        if text:
            self.editor.find(text)

    def _replace(self):
        find = self.find_var.get()
        replace = self.replace_var.get()
        if find:
            self.editor.replace(find, replace)

    def _replace_all(self):
        find = self.find_var.get()
        replace = self.replace_var.get()
        if find:
            self.editor.replace_all(find, replace)
