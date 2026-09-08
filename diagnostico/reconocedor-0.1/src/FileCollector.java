package com.tvbase.reconocimiento;

import android.os.SystemClock;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import org.json.JSONObject;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Locale;

/** Bounded, unprivileged collection of static platform files and public DT properties. */
public final class FileCollector {
    private static final Charset UTF8 = Charset.forName("UTF-8");
    private static final long TOTAL_LIMIT = 1536L * 1024L * 1024L;
    private static final long FILE_LIMIT = 128L * 1024L * 1024L;
    private static final long DT_TOTAL_LIMIT = 16L * 1024L * 1024L;
    private static final long DT_FILE_LIMIT = 1024L * 1024L;
    private static final long TIME_LIMIT_MS = 12L * 60L * 1000L;
    private static final int ENTRY_LIMIT = 18000;
    private static final int DIRECTORY_LIMIT = 4000;
    private static final int DEPTH_LIMIT = 18;
    private static final String[] ROOTS = {"/vendor", "/odm", "/system", "/product", "/system_ext"};
    private static final String[] SEEDS = {"lib", "lib64", "etc", "firmware", "usr/keylayout", "usr/keychars"};

    private FileCollector() { }

    public static JSONObject collect(File session, HardwareCollector.Progress cb) throws Exception {
        File canonicalSession = session.getCanonicalFile();
        if (!canonicalSession.isDirectory()) throw new IOException("La sesión no es un directorio existente");
        State state = new State(canonicalSession, cb);
        JSONObject result = new JSONObject();
        Index drivers = null;
        Index dt = null;
        try {
            state.makeDirectories(new File(canonicalSession, "drivers"));
            state.makeDirectories(new File(canonicalSession, "details/dt"));
            drivers = new Index(state, new File(canonicalSession, "drivers/inventory.jsonl"));
            dt = new Index(state, new File(canonicalSession, "details/dt/inventory.jsonl"));
            if (cb != null) cb.update("Recogiendo propiedades públicas accesibles del árbol de dispositivos");
            // /proc/device-tree normally aliases this directory. Never follow that alias blindly.
            File dtRoot = new File("/sys/firmware/devicetree/base");
            if (!state.stopped() && sourceRoot(state, dt, dtRoot, true)) {
                walk(state, dt, dtRoot, dtRoot, "", 0, true);
            } else if (!state.stopped()) {
                File alternative = new File("/proc/device-tree");
                if (sourceRoot(state, dt, alternative, true))
                    walk(state, dt, alternative, alternative, "", 0, true);
            }
            if (cb != null) cb.update("Inventariando controladores y bibliotecas accesibles");
            for (String root : ROOTS) {
                if (state.stopped()) break;
                File sourceRoot = new File(root);
                if (!sourceRoot(state, drivers, sourceRoot, false)) continue;
                for (String seed : SEEDS) {
                    if (state.stopped()) break;
                    File source = new File(sourceRoot, seed);
                    walk(state, drivers, sourceRoot, source, seed, 0, false);
                }
            }
            if (cb != null) cb.update("Verificando el cierre de los inventarios de archivos");
            result.put("drivers_index", drivers.finish());
            drivers = null;
            result.put("device_tree_index", dt.finish());
            dt = null;
            result.put("state", state.stopReason != null ? "partial_budget_or_cancelled"
                    : (state.errors > 0 || state.denied > 0 || state.copyLimited > 0 ? "partial_access_or_io"
                    : (state.omitted > 0 || state.unavailable > 0 ? "finished_with_exclusions" : "finished_bounded_inventory")));
            result.put("scope", "Static selected platform files; accessible public DT properties. Not a complete driver backup or hardware qualification.");
            result.put("entries_seen", state.entries);
            result.put("directories_seen", state.directories);
            result.put("copied_files", state.copied);
            result.put("copied_bytes", state.copiedBytes);
            result.put("source_bytes_read", state.readBytes);
            result.put("device_tree_copied_bytes", state.dtCopiedBytes);
            result.put("omitted", state.omitted);
            result.put("denied", state.denied);
            result.put("unavailable", state.unavailable);
            result.put("errors", state.errors);
            result.put("limited_files", state.copyLimited);
            result.put("stop_reason", state.stopReason == null ? JSONObject.NULL : state.stopReason);
            result.put("elapsed_ms", SystemClock.elapsedRealtime() - state.started);
            result.put("limits", new JSONObject().put("source_bytes", state.readLimit).put("file_bytes", FILE_LIMIT)
                    .put("dt_source_bytes", DT_TOTAL_LIMIT).put("dt_file_bytes", DT_FILE_LIMIT)
                    .put("entries", ENTRY_LIMIT).put("directories", DIRECTORY_LIMIT).put("depth", DEPTH_LIMIT)
                    .put("elapsed_ms", TIME_LIMIT_MS));
            result.put("time_limit_scope", "Checked between operations; cannot interrupt a kernel filesystem call already blocked.");
            result.put("privacy", "App data is outside allowed roots. Known account, WiFi configuration, serial/MAC DT, credential/key, calibration and NVRAM paths are excluded. Filename filtering cannot certify the contents of vendor binaries; review before public sharing.");
            result.put("durability", "Each successful copy was synced, closed, reread and SHA-256 compared; containing directories and final JSONL indices were synced.");
            return result;
        } finally {
            if (drivers != null) drivers.abort();
            if (dt != null) dt.abort();
        }
    }

