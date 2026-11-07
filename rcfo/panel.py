"""Menu screen: fox + link + credits on the left, title / instructions / menu on the right.

Designed for a 120 x 30 terminal and redrawn (screen cleared) each time the menu is shown, with a
few status lines and the input prompt underneath, so nothing scrolls off. Narrow or short
terminals fall back to a fox-less layout.
"""
from __future__ import annotations

import os
import re
import shutil
import sys

from . import fox
from . import ui

PROFILE_URL = "https://www.tiktok.com/@rcfo"
CREDIT_URL = "https://github.com/vanquzie/TikProfileBanner"
GUTTER = 4
MARGIN = 1
STATUS_ROWS = 3            # status lines kept under the panel
_ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\]8;;[^\x1b\x07]*(?:\x1b\\|\x07)")


def visible_len(s: str) -> int:
    return len(_ANSI.sub("", s))


def fit(s: str, width: int) -> str:
    """Shorten plain text to `width` columns with an ellipsis in the middle."""
    if len(s) <= width:
        return s
    keep = max(1, width - 1)
    return s[: keep // 2] + "…" + s[len(s) - (keep - keep // 2):]


def _osc8_ok() -> bool:
    if not ui.COLOUR or os.environ.get("TERM") == "dumb":
        return False
    return os.environ.get("TIK_RCFO_LINKS", "1") != "0"


def link(text: str, url: str) -> str:
    """OSC 8 hyperlink; terminals without support show just the text."""
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\" if _osc8_ok() else text


def _c(code: str, s: str) -> str:
    return f"\x1b[{code}m{s}\x1b[0m" if ui.COLOUR else s


def left_text() -> list[str]:
    """URL + credits for the left column (plain widths: 16, 31, 25, 23)."""
    tiktok = _c("1;38;2;37;244;238", "tik") + _c("1;38;2;254;44;85", "tok")  # cyan + pink accents
    url = link(tiktok + _c("38;2;200;205;214", ".com/@rcfo"), PROFILE_URL)
    return [
        url,
        _c("2", "Banner unlock: ") + _c("2", link("TikProfileBanner", CREDIT_URL)),
        _c("2", "by vanquzie · GPL-3.0 license"),
        _c("2", link("github.com/vanquzie", CREDIT_URL)),
    ]


LEFT_PLAIN_WIDTH = 31  # widest left-column text line ("Banner unlock: TikProfileBanner")


def right_text(width: int) -> list[str]:
    rows = ui.title_rows()
    return [
        *rows,
        ui.CYAN("▔▔▔▔▔▔▔▔") + ui.PINK("▔▔▔▔▔▔▔▔▔▔▔▔") + ui.DIM("  banner helper"),
        "",
        ui.WHITE(fit("Sign in to TikTok in the phone window, then:", width)),
        fit("Profile → Edit profile → ", width - 14) + ui.CYAN("Add background"),
        "→ Upload photo → album " + ui.CYAN("Banners"),
        "",
        f"{ui.CYAN('1')}  Add images",
        f"{ui.CYAN('2')}  Close program",
        f"{ui.PINK('3')}  " + fit("Close program and erase all program data", width - 3),
    ]


def render(columns: int, rows: int, status: list[str]) -> list[str]:
    """All lines of the menu screen except the prompt. Every line fits in `columns - 1`."""
    usable = columns - 1                                   # never touch the last column (no wrap)
    budget = rows - 1 - 1 - min(len(status), STATUS_ROWS)  # prompt + blank spacer + status
    right_w = 46
    left_extra = len(left_text())
    fox_h = min(19, budget - left_extra)
    fox_w = round(fox_h * 2 * fox._SOURCE_W / fox._SOURCE_H)
    left_w = max(fox_w, LEFT_PLAIN_WIDTH)
    lines: list[str] = []
    if fox_h >= 8 and MARGIN + left_w + GUTTER + right_w <= usable:
        left = [" " * ((left_w - fox_w) // 2) + r for r in fox._art(fox_w, fox_h, ui.COLOUR)] + left_text()
        right = right_text(right_w)
        top = max(0, (fox_h - len(right)) // 2)            # centre the menu beside the fox
        for y in range(max(len(left), top + len(right))):
            l = left[y] if y < len(left) else ""
            r = right[y - top] if 0 <= y - top < len(right) else ""
            pad = " " * (left_w - visible_len(l))
            lines.append((" " * MARGIN + l + pad + " " * GUTTER + r).rstrip() if r else " " * MARGIN + l)
    else:                                                  # small window: no fox
        right = right_text(max(20, usable - 2))
        lines = [" " + r for r in right] + [""] + [" " + t for t in left_text()]
        if len(lines) > budget:                            # very short: keep instructions, menu, link
            lines = [" " + r for r in right[5:]] + [" " + left_text()[0]]
        lines = lines[-max(1, budget):]
    lines.append("")
    for s in status[-STATUS_ROWS:]:
        if visible_len(s) > usable:                        # window shrank since the message was made
            s = fit(_ANSI.sub("", s), usable)
        lines.append(s)
    return lines


def draw(status: list[str] | None = None) -> None:
    size = shutil.get_terminal_size(fallback=(120, 30))
    out = render(size.columns, size.lines, status or [])
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[H\x1b[2J")                 # cursor home + clear screen
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def _width() -> int:
    return shutil.get_terminal_size(fallback=(120, 30)).columns - 1


def ok(text: str) -> str:
    return "  " + ui.GREEN("✓") + " " + fit(text, _width() - 4)


def warn(text: str) -> str:
    return "  " + ui.PINK("!") + " " + fit(text, _width() - 4)


def note(text: str) -> str:
    return "    " + ui.DIM(fit(text, _width() - 4))
