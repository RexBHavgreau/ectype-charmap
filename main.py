import json
import tkinter as tk
import unicodedata
from pathlib import Path
from tkinter import ttk


PAPER = "#f2f4f3"
INK = "#172321"
MUTED = "#667471"
LINE = "#cbd3d0"
PANEL = "#ffffff"
MINT = "#c9efdf"
CORAL = "#ff745e"
YELLOW = "#f4d75e"
DEEP = "#184f47"
MONO = ("TkFixedFont", 10)
SERIF = ("Georgia", 14)

CATEGORIES = [
    {"id": "basic", "name": "Basic Latin", "start": 0x20, "end": 0x7E},
    {"id": "latin1", "name": "Latin-1 Supplement", "start": 0xA0, "end": 0xFF},
    {"id": "greek", "name": "Greek & Coptic", "start": 0x370, "end": 0x3FF},
    {"id": "cyrillic", "name": "Cyrillic", "start": 0x400, "end": 0x4FF},
    {"id": "punctuation", "name": "Punctuation", "start": 0x2000, "end": 0x206F},
    {"id": "currency", "name": "Currency", "start": 0x20A0, "end": 0x20CF},
    {"id": "arrows", "name": "Arrows", "start": 0x2190, "end": 0x21FF},
    {"id": "math", "name": "Math operators", "start": 0x2200, "end": 0x22FF},
    {"id": "box", "name": "Box drawing", "start": 0x2500, "end": 0x257F},
    {"id": "emoji", "name": "Emoji faces", "start": 0x1F600, "end": 0x1F64F},
    {"id": "favorites", "name": "Favorites", "special": "favorites"},
    {"id": "recent", "name": "Recently used", "special": "recent"},
]


def code_label(codepoint):
    return f"U+{codepoint:04X}"


def character_name(character):
    return unicodedata.name(character, "UNNAMED CHARACTER").replace(" ", " ")


