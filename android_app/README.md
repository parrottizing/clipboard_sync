# Clipboard Sync Android App

This is an Accessibility Service app that monitors the clipboard in the background.

## How to Build and Install

1. Open this folder (`android_app`) in **Android Studio**.
2. Wait for Gradle sync to complete.
3. Connect your Android device via USB (ensure ADB debugging is on).
4. Click the **Run** button (green play icon) in Android Studio.

## Setup on Device

1. After installation, the app will not open a UI (it's a background service).
2. Go to **Settings > Accessibility**.
3. Find **Clipboard Sync** (or "Installed Apps" > "Clipboard Sync").
4. **Enable** the service.
5. Allow the permission warning.

Now the app will silently write clipboard content to `/sdcard/Android/data/com.example.clipboard/files/clipboard.txt`.
