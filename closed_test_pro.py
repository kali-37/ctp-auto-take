#!/usr/bin/env python3
"""
Closed Test Pro daily-testing automation.

Cycle per app:
  Open -> target app 35 s -> screenshot -> HOME -> Closed Test Pro -> Feedback
  -> close sheet -> restart Closed Test Pro (prevents the list-scroll freeze)

Scans from the top of the list for the next untested "Open" row.
"""

import argparse
import csv
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Blank = use the only connected device. Set CTP_SERIAL if you have more than one.
SERIAL = os.environ.get("CTP_SERIAL", "")
CTP = "com.closedtest.pro.closedtest_pro"
CTP_ACT = CTP + "/.MainActivity"
LAUNCHER = "com.sec.android.app.launcher"
OUTDIR = Path(os.environ.get("CTP_OUTDIR", str(Path.home() / "ctp-logs")))
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_PATH = OUTDIR / f"ctp-test-{STAMP}.log"
CSV_PATH = OUTDIR / f"ctp-test-{STAMP}.csv"
SHOT_DIR = OUTDIR / f"ctp-shots-{STAMP}"
SHOTS = []
CAPTURE_SHOTS = True


def adb(*args, timeout=40):
    cmd = ["adb"]
    if SERIAL:
        cmd += ["-s", SERIAL]
    cmd += [str(a) for a in args]
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def adb_bytes(*args, timeout=40):
    """Run adb and return raw stdout bytes (for screenshots)."""
    cmd = ["adb"]
    if SERIAL:
        cmd += ["-s", SERIAL]
    cmd += [str(a) for a in args]
    return subprocess.run(cmd, capture_output=True, timeout=timeout).stdout


def sh(*args, timeout=40):
    return adb("shell", *args, timeout=timeout).stdout


def log(msg):
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def screenshot(tag):
    """Capture a PNG straight from the device and return its local path."""
    if not CAPTURE_SHOTS:
        return ""

    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", tag).strip("-")[:60] or "shot"
    path = SHOT_DIR / f"{len(SHOTS) + 1:02d}-{safe}.png"

    data = adb_bytes("exec-out", "screencap", "-p")
    if data.startswith(b"\x89PNG"):
        path.write_bytes(data)
    else:
        # Older adb/devices: capture to the SD card and pull it.
        remote = "/sdcard/_ctp_shot.png"
        adb("shell", "screencap", "-p", remote)
        adb("pull", remote, str(path))
        adb("shell", "rm", "-f", remote)
        if not path.exists() or path.stat().st_size == 0:
            log(f"screenshot failed: {tag}")
            return ""

    SHOTS.append(path)
    log(f"screenshot: {path}")
    return str(path)


def dump_ui():
    for _ in range(10):
        r = adb("shell", "uiautomator", "dump", "/sdcard/_ctp_ui.xml")
        if "dumped" in ((r.stdout or "") + (r.stderr or "")).lower():
            xml = adb("shell", "cat", "/sdcard/_ctp_ui.xml").stdout
            try:
                return ET.fromstring(xml)
            except ET.ParseError:
                pass
        time.sleep(0.5)
    raise RuntimeError("uiautomator dump failed repeatedly")


def bounds_of(n):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
    if not m:
        raise ValueError(n.get("bounds"))
    return tuple(int(v) for v in m.groups())


def center(b):
    return (b[0] + b[2]) // 2, (b[1] + b[3]) // 2


def tap(x, y):
    sh("input", "tap", x, y)


def focus_pkg():
    out = sh("dumpsys", "window")
    m = re.findall(r"mCurrentFocus=Window\{[0-9a-f]+ u\d+ ([^/}\s]+)", out)
    return m[-1] if m else ""


def find_clickable(root, labels):
    wanted = {l.lower() for l in labels}
    for n in root.iter():
        if n.get("clickable") != "true":
            continue
        t = (n.get("text") or "").strip().lower()
        d = (n.get("content-desc") or "").strip().lower()
        if t in wanted or d in wanted:
            return n
    return None


def rows(root):
    out = []
    for n in root.iter():
        if not (n.get("class") or "").endswith("ImageView"):
            continue
        d = n.get("content-desc") or ""
        if "\n" not in d:
            continue
        name, status = d.split("\n", 1)
        out.append((name.strip(), status.strip(), bounds_of(n)))
    return out


