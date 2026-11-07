"""Colours, input prompts, download progress and drag-and-drop path handling."""
from __future__ import annotations

import os
import re
import shlex
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from . import config as C

# --- Colours ------------------------------------------------------------------------------------
def _enable_colour() -> bool:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    if C.IS_WINDOWS:  # turn on ANSI escape handling in classic Windows consoles
        try:
            import ctypes
            k = ctypes.windll.kernel32
            h = k.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            k.GetConsoleMode(h, ctypes.byref(mode))
            k.SetConsoleMode(h, mode.value | 0x0004)
        except Exception:
            return False
    return True


COLOUR = _enable_colour()


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if COLOUR else s


CYAN = lambda s: _c("38;2;37;244;238", s)      # TikTok cyan  #25F4EE
PINK = lambda s: _c("38;2;254;44;85", s)       # TikTok red   #FE2C55
WHITE = lambda s: _c("1;97", s)
DIM = lambda s: _c("2", s)
GREEN = lambda s: _c("32", s)


def progress(label: str, done: int, total: int) -> None:
    if not sys.stdout.isatty():
        return
    width = 28
    frac = done / total if total else 0
    bar = CYAN("█" * int(frac * width)) + DIM("░" * (width - int(frac * width)))
    sys.stdout.write(f"\r {bar} {frac * 100:5.1f}%  {label[:30]:30}")
    sys.stdout.flush()
    if done >= total:
        sys.stdout.write("\n")


class InputClosed(Exception):
    """stdin was closed (Ctrl-D / piped input ran out)."""


def ask(prompt: str) -> str:
    try:
        return input(f" {PINK('›')} {prompt}")
    except EOFError:
        print()
        raise InputClosed from None


def wait_enter(prompt: str = "Press Enter when done") -> None:
    ask(f"{prompt}... ")


# --- Drag-and-drop / pasted paths ---------------------------------------------------------------
def _variants(p: str) -> list[str]:
    p = os.path.expanduser(os.path.expandvars(p))
    return list(dict.fromkeys([p, unicodedata.normalize("NFC", p), unicodedata.normalize("NFD", p)]))


def _existing(p: str) -> Path | None:
    for v in _variants(p):
        if os.path.exists(v):
            return Path(v)
    return None


def _from_uri(token: str) -> str:
    if token.lower().startswith("file://"):
        u = urlparse(token)
        path = url2pathname(unquote(u.path))
        if u.netloc and u.netloc != "localhost":  # file://server/share -> UNC
            path = f"\\\\{u.netloc}{path}"
        return path
    return token


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if s.startswith("& "):           # PowerShell sometimes prefixes a dropped path with "& "
        s = s[2:].strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1]
    return s


def parse_paths(raw: str) -> list[str]:
    """Turn whatever a terminal pastes for dropped files into path strings (not yet checked).

    Handles: plain paths, paths with spaces, 'quoted' and "quoted" paths, macOS backslash-escaped
    spaces (My\\ Photo.jpg), file:// URIs, Windows drive and UNC paths, several dropped files.
    """
    raw = raw.strip().strip("\x00")
    if not raw:
        return []
    whole = _from_uri(_strip_quotes(raw))
    if _existing(whole):                                   # one path, possibly with spaces
        return [whole]
    windowsy = C.IS_WINDOWS or re.match(r'^[\'"&\s]*([A-Za-z]:[\\/]|\\\\)', raw)
    if windowsy:                                           # backslash is a separator, not an escape
        tokens = [a or b or c for a, b, c in re.findall(r'"([^"]+)"|\'([^\']+)\'|(\S+)', raw)]
        tokens = [t for t in tokens if t != "&"]
    else:
        try:
            tokens = shlex.split(raw, posix=True)          # undoes \  escapes and quotes
        except ValueError:
            tokens = [raw]
        if len(tokens) > 1 and _existing(" ".join(tokens)):
            tokens = [" ".join(tokens)]
    return [_from_uri(t) for t in tokens] or [whole]


_MAGIC = [(b"\xff\xd8\xff", "JPEG"), (b"\x89PNG\r\n\x1a\n", "PNG")]


def sniff(path: Path) -> str | None:
    try:
        with path.open("rb") as f:
            head = f.read(16)
    except OSError:
        return None
    for sig, kind in _MAGIC:
        if head.startswith(sig):
            return kind
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "WebP"
    if head[4:8] == b"ftyp" and head[8:12] in (b"heic", b"heix", b"mif1", b"msf1", b"heim", b"heis"):
        return "HEIC"
    return None


def check_image(raw: str) -> tuple[Path | None, str]:
    """Return (path, '') for a usable image, or (None, reason)."""
    p = _existing(raw)
    if p is None:
        return None, f"File not found: {raw}"
    if p.is_dir():
        return None, f"That's a folder, not an image: {p}"
    kind = sniff(p)
    if kind is None:
        return None, f"Not a supported image (JPG, PNG, WebP or HEIC): {p.name}"
    return p, kind


def device_name(p: Path, taken: set[str]) -> str:
    """Safe file name for the phone: keeps letters (any language), digits, spaces, - _ ."""
    stem = unicodedata.normalize("NFC", p.stem)
    stem = re.sub(r"[^\w\-() ]+", "_", stem, flags=re.UNICODE).strip(" ._") or "image"
    ext = {"JPEG": ".jpg", "PNG": ".png", "WebP": ".webp", "HEIC": ".heic"}[sniff(p) or "JPEG"]
    name, i = f"{stem}{ext}", 2
    while name in taken:
        name, i = f"{stem}_{i}{ext}", i + 1
    return name
