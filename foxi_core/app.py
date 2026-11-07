"""Main flow: (first-time setup) -> start phone + TikTok -> menu. Every screen is redrawn below
the same fox / link / credit header (see screen.py)."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from . import android as A
from . import config as C
from . import installer
from . import screen
from . import ui

STATUS_ROWS = 1         # one summary line under the menu (keeps room for a bigger fox)


def start_tiktok() -> list[str]:
    """Boot the phone and open TikTok; returns the first status lines for the menu."""
    screen.show([screen.title("Starting the phone…"), screen.note("(the phone opens in its own window)")])
    A.start_emulator()
    screen.show([screen.ok("Phone running"), screen.title("Opening TikTok…")])
    ver = A.package_version(C.TIKTOK_PKG)
    if ver != C.TIKTOK_VERSION:
        raise A.ToolError(f"TikTok {C.TIKTOK_VERSION} is not installed (found {ver or 'nothing'}).\n"
                          "Run with --erase, then start again to rebuild.")
    if A.module_active():
        return [screen.ok("TikTok is open in the phone window, banner module active.")]
    return [screen.warn("Banner module didn't load ('Add background' may be missing): choose 2, then start foxi again.")]


def menu_body(status: list[str]) -> list[str]:
    body = [ui.WHITE("Sign in, then: ") + f"Profile → Edit profile → {ui.CYAN('Add background')} → "
            f"Upload photo → {ui.CYAN('Banners')}", "",
            f"{ui.CYAN('1')}  Add images",
            f"{ui.CYAN('2')}  Close program",
            f"{ui.PINK('3')}  Close program and erase all program data"]
    return body + ([""] + status[-STATUS_ROWS:] if status else [])


def add_images(raw: str) -> list[str]:
    """Copy dropped/pasted image files into the phone's Banners album. Returns status lines."""
    paths = ui.parse_paths(raw)
    if not paths:
        return []
    existing = set(A.shell(f"ls {C.DEVICE_ALBUM} 2>/dev/null").split("\n"))
    added: list[str] = []
    problems: list[str] = []
    for p in paths:
        path, kind = ui.check_image(p)
        if path is None:
            problems.append(kind)
            continue
        name = ui.device_name(path, existing)
        A.push_image(path, name)
        existing.add(name)
        for _ in range(5):
            if A.in_gallery(name):
                break
            time.sleep(1)
        added.append(f"{name} ({kind})")
    return [summary(added, problems)]


def summary(added: list[str], problems: list[str]) -> str:
    """One status line for the menu: what was added, and the first problem if any."""
    if not added:
        return screen.warn(problems[0] + (f" (+{len(problems) - 1} more)" if len(problems) > 1 else ""))
    what = f"Added {added[0]}" if len(added) == 1 else f"Added {len(added)} images"
    if problems:
        return screen.warn(f"{what}; skipped {len(problems)}: {problems[0]}")
    return screen.ok(f"{what} to Banners. In TikTok: Add background → Upload photo → Banners.")


def close() -> None:
    screen.show([screen.title("Shutting down the phone…"), screen.note("Your setup and TikTok sign-in are kept.")])
    A.stop_all()
    screen.show([screen.ok("Closed. Start foxi again any time:  python3 foxi.py")])


def erase() -> bool:
    screen.show([screen.warn(f"This deletes {C.APP_DIR}"),
                 screen.note("the phone, its TikTok sign-in, imported images, downloads and settings."),
                 screen.note("Nothing outside that folder is touched (the apk folder is kept)."), ""])
    if ui.ask("Type ERASE to confirm (anything else cancels): ").strip().upper() != "ERASE":
        return False
    screen.show([screen.title("Signing out of TikTok on the phone and shutting down…")])
    if A.is_running():
        A.shell(f"am force-stop {C.TIKTOK_PKG}")
        A.shell(f"pm clear {C.TIKTOK_PKG}")
    A.stop_all()
    remove_app_dir()
    screen.show([screen.ok("All program data erased. The next start is a fresh first-time setup.")])
    return True


def remove_app_dir() -> None:
    target = C.APP_DIR.resolve()
    home = Path.home().resolve()
    # Safety: only ever delete our own dedicated folder, never home, a root, or the project folder
    if (target in (home, Path(target.anchor)) or home.is_relative_to(target)
            or C.PROJECT_DIR.is_relative_to(target) or not (target / "state.json").exists()):
        raise A.ToolError(f"Refusing to delete {target}: it doesn't look like foxi's data folder.")
    for _ in range(5):  # Windows may hold file locks for a moment after the emulator exits
        shutil.rmtree(target, ignore_errors=True)
        if not target.exists():
            return
        time.sleep(2)
    raise A.ToolError(f"Some files in {target} could not be deleted.\nClose other programs and delete it manually.")


def fail(message: str) -> None:
    """Final screen for an error: stays visible, with what to do next."""
    lines = [screen.warn(l) for l in message.splitlines() if l.strip()][:4]
    screen.show(lines + ["",
                         screen.note("Run  python3 foxi.py  again to retry; finished steps are skipped."),
                         screen.note("To start over from nothing:  python3 foxi.py --erase")])


def main() -> int:
    if sys.version_info < (3, 9):
        print("foxi needs Python 3.9 or newer.")
        return 1
    screen.enter()
    try:
        if "--erase" in sys.argv[1:]:  # escape hatch if setup can't finish
            if not C.APP_DIR.exists():
                screen.show([screen.ok("Nothing to erase.")])
                return 0
            return 0 if erase() else 1
        if not installer.is_ready():
            installer.run_setup()
        status = start_tiktok()
        while True:
            screen.show(menu_body(status))
            choice = ui.ask("Choose 1, 2 or 3: ").strip()
            if choice == "1":
                screen.show([screen.title("Add images"),
                             screen.note("Drag image files into this window (or paste a path), then press Enter."),
                             screen.note("JPG, PNG, WebP or HEIC. Press Enter on an empty line to go back."), ""])
                status = add_images(ui.ask("Image: "))
            elif choice == "2":
                close()
                return 0
            elif choice == "3":
                if erase():
                    return 0
                status = [screen.note("Erase cancelled.")]
            else:
                status = [screen.warn("Please type 1, 2 or 3.")] if choice else []
    except A.ToolError as e:
        fail(str(e))
        return 2
    except ui.InputClosed:
        close()
        return 0
    except KeyboardInterrupt:
        print()
        fail("Interrupted. The phone may still be running.\nStart foxi again and choose 2 to close it cleanly.")
        return 130
    finally:
        screen.leave()
