import os
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


def _natural_key(name):
    is_dir = 0 if os.path.isdir(name) else 1
    return (is_dir, name.lower())


class ProjectExplorer(tk.Frame):
    def __init__(self, parent, open_file_callback: Optional[Callable] = None,
                 refresh_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.open_file_callback = open_file_callback
        self.refresh_callback = refresh_callback
        self.current_dir: Optional[str] = None

        self.configure(bg="#EDE8D8")
        header = tk.Frame(self, bg="#4A6FA5", height=32)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="  Project Explorer", fg="#FFFFFF",
                 bg="#4A6FA5", font=("Segoe UI", 10, "bold")).pack(side="left")

        btn_frame = tk.Frame(header, bg="#4A6FA5")
        btn_frame.pack(side="right", padx=(0, 6))

        toggle_btn = tk.Label(btn_frame, text="\u229e", fg="#FFFFFF",
                               bg="#4A6FA5", cursor="hand2", font=("Segoe UI", 11))
        toggle_btn.pack(side="left", padx=(0, 4))
        toggle_btn.bind("<Button-1>", lambda e: self._toggle_expand())

        refresh_btn = tk.Label(btn_frame, text="\u21bb", fg="#CCCCCC",
                                bg="#4A6FA5", cursor="hand2", font=("Segoe UI", 13))
        refresh_btn.pack(side="left")
        refresh_btn.bind("<Button-1>", lambda e: self._do_refresh())

        self.tree = ttk.Treeview(self, show="tree", style="Explorer.Treeview")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<ButtonRelease-1>", self._on_single_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)

        style = ttk.Style()
        style.configure("Explorer.Treeview",
                        background="#EDE8D8", foreground="#4A4A4A",
                        fieldbackground="#EDE8D8", rowheight=24,
                        font=("Segoe UI", 11))
        style.map("Explorer.Treeview",
                  background=[("selected", "#C8E6C9")],
                  foreground=[("selected", "#2E2E2E")])
        style.configure("Explorer.Treeview.Item", padding=(0, 2))
        style.configure("Vertical.TScrollbar", background="#333", troughcolor="#252525",
                        arrowcolor="#888")

        self._popup = tk.Menu(self, tearoff=0, bg="#FFFFFF", fg="#3A3A3A",
                              activebackground="#C8E6C9", activeforeground="#1A1A1A",
                              font=("Segoe UI", 10))
        self._popup.add_command(label="Open", command=self._popup_open)
        self._popup.add_separator()
        self._popup.add_command(label="New File", command=self._popup_new_file)
        self._popup.add_command(label="New Folder", command=self._popup_new_folder)
        self._popup.add_separator()
        self._popup.add_command(label="Delete", command=self._popup_delete)
        self._popup.add_command(label="Rename", command=self._popup_rename)
        self._popup.add_separator()
        self._popup.add_command(label="Copy Path", command=self._popup_copy_path)
        self._popup.add_command(label="Open in Explorer", command=self._popup_open_explorer)

    def load_directory(self, directory: str):
        self.current_dir = directory
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not (directory and os.path.isdir(directory)):
            return
        node = self.tree.insert("", "end", text=os.path.basename(directory),
                                values=[directory], open=True)
        self._populate_children(node, directory)
        self.tree.selection_set(node)

    def _populate_children(self, parent_node: str, directory: str):
        existing = self.tree.get_children(parent_node)
        if existing and self.tree.item(existing[0], "text") == "":
            self.tree.delete(existing[0])
        try:
            entries = sorted(os.listdir(directory), key=_natural_key)
        except PermissionError:
            return
        for entry in entries:
            full = os.path.join(directory, entry)
            if entry.startswith(".") and entry not in {".gitignore", ".gitkeep",
                                                        ".gitattributes", ".editorconfig"}:
                continue
            if entry in {"__pycache__", "node_modules", ".git", ".idea",
                          ".settings", ".classpath", ".project", ".DS_Store"}:
                continue
            if os.path.isdir(full):
                child = self.tree.insert(parent_node, "end", text=entry, values=[full])
                self.tree.insert(child, "end", text="")
            else:
                self.tree.insert(parent_node, "end", text=entry, values=[full])

    def _on_tree_open(self, event):
        node = self.tree.focus()
        if not node:
            return
        path = self._get_path(node)
        if path and os.path.isdir(path):
            self._populate_children(node, path)

    def refresh(self):
        if self.current_dir:
            self.load_directory(self.current_dir)

    def _on_single_click(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if path and os.path.isfile(path) and self.open_file_callback:
            self.open_file_callback(path)

    def _on_double_click(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if path and os.path.isfile(path) and self.open_file_callback:
            self.open_file_callback(path)

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self._popup.post(event.x_root, event.y_root)

    def _get_path(self, item) -> Optional[str]:
        v = self.tree.item(item, "values")
        return v[0] if v else None

    def _popup_open(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if path and os.path.isfile(path) and self.open_file_callback:
            self.open_file_callback(path)

    def _popup_new_file(self):
        parent = self._popup_target_dir()
        if not parent:
            return
        name = self._ask("New File", "File name:", "NewFile.java")
        if name:
            try:
                open(os.path.join(parent, name), "w").close()
                self.refresh()
            except OSError as e:
                self._error(f"Cannot create file: {e}")

    def _popup_new_folder(self):
        parent = self._popup_target_dir()
        if not parent:
            return
        name = self._ask("New Folder", "Folder name:", "NewFolder")
        if name:
            try:
                os.makedirs(os.path.join(parent, name), exist_ok=True)
                self.refresh()
            except OSError as e:
                self._error(f"Cannot create folder: {e}")

    def _popup_target_dir(self) -> Optional[str]:
        sel = self.tree.selection()
        p = self.current_dir
        if sel:
            path = self._get_path(sel[0])
            if path:
                p = path if os.path.isdir(path) else os.path.dirname(path)
        return p

    def _popup_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if not path:
            return
        import tkinter.messagebox as mb
        if mb.askyesno("Delete", f"Delete '{os.path.basename(path)}'?"):
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.refresh()
            except OSError as e:
                self._error(f"Cannot delete: {e}")

    def _popup_rename(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if not path:
            return
        new = self._ask("Rename", "New name:", os.path.basename(path))
        if new:
            try:
                os.rename(path, os.path.join(os.path.dirname(path), new))
                self.refresh()
            except OSError as e:
                self._error(f"Cannot rename: {e}")

    def _popup_copy_path(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if path:
            self.clipboard_clear()
            self.clipboard_append(path)

    def _popup_open_explorer(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._get_path(sel[0])
        if not path:
            return
        target = path if os.path.isdir(path) else os.path.dirname(path)
        import subprocess
        subprocess.Popen(["explorer", target])

    def _toggle_expand(self):
        children = self.tree.get_children("")
        if not children:
            return
        root = children[0]
        root_path = self._get_path(root)
        if root_path and os.path.isdir(root_path):
            self._populate_all(root, root_path)
        all_open = self._all_real_open(root)
        self._set_all_open(root, not all_open)

    def _populate_all(self, node, path):
        self._populate_children(node, path)
        for child in self.tree.get_children(node):
            child_path = self._get_path(child)
            if child_path and os.path.isdir(child_path):
                self._populate_all(child, child_path)

    def _all_real_open(self, node):
        for child in self.tree.get_children(node):
            if not self.tree.item(child, "text"):
                continue
            if not self.tree.item(child, "open"):
                return False
            if not self._all_real_open(child):
                return False
        return True

    def _set_all_open(self, node, open_state):
        for child in self.tree.get_children(node):
            if not self.tree.item(child, "text"):
                continue
            self.tree.item(child, open=open_state)
            self._set_all_open(child, open_state)

    def _do_refresh(self):
        self.refresh()
        if self.refresh_callback:
            self.refresh_callback()

    def _ask(self, title: str, prompt: str, default: str = "") -> Optional[str]:
        d = tk.Toplevel(self)
        d.title(title)
        d.geometry("380x130")
        d.configure(bg="#F5F0E0")
        d.resizable(False, False)
        d.transient(self.winfo_toplevel())
        d.grab_set()

        var = tk.StringVar(value=default)
        tk.Label(d, text=prompt, fg="#3A3A3A", bg="#F5F0E0",
                 font=("Segoe UI", 10)).pack(pady=(18, 6))
        e = tk.Entry(d, textvariable=var, width=42,
                     font=("Segoe UI", 11), bg="#FFFFFF", fg="#2E2E2E",
                     insertbackground="#D14A4A", relief="flat")
        e.pack(pady=4, padx=18, fill="x")
        e.select_range(0, "end")
        e.focus_set()

        def ok():
            d.destroy()

        def cancel():
            var.set("")
            d.destroy()

        bf = tk.Frame(d, bg="#F5F0E0")
        bf.pack(pady=10)
        for txt, cmd in [("OK", ok), ("Cancel", cancel)]:
            tk.Button(bf, text=txt, command=cmd,
                      bg="#8FBC8F", fg="white", relief="flat",
                      activebackground="#7DAF7D",
                      font=("Segoe UI", 9), width=8).pack(side="left", padx=4)

        d.bind("<Return>", lambda e: ok())
        d.bind("<Escape>", lambda e: cancel())
        self.wait_window(d)
        v = var.get().strip()
        return v if v else None

    def _error(self, msg: str):
        import tkinter.messagebox as mb
        mb.showerror("Error", msg)
