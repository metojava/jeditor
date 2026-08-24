import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from .settings import settings


class ProblemsPanel(tk.Frame):
    def __init__(self, parent, java_callback=None):
        super().__init__(parent)
        self.java_callback = java_callback
        self._problems = []

        self.configure(bg="#EDE8D8")
        header = tk.Frame(self, bg="#4A6FA5", height=32)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="  Problems", fg="#FFFFFF",
                 bg="#4A6FA5", font=("Segoe UI", 10, "bold")).pack(side="left")

        self._count_label = tk.Label(header, text="0", fg="#FFFFFF",
                                      bg="#4A6FA5", font=("Segoe UI", 10))
        self._count_label.pack(side="right", padx=(0, 8))

        self.listbox = tk.Listbox(self, bg="#FDF6E3", fg="#3A3A3A",
                                   font=("Consolas", 10),
                                   selectbackground="#C8E6C9",
                                   relief="flat", borderwidth=0)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<ButtonRelease-1>", self._on_click)

    def set_problems(self, problems):
        self._problems = problems
        self.listbox.delete(0, "end")
        for p in problems:
            icon = "\u2716" if p["type"] == "error" else "\u26a0"
            self.listbox.insert("end", f"  {icon}  {p['line']}:{p['col']}  {p['msg']}")
        self._count_label.config(text=str(len(problems)))

    def clear(self):
        self._problems = []
        self.listbox.delete(0, "end")
        self._count_label.config(text="0")

    def _on_click(self, event):
        sel = self.listbox.curselection()
        if not sel or not self._problems:
            return
        p = self._problems[sel[0]]
        if p.get("callback"):
            p["callback"]()

    def analyze_file(self, file_path, goto_line_callback=None):
        if not file_path or not os.path.isfile(file_path):
            self.clear()
            return
        threading.Thread(target=self._run_analysis, args=(file_path, goto_line_callback),
                         daemon=True).start()

    def _run_analysis(self, file_path, goto_line_callback):
        problems = []

        java_cmd = "javac"
        if self.java_callback:
            java_info = self.java_callback()
            if java_info:
                jc = os.path.join(java_info.path, "javac")
                if os.path.isfile(jc):
                    java_cmd = jc
                else:
                    jc = os.path.join(java_info.path, "..", "javac")
                    if os.path.isfile(jc):
                        java_cmd = jc
        try:
            proc = subprocess.run([java_cmd, "-Xlint", file_path],
                                  capture_output=True, text=True, timeout=30,
                                  cwd=os.path.dirname(file_path))
            stderr = proc.stderr
        except FileNotFoundError:
            problems.append({"type": "error", "line": 0, "col": 0,
                             "msg": "javac not found. Install JDK.", "callback": None})
            self.after(0, lambda: self.set_problems(problems))
            return
        except subprocess.TimeoutExpired:
            problems.append({"type": "error", "line": 0, "col": 0,
                             "msg": "Analysis timed out.", "callback": None})
            self.after(0, lambda: self.set_problems(problems))
            return
        except Exception as e:
            problems.append({"type": "error", "line": 0, "col": 0,
                             "msg": f"Analysis error: {e}", "callback": None})
            self.after(0, lambda: self.set_problems(problems))
            return

        pattern = re.compile(r"^([\w\\/].+?\.java):(\d+):\s*(error|warning):\s*(.+)$", re.MULTILINE)
        for match in pattern.finditer(stderr):
            line_num = int(match.group(2))
            ptype = match.group(3)
            msg = match.group(4)
            cb = (lambda ln: lambda: goto_line_callback(ln))(line_num) if goto_line_callback else None
            problems.append({"type": ptype, "line": line_num, "col": 0, "msg": msg, "callback": cb})

        self.after(0, lambda: self.set_problems(problems))

    def apply_settings(self):
        pass
