# foxi

Set a **TikTok profile banner** (the background image behind your profile info) from your computer.
`foxi.py` starts a private Android phone in its own window, running the official TikTok app with
the banner option unlocked. You sign in, open your profile and add your banner.

> **Status: experimental.** The **Add background** button appears and TikTok accepts the upload.
> Whether *other people* see the banner has **not been confirmed yet** (see [What was tested](#what-was-tested)).

```
                        (fox)


 ▀█▀ ▀█▀ █ ▄▀ ▀█▀ █▀▀█ █ ▄▀   ▄   █▀▀█ █▀▀ █▀▀ █▀▀█
  █   █  ██▄   █  █  █ ██▄        █▀█▀ █   █▀▀ █  █
  ▀  ▀▀▀ ▀  ▀  ▀  ▀▀▀▀ ▀  ▀   ▀   ▀  ▀ ▀▀▀ ▀   ▀▀▀▀
                  tiktok.com/@rcfo
      https://github.com/corrupt-account/foxi
       Banner unlock by: github.com/vanquzie

 Sign in, then: Profile → Edit profile → Add background → Upload photo → Banners

 1  Add images
 2  Close program
 3  Close program and erase all program data
 › Choose 1, 2 or 3:
```

## You need

- **Python 3.9 or newer.** foxi doesn't install it.
  - macOS: `brew install python` or [python.org](https://www.python.org/downloads/)
  - Windows: [python.org](https://www.python.org/downloads/) (tick "Add python.exe to PATH") or `winget install Python.Python.3.12`
  - Linux: usually preinstalled
- **A supported computer** (see [Platforms](#platforms)) with hardware virtualization turned on.
- **About 14 GB free disk** for the first start (about 9 GB stays in use afterwards), and an internet connection.
- **The TikTok 47.1.3 APK** in the `apk/` folder (see [The TikTok APK](#the-tiktok-apk)).

No pip packages, Java, Android Studio or git are needed. foxi uses only Python's standard library.

## Start

From the `foxi` folder:

```bash
python3 foxi.py
```

On Windows run `py foxi.py`, or double-click `foxi.py`.

Every screen shows the same header, centred in the window: the fox, the `TIKTOK : RCFO` heading,
the TikTok link, this project's link and the credits. Only the part underneath changes. foxi draws in the terminal's alternate screen, so old screens
don't pile up in the scrollback. When foxi exits, its last screen (or an error with what to do
next) stays in the terminal. It fits a 120 × 30 Mac Terminal window; smaller windows drop the
heading or the fox.

### First start (20–40 minutes, mostly downloads)

foxi sets everything up in `~/.foxi`, one step per screen:

1. **Checks the computer** and free disk space.
2. **Downloads Google's Android emulator and Android 15 system image** (about 2.6 GB). All checksums are verified.
3. **Creates a virtual phone** the size of a Galaxy S24 screen.
4. **Downloads Magisk, Vector (LSPosed), rootAVD and TikProfileBanner.** All checksums are verified.
5. **Roots the virtual phone.**
6. **One-time taps in the phone window.** The screen shows exactly what to tap: switch on Zygisk
   and install Vector in Magisk, then the phone restarts.
7. **Installs TikTok** from `apk/TikTok-47.1.3.apk` and the banner module. The first time, you switch
   the module on in the Vector manager (one tap, shown on screen).

If something fails, the screen says what happened. Run `python3 foxi.py` again and it continues
from where it stopped.

### Later starts (about 15 seconds)

The phone and TikTok open straight away. Sign in yourself in the phone window. Your password and
codes go only into TikTok's own screen; foxi never reads or stores them. Then go to
**Profile → Edit profile → Add background → Upload photo**, and choose from the **Banners** album.

### Menu

- **1 · Add images.** Drag one or more image files into the terminal window, or paste a path, and
  press Enter. JPG, PNG, WebP and HEIC work, including names with spaces, quotes or non-Latin
  letters. Each image goes into the phone's **Banners** album while TikTok stays open, and you're
  back at the menu.
- **2 · Close program.** Shuts down the phone and foxi's own adb server. Your setup and TikTok
  sign-in are kept for next time.
- **3 · Close program and erase all program data.** Type `ERASE` to confirm. foxi signs TikTok out
  on the phone, shuts down and deletes `~/.foxi`: the phone, the sign-in, imported images,
  downloads and settings. The next start is a first start again. The `apk/` folder is kept.
  If setup ever gets stuck: `python3 foxi.py --erase`.

## The TikTok APK

The banner module only works with **TikTok 47.1.3**. foxi installs it from:

```
foxi/apk/TikTok-47.1.3.apk
```

| | |
|---|---|
| Version | TikTok 47.1.3 (`com.zhiliaoapp.musically`), single APK (not a bundle) |
| Source | [APKMirror: TikTok 47.1.3](https://www.apkmirror.com/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/tiktok-47-1-3-release/tiktok-47-1-3-android-apk-download/) |
| SHA-256 | `8b5569f592a5534652ae460ef1d9e7f7394b5b7fdde44ae64f106d76767e2622` |
| Signing certificate SHA-256 | `9041803e91bcb814b4b4399fb5c85a91640b755e5e8ba76813814bf4cf2ab5ba` (TikTok's own key) |

foxi installs the file only if its SHA-256 matches exactly. **The APK is not in the GitHub
repository**: it's TikTok's copyrighted app, and at 450 MB it's over GitHub's file-size limit. If
you cloned the repo, download that exact file and save it as `apk/TikTok-47.1.3.apk`. If it's
missing, foxi also looks in your Downloads folder, then asks you to drag the file into the window.

## Platforms

foxi has to **run on a computer** that can run Google's Android emulator. Phones can't run it, and
nothing is hosted online: publishing this code doesn't run a server anywhere.

| Platform | Can run foxi? | Tested? |
|---|---|---|
| macOS, Apple Silicon | Yes | **Yes** (details below) |
| macOS, Intel | Yes (x86_64 emulator and image) | No |
| Windows 10/11 x64 | Yes (turn on *Windows Hypervisor Platform*; uses rootAVD's `.bat`) | No |
| Linux x64 | Yes (needs KVM: add your user to the `kvm` group) | No |
| Windows on ARM, Linux on ARM | **No**: Google publishes no emulator for them | n/a |
| Android phone / iPhone | **No**: can't run the emulator. From a phone you can only remote-control a computer running foxi. | No |

Google's emulator package exists only for macOS arm64/x64, Windows x64 and Linux x64. rootAVD
ships `.sh` (macOS/Linux) and `.bat` (Windows). If a Windows user folder with spaces or non-ASCII
letters breaks the emulator, set `FOXI_HOME` to a simple path such as `C:\foxi-data`.

## Settings and data

foxi needs no configuration. Everything it creates lives in one folder, `~/.foxi`:

- its own copy of the Android emulator and tools
- the virtual phone, including your TikTok sign-in
- downloads and settings

It runs its own adb server on port 5038, never modifies an Android SDK you already have, and
"erase" never touches anything outside `~/.foxi`. adb may read an existing `~/.android/adbkey`,
which is left alone. Optional environment variables are listed in [.env.example](.env.example).

## What was tested

On a Mac with Apple Silicon (macOS 26), 2026-11-07:

- ✅ **First start from nothing.**
  - foxi downloaded, checked and unpacked the Android tools, created the phone and rooted it.
  - The one-time Magisk/Vector taps were then done by hand, and setup finished.
  - The low-disk check refuses cleanly.
- ✅ **Later start:** TikTok opens with the banner module active.
- ✅ **Screens in a real 120 × 30 Mac Terminal:** startup, a setup step, the menu and the closed
  screen all fit without wrapping, the prompt stays visible, and the scrollback holds a single header.
- ✅ **Adding images:**
  - a Finder drag with escaped spaces and brackets
  - a quoted Arabic file name
  - a `file://` path
  - a duplicate name (gets a number)
  - a missing file and a GIF (both refused with a message)
- ✅ **Close** leaves nothing running. **Erase** (tested on a copy): a wrong confirmation cancels;
  `ERASE` deletes only the data folder.
- ✅ **Banner:** the button appeared for a real account, and TikTok accepted and displayed the upload.
- ⚠️ **Visibility to others not checked.** After TikTok restarts, the owner's own app no longer
  shows the banner. The module author says TikTok never sends your banner back to you, so it has
  to be **checked from another account**. That hasn't been done yet.
- ❌ **Not tested yet:**
  - installing TikTok from `apk/` during setup (the APK was added to the folder after setup had finished)
  - Windows, Linux and Intel Macs

Offline tests (paths, images, erase safety, screen layout at many window sizes):

```bash
python3 -m unittest discover -s tests
```

## Why an emulator, not the website or an API?

Checked on 2026-11-07:

- **Website:** tiktok.com has no banner setting. Its profile code only uploads avatars, and public
  profile data has no banner field.
- **Developer API:** TikTok's API is read-only for profiles.
- **App:** version 47.1.3 contains the feature but hides it from accounts that aren't on TikTok's
  allow list. [TikProfileBanner](https://github.com/vanquzie/TikProfileBanner) un-hides it, which
  needs a rooted Android phone with LSPosed.

More detail is in [docs/architecture.md](docs/architecture.md).

## Risks

- **Account risk:** this unlocks a feature TikTok hasn't given your account, on a rooted, modified
  client. That breaks TikTok's terms and could get the account flagged or restricted.
- **TikTok can drop banners server-side at any time.**
- **Don't update TikTok:** the module only works on 47.1.3, so never update TikTok inside the phone
  or add a Google account to it.
- **Only sign in with your own account.** If a friend uses foxi, let them type, then use option 3.

## Credits and licenses

- **Banner unlock:** [TikProfileBanner](https://github.com/vanquzie/TikProfileBanner) by
  **vanquzie**, GPL-3.0. foxi downloads the author's release and doesn't modify or redistribute it.
- Other components and their licenses are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- foxi itself is MIT-licensed ([LICENSE](LICENSE)). It isn't affiliated with TikTok or ByteDance.
