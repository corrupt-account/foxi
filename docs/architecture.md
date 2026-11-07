# Architecture decision

## Findings that constrain the design

| Route to set a banner | Works? | Evidence (2026-11-07) |
|---|---|---|
| tiktok.com website | No | Profile-update code uploads only `UserAvatar`-type images; public profile JSON (`webapp.user-detail`) has no banner/background field. |
| Official TikTok API | No | Developer user endpoints (`/v2/user/info/`) are read-only; no profile-write endpoint. |
| Stock Android app | Only for allow-listed accounts | TikTok 47.7.2 showed no option for the tester's account. |
| Android app 47.1.3 + TikProfileBanner (LSPosed) | Button appears; upload accepted | Tested on a real account. Visibility to others not yet confirmed. |
| iOS app | Unknown, not modifiable | No equivalent module; iOS can't run Android apps. |

So the **native Android app with a hook framework** is required. Python can't replace the app;
it can only orchestrate an Android environment.

## Options compared

### 1. Local Python program (chosen): `tik_rcfo.py`
Python 3 (standard library only). On first launch it downloads Google's emulator, platform-tools
and Android 15 image directly from `dl.google.com` (pinned versions, Google's SHA-1s), so no Java,
`sdkmanager` or `avdmanager` is needed. It writes the virtual phone's config itself, and keeps
everything in `~/.tik-rcfo` with its own adb server port. Later launches go straight to a
three-item menu. The emulator window is the UI, and the user types into the real TikTok app.
(An earlier version also drove the screen with `uiautomator` to open Edit profile automatically.
That was dropped because blind taps on TikTok's feed were unreliable; the user now navigates.)

- ✅ Credentials never leave the user's machine; no server; free.
- ✅ The same code runs on macOS, Windows and Linux (paths and the rootAVD script differ per OS).
- ❌ Needs a desktop with virtualization, ~14 GB disk and a one-time setup with two manual taps.
- ❌ Can't run *on* a phone.

Why not shell scripts: they don't run on Windows. Why Python over Node or Go: it's preinstalled on
macOS and most Linux, one `winget` command away on Windows, and needs no build step or dependencies.

### 2. Browser UI with a local Python backend
A localhost web page wrapping the same commands, maybe streaming the emulator screen.

- Adds a web server, front end and screen streaming without removing any requirement: the
  emulator must still run on the same computer. The emulator's own window already is the UI.
- Not built. Worth revisiting only if a non-technical audience needs buttons instead of a terminal.

### 3. Remotely hosted Android sessions (for phones and iPhones)
The only way an iPhone or unrooted Android phone user gets the full flow without a computer.

What it needs:
- **Hosts with hardware virtualization:** bare-metal or nested-virtualization x86_64 Linux with KVM,
  running the emulator headless (e.g. Google's `android-emulator-container-scripts`, which
  stream over WebRTC), or ARM servers running Redroid.
- **Per user:** a fresh emulator cloned from a prepared snapshot (rooted, TikTok 47.1.3, module),
  ~2–4 vCPU, 4 GB RAM, ~8 GB disk. Destroy the whole instance when the session ends. Wiping
  the app alone isn't enough isolation.
- **Web front end:** auth, a queue, a WebRTC screen stream with touch/keyboard input, image upload
  into the instance, and TURN servers for users behind strict NATs.
- **Rough cost** (estimates, check current prices): a dedicated server (~€40–80/month) fits
  about 3–6 concurrent sessions; on-demand cloud VMs with nested virtualization cost
  ~$0.10–0.25 per session-hour, plus bandwidth (~1–3 Mbit/s per stream) and TURN.
- **Unavoidable trust problem:** the operator's server holds the live TikTok session token while
  the session runs, and keystrokes pass through the operator's stream. Users must trust the
  operator not to log them, even with honest code.
- **Practical problem:** many logins from datacenter IPs with a rooted, modified client are
  likely to trigger TikTok's security checks or account flags.

Not built. Publishing this repository doesn't host anything; someone would have to run and pay
for the servers above. The smallest alternative for phone users is remote-desktop access to a
computer they (or a friend) control, running option 1.

## Session isolation and data handling (option 1)

- Login happens only inside TikTok's own app. The tool has no login form.
- Screen dumps (`uiautomator dump /dev/tty`) stream into memory and are taken only on the
  profile and Edit-profile screens after sign-in. No screenshots are taken.
- `end` runs `pm clear` on TikTok (tokens, cache, drafts) and deletes the Banners album and
  Download images, including their MediaStore entries. Logging out inside TikTok first also
  ends the session server-side.
- `uninstall` deletes the emulator and restores the original system ramdisk.
