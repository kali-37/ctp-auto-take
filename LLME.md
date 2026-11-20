# LLME.md — AI setup agent for Closed Test Pro Auto Take

> **This file is for an AI assistant, not a human.**
>
> If you're a person: hand this file to ChatGPT, Claude, Cursor, Gemini, or any
> coding agent and say:
>
> *"Read this file and set up Closed Test Pro Auto Take for me. Ask before
> installing anything."*
>
> The agent will inspect your computer, install what's missing, configure the
> script for your phone, run a dry run, test one app, then run the full list.

---

## What the user gets

A working `closed_test_pro.py` run on their own computer and phone:

- Opens each untested app in their Closed Test Pro list.
- Keeps it in the foreground for 35 seconds.
- Captures a PNG screenshot over ADB.
- Returns to Closed Test Pro, taps Feedback, closes the sheet.
- Restarts Closed Test Pro to avoid the scroll freeze.
- Writes a log, a CSV, and a folder of screenshots.

The user should not have to edit code, read the whole README, or debug `adb`.
You do that. They only do the physical phone steps and approve installs.

---

## Hard rules

1. **Ask before installing software**, running `sudo`, changing `PATH`, or
   changing phone settings.
2. **Never ask for** the user's Google password, phone PIN, pattern, 2FA code,
   or recovery codes.
3. **Never run this on an account the user doesn't own.** Ask them to confirm.
4. **Warn once, clearly:** Closed Test Pro's listing says they filter scripts.
   Automation may violate their terms and get the account flagged. The user
   decides whether to continue.
5. **Don't disable security features**, root the phone, or install APKs from
   outside the Play Store.
6. **Keep logs and screenshots local.** Don't upload them anywhere.
7. **Verify every phase.** Don't report success because a command exited 0;
   check the actual output.
8. **Don't skip the dry run or the one-app test.** If they fail, stop and
   troubleshoot.
9. **Don't guess package names or coordinates.** Read them from the device.
10. **Stop if the phone is unauthorized, offline, or locked.** Ask the user to
    fix it.

---

## Phase 0 — Consent

Say this in plain language:

> "This script controls your phone over ADB. It will tap Open, wait, tap
> Feedback, and repeat. It doesn't install apps or write reviews. Closed Test
> Pro's listing says they filter scripts, so automation may be against their
> terms and could get your account flagged. Do you own the phone and account,
> and do you want to continue?"

If no, stop. If yes, continue.

---

## Phase 1 — Inspect the machine

Run these and record the results:

```bash
python3 --version || python --version
adb version || echo "ADB_MISSING"
adb devices
```

If a device is connected:

```bash
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
adb shell wm size
adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME
adb shell pm list packages | grep -i closedtest
```

Also determine the OS and shell:

```bash
uname -a          # macOS / Linux
```

```bat
ver               # Windows CMD
```

```powershell
$PSVersionTable.OS   # PowerShell
```

### Decision table

| Result | Action |
|---|---|
| `adb` missing | Go to Phase 2 and install Android Platform Tools. |
| `adb devices` empty | Ask the user to connect the phone, enable USB debugging, and accept the prompt. |
| `unauthorized` | Ask the user to unlock the phone and tap **Allow**. If no prompt, revoke USB debugging authorizations and replug. |
| `offline` | `adb kill-server`, `adb start-server`, replug. |
| `device` | Continue. |
| `pm list packages` has no `closedtest` | Ask the user to install **Closed Test Pro** from the Play Store and log in. |
| `wm size` works | Save width and height for Phase 5. |
| Home activity works | Save the package before `/` as `LAUNCHER` for Phase 5. |

---

## Phase 2 — Install prerequisites

Ask for permission before each install. Prefer the user's package manager;
fall back to the official downloads.

### Windows

Check for `winget`:

```powershell
winget --version
```

If available:

```powershell
winget install --id Python.Python.3.12 -e
```

Platform Tools (official ZIP):

```powershell
$url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\platform-tools.zip"
Expand-Archive "$env:TEMP\platform-tools.zip" -DestinationPath "$env:LOCALAPPDATA\Android" -Force
$env:Path += ";$env:LOCALAPPDATA\Android\platform-tools"
```

Persist `PATH` only with the user's approval. For Samsung phones, install the
official driver from:

<https://developer.samsung.com/mobile/android-usb-driver.html>

The driver installer is a GUI; ask the user to click through it.

### macOS

