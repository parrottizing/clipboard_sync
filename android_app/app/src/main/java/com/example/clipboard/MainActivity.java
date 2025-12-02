package com.example.clipboard;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.util.Log;
import android.webkit.MimeTypeMap;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {

    private static final String TAG = "ClipboardReadActivity";
    private static final String TEXT_FILENAME = "clipboard_content.txt";
    private static final String IMAGE_FILENAME = "clipboard_image.txt";
    private static final int MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB limit
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
            ClipData.Item item = clip.getItemAt(0);
            
            // Check for URI (image/file content)
            Uri uri = item.getUri();
            if (uri != null) {
                Log.i(TAG, "Clipboard contains URI: " + uri);
                handleImageUri(uri);
                return;
            }
            
            // Check for text
            CharSequence text = item.getText();
            if (text != null) {
                String clipboardText = text.toString();
                Log.i(TAG, "Clipboard text found: " + clipboardText);
                writeTextToFile(clipboardText);
                return;
            }
            
            Log.i(TAG, "Clipboard item has no text or URI");
        }
    }

    private void handleImageUri(Uri uri) {
        try {
            ContentResolver resolver = getContentResolver();
            String mimeType = resolver.getType(uri);
            
            // Check if it's an image
            if (mimeType == null || !mimeType.startsWith("image/")) {
                Log.w(TAG, "URI is not an image, MIME type: " + mimeType);
                return;
            }
            
            // Get filename if available
            String filename = getFileName(uri);
            
            // Read image data
            InputStream inputStream = resolver.openInputStream(uri);
            if (inputStream == null) {
                Log.e(TAG, "Failed to open input stream for URI");
                return;
            }
            
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            byte[] data = new byte[16384];
            int nRead;
            int totalSize = 0;
            
            while ((nRead = inputStream.read(data, 0, data.length)) != -1) {
                totalSize += nRead;
                if (totalSize > MAX_IMAGE_SIZE) {
                    Log.w(TAG, "Image too large (>" + MAX_IMAGE_SIZE + " bytes), skipping");
                    inputStream.close();
                    return;
                }
                buffer.write(data, 0, nRead);
            }
            
            inputStream.close();
            buffer.flush();
            
            byte[] imageBytes = buffer.toByteArray();
            String base64Image = Base64.encodeToString(imageBytes, Base64.NO_WRAP);
            
            // Write metadata and Base64 data to file
            String imageData = mimeType + "\n" + (filename != null ? filename : "image") + "\n" + base64Image;
            writeImageToFile(imageData);
            
            Log.i(TAG, "Successfully processed image: " + mimeType + ", size: " + imageBytes.length + " bytes");
            
        } catch (IOException e) {
            Log.e(TAG, "Error reading image from URI", e);
        } catch (SecurityException e) {
            Log.e(TAG, "Permission denied reading URI", e);
        }
    }
    
    private String getFileName(Uri uri) {
        String result = null;
        if (uri.getScheme().equals("content")) {
            try (Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
                if (cursor != null && cursor.moveToFirst()) {
                    int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                    if (index >= 0) {
                        result = cursor.getString(index);
                    }
                }
            } catch (Exception e) {
                Log.w(TAG, "Error getting filename", e);
            }
        }
        if (result == null) {
            result = uri.getPath();
            int cut = result.lastIndexOf('/');
            if (cut != -1) {
                result = result.substring(cut + 1);
            }
        }
        return result;
    }

    private void writeTextToFile(String data) {
        File file = new File(getExternalFilesDir(null), TEXT_FILENAME);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write(data.getBytes(StandardCharsets.UTF_8));
            Log.i(TAG, "Successfully wrote text to file: " + file.getAbsolutePath());
        } catch (IOException e) {
            Log.e(TAG, "Error writing text to file", e);
        }
    }
    
    private void writeImageToFile(String data) {
        File file = new File(getExternalFilesDir(null), IMAGE_FILENAME);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write(data.getBytes(StandardCharsets.UTF_8));
            Log.i(TAG, "Successfully wrote image to file: " + file.getAbsolutePath());
        } catch (IOException e) {
            Log.e(TAG, "Error writing image to file", e);
        }
    }
}
