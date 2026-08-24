import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Optional, Callable
from .syntax_highlighter import JavaSyntaxHighlighter
from .settings import settings


class LineNumberPanel(tk.Frame):
    def __init__(self, parent, text_widget):
        super().__init__(parent, bg=settings.get("editor", "line_numbers_bg"))
        self.text_widget = text_widget
        self._font = tkfont.Font(family=settings.get("editor", "font_family"),
                                   size=settings.get("editor", "font_size"))

        self.nums = tk.Text(self, wrap="none",
                             font=self._font,
                             bg=settings.get("editor", "line_numbers_bg"),
                             fg=settings.get("editor", "line_numbers_fg"),
                             padx=4, pady=4,
                             state="disabled",
                             relief="flat", borderwidth=0,
                             highlightthickness=0,
                             cursor="arrow", takefocus=0,
                             exportselection=False)
        self.nums.pack(side="left", fill="both", expand=True)

        self._sep = tk.Frame(self, bg="#CCBB99", width=1)
        self._sep.pack(side="right", fill="y")

    def _sync(self, event=None):
        tw = self.text_widget
        if not tw:
            return
        line_count = int(tw.index("end-1c").split(".")[0])
        lines = "\n".join(str(i) for i in range(1, line_count + 1))
        digits = max(3, len(str(max(line_count, 1))))
        self.nums.config(state="normal", width=digits + 1)
        self.nums.delete("1.0", "end")
        self.nums.insert("1.0", lines)
        self.nums.config(state="disabled")
        self.nums.yview_moveto(tw.yview()[0])


