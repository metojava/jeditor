import tkinter as tk
from tkinter import font as tkfont
import re


class JavaSyntaxHighlighter:
    KEYWORDS = {
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
        "class", "const", "continue", "default", "do", "double", "else", "enum",
        "extends", "final", "finally", "float", "for", "goto", "if", "implements",
        "import", "instanceof", "int", "interface", "long", "native", "new",
        "package", "private", "protected", "public", "return", "short", "static",
        "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "try", "void", "volatile", "while", "var", "record", "sealed",
        "permits", "yield", "true", "false", "null"
    }

    COMMON_TYPES = {
        "String", "Integer", "Double", "Float", "Long", "Boolean", "Byte",
        "Short", "Character", "Object", "System", "Math", "Arrays", "List",
        "ArrayList", "Map", "HashMap", "Set", "HashSet", "Collection",
        "Collections", "Optional", "Stream", "Function", "Consumer",
        "Supplier", "Predicate", "Runnable", "Callable", "Thread",
        "Exception", "RuntimeException", "IOException", "Throwable",
        "StringBuilder", "StringBuffer", "File", "Path", "Files",
        "Scanner", "PrintStream", "BufferedReader", "BufferedWriter",
        "InputStream", "OutputStream", "Reader", "Writer",
        "Comparable", "Comparator", "Iterator", "Iterable",
        "BigDecimal", "BigInteger", "LocalDate", "LocalTime",
        "LocalDateTime", "Instant", "Duration", "Period"
    }

    def __init__(self, text_widget: tk.Text):
        self.text = text_widget
        self._setup_tags()
        self._schedule_id = None

    def _setup_tags(self):
        from .settings import settings as s
        base_font = tkfont.Font(family=s.get("editor", "font_family"),
                                 size=s.get("editor", "font_size"))
        bold_font = tkfont.Font(family=s.get("editor", "font_family"),
                                 size=s.get("editor", "font_size"), weight="bold")
        italic_font = tkfont.Font(family=s.get("editor", "font_family"),
                                   size=s.get("editor", "font_size"), slant="italic")

        self.text.tag_configure("keyword", foreground=s.get("syntax", "keyword"), font=bold_font)
        self.text.tag_configure("string", foreground=s.get("syntax", "string"))
        self.text.tag_configure("char", foreground=s.get("syntax", "char"))
        self.text.tag_configure("comment", foreground=s.get("syntax", "comment"), font=italic_font)
        self.text.tag_configure("annotation", foreground=s.get("syntax", "annotation"))
        self.text.tag_configure("number", foreground=s.get("syntax", "number"))
        self.text.tag_configure("type", foreground=s.get("syntax", "type"))
        self.text.tag_configure("bracket", foreground="#A9B7C6")

    def schedule_highlight(self, delay=300):
        if self._schedule_id:
            self.text.after_cancel(self._schedule_id)
        self._schedule_id = self.text.after(delay, self.highlight)

    def highlight(self):
        self._schedule_id = None
        try:
            self.text.mark_set("range_start", "1.0")
            self.text.tag_remove("keyword", "1.0", "end")
            self.text.tag_remove("string", "1.0", "end")
            self.text.tag_remove("char", "1.0", "end")
            self.text.tag_remove("comment", "1.0", "end")
            self.text.tag_remove("annotation", "1.0", "end")
            self.text.tag_remove("number", "1.0", "end")
            self.text.tag_remove("type", "1.0", "end")
            self.text.tag_remove("bracket", "1.0", "end")

            text_content = self.text.get("1.0", "end-1c")
            if not text_content:
                return

            self._highlight_comments(text_content)
            self._highlight_strings_and_chars(text_content)
            self._highlight_numbers(text_content)
            self._highlight_annotations(text_content)
            self._highlight_keywords(text_content)
            self._highlight_types(text_content)
        except tk.TclError:
            pass

    def _highlight_comments(self, text):
        for match in re.finditer(r"//[^\n]*|/\*.*?\*/", text, re.DOTALL):
            start = self._idx(match.start())
            end = self._idx(match.end())
            self.text.tag_add("comment", start, end)

    def _highlight_strings_and_chars(self, text):
        for match in re.finditer(r'"(?:[^"\\]|\\.)*"', text):
            start = self._idx(match.start())
            end = self._idx(match.end())
            self.text.tag_add("string", start, end)
        for match in re.finditer(r"'(?:[^'\\]|\\.)'", text):
            start = self._idx(match.start())
            end = self._idx(match.end())
            self.text.tag_add("char", start, end)

    def _highlight_numbers(self, text):
        for match in re.finditer(r'\b\d+\.?\d*[fFLlDd]?\b|\b0[xX][0-9a-fA-F]+[lL]?\b', text):
            start = self._idx(match.start())
            end = self._idx(match.end())
            self.text.tag_add("number", start, end)

    def _highlight_annotations(self, text):
        for match in re.finditer(r'@\w+', text):
            start = self._idx(match.start())
            end = self._idx(match.end())
            self.text.tag_add("annotation", start, end)

    def _highlight_keywords(self, text):
        for kw in self.KEYWORDS:
            for match in re.finditer(r'\b' + re.escape(kw) + r'\b', text):
                start = self._idx(match.start())
                end = self._idx(match.end())
                self.text.tag_add("keyword", start, end)

    def _highlight_types(self, text):
        for t in self.COMMON_TYPES:
            for match in re.finditer(r'\b' + re.escape(t) + r'\b', text):
                start = self._idx(match.start())
                end = self._idx(match.end())
                self.text.tag_add("type", start, end)

    def _idx(self, pos: int) -> str:
        return f"1.0 + {pos} chars"
