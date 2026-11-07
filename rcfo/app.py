"""Main flow: (first-time setup) -> start phone + TikTok -> menu."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from . import android as A
from . import config as C
from . import installer
from . import ui


def start_tiktok() -> None:
    ui.step(1, 2, "Starting the phone")
    A.start_emulator()
    ui.ok("phone running (see the phone window)")
    ui.step(2, 2, "Opening TikTok")
    ver = A.package_version(C.TIKTOK_PKG)
    if ver != C.TIKTOK_VERSION:
        raise A.ToolError(f"TikTok {C.TIKTOK_VERSION} is not installed (found {ver or 'nothing'}). "
                          "Choose option 3 and start again to rebuild.")
    if A.module_active():
        ui.ok("TikTok open, banner module active")
    else:
        ui.warn("TikTok is open, but the banner module did not report in. The 'Add background'")
        ui.warn("button may be missing. Restarting the program usually fixes it.")
    print()
    ui.info(ui.WHITE("Sign in to TikTok in the phone window, then go to:"))
    ui.info("Profile → Edit profile → " + ui.CYAN("Add background") + " → Upload photo → album " + ui.CYAN("Banners"))


def add_images() -> None:
    ui.info(ui.DIM("Drag image files into this window (or paste a path) and press Enter. Empty = back."))
    raw = ui.ask("Image: ")
    paths = ui.parse_paths(raw)
    if not paths:
        return
    existing = set(A.shell(f"ls {C.DEVICE_ALBUM} 2>/dev/null").split("\n"))
    added = 0
    for p in paths:
        path, kind = ui.check_image(p)
        if path is None:
            ui.warn(kind)
            continue
        name = ui.device_name(path, existing)
        A.push_image(path, name)
        existing.add(name)
        for _ in range(5):
            if A.in_gallery(name):
                break
            time.sleep(1)
        else:
            ui.warn(f"{name} copied, but the photo picker hasn't listed it yet; it should appear shortly.")
        ui.ok(f"Added {ui.WHITE(name)} ({kind}) to the {ui.CYAN('Banners')} album")
        added += 1
    if added:
        ui.info("In TikTok: Add background → Upload photo → Banners. TikTok stays open.")


def close() -> None:
    ui.info("Shutting down the phone (your sign-in and setup are kept)...")
    A.stop_all()
    ui.ok("Closed. Start the program again any time.")


def erase() -> bool:
    ui.warn(f"This deletes {C.APP_DIR} : the phone, your TikTok sign-in on it, imported images,")
    ui.warn("downloads and settings. Nothing outside that folder is touched.")
    if ui.ask("Type ERASE to confirm: ").strip().upper() != "ERASE":
        ui.info("Cancelled.")
        return False
    ui.info("Signing out of TikTok on this phone and shutting down...")
    if A.is_running():
        A.shell(f"am force-stop {C.TIKTOK_PKG}")
        A.shell(f"pm clear {C.TIKTOK_PKG}")
    A.stop_all()
    remove_app_dir()
    ui.ok("All program data erased. The next launch starts a fresh setup.")
    return True


def remove_app_dir() -> None:
    target = C.APP_DIR.resolve()
    home = Path.home().resolve()
    # Safety: only ever delete our own dedicated folder, never home or a filesystem root
    if target in (home, Path(target.anchor)) or home.is_relative_to(target) or not (target / "state.json").exists():
        raise A.ToolError(f"Refusing to delete {target}: it doesn't look like this program's folder.")
    for _ in range(5):  # Windows may hold file locks for a moment after the emulator exits
        shutil.rmtree(target, ignore_errors=True)
        if not target.exists():
            return
        time.sleep(2)
    raise A.ToolError(f"Some files in {target} could not be deleted; close other programs and delete it manually.")


def main() -> int:
    if sys.version_info < (3, 9):
        print("Tik: RCFO needs Python 3.9 or newer.")
        return 1
    ui.title()
    try:
        if "--erase" in sys.argv[1:]:  # escape hatch if setup can't finish: python3 tik_rcfo.py --erase
            if not C.APP_DIR.exists():
                ui.ok("Nothing to erase.")
                return 0
            return 0 if erase() else 1
        if not installer.is_ready():
            installer.run_setup()
            print()
        start_tiktok()
        while True:
            choice = ui.menu()
            if choice == "1":
                add_images()
            elif choice == "2":
                close()
                return 0
            elif choice == "3":
                if erase():
                    return 0
            elif choice:
                ui.warn("Please type 1, 2 or 3.")
    except A.ToolError as e:
        print()
        ui.warn(str(e))
        ui.info(ui.DIM("Run the program again to retry. To remove everything: tik_rcfo.py --erase"))
        return 2
    except ui.InputClosed:
        close()
        return 0
    except KeyboardInterrupt:
        print()
        ui.info("Interrupted. The phone keeps running; start the program again and choose 2 to close it.")
        return 130
