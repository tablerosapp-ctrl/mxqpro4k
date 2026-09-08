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
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** Normal-APK observations; it never changes a device setting or invokes ADB/root. */
public final class HardwareCollector {
    public interface Progress { void update(String message); }
    private static final Charset UTF8 = Charset.forName("UTF-8");
    private static final int SMALL_READ = 8192;
    private static final long HARDWARE_BYTES = 1024L * 1024;
    private static final int HARDWARE_ENTRIES = 256;
    private static final int ARRAY_LIMIT = 64;
    private static final Object READ_LOCK = new Object();
    private static Thread activeRead;
    private HardwareCollector() {}

    /** A cancelled Future is not proof that its kernel/Binder operation ended. */
    public static boolean hasPendingReads() {
        synchronized (READ_LOCK) { return activeRead != null; }
    }
    public static final class PendingReadException extends IOException {
        private static final long serialVersionUID = 1L;
        PendingReadException() { super("An earlier observation worker is still running; no new read was started"); }
    }
    /**
     * Shared by Main's DT/WebView observations and this collector. There is one
     * real worker slot per app process and no queue. Actions must return memory
     * only: no session files, UI callbacks or report mutation are allowed.
     * Cancellation requests interruption; only the real worker's finally block
     * releases its slot, even when the underlying API ignores interruption.
     */
    public static <T> T readBounded(String name, long ms, Callable<T> action) throws Exception {
        if (action == null || ms < 1 || ms > 30000) throw new IllegalArgumentException("Invalid bounded observation");
        final FutureTask<T> task = new FutureTask<T>(action);
        final Thread thread = new Thread(new Runnable() {
            public void run() {
                try { task.run(); }
                finally { synchronized (READ_LOCK) { if (activeRead == Thread.currentThread()) activeRead = null; } }
            }
        }, "tvbase-read-" + clean(name, 48));
        thread.setDaemon(true);
        synchronized (READ_LOCK) {
            if (activeRead != null) throw new PendingReadException();
            activeRead = thread;
            try { thread.start(); }
            catch (Throwable startFailure) { activeRead = null; throw startFailure; }
        }
        try { return task.get(ms, TimeUnit.MILLISECONDS); }
        catch (TimeoutException e) { task.cancel(true); throw e; }
        catch (InterruptedException e) { task.cancel(true); Thread.currentThread().interrupt(); throw e; }
        catch (java.util.concurrent.ExecutionException e) {
            Throwable cause = e.getCause();
            if (cause instanceof Exception) throw (Exception) cause;
            if (cause instanceof Error) throw (Error) cause;
            throw e;
        }
        finally {
            // Future completion precedes the wrapper's final bookkeeping by a
            // few instructions. A bounded join avoids a spurious occupied slot
            // on back-to-back reads; cancellation never waits for a stuck call.
            if (task.isDone() && !task.isCancelled()) thread.join(50);
        }
    }

