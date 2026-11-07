# Tik: RCFO

Set a **TikTok profile banner** (the background image behind your profile info) from your computer.
One Python file starts a private Android phone in a window with the official TikTok app. You sign
in, open your profile, and add your banner.

> **Status: experimental.** The **Add background** button appears and TikTok accepts the upload.
> Whether *other people* see the banner has **not been confirmed yet** (see [What was tested](#what-was-tested)).

## You need

- **Python 3.9 or newer.** It isn't installed by the program.
  macOS: `brew install python` or [python.org](https://www.python.org/downloads/) ·
  Windows: [python.org](https://www.python.org/downloads/) (tick "Add python.exe to PATH") or `winget install Python.Python.3.12` ·
  Linux: usually preinstalled.
- A **supported computer** (see the table below) with hardware virtualization turned on.
- **About 14 GB free disk** for the first launch (about 9 GB stays used afterwards), and an internet connection.
- **TikTok 47.1.3 APK**, downloaded by you once from
  [APKMirror](https://www.apkmirror.com/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/tiktok-47-1-3-release/tiktok-47-1-3-android-apk-download/)
  (the APK, not the bundle). The program checks it is byte-for-byte TikTok's official file.

Nothing else: no pip packages, Java, Android Studio or git.

## Use

```bash
python3 tik_rcfo.py          # Windows: py tik_rcfo.py  (or double-click the file)
```

**First launch** (20–40 min, mostly downloads) sets up everything inside one folder, `~/.tik-rcfo`,
with step-by-step progress:

1. Checks the computer and free disk space.
2. Downloads Google's Android emulator and Android 15 system image (≈2.6 GB, checksum-verified).
3. Creates a virtual phone (Galaxy S24 screen size).
4. Downloads Magisk, Vector (LSPosed), rootAVD and TikProfileBanner (checksum-verified). It
   finds the TikTok APK in your Downloads folder, or asks you to drag it into the window.
5. Roots the virtual phone.
6. **Two short one-time steps in the phone window** (the program shows exactly what to tap):
   enable Zygisk and install Vector in Magisk, then switch the banner module on.
7. Installs TikTok and checks the banner module is active.

**Later launches** skip all of that: the phone and TikTok open in about 15 seconds.

Then TikTok is open in the phone window. Sign in yourself (password and codes go only into TikTok's
own screen; the program never reads or stores them), go to **Profile → Edit profile → Add background
→ Upload photo**, and pick from the **Banners** album. The terminal shows:

```
   1  Add images
   2  Close program
   3  Close program and erase all program data
```

- **1 · Add images.** Drag one or more image files into the terminal (or paste a path) and press
  Enter. JPG, PNG, WebP and HEIC are accepted. Each is copied into the phone's **Banners** album
  while TikTok stays open, and you're back at the menu.
- **2 · Close program.** Shuts down the phone and the program's own adb server. Your setup and
  TikTok sign-in are kept for next time.
- **3 · Close and erase.** Asks you to type `ERASE`, signs TikTok out on the phone, shuts down,
  then deletes `~/.tik-rcfo` (the phone, sign-in, imported images, downloads, settings). The next
  launch is a first launch again. If setup ever fails halfway: `python3 tik_rcfo.py --erase`.

Isolation: everything lives in `~/.tik-rcfo` (change it with `TIK_RCFO_HOME`, see
[.env.example](.env.example)). The program uses its own emulator copy, its own adb server port
(5038) and its own phone. It never modifies an Android SDK you already have, and erasing never
touches anything outside that folder. adb may read your existing `~/.android/adbkey`; it is left alone.

## Platforms

The program has to **run on a computer** that can run Google's Android emulator. Phones can't run
it, and nothing is hosted online: publishing this code doesn't run a server anywhere.

| Platform | Can run it? | Tested? |
|---|---|---|
| macOS, Apple Silicon | Yes | **Yes**: setup, later launches, image import, close, erase (details below) |
| macOS, Intel | Yes (x86_64 emulator + image) | No |
| Windows 10/11 x64 | Yes (needs *Windows Hypervisor Platform* turned on; uses rootAVD's `.bat`) | No |
| Linux x64 | Yes (needs KVM: your user in the `kvm` group) | No |
| Windows on ARM, Linux on ARM | **No**: Google publishes no emulator for these | n/a |
| Android phone / iPhone | **No**: can't run the emulator. From a phone you can only remote-control a computer that runs it. | No |

Facts behind this table: Google's emulator package (`repository2-3.xml`) exists only for macOS
arm64/x64, Windows x64 and Linux x64. rootAVD ships `.sh` (macOS/Linux) and `.bat` (Windows).
Known untested risks on Windows: a user folder with non-ASCII characters or spaces can break
the emulator or rootAVD; if it does, set `TIK_RCFO_HOME` to a simple path like `C:\tik-rcfo`.

## What was tested

On a Mac with Apple Silicon (macOS 26), 2026-11-07:

- ✅ **First-launch pieces:**
  - The disk-space check refused correctly with too little space.
  - Downloading, checksum-verifying and unpacking the emulator, platform tools and Android 15 image into an empty folder worked.
  - The generated virtual phone booted.
  - The root step worked on a clean image (Magisk running afterwards).
- ✅ **Resuming setup** on an existing phone: steps already done were detected, rooting re-ran,
  and Vector and the module were found active.
- ✅ **Later launch:** TikTok opened with the module active, in about 15 s.
- ✅ **Image import:**
  - macOS drag-and-drop with escaped spaces and parentheses
  - a quoted Arabic file name
  - a `file://` URI
  - a duplicate name (renamed)
  - a missing file and a GIF (both rejected with a message)
- ✅ **Close** (nothing left running) and **erase**: a wrong confirmation cancels; `ERASE` deletes only the program folder.
- ✅ **Banner:** the button showed for a real account, and TikTok accepted the upload and showed it.
- ⚠️ After restarting TikTok, the owner's own app no longer shows the banner. The module author
  says TikTok never sends your banner back to you, so it **must be checked from another account**.
  That hasn't been done yet.
- ❌ **Not tested:**
  - a complete first launch from zero in one run (this Mac lacked disk space)
  - the two manual Magisk/Vector steps on a fresh phone
  - installing TikTok from a fresh APK
  - Windows, Linux and Intel Macs

Offline tests (path parsing, image checks, erase safety): `python3 -m unittest discover -s tests`.

## Why an emulator, not the website or an API?

Checked on 2026-11-07:
- The tiktok.com website has no banner setting. Its profile code only uploads avatars, and public
  profile data has no banner field.
- TikTok's developer API is read-only for profiles.
- The app (47.1.3) contains the feature but hides it from accounts that aren't on TikTok's allow
  list. The GPL-3.0 [TikProfileBanner](https://github.com/vanquzie/TikProfileBanner) module
  un-hides it, which needs a rooted Android with LSPosed. More detail in [docs/architecture.md](docs/architecture.md).

## Risks

- **Account risk:** this unlocks a feature TikTok hasn't given your account, using a rooted, modified
  client. That breaks TikTok's terms and could get the account flagged or restricted.
- TikTok can drop banners server-side at any time. The module only works on TikTok **47.1.3**, so
  never update TikTok inside the phone or add a Google account to it.
- Only sign in with your own account. If a friend uses it, let them type, then use option 3.

## Credits

[TikProfileBanner](https://github.com/vanquzie/TikProfileBanner) · [Magisk](https://github.com/topjohnwu/Magisk) ·
[Vector/LSPosed](https://github.com/JingMatrix/Vector) · [rootAVD](https://gitlab.com/newbit/rootAVD) ·
Android Emulator by Google. Not affiliated with TikTok or ByteDance. License: MIT.
