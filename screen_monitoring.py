import psutil
import time
import win32gui
import win32con
import win32process
import win32api
from pynput import keyboard # type: ignore
from datetime import datetime, timedelta
from pynput.keyboard import Key # type: ignore
import os 

# Set exam duration in minutes
EXAM_DURATION_MIN = 30

# Blacklisted apps
blacklist = ['chrome.exe', 'discord.exe', 'whatsapp.exe', 'telegram.exe', 'msedge.exe']
# Add your allowed app/window title here
allowed_window_titles = ['Exam Portal', 'exam.html', 'Python', 'MyExamApp','screen_monitoring.py']  # You can customize these

# Logging
def log_event(event):
    with open("proctoring_log.txt", "a") as f:
        f.write(f"{datetime.now()} - {event}\n")
    print(f"🚨 {event}")

# 1. Unauthorized Apps Detection + Auto Termination
terminated_pids = set()

def check_blacklisted_apps():
    global terminated_pids
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            pid = proc.info['pid']
            if name in blacklist and pid not in terminated_pids:
                log_event(f"Unauthorized App Detected: {name} (Terminating...)")
                psutil.Process(pid).terminate()
                terminated_pids.add(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            continue


# 2. Active Window Monitoring
last_window = None
def detect_tab_switching():
    global last_window
    try:
        hwnd = win32gui.GetForegroundWindow()
        current_window = win32gui.GetWindowText(hwnd)

        if last_window != current_window:
            last_window = current_window

            # If current window is NOT allowed
            if not any(allowed.lower() in current_window.lower() for allowed in allowed_window_titles):
                log_event(f"❌ Unauthorized window switched: {current_window}")

                # Optional: force user back to allowed window
                # flash the taskbar icon
                win32gui.FlashWindow(hwnd, True)

                # Optional: show popup warning
                # import pymsgbox; pymsgbox.alert("Unauthorized window! Return to exam immediately.")

    except Exception:
        pass

ctrl_pressed = False
alt_pressed = False

def on_key_press(key):
    global ctrl_pressed, alt_pressed
    try:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            ctrl_pressed = True
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_pressed = True
        elif key == keyboard.Key.f2:
            log_event("F2 Key Pressed")
        elif key == keyboard.Key.f5:
            log_event("F5 Key Pressed (Refresh)")
        elif ctrl_pressed and key == keyboard.KeyCode.from_char('c'):
            log_event("Ctrl+C Pressed (Copy)")
        elif ctrl_pressed and key == keyboard.KeyCode.from_char('v'):
            log_event("Ctrl+V Pressed (Paste)")
        elif alt_pressed and key == keyboard.Key.tab:
            log_event("Alt+Tab Pressed (App Switch)")
        elif alt_pressed and key == keyboard.Key.f4:
            log_event("Alt+F4 Pressed (Close Window)")
        elif key == keyboard.Key.cmd:
            log_event("Windows Key Pressed (Start Menu)")
        # ❌ Do NOT allow Esc to exit the program
        elif key == keyboard.Key.esc:
            log_event("⚠️ Esc Key Pressed (Ignored for security)")

        # ✅ Proctor Exit: Ctrl + Q
        elif ctrl_pressed and key == keyboard.KeyCode.from_char('q'):
            log_event("🔐 Proctor Exit Triggered - Ctrl+Q Pressed")
            os._exit(0)  # Force exit
    except Exception:
        pass

def on_key_release(key):
    global ctrl_pressed, alt_pressed
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        ctrl_pressed = False
    if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
        alt_pressed = False


# Main Proctoring Function
def start_proctoring():
    print("🛡️ AI Proctoring Started...")
    log_event("Exam session started")

    # Start keyboard listener
    listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    listener.start()

    # Start timer
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=EXAM_DURATION_MIN)

    while datetime.now() < end_time:
        check_blacklisted_apps()
        detect_tab_switching()
        time.sleep(2)  # check every 2 seconds

    log_event("Exam session ended")
    print("✅ Exam finished.")

if __name__ == "__main__":
    start_proctoring()