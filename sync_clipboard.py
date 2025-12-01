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
    # Updated to use the custom app's WriteReceiver
    cmd_str = f"am broadcast -a com.example.clipboard.WRITE -n com.example.clipboard/.WriteReceiver -e text {quoted_text}"
    
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

def read_from_device(device_id):
    """Reads clipboard content from a specific Android device."""
    try:
        # The Accessibility Service automatically writes to this file
        # /sdcard/Android/data/com.example.clipboard/files/clipboard.txt
        
        cmd = ["adb", "-s", device_id, "shell", "cat", "/sdcard/Android/data/com.example.clipboard/files/clipboard.txt"]
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
                if "SemClipboardToastController" in line and "Copy toast is shown" in line:
                    clipboard_event_queue.put(self.device_id)
                elif "ClipboardListener" in line and "showCopyToast" in line:
                    clipboard_event_queue.put(self.device_id)
                # Also listen for our own app's logs to confirm it saw the change
                elif "ClipboardMonitor" in line and "Clipboard changed:" in line:
                    clipboard_event_queue.put(self.device_id)
                    
        except Exception as e:
            print(f"[{self.device_id}] Logcat monitor error: {e}")
        finally:
            process.terminate()

def main():
    print("Two-way Clipboard Sync Started (Mac <-> Android)...")
    print("Ensure 'Clipboard Sync' app is installed and Accessibility Service is enabled.")
    
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
    # Track last read time globally to debounce rapid events across duplicate device entries
    last_global_read_time = 0

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
                    
                    current_time = time.time()
                    
                    # Check for feedback loop (ignore events shortly after we sent data)
                    if event_device_id in last_send_time:
                        if current_time - last_send_time[event_device_id] < 3.0:
                            print(f"[{event_device_id}] Ignoring echo event (feedback loop protection)")
                            continue

                    # Check for rapid duplicate events (global debounce)
                    if current_time - last_global_read_time < 1.0:
                         # print(f"[{event_device_id}] Ignoring rapid duplicate event (global debounce)")
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
                                last_global_read_time = current_time
            
            except queue.Empty:
                pass
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping clipboard sync.")
        for monitor in monitors.values():
            monitor.stop_event.set()

if __name__ == "__main__":
    main()
