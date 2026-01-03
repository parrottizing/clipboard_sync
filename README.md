# Clipboard Sync

A bidirectional clipboard synchronization tool between Mac and Android. Sync text and images seamlessly between your devices via ADB.

## ✨ Features

- **📝 Text Sync** — Copy text on Mac → appears on Android, and vice versa
- **🖼️ Image Sync** — Copy images on Mac → sent to Android, and vice versa
- **📷 Finder Integration** — Select image files in Finder → automatically sent to Android
- **💬 Telegram Support** — Copy images from Telegram on Mac → sent to Android
- **🔄 Orientation Preservation** — Vertical images stay vertical when synced
- **🚀 Spotlight Launch** — Run with `ClipboardSync.app` directly from Spotlight

## Prerequisites

1. **Python 3** installed on your Mac
2. **ADB (Android Debug Bridge)** installed and added to your PATH
3. **Android Device** with USB Debugging enabled
4. **Pillow** for image processing (`pip install Pillow`)
5. **The Clipboard Sync Android app** installed on your device (see `android_app/README.md`)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd clipboard_sync
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Build and install the Android app (see [`android_app/README.md`](android_app/README.md))

## Usage

### Option 1: Run from Terminal
```bash
python3 sync_clipboard.py
```

### Option 2: Run from Spotlight
1. Open Spotlight (Cmd + Space)
2. Type "ClipboardSync"
3. Press Enter

### Option 3: Double-click
Double-click `start_sync.command` in Finder.

---

Once running, the sync works automatically:

| Action | Result |
|--------|--------|
| Copy text on Mac | Text appears in Android clipboard |
| Copy text on Android | Text appears in Mac clipboard |
| Copy image on Mac | Image sent to Android |
| Copy image on Android | Image appears in Mac clipboard |
| Select image file in Finder | Image sent to Android |

## How It Works

- **Mac → Android**: The script monitors the Mac clipboard for changes and sends content to Android via ADB broadcasts
- **Android → Mac**: The Android Accessibility Service writes clipboard content to a file, which the Mac script reads via ADB

## Troubleshooting

- **"No devices connected"**: Ensure your device appears in `adb devices`
- **Text not syncing to Android**: Ensure the Clipboard Sync Android app is installed and the Accessibility Service is enabled
- **Images not syncing**: Make sure Pillow is installed (`pip install Pillow`)
- **App not in Spotlight**: Move `ClipboardSync.app` to `/Applications` or add its location to Spotlight search paths

## Project Structure

```
clipboard_sync/
├── sync_clipboard.py      # Main Python sync script
├── start_sync.command     # Shell script to launch from Finder
├── ClipboardSync.app/     # macOS app bundle for Spotlight
├── requirements.txt       # Python dependencies
├── android_app/           # Android Accessibility Service app
│   └── README.md          # Android app build instructions
└── README.md              # This file
```
