"""First launch: build a private Android phone with TikTok 47.1.3 + TikProfileBanner inside APP_DIR.

Each step checks whether it is already done, so an interrupted setup resumes where it stopped.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

from . import android as A
from . import config as C
from . import ui

TOTAL = 7


# --- State --------------------------------------------------------------------------------------
def state() -> dict:
    try:
        return json.loads(C.STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(**kw) -> None:
    C.APP_DIR.mkdir(parents=True, exist_ok=True)
    C.STATE_FILE.write_text(json.dumps(state() | kw, indent=2), encoding="utf-8")


def is_ready() -> bool:
    return bool(state().get("ready")) and C.emulator_path().exists() and (C.AVD_HOME / f"{C.AVD_NAME}.avd").is_dir()


# --- Downloads ----------------------------------------------------------------------------------
def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, expected: str, algo: str = "sha256") -> Path:
    dest = C.CACHE_DIR / url.rsplit("/", 1)[-1]
    if dest.exists() and digest(dest, algo) == expected:
        return dest
    C.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "tik-rcfo-setup"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total, done = int(r.headers.get("Content-Length") or 0), 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            ui.progress(dest.name, done, total or done)
    if digest(tmp, algo) != expected:
        tmp.unlink()
        raise A.ToolError(f"Download check failed for {dest.name} (checksum mismatch). Try again later.")
    tmp.replace(dest)
    return dest


def unzip(zpath: Path, into: Path) -> None:
    """Extract keeping Unix permissions and symlinks (the emulator needs both)."""
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            target = into / info.filename
            mode = info.external_attr >> 16
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if stat.S_ISLNK(mode) and not C.IS_WINDOWS:
                if target.is_symlink() or target.exists():
                    target.unlink()
                os.symlink(z.read(info).decode(), target)
                continue
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
            if mode & 0o777 and not C.IS_WINDOWS:
                target.chmod(mode & 0o777)


def install_package(name: str, url: str, sha1: str, top: str, dest: Path) -> None:
    if dest.exists():
        return
    ui.info(f"downloading {name}")
    z = fetch(url, sha1, "sha1")
    ui.info(f"unpacking {name}")
    stage = C.SDK_DIR / ".stage"
    shutil.rmtree(stage, ignore_errors=True)
    unzip(z, stage)
    dest.parent.mkdir(parents=True, exist_ok=True)
    (stage / top).rename(dest)
    shutil.rmtree(stage, ignore_errors=True)
    z.unlink()  # keep disk use down


# --- Steps --------------------------------------------------------------------------------------
def step_check() -> None:
    ui.step(1, TOTAL, "Checking this computer")
    if C.HOST is None:
        raise A.ToolError(f"Google's Android emulator doesn't run on {C.SYSTEM} {C.MACHINE}. "
                          "Supported: macOS (Apple Silicon or Intel), Windows x64, Linux x64.")
    save_state(app="tik-rcfo")  # marks the folder as ours (checked before erasing it)
    if not C.emulator_path().exists():
        free = shutil.disk_usage(C.APP_DIR).free / 1e9
        if free < C.SETUP_FREE_GB:
            raise A.ToolError(f"First-time setup needs about {C.SETUP_FREE_GB} GB free disk space; "
                              f"this computer has {free:.1f} GB. Free some space and start again.")
    ui.ok(f"{C.SYSTEM} {C.MACHINE}, program folder: {C.APP_DIR}")


def step_sdk() -> None:
    ui.step(2, TOTAL, "Android emulator and system image (about 2.6 GB download, first time only)")
    pt, pt_sha = C.PLATFORM_TOOLS[C.SYSTEM]
    install_package("Android platform tools", C._G + pt, pt_sha, "platform-tools", C.SDK_DIR / "platform-tools")
    em, em_sha = C.EMULATOR[C.HOST]
    install_package("Android emulator", C._G + em, em_sha, "emulator", C.SDK_DIR / "emulator")
    url, sha1 = C.SYSTEM_IMAGE[C.ABI]
    install_package("Android 15 system image", url, sha1, C.ABI, C.SDK_DIR / C.SYS_IMG_REL)
    (C.SDK_DIR / "platforms").mkdir(exist_ok=True)  # the emulator expects this folder to exist
    accel = subprocess.run([str(C.emulator_path()), "-accel-check"], capture_output=True, text=True,
                           env=C.android_env(), stdin=subprocess.DEVNULL, timeout=60)
    if accel.returncode != 0:
        hint = {"Windows": "Turn on 'Windows Hypervisor Platform' in 'Turn Windows features on or off', then restart.",
                "Linux": "Enable virtualization in the BIOS and add yourself to the 'kvm' group (sudo adduser $USER kvm)."}
        raise A.ToolError("Hardware virtualization isn't available, so the phone emulator can't run.\n"
                          f"{(accel.stdout or accel.stderr).strip()[-300:]}\n{hint.get(C.SYSTEM, '')}")
    ui.ok("Android tools ready")


def step_avd() -> None:
    ui.step(3, TOTAL, "Creating the virtual phone")
    avd = C.AVD_HOME / f"{C.AVD_NAME}.avd"
    if not (avd / "config.ini").exists():
        avd.mkdir(parents=True, exist_ok=True)
        (avd / "config.ini").write_text("".join(f"{k}={v}\n" for k, v in C.AVD_CONFIG.items()), encoding="utf-8")
        (C.AVD_HOME / f"{C.AVD_NAME}.ini").write_text(
            f"avd.ini.encoding=UTF-8\npath={avd}\npath.rel=avd/{C.AVD_NAME}.avd\ntarget=android-35\n", encoding="utf-8")
    ui.ok("virtual phone ready (Galaxy S24 screen size)")


def find_tiktok_apk() -> Path:
    cached = C.CACHE_DIR / f"tiktok-{C.TIKTOK_VERSION}.apk"
    if cached.exists() and digest(cached, "sha256") == C.TIKTOK_APK_SHA256:
        return cached
    downloads = Path.home() / "Downloads"
    for p in sorted(downloads.glob("*.apk")) if downloads.is_dir() else []:
        if 400e6 < p.stat().st_size < 600e6 and digest(p, "sha256") == C.TIKTOK_APK_SHA256:
            shutil.copyfile(p, cached)
            ui.info(f"found it in Downloads: {p.name}")
            return cached
    ui.warn(f"TikTok {C.TIKTOK_VERSION} has to be downloaded by you (one time). Get the APK (not the bundle) here:")
    ui.info(ui.CYAN(C.TIKTOK_PAGE))
    while True:
        raw = ui.ask("Drag the downloaded .apk file here and press Enter: ")
        paths = ui.parse_paths(raw)
        p = ui._existing(paths[0]) if paths else None
        if p and p.is_file() and digest(p, "sha256") == C.TIKTOK_APK_SHA256:
            C.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, cached)
            return cached
        ui.warn("That isn't the official TikTok 47.1.3 APK (file missing or checksum differs). Try again.")


def step_files() -> dict[str, Path]:
    ui.step(4, TOTAL, "Downloading Magisk, Vector (LSPosed), rootAVD and TikProfileBanner")
    files = {k: fetch(u, h) for k, (u, h) in C.FILES.items()}
    ui.ok("files downloaded and checksum-verified")
    return files


def step_root(files: dict[str, Path]) -> None:
    ui.step(5, TOTAL, "Rooting the virtual phone (Magisk)")
    img = C.SDK_DIR / C.SYS_IMG_REL / "ramdisk.img"
    if state().get("rooted_ramdisk") == digest(img, "sha256"):
        ui.ok("already rooted")
        return
    work = C.WORK_DIR / "rootAVD"
    shutil.rmtree(work, ignore_errors=True)
    (work / "Apps").mkdir(parents=True)
    shutil.copyfile(files["rootavd_sh"], work / "rootAVD.sh")
    shutil.copyfile(files["rootavd_bat"], work / "rootAVD.bat")
    shutil.copyfile(files["magisk"], work / "Magisk.zip")
    (work / "rootAVD.sh").chmod(0o755)
    ui.info("starting the phone (first boot takes a few minutes)...")
    A.start_emulator()
    ui.info("patching (the phone shuts down when finished)...")
    script = ["cmd", "/c", "rootAVD.bat"] if C.IS_WINDOWS else ["bash", "./rootAVD.sh"]
    rel = C.SYS_IMG_REL.replace("/", "\\") if C.IS_WINDOWS else C.SYS_IMG_REL
    A.run([*script, f"{rel}{os.sep}ramdisk.img"], cwd=work, input="1\n\n\n", timeout=1800, check=False)
    for _ in range(60):
        if not A.is_running():
            break
        time.sleep(2)
    A.stop_all()
    new = digest(img, "sha256")
    if new == state().get("stock_ramdisk") or not (C.SDK_DIR / C.SYS_IMG_REL / "ramdisk.img.backup").exists():
        raise A.ToolError("Rooting did not complete. Start the program again to retry.")
    save_state(rooted_ramdisk=new)
    shutil.rmtree(work, ignore_errors=True)
    ui.ok("rooted")


def step_framework(files: dict[str, Path]) -> None:
    ui.step(6, TOTAL, "Installing the Vector (LSPosed) framework")
    A.start_emulator()
    if "vectord" in A.shell("ps -A"):
        ui.ok("already installed")
        return
    if not A.package_version("com.topjohnwu.magisk"):
        A.adb("install", str(files["magisk"]), timeout=300)
    target = "/sdcard/Download/Vector-v2.2.zip"
    A.adb("push", str(files["vector"]), target, timeout=300)
    A.media_scan(target)
    A.launch("com.topjohnwu.magisk")
    ui.warn("Please do this in the phone window (one time only):")
    for line in ("1. If Magisk asks for 'Additional setup', tap OK. The phone restarts; open Magisk again.",
                 "2. Tap the gear (Settings) and switch ON 'Zygisk'.",
                 "3. Modules tab -> 'Install from storage' -> Downloads -> Vector-v2.2.zip -> OK.",
                 "4. When it says Done, tap 'Reboot'."):
        ui.info(line)
    ui.wait_enter("Press Enter after the phone has restarted")
    A.wait_boot()
    time.sleep(10)
    if "vectord" not in A.shell("ps -A"):  # keep the zip on the phone so the user can retry right away
        raise A.ToolError("Vector isn't running yet. Start the program again and repeat the steps in Magisk.")
    A.shell(f"rm -f {target}")
    ui.ok("Vector running")


def open_vector_manager() -> None:
    A.shell("am start -a android.intent.action.MAIN -c org.matrix.vector.manager.LAUNCH_MANAGER "
            "com.android.shell/.BugreportWarningActivity")


def step_apps(files: dict[str, Path]) -> None:
    ui.step(7, TOTAL, f"Installing TikTok {C.TIKTOK_VERSION} and the banner module")
    ver = A.package_version(C.TIKTOK_PKG)
    if ver != C.TIKTOK_VERSION:
        apk = find_tiktok_apk()
        if ver:
            A.adb("uninstall", C.TIKTOK_PKG)
        ui.info("installing TikTok (about a minute)...")
        A.adb("install", str(apk), timeout=900)
        apk.unlink()  # 450 MB we no longer need
    if not A.package_version(C.MODULE_PKG):
        A.adb("install", str(files["module"]), timeout=300)
    while not A.module_active():
        open_vector_manager()
        ui.warn("Turn the module on in the phone window (one time only):")
        ui.info("Modules -> TikProfileBanner -> switch ON -> tick TikTok.")
        ui.wait_enter()
    ui.ok("banner module active inside TikTok")


def run_setup() -> None:
    ui.info(ui.DIM("First launch: setting everything up. Later launches start straight away."))
    step_check()
    step_sdk()
    step_avd()
    files = step_files()
    if "stock_ramdisk" not in state():
        save_state(stock_ramdisk=digest(C.SDK_DIR / C.SYS_IMG_REL / "ramdisk.img", "sha256"))
    step_root(files)
    step_framework(files)
    step_apps(files)
    save_state(ready=True)
    ui.ok("Setup complete")