    public static JSONObject collect(final Context context, File session, Progress cb) throws Exception {
        // Signature retained for Main/0.1 compatibility. This version never
        // opens, enumerates or writes the session; ReportArchive owns all writes.
        final long began = SystemClock.elapsedRealtime();
        JSONObject result = new JSONObject();
        result.put("schema_version", 1).put("collector", "HardwareCollector/0.2")
            .put("privilege", "normal_apk").put("network_requests", false)
            .put("root_or_adb", false);
        JSONObject sections = new JSONObject();
        result.put("sections", sections);
        progress(cb, "Leyendo la plataforma y memoria disponibles");
        sections.put("build", observed("android.os.Build", build()));
        sections.put("memory_storage", timed("Android memory/storage APIs", 2500, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return memoryStorage(context); }
        }));
        sections.put("displays", timed("DisplayManager", 2500, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return displays(context); }
        }));
        progress(cb, "Consultando codecs y controles declarados por Android");
        sections.put("codecs", timed("MediaCodecList.ALL_CODECS", 4000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return codecs(); }
        }));
        sections.put("input_devices", timed("InputDevice", 2500, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return inputs(); }
        }));
        progress(cb, "Inventariando paquetes y funciones del sistema");
        sections.put("packages_features", timed("PackageManager", 4000, new Callable<JSONObject>() {
            public JSONObject call() throws Exception { return packages(context); }
        }));
        progress(cb, "Leyendo propiedades, buses y particiones accesibles");
        JSONArray commands = new JSONArray();
        commands.put(command("getprop", new String[]{"/system/bin/getprop"}, true));
        commands.put(command("uname", new String[]{"/system/bin/uname", "-s", "-r", "-m", "-v"}, false));
        commands.put(command("id", new String[]{"/system/bin/id"}, false));
        sections.put("commands", commands);
        HardwareFiles files = new HardwareFiles();
        files.collect();
        JSONObject fileSummary = files.finish();
        sections.put("hardware_files", fileSummary);
        sections.put("driver_files", new JSONObject().put("state", "deferred_to_recovery")
            .put("binary_driver_copies", false).put("device_tree_traversal", false)
            .put("reason", "Deep firmware, driver file and device-tree acquisition is a separate recovery operation; this APK records accessible metadata only."));
        result.put("elapsed_ms", SystemClock.elapsedRealtime() - began);
        result.put("state", "finished_with_observations");
        result.put("pending_read_worker", hasPendingReads()).put("maximum_observation_workers", 1)
            .put("writes_from_observation_workers", false).put("array_item_limit", ARRAY_LIMIT);
        result.put("completeness", "Only accessible observations; inspect every section and omission. This is not a complete hardware or firmware backup.");
        result.put("limits", new JSONArray(Arrays.asList(
            "Build properties and DT describe software configuration, not an independently identified physical chip.",
            "Codecs advertise capabilities; none were instantiated or benchmarked. Hardware decoding, VP9 alpha and simultaneous video remain untested.",
            "Bound sysfs driver names are stronger evidence of the active software binding, not proof that every function works.",
            "Package visibility and protected proc/sysfs files may be restricted by Android; denial is recorded.",
            "Timeout only bounds the client. One real observation worker may remain blocked; the slot stays occupied until that worker exits. No observation worker writes report files.",
            "A sysfs directory listing itself may allocate or block inside Android before returning; only returned entries and client waiting are bounded. Omitted nodes are not evidence of absent hardware.",
            "Array processing and text size are capped. Drivers and DT trees are not copied by this version.",
            "Fixed getprop/uname/id processes share the reader slot; after best-effort destroy the worker waits for the started process to exit. A surviving process keeps the slot occupied; interruption does not certify process termination.",
            "No private app data, WiFi credentials, key material, network connections or privileged partition reads are collected."
        )));
        return result;
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
        JSONObject answer;
        try { answer = observed(source, readBounded(source, ms, action)); }
        catch (TimeoutException e) {
            answer = failure(source, "timeout", e).put("operation_may_continue", true);
        } catch (PendingReadException e) {
            answer = failure(source, "skipped_pending_read", e).put("operation_started", false);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); throw e;
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
            if (Thread.currentThread().isInterrupted()) throw new IOException("Storage observation interrupted");
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
        Display[] reported = ((DisplayManager) context.getSystemService(Context.DISPLAY_SERVICE)).getDisplays();
        for (int index = 0; index < reported.length && index < 16; index++) {
            if (Thread.currentThread().isInterrupted()) throw new IOException("Display observation interrupted");
            Display d = reported[index];
            JSONObject j = new JSONObject().put("id", d.getDisplayId()).put("name", d.getName())
                .put("state", d.getState()).put("flags", d.getFlags()).put("refresh_hz", d.getRefreshRate());
            Point size = new Point(); d.getRealSize(size);
            DisplayMetrics m = new DisplayMetrics(); d.getRealMetrics(m);
            j.put("real_width", size.x).put("real_height", size.y).put("density_dpi", m.densityDpi)
                .put("xdpi", m.xdpi).put("ydpi", m.ydpi);
            JSONArray modes = new JSONArray();
            if (Build.VERSION.SDK_INT >= 23) {
                Display.Mode[] supported = d.getSupportedModes();
                for (int indexMode = 0; indexMode < supported.length && indexMode < ARRAY_LIMIT; indexMode++) {
                    Display.Mode mode = supported[indexMode]; modes.put(new JSONObject()
                    .put("mode_id", mode.getModeId()).put("width", mode.getPhysicalWidth())
                    .put("height", mode.getPhysicalHeight()).put("refresh_hz", mode.getRefreshRate()));
                }
                j.put("omitted_modes", Math.max(0, supported.length - modes.length()));
                j.put("active_mode_id", d.getMode().getModeId());
            }
            j.put("supported_modes", modes); all.put(j);
        }
        return new JSONObject().put("items", all).put("omitted_displays", reported.length - all.length())
            .put("note", "Advertised display modes; no output mode was changed.");
    }
    private static JSONObject codecs() throws Exception {
        MediaCodecInfo[] all = new MediaCodecList(MediaCodecList.ALL_CODECS).getCodecInfos();
        JSONArray items = new JSONArray();
        for (int n = 0; n < all.length && n < 64; n++) {
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
            for (int t = 0; t < supported.length && t < 8; t++) {
                if (Thread.currentThread().isInterrupted()) throw new IOException("Codec observation interrupted");
                String type = supported[t];
                JSONObject cap = new JSONObject().put("mime", type);
                try {
                    MediaCodecInfo.CodecCapabilities c = info.getCapabilitiesForType(type);
                    cap.put("state", "observed").put("color_formats", ints(c.colorFormats));
                    JSONArray levels = new JSONArray();
                    for (int indexLevel = 0; indexLevel < c.profileLevels.length && indexLevel < ARRAY_LIMIT; indexLevel++) {
                        MediaCodecInfo.CodecProfileLevel pl = c.profileLevels[indexLevel];
                        levels.put(new JSONObject().put("profile", pl.profile).put("level", pl.level));
                    }
                    cap.put("profile_levels", levels).put("omitted_profile_levels", Math.max(0, c.profileLevels.length - levels.length()));
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
                        Range<Integer>[] supportedRates = a.getSupportedSampleRateRanges();
                        for (int rateIndex = 0; rateIndex < supportedRates.length && rateIndex < ARRAY_LIMIT; rateIndex++) rates.put(range(supportedRates[rateIndex]));
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
            j.put("types", types).put("omitted_types", Math.max(0, supported.length - types.length())); items.put(j);
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
            if (Thread.currentThread().isInterrupted()) throw new IOException("Input observation interrupted");
            InputDevice d = InputDevice.getDevice(ids[i]);
            if (d == null) { items.put(new JSONObject().put("id", ids[i]).put("state", "disappeared")); continue; }
            JSONObject j = new JSONObject().put("id", d.getId()).put("name", d.getName())
                .put("vendor_id", d.getVendorId()).put("product_id", d.getProductId())
                .put("sources", d.getSources()).put("virtual", d.isVirtual()).put("keyboard_type", d.getKeyboardType());
            JSONArray motion = new JSONArray();
            List<InputDevice.MotionRange> reportedMotion = d.getMotionRanges();
            for (int motionIndex = 0; motionIndex < reportedMotion.size() && motionIndex < ARRAY_LIMIT; motionIndex++) {
                InputDevice.MotionRange r = reportedMotion.get(motionIndex); motion.put(new JSONObject()
                .put("axis", r.getAxis()).put("source", r.getSource()).put("min", r.getMin())
                .put("max", r.getMax()).put("flat", r.getFlat()).put("fuzz", r.getFuzz()).put("resolution", r.getResolution()));
            }
            j.put("motion_ranges", motion).put("omitted_motion_ranges", reportedMotion.size() - motion.length());
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
        if (fs != null) for (int featureIndex = 0; featureIndex < fs.length && featureIndex < 256; featureIndex++) {
            if (Thread.currentThread().isInterrupted()) throw new IOException("Feature observation interrupted");
            FeatureInfo f = fs[featureIndex];
            JSONObject j = new JSONObject().put("name", f.name == null ? JSONObject.NULL : f.name)
                .put("flags", f.flags).put("req_gl_es_version", f.reqGlEsVersion);
            if (Build.VERSION.SDK_INT >= 24) j.put("version", f.version);
            features.put(j);
        }
        int flags = PackageManager.GET_SIGNATURES | PackageManager.GET_PERMISSIONS | PackageManager.GET_META_DATA;
        if (Build.VERSION.SDK_INT >= 28) flags |= PackageManager.GET_SIGNING_CERTIFICATES;
        List<PackageInfo> list = pm.getInstalledPackages(flags);
        JSONArray items = new JSONArray();
        for (int i = 0; i < list.size() && i < 256; i++) {
            if (Thread.currentThread().isInterrupted()) break;
            PackageInfo p = list.get(i);
            JSONObject j = new JSONObject().put("package_name", clean(p.packageName, 256));
            try {
                j.put("version_name", clean(p.versionName, 256)).put("version_code", Build.VERSION.SDK_INT >= 28 ? p.getLongVersionCode() : p.versionCode);
                ApplicationInfo a = p.applicationInfo;
                if (a != null) {
                    j.put("source_dir", clean(a.sourceDir, 1024)).put("split_source_dirs", strings(a.splitSourceDirs))
                        .put("flags", a.flags).put("enabled", a.enabled).put("target_sdk", a.targetSdkVersion)
                        .put("native_library_dir", clean(a.nativeLibraryDir, 1024)).put("system_app", (a.flags & ApplicationInfo.FLAG_SYSTEM) != 0);
                    if (Build.VERSION.SDK_INT >= 24) j.put("min_sdk", a.minSdkVersion);
                    JSONArray metadata = new JSONArray();
                    Bundle b = a.metaData;
                    if (b != null) for (String key : b.keySet()) {
                        if (metadata.length() >= 32 || Thread.currentThread().isInterrupted()) break;
                        metadata.put(new JSONObject().put("key", clean(key, 256))
                            .put("state", "value_excluded").put("reason", "Metadata values can contain credentials; only names are inventoried."));
                    }
                    j.put("metadata", metadata);
                }
                j.put("requested_permissions", strings(p.requestedPermissions)).put("requested_permission_flags", ints(p.requestedPermissionsFlags));
                JSONArray certs = new JSONArray(); Signature[] signatures = p.signatures;
                if (Build.VERSION.SDK_INT >= 28 && p.signingInfo != null)
                    signatures = p.signingInfo.hasMultipleSigners() ? p.signingInfo.getApkContentsSigners() : p.signingInfo.getSigningCertificateHistory();
                if (signatures != null) for (int signatureIndex = 0; signatureIndex < signatures.length && signatureIndex < 8; signatureIndex++) {
                    byte[] certificate = signatures[signatureIndex].toByteArray();
                    if (certificate.length > 65536) certs.put(new JSONObject().put("state", "omitted").put("reason", "certificate byte limit"));
                    else certs.put(new JSONObject().put("sha256", hex(MessageDigest.getInstance("SHA-256").digest(certificate))));
                }
                j.put("signing_certificate_hashes", certs).put("state", "observed");
            } catch (Exception e) { j.put("state", "error").put("error", clean(e.toString(), 1024)); }
            items.put(j);
        }
        return new JSONObject().put("features", features).put("omitted_features", fs == null ? 0 : fs.length - features.length())
            .put("packages", items).put("visible_count", list.size()).put("array_item_limit", ARRAY_LIMIT)
            .put("metadata_key_limit", 32).put("certificate_count_limit", 8)
            .put("omitted_visible_packages", list.size() - items.length())
            .put("visibility_limit", "Normal PackageManager visibility; absence is not proof of absence. No private application data was opened.");
    }
    private static JSONArray strings(String[] values) {
        JSONArray j = new JSONArray();
        if (values != null) for (int i = 0; i < values.length && i < ARRAY_LIMIT; i++) j.put(clean(values[i], 256));
        return j;
    }
    private static JSONArray ints(int[] values) { JSONArray j = new JSONArray(); if (values != null) for (int i = 0; i < values.length && i < ARRAY_LIMIT; i++) j.put(values[i]); return j; }
    private static JSONObject range(Range<?> value) throws Exception { return new JSONObject().put("lower", value.getLower()).put("upper", value.getUpper()); }
    private static String hex(byte[] bytes) { StringBuilder b = new StringBuilder(); for (byte v : bytes) b.append(String.format(java.util.Locale.US, "%02x", v & 255)); return b.toString(); }

    private static JSONObject command(final String name, final String[] argv, final boolean properties) throws Exception {
        return timed("ProcessBuilder fixed allowlist: " + name, 2500, new Callable<JSONObject>() {
            public JSONObject call() throws Exception {
                if (!(name.equals("getprop") || name.equals("uname") || name.equals("id"))) throw new IOException("Command not allowed");
                Process process = null;
                try {
                    process = new ProcessBuilder(argv).redirectErrorStream(true).start();
                    process.getOutputStream().close();
                    byte[] bytes;
                    try { bytes = readBytes(process.getInputStream(), 128 * 1024); }
                    finally { process.getInputStream().close(); }
                    boolean truncated = bytes.length > 128 * 1024;
                    if (truncated) bytes = Arrays.copyOf(bytes, 128 * 1024);
                    Integer code = null;
                    try { code = process.exitValue(); } catch (IllegalThreadStateException alive) { }
                    JSONObject value = new JSONObject().put("argv", strings(argv)).put("stream_limit_bytes", 128 * 1024)
                        .put("truncated", truncated).put("exit_code", code == null ? JSONObject.NULL : code)
                        .put("process_may_continue", code == null).put("stderr", "merged; getprop retains only sanitized property records")
                        .put("state", truncated || code == null ? "partial" : code == 0 ? "observed" : "error");
                    String text = new String(bytes, UTF8);
                    if (properties) value.put("properties", sanitizeProperties(text)); else value.put("text", text);
                    return value;
                } finally {
                    // Cleanup is best effort and belongs to the tracked worker;
                    // if a native read/close/destroy blocks, its slot stays busy.
                    if (process != null) {
                        try { process.destroy(); }
                        finally {
                            // Never free the sole slot while a process we
                            // started can still run. waitFor belongs to this
                            // worker, not the capture/UI thread. Cancellation
                            // cannot turn a surviving child into a free slot.
                            boolean interrupted = false;
                            for (;;) {
                                try { process.waitFor(); break; }
                                catch (InterruptedException e) { interrupted = true; }
                            }
                            if (interrupted) Thread.currentThread().interrupt();
                        }
                    }
                }
            }
        });
    }
    private static JSONArray sanitizeProperties(String text) throws Exception {
        JSONArray props = new JSONArray();
        for (String line : text.split("\\r?\\n")) {
            if (Thread.currentThread().isInterrupted()) throw new IOException("Property observation interrupted");
            if (props.length() >= 2048) break;
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

    /** A byte cap bounds returned data, not a native syscall that ignores interrupts. */
    static byte[] readBytes(InputStream input, int cap) throws IOException {
        if (cap < 1 || cap > 1024 * 1024) throw new IOException("Invalid observation byte limit");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[Math.min(4096, cap + 1)];
        int empty = 0;
        while (out.size() <= cap) {
            if (Thread.currentThread().isInterrupted()) throw new IOException("Reader interrupted");
            int n = input.read(buffer, 0, Math.min(buffer.length, cap + 1 - out.size()));
            if (n == -1) break;
            if (n == 0) { if (++empty >= 3) throw new IOException("Reader made no progress"); continue; }
            empty = 0; out.write(buffer, 0, n);
        }
        if (Thread.currentThread().isInterrupted()) throw new IOException("Reader interrupted");
        return out.toByteArray();
    }

    /** Fixed virtual roots only. Discovery and reads return memory, never files. */
    private static final class HardwareFiles {
        final JSONArray entries = new JSONArray();
        final long deadline = SystemClock.elapsedRealtime() + 15000;
        long captured;
        int reads, timeoutCount;
        boolean stopped;
        final java.util.ArrayList<String> blocks = new java.util.ArrayList<String>();
        final java.util.ArrayList<String> devices = new java.util.ArrayList<String>();

        void collect() throws Exception {
            for (String name : new String[]{"cpuinfo", "meminfo", "version", "modules", "partitions", "mounts", "filesystems", "devices"})
                capture("/proc/" + name, 65536);
            // Describe bindings before optional attributes so a busy platform
            // directory does not consume the budget before SDIO/USB are seen.
            discover("/sys/class/block", 24, "block_node", blocks);
            for (String bus : new String[]{"sdio", "usb", "platform", "mmc"})
                discover("/sys/bus/" + bus + "/devices", 16, "bus_device", devices);
            for (String path : blocks) {
                if (!room()) break;
                for (String attr : new String[]{"dev", "size", "removable", "ro", "device/type", "device/name"})
                    capture(path + "/" + attr, SMALL_READ);
            }
            for (String path : devices) {
                if (!room()) break;
                for (String attr : new String[]{"vendor", "device", "modalias", "idVendor", "idProduct", "name"})
                    capture(path + "/" + attr, SMALL_READ);
            }
            for (String path : new String[]{"/sys/class/graphics/fb0/name", "/sys/class/graphics/fb0/modes", "/sys/class/graphics/fb0/virtual_size"})
                capture(path, SMALL_READ);
            exclude("/proc/cmdline", "may contain identifiers or secret OEM boot arguments");
            exclude("/sys/class/net/*/address", "MAC addresses excluded");
            exclude("/dev/block/*", "raw partition acquisition deferred to recovery; no device node opened");
            exclude("/proc/device-tree and /sys/firmware/devicetree", "deep traversal deferred to recovery; Main owns the separately bounded profile identity read");
            exclude("/sys/bus/{i2c,spi,pci,amba}", "additional bus traversal deferred to the deeper inventory");
        }

        boolean room() throws Exception {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedException("Collector interrupted");
            if (!stopped && (entries.length() >= HARDWARE_ENTRIES || captured >= HARDWARE_BYTES
                    || reads >= 160 || SystemClock.elapsedRealtime() >= deadline || hasPendingReads())) {
                stopped = true;
                entries.put(new JSONObject().put("source", "hardware metadata observation").put("state", "omitted")
                    .put("reason", hasPendingReads() ? "an earlier worker is still running" : "entry, byte, read-count or 15-second cooperative deadline reached")
                    .put("remaining_sources_enumerated", false));
            }
            return !stopped;
        }
        <T> T observe(String source, Callable<T> action) throws Exception {
            if (!room()) return null;
            reads++;
            try { return readBounded("attribute", 1200, action); }
            catch (TimeoutException e) {
                timeoutCount++; stopped = true;
                entries.put(failure(source, "timeout", e).put("operation_may_continue", true).put("remaining_reads_skipped", true));
            } catch (PendingReadException e) {
                stopped = true;
                entries.put(failure(source, "skipped_pending_read", e).put("operation_started", false));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt(); throw e;
            } catch (Exception e) {
                String state = "unavailable";
                if (e instanceof android.system.ErrnoException) {
                    int errno = ((android.system.ErrnoException) e).errno;
                    if (errno == OsConstants.EACCES || errno == OsConstants.EPERM) state = "denied";
                } else if (e instanceof SecurityException) state = "denied";
                entries.put(failure(source, state, e));
            }
            return null;
        }
        void discover(final String directory, final int maximum, final String kind, List<String> targets) throws Exception {
            JSONObject listing = observe(directory, new Callable<JSONObject>() {
                public JSONObject call() throws Exception {
                    String[] names = new File(directory).list();
                    JSONObject answer = new JSONObject().put("source", directory).put("kind", "directory")
                        .put("maximum_selected_entries", maximum).put("maximum_processed_directory_entries", 1024);
                    JSONArray selected = new JSONArray();
                    if (names == null) return answer.put("state", "unavailable").put("names", selected)
                        .put("reason", "directory absent or access denied");
                    answer.put("reported_count", names.length);
                    if (names.length > 1024) return answer.put("state", "omitted").put("names", selected)
                        .put("reason", "returned directory array exceeds processing limit");
                    Arrays.sort(names);
                    for (String name : names) {
                        if (Thread.currentThread().isInterrupted()) throw new IOException("Directory processing interrupted");
                        if (selected.length() >= maximum) break;
                        if (name.equals(".") || name.equals("..") || !name.matches("[A-Za-z0-9_.:+-]{1,128}")) continue;
                        selected.put(name);
                    }
                    return answer.put("state", "observed").put("names", selected)
                        .put("omitted_entries", names.length - selected.length());
                }
            });
            if (listing == null) return;
            entries.put(listing);
            JSONArray names = listing.getJSONArray("names");
            for (int i = 0; i < names.length() && room(); i++) {
                final String path = directory + "/" + names.getString(i);
                JSONObject descriptor = observe(path, new Callable<JSONObject>() {
                    public JSONObject call() throws Exception {
                        File file = new File(path);
                        String canonical = file.getCanonicalPath();
                        if (!canonical.startsWith("/sys/devices/")) throw new IOException("Unexpected sysfs target");
                        JSONObject node = new JSONObject().put("source", path).put("kind", kind)
                            .put("canonical", clean(canonical, 4096)).put("state", "observed");
                        File driver = new File(file, "driver");
                        try {
                            StructStat st = Os.lstat(driver.getPath());
                            if (OsConstants.S_ISLNK(st.st_mode)) {
                                String binding = driver.getCanonicalPath();
                                if (!binding.startsWith("/sys/")) throw new IOException("Driver link escaped sysfs");
                                node.put("driver", clean(binding, 4096)).put("driver_name", clean(new File(binding).getName(), 256));
                            } else node.put("driver_state", "not_a_link");
                        } catch (Exception e) { node.put("driver_state", "absent_or_denied").put("driver_error_type", e.getClass().getSimpleName()); }
                        return node;
                    }
                });
                if (descriptor != null) { entries.put(descriptor); targets.add(path); }
            }
        }
        void exclude(String source, String reason) throws Exception {
            entries.put(new JSONObject().put("source", source).put("state", "excluded").put("reason", reason));
        }
        void capture(final String source, final int cap) throws Exception {
            final int limit = (int) Math.min((long) cap, HARDWARE_BYTES - captured);
            if (limit < 1) { room(); return; }
            byte[] bytes = observe(source, new Callable<byte[]>() {
                public byte[] call() throws Exception {
                    File file = new File(source);
                    String canonical = file.getCanonicalPath();
                    if (!(canonical.startsWith("/proc/") || canonical.startsWith("/sys/"))) throw new IOException("Virtual path escaped");
                    StructStat st = Os.stat(canonical);
                    if (!OsConstants.S_ISREG(st.st_mode)) throw new IOException("Not a regular virtual attribute");
                    FileDescriptor fd = Os.open(canonical, OsConstants.O_RDONLY | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0);
                    FileInputStream input = new FileInputStream(fd);
                    try {
                        if (!OsConstants.S_ISREG(Os.fstat(fd).st_mode)) throw new IOException("Opened source is not a regular virtual attribute");
                        return readBytes(input, limit);
                    }
                    finally { input.close(); }
                }
            });
            if (bytes == null) return;
            boolean truncated = bytes.length > limit;
            if (truncated) bytes = Arrays.copyOf(bytes, limit);
            String text = new String(bytes, UTF8).replace('\0', '|');
            boolean filtered = source.equals("/proc/cpuinfo");
            if (filtered) {
                StringBuilder safe = new StringBuilder();
                for (String line : text.split("\\r?\\n"))
                    if (!line.trim().toLowerCase(java.util.Locale.US).startsWith("serial")) safe.append(line).append('\n');
                text = safe.toString(); bytes = text.getBytes(UTF8);
                if (bytes.length > limit) {
                    bytes = Arrays.copyOf(bytes, limit); text = new String(bytes, UTF8); truncated = true;
                }
            }
            captured += bytes.length;
            entries.put(new JSONObject().put("source", source).put("state", truncated ? "truncated" : "observed")
                .put("captured_bytes", bytes.length).put("sha256", hex(MessageDigest.getInstance("SHA-256").digest(bytes)))
                .put("text", text).put("sensitive_serial_lines_excluded", filtered));
        }
        JSONObject finish() throws Exception {
            return new JSONObject().put("schema_version", 1).put("source", "bounded proc/sysfs metadata allowlist")
                .put("state", "finished_with_observations").put("inventory_storage", "inline")
                .put("observations", entries).put("entries", entries.length()).put("read_attempts", reads)
                .put("captured_bytes", captured).put("stopped_at_limit", stopped).put("timeout_count", timeoutCount)
                .put("bytes_limit", HARDWARE_BYTES).put("entries_limit", HARDWARE_ENTRIES).put("read_limit", 160)
                .put("client_read_limit_ms", 1200).put("cooperative_section_limit_ms", 15000)
                .put("pending_read_worker", hasPendingReads()).put("binary_files_copied", false);
        }
    }
}
