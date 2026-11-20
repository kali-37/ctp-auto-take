# Closed Test Pro Auto Take

A Python + ADB script that automates the daily testing loop in the **Closed Test Pro** Android app.

It scans your list, opens each untested app, keeps it in the foreground for 35 seconds, returns to Closed Test Pro, taps **Feedback**, closes the sheet, and restarts the app so the list doesn't freeze mid-scroll.

> **Disclaimer:** This is an unofficial personal productivity script. It is not affiliated with Closed Test Pro or Google. Automation may violate Closed Test Pro's terms — their Play Store listing says they filter scripts. Use at your own risk, and don't run it on an account you can't afford to lose.

---

## Let an AI do the setup for you

Don't want to touch a terminal? Open **LLME.md** in this repo and hand it to Cursor, Claude Code, OpenCode, Gemini CLI, or any coding agent:

> "Read this file and set up Closed Test Pro Auto Take for me. Ask before installing anything."

The agent will inspect your computer, install what's missing, configure the script for your phone, run a dry run, test one app, then run the full list. You only handle the physical phone steps and approve installs.

---

## What it does

For every list row with an **Open** button:

1. Taps **Open** and launches the target app.
2. Keeps it in the foreground for **35 seconds** (configurable).
3. Captures a PNG screenshot straight from the phone over ADB.
4. Returns to Closed Test Pro.
5. Taps **Feedback** and closes the Play Store sheet.
6. Restarts Closed Test Pro to prevent the list-scroll freeze.
7. Moves to the next untested row.

It scans from the top of the list, skips rows that are already tested or paused, and stops when no untested **Open** row remains. It writes a `.log`, a `.csv`, and a folder of screenshots for every run.

**It does not:** install apps, create fake accounts, submit fake reviews, or bypass the timer. It performs the same taps you'd make yourself.

---

## What you need

