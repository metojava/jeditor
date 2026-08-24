import tkinter as tk
from tkinter import ttk
from .settings import settings


class OutputConsole(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.text = tk.Text(self, wrap="word",
                            font=("Consolas", 11),
                            bg=settings.get("ui", "output_bg"),
                            fg=settings.get("ui", "output_fg"),
                            insertbackground="white",
                            relief="flat", borderwidth=0,
                            state="disabled", padx=4, pady=4)
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.tag_configure("error", foreground="#E06C75")
        self.text.tag_configure("warning", foreground="#D19A66")
        self.text.tag_configure("info", foreground="#61AFEF")
        self.text.tag_configure("success", foreground="#98C379")

    def append(self, text: str, tag: str = None):
        self.text.configure(state="normal")
        self.text.insert("end", text, tag)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def append_error(self, text: str):
        self.append(text, "error")

    def append_success(self, text: str):
        self.append(text, "success")

    def append_info(self, text: str):
        self.append(text, "info")

    def append_warning(self, text: str):
        self.append(text, "warning")

    def apply_settings(self):
        self.text.configure(
            bg=settings.get("ui", "output_bg"),
            fg=settings.get("ui", "output_fg"),
        )
