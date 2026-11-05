# Ectype Charmap

A compact desktop Unicode character picker with named collections, cross-collection name and code-point search, recent characters, and favorites. Hover to see a character's Unicode name and click to copy it. Combining marks are shown on a dotted circle so they are easy to identify; the circle is not copied.

## Run

Requires Python 3 with Tkinter installed.

```sh
python3 main.py
```

## Build for Windows

On Windows, run `build_windows.bat` to create `dist\EctypeCharmap.exe`. The script installs PyInstaller if needed. Python 3 with the Python Launcher (`py`) must be installed.

GitHub Actions also builds the Windows executable on pushes, pull requests, and manual workflow runs. Download `EctypeCharmap.exe` from the `ectype-charmap-windows` workflow artifact.
