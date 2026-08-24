import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .editor_panel import EditorPanel
from .project_explorer import ProjectExplorer
from .problems_panel import ProblemsPanel
from .maven_panel import MavenPanel
from .output_console import OutputConsole
from .terminal_console import TerminalConsole
from .find_replace import FindReplaceDialog
from .settings import settings
from .settings_dialog import SettingsDialog
from .project_manager import ProjectManager
from .java_finder import JavaFinder


THEME_BG = "#F5F0E0"
THEME_BG2 = "#EDE8D8"
THEME_BG3 = "#FFFFFF"
THEME_FG = "#3A3A3A"
THEME_FG2 = "#5A5A5A"
THEME_SEL = "#C8E6C9"
THEME_TAB = "#E8E0CE"
THEME_TAB_ACTIVE = "#FDF6E3"
THEME_ACCENT = "#8FBC8F"


class JEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JEditor - Java Editor")
        self.geometry("1200x800")
        self.minsize(900, 600)
        self.configure(bg=THEME_BG)

        self._init_java_finder()
        self._init_project_manager()
        self._setup_styles()
        self._create_widgets()
        self._create_menus()
        self._create_statusbar()
        self._bind_shortcuts()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self._check_java)
        self.after(100, lambda: self._load_explorer())

    def _load_explorer(self):
        try:
            self.explorer.load_directory(os.getcwd())
        except Exception as e:
            self._output(f"Error loading explorer: {e}\n")

    def _apply_theme(self, theme):
        if theme == "dark":
            settings.set("editor", "background", "#1E1E1E")
            settings.set("editor", "foreground", "#FFFFFF")
            settings.set("editor", "caret_color", "#FFFFFF")
            settings.set("editor", "selection_bg", "#264F78")
            settings.set("editor", "selection_fg", "#FFFFFF")
            settings.set("editor", "line_numbers_bg", "#252526")
            settings.set("editor", "line_numbers_fg", "#858585")
        else:
            settings.set("editor", "background", "#FFFFFF")
            settings.set("editor", "foreground", "#000000")
            settings.set("editor", "caret_color", "#000000")
            settings.set("editor", "selection_bg", "#ADD6FF")
            settings.set("editor", "selection_fg", "#000000")
            settings.set("editor", "line_numbers_bg", "#F5F5F5")
            settings.set("editor", "line_numbers_fg", "#A0A0A0")
        settings.save()
        for panel in self._editor_panels:
            panel.apply_settings()
        self.problems_panel.apply_settings()
        self.maven_panel.apply_settings()

    def _init_java_finder(self):
        self.java_finder = JavaFinder()
        self.java_installations = self.java_finder.find_all()
        self.recommended_java = self.java_finder.recommend(self.java_installations)

    def _init_project_manager(self):
        self.project_manager = ProjectManager()
        self.project_manager.set_output_callback(self._output)

    def _create_widgets(self):
        self._create_project_explorer()
        self._create_editor_area()
        self._create_output_console()
        self._layout_panels()

    def _create_project_explorer(self):
        pass  # created in _layout_panels

    def _create_editor_area(self):
        self._editor_panels = []

    def _create_output_console(self):
        self.output_console = None

    def _layout_panels(self):
        # Output console at bottom (pack first so it gets space)
        self.output_frame = tk.Frame(self, bg=THEME_BG2, height=180)
        self.output_frame.pack(side="bottom", fill="x")
        self.output_frame.pack_propagate(False)

        self.output_handle = tk.Frame(self.output_frame, bg=THEME_BG2, height=26,
                                       cursor="sb_v_double_arrow")
        self.output_handle.pack(fill="x", side="top")
        self.output_handle.pack_propagate(False)

        bar = tk.Frame(self.output_handle, bg=THEME_BG3, height=2)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        toggle_lbl = tk.Label(self.output_handle, text="  \u25bc  Output",
                               bg=THEME_BG2, fg=THEME_FG2,
                               font=("Segoe UI", 9), cursor="hand2")
        toggle_lbl.pack(side="left")
        toggle_lbl.bind("<Button-1>", self._toggle_output)

        # Tabbed output: Output + Terminal
        self.output_notebook = ttk.Notebook(self.output_frame, style="EditorNotebook")
        self.output_notebook.pack(fill="both", expand=True)

        self.output_console = OutputConsole(self.output_notebook)
        self.output_notebook.add(self.output_console, text="  Output  ")

        self.terminal_console = TerminalConsole(self.output_notebook,
                                                project_dir_callback=self._get_project_dir)
        self.terminal_console.on_command_done = self._on_terminal_command_done
        self.output_notebook.add(self.terminal_console, text="  Terminal  ")

        clear_lbl = tk.Label(self.output_handle, text="Clear",
                              bg=THEME_BG2, fg="#787878",
                              font=("Segoe UI", 9), cursor="hand2")
        clear_lbl.pack(side="right", padx=(0, 8))
        clear_lbl.bind("<Button-1>", lambda e: self._clear_current_output())

        self._output_showing = True
        self._output_divider_pos = 180

        self.output_handle.bind("<Button-1>", self._start_output_drag)
        self.output_handle.bind("<B1-Motion>", self._do_output_drag)

        # Main horizontal split: explorer | editor
        self.main_pw = tk.PanedWindow(self, orient="horizontal",
                                       bg=THEME_BG2, sashrelief="flat",
                                       sashwidth=3, sashpad=0)
        self.main_pw.pack(side="top", fill="both", expand=True)

        # Explorer panel (left)
        self.explorer_container = tk.Frame(self.main_pw, bg=THEME_BG2)
        self.explorer = ProjectExplorer(
            self.explorer_container,
            open_file_callback=self._open_file,
            refresh_callback=self._on_project_refresh
        )
        self.explorer.pack(fill="both", expand=True)
        self.main_pw.add(self.explorer_container, width=260, minsize=120)

        # Editor container (center)
        editor_container = tk.Frame(self.main_pw, bg=THEME_BG)
        editor_container.pack(fill="both", expand=True)
        self.main_pw.add(editor_container, width=500, minsize=200)

        # Title bar at top of editor
        self.editor_title_bar = tk.Frame(editor_container, bg=THEME_TAB, height=28)
        self.editor_title_bar.pack(fill="x")
        self.editor_title_bar.pack_propagate(False)

        self.editor_title_label = tk.Label(self.editor_title_bar,
                                            text="  No file open",
                                            fg="#000000", bg=THEME_TAB,
                                            font=("Segoe UI", 10),
                                            anchor="w")
        self.editor_title_label.pack(side="left", fill="x")

        # Right-side notebook: Problems + Maven
        self.right_notebook = ttk.Notebook(self.main_pw, style="EditorNotebook")
        self.right_notebook.enable_traversal()
        self.main_pw.add(self.right_notebook, width=220, minsize=100)

        self.problems_panel = ProblemsPanel(self.right_notebook)
        self.right_notebook.add(self.problems_panel, text="  Problems  ")

        self.maven_panel = MavenPanel(self.right_notebook,
                                       run_callback=self._run_maven_command)
        self.right_notebook.add(self.maven_panel, text="  Maven  ")

        # Editor notebook (child of editor_container)
        self.editor_notebook = ttk.Notebook(editor_container, style="EditorNotebook")
        self.editor_notebook.enable_traversal()
        self.editor_notebook.bind("<Button-3>", self._on_tab_right_click)
        self.editor_notebook.bind("<<NotebookTabChanged>>", lambda e: (self._update_editor_title(), self._analyze_current_file()))
        self.editor_notebook.pack(fill="both", expand=True)

    def _start_output_drag(self, event):
        self._drag_start_y = event.y_root
        self._drag_start_height = self.output_frame.winfo_height()

    def _do_output_drag(self, event):
        delta = self._drag_start_y - event.y_root
        new_h = max(30, self._drag_start_height + delta)
        self.output_frame.configure(height=new_h)
        self._output_divider_pos = new_h

    def _toggle_output(self, event=None):
        if self._output_showing:
            self._output_divider_pos = max(30, self.output_frame.winfo_height())
            self.output_frame.pack_forget()
            self._output_showing = False
        else:
            self.output_frame.configure(height=self._output_divider_pos)
            self.output_frame.pack(side="bottom", fill="both")
            self._output_showing = True

    def _toggle_output_visible(self):
        self._toggle_output()

    def _create_menus(self):
        self.option_add("*tearOff", False)
        mb = tk.Menu(self, bg=THEME_BG2, fg=THEME_FG,
                     activebackground=THEME_BG3, activeforeground="white",
                     font=("Segoe UI", 10))

        file_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                         activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="File", menu=file_m)
        file_m.add_command(label="New File", command=self._new_file, accelerator="Ctrl+N")
        file_m.add_command(label="Open File...", command=self._open_file_dialog, accelerator="Ctrl+O")
        file_m.add_command(label="Open Folder...", command=self._open_folder_dialog, accelerator="Ctrl+Shift+O")
        file_m.add_separator()
        file_m.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_m.add_command(label="Save As...", command=self._save_as_file, accelerator="Ctrl+Shift+S")
        file_m.add_command(label="Save All", command=self._save_all, accelerator="Ctrl+Alt+S")
        file_m.add_separator()
        file_m.add_command(label="Close Tab", command=self._close_tab, accelerator="Ctrl+W")
        file_m.add_command(label="Close All", command=self._close_all_tabs)
        file_m.add_separator()
        file_m.add_command(label="Exit", command=self._on_close, accelerator="Alt+F4")

        edit_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                         activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="Edit", menu=edit_m)
        edit_m.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_m.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        edit_m.add_separator()
        edit_m.add_command(label="Cut", command=self._cut, accelerator="Ctrl+X")
        edit_m.add_command(label="Copy", command=self._copy, accelerator="Ctrl+C")
        edit_m.add_command(label="Paste", command=self._paste, accelerator="Ctrl+V")
        edit_m.add_separator()
        edit_m.add_command(label="Find/Replace...", command=self._show_find_replace, accelerator="Ctrl+F")

        view_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                         activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="View", menu=view_m)
        self._show_explorer_var = tk.BooleanVar(value=True)
        view_m.add_checkbutton(label="Project Explorer", variable=self._show_explorer_var,
                               command=self._toggle_explorer, accelerator="Ctrl+E")
        self._show_output_var = tk.BooleanVar(value=True)
        view_m.add_checkbutton(label="Output Console", variable=self._show_output_var,
                               command=self._toggle_output_visible, accelerator="Ctrl+`")
        view_m.add_separator()
        theme_m = tk.Menu(view_m, bg=THEME_BG2, fg=THEME_FG,
                          activebackground=THEME_BG3, activeforeground="white")
        view_m.add_cascade(label="Theme", menu=theme_m)
        theme_m.add_command(label="Light (White)", command=lambda: self._apply_theme("light"))
        theme_m.add_command(label="Dark (Black)", command=lambda: self._apply_theme("dark"))

        proj_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                         activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="Project", menu=proj_m)
        proj_m.add_command(label="New Maven Project...", command=self._new_maven_project)
        proj_m.add_command(label="New Gradle Project...", command=self._new_gradle_project)
        proj_m.add_separator()
        proj_m.add_command(label="Open Project...", command=self._open_folder_dialog)
        proj_m.add_command(label="Close Project", command=self._close_project)
        proj_m.add_separator()
        proj_m.add_command(label="Project Info", command=self._show_project_info)

        build_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                          activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="Build", menu=build_m)
        build_m.add_command(label="Compile", command=self._build_project, accelerator="Ctrl+B")
        build_m.add_command(label="Run", command=self._run_project, accelerator="Ctrl+R")
        build_m.add_command(label="Test", command=self._test_project, accelerator="Ctrl+T")
        build_m.add_separator()
        build_m.add_command(label="Clean", command=self._clean_project)
        build_m.add_command(label="Package", command=self._package_project)

        tools_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                          activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="Tools", menu=tools_m)
        tools_m.add_command(label="Find Java Installations...", command=self._show_java_info)
        tools_m.add_separator()
        tools_m.add_command(label="Settings...", command=self._show_settings, accelerator="Ctrl+,")

        help_m = tk.Menu(mb, bg=THEME_BG2, fg=THEME_FG,
                         activebackground=THEME_BG3, activeforeground="white")
        mb.add_cascade(label="Help", menu=help_m)
        help_m.add_command(label="About JEditor", command=self._show_about)

        self.config(menu=mb)

    def _create_statusbar(self):
        frame = tk.Frame(self, bg=THEME_BG2, height=24)
        frame.pack(side="bottom", fill="x")
        frame.pack_propagate(False)

        tk.Label(frame, text=" Ready", anchor="w",
                 bg=THEME_BG2, fg="#888888",
                 font=("Consolas", 10)).pack(side="left", padx=8)

        self.java_info = tk.Label(frame, text="", anchor="e",
                                   bg=THEME_BG2, fg="#888888",
                                   font=("Consolas", 10))
        self.java_info.pack(side="right", padx=8)

        self.java_status = tk.Label(frame, text="", anchor="e",
                                     bg=THEME_BG2, fg="#888888",
                                     font=("Consolas", 10))
        self.java_status.pack(side="right", padx=8)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("EditorNotebook", background=THEME_TAB, borderwidth=0)
        style.layout("EditorNotebook", [("Notebook.client", {"sticky": "nswe"})])
        style.configure("EditorNotebook.Tab",
                        background=THEME_TAB, foreground="#000000",
                        padding=[10, 4], font=("Segoe UI", 10))
        style.map("EditorNotebook.Tab",
                  background=[("selected", THEME_TAB_ACTIVE)],
                  foreground=[("selected", "#000000")])
        style.layout("EditorNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                    ("Notebook.label", {"side": "top", "sticky": ""})
                ]})
            ]})
        ])

        style.configure("Vertical.TScrollbar", background=THEME_BG3, troughcolor=THEME_BG,
                        arrowcolor=THEME_FG2, bordercolor=THEME_BG2)

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self._new_file())
        self.bind("<Control-o>", lambda e: self._open_file_dialog())
        self.bind("<Control-O>", lambda e: self._open_folder_dialog())
        self.bind("<Control-s>", lambda e: self._save_file())
        self.bind("<Control-S>", lambda e: self._save_as_file())
        self.bind("<Control-w>", lambda e: self._close_tab())
        self.bind("<Control-f>", lambda e: self._show_find_replace())
        self.bind("<Control-b>", lambda e: self._build_project())
        self.bind("<Control-r>", lambda e: self._run_project())
        self.bind("<Control-t>", lambda e: self._test_project())
        self.bind("<Control-comma>", lambda e: self._show_settings())
        self.bind("<Control-e>", lambda e: self._toggle_explorer())
        self.bind("<Control-grave>", lambda e: self._toggle_output_visible())

    def _check_java(self):
        if self.recommended_java:
            self.java_info.config(text=self.recommended_java.vendor)
            self.java_status.config(text=f"Java {self.recommended_java.version}")
        elif not self.java_installations:
            self.java_status.config(text="No JDK found")
        else:
            inst = self.java_installations[0]
            self.java_info.config(text=inst.vendor)
            self.java_status.config(text=f"Java {inst.version}")

    def _output(self, text):
        if self.output_console:
            self.output_console.append(text)

    def _get_project_dir(self):
        if self.project_manager and self.project_manager.project_dir:
            return self.project_manager.project_dir
        return os.getcwd()

    def _clear_current_output(self):
        tab = self.output_notebook.select()
        widget = self.output_notebook.nametowidget(tab)
        if hasattr(widget, "clear"):
            widget.clear()

    def _on_terminal_command_done(self):
        self.explorer.refresh()

    def set_status(self, text):
        pass  # status updates are less intrusive now

    def get_current_editor(self):
        sel = self.editor_notebook.select()
        return self.editor_notebook.nametowidget(sel) if sel else None

    def _new_file(self):
        panel = EditorPanel(self.editor_notebook)
        title = f"Untitled_{len(self._editor_panels) + 1}.java"
        panel.title = title
        self._add_tab(panel, title)

    def _open_file_dialog(self):
        d = self.project_manager.project_dir or os.getcwd()
        path = filedialog.askopenfilename(initialdir=d, title="Open File",
            filetypes=[("Java files", "*.java"),
                       ("All files", "*.java;*.xml;*.properties;*.json;*.yaml;*.yml;*.gradle;*.txt;*.md"),
                       ("All files", "*.*")])
        if path:
            self._open_file(path)

    def _open_folder_dialog(self):
        d = self.project_manager.project_dir or os.getcwd()
        path = filedialog.askdirectory(initialdir=d, title="Open Folder")
        if path:
            self._open_project(path)

    def _open_file(self, path):
        for i, p in enumerate(self._editor_panels):
            if p.file_path == path:
                self.editor_notebook.select(i)
                self._analyze_current_file()
                return
        panel = EditorPanel(self.editor_notebook, path)
        self._add_tab(panel, panel.title)
        self._update_editor_title()
        self._output(f"Opened: {path}\n")
        self._analyze_current_file()

    def _update_editor_title(self):
        panel = self.get_current_editor()
        if panel:
            self.editor_title_label.config(text=f"  {panel.title}")
        else:
            self.editor_title_label.config(text="  No file open")

    def _analyze_current_file(self):
        panel = self.get_current_editor()
        if panel and panel.file_path and panel.file_path.endswith(".java"):
            self.problems_panel.analyze_file(panel.file_path, self._goto_line)
        else:
            self.problems_panel.clear()

    def _goto_line(self, line):
        panel = self.get_current_editor()
        if panel:
            panel.mark_set("insert", f"{line}.0")
            panel.highlight_line(line)

    def _open_project(self, path):
        self.project_manager.open_project(path)
        self.explorer.load_directory(path)
        info = self.project_manager.get_project_info()
        title = f"JEditor - {os.path.basename(path)}"
        ptype = info.get("type", "plain").upper()
        if info.get("artifact"):
            title += f" [{info['artifact']}]"
        title += f" ({ptype})"
        self.title(title)
        if self.terminal_console:
            self.terminal_console.update_project_dir()

    def _add_tab(self, panel, title):
        panel.on_title_change(self._update_tab_title)
        self.editor_notebook.add(panel, text=title)
        self.editor_notebook.select(panel)
        self._editor_panels.append(panel)
        self._add_tab_close_button(panel)

    def _add_tab_close_button(self, panel):
        idx = self._editor_panels.index(panel)
        tab_frame = tk.Frame(self.editor_notebook, bg=THEME_TAB, highlightthickness=0)
        tab_frame.pack_propagate(False)
        lbl = tk.Label(tab_frame, text=panel.title, bg=THEME_TAB, fg=THEME_FG2,
                       font=("Segoe UI", 10))
        lbl.pack(side="left", padx=(6, 2))
        close_btn = tk.Label(tab_frame, text=" \u2716 ", bg=THEME_TAB, fg="#888888",
                             font=("Segoe UI", 9), cursor="hand2")
        close_btn.pack(side="right", padx=(2, 4))
        close_btn.bind("<Button-1>", lambda e, p=panel: self._close_specific_tab(p))
        self.editor_notebook.tab(idx, text="", window=tab_frame)

    def _update_tab_title(self, panel):
        try:
            idx = self._editor_panels.index(panel)
            marker = " \u25cf" if panel.dirty else ""
            tab_frame = self.editor_notebook.tab(idx, "window")
            if tab_frame:
                for child in tab_frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(text=panel.title + marker)
                        break
            self.editor_notebook.tab(idx, text="")
        except ValueError:
            pass

    def _close_specific_tab(self, panel):
        if panel.dirty:
            r = messagebox.askyesnocancel("Unsaved Changes",
                f"Save changes to '{panel.title}'?")
            if r is None:
                return
            if r and panel.file_path:
                panel.save()
            elif r:
                self._save_as_file()
                if not panel.file_path:
                    return
        idx = self._editor_panels.index(panel)
        self.editor_notebook.forget(idx)
        self._editor_panels.remove(panel)
        self._update_editor_title()

    def _save_file(self):
        panel = self.get_current_editor()
        if panel:
            if panel.file_path:
                panel.save()
            else:
                self._save_as_file()

    def _save_as_file(self):
        panel = self.get_current_editor()
        if not panel:
            return
        d = self.project_manager.project_dir or os.getcwd()
        path = filedialog.asksaveasfilename(initialdir=d, initialfile=panel.title,
            defaultextension=".java",
            filetypes=[("Java files", "*.java"), ("All files", "*.*")])
        if path:
            panel.save_as(path)
            idx = self._editor_panels.index(panel)
            self.editor_notebook.tab(idx, text=panel.title)

    def _save_all(self):
        for p in self._editor_panels:
            if p.dirty and p.file_path:
                p.save()

    def _close_tab(self):
        panel = self.get_current_editor()
        if not panel:
            return
        if panel.dirty:
            r = messagebox.askyesnocancel("Unsaved Changes",
                f"Save changes to '{panel.title}'?")
            if r is None:
                return
            if r and panel.file_path:
                panel.save()
            elif r:
                self._save_as_file()
                if not panel.file_path:
                    return
        idx = self._editor_panels.index(panel)
        self.editor_notebook.forget(idx)
        self._editor_panels.remove(panel)

    def _close_all_tabs(self):
        while self._editor_panels:
            self._close_tab()

    def _undo(self):
        p = self.get_current_editor()
        if p:
            try: p.text.edit_undo()
            except tk.TclError: pass

    def _redo(self):
        p = self.get_current_editor()
        if p:
            try: p.text.edit_redo()
            except tk.TclError: pass

    def _cut(self):
        p = self.get_current_editor()
        if p: p.text.event_generate("<<Cut>>")

    def _copy(self):
        p = self.get_current_editor()
        if p: p.text.event_generate("<<Copy>>")

    def _paste(self):
        p = self.get_current_editor()
        if p: p.text.event_generate("<<Paste>>")

    def _show_find_replace(self):
        p = self.get_current_editor()
        if p:
            FindReplaceDialog(self, p)

    def _toggle_explorer(self):
        if self._show_explorer_var.get():
            self.explorer_container.pack(fill="both", expand=True)
            self.main_pw.insert(0, self.explorer_container, width=260, minsize=120)
        else:
            self.main_pw.forget(self.explorer_container)

    def _new_maven_project(self):
        d = NewProjectDialog(self, "maven")
        self.wait_window(d)
        if d.result:
            path, gid, aid, jv = d.result
            ok = self.project_manager.create_maven_project(path, gid, aid, jv)
            if ok:
                self._open_project(path)
                self.output_console.append_success(f"Maven project '{aid}' created.\n")
            else:
                self.output_console.append_error("Failed to create Maven project.\n")

    def _new_gradle_project(self):
        d = NewProjectDialog(self, "gradle")
        self.wait_window(d)
        if d.result:
            path, gid, aid, jv = d.result
            ok = self.project_manager.create_gradle_project(path, gid, aid, jv)
            if ok:
                self._open_project(path)
                self.output_console.append_success(f"Gradle project '{aid}' created.\n")
            else:
                self.output_console.append_error("Failed to create Gradle project.\n")

    def _close_project(self):
        self._close_all_tabs()
        self.project_manager.project_dir = None
        self.explorer.load_directory("")
        self.title("JEditor - Java Editor")

    def _show_project_info(self):
        info = self.project_manager.get_project_info()
        if not info.get("name"):
            messagebox.showinfo("Project Info", "No project is open.")
            return
        lines = [f"Name: {info['name']}", f"Type: {info.get('type', 'plain').upper()}"]
        for k in ["group", "artifact", "version", "java_version"]:
            if info.get(k):
                lines.append(f"{k.title()}: {info[k]}")
        if self.project_manager.project_dir:
            lines.append(f"Location: {self.project_manager.project_dir}")
        messagebox.showinfo("Project Info", "\n".join(lines))

    def _build_project(self):
        self.output_console.clear()
        if self.project_manager.project_dir:
            self.output_console.append("=== Building project ===\n")
            self.project_manager.build_project()
        else:
            self._compile_single_file()

    def _run_project(self):
        self.output_console.clear()
        if self.project_manager.project_dir:
            self.output_console.append("=== Running project ===\n")
            self.project_manager.run_project()
        else:
            self._run_single_file()

    def _test_project(self):
        if self.project_manager.project_dir:
            self.output_console.clear()
            self.output_console.append("=== Running tests ===\n")
            self.project_manager.test_project()
        else:
            self.output_console.append("Open a project to run tests.\n")

    def _clean_project(self):
        if self.project_manager.project_dir:
            self.output_console.clear()
            self.output_console.append("=== Cleaning ===\n")
            self.project_manager.clean_project()
        else:
            self.output_console.append("Open a project to clean.\n")

    def _package_project(self):
        if self.project_manager.project_dir:
            self.output_console.clear()
            self.output_console.append("=== Packaging ===\n")
            self.project_manager.package_project()
        else:
            self.output_console.append("Open a project to package.\n")

    def _run_maven_command(self, cmd):
        if self.terminal_console:
            self.output_notebook.select(self.terminal_console)
            self.terminal_console.run_command(cmd)

    def _compile_single_file(self):
        panel = self.get_current_editor()
        if not panel or not panel.file_path:
            self.output_console.append("Save the file first, then compile.\n")
            return
        self.output_console.clear()
        self.output_console.append(f"=== Compiling {panel.title} ===\n")
        import subprocess, threading
        def run():
            try:
                javac = "javac"
                if self.recommended_java:
                    javac = os.path.join(self.recommended_java.path, "javac")
                    if not os.path.isfile(javac):
                        javac = os.path.join(self.recommended_java.path, "..", "javac")
                    if not os.path.isfile(javac):
                        javac = "javac"
                proc = subprocess.run([javac, panel.file_path],
                    capture_output=True, text=True, timeout=30)
                out = (proc.stdout or "") + (proc.stderr or "")
                ok = proc.returncode == 0
                self.after(0, lambda: self.output_console.append(out))
                self.after(0, lambda: self.output_console.append(
                    f"\n=== {'Compilation successful' if ok else f'Exit code {proc.returncode}'} ===\n"))
            except Exception as e:
                self.after(0, lambda: self.output_console.append(f"Error: {e}\n"))
        threading.Thread(target=run, daemon=True).start()

    def _run_single_file(self):
        panel = self.get_current_editor()
        if not panel or not panel.file_path:
            self.output_console.append("Save the file first, then run.\n")
            return
        self.output_console.clear()
        class_name = os.path.splitext(os.path.basename(panel.file_path))[0]
        import subprocess, threading
        def run():
            try:
                java = "java"
                if self.recommended_java:
                    java = os.path.join(self.recommended_java.path, "java")
                    if not os.path.isfile(java):
                        java = "java"
                proc = subprocess.Popen([java, "-cp", os.path.dirname(panel.file_path), class_name],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, cwd=os.path.dirname(panel.file_path))
                for line in proc.stdout:
                    self.after(0, lambda l=line: self.output_console.append(l))
                proc.wait()
                self.after(0, lambda: self.output_console.append(
                    f"\n=== Process exited with code {proc.returncode} ===\n"))
            except Exception as e:
                self.after(0, lambda: self.output_console.append(f"Error: {e}\n"))
        threading.Thread(target=run, daemon=True).start()

    def _show_java_info(self):
        lines = ["Java Installations Found:\n"]
        if not self.java_installations:
            lines.append("  None detected.\n")
        for inst in self.java_installations:
            m = "  \u2713 RECOMMENDED" if inst == self.recommended_java else "    "
            lines.append(f"{m} {inst.display_name()}\n  Vendor: {inst.vendor}\n")
        lines.append(f"\nJAVA_HOME: {os.environ.get('JAVA_HOME', '(not set)')}\n")
        self.output_console.clear()
        self.output_console.append("".join(lines))

    def _show_settings(self):
        def apply():
            for p in self._editor_panels:
                p.apply_settings()
            self._setup_styles()
            self.configure(bg=THEME_BG)
        SettingsDialog(self, apply_callback=apply)

    def _show_about(self):
        messagebox.showinfo("About JEditor",
            "JEditor - Java Editor\n\n"
            "A lightweight Java IDE with:\n"
            "\u2022 Maven & Gradle project support\n"
            "\u2022 Java syntax highlighting\n"
            "\u2022 Project explorer\n"
            "\u2022 Find/Replace\n"
            "\u2022 Build & Run\n"
            "\u2022 Customizable themes\n\n"
            "Built with Python & Tkinter")

    def _on_project_refresh(self):
        if self.project_manager.project_dir:
            self.project_manager.open_project(self.project_manager.project_dir)

    def _on_tab_right_click(self, event):
        p = self.get_current_editor()
        if not p:
            return
        m = tk.Menu(self, tearoff=0, bg=THEME_BG2, fg=THEME_FG,
                    activebackground=THEME_SEL, activeforeground="#1A1A1A")
        m.add_command(label="Close", command=self._close_tab)
        m.add_command(label="Close Others", command=self._close_other_tabs)
        m.add_separator()
        m.add_command(label="Copy Path", command=self._copy_tab_path)
        m.post(event.x_root, event.y_root)

    def _close_other_tabs(self):
        current = self.get_current_editor()
        for p in list(self._editor_panels):
            if p is not current:
                idx = self._editor_panels.index(p)
                self.editor_notebook.forget(idx)
                self._editor_panels.remove(p)

    def _copy_tab_path(self):
        p = self.get_current_editor()
        if p and p.file_path:
            self.clipboard_clear()
            self.clipboard_append(p.file_path)

    def _on_close(self):
        dirty = [p for p in self._editor_panels if p.dirty]
        if dirty:
            r = messagebox.askyesnocancel("Unsaved Changes",
                f"{len(dirty)} file(s) have unsaved changes. Save before exiting?")
            if r is None:
                return
            if r:
                self._save_all()
        self.destroy()