    private static boolean sourceRoot(State s, Index index, File root, boolean isDt) throws Exception {
        JSONObject row = row(root, isDt).put("kind", "source_root");
        try {
            requireSourcePath(root);
            StructStat st = Os.lstat(root.getPath());
            if (!OsConstants.S_ISDIR(st.st_mode)) throw new IOException("Root is not a real directory");
            index.add(row.put("state", "accessible"));
            return true;
        } catch (Exception e) {
            recordError(s, row, e);
            index.add(row);
            return false;
        }
    }

    private static void walk(State s, Index index, File root, File source, String relative,
                             int depth, boolean isDt) throws Exception {
        if (s.stopped()) return;
        if (++s.entries > ENTRY_LIMIT) { s.stopReason = "entry_limit"; return; }
        s.progress("Revisando archivos y carpetas");
        JSONObject record = row(source, isDt);
        if (!safeRelative(relative)) { s.omitted++; index.add(record.put("state", "omitted_unsafe_name")); return; }
        if (sensitive(relative, isDt)) { s.omitted++; index.add(record.put("state", "omitted_sensitive_path")); return; }
        try {
            requireSourcePath(source);
            StructStat before = Os.lstat(source.getPath());
            if (OsConstants.S_ISLNK(before.st_mode)) {
                s.omitted++; index.add(record.put("state", "omitted_symlink")); return;
            }
            if (OsConstants.S_ISDIR(before.st_mode)) {
                if (++s.directories > DIRECTORY_LIMIT) { s.stopReason = "directory_limit"; index.add(record.put("state", s.stopReason)); return; }
                if (depth >= DEPTH_LIMIT) { s.omitted++; index.add(record.put("state", "omitted_depth_limit")); return; }
                if (!isDt && !wantedDirectory(relative)) {
                    s.omitted++; index.add(record.put("state", "omitted_directory_outside_scope")); return;
                }
                String[] children = source.list();
                if (children == null) { s.denied++; index.add(record.put("state", "directory_unreadable")); return; }
                if (children.length > ENTRY_LIMIT - s.entries) {
                    s.stopReason = "directory_entry_budget";
                    index.add(record.put("state", s.stopReason).put("children", children.length)); return;
                }
                Arrays.sort(children);
                for (String name : children) {
                    if (s.stopped()) break;
                    if (!safeSegment(name)) { s.omitted++; index.add(record.put("state", "omitted_unsafe_child_name")); continue; }
                    String childRelative = relative.length() == 0 ? name : relative + "/" + name;
                    walk(s, index, root, new File(source, name), childRelative, depth + 1, isDt);
                }
                return;
            }
            if (!OsConstants.S_ISREG(before.st_mode)) {
                s.omitted++; index.add(record.put("state", "omitted_non_regular")); return;
            }
            if (!isDt && !wantedFile(relative)) {
                s.omitted++; index.add(record.put("state", "omitted_file_outside_scope")); return;
            }
            record.put("declared_bytes", before.st_size).put("mode", before.st_mode & 07777);
            long perFile = isDt ? DT_FILE_LIMIT : FILE_LIMIT;
            if (before.st_size < 0 || before.st_size > perFile) {
                s.copyLimited++; index.add(record.put("state", "omitted_file_size_limit")); return;
            }
            long remaining = Math.min(s.readLimit - s.readBytes, isDt ? DT_TOTAL_LIMIT - s.dtReadBytes : s.readLimit);
            if (before.st_size > remaining || remaining <= 0) {
                s.copyLimited++; index.add(record.put("state", "omitted_remaining_byte_budget"));
                if (s.readLimit - s.readBytes <= 0) s.stopReason = "source_byte_limit";
                return;
            }
            String portableRelative = portableRelative(relative);
            String destination = isDt ? "details/dt/files/" + portableRelative
                    : "drivers/" + root.getName() + "/" + portableRelative;
            copy(s, source, new File(s.session, destination), before, perFile, remaining, isDt, record);
            index.add(record);
        } catch (Exception e) {
            recordError(s, record, e);
            index.add(record);
        }
    }

