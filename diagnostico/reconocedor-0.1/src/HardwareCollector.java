package com.tvbase.reconocimiento;

import android.app.ActivityManager;
import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.FeatureInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.graphics.Point;
import android.hardware.display.DisplayManager;
import android.media.MediaCodecInfo;
import android.media.MediaCodecList;
import android.os.Build;
import android.os.Bundle;
import android.os.StatFs;
import android.os.SystemClock;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import android.util.DisplayMetrics;
import android.util.Range;
import android.view.Display;
import android.view.InputDevice;
import android.view.KeyEvent;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** Normal-APK observations; it never changes a device setting or invokes ADB/root. */
public final class HardwareCollector {
    public interface Progress { void update(String message); }
    private static final Charset UTF8 = Charset.forName("UTF-8");
    private static final int SMALL_READ = 32768;
    private static final long HARDWARE_BYTES = 12L * 1024 * 1024;
    private static final int HARDWARE_ENTRIES = 3000;
    private HardwareCollector() {}

    public static JSONObject collect(final Context context, File session, Progress cb) throws Exception {
        validateSession(context, session);
        final long began = SystemClock.elapsedRealtime();
        JSONObject result = new JSONObject();
        result.put("schema_version", 1).put("collector", "HardwareCollector/0.1")
            .put("privilege", "normal_apk").put("network_requests", false)
            .put("root_or_adb", false);
        JSONObject sections = new JSONObject();
        result.put("sections", sections);
        progress(cb, "Leyendo la plataforma y memoria disponibles");
        sections.put("build", observed("android.os.Build", build()));
        sections.put("memory_storage", timed("Android memory/storage APIs", 12000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return memoryStorage(context); }
        }));
        sections.put("displays", timed("DisplayManager", 12000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return displays(context); }
        }));
        progress(cb, "Consultando codecs y controles declarados por Android");
        sections.put("codecs", timed("MediaCodecList.ALL_CODECS", 20000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return codecs(); }
        }));
        sections.put("input_devices", timed("InputDevice", 12000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return inputs(); }
        }));
        progress(cb, "Inventariando paquetes y funciones del sistema");
        sections.put("packages_features", timed("PackageManager", 20000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return packages(context); }
        }));
        progress(cb, "Leyendo propiedades, buses y particiones accesibles");
        JSONArray commands = new JSONArray();
        commands.put(command("getprop", new String[]{"/system/bin/getprop"}, true));
        commands.put(command("uname", new String[]{"/system/bin/uname", "-s", "-r", "-m", "-v"}, false));
        commands.put(command("id", new String[]{"/system/bin/id"}, false));
        sections.put("commands", commands);
        HardwareFiles files = new HardwareFiles(session);
        files.collect();
        JSONObject fileSummary = files.finish();
        sections.put("hardware_files", fileSummary);
        progress(cb, "Guardando bibliotecas, firmware y configuración de hardware legibles");
        sections.put("driver_files", FileCollector.collect(session, cb));
        result.put("elapsed_ms", SystemClock.elapsedRealtime() - began);
        result.put("state", "finished_with_observations");
        result.put("completeness", "Only accessible observations; inspect every section and omission. This is not a complete hardware or firmware backup.");
        result.put("limits", new JSONArray(Arrays.asList(
            "Build properties and DT describe software configuration, not an independently identified physical chip.",
            "Codecs advertise capabilities; none were instantiated or benchmarked. Hardware decoding, VP9 alpha and simultaneous video remain untested.",
            "Bound sysfs driver names are stronger evidence of the active software binding, not proof that every function works.",
            "Package visibility and protected proc/sysfs files may be restricted by Android; denial is recorded.",
            "API timeout only bounds this client. A system service may continue work; no such worker writes report files.",
            "No private app data, WiFi credentials, key material, network connections or privileged partition reads are collected."
        )));
        return result;
    }

    private static void validateSession(Context context, File session) throws Exception {
        String root = new File(context.getApplicationInfo().dataDir).getCanonicalPath();
        String path = session.getCanonicalPath();
        if (!path.startsWith(root + File.separator) || !session.isDirectory())
            throw new IOException("The session must be an existing private app directory");
        File cursor = session.getAbsoluteFile();
        while (cursor != null && !cursor.getCanonicalPath().equals(root)) {
            StructStat st = Os.lstat(cursor.getPath());
            if (!OsConstants.S_ISDIR(st.st_mode) || OsConstants.S_ISLNK(st.st_mode))
                throw new IOException("Session path contains a non-directory or link");
            cursor = cursor.getParentFile();
        }
    }
    private static void progress(Progress cb, String text) { if (cb != null) cb.update(text); }
    private static JSONObject observed(String source, Object value) throws Exception {
        return new JSONObject().put("state", "observed").put("source", source).put("value", value);
    }
    private static JSONObject failure(String source, String state, Throwable error) throws Exception {
        return new JSONObject().put("state", state).put("source", source)
            .put("error_type", error.getClass().getSimpleName()).put("error", clean(error.getMessage(), 1024));
    }
    private static String clean(String text, int limit) {
        if (text == null) return "";
        return text.length() <= limit ? text : text.substring(0, limit) + " [truncated]";
    }
    /** Timed tasks return data only. They never receive the session or write files. */
    private static JSONObject timed(String source, long ms, Callable<JSONObject> action) throws Exception {
        long started = SystemClock.elapsedRealtime();
        FutureTask<JSONObject> task = new FutureTask<JSONObject>(action);
        Thread thread = new Thread(task, "tvbase-observation");
        thread.setDaemon(true); thread.start();
        JSONObject answer;
        try { answer = observed(source, task.get(ms, TimeUnit.MILLISECONDS)); }
        catch (TimeoutException e) {
            task.cancel(true);
            answer = failure(source, "timeout", e).put("operation_may_continue", true);
        } catch (Exception e) {
            Throwable cause = e.getCause() == null ? e : e.getCause();
            answer = failure(source, cause instanceof SecurityException ? "denied" : "error", cause);
        }
        return answer.put("elapsed_ms", SystemClock.elapsedRealtime() - started).put("client_limit_ms", ms);
    }
    private static JSONObject build() throws Exception {
        JSONObject j = new JSONObject();
        j.put("brand", Build.BRAND).put("manufacturer", Build.MANUFACTURER).put("model", Build.MODEL)
            .put("device", Build.DEVICE).put("product", Build.PRODUCT).put("board", Build.BOARD)
            .put("hardware", Build.HARDWARE).put("bootloader", Build.BOOTLOADER)
            .put("build_id", Build.ID).put("display", Build.DISPLAY).put("fingerprint", Build.FINGERPRINT)
            .put("tags", Build.TAGS).put("type", Build.TYPE).put("sdk", Build.VERSION.SDK_INT)
            .put("release", Build.VERSION.RELEASE).put("incremental", Build.VERSION.INCREMENTAL)
            .put("codename", Build.VERSION.CODENAME).put("abis", strings(Build.SUPPORTED_ABIS));
        if (Build.VERSION.SDK_INT >= 23) j.put("security_patch", Build.VERSION.SECURITY_PATCH);
        j.put("serial", new JSONObject().put("state", "excluded").put("reason", "personal device identifier"));
        return j;
    }
    private static JSONObject memoryStorage(Context context) throws Exception {
        JSONObject j = new JSONObject();
        ActivityManager.MemoryInfo mem = new ActivityManager.MemoryInfo();
        ((ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE)).getMemoryInfo(mem);
        j.put("memory", new JSONObject().put("source", "ActivityManager.MemoryInfo")
            .put("total_visible_bytes", mem.totalMem).put("available_bytes", mem.availMem)
            .put("low_memory", mem.lowMemory).put("threshold_bytes", mem.threshold)
            .put("app_max_heap_bytes", Runtime.getRuntime().maxMemory())
            .put("available_processors", Runtime.getRuntime().availableProcessors()));
        JSONArray storage = new JSONArray();
        for (String path : new String[]{"/data", "/system", "/vendor", "/product", "/odm", "/system_ext"}) {
            try {
                StatFs stat = new StatFs(path);
                storage.put(new JSONObject().put("source", path).put("state", "observed")
                    .put("total_bytes", stat.getTotalBytes()).put("available_bytes", stat.getAvailableBytes())
                    .put("free_bytes", stat.getFreeBytes()).put("block_size", stat.getBlockSizeLong()));
            } catch (Exception e) { storage.put(failure(path, "unavailable", e)); }
        }
        return j.put("storage", storage).put("storage_note", "Mount capacity is not raw eMMC capacity; no external storage directory is created.");
    }
    private static JSONObject displays(Context context) throws Exception {
        JSONArray all = new JSONArray();
        for (Display d : ((DisplayManager) context.getSystemService(Context.DISPLAY_SERVICE)).getDisplays()) {
            JSONObject j = new JSONObject().put("id", d.getDisplayId()).put("name", d.getName())
                .put("state", d.getState()).put("flags", d.getFlags()).put("refresh_hz", d.getRefreshRate());
            Point size = new Point(); d.getRealSize(size);
            DisplayMetrics m = new DisplayMetrics(); d.getRealMetrics(m);
            j.put("real_width", size.x).put("real_height", size.y).put("density_dpi", m.densityDpi)
                .put("xdpi", m.xdpi).put("ydpi", m.ydpi);
            JSONArray modes = new JSONArray();
            if (Build.VERSION.SDK_INT >= 23) {
                for (Display.Mode mode : d.getSupportedModes()) modes.put(new JSONObject()
                    .put("mode_id", mode.getModeId()).put("width", mode.getPhysicalWidth())
                    .put("height", mode.getPhysicalHeight()).put("refresh_hz", mode.getRefreshRate()));
                j.put("active_mode_id", d.getMode().getModeId());
            }
            j.put("supported_modes", modes); all.put(j);
        }
        return new JSONObject().put("items", all).put("note", "Advertised display modes; no output mode was changed.");
    }
    private static JSONObject codecs() throws Exception {
        MediaCodecInfo[] all = new MediaCodecList(MediaCodecList.ALL_CODECS).getCodecInfos();
        JSONArray items = new JSONArray();
        for (int n = 0; n < all.length && n < 256; n++) {
            if (Thread.currentThread().isInterrupted()) break;
            MediaCodecInfo info = all[n];
            JSONObject j = new JSONObject().put("name", info.getName()).put("encoder", info.isEncoder());
            if (Build.VERSION.SDK_INT >= 29) {
                for (String method : new String[]{"isHardwareAccelerated", "isSoftwareOnly", "isVendor", "isAlias", "getCanonicalName"}) {
                    try { j.put(method, info.getClass().getMethod(method).invoke(info)); }
                    catch (Exception e) { j.put(method, failure("MediaCodecInfo." + method, "unavailable", e)); }
                }
            } else j.put("hardware_acceleration", new JSONObject().put("state", "unavailable")
                .put("reason", "Android exposes hardware/software classification from API 29; names are not substituted as proof."));
            JSONArray types = new JSONArray();
            String[] supported = info.getSupportedTypes();
            for (int t = 0; t < supported.length && t < 32; t++) {
                String type = supported[t];
                JSONObject cap = new JSONObject().put("mime", type);
                try {
                    MediaCodecInfo.CodecCapabilities c = info.getCapabilitiesForType(type);
                    cap.put("state", "observed").put("color_formats", ints(c.colorFormats));
                    JSONArray levels = new JSONArray();
                    for (MediaCodecInfo.CodecProfileLevel pl : c.profileLevels)
                        levels.put(new JSONObject().put("profile", pl.profile).put("level", pl.level));
                    cap.put("profile_levels", levels);
                    if (Build.VERSION.SDK_INT >= 23) cap.put("max_supported_instances", c.getMaxSupportedInstances());
                    JSONArray features = new JSONArray();
                    for (String name : new String[]{"adaptive-playback", "secure-playback", "tunneled-playback", "partial-frame", "intra-refresh", "multiple-frames", "dynamic-timestamp", "low-latency"})
                        features.put(new JSONObject().put("name", name).put("supported", c.isFeatureSupported(name)).put("required", c.isFeatureRequired(name)));
                    cap.put("features", features);
                    MediaCodecInfo.VideoCapabilities v = c.getVideoCapabilities();
                    if (v != null) cap.put("video", new JSONObject().put("widths", range(v.getSupportedWidths()))
                        .put("heights", range(v.getSupportedHeights())).put("frame_rates", range(v.getSupportedFrameRates()))
                        .put("bitrates", range(v.getBitrateRange())).put("width_alignment", v.getWidthAlignment())
                        .put("height_alignment", v.getHeightAlignment()));
                    MediaCodecInfo.AudioCapabilities a = c.getAudioCapabilities();
                    if (a != null) {
                        JSONArray rates = new JSONArray();
                        for (Range<Integer> r : a.getSupportedSampleRateRanges()) rates.put(range(r));
                        cap.put("audio", new JSONObject().put("max_input_channels", a.getMaxInputChannelCount())
                            .put("sample_rate_ranges", rates).put("sample_rates", ints(a.getSupportedSampleRates()))
                            .put("bitrates", range(a.getBitrateRange())));
                    }
                    MediaCodecInfo.EncoderCapabilities en = c.getEncoderCapabilities();
                    if (en != null) cap.put("encoder", new JSONObject().put("complexity", range(en.getComplexityRange()))
                        .put("cq", en.isBitrateModeSupported(MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CQ))
                        .put("vbr", en.isBitrateModeSupported(MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR))
                        .put("cbr", en.isBitrateModeSupported(MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR)));
                } catch (Exception e) { cap.put("state", "error").put("error", clean(e.toString(), 1024)); }
                types.put(cap);
            }
            j.put("types", types).put("omitted_types", Math.max(0, supported.length - 32)); items.put(j);
        }
        return new JSONObject().put("items", items).put("reported_codec_count", all.length)
            .put("omitted_codecs", all.length - items.length()).put("runtime_decode_test", "not_performed");
    }
    private static JSONObject inputs() throws Exception {
        int[] ids = InputDevice.getDeviceIds(); JSONArray items = new JSONArray();
        int[] keys = {KeyEvent.KEYCODE_HOME, KeyEvent.KEYCODE_BACK, KeyEvent.KEYCODE_MENU,
            KeyEvent.KEYCODE_DPAD_CENTER, KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_DOWN,
            KeyEvent.KEYCODE_DPAD_LEFT, KeyEvent.KEYCODE_DPAD_RIGHT, KeyEvent.KEYCODE_ENTER,
            KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE, KeyEvent.KEYCODE_VOLUME_UP, KeyEvent.KEYCODE_VOLUME_DOWN,
            KeyEvent.KEYCODE_POWER};
        for (int i = 0; i < ids.length && i < 256; i++) {
            InputDevice d = InputDevice.getDevice(ids[i]);
            if (d == null) { items.put(new JSONObject().put("id", ids[i]).put("state", "disappeared")); continue; }
            JSONObject j = new JSONObject().put("id", d.getId()).put("name", d.getName())
                .put("vendor_id", d.getVendorId()).put("product_id", d.getProductId())
                .put("sources", d.getSources()).put("virtual", d.isVirtual()).put("keyboard_type", d.getKeyboardType());
            JSONArray motion = new JSONArray();
            for (InputDevice.MotionRange r : d.getMotionRanges()) motion.put(new JSONObject()
                .put("axis", r.getAxis()).put("source", r.getSource()).put("min", r.getMin())
                .put("max", r.getMax()).put("flat", r.getFlat()).put("fuzz", r.getFuzz()).put("resolution", r.getResolution()));
            j.put("motion_ranges", motion);
            JSONArray coverage = new JSONArray(); boolean[] present = d.hasKeys(keys);
            for (int k = 0; k < keys.length; k++) coverage.put(new JSONObject().put("keycode", keys[k])
                .put("name", KeyEvent.keyCodeToString(keys[k])).put("declared", present[k]));
            j.put("key_capabilities", coverage); items.put(j);
        }
        return new JSONObject().put("items", items).put("omitted_devices", Math.max(0, ids.length - 256))
            .put("note", "Declared input capabilities; no key events were recorded and HOME delivery is not tested.");
    }
    @SuppressWarnings("deprecation")
    private static JSONObject packages(Context context) throws Exception {
        PackageManager pm = context.getPackageManager();
        JSONArray features = new JSONArray();
        FeatureInfo[] fs = pm.getSystemAvailableFeatures();
        if (fs != null) for (FeatureInfo f : fs) {
            JSONObject j = new JSONObject().put("name", f.name == null ? JSONObject.NULL : f.name)
                .put("flags", f.flags).put("req_gl_es_version", f.reqGlEsVersion);
            if (Build.VERSION.SDK_INT >= 24) j.put("version", f.version);
            features.put(j);
        }
        int flags = PackageManager.GET_SIGNATURES | PackageManager.GET_PERMISSIONS | PackageManager.GET_META_DATA;
        if (Build.VERSION.SDK_INT >= 28) flags |= PackageManager.GET_SIGNING_CERTIFICATES;
        List<PackageInfo> list = pm.getInstalledPackages(flags);
        JSONArray items = new JSONArray();
        for (int i = 0; i < list.size() && i < 2048; i++) {
            if (Thread.currentThread().isInterrupted()) break;
            PackageInfo p = list.get(i);
            JSONObject j = new JSONObject().put("package_name", p.packageName);
            try {
                j.put("version_name", p.versionName).put("version_code", Build.VERSION.SDK_INT >= 28 ? p.getLongVersionCode() : p.versionCode);
                ApplicationInfo a = p.applicationInfo;
                if (a != null) {
                    j.put("source_dir", a.sourceDir).put("split_source_dirs", strings(a.splitSourceDirs))
                        .put("flags", a.flags).put("enabled", a.enabled).put("target_sdk", a.targetSdkVersion)
                        .put("native_library_dir", a.nativeLibraryDir).put("system_app", (a.flags & ApplicationInfo.FLAG_SYSTEM) != 0);
                    if (Build.VERSION.SDK_INT >= 24) j.put("min_sdk", a.minSdkVersion);
                    JSONArray metadata = new JSONArray();
                    Bundle b = a.metaData;
                    if (b != null) for (String key : b.keySet()) metadata.put(new JSONObject().put("key", key)
                        .put("state", "value_excluded").put("reason", "Metadata values can contain credentials; only names are inventoried."));
                    j.put("metadata", metadata);
                }
                j.put("requested_permissions", strings(p.requestedPermissions)).put("requested_permission_flags", ints(p.requestedPermissionsFlags));
                JSONArray certs = new JSONArray(); Signature[] signatures = p.signatures;
                if (Build.VERSION.SDK_INT >= 28 && p.signingInfo != null)
                    signatures = p.signingInfo.hasMultipleSigners() ? p.signingInfo.getApkContentsSigners() : p.signingInfo.getSigningCertificateHistory();
                if (signatures != null) for (Signature signature : signatures)
                    certs.put(new JSONObject().put("sha256", hex(MessageDigest.getInstance("SHA-256").digest(signature.toByteArray()))));
                j.put("signing_certificate_hashes", certs).put("state", "observed");
            } catch (Exception e) { j.put("state", "error").put("error", clean(e.toString(), 1024)); }
            items.put(j);
        }
        return new JSONObject().put("features", features).put("packages", items).put("visible_count", list.size())
            .put("omitted_visible_packages", list.size() - items.length())
            .put("visibility_limit", "Normal PackageManager visibility; absence is not proof of absence. No private application data was opened.");
    }
    private static JSONArray strings(String[] values) { return values == null ? new JSONArray() : new JSONArray(Arrays.asList(values)); }
    private static JSONArray ints(int[] values) { JSONArray j = new JSONArray(); if (values != null) for (int value : values) j.put(value); return j; }
    private static JSONObject range(Range<?> value) throws Exception { return new JSONObject().put("lower", value.getLower()).put("upper", value.getUpper()); }
    private static String hex(byte[] bytes) { StringBuilder b = new StringBuilder(); for (byte v : bytes) b.append(String.format(java.util.Locale.US, "%02x", v & 255)); return b.toString(); }

    private static final class Drain implements Runnable {
        final InputStream input; final ByteArrayOutputStream out = new ByteArrayOutputStream();
        boolean truncated, complete; String error = "";
        Drain(InputStream input) { this.input = input; }
        public void run() {
            byte[] bytes = new byte[8192];
            try {
                int n; while ((n = input.read(bytes)) != -1) {
                    synchronized (this) {
                        int amount = Math.min(n, 1024 * 1024 - out.size());
                        if (amount > 0) out.write(bytes, 0, amount);
                        if (amount < n) { truncated = true; break; }
                    }
                }
            } catch (Exception e) { synchronized (this) { error = e.getClass().getSimpleName(); } }
            finally { try { input.close(); } catch (Exception ignored) {} synchronized (this) { complete = true; } }
        }
        synchronized JSONObject snapshot(boolean properties) throws Exception {
            String value = new String(out.toByteArray(), UTF8);
            JSONObject j = new JSONObject().put("truncated", truncated).put("reader_complete", complete).put("read_error", error);
            if (properties) return j.put("properties", sanitizeProperties(value));
            return j.put("text", value);
        }
    }
    private static JSONObject command(String name, String[] argv, boolean properties) throws Exception {
        long start = SystemClock.elapsedRealtime(); Process process = null;
        JSONObject j = new JSONObject().put("source", "ProcessBuilder fixed allowlist").put("argv", strings(argv));
        try {
            if (!(name.equals("getprop") || name.equals("uname") || name.equals("id"))) throw new IOException("Command not allowed");
            process = new ProcessBuilder(argv).start(); process.getOutputStream().close();
            Drain stdout = new Drain(process.getInputStream()), stderr = new Drain(process.getErrorStream());
            Thread a = new Thread(stdout, "tvbase-command-out"), b = new Thread(stderr, "tvbase-command-error");
            a.setDaemon(true); b.setDaemon(true); a.start(); b.start();
            Integer code = null;
            while (SystemClock.elapsedRealtime() - start < 6000) {
                try { code = process.exitValue(); break; } catch (IllegalThreadStateException alive) { SystemClock.sleep(25); }
            }
            boolean timeout = code == null;
            if (timeout) process.destroy();
            a.join(500); b.join(500);
            if (a.isAlive()) try { process.getInputStream().close(); } catch (Exception ignored) {}
            if (b.isAlive()) try { process.getErrorStream().close(); } catch (Exception ignored) {}
            if (code == null) try { code = process.exitValue(); } catch (IllegalThreadStateException alive) {}
            boolean incomplete;
            synchronized (stdout) { incomplete = !stdout.complete || stdout.truncated || !stdout.error.isEmpty(); }
            synchronized (stderr) { incomplete |= !stderr.complete || stderr.truncated || !stderr.error.isEmpty(); }
            j.put("state", timeout ? "timeout" : code == null || code != 0 ? "error" : incomplete ? "partial" : "observed")
                .put("exit_code", code == null ? JSONObject.NULL : code).put("timed_out", timeout)
                .put("process_may_continue", code == null).put("stdout", stdout.snapshot(properties));
            // getprop stderr is not a property stream; retain only failure type to avoid accidental values.
            j.put("stderr", properties ? new JSONObject().put("state", "content_excluded").put("reason", "Property command error stream may expose values").put("metadata", stderrMetadata(stderr)) : stderr.snapshot(false));
        } catch (Exception e) { j.put("state", "error").put("error", clean(e.toString(), 1024)); }
        finally { if (process != null) process.destroy(); }
        return j.put("elapsed_ms", SystemClock.elapsedRealtime() - start).put("client_limit_ms", 6000).put("stream_limit_bytes", 1048576);
    }
    private static JSONObject stderrMetadata(Drain d) throws Exception {
        synchronized (d) { return new JSONObject().put("bytes", d.out.size()).put("truncated", d.truncated).put("reader_complete", d.complete).put("read_error", d.error); }
    }
    private static JSONArray sanitizeProperties(String text) throws Exception {
        JSONArray props = new JSONArray();
        for (String line : text.split("\\r?\\n")) {
            int split = line.indexOf("]: [");
            if (!line.startsWith("[") || split < 2 || !line.endsWith("]")) continue;
            String key = line.substring(1, split), value = line.substring(split + 4, line.length() - 1);
            boolean hardware = key.startsWith("ro.build.") || key.startsWith("ro.product.")
                || key.startsWith("ro.board.") || key.startsWith("ro.hardware.") || key.startsWith("ro.soc.")
                || key.startsWith("ro.vendor.build.") || key.startsWith("ro.odm.build.")
                || key.startsWith("ro.system.build.") || key.startsWith("ro.system_ext.build.")
                || key.startsWith("init.svc.") || key.startsWith("persist.sys.usb.")
                || Arrays.asList("ro.hardware", "ro.boot.hardware", "ro.boot.board", "ro.boot.bootreason",
                    "ro.bootmode", "ro.revision", "ro.opengles.version", "ro.sf.lcd_density", "ro.debuggable",
                    "ro.secure", "ro.adb.secure", "ro.crypto.state", "ro.crypto.type", "ro.boot.verifiedbootstate",
                    "ro.boot.flash.locked", "ro.boot.vbmeta.device_state", "ro.boot.slot_suffix", "ro.boot.dtbo_idx",
                    "ro.boot.dtb_idx", "sys.boot.reason", "sys.boot_completed", "service.adb.tcp.port",
                    "persist.adb.tcp.port").contains(key);
            String lower = key.toLowerCase(java.util.Locale.US);
            boolean sensitive = lower.matches(".*(serial|password|passwd|secret|token|credential|ssid|bssid|address|macaddr|bdaddr|android_id|hostname|fingerprintid|attest|key).*")
                || lower.endsWith(".host") || lower.endsWith(".user");
            JSONObject p = new JSONObject().put("name", key);
            if (!hardware || sensitive) p.put("state", "excluded").put("reason", "outside hardware allowlist or potentially sensitive");
            else p.put("state", "observed").put("value", clean(value, 8192));
            props.put(p);
        }
        return props;
    }

    /** Only a fixed set of virtual attributes are read; no device nodes are opened. */
    private static final class HardwareFiles {
        final File session; final JSONArray entries = new JSONArray();
        long written, deadline = SystemClock.elapsedRealtime() + 65000; int reads, timeoutCount; boolean stopped;
        HardwareFiles(File session) { this.session = session; }
        void collect() throws Exception {
            for (String file : new String[]{"cpuinfo", "meminfo", "version", "modules", "partitions", "mounts", "filesystems", "devices", "cmdline"}) {
                // Kernel command lines can include serials and secret OEM arguments; keep an explicit exclusion.
                if (file.equals("cmdline")) { exclude("/proc/cmdline", "may contain personal identifiers or secret boot arguments"); continue; }
                capture("/proc/" + file, "details/proc/" + file + ".txt", 1024 * 1024);
            }
            for (String bus : new String[]{"platform", "sdio", "mmc", "usb", "i2c", "spi", "pci", "amba"}) {
                File dir = new File("/sys/bus/" + bus + "/devices");
                for (File device : children(dir)) {
                    if (!room()) break;
                    JSONObject j = new JSONObject().put("source", device.getPath()).put("kind", "bus_device");
                    try {
                        String real = device.getCanonicalPath();
                        if (!real.startsWith("/sys/devices/")) throw new IOException("Unexpected sysfs target");
                        j.put("state", "observed").put("canonical", real);
                        File driver = new File(device, "driver");
                        try { StructStat st = Os.lstat(driver.getPath());
                            j.put("driver", OsConstants.S_ISLNK(st.st_mode) ? driver.getCanonicalPath() : "not_a_link");
                        } catch (Exception e) { j.put("driver_state", "absent_or_denied"); }
                        entries.put(j);
                        for (String attr : new String[]{"vendor", "device", "class", "revision", "modalias", "idVendor", "idProduct", "bcdDevice", "manufacturer", "product", "name", "type", "of_node/compatible"})
                            capture(new File(device, attr).getPath(), null, SMALL_READ);
                    } catch (Exception e) { entries.put(failure(device.getPath(), "unavailable", e)); }
                }
            }
            for (File block : children(new File("/sys/class/block"))) {
                if (!room()) break;
                JSONObject j = new JSONObject().put("source", block.getPath()).put("kind", "block_node");
                try {
                    String real = block.getCanonicalPath();
                    if (!real.startsWith("/sys/devices/")) throw new IOException("Unexpected block target");
                    j.put("canonical", real).put("state", "observed"); entries.put(j);
                    for (String attr : new String[]{"dev", "partition", "size", "start", "removable", "ro", "alignment_offset", "queue/logical_block_size", "queue/physical_block_size", "device/type", "device/name", "device/manfid", "device/oemid", "device/fwrev", "device/hwrev"})
                        capture(new File(block, attr).getPath(), null, SMALL_READ);
                } catch (Exception e) { entries.put(failure(block.getPath(), "unavailable", e)); }
            }
            for (String path : new String[]{"/sys/class/graphics/fb0/name", "/sys/class/graphics/fb0/modes", "/sys/class/graphics/fb0/virtual_size", "/sys/class/misc/mali0/device/uevent"}) capture(path, null, SMALL_READ);
            exclude("/sys/class/net/*/address", "MAC addresses excluded; SDIO/USB binding observations are collected instead");
            exclude("/dev/block/*", "Normal APK does not read raw partitions or alter mount state");
        }
        List<File> children(File dir) throws Exception {
            if (!room()) return Collections.emptyList();
            File[] files = dir.listFiles();
            if (files == null) { entries.put(new JSONObject().put("source", dir.getPath()).put("state", "unavailable").put("reason", "directory missing or access denied")); return Collections.emptyList(); }
            Arrays.sort(files); int count = Math.min(files.length, 256);
            if (count < files.length) entries.put(new JSONObject().put("source", dir.getPath()).put("state", "omitted").put("reason", "directory entry limit").put("omitted_count", files.length - count));
            return Arrays.asList(Arrays.copyOf(files, count));
        }
        boolean room() throws Exception {
            if (!stopped && (entries.length() >= HARDWARE_ENTRIES || written >= HARDWARE_BYTES || SystemClock.elapsedRealtime() >= deadline || timeoutCount >= 3)) {
                stopped = true; entries.put(new JSONObject().put("source", "hardware attribute traversal").put("state", "omitted")
                    .put("reason", "entry, byte, 65-second cooperative deadline or three-timeout limit reached").put("remaining_sources_enumerated", false));
            }
            return !stopped;
        }
        void exclude(String source, String why) throws Exception { entries.put(new JSONObject().put("source", source).put("state", "excluded").put("reason", why)); }
        void capture(final String source, String destination, final int cap) throws Exception {
            if (!room()) return;
            reads++;
            FutureTask<byte[]> task = new FutureTask<byte[]>(new Callable<byte[]>() {
                public byte[] call() throws Exception {
                    File file = new File(source); String real = file.getCanonicalPath();
                    if (!(real.startsWith("/proc/") || real.startsWith("/sys/devices/") || real.startsWith("/sys/"))) throw new IOException("Virtual path escaped");
                    StructStat st = Os.stat(real);
                    if (!OsConstants.S_ISREG(st.st_mode)) throw new IOException("Not a regular virtual attribute");
                    ByteArrayOutputStream out = new ByteArrayOutputStream();
                    FileInputStream input = new FileInputStream(file);
                    try {
                        byte[] buf = new byte[4096]; int n;
                        while (out.size() <= cap && (n = input.read(buf, 0, Math.min(buf.length, cap + 1 - out.size()))) != -1) {
                            if (Thread.currentThread().isInterrupted()) throw new IOException("Reader interrupted");
                            out.write(buf, 0, n); if (out.size() > cap) break;
                        }
                    } finally { input.close(); }
                    return out.toByteArray();
                }
            });
            Thread thread = new Thread(task, "tvbase-attribute"); thread.setDaemon(true); thread.start();
            try {
                byte[] bytes = task.get(1200, TimeUnit.MILLISECONDS);
                boolean truncated = bytes.length > cap;
                if (truncated) bytes = Arrays.copyOf(bytes, cap);
                JSONObject j = new JSONObject().put("source", source).put("state", truncated ? "truncated" : "observed")
                    .put("captured_bytes", bytes.length).put("sha256", hex(MessageDigest.getInstance("SHA-256").digest(bytes)));
                if (destination == null) j.put("text", new String(bytes, UTF8).replace('\0', '|'));
                else { write(session, destination, bytes); j.put("file", destination); }
                written += bytes.length; entries.put(j);
            } catch (TimeoutException e) { task.cancel(true); timeoutCount++; entries.put(failure(source, "timeout", e).put("operation_may_continue", true)); }
            catch (Exception e) {
                Throwable cause = e.getCause() == null ? e : e.getCause();
                String state = "unavailable";
                if (cause instanceof android.system.ErrnoException) {
                    int errno = ((android.system.ErrnoException) cause).errno;
                    if (errno == OsConstants.EACCES || errno == OsConstants.EPERM) state = "denied";
                } else if (cause instanceof SecurityException) state = "denied";
                entries.put(failure(source, state, cause));
            }
        }
        JSONObject finish() throws Exception {
            JSONObject index = new JSONObject().put("schema_version", 1).put("entries", entries)
                .put("read_attempts", reads).put("captured_bytes", written).put("stopped_at_limit", stopped)
                .put("timeout_count", timeoutCount).put("bytes_limit", HARDWARE_BYTES).put("entries_limit", HARDWARE_ENTRIES)
                .put("state", "finished_with_observations");
            byte[] bytes = index.toString(2).getBytes(UTF8);
            String path = "details/hardware-files.json"; write(session, path, bytes);
            return new JSONObject().put("source", "fixed proc/sysfs allowlist").put("state", "finished_with_observations")
                .put("inventory", path).put("inventory_sha256", hex(MessageDigest.getInstance("SHA-256").digest(bytes)))
                .put("entries", entries.length()).put("captured_bytes", written).put("stopped_at_limit", stopped).put("timeout_count", timeoutCount);
        }
    }
    /** Only called by the collector thread after a reader has returned its bytes. */
    private static void write(File session, String relative, byte[] bytes) throws Exception {
        if (relative.startsWith("/") || relative.contains("..") || relative.contains("\\")) throw new IOException("Unsafe report path");
        File file = new File(session, relative), parent = file.getParentFile();
        if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create report directory");
        String base = session.getCanonicalPath();
        if (!file.getCanonicalPath().startsWith(base + File.separator)) throw new IOException("Report path escaped");
        FileDescriptor fd = Os.open(file.getPath(), OsConstants.O_WRONLY | OsConstants.O_CREAT | OsConstants.O_EXCL | OsConstants.O_NOFOLLOW, 0600);
        FileOutputStream output = new FileOutputStream(fd);
        try { output.write(bytes); output.flush(); output.getFD().sync(); } finally { output.close(); }
        FileInputStream verify = new FileInputStream(file);
        try {
            int offset = 0, n; byte[] buffer = new byte[8192];
            while ((n = verify.read(buffer)) != -1) {
                if (offset + n > bytes.length) throw new IOException("Report readback grew");
                for (int i = 0; i < n; i++) if (buffer[i] != bytes[offset + i]) throw new IOException("Report readback differs");
                offset += n;
            }
            if (offset != bytes.length) throw new IOException("Report readback is truncated");
        } finally { verify.close(); }
        FileDescriptor dir = Os.open(parent.getPath(), OsConstants.O_RDONLY | OsConstants.O_NOFOLLOW, 0);
        try {
            if (!OsConstants.S_ISDIR(Os.fstat(dir).st_mode)) throw new IOException("Report parent is not a directory");
            Os.fsync(dir);
        } finally { Os.close(dir); }
    }
}
