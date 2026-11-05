import tkinter as tk
from tkinter import ttk

import characters


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

class GlyphIndex:
    def __init__(self, root):
        self.root = root
        self.root.title("Glyph Index — Character Map")
        self.root.geometry("1180x780")
        self.root.minsize(840, 620)
        self.root.configure(bg=PAPER)

        self.selected_character = "A"
        self.mode = tk.StringVar(value="copy")
        self.query = tk.StringVar()
        self.favorites = characters.favorites()
        self.recent = characters.recent()
        default_set = "Recently used" if self.recent else "Basic Latin"
        self.active_category = tk.StringVar(value=default_set)
        self.glyph_buttons = {}
        self.toast_job = None

        self._configure_styles()
        self._build_ui()
        self._set_mode("copy")
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
        collection_count = len(characters.SET_NAMES) - 2
        searchable_count = len(characters.all_characters())
        self.total_label = ttk.Label(
            intro,
            text=f"{collection_count} SETS · {searchable_count:,} CHARACTERS",
            foreground=DEEP,
            font=MONO,
        )
        self.total_label.pack(side="right", anchor="s", pady=(0, 3))

        controls = tk.Frame(main, bg=PANEL, highlightbackground=INK, highlightthickness=1, padx=12, pady=10)
        controls.pack(fill="x", pady=(0, 13))
        self.category_picker = ttk.Combobox(
            controls,
            textvariable=self.active_category,
            values=characters.SET_NAMES,
            state="readonly",
            width=22,
        )
        self.category_picker.pack(side="left", padx=(0, 10))
        self.category_picker.bind("<<ComboboxSelected>>", lambda _event: self._render_grid())
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
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(0, weight=1)
        self._build_browser(workspace)
        self._build_inspector(workspace)

        self.status = tk.StringVar(value="Ready")
        status = ttk.Label(main, textvariable=self.status, style="Muted.TLabel", anchor="w")
        status.pack(fill="x", pady=(7, 0))

    def _build_browser(self, parent):
        self.browser = tk.Frame(parent, bg=PANEL, padx=17, pady=15)
        self.browser.grid(row=0, column=0, sticky="nsew")
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
        grid_area = tk.Frame(self.browser, bg=PANEL)
        grid_area.grid(row=1, column=0, sticky="nsew")
        grid_area.grid_rowconfigure(0, weight=1)
        grid_area.grid_columnconfigure(0, weight=1)
        self.grid_canvas = tk.Canvas(grid_area, bg=PANEL, bd=0, highlightthickness=0)
        self.grid_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(grid_area, orient="vertical", command=self.grid_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_canvas.configure(yscrollcommand=scrollbar.set)
        self.grid_frame = tk.Frame(self.grid_canvas, bg=PANEL)
        self.grid_window = self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda _event: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))
        self.grid_canvas.bind("<Configure>", lambda event: self.grid_canvas.itemconfigure(self.grid_window, width=event.width))
        self.grid_canvas.bind_all("<MouseWheel>", self._scroll_grid)
        self.grid_canvas.bind_all("<Button-4>", self._scroll_grid)
        self.grid_canvas.bind_all("<Button-5>", self._scroll_grid)
        for column in range(10):
            self.grid_frame.grid_columnconfigure(column, weight=1, uniform="glyph")

    def _build_inspector(self, parent):
        self.inspector = tk.Frame(parent, bg="#f8faf9", width=285, highlightbackground=INK, highlightthickness=1)
        self.inspector.grid(row=0, column=1, sticky="nsew")
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
        self.selected_decimal = tk.Label(meta, text="", bg="#f8faf9", fg=MUTED, font=("TkFixedFont", 8), wraplength=170, justify="right")
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

    def _render_grid(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.glyph_buttons.clear()
        query = self.query.get().strip().lower()
        if query:
            points = characters.search(query)
            self.collection_title.configure(text="Search results")
            self.range_label.configure(text="Unicode names and code points across all sets")
        else:
            set_name = self.active_category.get()
            points = characters.characters_for(set_name, self.recent, self.favorites)
            self.collection_title.configure(text=set_name)
            self.range_label.configure(text=f"{len(points)} characters · hover for Unicode name")
        self.visible_label.configure(text=f"{len(points)} shown")
        self.grid_canvas.yview_moveto(0)
        if not points:
            tk.Label(self.grid_frame, text="No characters match that search.", bg=PANEL, fg=MUTED, font=("TkDefaultFont", 10)).grid(row=0, column=0, columnspan=10, pady=38)
            return
        for index, shown in enumerate(points):
            row, column = divmod(index, 10)
            code = " ".join(f"{ord(character):04X}" for character in characters.as_typed(shown))
            active = shown == self.selected_character
            button = tk.Button(
                self.grid_frame,
                text=f"{shown}\n{code}",
                command=lambda selected=shown: self._activate_character(selected),
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
            button.bind("<Enter>", lambda _event, glyph=shown: self.status.set(f"{characters.name(glyph)} · {characters.code_label(glyph)}"))
            button.bind("<Leave>", lambda _event: self.status.set("Ready"))
            button.bind("<KeyPress-Right>", lambda event, i=index: self._move_grid_focus(event, points, i, 1))
            button.bind("<KeyPress-Left>", lambda event, i=index: self._move_grid_focus(event, points, i, -1))
            button.bind("<KeyPress-Down>", lambda event, i=index: self._move_grid_focus(event, points, i, 10))
            button.bind("<KeyPress-Up>", lambda event, i=index: self._move_grid_focus(event, points, i, -10))
            self.glyph_buttons[shown] = button

    def _scroll_grid(self, event):
        if getattr(event, "num", None) == 4:
            units = -3
        elif getattr(event, "num", None) == 5:
            units = 3
        else:
            units = -1 if event.delta > 0 else 1
        self.grid_canvas.yview_scroll(units, "units")
        return "break"

    def _move_grid_focus(self, event, points, current, offset):
        next_index = current + offset
        if 0 <= next_index < len(points):
            self.glyph_buttons[points[next_index]].focus_set()
        return "break"

    def _activate_character(self, shown):
        self.selected_character = shown
        self.recent = [character for character in self.recent if character != shown]
        self.recent.insert(0, shown)
        self.recent = self.recent[:characters.RECENT_LIMIT]
        characters.remember(shown)
        self._render_selection()
        button = self.glyph_buttons.get(shown)
        if button:
            button.configure(bg=YELLOW, bd=2)
        if self.mode.get() == "copy":
            self._copy_character()
        else:
            self._insert_character()
        if self.active_category.get() == "Recently used" and not self.query.get().strip():
            self._render_grid()

    def _render_selection(self):
        self.selected_glyph.configure(text=self.selected_character)
        self.selected_code.configure(text=characters.code_label(self.selected_character))
        self.selected_decimal.configure(text=characters.name(self.selected_character))
        favorite = self.selected_character in self.favorites
        self.favorite_button.configure(text="★" if favorite else "☆", bg="#ffe1d9" if favorite else PANEL, fg="#b35335" if favorite else INK, command=self._toggle_favorite)
        self.action_button.configure(text="Copy character" if self.mode.get() == "copy" else "Insert at cursor")

    def _set_mode(self, mode):
        self.mode.set(mode)
        self.copy_mode_button.configure(style="Mode.TButton" if mode != "copy" else "Selected.Mode.TButton")
        self.insert_mode_button.configure(style="Mode.TButton" if mode != "insert" else "Selected.Mode.TButton")
        style = ttk.Style(self.root)
        style.configure("Selected.Mode.TButton", background=INK, foreground="#ffffff", padding=(12, 8))
        style.map("Selected.Mode.TButton", background=[("active", INK)])
        self._render_selection()
        self._render_grid()

    def _toggle_favorite(self):
        if self.selected_character in self.favorites:
            self.favorites.remove(self.selected_character)
        else:
            self.favorites.insert(0, self.selected_character)
        characters.save_favorites(self.favorites)
        self._render_selection()
        if self.active_category.get() == "Favorites" and not self.query.get().strip():
            self._render_grid()

    def _copy_character(self):
        character = characters.as_typed(self.selected_character)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(character)
            self.root.update()
            self._notify(f"Copied {characters.code_label(self.selected_character)}")
        except tk.TclError:
            self._notify("Could not access the system clipboard")

    def _insert_character(self):
        character = characters.as_typed(self.selected_character)
        try:
            self.compose_text.insert("insert", character)
            self.compose_text.focus_set()
            self._update_character_count()
            self._notify(f"Inserted {characters.code_label(self.selected_character)}")
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