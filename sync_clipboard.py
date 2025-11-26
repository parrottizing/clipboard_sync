import time
import subprocess
import shlex
import pyperclip
import sys
import os

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

def read_from_device(device_id):
    """Reads clipboard content from a specific Android device."""
    try:
        # 1. Trigger the broadcast to read clipboard to file
        # Note: This might require user interaction on the device (tapping the floating window)
        # if the app doesn't have background permissions or on newer Android versions.
        subprocess.run(
            ["adb", "-s", device_id, "shell", "am", "broadcast", "-a", "ch.pete.adbclipboard.READ_CLIPBOARD", "-n", "ch.pete.adbclipboard/.ReadReceiver"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        
        # 2. Read the file content
        # The file path is standard for ch.pete.adbclipboard
        cmd = ["adb", "-s", device_id, "shell", "cat", "/sdcard/Android/data/ch.pete.adbclipboard/files/clipboard.txt"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            return result.stdout
        else:
            # If file doesn't exist or other error, return None or empty string
            return None
            
    except Exception as e:
        print(f"[{device_id}] Exception during read: {e}")
        return None

def main():
    print("Two-way Clipboard Sync Started (Mac <-> Android)...")
    print("Ensure 'AdbClipboard' app is installed and open on your Android device.")
    print("Note: For Android -> Mac sync, you might need to tap the AdbClipboard floating icon on your phone.")
    
    last_mac_clipboard = ""
    last_android_clipboard = ""
    
    # Initialize last_mac_clipboard
    try:
        last_mac_clipboard = pyperclip.paste()
    except:
        pass

    try:
        while True:
            devices = get_connected_devices()
            if not devices:
                print("No devices connected. Waiting...")
                time.sleep(2)
                continue

            # --- Mac to Android ---
            try:
                current_mac_clipboard = pyperclip.paste()
            except Exception as e:
                print(f"Error reading Mac clipboard: {e}")
                current_mac_clipboard = last_mac_clipboard

            if current_mac_clipboard != last_mac_clipboard:
                if current_mac_clipboard.strip():
                    for device in devices:
                        send_to_device(device, current_mac_clipboard)
                    # Update both to avoid loop
                    last_mac_clipboard = current_mac_clipboard
                    last_android_clipboard = current_mac_clipboard 

            # --- Android to Mac ---
            # We'll check Android clipboard every cycle
            for device in devices:
                android_content = read_from_device(device)
                
                if android_content is not None:
                    # Check if it's different from what we last knew AND different from current Mac clipboard
                    # (to avoid immediate echo back if Mac just updated it)
                    if android_content != last_android_clipboard and android_content != current_mac_clipboard:
                        if android_content.strip():
                            print(f"[{device}] Received from Android: {android_content[:30]}..." if len(android_content) > 30 else f"[{device}] Received from Android: {android_content}")
                            pyperclip.copy(android_content)
                            last_mac_clipboard = android_content
                            last_android_clipboard = android_content
            
            time.sleep(1) # Poll interval
            
    except KeyboardInterrupt:
        print("\nStopping clipboard sync.")

if __name__ == "__main__":
    main()
