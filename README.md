# Closed Test Pro automation

Automates the daily testing routine in the **Closed Test Pro** Android app.

New here? Read the **[full setup guide](SETUP.md)**. Want an AI to do the setup? Hand **[LLME.md](LLME.md)** to a coding agent.

## Let an AI do the setup

Hand [`LLME.md`](LLME.md) to ChatGPT, Claude, Cursor, Gemini, or any coding
agent and say:

> "Read this file and set up Closed Test Pro Auto Take for me. Ask before
> installing anything."

The agent inspects the machine, installs Python/adb if needed, configures the
script for the phone, runs a dry run, tests one app, then runs the full list.

For every list row with an **Open** button it:

1. taps **Open** and launches the target app
2. keeps it in the foreground for **35 seconds**
3. captures a PNG screenshot straight from the device over ADB
4. returns to Closed Test Pro
5. taps **Feedback** and closes the Play Store sheet
6. restarts Closed Test Pro (prevents the list-scroll freeze)

It scans the whole list from the top, skips already-tested and paused rows,
and stops when no untested **Open** row remains.

## Requirements

- Samsung phone connected over USB with USB debugging authorized (`adb devices` shows `device`)
- Closed Test Pro installed and logged in
- Python 3.9+ and Android Platform Tools (`adb`)

## Setup

`adb` uses the only connected device by default. If you have more than one
device attached, set the serial:

```bash
export CTP_SERIAL=<YOUR_SERIAL>        # macOS/Linux
set CTP_SERIAL=<YOUR_SERIAL>           # Windows CMD
$env:CTP_SERIAL="<YOUR_SERIAL>"        # Windows PowerShell
```

Or edit `SERIAL` at the top of the script. Do not commit your real serial.

Logs go to `~/ctp-logs` by default. Override with `CTP_OUTDIR`.

The launcher package (`com.sec.android.app.launcher`) and the swipe
coordinates in `scroll()` are set for a Samsung 1080x2400 screen. On another
device, update those two values.

## Usage

```bash
# list the Open apps without testing anything
python3 closed_test_pro.py --dry-run

# run the full daily testing
python3 closed_test_pro.py

# shorter/longer per-app duration, or stop after N apps
python3 closed_test_pro.py --duration 35 --max-apps 5

# disable screenshots
python3 closed_test_pro.py --no-screenshots
```

## Output

Each run writes to `~/ctp-logs/` (or `CTP_OUTDIR`):

- `ctp-test-<stamp>.log` — full timeline
- `ctp-test-<stamp>.csv` — one row per app, including the screenshot path
- `ctp-shots-<stamp>/` — PNGs captured over ADB (`start`, each app, failures, `done`)

Some apps block screenshots with `FLAG_SECURE`; those PNGs will be black.

## Disclaimer

Unofficial and not affiliated with Closed Test Pro or Google. Automation may
violate Closed Test Pro's terms — use at your own risk.
