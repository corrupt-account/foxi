#!/usr/bin/env python3
"""foxi - set a TikTok profile banner from your computer.

Run:  python3 foxi.py      (Windows: py foxi.py, or double-click)
"""
import os
import sys

if sys.version_info < (3, 9):
    sys.exit("foxi needs Python 3.9 or newer: https://www.python.org/downloads/")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rcfo.app import main  # noqa: E402

def _own_console_window() -> bool:
    """True when Windows opened a console just for us (double-click), so it would vanish on exit."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        return ctypes.windll.kernel32.GetConsoleProcessList((ctypes.c_uint * 4)(), 4) <= 2
    except Exception:
        return False


if __name__ == "__main__":
    code = main()
    if _own_console_window():
        input("\nPress Enter to close this window...")
    sys.exit(code)
