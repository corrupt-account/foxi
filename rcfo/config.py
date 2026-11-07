"""Paths, pinned downloads and checksums.

Everything this program creates lives under APP_DIR, so "erase all program data" is one folder.
"""
from __future__ import annotations

import os
import platform
from pathlib import Path

APP_NAME = "Tik: RCFO"
APP_DIR = Path(os.environ.get("TIK_RCFO_HOME") or Path.home() / ".tik-rcfo").expanduser()
SDK_DIR = APP_DIR / "sdk"            # private Android SDK (emulator, adb, system image)
AVD_HOME = APP_DIR / "avd"           # the emulator's virtual phone (login data lives here)
ANDROID_USER_HOME = APP_DIR / "android"  # emulator settings that would otherwise go to ~/.android
CACHE_DIR = APP_DIR / "downloads"
WORK_DIR = APP_DIR / "work"
STATE_FILE = APP_DIR / "state.json"
EMULATOR_LOG = APP_DIR / "emulator.log"

AVD_NAME = "TikRCFO"
ADB_PORT = "5038"                    # own adb server, so closing never disturbs other Android tools
CONSOLE_PORT = "5584"                # emulator console port -> serial "emulator-5584"
SERIAL = f"emulator-{CONSOLE_PORT}"

SYSTEM = platform.system()           # Darwin / Windows / Linux
IS_WINDOWS = SYSTEM == "Windows"
MACHINE = platform.machine().lower()
ABI = "arm64-v8a" if MACHINE in ("arm64", "aarch64") else "x86_64"
SYS_IMG_REL = f"system-images/android-35/google_apis_playstore/{ABI}"

# --- Android packages: official Google URLs + Google's published SHA-1 (repository2-3.xml) ------
_G = "https://dl.google.com/android/repository/"
_HOST = {("Darwin", "arm64-v8a"): "darwin_aarch64", ("Darwin", "x86_64"): "darwin_x64",
         ("Windows", "x86_64"): "windows_x64", ("Linux", "x86_64"): "linux_x64"}
HOST = _HOST.get((SYSTEM, ABI))      # None = Google ships no emulator for this computer

EMULATOR = {  # emulator 37.2.13 (tested)
    "darwin_aarch64": ("emulator-darwin_aarch64-16740729.zip", "6c5e61b873e11c7d1d08683bea089f762baee070"),
    "darwin_x64": ("emulator-darwin_x64-16740729.zip", "b0c5fdc92430079436e9aec5983f14a5499de9b0"),
    "windows_x64": ("emulator-windows_x64-16740729.zip", "4d7268aa7787c640ad892844e6c9a5f159e91ad3"),
    "linux_x64": ("emulator-linux_x64-16740729.zip", "f41f9e31eb5ca64926603c03265c50bbc0ff4172"),
}
PLATFORM_TOOLS = {  # platform-tools 37.0.1 (tested)
    "Darwin": ("platform-tools_r37.0.1-darwin.zip", "6ae73f4de6452dc57e62ec02b68eed92a4c21661"),
    "Windows": ("platform-tools_r37.0.1-win.zip", "e03e78b1d80b396f1c3358e31251cb31740e1110"),
    "Linux": ("platform-tools_r37.0.1-linux.zip", "477254aa5f903c15cf51001717bdf347fb6b53e0"),
}
SYSTEM_IMAGE = {  # Android 15 Google Play image, revision 9 (tested)
    "arm64-v8a": (_G + "sys-img/google_apis_playstore/arm64-v8a-35_r09.zip",
                  "b01416bc0bca12a85295dad179f9b8a1cae3d1e6"),
    "x86_64": (_G + "sys-img/google_apis_playstore/x86_64-35_r09.zip",
               "2f0054868e6aab3c098acd3decba17a82aed4176"),
}

