# Mac to Android Clipboard Sync

A simple Python tool to synchronize your Mac clipboard to a connected Android device via ADB.

## Prerequisites

1.  **Python 3** installed on your Mac.
2.  **ADB (Android Debug Bridge)** installed and added to your PATH.
3.  **Android Device** with USB Debugging enabled.
4.  **[AdbClipboard](https://github.com/PRosenb/AdbClipboard)** app installed on your Android device.

## Installation

1.  Clone this repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Connect your Android device via USB or WiFi.
2.  Ensure the **AdbClipboard** app is installed on your phone.
3.  Run the script:
    ```bash
    python3 sync_clipboard.py
    ```
4.  Copy text on your Mac. It will automatically appear in your Android clipboard!

## Troubleshooting

-   **"Failed to sync..."**: Ensure your device is listed in `adb devices`.
-   **Nothing happens on phone**: Ensure you have the `ch.pete.adbclipboard` app installed (AdbClipboard) and it has been opened at least once.
