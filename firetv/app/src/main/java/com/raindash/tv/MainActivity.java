package com.raindash.tv;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Full-screen WebView showing the RainDash dashboard served by the Rain World mod.
 *
 * The mod launches this activity over ADB with the dashboard URL:
 *   am start -n com.raindash.tv/.MainActivity --es url http://PC:8787/
 * Started from the launcher instead, it reuses the last URL or finds the PC by LAN broadcast.
 * Menu button: open the setup screen.
 */
public class MainActivity extends Activity {
    private static final String PREFS = "raindash";
    private static final String KEY_URL = "url";
    private static final String SETUP = "file:///android_asset/setup.html";
    private static final String OFFLINE = "file:///android_asset/offline.html";

    private WebView web;
    private String dashboardUrl;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean waiting;          // showing the offline page and polling for the PC
    private int retryGeneration;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        web.setFocusable(true);
        web.setFocusableInTouchMode(true);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        web.addJavascriptInterface(new Bridge(), "RainDashApp");
        web.setWebViewClient(new Client());
        setContentView(web);
        hideSystemUi();

        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemUi();
        web.onResume();
    }

    @Override
    protected void onPause() {
        web.onPause();
        super.onPause();
    }

    private void hideSystemUi() {
        web.setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    private SharedPreferences prefs() {
        return getSharedPreferences(PREFS, MODE_PRIVATE);
    }

    private void handleIntent(Intent intent) {
        String url = intent != null ? intent.getStringExtra("url") : null;
        if (url == null && intent != null && intent.getData() != null) url = intent.getData().toString();
        if (url != null) {
            url = normalize(url);
            prefs().edit().putString(KEY_URL, url).apply();
            open(url);
            return;
        }
        String saved = prefs().getString(KEY_URL, null);
        if (saved != null) open(saved);
        else showSetup();
    }

    private void open(String url) {
        dashboardUrl = url;
        waiting = false;
        retryGeneration++;
        web.loadUrl(url);
        web.requestFocus();
    }

    private void showSetup() {
        waiting = false;
        retryGeneration++;
        web.loadUrl(SETUP);
        web.requestFocus();
    }

    /** The PC isn't answering: show a waiting screen, poll it, and look for it on the LAN in case its IP changed. */
    private void showOffline() {
        if (waiting) return;
        waiting = true;
        int generation = ++retryGeneration;
        web.loadUrl(OFFLINE + "?url=" + Uri.encode(dashboardUrl == null ? "" : dashboardUrl));
        schedulePoll(generation, 3000);
    }

    private void schedulePoll(final int generation, long delayMs) {
        handler.postDelayed(() -> {
            if (generation != retryGeneration || isFinishing()) return;
            final String target = dashboardUrl;
            new Thread(() -> {
                final String found = reachable(target) ? target : Discovery.find(MainActivity.this, 1500);
                handler.post(() -> {
                    if (generation != retryGeneration) return;
                    if (found != null) {
                        prefs().edit().putString(KEY_URL, found).apply();
                        open(found);
                    } else {
                        schedulePoll(generation, 4000);
                    }
                });
            }).start();
        }, delayMs);
    }

    private static boolean reachable(String base) {
        if (base == null) return false;
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(base + "api/state").openConnection();
            c.setConnectTimeout(1500);
            c.setReadTimeout(1500);
            return c.getResponseCode() == 200;
        } catch (Exception e) {
            return false;
        } finally {
            if (c != null) c.disconnect();
        }
    }

    static String normalize(String url) {
        url = url.trim();
        if (!url.startsWith("http://") && !url.startsWith("https://")) url = "http://" + url;
        Uri u = Uri.parse(url);
        if (u.getPort() == -1) url = u.getScheme() + "://" + u.getHost() + ":8787" + (u.getPath() == null ? "" : u.getPath());
        if (!url.endsWith("/")) url += "/";
        return url;
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        if (event.getAction() == KeyEvent.ACTION_DOWN) {
            switch (event.getKeyCode()) {
                case KeyEvent.KEYCODE_MENU:
                    showSetup();
                    return true;
                case KeyEvent.KEYCODE_MEDIA_REWIND:
                case KeyEvent.KEYCODE_MEDIA_FAST_FORWARD:
                    // Let the page switch tabs with these.
                    web.evaluateJavascript("document.dispatchEvent(new KeyboardEvent('keydown',{key:'"
                            + (event.getKeyCode() == KeyEvent.KEYCODE_MEDIA_REWIND ? "MediaRewind" : "MediaFastForward")
                            + "'}))", null);
                    return true;
                default:
                    break;
            }
        }
        return super.dispatchKeyEvent(event);
    }

    @Override
    public void onBackPressed() {
        String current = web.getUrl();
        if (current == null || current.startsWith("file:")) {
            if (current != null && current.startsWith(SETUP) && prefs().getString(KEY_URL, null) != null && !waiting) {
                open(prefs().getString(KEY_URL, null));
                return;
            }
            super.onBackPressed();
            return;
        }
        web.evaluateJavascript("(window.rdBack && window.rdBack()) ? 'yes' : 'no'", value -> {
            if (value == null || !value.contains("yes")) finish();
        });
    }

    private class Client extends WebViewClient {
        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            if (Build.VERSION.SDK_INT >= 21 && request.isForMainFrame() && !request.getUrl().toString().startsWith("file:")) {
                showOffline();
            }
        }

        @SuppressWarnings("deprecation")
        @Override
        public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
            if (Build.VERSION.SDK_INT < 23 && failingUrl != null && !failingUrl.startsWith("file:")) showOffline();
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            return false;
        }
    }

    /** Exposed to setup.html / offline.html as window.RainDashApp. */
    private class Bridge {
        @JavascriptInterface
        public void setUrl(final String url) {
            handler.post(() -> {
                String u = normalize(url);
                prefs().edit().putString(KEY_URL, u).apply();
                open(u);
            });
        }

        @JavascriptInterface
        public String getUrl() {
            return prefs().getString(KEY_URL, "");
        }

        @JavascriptInterface
        public void discover() {
            new Thread(() -> {
                final String found = Discovery.find(MainActivity.this, 2000);
                handler.post(() -> web.evaluateJavascript(
                        "window.onDiscovered && window.onDiscovered(" + (found == null ? "null" : "'" + found.replace("'", "") + "'") + ")",
                        null));
            }).start();
        }

        @JavascriptInterface
        public void openSetup() {
            handler.post(MainActivity.this::showSetup);
        }
    }
}