class GlyphIndex:
    def __init__(self, root):
        self.root = root
        self.root.title("Glyph Index — Character Map")
        self.root.geometry("1180x780")
        self.root.minsize(840, 620)
        self.root.configure(bg=PAPER)

        self.active_category = CATEGORIES[0]
        self.selected_codepoint = ord("A")
        self.mode = tk.StringVar(value="copy")
        self.query = tk.StringVar()
        self.favorites = self._load_favorites()
        self.recent = []
        self.glyph_buttons = {}
        self.toast_job = None

        self._configure_styles()
        self._build_ui()
        self._render_categories()
        self._render_grid()
        self._render_selection()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background=PAPER)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Sidebar.TFrame", background="#e8eeeb")
        style.configure("TLabel", background=PAPER, foreground=INK, font=("TkDefaultFont", 10))
        style.configure("Muted.TLabel", background=PAPER, foreground=MUTED, font=("TkDefaultFont", 9))
        style.configure("Panel.TLabel", background=PANEL, foreground=INK, font=("TkDefaultFont", 10))
        style.configure("Heading.TLabel", background=PAPER, foreground=INK, font=("Georgia", 25))
        style.configure("Selected.TLabel", background="#f8faf9", foreground=INK)
        style.configure("TButton", padding=(8, 6), font=("TkDefaultFont", 9))
        style.configure("Mode.TButton", padding=(12, 8))
        style.configure("Action.TButton", background=CORAL, foreground=INK, padding=(10, 9), font=("TkDefaultFont", 10, "bold"))
        style.map("Action.TButton", background=[("active", "#ff8e7c")])
        style.configure("Category.TButton", anchor="w", background="#e8eeeb", borderwidth=0, padding=(9, 8))
        style.map("Category.TButton", background=[("active", "#ffffff"), ("selected", DEEP)], foreground=[("selected", "#ffffff")])
        style.configure("Search.TEntry", padding=(10, 8), fieldbackground="#f8faf9")

    def _build_ui(self):
        header = tk.Frame(self.root, bg=PAPER, height=58, highlightthickness=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        brand = tk.Frame(header, bg=PAPER)
        brand.pack(side="left", padx=24, pady=14)
        tk.Label(brand, text="g", bg=CORAL, fg=INK, font=("Georgia", 17, "bold"), width=2).pack(side="left", padx=(0, 10))
        tk.Label(brand, text="GLYPH INDEX", bg=PAPER, fg=INK, font=("TkDefaultFont", 10, "bold")).pack(side="left")
        tk.Label(header, text="A CHARACTER MAP FOR THE CURIOUS", bg=PAPER, fg=MUTED, font=MONO).pack(side="right", padx=24)
        tk.Frame(self.root, bg=INK, height=1).pack(fill="x")

        main = ttk.Frame(self.root, padding=(24, 21, 24, 22))
        main.pack(fill="both", expand=True)
        intro = ttk.Frame(main)
        intro.pack(fill="x", pady=(0, 17))
        intro_copy = ttk.Frame(intro)
        intro_copy.pack(side="left")
        ttk.Label(intro_copy, text="Character map", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(intro_copy, text="Find a character. Put it where you need it.", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
        self.total_label = ttk.Label(intro, text="", foreground=DEEP, font=MONO)
        self.total_label.pack(side="right", anchor="s", pady=(0, 3))

        controls = tk.Frame(main, bg=PANEL, highlightbackground=INK, highlightthickness=1, padx=12, pady=10)
        controls.pack(fill="x", pady=(0, 13))
        search_wrap = tk.Frame(controls, bg="#f8faf9", highlightbackground=LINE, highlightthickness=1)
        search_wrap.pack(side="left", fill="x", expand=True, padx=(0, 14))
        tk.Label(search_wrap, text="⌕", bg="#f8faf9", fg=MUTED, font=("TkDefaultFont", 16)).pack(side="left", padx=(9, 2))
        search_entry = ttk.Entry(search_wrap, textvariable=self.query, style="Search.TEntry")
        search_entry.pack(side="left", fill="x", expand=True, padx=(2, 8), pady=2)
        search_entry.bind("<KeyRelease>", lambda _event: self._render_grid())
        search_entry.bind("<Escape>", self._clear_search)
        mode_frame = tk.Frame(controls, bg=PAPER, highlightbackground=INK, highlightthickness=1, padx=3, pady=3)
        mode_frame.pack(side="right")
        self.copy_mode_button = ttk.Button(mode_frame, text="Copy on click", style="Mode.TButton", command=lambda: self._set_mode("copy"))
        self.insert_mode_button = ttk.Button(mode_frame, text="Insert into text", style="Mode.TButton", command=lambda: self._set_mode("insert"))
        self.copy_mode_button.pack(side="left")
        self.insert_mode_button.pack(side="left")

        workspace = tk.Frame(main, bg=PANEL, highlightbackground=INK, highlightthickness=1)
        workspace.pack(fill="both", expand=True)
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)
        self._build_sidebar(workspace)
        self._build_browser(workspace)
        self._build_inspector(workspace)

        self.status = tk.StringVar(value="Ready")
        status = ttk.Label(main, textvariable=self.status, style="Muted.TLabel", anchor="w")
        status.pack(fill="x", pady=(7, 0))

    def _build_sidebar(self, parent):
        self.sidebar = tk.Frame(parent, bg="#e8eeeb", width=190, padx=10, pady=14, highlightbackground=INK, highlightthickness=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        tk.Label(self.sidebar, text="BROWSE COLLECTION", bg="#e8eeeb", fg=MUTED, font=("TkFixedFont", 8)).pack(anchor="w", padx=8, pady=(0, 9))
        self.category_container = tk.Frame(self.sidebar, bg="#e8eeeb")
        self.category_container.pack(fill="both", expand=True)

    def _build_browser(self, parent):
        self.browser = tk.Frame(parent, bg=PANEL, padx=17, pady=15)
        self.browser.grid(row=0, column=1, sticky="nsew")
        self.browser.grid_columnconfigure(0, weight=1)
        self.browser.grid_rowconfigure(1, weight=1)
        heading = tk.Frame(self.browser, bg=PANEL)
        heading.grid(row=0, column=0, sticky="ew")
        self.collection_title = tk.Label(heading, text="", bg=PANEL, fg=INK, font=("Georgia", 17))
        self.collection_title.pack(anchor="w")
        self.range_label = tk.Label(heading, text="", bg=PANEL, fg=MUTED, font=("TkFixedFont", 8))
        self.range_label.pack(anchor="w", pady=(3, 10))
        self.visible_label = tk.Label(heading, text="", bg=PANEL, fg=MUTED, font=("TkFixedFont", 8))
        self.visible_label.pack(anchor="e", pady=(0, 4))
        self.grid_frame = tk.Frame(self.browser, bg=PANEL)
        self.grid_frame.grid(row=1, column=0, sticky="new")
        for column in range(10):
            self.grid_frame.grid_columnconfigure(column, weight=1, uniform="glyph")

    def _build_inspector(self, parent):
        self.inspector = tk.Frame(parent, bg="#f8faf9", width=285, highlightbackground=INK, highlightthickness=1)
        self.inspector.grid(row=0, column=2, sticky="nsew")
        self.inspector.grid_propagate(False)
        selected = tk.Frame(self.inspector, bg="#f8faf9", padx=15, pady=14)
        selected.pack(fill="x")
        top = tk.Frame(selected, bg="#f8faf9")
        top.pack(fill="x")
        tk.Label(top, text="SELECTED CHARACTER", bg="#f8faf9", fg=MUTED, font=("TkFixedFont", 8)).pack(side="left")
        self.favorite_button = tk.Button(top, text="☆", command=self._toggle_favorite, bg=PANEL, fg=INK, activebackground=YELLOW, relief="solid", bd=1, width=2, cursor="hand2")
        self.favorite_button.pack(side="right")
        self.selected_glyph = tk.Label(selected, text="A", bg="#f8faf9", fg=INK, font=("Georgia", 78), height=2)
        self.selected_glyph.pack(fill="x")
        meta = tk.Frame(selected, bg="#f8faf9", highlightbackground=LINE, highlightthickness=1)
        meta.pack(fill="x", pady=(2, 0))
        self.selected_code = tk.Label(meta, text="", bg="#f8faf9", fg=INK, font=MONO)
        self.selected_code.pack(side="left", padx=7, pady=6)
        self.selected_decimal = tk.Label(meta, text="", bg="#f8faf9", fg=MUTED, font=("TkFixedFont", 8))
        self.selected_decimal.pack(side="right", padx=7, pady=6)
        self.action_button = ttk.Button(selected, text="Copy character", style="Action.TButton", command=self._perform_primary_action)
        self.action_button.pack(fill="x", pady=(11, 0))

        tk.Frame(self.inspector, bg=INK, height=1).pack(fill="x")
        composer = tk.Frame(self.inspector, bg=PANEL, padx=14, pady=13)
        composer.pack(fill="both", expand=True)
        label = tk.Frame(composer, bg=PANEL)
        label.pack(fill="x", pady=(0, 8))
        tk.Label(label, text="Your text", bg=PANEL, fg=INK, font=("TkDefaultFont", 10, "bold")).pack(side="left")
        tk.Label(label, text="INSERT TARGET", bg=PANEL, fg=MUTED, font=("TkFixedFont", 7)).pack(side="right")
        self.compose_text = tk.Text(composer, wrap="word", undo=True, height=9, bd=1, relief="solid", highlightthickness=1, highlightbackground=LINE, highlightcolor=DEEP, padx=9, pady=8, font=MONO)
        self.compose_text.pack(fill="both", expand=True)
        self.compose_text.bind("<KeyRelease>", self._update_character_count)
        self.compose_text.bind("<<Paste>>", self._update_character_count)
        footer = tk.Frame(composer, bg=PANEL)
        footer.pack(fill="x", pady=(7, 0))
        self.character_count = tk.Label(footer, text="0 characters", bg=PANEL, fg=MUTED, font=("TkFixedFont", 8))
        self.character_count.pack(side="left")
        tk.Button(footer, text="Clear text", command=self._clear_text, bg=PANEL, fg=DEEP, relief="flat", cursor="hand2", font=("TkFixedFont", 8, "underline")).pack(side="right")

    def _load_favorites(self):
        path = Path.home() / ".config" / "glyph-index" / "favorites.json"
        try:
            values = json.loads(path.read_text(encoding="utf-8"))
            return [int(value) for value in values if isinstance(value, int)]
        except (OSError, ValueError, TypeError):
            return []

    def _save_favorites(self):
        path = Path.home() / ".config" / "glyph-index" / "favorites.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.favorites), encoding="utf-8")
        except OSError:
            self.status.set("Could not save favorites")

    def _characters_for(self, category):
        if category.get("special") == "favorites":
            return self.favorites[:]
        if category.get("special") == "recent":
            return self.recent[:]
        result = []
        for codepoint in range(category["start"], category["end"] + 1):
            if unicodedata.category(chr(codepoint)) != "Cn":
                result.append(codepoint)
        return result

    def _render_categories(self):
        for child in self.category_container.winfo_children():
            child.destroy()
        for index, category in enumerate(CATEGORIES):
            if index == 10:
                tk.Frame(self.category_container, bg=LINE, height=1).pack(fill="x", padx=8, pady=9)
            active = category["id"] == self.active_category["id"]
            button = tk.Button(
                self.category_container,
                text=f'{category["name"]}  {len(self._characters_for(category))}',
                command=lambda selected=category: self._select_category(selected),
                anchor="w", padx=9, pady=7, relief="flat", bd=0, cursor="hand2",
                bg=DEEP if active else "#e8eeeb", fg="#ffffff" if active else INK,
                activebackground=DEEP if active else PANEL,
                activeforeground="#ffffff" if active else INK,
                font=("TkDefaultFont", 9),
            )
            button.pack(fill="x", pady=1)

    def _select_category(self, category):
        self.active_category = category
        self._render_categories()
        self._render_grid()

    def _render_grid(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.glyph_buttons.clear()
        points = self._characters_for(self.active_category)
        query = self.query.get().strip().lower()
        if query:
            query_hex = query.removeprefix("u+")
            points = [point for point in points if self._matches_search(point, query, query_hex)]
        category = self.active_category
        self.collection_title.configure(text=category["name"])
        if "start" in category:
            self.range_label.configure(text=f'{code_label(category["start"])}–{code_label(category["end"])}')
        else:
            self.range_label.configure(text=f"{len(points)} saved characters")
        self.visible_label.configure(text=f"{len(points)} shown")
        if not points:
            tk.Label(self.grid_frame, text="No characters match that search.", bg=PANEL, fg=MUTED, font=("TkDefaultFont", 10)).grid(row=0, column=0, columnspan=10, pady=38)
            return
        for index, point in enumerate(points):
            row, column = divmod(index, 10)
            character = chr(point)
            active = point == self.selected_codepoint
            button = tk.Button(
                self.grid_frame,
                text=f"{character}\n{point:X}",
                command=lambda selected=point: self._activate_character(selected),
                bg=YELLOW if active else PANEL,
                fg=INK,
                activebackground=MINT,
                activeforeground=INK,
                relief="solid",
                bd=2 if active else 1,
                highlightthickness=0,
                font=("Georgia", 16),
                cursor="hand2",
                takefocus=True,
                width=4,
                height=2,
            )
            button.grid(row=row, column=column, sticky="nsew", padx=2, pady=2)
            button.bind("<Enter>", lambda _event, glyph=character, code=point: self.status.set(f"{character_name(glyph).title()} · {code_label(code)}"))
            button.bind("<Leave>", lambda _event: self.status.set("Ready"))
            button.bind("<KeyPress-Right>", lambda event, i=index: self._move_grid_focus(event, points, i, 1))
            button.bind("<KeyPress-Left>", lambda event, i=index: self._move_grid_focus(event, points, i, -1))
            button.bind("<KeyPress-Down>", lambda event, i=index: self._move_grid_focus(event, points, i, 10))
            button.bind("<KeyPress-Up>", lambda event, i=index: self._move_grid_focus(event, points, i, -10))
            self.glyph_buttons[point] = button

    def _matches_search(self, point, query, query_hex):
        character = chr(point)
        name = unicodedata.name(character, "").lower()
        hexadecimal = f"{point:x}"
        decimal = str(point)
        return query in character.lower() or query in name or query_hex in hexadecimal or query in decimal

    def _move_grid_focus(self, event, points, current, offset):
        next_index = current + offset
        if 0 <= next_index < len(points):
            self.glyph_buttons[points[next_index]].focus_set()
        return "break"

    def _activate_character(self, codepoint):
        self.selected_codepoint = codepoint
        self.recent = [point for point in self.recent if point != codepoint]
        self.recent.insert(0, codepoint)
        self.recent = self.recent[:24]
        self._render_selection()
        button = self.glyph_buttons.get(codepoint)
        if button:
            button.configure(bg=YELLOW, bd=2)
        if self.mode.get() == "copy":
            self._copy_character()
        else:
            self._insert_character()
        if self.active_category.get("special") == "recent":
            self._render_grid()
        self._render_categories()

    def _render_selection(self):
        character = chr(self.selected_codepoint)
        self.selected_glyph.configure(text=character)
        self.selected_code.configure(text=code_label(self.selected_codepoint))
        self.selected_decimal.configure(text=f"Decimal {self.selected_codepoint}")
        favorite = self.selected_codepoint in self.favorites
        self.favorite_button.configure(text="★" if favorite else "☆", bg="#ffe1d9" if favorite else PANEL, fg="#b35335" if favorite else INK, command=self._toggle_favorite)
        self.action_button.configure(text="Copy character" if self.mode.get() == "copy" else "Insert at cursor")

    def _set_mode(self, mode):
        self.mode.set(mode)
        self.copy_mode_button.configure(style="Mode.TButton" if mode != "copy" else "Selected.Mode.TButton")
        self.insert_mode_button.configure(style="Mode.TButton" if mode != "insert" else "Selected.Mode.TButton")
        self.root.style = ttk.Style(self.root)
        self.root.style.configure("Selected.Mode.TButton", background=INK, foreground="#ffffff", padding=(12, 8))
        self.root.style.map("Selected.Mode.TButton", background=[("active", INK)])
        self._render_selection()
        self._render_grid()

    def _toggle_favorite(self):
        if self.selected_codepoint in self.favorites:
            self.favorites.remove(self.selected_codepoint)
        else:
            self.favorites.insert(0, self.selected_codepoint)
        self._save_favorites()
        self._render_categories()
        self._render_selection()
        if self.active_category.get("special") == "favorites":
            self._render_grid()

    def _copy_character(self):
        character = chr(self.selected_codepoint)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(character)
            self.root.update()
            self._notify(f"Copied {code_label(self.selected_codepoint)}")
        except tk.TclError:
            self._notify("Could not access the system clipboard")

    def _insert_character(self):
        character = chr(self.selected_codepoint)
        try:
            self.compose_text.insert("insert", character)
            self.compose_text.focus_set()
            self._update_character_count()
            self._notify(f"Inserted {code_label(self.selected_codepoint)}")
        except tk.TclError:
            self._notify("Could not insert the selected character")

    def _perform_primary_action(self):
        if self.mode.get() == "copy":
            self._copy_character()
        else:
            self._insert_character()

    def _update_character_count(self, _event=None):
        text = self.compose_text.get("1.0", "end-1c")
        count = len(text)
        self.character_count.configure(text=f"{count} {'character' if count == 1 else 'characters'}")

    def _clear_text(self):
        self.compose_text.delete("1.0", "end")
        self.compose_text.focus_set()
        self._update_character_count()

    def _clear_search(self, _event=None):
        self.query.set("")
        self._render_grid()
        return "break"

    def _notify(self, message):
        self.status.set(message)
        if self.toast_job:
            self.root.after_cancel(self.toast_job)
        self.toast_job = self.root.after(1800, lambda: self.status.set("Ready"))


if __name__ == "__main__":
    app_root = tk.Tk()
    GlyphIndex(app_root)
    app_root.mainloop()