# --- Root + hook framework + module (SHA-256) --------------------------------------------------
_RA = "https://gitlab.com/newbit/rootAVD/-/raw/613caa44371f85e1a461bc030e07ddc2d71afe32/"
FILES = {
    "magisk": ("https://github.com/topjohnwu/Magisk/releases/download/v31.1/Magisk-v31.1.apk",
               "89cefac0a318afa39fb3880c45c87b036c05bc1ebf02a7a715b7f8d7c26ac6e7"),
    "vector": ("https://github.com/JingMatrix/Vector/releases/download/v2.2/Vector-v2.2-3080-Release.zip",
               "9ee8323575d615f7b3f1076ff60b2a63a49390ef11881b52632311a37f6f79cc"),
    "module": ("https://github.com/vanquzie/TikProfileBanner/releases/download/v0.1.2/TikProfileBanner-v0.1.2.apk",
               "fb0de9090f30fbd2576f3e58a692b70a272955db0db40835fd863c03208f9151"),
    "rootavd_sh": (_RA + "rootAVD.sh", "f69e5524b3fab04abd9ad8a1a6a9053e3b4244228b4194379069ed0b7c9df036"),
    "rootavd_bat": (_RA + "rootAVD.bat", "0e8b9cae5a5d892263a014f4518c7e2bdbb10ba6f38e2a5cf8e0f9a4e122b110"),
}

# --- TikTok ------------------------------------------------------------------------------------
TIKTOK_PKG = "com.zhiliaoapp.musically"
TIKTOK_VERSION = "47.1.3"            # the module only hooks this exact build
# SHA-256 of TikTok's own signed 47.1.3 APK (signer cert SHA-256 9041803e...2ab5ba, CN=musical.ly);
# a matching hash means the file is byte-identical to TikTok's release.
TIKTOK_APK_SHA256 = "8b5569f592a5534652ae460ef1d9e7f7394b5b7fdde44ae64f106d76767e2622"
TIKTOK_PAGE = ("https://www.apkmirror.com/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/"
               "tiktok-47-1-3-release/tiktok-47-1-3-android-apk-download/")
MODULE_PKG = "com.vanquzie.tikprofilebanner"
MODULE_HOOK_LOG = "Completed profile banner force hook installation"

DEVICE_ALBUM = "/sdcard/Pictures/Banners"
IMAGE_TYPES = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WebP", ".heic": "HEIC", ".heif": "HEIC"}

AVD_CONFIG = {  # Galaxy S24-sized phone (tested profile)
    "avd.ini.encoding": "UTF-8", "AvdId": AVD_NAME, "avd.name": AVD_NAME,
    "abi.type": ABI, "hw.cpu.arch": "arm64" if ABI == "arm64-v8a" else "x86_64",
    "image.sysdir.1": SYS_IMG_REL + "/", "tag.id": "google_apis_playstore", "tag.display": "Google Play",
    "target": "android-35", "PlayStore.enabled": "yes",
    "hw.lcd.width": "1080", "hw.lcd.height": "2340", "hw.lcd.density": "420",
    "hw.device.manufacturer": "Samsung", "hw.device.name": "Galaxy S24 size",
    "hw.ramSize": "4096", "hw.cpu.ncore": "4", "hw.gpu.enabled": "yes", "hw.gpu.mode": "auto",
    "hw.keyboard": "yes", "hw.mainKeys": "no", "hw.sdCard": "yes", "sdcard.size": "512 MB",
    "disk.dataPartition.size": "6G", "vm.heapSize": "228M", "showDeviceFrame": "no",
    "fastboot.forceColdBoot": "yes", "hw.camera.back": "none", "hw.camera.front": "none",
}
SETUP_FREE_GB = 14   # downloads (~2.6 GB) + unpacked SDK (~3.5 GB) + phone storage (~7.5 GB)


def exe(name: str) -> str:
    return name + (".exe" if IS_WINDOWS else "")


def adb_path() -> Path:
    return SDK_DIR / "platform-tools" / exe("adb")


def emulator_path() -> Path:
    return SDK_DIR / "emulator" / exe("emulator")


def android_env() -> dict[str, str]:
    """Environment for every Android tool we start: points them at APP_DIR only."""
    env = dict(os.environ)
    env.update({
        "ANDROID_HOME": str(SDK_DIR), "ANDROID_SDK_ROOT": str(SDK_DIR),
        "ANDROID_AVD_HOME": str(AVD_HOME), "ANDROID_USER_HOME": str(ANDROID_USER_HOME),
        "ANDROID_EMULATOR_HOME": str(ANDROID_USER_HOME),
        "ANDROID_ADB_SERVER_PORT": ADB_PORT, "ANDROID_SERIAL": SERIAL,
        "PATH": os.pathsep.join([str(SDK_DIR / "platform-tools"), env.get("PATH", "")]),
    })
    return env