class EditorPanel(tk.Frame):
    def __init__(self, parent, file_path: Optional[str] = None, title: str = "Untitled.java"):
        super().__init__(parent)
        self.file_path = file_path
        self.title = title
        self.dirty = False
        self._callbacks = []

        self.text = tk.Text(self, wrap="none", undo=True,
                            font=(settings.get("editor", "font_family"),
                                  settings.get("editor", "font_size")),
                            bg=settings.get("editor", "background"),
                            fg=settings.get("editor", "foreground"),
                            insertbackground=settings.get("editor", "caret_color"),
                            selectbackground=settings.get("editor", "selection_bg"),
                            selectforeground=settings.get("editor", "selection_fg"),
                            relief="flat", borderwidth=0,
                            padx=6, pady=4)
        self.line_numbers = LineNumberPanel(self, self.text)
        self.line_numbers.pack(side="left", fill="y")

        self.text.tag_configure("bracket", foreground="#A9B7C6")
        self.text.tag_configure("problem_highlight", background="#FFD700", foreground="#000000")

        self.highlighter = JavaSyntaxHighlighter(self.text)

        text_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._scroll_both)
        text_scrollbar.pack(side="right", fill="y")

        self.text.pack(side="left", fill="both", expand=True)
        self.text.configure(yscrollcommand=self._sync_scroll)

        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Button-4>", self._on_mousewheel)
        self.text.bind("<Button-5>", self._on_mousewheel)
        self.text.bind("<<Paste>>", lambda e: self._schedule_highlight())
        self.text.bind("<Configure>", self.line_numbers._sync)

        self._scrollbar = text_scrollbar
        self._highlight_scheduled = None

        if file_path and os.path.isfile(file_path):
            self.load_file(file_path)

        self.after(100, self.line_numbers._sync)

    def load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.text.edit_reset()
            self.file_path = path
            self.title = os.path.basename(path)
            self.dirty = False
            self._notify_title()
            self.after(50, self.highlighter.highlight)
            self.after(100, self.line_numbers._sync)
        except (OSError, UnicodeDecodeError) as e:
            self.text.insert("1.0", f"Error loading file: {e}")

    def save(self):
        if not self.file_path:
            return False
        try:
            content = self.text.get("1.0", "end-1c")
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.dirty = False
            self._notify_title()
            return True
        except OSError as e:
            import tkinter.messagebox as mb
            mb.showerror("Save Error", f"Cannot save file: {e}")
            return False

    def save_as(self, path: str):
        self.file_path = path
        self.title = os.path.basename(path)
        return self.save()

    def find(self, text: str) -> bool:
        if not text:
            return False
        content = self.text.get("1.0", "end-1c")
        start_pos = self.text.index("insert")
        start_offset = self._text_index_to_offset(start_pos)
        idx = content.find(text, start_offset)
        if idx < 0:
            idx = content.find(text)
        if idx >= 0:
            pos = f"1.0 + {idx} chars"
            self.text.mark_set("insert", pos)
            self.text.see(pos)
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", pos, f"{pos} + {len(text)} chars")
            return True
        return False

    def replace(self, find_text: str, replace_text: str) -> bool:
        if self.text.tag_ranges("sel"):
            sel_text = self.text.get("sel.first", "sel.last")
            if sel_text == find_text:
                self.text.replace("sel.first", "sel.last", replace_text)
                return True
        return self.find(find_text)

    def replace_all(self, find_text: str, replace_text: str):
        content = self.text.get("1.0", "end-1c")
        new_content = content.replace(find_text, replace_text)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", new_content)
        self.highlighter.schedule_highlight(100)

    def on_title_change(self, callback: Callable):
        self._callbacks.append(callback)

    def _notify_title(self):
        for cb in self._callbacks:
            cb(self)

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            if not self.dirty:
                self.dirty = True
                self._notify_title()
            self.text.edit_modified(False)

    def _on_key_release(self, event):
        if event.keysym in ("Return", "BackSpace", "Delete", "Tab", "space"):
            self._schedule_highlight()
        self.after(10, self.line_numbers._sync)

    def _schedule_highlight(self):
        if self._highlight_scheduled:
            self.after_cancel(self._highlight_scheduled)
        self._highlight_scheduled = self.after(300, self._do_highlight)

    def _do_highlight(self):
        self._highlight_scheduled = None
        self.highlighter.highlight()

    def _scroll_both(self, *args):
        self.text.yview_moveto(args[0] if args else 0)
        self.line_numbers._sync()

    def _sync_scroll(self, *args):
        self._scrollbar.set(*args)
        self.line_numbers._sync()

    def highlight_line(self, line: int, color: str = None):
        self.text.tag_remove("problem_highlight", "1.0", "end")
        if line < 1:
            return
        start = f"{line}.0"
        end = f"{line}.end"
        if color:
            self.text.tag_configure("problem_highlight", background=color)
        self.text.tag_add("problem_highlight", start, end)
        self.text.see(start)

    def clear_highlight(self):
        self.text.tag_remove("problem_highlight", "1.0", "end")

    def _on_mousewheel(self, event):
        self.after(50, self.line_numbers._sync)

    def _text_index_to_offset(self, index: str) -> int:
        lines = index.split(".")
        if len(lines) != 2:
            return 0
        line_num = int(lines[0]) - 1
        char_offset = int(lines[1])
        total = 0
        for i, line in enumerate(self.text.get("1.0", "end-1c").split("\n")):
            if i < line_num:
                total += len(line) + 1
            else:
                total += char_offset
                break
        return total

    def apply_settings(self):
        font_family = settings.get("editor", "font_family")
        font_size = settings.get("editor", "font_size")
        self.text.configure(
            font=(font_family, font_size),
            bg=settings.get("editor", "background"),
            fg=settings.get("editor", "foreground"),
            insertbackground=settings.get("editor", "caret_color"),
            selectbackground=settings.get("editor", "selection_bg"),
            selectforeground=settings.get("editor", "selection_fg"),
        )
        self.line_numbers._font = tkfont.Font(family=font_family, size=font_size)
        self.line_numbers.config(bg=settings.get("editor", "line_numbers_bg"))
        self.line_numbers.nums.config(font=self.line_numbers._font,
                                       bg=settings.get("editor", "line_numbers_bg"),
                                       fg=settings.get("editor", "line_numbers_fg"))
        self.highlighter._setup_tags()
        self.highlighter.highlight()
        self.line_numbers._sync()