```bash
brew install python
brew install --cask android-platform-tools
```

If Homebrew is missing, ask before installing it, or use the official Python
installer and the Platform Tools ZIP.

### Linux

```bash
sudo apt update
sudo apt install -y python3 adb
```

Ask before `sudo`. For Fedora:

```bash
sudo dnf install -y python3 android-tools
```

If `adb devices` shows `no permissions`, add the Samsung udev rule **with
consent**:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Verify

```bash
adb version
adb devices
```

The phone must show `device`, not `unauthorized` or `offline`.

---

## Phase 3 — Phone setup

These are physical steps. Give them one at a time and wait for confirmation.

1. Install **Closed Test Pro** from the Play Store and log in.
2. Open **Settings → About phone → Software information**.
3. Tap **Build number** seven times.
4. Go to **Settings → Developer options**.
5. Turn on **USB debugging**.
6. Connect the phone with a USB **data** cable.
7. On the phone, tap **Allow** on the USB debugging prompt. Check **Always
   allow from this computer**.
8. Choose **File transfer / Android Auto** if asked for a USB mode.
9. Unlock the phone and leave it unlocked.

Verify:

```bash
adb devices
adb shell getprop ro.product.model
```

Expected: the serial followed by `device`, and the phone model.

---

## Phase 4 — Get the script

If the user already has the repo:

```bash
cd /path/to/close_test_pro
```

If they have a repo URL:

```bash
git clone <REPO_URL>
cd <REPO_FOLDER>
```

Or download the raw file:

```bash
curl -L <RAW_URL> -o closed_test_pro.py
```

Verify it parses:

```bash
python3 -m py_compile closed_test_pro.py
```

On Windows:

```bat
python -m py_compile closed_test_pro.py
```

If the file is missing `adb_bytes` or `screenshot`, you have an older copy. Ask
the user for the latest repo URL.

---

## Phase 5 — Configure for this phone

Open `closed_test_pro.py` and set these values.

### Serial

The script reads `CTP_SERIAL` from the environment. If exactly one device is
connected, leave it blank. If multiple devices are connected:

```bash
export CTP_SERIAL=<serial>
```

Windows:

```bat
set CTP_SERIAL=<serial>
```

or PowerShell:

```powershell
$env:CTP_SERIAL="<serial>"
```

### Launcher

Default is Samsung:

```python
LAUNCHER = "com.sec.android.app.launcher"
```

From Phase 1, take the package before `/` and update it if different:

```python
LAUNCHER = "<detected.package>"
```

Common values:

| Phone | Launcher package |
|---|---|
| Samsung | `com.sec.android.app.launcher` |
| Pixel | `com.google.android.apps.nexuslauncher` |
| AOSP | `com.android.launcher3` |
| Xiaomi / POCO | `com.miui.home` |
| OnePlus | `com.oneplus.launcher` or `net.oneplus.launcher` |
| Oppo / Realme | `com.coloros.launcher` |
| Nothing | `com.nothing.launcher` |

### Swipe coordinates

`scroll()` is set for 1080 × 2400:

```python
sh("input", "swipe", 540, 1650, 540, 950, dur)
```

Read the screen size:

```bash
adb shell wm size
```

Example: `Physical size: 1080x2340`.

Compute:

- `x = width // 2`
- `start_y = int(height * 0.6875)`
- `end_y = int(height * 0.3958)`

For 1080 × 2340:

```python
sh("input", "swipe", 540, 1609, 540, 926, dur)
```

If the list barely moves, increase the distance. If it overshoots, decrease it.

### Output folder

Default is `~/ctp-logs` on every OS. Leave it unless the user wants a different
folder:

```bash
export CTP_OUTDIR=/path/to/logs
```

### Do not change

- `CTP = "com.closedtest.pro.closedtest_pro"`
- `CTP_ACT = CTP + "/.MainActivity"`

unless `adb shell pm list packages` shows a different package or the activity
resolves differently.

---

## Phase 6 — Dry run, then one app

### Dry run

```bash
python3 closed_test_pro.py --dry-run
```

Expected: a list of `OPEN <app name>` lines and `DONE`. No taps, no
screenshots.

If it finds nothing:

- Confirm the phone is on the Closed Test Pro list screen.
- Confirm the list has an **Open** button.
- Dump the UI and inspect it:

```bash
adb shell uiautomator dump /sdcard/ui.xml
adb shell cat /sdcard/ui.xml
```

### One-app test

