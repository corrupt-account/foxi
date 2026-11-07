"""One left-aligned column, redrawn for every screen:

    fox  ->  2 blank lines  ->  TIKTOK : RCFO (block letters, fox colours)  ->  tiktok.com/@rcfo
         ->  https://github.com/corrupt-account/foxi  ->  "Banner unlock by: github.com/vanquzie"
         (this header block is centred in the window)
         ->  current body (left-aligned)

The header has the same size on every screen (the fox is sized for BODY_ROWS lines of body),
so nothing jumps. Each new screen clears the terminal: no duplicated headers, no growing logs.
Fits 120 x 30; smaller windows shrink or drop the fox.
"""
from __future__ import annotations

import os
import re
import shutil
import sys

from . import fox
from . import ui

PROFILE_URL = "https://www.tiktok.com/@rcfo"
CREDIT_URL = "https://github.com/vanquzie/TikProfileBanner"   # TikProfileBanner by vanquzie, GPL-3.0
PROJECT_URL = "https://github.com/corrupt-account/foxi"       # this project
FOX_GAP = 2             # blank lines between the fox and the heading
BODY_ROWS = 8           # lines reserved under the header (tallest body incl. prompt: setup step 6)
FOX_MAX_ROWS = 15
FOX_MIN_ROWS = 6
INDENT = " "
_ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\]8;;[^\x1b\x07]*(?:\x1b\\|\x07)")


def visible_len(s: str) -> int:
    return len(_ANSI.sub("", s))


def fit(s: str, width: int) -> str:
    """Shorten plain text to `width` columns with an ellipsis in the middle."""
    if len(s) <= width:
        return s
    keep = max(1, width - 1)
    return s[: keep // 2] + "…" + s[len(s) - (keep - keep // 2):]


def size() -> tuple[int, int]:
    s = shutil.get_terminal_size(fallback=(120, 30))
    return s.columns, s.lines


def width() -> int:
    """Usable text width for body lines (never the last column, so nothing wraps)."""
    return size()[0] - 1 - len(INDENT)


def _c(code: str, s: str) -> str:
    return f"\x1b[{code}m{s}\x1b[0m" if ui.COLOUR else s


def link(text: str, url: str) -> str:
    """OSC 8 hyperlink where supported; other terminals just show the text."""
    if ui.COLOUR and os.environ.get("TERM") != "dumb" and os.environ.get("FOXI_LINKS", "1") != "0":
        return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"
    return text


# "TIKTOK : RCFO" in a 3-row block font (50 columns), shaded gold -> copper like the fox
_GLYPHS = {
    "T": ("▀█▀", " █ ", " ▀ "), "I": ("▀█▀", " █ ", "▀▀▀"), "K": ("█ ▄▀", "██▄ ", "▀  ▀"),
    "O": ("█▀▀█", "█  █", "▀▀▀▀"), ":": ("▄", " ", "▀"),
    "R": ("█▀▀█", "█▀█▀", "▀  ▀"), "C": ("█▀▀", "█  ", "▀▀▀"), "F": ("█▀▀", "█▀▀", "▀  "), " ": (" ", " ", " "),
}
HEADING = [" ".join(_GLYPHS[ch][r] for ch in "TIKTOK : RCFO") for r in range(3)]
HEADING_WIDTH = max(map(len, HEADING))
_HEADING_TONES = ((255, 196, 106), (222, 156, 92), (183, 116, 64))   # sampled from the fox's palette


def heading_rows() -> list[str]:
    return [_c("1;38;2;{};{};{}".format(*tone), row) for tone, row in zip(_HEADING_TONES, HEADING)]


def url_line() -> str:
    return link("tiktok.com/@rcfo", PROFILE_URL)                                   # plain, no colour


def project_line() -> str:
    return link(PROJECT_URL, PROJECT_URL)                                           # plain, like the TikTok link


def credit_line() -> str:
    return _c("38;2;128;132;140", "Banner unlock by: ") + _c("38;2;128;132;140", link("github.com/vanquzie", CREDIT_URL))


def header(columns: int, rows: int) -> list[str]:
    """Fox, gap, heading, URLs and credits as one block, centred in the terminal window."""
    avail = rows - BODY_ROWS - 4                          # 4 = tiktok url + project url + credit + spacer
    show_heading = avail >= len(HEADING) and HEADING_WIDTH <= columns - 1 - len(INDENT)
    fox_h = min(FOX_MAX_ROWS, avail - (len(HEADING) if show_heading else 0) - FOX_GAP)
    fox_w = round(fox_h * 2 * fox._SOURCE_W / fox._SOURCE_H)
    block: list[str] = []
    if fox_h >= FOX_MIN_ROWS and fox_w <= columns - 2:
        block += fox._art(fox_w, fox_h, ui.COLOUR) + [""] * FOX_GAP
    if show_heading:
        block += heading_rows()
    block += [url_line(), project_line(), credit_line()]
    width = HEADING_WIDTH if show_heading else max(visible_len(l) for l in block)
    usable = columns - 1                                  # never touch the last column (no wrap)
    pad = " " * max(0, (usable - width) // 2)             # block centred in the window
    return [(pad + centred(l, width)) if l else "" for l in block] + [""]


def centred(s: str, width: int) -> str:
    """Centre `s` inside a box `width` columns wide."""
    return " " * max(0, (width - visible_len(s)) // 2) + s


def render(body: list[str], columns: int, rows: int) -> list[str]:
    """Header + body; every line fits in columns-1 and the total leaves a row for the prompt."""
    usable = columns - 1
    out = header(columns, rows)
    room = max(1, rows - len(out) - 1)                     # keep one row for the prompt / cursor
    for line in body[-room:]:
        if visible_len(INDENT + line) > usable:
            line = fit(_ANSI.sub("", line), usable - len(INDENT))
        out.append(INDENT + line if line else "")
    return out


_alt = False
_last: list[str] = []


def enter() -> None:
    """Draw in the terminal's alternate screen so redraws never pile up in the scrollback."""
    global _alt
    if sys.stdout.isatty() and os.environ.get("TERM") != "dumb":
        sys.stdout.write("\x1b[?1049h")
        _alt = True


def leave() -> None:
    """Back to the normal screen, re-printing the last screen once so final messages stay visible."""
    global _alt
    if _alt:
        sys.stdout.write("\x1b[?1049l")
        _alt = False
        cols, rows = size()
        sys.stdout.write("\n".join(render(_last, cols, rows)) + "\n")
        sys.stdout.flush()


def show(body: list[str] | None = None) -> None:
    """Clear the terminal and draw header + body (when output is a terminal; else just print)."""
    global _last
    _last = list(body or [])
    cols, rows = size()
    lines = render(_last, cols, rows)
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[H\x1b[2J")
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


def say(line: str) -> None:
    """Add one line under the current screen (within the reserved body rows)."""
    print(INDENT + (fit(line, width()) if visible_len(line) == len(line) else line), flush=True)


# --- Body line helpers (plain text is fitted to the window before colouring) --------------------
def ok(text: str) -> str:
    return ui.GREEN("✓") + " " + fit(text, width() - 2)


def warn(text: str) -> str:
    return ui.PINK("!") + " " + fit(text, width() - 2)


def note(text: str) -> str:
    return ui.DIM(fit(text, width()))


def title(text: str) -> str:
    return ui.WHITE(fit(text, width()))


def step_body(n: int, total: int, text: str) -> list[str]:
    return [ui.CYAN(f"Setup {n}/{total} · ") + title(fit(text, width() - 12)), ""]