    private static void copy(State s, File source, File target, StructStat before, long perFile,
                             long remaining, boolean isDt, JSONObject record) throws Exception {
        FileInputStream in = null;
        FileOutputStream out = null;
        StructStat created = null;
        boolean verified = false;
        long bytes = 0;
        long started = SystemClock.elapsedRealtime();
        try {
            requireSourcePath(source);
            FileDescriptor sourceFd = Os.open(source.getPath(), OsConstants.O_RDONLY | OsConstants.O_NOFOLLOW
                    | OsConstants.O_CLOEXEC | OsConstants.O_NONBLOCK, 0);
            in = new FileInputStream(sourceFd);
            StructStat opened = Os.fstat(sourceFd);
            if (!sameFile(before, opened) || !OsConstants.S_ISREG(opened.st_mode))
                throw new IOException("Source changed before open");
            requireSourcePath(source);
            s.makeDirectories(target.getParentFile());
            s.requireDestination(target);
            FileDescriptor outputFd = Os.open(target.getPath(), OsConstants.O_WRONLY | OsConstants.O_CREAT
                    | OsConstants.O_EXCL | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0600);
            out = new FileOutputStream(outputFd);
            created = Os.fstat(outputFd);
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[65536];
            long readCap = Math.min(perFile, remaining);
            while (true) {
                if (s.timeOrCancelled()) throw new LimitedException("Copy stopped at time/cancellation limit");
                // Real files have a declared length. DT properties may report zero instead.
                if ((!isDt || opened.st_size != 0) && bytes == opened.st_size) break;
                if (bytes >= readCap) throw new LimitedException("Copy reached its byte limit before a verified end");
                int count = in.read(buffer, 0, (int)Math.min(buffer.length, readCap - bytes));
                if (count == -1) break;
                s.readBytes += count;
                if (isDt) s.dtReadBytes += count;
                bytes += count;
                hash.update(buffer, 0, count);
                out.write(buffer, 0, count);
                s.progress("Leyendo y copiando archivos");
            }
            StructStat ended = Os.fstat(sourceFd);
            requireSourcePath(source);
            StructStat after = Os.lstat(source.getPath());
            if (!sameFile(opened, ended) || !sameFile(opened, after)
                    || opened.st_size != ended.st_size || opened.st_mtime != ended.st_mtime
                    || opened.st_ctime != ended.st_ctime)
                throw new IOException("Source changed during reading");
            // DT pseudo-files can legitimately report size zero despite containing bytes.
            if ((!isDt || opened.st_size != 0) && bytes != opened.st_size)
                throw new IOException("Source length differs from metadata");
            out.flush();
            outputFd.sync();
            out.close(); out = null;
            in.close(); in = null;
            String originalHash = hex(hash.digest());
            Digest check = digestTarget(s, target, created, bytes);
            if (check.bytes != bytes || !check.sha.equals(originalHash))
                throw new IOException("Destination readback differs");
            syncDirectory(target.getParentFile());
            verified = true;
            s.copied++;
            s.copiedBytes += bytes;
            if (isDt) s.dtCopiedBytes += bytes;
            s.progress("Comprobando las copias guardadas");
            record.put("state", "copied_synced_readback_verified").put("bytes", bytes)
                    .put("sha256", originalHash).put("relative_path", s.relative(target))
                    .put("declared_size_zero_with_content", isDt && opened.st_size == 0 && bytes > 0);
        } catch (LimitedException e) {
            s.copyLimited++;
            record.put("state", "copy_limited").put("bytes_read", bytes).put("message", e.getMessage());
        } finally {
            if (in != null) try { in.close(); } catch (IOException e) { s.errors++; }
            if (out != null) try { out.close(); } catch (IOException e) { s.errors++; }
            if (!verified && created != null) {
                try {
                    s.requireDestination(target);
                    if (!sameFile(created, Os.lstat(target.getPath()))) throw new IOException("Partial destination identity changed");
                    Os.remove(target.getPath());
                    syncDirectory(target.getParentFile());
                    record.put("partial_removed", true);
                } catch (Exception cleanup) {
                    s.errors++;
                    record.put("partial_removed", false).put("partial_path", s.relative(target))
                            .put("cleanup_error", brief(cleanup));
                }
            }
            record.put("elapsed_ms", SystemClock.elapsedRealtime() - started);
        }
    }