def row_for_y(row_list, y):
    best, best_dist = None, 10 ** 9
    for name, status, b in row_list:
        cy = (b[1] + b[3]) // 2
        if b[1] - 80 <= y <= b[3] + 80:
            dist = abs(cy - y)
            if dist < best_dist:
                best, best_dist = (name, status, b), dist
    return best


def open_buttons(root):
    out, rs = [], rows(root)
    for n in root.iter():
        if n.get("clickable") != "true":
            continue
        if (n.get("content-desc") or "").strip() != "Open" and (n.get("text") or "").strip() != "Open":
            continue
        b = bounds_of(n)
        row = row_for_y(rs, (b[1] + b[3]) // 2)
        out.append((row[0] if row else "?", b))
    return out


def feedback_button(root, name, row_b):
    ys = (row_b[1] - 80, row_b[3] + 80)
    for n in root.iter():
        if n.get("clickable") != "true":
            continue
        d = (n.get("content-desc") or "").strip()
        t = (n.get("text") or "").strip()
        if d != "Feedback" and t != "Feedback":
            continue
        b = bounds_of(n)
        if ys[0] <= (b[1] + b[3]) // 2 <= ys[1]:
            return n
    return None


def scroll(direction, dur=400):
    # inside the scrollable list only: below the progress header, above the snackbar
    if direction == "down":
        sh("input", "swipe", 540, 1650, 540, 950, dur)
    else:
        sh("input", "swipe", 540, 950, 540, 1650, dur)
    time.sleep(1.2)


def start_ctp():
    for attempt in range(3):
        r = adb("shell", "am", "start", "-n", CTP_ACT)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        if "Error" not in out:
            break
        log(f"am start failed (attempt {attempt+1}): {out}")
        time.sleep(2.0)
    time.sleep(2.5)

    root = dump_ui()
    # wait for the CTP UI (prompt or list) to render, up to ~20 s
    for _ in range(24):
        descs = [(n.get("content-desc") or "") for n in root.iter()]
        texts = [(n.get("text") or "") for n in root.iter()]
        if any("Daily Testing" in d or "Today's Progress" in d for d in descs) or \
           any("tested" in t.lower() and "apps" in t.lower() for t in texts):
            break
        time.sleep(0.8)
        root = dump_ui()

    # dismiss the daily-testing prompt if present
    for _ in range(2):
        n = find_clickable(root, ["Let's Start", "Lets Start"])
        if n is None:
            n = find_clickable(root, ["Remind Later", "Not now"])
        if n is None:
            break
        tap(*center(bounds_of(n)))
        time.sleep(1.5)
        root = dump_ui()


def restart_ctp():
    sh("am", "force-stop", CTP)
    time.sleep(2.0)
    start_ctp()


def go_home():
    sh("input", "keyevent", "KEYCODE_HOME")
    time.sleep(1.2)


def wait_app(timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        pkg = focus_pkg()
        if pkg in ("", LAUNCHER, CTP):
            time.sleep(0.5)
            continue
        if "permissioncontroller" in pkg:
            log(f"permission dialog ({pkg}) - dismissing")
            sh("input", "keyevent", "KEYCODE_BACK")
            time.sleep(1.3)
            continue
        return pkg, time.time() - t0
    return None, time.time() - t0


def close_feedback_sheet():
    root = dump_ui()
    n = find_clickable(root, ["Close sheet"])
    if n is None:
        cands = [x for x in root.iter() if (x.get("content-desc") or "").strip().lower() == "close"]
        if cands:
            n = min(cands, key=lambda x: bounds_of(x)[1])
    if n is not None:
        tap(*center(bounds_of(n)))
        time.sleep(1.2)
    else:
        sh("input", "keyevent", "KEYCODE_BACK")
        time.sleep(1.2)


def return_to_ctp():
    go_home()
    start_ctp()


def handle_feedback(name):
    root = dump_ui()
    r = next((r for r in rows(root) if r[0] == name), None)

    if r is None:
        for _ in range(3):
            scroll("down")
            root = dump_ui()
            r = next((r for r in rows(root) if r[0] == name), None)
            if r:
                break
        if r is None:
            for _ in range(6):
                scroll("up")
                root = dump_ui()
                r = next((r for r in rows(root) if r[0] == name), None)
                if r:
                    break

    if r is None:
        log(f"feedback: row for {name} not found")
        return "ROW-NOT-FOUND"
    if "tested" in r[1].lower():
        log(f"feedback: {name} already Tested Today, nothing to click")
        return "ALREADY-TESTED"

    btn = feedback_button(root, name, r[2])
    if btn is None:
        time.sleep(2.0)
        root = dump_ui()
        r = next((rr for rr in rows(root) if rr[0] == name), None)
        if r:
            btn = feedback_button(root, name, r[2])
    if btn is None:
        log(f"feedback: no Feedback button for {name} (status: {r[1]})")
        return "NO-FEEDBACK"

    log(f"feedback: tapping Feedback for {name}")
    tap(*center(bounds_of(btn)))
    time.sleep(2.5)
    close_feedback_sheet()
    if focus_pkg() != CTP:
        return_to_ctp()
    log("feedback: back on Closed Test Pro")
    return "CLICKED"


def scroll_to_top():
    for _ in range(16):
        root = dump_ui()
        if any("Today's Progress" in (n.get("content-desc") or "") for n in root.iter()):
            return root
        scroll("up")
    return dump_ui()


def progress_text(root):
    for n in root.iter():
        d = (n.get("content-desc") or "").strip()
        if re.match(r"^\d+\s*/\s*\d+\s*apps$", d):
            return d
    return "?"


def visible_names(root):
    return {r[0] for r in rows(root)}


def find_next_open(tested):
    """Scan from the current (top) position downward; return first untested Open."""
    no_move = 0
    for _ in range(24):
        root = dump_ui()
        for name, b in open_buttons(root):
            if name not in tested:
                return name, b
        before = visible_names(root)
        scroll("down")
        after = visible_names(dump_ui())
        if after == before or not after:
            no_move += 1
            if no_move >= 2:
                return None
        else:
            no_move = 0
    return None


def main():
    global CAPTURE_SHOTS

    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=35.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-apps", type=int, default=0)
    ap.add_argument("--no-screenshots", action="store_true",
                    help="do not capture PNG screenshots over ADB")
    args = ap.parse_args()

    CAPTURE_SHOTS = not args.no_screenshots and not args.dry_run

    OUTDIR.mkdir(parents=True, exist_ok=True)
    log(f"CTP automation start | duration={args.duration}s dry_run={args.dry_run} screenshots={CAPTURE_SHOTS}")
    sh("svc", "power", "stayon", "true")
    sh("input", "keyevent", "KEYCODE_WAKEUP")

    restart_ctp()
    root = dump_ui()
    log(f"today progress: {progress_text(root)}")
    screenshot("start")

    tested, results, total = set(), [], 0
    started = time.time()

    for _ in range(40):
        name_b = find_next_open(tested)
        if name_b is None:
            break
        name, b = name_b
        log(f"OPEN {name}")

        if args.dry_run:
            tested.add(name)
            total += 1
            if args.max_apps and total >= args.max_apps:
                break
            continue

        tap(*center(b))
        pkg, delay = wait_app(timeout=20.0)
        if pkg is None:
            log(f"FAILED to launch {name}")
            shot = screenshot(f"{name}-failed")
            results.append(["FAILED", name, "", "", "", shot])
            tested.add(name)
            restart_ctp()
            continue

        log(f"{name} -> {pkg} (launched in {delay:.1f}s), waiting {args.duration:.0f}s")
        time.sleep(max(0.0, args.duration - delay))
        shot = screenshot(f"{name}-open")
        end_pkg = focus_pkg()
        log(f"{name} done (end focus: {end_pkg or '?'})")

        return_to_ctp()
        fb = handle_feedback(name)
        results.append(["OK" if end_pkg and end_pkg != LAUNCHER else "LEFT-APP",
                        name, pkg, f"{delay:.1f}", fb, shot])
        tested.add(name)
        total += 1
        log(f"progress now: {progress_text(dump_ui())}")

        restart_ctp()  # fresh scroll state for the next scan
        if args.max_apps and total >= args.max_apps:
            break

    elapsed = time.time() - started
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["result", "app", "package", "launch_delay_s", "feedback", "screenshot"])
        w.writerows(results)

    root = dump_ui()
    screenshot("done")
    log(f"DONE | handled={total} | progress={progress_text(root)} | elapsed={elapsed/60:.1f} min")
    if CAPTURE_SHOTS:
        log(f"screenshots: {SHOT_DIR} ({len(SHOTS)} files)")
    log(f"log: {LOG_PATH}")
    log(f"csv: {CSV_PATH}")
    go_home()


if __name__ == "__main__":
    main()