```bash
python3 closed_test_pro.py --max-apps 1
```

Watch the phone. Verify:

1. The correct app opens.
2. It stays in the foreground for 35 seconds.
3. A screenshot appears in `~/ctp-logs/ctp-shots-*/`.
4. The script returns to Closed Test Pro.
5. It taps Feedback and closes the sheet.
6. The CSV has a row for the app.

If any step fails, go to Troubleshooting. Do not run the full list.

---

## Phase 7 — Full run

```bash
python3 closed_test_pro.py
```

Keep the phone connected and unlocked. Monitor the log. Stop if you see
repeated `FAILED` or `LEFT-APP` results.

At the end, collect:

```bash
ls -lt ~/ctp-logs | head
```

Report:

- `handled` count
- `progress` (e.g., `8/12 apps`)
- failures and their reasons
- log path
- CSV path
- screenshot folder path

Don't paste the entire log. Summarize and link the paths.

---

## Phase 8 — Optional scheduling

Only if the user asks. The phone must be connected, unlocked, and logged in.

### Windows Task Scheduler

```powershell
schtasks /Create /SC DAILY /TN "CTP Auto Take" /TR "python C:\path\to\closed_test_pro.py" /ST 09:00
```

### macOS / Linux cron

```bash
crontab -e
```

```cron
0 9 * * * /usr/bin/python3 /path/to/closed_test_pro.py
```

Warn the user: if the phone is asleep, locked, or disconnected, the scheduled
run will fail.

---

## Troubleshooting

| Symptom | Agent action |
|---|---|
| `adb: command not found` | Install Platform Tools, add to `PATH`, reopen the shell. |
| `no devices/emulators found` | Check cable (data, not charge-only), USB debugging, USB mode, Windows driver. Then `adb kill-server` and `adb devices`. |
| `unauthorized` | Ask the user to accept the prompt. If missing, revoke USB debugging authorizations and replug. |
| `offline` | `adb kill-server`, `adb start-server`, replug. |
| `uiautomator dump failed repeatedly` | Unlock the phone, close overlays, disable animations in Developer options, retry. |
| `am start failed` | Resolve the activity: `adb shell cmd package resolve-activity --brief com.closedtest.pro.closedtest_pro`. Update `CTP_ACT` only if it differs. |
| Stuck after tapping Open | `LAUNCHER` is wrong or a system dialog is showing. Check `adb shell dumpsys window | grep mCurrentFocus` and update `LAUNCHER`. |
| Opens the launcher, not the app | Update `LAUNCHER`. |
| Scroll doesn't move | Recompute the swipe coordinates from `wm size`. |
| Feedback button not found | The app may already be tested, the row is off-screen, or the UI changed. Refresh the list and inspect the UI dump. |
| Stops early | End of list or `--max-apps`. Check the log. |
| Screenshots are black | The app uses `FLAG_SECURE`; that's expected. Use the log/CSV as the record. |
| `screenshot failed` | Test `adb shell screencap -p /sdcard/test.png` and `adb pull /sdcard/test.png`. Unlock the phone. |
| CSV empty | `--dry-run` was used, or nothing was handled. |
| Phone locks mid-run | Unlock it and keep it connected. `stayon` doesn't override a manual lock. |
| CTP UI changed | Dump the UI, find the new `text`/`content-desc` values, and update the selectors. Ask before editing code. |

---

## What to tell the user at the end

Keep it short:

```text
Done.

Handled: N apps
Progress: X/Y
Failures: ...
Log: ~/ctp-logs/ctp-test-....log
CSV: ~/ctp-logs/ctp-test-....csv
Screenshots: ~/ctp-logs/ctp-shots-.../

The phone is back on the home screen. Want me to set up a daily schedule?
```

Also remind them:

- The script is unofficial.
- Automation may violate Closed Test Pro's terms.
- They should check the results before trusting a full run.

---

## One-shot prompt for the user

Copy this into the AI:

```text
Read LLME.md at <REPO URL> and follow it exactly.

Set up Closed Test Pro Auto Take on my computer for my Android phone.
Ask before installing anything or changing phone settings.
Do not ask for my Google password, PIN, or 2FA.
Run the dry run, then one app, then the full list.
At the end, give me the log, CSV, and screenshot paths.
```

If the AI can't open the URL, paste the contents of `LLME.md` and
`SETUP.md` into the chat.

---

## License

MIT. The script is provided as-is. The user is responsible for their account,
their phone, and their use of the tool.