    private static boolean wantedDirectory(String path) {
        String p = path.toLowerCase(Locale.US);
        if (p.equals("lib") || p.startsWith("lib/") || p.equals("lib64") || p.startsWith("lib64/")) return true;
        if (p.equals("firmware") || p.startsWith("firmware/")) return true;
        if (p.equals("usr/keylayout") || p.startsWith("usr/keylayout/") || p.equals("usr/keychars") || p.startsWith("usr/keychars/")) return true;
        if (p.equals("etc")) return true;
        String[] dirs = {"etc/firmware", "etc/init", "etc/vintf", "etc/permissions", "etc/egl", "etc/vulkan", "etc/audio", "etc/media", "etc/display", "etc/modules"};
        for (String dir : dirs) if (p.equals(dir) || p.startsWith(dir + "/")) return true;
        return false;
    }

    private static boolean wantedFile(String path) {
        String p = path.toLowerCase(Locale.US);
        String name = p.substring(p.lastIndexOf('/') + 1);
        if (p.startsWith("firmware/") || p.startsWith("etc/firmware/"))
            return ends(name, ".bin", ".fw", ".hcd", ".ucode", ".dat", ".img", ".hex", ".elf", ".mbn");
        if (name.endsWith(".ko") || name.endsWith(".ko.xz") || name.endsWith(".ko.gz")) return true;
        if (p.contains("/modules/") && name.startsWith("modules.")) return true;
        if (p.startsWith("usr/keylayout/")) return name.endsWith(".kl");
        if (p.startsWith("usr/keychars/")) return name.endsWith(".kcm");
        if (p.startsWith("etc/init/")) return name.endsWith(".rc");
        if (p.startsWith("etc/vintf/") || p.startsWith("etc/permissions/")) return name.endsWith(".xml");
        if (p.startsWith("etc/")) {
            boolean configName = name.startsWith("media") || name.startsWith("audio") || name.startsWith("mixer")
                    || name.startsWith("codec") || name.startsWith("display") || name.startsWith("ueventd")
                    || name.equals("manifest.xml") || name.startsWith("compatibility_matrix") || name.startsWith("fstab");
            boolean configDirectory = p.startsWith("etc/audio/") || p.startsWith("etc/media/")
                    || p.startsWith("etc/display/") || p.startsWith("etc/egl/") || p.startsWith("etc/vulkan/");
            return (configName || configDirectory) && ends(name, ".xml", ".conf", ".cfg", ".rc", ".json", ".txt");
        }
        if (!(p.startsWith("lib/") || p.startsWith("lib64/")) || !name.endsWith(".so")) return false;
        if (p.contains("/hw/") || p.contains("/egl/")) return true;
        String[] prefixes = {"libegl", "libgles", "libvulkan", "libopencl", "libmali", "libmedia", "libstagefright",
                "libomx", "libcodec", "libamcodec", "libamplayer", "libamvideo", "libav", "libffmpeg", "libvdec", "libvenc",
                "libion", "libui", "libgui", "libnativewindow", "libsync", "libhardware", "libaudio", "libgralloc",
                "libhwcomposer", "libjpeg", "libyuv", "libpng", "libvpx", "libwebm", "libvp9", "libh264", "libhevc",
                "libvpu", "librockchip", "librk", "libpv", "android.hardware.graphics.", "android.hardware.media.", "android.hardware.audio."};
        for (String prefix : prefixes) if (name.startsWith(prefix)) return true;
        return false;
    }

