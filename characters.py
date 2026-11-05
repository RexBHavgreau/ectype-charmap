import json
import os
import unicodedata
from pathlib import Path


RECENT_LIMIT = 24
DISPLAY_CIRCLE = "◌"

COLLECTIONS = {
    "Basic Latin": [(0x20, 0x7E)],
    "Latin & diacritics": [(0xA0, 0x024F), (0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF)],
    "IPA & phonetics": [(0x0250, 0x02FF), (0x1D00, 0x1D7F)],
    "Greek": [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    "Cyrillic": [(0x0400, 0x052F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F)],
    "Hebrew": [(0x0590, 0x05FF)],
    "Combining marks": [(0x0300, 0x036F), (0x1AB0, 0x1AFF), (0x1DC0, 0x1DFF), (0x20D0, 0x20FF), (0xFE20, 0xFE2F)],
    "Superscripts & subscripts": [(0x2070, 0x209F), (0x1D2C, 0x1D7F)],
    "Punctuation": [(0x2000, 0x206F), (0x2E00, 0x2E7F)],
    "Currency & letterlike": [(0x20A0, 0x20CF), (0x2100, 0x214F)],
    "Math operators": [(0x2200, 0x22FF), (0x2A00, 0x2AFF)],
    "Arrows": [(0x2190, 0x21FF), (0x27F0, 0x27FF), (0x2900, 0x297F)],
    "Box drawing & blocks": [(0x2500, 0x259F)],
    "Japanese": [(0x3000, 0x30FF), (0x31F0, 0x31FF)],
    "Symbols & emoji": [(0x2600, 0x27BF), (0x1F300, 0x1F5FF), (0x1F600, 0x1F64F), (0x1F680, 0x1F6FF), (0x1F900, 0x1F9FF), (0x1FA70, 0x1FAFF)],
}

SET_NAMES = ["Recently used", *COLLECTIONS, "Favorites"]
SEARCH_RANGES = [bounds for ranges in COLLECTIONS.values() for bounds in ranges]
SEARCH_RANGES += [(0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF), (0x1F00, 0x1FFF)]


def as_typed(shown):
    return shown.replace(DISPLAY_CIRCLE, "")


def _shown_character(character):
    if unicodedata.category(character).startswith("M"):
        return DISPLAY_CIRCLE + character
    return character


def code_label(shown):
    return " + ".join(f"U+{ord(character):04X}" for character in as_typed(shown))


def name(shown):
    names = [unicodedata.name(character, f"U+{ord(character):04X}").title() for character in as_typed(shown)]
    return " + ".join(names) or "Unnamed character"


def _characters_in_ranges(ranges):
    result = []
    seen = set()
    for start, end in ranges:
        for codepoint in range(start, end + 1):
            character = chr(codepoint)
            if unicodedata.name(character, ""):
                shown = _shown_character(character)
                if shown not in seen:
                    result.append(shown)
                    seen.add(shown)
    return result


def all_characters():
    return _characters_in_ranges(SEARCH_RANGES)


def characters_for(set_name, recent_values=None, favorite_values=None):
    if set_name == "Recently used":
        return list(recent_values or [])
    if set_name == "Favorites":
        return list(favorite_values or [])
    return _characters_in_ranges(COLLECTIONS[set_name])


def search(query, limit=500):
    words = query.casefold().split()
    if not words:
        return []
    results = []
    for shown in all_characters():
        character_name = name(shown).casefold()
        raw = as_typed(shown)
        code = " ".join(f"u+{ord(character):04x}" for character in raw)
        literal = shown.casefold()
        if (all(word in character_name for word in words)
                or query.casefold() in code
                or query.casefold() in literal):
            results.append(shown)
            if len(results) >= limit:
                break
    return results


def _data_directory():
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "Glyph Index"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "glyph-index"


def _read_list(path, key):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    if isinstance(data, dict):
        values = data.get(key, [])
    elif key == "favorites" and isinstance(data, list):
        values = data
    else:
        values = []
    result = []
    for value in values:
        if isinstance(value, int) and 0 <= value <= 0x10FFFF:
            result.append(_shown_character(chr(value)))
        elif isinstance(value, str):
            result.append(value)
    return result


def recent():
    return _read_list(_data_directory() / "characters.json", "recent")[:RECENT_LIMIT]


def remember(shown):
    path = _data_directory() / "characters.json"
    values = [shown, *[value for value in recent() if value != shown]][:RECENT_LIMIT]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"recent": values}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def favorites():
    path = _data_directory() / "characters.json"
    values = _read_list(path, "favorites")
    if values:
        return values
    legacy = Path.home() / ".config" / "glyph-index" / "favorites.json"
    return _read_list(legacy, "favorites")


def save_favorites(values):
    path = _data_directory() / "characters.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError, TypeError):
        data = {}
    data["favorites"] = values
    try:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass