import tkinter as tk
from tkinter import ttk

import characters


PAPER = "#f2f4f3"
INK = "#172321"
MUTED = "#667471"
LINE = "#cbd3d0"
PANEL = "#ffffff"
MINT = "#c9efdf"

class EctypeCharmap:
    def __init__(self, root):
        self.root = root
        self.root.title("Ectype Charmap")
        self.root.geometry("500x440")
        self.root.minsize(390, 320)
        self.root.configure(bg=PAPER)

        self.query = tk.StringVar()
        self.favorites = characters.favorites()
        self.recent = characters.recent()
        default_set = "Recently used" if self.recent else "Basic Latin"
        self.active_category = tk.StringVar(value=default_set)
        self.glyph_buttons = {}
        self.columns = 10
        self.search_hint = "Find by name: macron, dot below, omega…"

        self._configure_styles()
        self._build_ui()
        self._render_grid()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background=PAPER)
        style.configure("TLabel", background=PAPER, foreground=INK, font=("TkDefaultFont", 10))
        style.configure("Muted.TLabel", background=PAPER, foreground=MUTED, font=("TkDefaultFont", 9))
        style.configure("Search.TEntry", padding=(6, 5), fieldbackground=PANEL)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)
        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=(0, 7))
        self.category_picker = ttk.Combobox(controls, textvariable=self.active_category, values=characters.SET_NAMES, state="readonly", width=22)
        self.category_picker.pack(side="left", padx=(0, 7))
        self.category_picker.bind("<<ComboboxSelected>>", lambda _event: self._render_grid())
        self.search_entry = ttk.Entry(controls, textvariable=self.query, style="Search.TEntry")
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, self.search_hint)
        self.search_entry.configure(foreground=MUTED)
        self.search_entry.bind("<FocusIn>", self._focus_search)
        self.search_entry.bind("<FocusOut>", self._blur_search)
        self.search_entry.bind("<KeyRelease>", lambda _event: self._render_grid())
        self.search_entry.bind("<Escape>", self._clear_search)

        grid_area = tk.Frame(main, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        grid_area.pack(fill="both", expand=True)
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
        self.grid_canvas.bind("<Configure>", self._resize_grid)
        self.grid_canvas.bind_all("<MouseWheel>", self._scroll_grid)
        self.grid_canvas.bind_all("<Button-4>", self._scroll_grid)
        self.grid_canvas.bind_all("<Button-5>", self._scroll_grid)

        self.character_name = ttk.Label(main, text="Hover for Unicode name · click to copy", style="Muted.TLabel", anchor="w")
        self.character_name.pack(fill="x", pady=(6, 0))

    def _render_grid(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.glyph_buttons.clear()
        query = self.query.get().strip().lower()
        if query == self.search_hint.lower():
            query = ""
        if query:
            points = characters.search(query)
        else:
            set_name = self.active_category.get()
            points = characters.characters_for(set_name, self.recent, self.favorites)
        self.grid_canvas.yview_moveto(0)
        if not points:
            tk.Label(self.grid_frame, text="No matching characters", bg=PANEL, fg=MUTED, font=("TkDefaultFont", 10)).grid(row=0, column=0, columnspan=self.columns, pady=24)
            return
        for index, shown in enumerate(points):
            row, column = divmod(index, self.columns)
            button = tk.Button(
                self.grid_frame,
                text=shown,
                command=lambda selected=shown: self._activate_character(selected),
                bg=PANEL,
                fg=INK,
                activebackground=MINT,
                activeforeground=INK,
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=("TkDefaultFont", 17),
                cursor="hand2",
                takefocus=True,
                width=2,
                height=1,
            )
            button.grid(row=row, column=column, padx=1, pady=1)
            button.bind("<Enter>", lambda _event, glyph=shown: self.character_name.configure(text=f"{characters.name(glyph)} · {characters.code_label(glyph)}"))
            button.bind("<Leave>", lambda _event: self.character_name.configure(text="Hover for Unicode name · click to copy"))
            button.bind("<Button-3>", lambda event, glyph=shown: self._show_character_menu(event, glyph))
            button.bind("<KeyPress-Right>", lambda event, i=index: self._move_grid_focus(event, points, i, 1))
            button.bind("<KeyPress-Left>", lambda event, i=index: self._move_grid_focus(event, points, i, -1))
            button.bind("<KeyPress-Down>", lambda event, i=index: self._move_grid_focus(event, points, i, self.columns))
            button.bind("<KeyPress-Up>", lambda event, i=index: self._move_grid_focus(event, points, i, -self.columns))
            self.glyph_buttons[index] = button

    def _resize_grid(self, event):
        self.grid_canvas.itemconfigure(self.grid_window, width=event.width)
        columns = max(1, event.width // 44)
        if columns != self.columns:
            self.columns = columns
            self._render_grid()

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
            self.glyph_buttons[next_index].focus_set()
        return "break"

    def _activate_character(self, shown):
        self.recent = [character for character in self.recent if character != shown]
        self.recent.insert(0, shown)
        self.recent = self.recent[:characters.RECENT_LIMIT]
        characters.remember(shown)
        self._copy_character(shown)
        if self.active_category.get() == "Recently used" and not self._search_text():
            self._render_grid()

    def _show_character_menu(self, event, shown):
        self.context_menu = tk.Menu(self.root, tearoff=False)
        label = "Remove from Favorites" if shown in self.favorites else "Add to Favorites"
        self.context_menu.add_command(label=label, command=lambda: self._toggle_favorite(shown))
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _toggle_favorite(self, shown):
        if shown in self.favorites:
            self.favorites.remove(shown)
        else:
            self.favorites.insert(0, shown)
        characters.save_favorites(self.favorites)
        self.character_name.configure(text=f"{'Removed from' if shown not in self.favorites else 'Added to'} Favorites · {characters.name(shown)}")
        if self.active_category.get() == "Favorites" and not self._search_text():
            self._render_grid()

    def _copy_character(self, shown):
        character = characters.as_typed(shown)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(character)
            self.root.update()
            self.character_name.configure(text=f"Copied {characters.name(shown)} · {characters.code_label(shown)}")
        except tk.TclError:
            self.character_name.configure(text="Could not access the system clipboard")

    def _search_text(self):
        query = self.query.get().strip()
        return "" if query.lower() == self.search_hint.lower() else query

    def _focus_search(self, _event):
        if self.query.get() == self.search_hint:
            self.query.set("")
            self.search_entry.configure(foreground=INK)

    def _blur_search(self, _event):
        if not self.query.get().strip():
            self.query.set(self.search_hint)
            self.search_entry.configure(foreground=MUTED)
            self._render_grid()

    def _clear_search(self, _event=None):
        self.query.set("")
        self.search_entry.configure(foreground=INK)
        self._render_grid()
        return "break"


if __name__ == "__main__":
    app_root = tk.Tk()
    EctypeCharmap(app_root)
    app_root.mainloop()