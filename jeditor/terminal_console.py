import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from .settings import settings


class TerminalConsole(tk.Frame):
    def __init__(self, parent, project_dir_callback=None):
        super().__init__(parent)
        self.project_dir_callback = project_dir_callback
        self.history = []
        self.history_index = -1
        self._current_dir = self.project_dir

        entry_frame = tk.Frame(self, bg="#252526")
        entry_frame.pack(side="bottom", fill="x")

        self.prompt_label = tk.Label(entry_frame, text=self._get_prompt(),
                                      bg="#252526", fg="#FFFFFF",
                                      font=("Consolas", 11))
        self.prompt_label.pack(side="left")

        self.entry = tk.Entry(entry_frame, bg="#1E1E1E", fg="#FFFFFF",
                               insertbackground="white",
                               font=("Consolas", 11), relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)

        self.text = tk.Text(self, wrap="word",
                            font=("Consolas", 11),
                            bg="#1E1E1E", fg="#D4D4D4",
                            insertbackground="white",
                            relief="flat", borderwidth=0,
                            state="disabled", padx=4, pady=4)
        self.text.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.entry.bind("<Return>", self._on_command)
        self.entry.bind("<Up>", self._on_up)
        self.entry.bind("<Down>", self._on_down)

        self._show_startup_message()

    def _show_startup_message(self):
        self._append_output(f"Terminal - Current folder: {self._current_dir}\n\n")

    @property
    def project_dir(self):
        if self.project_dir_callback:
            return self.project_dir_callback()
        return os.getcwd()

    def _get_prompt(self):
        return f"{self._current_dir}> "

    def _append_output(self, text, tag=None):
        self.text.configure(state="normal")
        self.text.insert("end", text, tag)
        self.text.see("end")
        self.text.configure(state="disabled")

    def update_prompt(self):
        self.prompt_label.config(text=self._get_prompt())

    def update_project_dir(self):
        self._current_dir = self.project_dir
        self.update_prompt()

    def _on_command(self, event=None):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.history.append(cmd)
        self.history_index = len(self.history)
        self.entry.delete(0, "end")
        self._append_output(f"{self._get_prompt()}{cmd}\n")
        threading.Thread(target=self._run_command, args=(cmd,), daemon=True).start()

    def _on_up(self, event):
        if self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.history[self.history_index])

    def _on_down(self, event):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.history[self.history_index])
        else:
            self.history_index = len(self.history)
            self.entry.delete(0, "end")

    def _run_command(self, cmd):
        if cmd.startswith("cd ") or cmd == "cd":
            parts = cmd.split(maxsplit=1)
            target = parts[1] if len(parts) > 1 else os.path.expanduser("~")
            new_dir = os.path.join(self._current_dir, target) if not os.path.isabs(target) else target
            new_dir = os.path.abspath(new_dir)
            if os.path.isdir(new_dir):
                self._current_dir = new_dir
                self.after(0, lambda: self._append_output(f"\n"))
                self.after(0, self.update_prompt)
            else:
                self.after(0, lambda: self._append_output(f"The system cannot find the path specified.\n\n"))
                self.after(0, self.update_prompt)
            return
        self._run_process(cmd)

    def _run_process(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, cwd=self._current_dir,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            for line in iter(proc.stdout.readline, ""):
                self.after(0, lambda l=line: self._append_output(l))
            proc.wait()
            rc = proc.returncode
            tag = None if rc == 0 else "error"
            self.after(0, lambda: self._append_output(f"\nExit code: {rc}\n\n", tag))
            if hasattr(self, "on_command_done") and self.on_command_done:
                self.after(0, self.on_command_done)
        except Exception as e:
            self.after(0, lambda: self._append_output(f"Error: {e}\n\n"))
        finally:
            self.after(0, self.update_prompt)

    def run_command(self, cmd):
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self._on_command()

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
