package com.example.clipboard;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Base64;
import android.util.Log;
import androidx.core.content.FileProvider;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;

public class WriteReceiver extends BroadcastReceiver {
    private static final String TAG = "ClipboardWriteReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent != null && "com.example.clipboard.WRITE".equals(intent.getAction())) {
            
            // Check for image file path (new method)
            String imageFilePath = intent.getStringExtra("image_file");
            if (imageFilePath != null) {
                Log.d(TAG, "Received image file path: " + imageFilePath);
                handleImageFromFile(context, imageFilePath);
                return;
            }
            
            // Check for image data (old method, kept for compatibility)
            String imageData = intent.getStringExtra("image_data");
            String mimeType = intent.getStringExtra("mime_type");
            
            if (imageData != null && mimeType != null) {
                Log.d(TAG, "Received image data directly, MIME type: " + mimeType);
                handleImageWrite(context, imageData, mimeType);
                return;
            }
            
            // Check for text data
            String text = intent.getStringExtra("text");
            if (text != null) {
                Log.d(TAG, "Received text to write: " + text);
                handleTextWrite(context, text);
                return;
            }
            
            Log.w(TAG, "No text, image data, or image file in intent");
        }
    }
    
    private void handleImageFromFile(Context context, String filePath) {
        BufferedReader reader = null;
        try {
            File imageFile = new File(filePath);
            if (!imageFile.exists()) {
                Log.e(TAG, "Image file does not exist: " + filePath);
                return;
            }
            
            reader = new BufferedReader(new FileReader(imageFile));
            
            // Read MIME type (line 1)
            String mimeType = reader.readLine();
            if (mimeType == null) {
                Log.e(TAG, "Could not read MIME type from file");
                return;
            }
            
            // Skip filename (line 2)
            reader.readLine();
            
            // Read Base64 data (rest of file)
            StringBuilder base64Data = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                base64Data.append(line);
            }
            
            Log.i(TAG, "Read image from file: " + mimeType + ", data length: " + base64Data.length());
            
            // Process the image
            handleImageWrite(context, base64Data.toString(), mimeType);
            
            // Clean up the file
            if (imageFile.delete()) {
                Log.d(TAG, "Deleted temp image file");
            }
            
        } catch (IOException e) {
            Log.e(TAG, "Error reading image file", e);
        } finally {
            if (reader != null) {
                try {
                    reader.close();
                } catch (IOException e) {
                    // Ignore
                }
            }
        }
    }
    
    private void handleTextWrite(Context context, String text) {
        try {
            ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) {
                ClipData clip = ClipData.newPlainText("ADB", text);
                clipboard.setPrimaryClip(clip);
                Log.i(TAG, "Text written to clipboard");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error writing text to clipboard", e);
        }
    }
    
    private void handleImageWrite(Context context, String base64Data, String mimeType) {
        try {
            // Decode Base64 to byte array
            byte[] imageBytes = Base64.decode(base64Data, Base64.NO_WRAP);
            
            Log.i(TAG, "Decoded image: " + imageBytes.length + " bytes");
            
            // Determine file extension from MIME type
            String extension = getExtensionFromMimeType(mimeType);
            
            // Create temporary file in cache directory
            File cacheDir = new File(context.getCacheDir(), "clipboard_images");
            if (!cacheDir.exists()) {
                cacheDir.mkdirs();
            }
            
            // Clean old files (keep cache small)
            cleanOldFiles(cacheDir);
            
            File imageFile = new File(cacheDir, "clipboard_image_" + System.currentTimeMillis() + extension);
            
            // Write decoded data to file
            try (FileOutputStream fos = new FileOutputStream(imageFile)) {
                fos.write(imageBytes);
                fos.flush();
            }
            
            Log.i(TAG, "Image written to temp file: " + imageFile.getAbsolutePath());
            
            // Create content URI using FileProvider
            Uri contentUri = FileProvider.getUriForFile(
                context,
                "com.example.clipboard.fileprovider",
                imageFile
            );
            
            Log.i(TAG, "Created content URI: " + contentUri);
            
            // Write URI to clipboard
            ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) {
                ClipData clip = ClipData.newUri(context.getContentResolver(), "ADB Image", contentUri);
                clipboard.setPrimaryClip(clip);
                Log.i(TAG, "Image URI written to clipboard");
            }
            
        } catch (IllegalArgumentException e) {
            Log.e(TAG, "Invalid Base64 data", e);
        } catch (IOException e) {
            Log.e(TAG, "Error writing image file", e);
        } catch (Exception e) {
            Log.e(TAG, "Error writing image to clipboard", e);
        }
    }
    
    private String getExtensionFromMimeType(String mimeType) {
        switch (mimeType) {
            case "image/jpeg":
            case "image/jpg":
                return ".jpg";
            case "image/png":
                return ".png";
            case "image/gif":
                return ".gif";
            case "image/webp":
                return ".webp";
            default:
                return ".png";
        }
    }
    
    private void cleanOldFiles(File directory) {
        File[] files = directory.listFiles();
        if (files != null && files.length > 5) {
            // Keep only the 5 most recent files
            java.util.Arrays.sort(files, (f1, f2) -> Long.compare(f2.lastModified(), f1.lastModified()));
            for (int i = 5; i < files.length; i++) {
                files[i].delete();
            }
        }
    }
}