| Tool | Why you need it | Download |
|---|---|---|
| **Closed Test Pro** | The app you're automating | [Google Play](https://play.google.com/store/apps/details?id=com.closedtest.pro.closedtest_pro) |
| **Python 3.9+** | Runs the script | [python.org/downloads](https://www.python.org/downloads/) |
| **Android Platform Tools** | Provides `adb` | [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools) |
| **Samsung USB Driver** | Windows only, so Windows can see a Samsung phone | [developer.samsung.com/mobile/android-usb-driver.html](https://developer.samsung.com/mobile/android-usb-driver.html) |
| **The script** | `closed_test_pro.py` from this repo | [Download](https://github.com/kali-37/ctp-auto-take/raw/main/closed_test_pro.py) |

You also need:

- A Windows, macOS, or Linux computer.
- A USB data cable (not a charge-only cable).
- An Android phone with USB debugging enabled.
- The phone unlocked and connected to the computer while the script runs.

**Device note:** The script was built and tested on a **Samsung** phone (One UI). It can work on other Android phones, but you may need to change the launcher package and swipe coordinates. See [Configure it](#4-configure-it).

---

## 1. Set up your phone

1. Install **Closed Test Pro** from the Play Store and log in.
2. Complete any onboarding so the main testing list is visible.
3. Open **Settings → About phone → Software information**.
4. Tap **Build number** seven times. You should see "Developer mode has been enabled."
5. Go back to **Settings → Developer options**.
6. Turn on **USB debugging**.
7. Connect the phone to your computer with a USB cable.
8. On the phone, tap **Allow** on the "Allow USB debugging?" prompt. Check **Always allow from this computer**.
9. If the phone asks for a USB mode, choose **File transfer / Android Auto** (not "Charging only").
10. Keep the phone **unlocked** while the script runs.

> The script wakes the screen and keeps it on while USB is connected, but it cannot enter your PIN or pattern. Unlock the phone before you start.

---

## 2. Set up your computer

### Windows

1. Install Python 3 from [python.org/downloads](https://www.python.org/downloads/). During setup, check **Add python.exe to PATH**.
2. Download **Android Platform Tools** from [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools).
3. Extract the ZIP to `C:\platform-tools`.
4. Add `C:\platform-tools` to your **PATH**:
   - Press `Win`, search **Environment Variables**, open **Edit the system environment variables**.
   - **Environment Variables → Path → Edit → New →** `C:\platform-tools` → OK.
5. Install the **Samsung USB Driver** from [developer.samsung.com/mobile/android-usb-driver.html](https://developer.samsung.com/mobile/android-usb-driver.html).
6. Open **Command Prompt** and check both tools:

```bat
python --version
adb version
adb devices
```

`adb devices` should list your phone with the status `device`.

### macOS

1. Install Python 3 from [python.org/downloads](https://www.python.org/downloads/) or with Homebrew:

```bash
brew install python
```

2. Install `adb` with Homebrew:

```bash
brew install android-platform-tools
```

Or download Android Platform Tools from [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools) and add the folder to your `PATH`.

3. Check:

```bash
python3 --version
adb version
adb devices
```

No Samsung driver is needed on macOS.

### Linux

1. Install Python 3 and `adb`:

```bash
sudo apt update
sudo apt install python3 adb
```

On Fedora:

```bash
sudo dnf install python3 android-tools
```

2. If `adb devices` shows `no permissions`, add a udev rule for Samsung:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

3. Unplug the phone, plug it back in, and accept the debugging prompt.
4. Check:

```bash
python3 --version
adb devices
```

---

## 3. Get the script

1. Open `closed_test_pro.py` in this repo.
2. Click **Raw**.
3. Save the page as `closed_test_pro.py`.

Or clone the repo:

```bash
git clone https://github.com/kali-37/ctp-auto-take.git
cd ctp-auto-take
```

---

## 4. Configure it

Open `closed_test_pro.py` in any text editor (Notepad, VS Code, nano, etc.). The defaults work for a single connected phone. Change these values if needed.

### `SERIAL`

```python
SERIAL = os.environ.get("CTP_SERIAL", "")
```

Leave it blank and `adb` uses the only connected device. If you have more than one device attached, set the serial:

```bash
# macOS / Linux
export CTP_SERIAL=YOUR_DEVICE_SERIAL

# Windows CMD
set CTP_SERIAL=YOUR_DEVICE_SERIAL

# Windows PowerShell
$env:CTP_SERIAL="YOUR_DEVICE_SERIAL"
```

Get your serial from:

```bash
adb devices
```

The first column is the serial. Copy it exactly.

### `OUTDIR`

```python
OUTDIR = Path(os.environ.get("CTP_OUTDIR", str(Path.home() / "ctp-logs")))
```

The default is `~/ctp-logs` on every OS. To use a different folder:

```bash
# macOS / Linux
export CTP_OUTDIR=/path/to/logs

# Windows CMD
set CTP_OUTDIR=C:\path\to\logs
```

The script creates the folder if it doesn't exist.

### `LAUNCHER`

```python
LAUNCHER = "com.sec.android.app.launcher"
```

This is Samsung's One UI home app. If you use a different phone, find your launcher package:

```bash
adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME
```

The output looks like:

```text
priority=0 ... com.google.android.apps.nexuslauncher/.NexusLauncherActivity
```

Use the package name before the `/`:

```python
LAUNCHER = "com.google.android.apps.nexuslauncher"
```

Common values:

| Phone | Launcher package |
|---|---|
| Samsung (One UI) | `com.sec.android.app.launcher` |
| Google Pixel | `com.google.android.apps.nexuslauncher` |
| AOSP / stock Android | `com.android.launcher3` |
| Xiaomi / POCO (MIUI/HyperOS) | `com.miui.home` |
| OnePlus | `com.oneplus.launcher` or `net.oneplus.launcher` |
| Oppo / Realme (ColorOS) | `com.coloros.launcher` |
| Nothing | `com.nothing.launcher` |

If the value is wrong, the script may think the launcher is the target app and wait forever, or record the wrong result.

### Swipe coordinates

The `scroll()` function uses hardcoded coordinates for a **1080 × 2400** screen:

```python
sh("input", "swipe", 540, 1650, 540, 950, dur)
```

- `540` is the horizontal center (1080 ÷ 2).
- `1650` is the start Y (2400 × 0.6875).
- `950` is the end Y (2400 × 0.3958).

Get your screen size:

```bash
adb shell wm size
```

Example output:

```text
Physical size: 1080x2340
```

For a 1080 × 2340 screen:

- x = 540
- start Y = 2340 × 0.6875 ≈ **1609**
- end Y = 2340 × 0.3958 ≈ **926**

So the line becomes:

```python
sh("input", "swipe", 540, 1609, 540, 926, dur)
```

If the list barely moves, increase the distance. If it overshoots, decrease it.

### Optional: row tolerance

`row_for_y()` uses a ±80 px window to match a button to its row. On a much larger or smaller screen, scale it:

```python
tol = int(screen_height * 0.033)
```

The script doesn't read the screen height automatically, so hardcode the number you need if the default doesn't match.

---

## 5. Run it

### Step 1 — dry run

This lists the Open apps without tapping anything:

```bash
python3 closed_test_pro.py --dry-run
```

On Windows, use `python` instead of `python3`:

```bat
python closed_test_pro.py --dry-run
```

Check that the app names look right and that it finds the rows you expect.

### Step 2 — test two apps

```bash
python3 closed_test_pro.py --max-apps 2
```

Watch the phone for these two. Make sure the script:

- opens the right app,
- returns to Closed Test Pro,
- taps Feedback,
- closes the sheet,
- moves to the next row.

### Step 3 — full run

```bash
python3 closed_test_pro.py
```

Keep the phone connected and unlocked. The script handles the rest.

### All options

| Option | Default | What it does |
|---|---|---|
| `--duration 35` | `35` | Seconds each app stays in the foreground |
| `--max-apps 2` | `0` (all) | Stop after N apps |
| `--dry-run` | off | List Open apps without tapping |
| `--no-screenshots` | off | Skip PNG capture (screenshots are on by default) |

Examples:

```bash
# shorter foreground time
python3 closed_test_pro.py --duration 20

# only five apps
python3 closed_test_pro.py --max-apps 5

# preview the list
python3 closed_test_pro.py --dry-run

# run without screenshots
python3 closed_test_pro.py --no-screenshots
```

### Logs and screenshots

The script writes to `OUTDIR`:

```text
ctp-test-YYYYMMDD-HHMMSS.log
ctp-test-YYYYMMDD-HHMMSS.csv
ctp-shots-YYYYMMDD-HHMMSS/
```

The CSV columns are:

```text
result, app, package, launch_delay_s, feedback, screenshot
```

`result` is `OK`, `LEFT-APP`, or `FAILED`. The log has the full timeline, and the `screenshot` column points to the PNG captured for that app.

Screenshots are taken at the start, after each app's foreground time, on failures, and at the end. Some apps use `FLAG_SECURE` and will appear black; that's an Android restriction, not a script bug.

---

## How it works

The script uses only Android's built-in `adb` commands:

- `uiautomator dump` reads the current screen as XML.
- `input tap` and `input swipe` perform the taps and scrolls.
- `dumpsys window` checks which app is in the foreground.
- `am start` and `am force-stop` launch and restart Closed Test Pro.

The cycle per app is:

```text
Open → wait for target app → 35 s → screenshot → HOME → Closed Test Pro
     → Feedback → close sheet → restart Closed Test Pro → next row
```

Screenshots use `adb exec-out screencap -p` (with a `screencap` + `pull` fallback for older devices) and are saved as PNGs.

It restarts Closed Test Pro after every app because the list can freeze mid-scroll after the feedback sheet closes.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `adb: command not found` | Add Android Platform Tools to your `PATH`, or run the script from the platform-tools folder. |
| `adb: no devices/emulators found` | Use a data cable, enable USB debugging, choose File transfer mode, install the Samsung driver on Windows, then run `adb kill-server` and `adb devices`. |
| `unauthorized` | Unlock the phone and accept the "Allow USB debugging?" prompt. If it doesn't appear, revoke USB debugging authorizations in Developer options and replug. |
| `device offline` | Run `adb kill-server` then `adb start-server`, then replug the phone. |
| `uiautomator dump failed repeatedly` | Unlock the phone, close any overlay apps, disable animations in Developer options, and try again. |
| `am start failed` | Closed Test Pro's activity changed. Check it with `adb shell cmd package resolve-activity --brief com.closedtest.pro.closedtest_pro` and update `CTP_ACT`. |
| Script waits forever after tapping Open | `LAUNCHER` is wrong, or the target app shows a system dialog. Check `adb shell dumpsys window \| grep mCurrentFocus` while it's stuck. |
| Opens the launcher instead of the app | Update `LAUNCHER` to your phone's home app. |
| Scroll doesn't move | Update the swipe coordinates for your screen size. |
| Feedback button not found | The app may already be tested, the list may be stale, or the row is off-screen. Refresh Closed Test Pro and rerun. |
| Script stops early | It reached the end of the list, or you passed `--max-apps`. Check the log. |
| `python3: command not found` on Windows | Use `python` instead, and confirm Python is on `PATH`. |
| CSV is empty | You ran with `--dry-run`, or no apps were handled. |
| Phone locks mid-run | Unlock it and keep it connected. The script sets `stayon`, but a manual lock still overrides it. |
| Feedback sheet doesn't close | The close label may have changed. Update `close_feedback_sheet()` to match the new UI. |
| Screenshots are black | The app uses `FLAG_SECURE`. Android blocks screen capture for that app; use the log/CSV as the record instead. |
| `screenshot failed` in the log | The device rejected `exec-out screencap`. The script falls back to `screencap` + `pull`; if that also fails, unlock the phone and test manually with `adb shell screencap -p /sdcard/test.png` then `adb pull /sdcard/test.png`. |
| `screencap: unable to capture screen` | The phone is locked or the screen is off. Unlock it and rerun. |

If Closed Test Pro updates its UI, the selectors in `rows()`, `open_buttons()`, `feedback_button()`, and `close_feedback_sheet()` may need updating. The script reads `content-desc` and `text` values, so use `uiautomator dump` to inspect the new screen.

---

## Scheduling (optional)

You can run the script automatically, but the phone must be connected, unlocked, and logged in.

### Windows Task Scheduler

1. Open **Task Scheduler → Create Basic Task**.
2. Trigger: **Daily**, pick a time.
3. Action: **Start a program**.
4. Program: `python`
5. Arguments: `C:\path\to\closed_test_pro.py`
6. Start in: `C:\path\to`

### macOS / Linux cron

```bash
crontab -e
```

Add:

```cron
0 9 * * * /usr/bin/python3 /path/to/closed_test_pro.py
```

This runs at 09:00 every day. The phone must be plugged in and unlocked at that time.

> Scheduling is optional. Run it manually for the first few days so you can catch device-specific issues.

---

## Safety and terms

- **Unofficial.** This project is not affiliated with Closed Test Pro or Google.
- **Terms of service.** Closed Test Pro's listing says they filter out "emulators, scripts, and inactive accounts." Automating their app may violate their terms and could get your account flagged. Check their terms before you run it.
- **No fake activity.** The script performs the same UI taps a human tester would. It does not fake installs, reviews, or account activity.
- **Local only.** The script uses `adb` on your computer. It doesn't send data to any server. Read the code before running it.
- **No warranty.** Provided as-is, under the MIT License. You are responsible for your account and your device.

---

## FAQ

**Does it need root?**
No. It uses standard `adb` input commands.

**Does it work on an emulator?**
No. Use a real phone. Closed Test Pro also says they filter emulators.

**Does it work on iPhone?**
No. It's Android-only.

**Does it install the apps?**
No. It opens apps that are already in your Closed Test Pro list and already installed.

**Does it write feedback text?**
No. It taps the Feedback button and closes the sheet. It doesn't submit a written review.

**Can I run it overnight?**
Yes, if the phone stays connected and unlocked. The script sets the screen to stay on, but a manual lock or a dead battery will stop it.

**Can I run multiple phones at once?**
The script is written for one serial at a time. Run one instance per phone, or duplicate the script and change `SERIAL` and `OUTDIR` for each device.

**Why Samsung?**
The original script was built on a Samsung phone. The logic is generic, but the launcher package and swipe coordinates are device-specific. See [Configure it](#4-configure-it).

**Is this allowed?**
That's between you and Closed Test Pro. The script is honest about what it does, but automation may still violate their rules. Use your judgment.

---

## License

MIT. Do what you want, keep the disclaimer, and don't blame the author if your account gets flagged.
