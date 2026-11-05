# Glyph Index

A desktop character map with named Unicode collections, cross-collection name and code-point search, recent characters, and favorites. Select a character to copy it, or switch to insert mode to place it at the caret in the built-in text editor. Combining marks are previewed on a dotted circle and inserted without it.

## Run

Requires Python 3 with Tkinter installed.

```sh
python3 main.py
```

## Build for Windows

On Windows, run `build_windows.bat` to create `dist\GlyphIndex.exe`. The script installs PyInstaller if needed. Python 3 with the Python Launcher (`py`) must be installed.

GitHub Actions also builds the Windows executable on pushes, pull requests, and manual workflow runs. Download `GlyphIndex.exe` from the `glyph-index-windows` workflow artifact.
