package com.example.clipboard;

import android.accessibilityservice.AccessibilityService;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

public class ClipboardMonitorService extends AccessibilityService {

    private static final String TAG = "ClipboardMonitor";
    private ClipboardManager.OnPrimaryClipChangedListener listener;

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        Log.d(TAG, "Service Connected");

        final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        listener = new ClipboardManager.OnPrimaryClipChangedListener() {
            @Override
            public void onPrimaryClipChanged() {
                if (clipboard.hasPrimaryClip()) {
                    ClipData clip = clipboard.getPrimaryClip();
                    if (clip != null && clip.getItemCount() > 0) {
                        CharSequence text = clip.getItemAt(0).getText();
                        if (text != null) {
                            Log.d(TAG, "Clipboard changed: " + text);
                            saveToFile(text.toString());
                        }
                    }
                }
            }
        };
        clipboard.addPrimaryClipChangedListener(listener);
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // We don't strictly need to do anything here for clipboard monitoring
    }

    @Override
    public void onInterrupt() {
    }

    @Override
    public boolean onUnbind(android.content.Intent intent) {
        if (listener != null) {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            clipboard.removePrimaryClipChangedListener(listener);
        }
        return super.onUnbind(intent);
    }

    private void saveToFile(String text) {
        // Save to app-specific external storage which is readable by ADB
        // /sdcard/Android/data/com.example.clipboard/files/clipboard.txt
        File dir = getExternalFilesDir(null);
        if (dir != null) {
            File file = new File(dir, "clipboard.txt");
            try (FileOutputStream fos = new FileOutputStream(file)) {
                fos.write(text.getBytes());
                Log.d(TAG, "Saved to " + file.getAbsolutePath());
            } catch (IOException e) {
                Log.e(TAG, "Failed to save file", e);
            }
        }
    }
}
