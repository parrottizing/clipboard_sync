import time
import subprocess
import shlex
import pyperclip
import sys

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
    # Quote the text for the remote shell
    quoted_text = shlex.quote(text)
    
    # Construct the command string
    # Correct command for ch.pete.adbclipboard based on documentation
    # Action: ch.pete.adbclipboard.WRITE
    # Component: ch.pete.adbclipboard/.WriteReceiver
    # Extra: text
    cmd_str = f"am broadcast -a ch.pete.adbclipboard.WRITE -n ch.pete.adbclipboard/.WriteReceiver -e text {quoted_text}"
    
    try:
        # Use Popen to write to stdin of adb shell
        # This avoids adb client parsing issues with newlines in arguments
        process = subprocess.Popen(
            ["adb", "-s", device_id, "shell"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the command and get output
        stdout, stderr = process.communicate(input=cmd_str)
        
        if process.returncode == 0:
            # Check for broadcast specific errors in stdout/stderr if needed
            if "Error" in stderr or "inaccessible" in stderr:
                 print(f"[{device_id}] Potential error: {stderr.strip()}")
            else:
                 print(f"[{device_id}] Synced: {text[:30]}..." if len(text) > 30 else f"[{device_id}] Synced: {text}")
        else:
            print(f"[{device_id}] ADB failed: {stderr.strip()}")
            
    except Exception as e:
        print(f"[{device_id}] Exception during sync: {e}")

def main():
    print("Mac to Android Clipboard Sync Started...")
    print("Ensure 'AdbClipboard' app is installed and open on your Android device.")
    
    last_clipboard = ""
    
    try:
        while True:
            try:
                current_clipboard = pyperclip.paste()
            except Exception as e:
                print(f"Error reading clipboard: {e}")
                time.sleep(1)
                continue

            if current_clipboard != last_clipboard:
                if current_clipboard.strip():
                    devices = get_connected_devices()
                    if not devices:
                        print("No devices connected.")
                    else:
                        for device in devices:
                            send_to_device(device, current_clipboard)
                last_clipboard = current_clipboard
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping clipboard sync.")

if __name__ == "__main__":
    main()
