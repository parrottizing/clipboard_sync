package com.example.clipboard;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class WriteReceiver extends BroadcastReceiver {
    private static final String TAG = "ClipboardWriteReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent != null && "com.example.clipboard.WRITE".equals(intent.getAction())) {
            String text = intent.getStringExtra("text");
            if (text != null) {
                Log.d(TAG, "Received text to write: " + text);
                ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                ClipData clip = ClipData.newPlainText("ADB", text);
                clipboard.setPrimaryClip(clip);
            }
        }
    }
}
