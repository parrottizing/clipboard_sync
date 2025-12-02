package com.example.clipboard;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {

    private static final String TAG = "ClipboardReadActivity";
    private static final String FILENAME = "clipboard_content.txt";
    private boolean hasProcessed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // No setContentView needed for a transparent activity
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus && !hasProcessed) {
            hasProcessed = true;
            readClipboardAndWriteToFile();
            finish();
        }
    }

    private void readClipboardAndWriteToFile() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard == null) {
            Log.e(TAG, "ClipboardManager is null");
            return;
        }

        if (!clipboard.hasPrimaryClip()) {
            Log.i(TAG, "No primary clip");
            return;
        }

        ClipData clip = clipboard.getPrimaryClip();
        if (clip != null && clip.getItemCount() > 0) {
            CharSequence text = clip.getItemAt(0).getText();
            if (text != null) {
                String clipboardText = text.toString();
                Log.i(TAG, "Clipboard text found: " + clipboardText);
                writeToFile(clipboardText);
            } else {
                Log.i(TAG, "Clipboard item text is null");
            }
        }
    }

    private void writeToFile(String data) {
        File file = new File(getExternalFilesDir(null), FILENAME);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write(data.getBytes(StandardCharsets.UTF_8));
            Log.i(TAG, "Successfully wrote to file: " + file.getAbsolutePath());
        } catch (IOException e) {
            Log.e(TAG, "Error writing to file", e);
        }
    }
}
