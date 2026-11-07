"""Small wrappers around this program's private adb + emulator."""
from __future__ import annotations

import re
import shlex
import subprocess
import time
from pathlib import Path

from . import config as C


class ToolError(RuntimeError):
    pass


def run(cmd: list[str], check: bool = True, timeout: float | None = 120, input: str | None = None,
        cwd: Path | None = None) -> str:
    # Never let child tools (adb shell reads stdin!) consume what the user types in our menu.
    stdin = {} if input is not None else {"stdin": subprocess.DEVNULL}
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=input, cwd=cwd,
                           env=C.android_env(), encoding="utf-8", errors="replace", **stdin)
    except FileNotFoundError as e:
        raise ToolError(f"Missing program: {cmd[0]}") from e
    except subprocess.TimeoutExpired as e:
        raise ToolError(f"Timed out after {timeout:.0f}s: {Path(cmd[0]).name} {' '.join(cmd[1:3])}") from e
    if check and p.returncode != 0:
        raise ToolError(f"{Path(cmd[0]).name} {' '.join(cmd[1:3])} failed:\n{(p.stderr or p.stdout).strip()[-600:]}")
    return p.stdout


def adb(*args: str, check: bool = True, timeout: float | None = 120) -> str:
    return run([str(C.adb_path()), "-s", C.SERIAL, *args], check=check, timeout=timeout)


def shell(cmd: str, timeout: float | None = 60) -> str:
    return adb("shell", cmd, check=False, timeout=timeout).replace("\r", "")


def is_running() -> bool:
    if not C.adb_path().exists():
        return False
    out = run([str(C.adb_path()), "devices"], check=False, timeout=20)
    return any(line.split()[:2] == [C.SERIAL, "device"] for line in out.splitlines())


def _log_tail() -> str:
    try:
        lines = C.EMULATOR_LOG.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    bad = [l for l in lines if l.startswith(("FATAL", "ERROR"))]
    return "\n".join((bad or lines)[-4:])


def wait_boot(proc: subprocess.Popen | None = None, timeout: int = 600) -> None:
    end = time.time() + timeout
    while time.time() < end:
        if proc is not None and proc.poll() is not None:
            raise ToolError(f"The phone emulator stopped while starting:\n{_log_tail()}")
        if is_running() and shell("getprop sys.boot_completed", timeout=20).strip() == "1":
            return
        time.sleep(3)
    raise ToolError(f"The phone emulator did not finish starting within {timeout // 60} minutes.")


def start_emulator() -> None:
    if is_running():
        return
    C.APP_DIR.mkdir(parents=True, exist_ok=True)
    args = [str(C.emulator_path()), "-avd", C.AVD_NAME, "-port", C.CONSOLE_PORT,
            "-no-snapshot", "-no-boot-anim", "-no-audio"]
    kw = ({"creationflags": 0x00000008 | 0x00000200} if C.IS_WINDOWS  # detached, new process group
          else {"start_new_session": True})
    for attempt in range(12):
        with open(C.EMULATOR_LOG, "w", encoding="utf-8") as log:
            proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    env=C.android_env(), **kw)
        try:
            wait_boot(proc)
            break
        except ToolError:
            # A previous run may still be shutting down and holding the phone's lock: wait and retry.
            if "multiple emulators with the same AVD" not in _log_tail() or attempt == 11:
                raise
            time.sleep(5)
    shell("settings put system screen_off_timeout 2147483647")


def stop_all() -> None:
    """Shut down the emulator and this program's own adb server (port 5038 only)."""
    if is_running():
        adb("emu", "kill", check=False, timeout=30)
        for _ in range(40):
            if not is_running():
                break
            time.sleep(1)
    if C.adb_path().exists():
        run([str(C.adb_path()), "kill-server"], check=False, timeout=20)


def package_version(pkg: str) -> str | None:
    m = re.search(r"versionName=(\S+)", shell(f"dumpsys package {pkg}"))
    return m.group(1) if m else None


def launch(pkg: str) -> None:
    shell(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")


def module_active(timeout: int = 60) -> bool:
    """Start TikTok fresh and wait for TikProfileBanner's log line."""
    adb("logcat", "-c", check=False)
    shell(f"am force-stop {C.TIKTOK_PKG}")
    launch(C.TIKTOK_PKG)
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(2)
        if C.MODULE_HOOK_LOG in adb("logcat", "-d", check=False, timeout=60):
            return True
    return False


def media_scan(device_path: str) -> None:
    shell("am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d " + shlex.quote("file://" + device_path))


def in_gallery(name: str) -> bool:
    where = shlex.quote(f"_display_name='{name}'") if "'" not in name else shlex.quote(f'_display_name="{name}"')
    out = shell(f"content query --uri content://media/external/images/media --projection _display_name --where {where}")
    return "Row:" in out


def push_image(src: Path, name: str) -> None:
    shell(f"mkdir -p {C.DEVICE_ALBUM}")
    adb("push", str(src), f"{C.DEVICE_ALBUM}/{name}", timeout=300)
    media_scan(f"{C.DEVICE_ALBUM}/{name}")
