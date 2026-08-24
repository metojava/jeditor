import tkinter as tk
from tkinter import ttk

MAVEN_COMMANDS = [
    "clean",
    "validate",
    "compile",
    "test-compile",
    "test",
    "package",
    "verify",
    "install",
    "deploy",
    "site",
    "dependency:resolve",
    "dependency:tree",
]


class MavenPanel(tk.Frame):
    def __init__(self, parent, run_callback=None):
        super().__init__(parent)
        self.run_callback = run_callback
        self.configure(bg="#EDE8D8")

        header = tk.Frame(self, bg="#4A6FA5", height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="  Maven Commands", fg="#FFFFFF",
                 bg="#4A6FA5", font=("Segoe UI", 10, "bold")).pack(side="left")

        self.listbox = tk.Listbox(self, selectmode="multiple",
                                   bg="#FDF6E3", fg="#3A3A3A",
                                   font=("Consolas", 11),
                                   selectbackground="#C8E6C9",
                                   relief="flat", borderwidth=0,
                                   highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)

        for cmd in MAVEN_COMMANDS:
            self.listbox.insert("end", f"  mvn {cmd}")

        info = tk.Label(self, text="Select commands, then press Enter to run",
                         bg="#EDE8D8", fg="#888888",
                         font=("Segoe UI", 9))
        info.pack(fill="x", padx=4, pady=(0, 4))

        self.listbox.bind("<Return>", self._on_enter)
        self.listbox.bind("<KP_Enter>", self._on_enter)
        self.listbox.focus_set()

    def _on_enter(self, event=None):
        sel = self.listbox.curselection()
        if not sel or not self.run_callback:
            return
        for idx in sel:
            cmd = MAVEN_COMMANDS[idx]
            self.run_callback(f"mvn {cmd}")

    def apply_settings(self):
        pass
