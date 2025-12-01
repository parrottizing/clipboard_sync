import time
import subprocess
import shlex
import pyperclip
import sys
import os
import threading
import queue

# Global queue to communicate between threads
clipboard_event_queue = queue.Queue()

def get_connected_devices():
    """Returns a list of connected device IDs."""
    try:
        output = subprocess.check_output(["adb", "devices"]).decode("utf-8")
        devices = []
        for line in output.splitlines()[1:]:
            if line.strip() and "device" in line:
                parts = line.split()
                if parts[1] == "device":
                    devices.append(parts[0])
        return devices
    except subprocess.CalledProcessError:
        return []

def send_to_device(device_id, text):
    """Sends text to a specific Android device via ADB broadcast using stdin."""
    quoted_text = shlex.quote(text)
    cmd_str = f"am broadcast -a ch.pete.adbclipboard.WRITE -n ch.pete.adbclipboard/.WriteReceiver -e text {quoted_text}"
    
    try:
        process = subprocess.Popen(
            ["adb", "-s", device_id, "shell"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=cmd_str)
        
        if process.returncode == 0:
            if "Error" in stderr or "inaccessible" in stderr:
                 print(f"[{device_id}] Potential error sending: {stderr.strip()}")
            else:
                 print(f"[{device_id}] Sent to Android: {text[:30]}..." if len(text) > 30 else f"[{device_id}] Sent to Android: {text}")
        else:
            print(f"[{device_id}] ADB failed sending: {stderr.strip()}")
            
    except Exception as e:
        print(f"[{device_id}] Exception during send: {e}")

import re

def trigger_clipboard_write(device_id):
    """
    Triggers the clipboard write by tapping the floating icon.
    Finds the window coordinates dynamically.
    """
    try:
        # 1. Get PID of the app
        pid_cmd = ["adb", "-s", device_id, "shell", "pidof", "ch.pete.adbclipboard"]
        pid_result = subprocess.run(pid_cmd, capture_output=True, text=True)
        pid = pid_result.stdout.strip()
        
        if not pid:
            print(f"[{device_id}] App not running. Launching...")
            subprocess.run(["adb", "-s", device_id, "shell", "monkey", "-p", "ch.pete.adbclipboard", "-c", "android.intent.category.LAUNCHER", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            # Try getting PID again
            pid_result = subprocess.run(pid_cmd, capture_output=True, text=True)
            pid = pid_result.stdout.strip()
            if not pid:
                print(f"[{device_id}] Failed to launch app.")
                return False

        # 2. Find window bounds using dumpsys
        # We look for a window that matches the PID or package name and has a valid frame
        dumpsys_cmd = ["adb", "-s", device_id, "shell", "dumpsys", "window", "windows"]
        dumpsys_result = subprocess.run(dumpsys_cmd, capture_output=True, text=True)
        
        # Regex to find window block for our PID or package
        # We look for "Window{... ch.pete.adbclipboard ...}" or similar, then the "Frames" line
        # The output format is complex, so we'll try to find the specific window name usually associated with the overlay
        # Based on logs, it might be "PopupWindow:..." or just associated with the PID
        
        lines = dumpsys_result.stdout.splitlines()
        target_window_found = False
        bounds = None
        
        current_window = None
        
        for line in lines:
            line = line.strip()
            if "Window{" in line and (pid in line or "ch.pete.adbclipboard" in line):
                current_window = line
                target_window_found = True
                continue
            
            if target_window_found and "Frames:" in line:
                # Format: Frames: parent=[0,81][1080,2196] display=[0,81][1080,2196] frame=[5,157][233,385]
                match = re.search(r"frame=\[(\d+),(\d+)\]\[(\d+),(\d+)\]", line)
                if match:
                    left, top, right, bottom = map(int, match.groups())
                    if right - left > 0 and bottom - top > 0:
                        bounds = (left, top, right, bottom)
                        break # Found a valid window
        
        if not bounds:
            print(f"[{device_id}] Could not find window bounds for overlay.")
            return False
            
        left, top, right, bottom = bounds
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        print(f"[{device_id}] Tapping at {center_x}, {center_y} (Window: {left},{top} - {right},{bottom})")
        
        # 3. Tap the center
        subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(center_x), str(center_y)], check=False)
        return True

    except Exception as e:
        print(f"[{device_id}] Error triggering write: {e}")
        return False

def read_from_device(device_id):
    """Reads clipboard content from a specific Android device."""
    try:
        # 1. Trigger the clipboard write (Tap method)
        if not trigger_clipboard_write(device_id):
            # Fallback to broadcast if tap fails (though unlikely to work for background)
            print(f"[{device_id}] Tap failed, trying broadcast...")
            subprocess.run(
                ["adb", "-s", device_id, "shell", "am", "broadcast", "-a", "ch.pete.adbclipboard.READ_CLIPBOARD", "-n", "ch.pete.adbclipboard/.ReadReceiver"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        
        # Give it a moment to write the file
        time.sleep(0.5)

        # 2. Read the file content
        cmd = ["adb", "-s", device_id, "shell", "cat", "/sdcard/Android/data/ch.pete.adbclipboard/files/clipboard.txt"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return None
            
    except Exception as e:
        print(f"[{device_id}] Exception during read: {e}")
        return None

class LogcatMonitor(threading.Thread):
    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
        self.daemon = True
        self.stop_event = threading.Event()

    def run(self):
        print(f"[{self.device_id}] Starting Logcat Monitor...")
        # Clear logs first
        subprocess.run(["adb", "-s", self.device_id, "logcat", "-c"], stderr=subprocess.DEVNULL)
        
        process = subprocess.Popen(
            ["adb", "-s", self.device_id, "logcat", "-v", "time"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors='replace'
        )
        
        try:
            while not self.stop_event.is_set():
                line = process.stdout.readline()
                if not line:
                    break
                
                # Check for specific keywords indicating a copy action
                # "SemClipboardToastController" is for Samsung
                # "ClipboardListener.showCopyToast" is generic Android
                if "SemClipboardToastController" in line and "Copy toast is shown" in line:
                    clipboard_event_queue.put(self.device_id)
                elif "ClipboardListener" in line and "showCopyToast" in line:
                    clipboard_event_queue.put(self.device_id)
                    
        except Exception as e:
            print(f"[{self.device_id}] Logcat monitor error: {e}")
        finally:
            process.terminate()

def main():
    print("Two-way Clipboard Sync Started (Mac <-> Android)...")
    print("Ensure 'AdbClipboard' app is installed and open on your Android device.")
    print("Monitoring for copy events to trigger auto-sync...")
    
    last_mac_clipboard = ""
    last_android_clipboard = ""
    
    # Initialize last_mac_clipboard
    try:
        last_mac_clipboard = pyperclip.paste()
    except:
        pass

    # Start logcat monitors for connected devices
    devices = get_connected_devices()
    monitors = {}
    for device in devices:
        monitor = LogcatMonitor(device)
        monitor.start()
        monitors[device] = monitor

    # Track last send time to avoid feedback loops
    last_send_time = {}

    try:
        while True:
            # Check for new devices or disconnected devices (basic handling)
            current_devices = get_connected_devices()
            for device in current_devices:
                if device not in monitors:
                    monitor = LogcatMonitor(device)
                    monitor.start()
                    monitors[device] = monitor
            
            # --- Mac to Android ---
            try:
                current_mac_clipboard = pyperclip.paste()
            except Exception as e:
                print(f"Error reading Mac clipboard: {e}")
                current_mac_clipboard = last_mac_clipboard

            if current_mac_clipboard != last_mac_clipboard:
                if current_mac_clipboard.strip():
                    for device in current_devices:
                        send_to_device(device, current_mac_clipboard)
                        last_send_time[device] = time.time()
                    last_mac_clipboard = current_mac_clipboard
                    last_android_clipboard = current_mac_clipboard 

            # --- Android to Mac (Event Driven) ---
            try:
                # Check if any device reported a copy event
                # We use a non-blocking get
                while True:
                    event_device_id = clipboard_event_queue.get_nowait()
                    
                    # Check for feedback loop (ignore events shortly after we sent data)
                    if event_device_id in last_send_time:
                        if time.time() - last_send_time[event_device_id] < 3.0:
                            print(f"[{event_device_id}] Ignoring echo event (feedback loop protection)")
                            continue

                    print(f"[{event_device_id}] Detected copy event! Syncing...")
                    
                    android_content = read_from_device(event_device_id)
                    
                    if android_content is not None:
                        if android_content != last_android_clipboard and android_content != current_mac_clipboard:
                            if android_content.strip():
                                print(f"[{event_device_id}] Received from Android: {android_content[:30]}..." if len(android_content) > 30 else f"[{event_device_id}] Received from Android: {android_content}")
                                pyperclip.copy(android_content)
                                last_mac_clipboard = android_content
                                last_android_clipboard = android_content
            except queue.Empty:
                pass
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping clipboard sync.")
        for monitor in monitors.values():
            monitor.stop_event.set()

if __name__ == "__main__":
    main()
