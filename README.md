# Ectype Charmap

Ectype OCR's character pane as a desktop window of its own: the special characters scholarly books use and keyboards lack, in sets (Superscripts, Transliteration, Accented Latin, Combining marks, IPA, Greek, Hebrew, Hebrew accents, Editorial marks, Punctuation), found by Unicode name, the ones used last, and favorites.

- Point at a character to see its Unicode name; click it (or press Enter) to type it into the box at the bottom and copy it.
- Clicks type at the cursor in the box, so a combining mark (shown on a dotted circle ◌, which is not copied) lands on the letter before it. Copy (or Enter in the box) copies the whole text.
- Ω shows the characters used last. Right-click a character to add it to Favorites or copy its code point.
- The window stays on top, beside your work. Ctrl+F jumps to the search box.

## Run

Requires Python 3 and PySide6.

```sh
python3 -m pip install -r requirements.txt
python3 main.py
```

## Build for Windows

On Windows, run `build_windows.bat` to create `dist\EctypeCharmap.exe`. The script installs PyInstaller and PySide6 if needed. Python 3 with the Python Launcher (`py`) must be installed.

GitHub Actions also builds the Windows executable on pushes, pull requests, and manual workflow runs. Download `EctypeCharmap.exe` from the `ectype-charmap-windows` workflow artifact.