    private static boolean sensitive(String path, boolean dt) {
        String p = path.toLowerCase(Locale.US);
        String[] segments = p.split("/");
        for (String n : segments) {
            if (n.equals("data") || n.equals("persist") || n.equals("metadata") || n.equals("private") || n.equals("accounts")
                    || n.equals("security") || n.equals("cacerts") || n.equals("certs") || n.equals("keys")
                    || n.contains("keystore") || n.contains("credential") || n.contains("password") || n.contains("secret")
                    || n.contains("wpa_supplicant") || n.contains("hostapd") || n.contains("wificonfigstore")
                    || n.contains("wifi_config") || n.contains("wifi_network") || n.contains("bt_config")
                    || n.contains("nvram") || n.contains("calibration") || n.contains("eeprom") || n.contains("efuse")
                    || n.contains("widevine") || n.contains("oemcrypto") || n.contains("hdcp") || n.contains("keymaster")
                    || n.contains("gatekeeper") || n.contains("provision") || n.endsWith(".pem") || n.endsWith(".key")
                    || n.endsWith(".p12") || n.endsWith(".pfx") || n.endsWith(".crt") || n.endsWith(".jks")
                    || n.endsWith(".der") || n.endsWith(".cer") || n.endsWith(".p7b") || n.endsWith(".p8")) return true;
            if (dt && (n.equals("chosen") || n.startsWith("chosen@") || n.contains("serial-number")
                    || n.contains("mac-address") || n.contains("macaddr") || n.contains("unifykey")
                    || n.equals("key") || n.equals("otp") || n.startsWith("otp@"))) return true;
        }
        return false;
    }

    private static boolean ends(String name, String... suffixes) {
        for (String suffix : suffixes) if (name.endsWith(suffix)) return true;
        return false;
    }

    private static boolean safeSegment(String value) {
        return value.length() > 0 && !value.equals(".") && !value.equals("..") && value.indexOf('/') < 0
                && value.indexOf('\\') < 0 && value.indexOf(':') < 0 && value.indexOf('\0') < 0
                && value.indexOf('\n') < 0 && value.indexOf('\r') < 0;
    }

    private static boolean safeRelative(String value) {
        if (value.length() == 0) return true;
        for (String part : value.split("/", -1)) if (!safeSegment(part)) return false;
        return true;
    }

