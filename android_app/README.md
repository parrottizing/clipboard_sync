# Clipboard Sync Android App

An Accessibility Service app that enables bidirectional clipboard sync between your Android device and Mac.

## Features

- **📝 Text Sync** — Monitors clipboard for text and syncs with Mac
- **🖼️ Image Sync** — Receives images from Mac and saves them to your device
- **🔇 Silent Background Service** — No UI, runs in background via Accessibility Service

## How to Build and Install

1. Open this folder (`android_app`) in **Android Studio**
2. Wait for Gradle sync to complete
3. Connect your Android device via USB (ensure ADB debugging is on)
4. Click the **Run** button (green play icon) in Android Studio

Alternatively, build from command line:
```bash
./gradlew installDebug
```

## Setup on Device

After installation, you need to enable the Accessibility Service:

1. Go to **Settings > Accessibility**
2. Find **Clipboard Sync** (may be under "Installed Apps" or "Downloaded Services")
3. **Enable** the service
4. Accept the permission warning

> **Note**: The app has no visible UI — it runs entirely as a background service.

## How It Works

| Direction | Mechanism |
|-----------|-----------|
| **Android → Mac** | Clipboard content is written to `/sdcard/Android/data/com.example.clipboard/files/clipboard.txt`, which the Mac script reads via ADB |
| **Mac → Android** | The Mac script sends ADB broadcasts that the app receives and writes to the Android clipboard |

## Data Location

- **Text clipboard**: `/sdcard/Android/data/com.example.clipboard/files/clipboard.txt`
- **Received images**: Saved to device storage

## Troubleshooting

- **Service not appearing**: Make sure the app is installed and restart your device
- **Clipboard not syncing**: Verify the Accessibility Service is enabled in Settings
- **Permission issues**: Some devices require additional permissions for background services

## Requirements

- Android 7.0 (API 24) or higher
- USB Debugging enabled for ADB connection
