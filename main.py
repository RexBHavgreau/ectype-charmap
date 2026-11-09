"""Ectype Charmap: Ectype OCR's character pane as a window of its own.

Characters are shown in sets or found by name; a click types one into the box at the bottom,
where the cursor is (a combining mark after the letter before it), and copies it.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QPushButton, QToolButton, QVBoxLayout, QWidget,
                               QWidgetAction)

import characters

HINT = "Point at a character to see its name; click it to insert it."


class CharacterGrid(QListWidget):
    """Characters in a wrapping grid; a click (or Enter) sends the one clicked (`picked`),
    a right-click asks for its menu (`menu_requested`)."""

    picked = Signal(str)
    menu_requested = Signal(str, object)

    def __init__(self, cell: int = 44, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setUniformItemSizes(True)
        self.setGridSize(QSize(cell, cell))
        font = self.font()
        font.setPointSizeF(max(15.0, font.pointSizeF() * 1.5))
        self.setFont(font)
        self.itemClicked.connect(self._pick)
        self.itemActivated.connect(self._pick)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def _pick(self, item: QListWidgetItem) -> None:
        self.picked.emit(item.data(Qt.ItemDataRole.UserRole))

    def _menu(self, pos) -> None:
        item = self.itemAt(pos)
        if item is not None:
            self.menu_requested.emit(item.data(Qt.ItemDataRole.UserRole), self.viewport().mapToGlobal(pos))

    def show_chars(self, chars: list[str]) -> None:
        self.clear()
        for shown in chars:
            item = QListWidgetItem(shown)
            item.setData(Qt.ItemDataRole.UserRole, shown)
            item.setToolTip(characters.name(shown))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addItem(item)


class CharacterPane(QWidget):
    """A floating window of special characters (superscripts, transliteration, Hebrew points
    and accents...), in sets or found by name. It stays on top, beside the work, like
    Ectype's character pane and InDesign's Glyphs panel."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Special characters")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(460, 420)
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.sets = QComboBox()
        self.sets.addItems(characters.SET_NAMES)
        self.sets.currentIndexChanged.connect(self._show)
        row.addWidget(self.sets)
        self.find = QLineEdit()
        self.find.setPlaceholderText("Find by name: macron, dot below, superscript two…")
        self.find.setClearButtonEnabled(True)
        self.find.textChanged.connect(self._show)
        row.addWidget(self.find, 1)
        layout.addLayout(row)

        self.grid = CharacterGrid()
        self.grid.picked.connect(self.insert_char)
        self.grid.menu_requested.connect(self._character_menu)
        self.grid.itemEntered.connect(lambda item: self.name.setText(item.toolTip()))
        self.grid.setMouseTracking(True)
        layout.addWidget(self.grid, 1)

        self.name = QLabel(HINT)
        layout.addWidget(self.name)

        # The text being put together: clicks type into it at the cursor, so a combining mark
        # lands on the letter before it, as in Review's correction box.
        bottom = QHBoxLayout()
        self.special = QToolButton()
        self.special.setText("Ω")
        self.special.setToolTip("The characters used last")
        self.special.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.special_menu = QMenu(self.special)
        self.special_menu.aboutToShow.connect(self._fill_special_menu)
        self.special.setMenu(self.special_menu)
        bottom.addWidget(self.special)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Text to copy")
        self.edit.setClearButtonEnabled(True)
        font = self.edit.font()
        font.setPointSizeF(max(16.0, font.pointSizeF() * 1.6))
        self.edit.setFont(font)
        self.edit.returnPressed.connect(self.copy_text)
        bottom.addWidget(self.edit, 1)
        copy = QPushButton("Copy")
        copy.setToolTip("Copy the text in the box")
        copy.clicked.connect(self.copy_text)
        bottom.addWidget(copy)
        layout.addLayout(bottom)

        find = QAction(self)
        find.setShortcut(QKeySequence.StandardKey.Find)
        find.triggered.connect(lambda: (self.find.setFocus(), self.find.selectAll()))
        self.addAction(find)

        self.sets.setCurrentIndex(0 if characters.recent() else 1)
        self._show()

    def _show(self, *_) -> None:
        query = self.find.text().strip()
        current = self.sets.currentText()
        if query:
            self.grid.show_chars(characters.search(query))
        elif current == "Recently used":
            self.grid.show_chars(characters.recent())
        elif current == "Favorites":
            self.grid.show_chars(characters.favorites())
        else:
            self.grid.show_chars(characters.SETS[current])

    def _refresh(self, set_name: str) -> None:
        if self.sets.currentText() == set_name and not self.find.text().strip():
            self._show()

    def insert_char(self, shown: str) -> None:
        """A character typed where the cursor is in the box (a combining mark after the letter
        before it), copied, and remembered as used."""
        typed = characters.as_typed(shown)
        self.edit.insert(typed)
        QGuiApplication.clipboard().setText(typed)
        characters.remember(shown)
        self.name.setText(f"Copied {characters.name(shown)} · {characters.code_label(shown)}")
        self._refresh("Recently used")

    def copy_text(self) -> None:
        text = self.edit.text()
        if text:
            QGuiApplication.clipboard().setText(text)
            self.name.setText(f"Copied “{text}”")

    def _fill_special_menu(self) -> None:
        """The characters used last, as a grid of eight across."""
        self.special_menu.clear()
        recent = characters.recent()
        if not recent:
            self.special_menu.addAction("No characters used yet").setEnabled(False)
            return
        grid = CharacterGrid(cell=40)
        grid.show_chars(recent)
        grid.setFixedSize(8 * 40 + 8, 40 * ((len(recent) + 7) // 8) + 8)
        grid.picked.connect(lambda c: (self.special_menu.close(), self.insert_char(c)))
        holder = QWidgetAction(self.special_menu)
        holder.setDefaultWidget(grid)
        self.special_menu.addAction(holder)

    def _character_menu(self, shown: str, where) -> None:
        favorites = characters.favorites()
        menu = QMenu(self)
        if shown in favorites:
            menu.addAction("Remove from Favorites", lambda: self._set_favorite(shown, False))
        else:
            menu.addAction("Add to Favorites", lambda: self._set_favorite(shown, True))
        menu.addAction("Copy code point", lambda: QGuiApplication.clipboard().setText(characters.code_label(shown)))
        menu.exec(where)

    def _set_favorite(self, shown: str, add: bool) -> None:
        favorites = [c for c in characters.favorites() if c != shown]
        if add:
            favorites.insert(0, shown)
        characters.save_favorites(favorites)
        self.name.setText(f"{'Added to' if add else 'Removed from'} Favorites · {characters.name(shown)}")
        self._refresh("Favorites")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ectype Charmap")
    pane = CharacterPane()
    pane.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