    private static String portableRelative(String relative) throws Exception {
        if (relative.length() == 0 || !safeRelative(relative)) throw new IOException("Unsafe source-relative path");
        StringBuilder mapped = new StringBuilder();
        for (String segment : relative.split("/", -1)) {
            if (mapped.length() > 0) mapped.append('/');
            StringBuilder prefix = new StringBuilder("f_");
            for (int i = 0; i < segment.length() && prefix.length() < 40; i++) {
                char c = segment.charAt(i);
                if (c >= 'A' && c <= 'Z') c = (char)(c + ('a' - 'A'));
                prefix.append((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-' || c == '_' ? c : '_');
            }
            String suffix = hex(MessageDigest.getInstance("SHA-256").digest(segment.getBytes(UTF8))).substring(0, 16);
            mapped.append(prefix).append("__").append(suffix);
        }
        return mapped.toString();
    }

    private static void requireSourcePath(File path) throws Exception {
        String absolute = path.getAbsolutePath();
        boolean allowed = false;
        for (String root : ROOTS) if (absolute.equals(root) || absolute.startsWith(root + "/")) allowed = true;
        if (absolute.equals("/sys/firmware/devicetree/base") || absolute.startsWith("/sys/firmware/devicetree/base/")) allowed = true;
        if (absolute.equals("/proc/device-tree") || absolute.startsWith("/proc/device-tree/")) allowed = true;
        if (!allowed || !safeRelative(absolute.substring(1))) throw new IOException("Source outside permitted roots");
        File node = path;
        while (node != null && !node.getPath().equals("/")) {
            StructStat st = Os.lstat(node.getPath());
            if (OsConstants.S_ISLNK(st.st_mode)) throw new SymlinkException();
            if (!node.equals(path) && !OsConstants.S_ISDIR(st.st_mode)) throw new IOException("Source ancestor is not a directory");
            node = node.getParentFile();
        }
        if (!path.getCanonicalPath().equals(absolute)) throw new IOException("Source canonical path differs");
    }

    private static boolean sameFile(StructStat a, StructStat b) {
        return a.st_dev == b.st_dev && a.st_ino == b.st_ino && (a.st_mode & OsConstants.S_IFMT) == (b.st_mode & OsConstants.S_IFMT);
    }

    private static void syncDirectory(File directory) throws Exception {
        StructStat before = Os.lstat(directory.getPath());
        if (!OsConstants.S_ISDIR(before.st_mode)) throw new IOException("Sync target is not a real directory");
        FileDescriptor fd = Os.open(directory.getPath(), OsConstants.O_RDONLY | OsConstants.O_NONBLOCK
                | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0);
        try {
            if (!sameFile(before, Os.fstat(fd))) throw new IOException("Sync directory changed");
            Os.fsync(fd);
        } finally { Os.close(fd); }
    }

    private static Digest digestTarget(State s, File target, StructStat expected, long expectedBytes) throws Exception {
        s.requireDestination(target);
        FileDescriptor fd = Os.open(target.getPath(), OsConstants.O_RDONLY | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0);
        FileInputStream in = new FileInputStream(fd);
        try {
            StructStat before = Os.fstat(fd);
            if (!sameFile(expected, before) || !OsConstants.S_ISREG(before.st_mode) || before.st_size != expectedBytes)
                throw new IOException("Destination identity/length differs");
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            long bytes = 0;
            byte[] buffer = new byte[65536];
            int count;
            while ((count = in.read(buffer)) != -1) {
                bytes += count;
                if (bytes > expectedBytes) throw new IOException("Destination grew during verification");
                hash.update(buffer, 0, count);
                s.readbackBytes += count;
                s.progress("Releyendo copias para comprobarlas");
            }
            StructStat after = Os.fstat(fd);
            if (!sameFile(before, after) || before.st_size != after.st_size || before.st_mtime != after.st_mtime
                    || before.st_ctime != after.st_ctime) throw new IOException("Destination changed during verification");
            s.requireDestination(target);
            if (!sameFile(before, Os.lstat(target.getPath()))) throw new IOException("Destination path changed");
            return new Digest(bytes, hex(hash.digest()));
        } finally { in.close(); }
    }

    private static JSONObject row(File source, boolean dt) throws Exception {
        return new JSONObject().put("source", source.getPath()).put("scope", dt ? "device_tree" : "static_platform_file");
    }

    private static void recordError(State s, JSONObject row, Exception e) throws Exception {
        String status = "error";
        if (e instanceof SymlinkException) { status = "omitted_symlink"; s.omitted++; }
        else if (e instanceof ErrnoException && (((ErrnoException)e).errno == OsConstants.EACCES || ((ErrnoException)e).errno == OsConstants.EPERM)) {
            status = "denied"; s.denied++;
        } else if (e instanceof ErrnoException && ((ErrnoException)e).errno == OsConstants.ENOENT) {
            status = "unavailable"; s.unavailable++;
        } else { s.errors++; }
        row.put("state", status).put("error", brief(e));
        if (e instanceof ErrnoException) row.put("errno", ((ErrnoException)e).errno);
    }

    private static String brief(Exception error) {
        String message = error.getClass().getSimpleName() + ": " + String.valueOf(error.getMessage());
        return message.length() <= 240 ? message : message.substring(0, 240);
    }

    private static String hex(byte[] bytes) {
        char[] chars = "0123456789abcdef".toCharArray();
        char[] output = new char[bytes.length * 2];
        for (int i = 0; i < bytes.length; i++) { output[2 * i] = chars[(bytes[i] >>> 4) & 15]; output[2 * i + 1] = chars[bytes[i] & 15]; }
        return new String(output);
    }

    private static final class State {
        final File session;
        final HardwareCollector.Progress callback;
        final long started = SystemClock.elapsedRealtime();
        final long readLimit;
        int entries, directories, copied, omitted, denied, unavailable, errors, copyLimited;
        long readBytes, copiedBytes, dtReadBytes, dtCopiedBytes;
        long readbackBytes, lastProgress;
        String stopReason;
        State(File session, HardwareCollector.Progress callback) {
            this.session = session;
            this.callback = callback;
            readLimit = Math.min(TOTAL_LIMIT, Math.max(0L, session.getUsableSpace() - 128L * 1024L * 1024L) / 3L);
        }
        void progress(String phase) {
            long now = SystemClock.elapsedRealtime();
            if (callback == null || now - lastProgress < 1500L) return;
            lastProgress = now;
            callback.update(phase + "…\nArchivos y carpetas revisados: " + entries
                    + " · Leídos: " + (readBytes / 1048576L) + " MB"
                    + "\nCopias verificadas: " + copied + " (" + (copiedBytes / 1048576L)
                    + " MB) · Releídos: " + (readbackBytes / 1048576L) + " MB");
        }
        boolean timeOrCancelled() {
            if (Thread.currentThread().isInterrupted()) stopReason = "cancelled";
            else if (SystemClock.elapsedRealtime() - started >= TIME_LIMIT_MS) stopReason = "time_limit";
            return "cancelled".equals(stopReason) || "time_limit".equals(stopReason);
        }
        boolean stopped() {
            if (stopReason != null) return true;
            if (!timeOrCancelled() && readBytes >= readLimit) stopReason = "source_byte_limit";
            return stopReason != null;
        }
        String relative(File target) throws Exception {
            String absolute = target.getAbsolutePath();
            String prefix = session.getPath() + "/";
            if (!absolute.startsWith(prefix)) throw new IOException("Destination outside session");
            return absolute.substring(prefix.length());
        }
        void requireDestination(File target) throws Exception {
            String rel = relative(target);
            if (!safeRelative(rel) || !(rel.startsWith("drivers/") || rel.startsWith("details/dt/")))
                throw new IOException("Destination outside collector directories");
            File node = target.getParentFile();
            while (!node.equals(session)) {
                StructStat st = Os.lstat(node.getPath());
                if (!OsConstants.S_ISDIR(st.st_mode) || OsConstants.S_ISLNK(st.st_mode)) throw new IOException("Unsafe destination ancestor");
                node = node.getParentFile();
                if (node == null) throw new IOException("Destination escaped session");
            }
            if (!target.getParentFile().getCanonicalPath().equals(target.getParentFile().getAbsolutePath()))
                throw new IOException("Destination parent redirected");
        }
        void makeDirectories(File target) throws Exception {
            if (target.equals(session)) return;
            String rel = relative(target);
            if (!safeRelative(rel) || !(rel.equals("drivers") || rel.startsWith("drivers/") || rel.equals("details") || rel.equals("details/dt") || rel.startsWith("details/dt/")))
                throw new IOException("Unsafe directory destination");
            makeDirectories(target.getParentFile());
            try {
                StructStat st = Os.lstat(target.getPath());
                if (!OsConstants.S_ISDIR(st.st_mode) || OsConstants.S_ISLNK(st.st_mode)) throw new IOException("Destination directory occupied");
            } catch (ErrnoException e) {
                if (e.errno != OsConstants.ENOENT) throw e;
                Os.mkdir(target.getPath(), 0700);
                syncDirectory(target);
                syncDirectory(target.getParentFile());
            }
        }
    }

    private static final class Index {
        final State state;
        final File file;
        final FileOutputStream stream;
        final StructStat identity;
        final MessageDigest hash = MessageDigest.getInstance("SHA-256");
        long bytes;
        int rows;
        boolean closed;
        Index(State state, File file) throws Exception {
            this.state = state;
            this.file = file;
            state.requireDestination(file);
            FileDescriptor fd = Os.open(file.getPath(), OsConstants.O_WRONLY | OsConstants.O_CREAT | OsConstants.O_EXCL
                    | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0600);
            stream = new FileOutputStream(fd);
            identity = Os.fstat(fd);
        }
        void add(JSONObject row) throws Exception {
            byte[] data = (row.toString() + "\n").getBytes(UTF8);
            stream.write(data); hash.update(data); bytes += data.length; rows++;
        }
        JSONObject finish() throws Exception {
            stream.flush(); stream.getFD().sync(); stream.close(); closed = true;
            String expected = hex(hash.digest());
            Digest actual = digestTarget(state, file, identity, bytes);
            if (!expected.equals(actual.sha) || actual.bytes != bytes) throw new IOException("Inventory readback differs");
            syncDirectory(file.getParentFile());
            return new JSONObject().put("relative_path", state.relative(file)).put("bytes", bytes)
                    .put("rows", rows).put("sha256", expected).put("state", "synced_readback_verified");
        }
        void abort() { if (!closed) { try { stream.close(); } catch (IOException ignored) { } closed = true; } }
    }

    private static final class Digest {
        final long bytes;
        final String sha;
        Digest(long bytes, String sha) { this.bytes = bytes; this.sha = sha; }
    }
    private static final class LimitedException extends IOException {
        private static final long serialVersionUID = 1L;
        LimitedException(String text) { super(text); }
    }
    private static final class SymlinkException extends IOException {
        private static final long serialVersionUID = 1L;
        SymlinkException() { super("Symlink is outside collection policy"); }
    }
}