class NewProjectDialog(tk.Toplevel):
    def __init__(self, parent, project_type="maven"):
        super().__init__(parent)
        self.result = None
        self.project_type = project_type
        self.title(f"New {project_type.title()} Project")
        self.geometry("500x340")
        self.configure(bg=THEME_BG)
        self.transient(parent)
        self.grab_set()
        self._create_widgets()
        self.bind("<Escape>", lambda e: self.destroy())

    def _create_widgets(self):
        f = tk.Frame(self, bg=THEME_BG, padx=18, pady=18)
        f.pack(fill="both", expand=True)

        r = 0
        tk.Label(f, text="Location:", bg=THEME_BG, fg=THEME_FG,
                 font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w")
        lf = tk.Frame(f, bg=THEME_BG)
        lf.grid(row=r, column=1, sticky="ew", pady=3)
        self.loc_var = tk.StringVar(value=os.getcwd())
        tk.Entry(lf, textvariable=self.loc_var, bg=THEME_BG3, fg="white",
                 insertbackground="white", relief="flat",
                 font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)
        tk.Button(lf, text="...", command=self._browse,
                  bg=THEME_BG3, fg="white", relief="flat",
                  activebackground="#5A5A5A", font=("Segoe UI", 9), width=3).pack(side="right", padx=(4, 0))

        r += 1
        tk.Label(f, text="Project Name:", bg=THEME_BG, fg=THEME_FG,
                 font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w")
        self.name_var = tk.StringVar(value="my-java-app")
        tk.Entry(f, textvariable=self.name_var, bg=THEME_BG3, fg="white",
                 insertbackground="white", relief="flat",
                 font=("Segoe UI", 10)).grid(row=r, column=1, sticky="ew", pady=3)

        r += 1
        tk.Label(f, text="Group ID:", bg=THEME_BG, fg=THEME_FG,
                 font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w")
        self.grp_var = tk.StringVar(value="com.example")
        tk.Entry(f, textvariable=self.grp_var, bg=THEME_BG3, fg="white",
                 insertbackground="white", relief="flat",
                 font=("Segoe UI", 10)).grid(row=r, column=1, sticky="ew", pady=3)

        r += 1
        tk.Label(f, text="Artifact ID:", bg=THEME_BG, fg=THEME_FG,
                 font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w")
        self.art_var = tk.StringVar(value="demo")
        tk.Entry(f, textvariable=self.art_var, bg=THEME_BG3, fg="white",
                 insertbackground="white", relief="flat",
                 font=("Segoe UI", 10)).grid(row=r, column=1, sticky="ew", pady=3)

        r += 1
        tk.Label(f, text="Java Version:", bg=THEME_BG, fg=THEME_FG,
                 font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w")
        jf = tk.Frame(f, bg=THEME_BG)
        jf.grid(row=r, column=1, sticky="w", pady=3)
        self.jv_var = tk.StringVar(value="17")
        for v in ["8", "11", "17", "21", "22", "23"]:
            tk.Radiobutton(jf, text=v, variable=self.jv_var, value=v,
                           bg=THEME_BG, fg=THEME_FG, selectcolor=THEME_BG,
                           activebackground=THEME_BG, activeforeground=THEME_FG,
                           font=("Consolas", 10)).pack(side="left", padx=4)

        if self.project_type == "gradle":
            r += 1
            self.kts_var = tk.BooleanVar(value=False)
            tk.Checkbutton(f, text="Use Kotlin DSL (build.gradle.kts)",
                           variable=self.kts_var,
                           bg=THEME_BG, fg=THEME_FG, selectcolor=THEME_BG,
                           activebackground=THEME_BG, activeforeground=THEME_FG,
                           font=("Segoe UI", 10)).grid(row=r, column=0, columnspan=2, sticky="w", pady=5)

        r += 1
        bf = tk.Frame(f, bg=THEME_BG)
        bf.grid(row=r, column=0, columnspan=2, pady=(18, 0))
        tk.Button(bf, text="Create Project", command=self._create,
                  bg="#3C7E3C", fg="white", relief="flat",
                  activebackground="#4A9A4A",
                  font=("Segoe UI", 10), padx=12).pack(side="left", padx=6)
        tk.Button(bf, text="Cancel", command=self.destroy,
                  bg=THEME_BG3, fg="white", relief="flat",
                  activebackground="#5A5A5A",
                  font=("Segoe UI", 10), padx=12).pack(side="left", padx=6)

        f.columnconfigure(1, weight=1)

    def _browse(self):
        p = filedialog.askdirectory(initialdir=self.loc_var.get(), title="Choose location")
        if p:
            self.loc_var.set(p)

    def _create(self):
        loc = self.loc_var.get().strip()
        name = self.name_var.get().strip()
        gid = self.grp_var.get().strip()
        aid = self.art_var.get().strip()
        jv = self.jv_var.get().strip()
        if not all([loc, name, gid, aid, jv]):
            messagebox.showerror("Error", "All fields are required.")
            return
        d = os.path.join(loc, name)
        if os.path.exists(d):
            if not messagebox.askyesno("Directory exists", f"'{d}' already exists. Overwrite?"):
                return
        self.result = (d, gid, aid, jv)
        self.destroy()


def main():
    app = JEditor()
    app.mainloop()


if __name__ == "__main__":
    main()
