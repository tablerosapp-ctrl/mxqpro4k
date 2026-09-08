package com.tvbase.reconocimiento;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.nio.charset.CodingErrorAction;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.json.JSONArray;
import org.json.JSONObject;

/** Read-only marked-storage discovery. No Android API, file writer or callbacks. */
public final class UsbLocator {
    public static final String FOLDER = "TVBASE-RECONOCIMIENTO";
    public static final String MARKER = "MEDIA.json";
    public static final String SCHEMA = "tvbase-recognition-media-1";
    public static final String MEDIA_ID = "tvbase-recognition-kingston-20260908-c73d9a14";
    public static final int MAX_DEPTH = 3, MAX_DIRECTORIES = 128, MAX_ENTRIES = 64,
        MAX_DIRECTORY_ARRAY = 4096, MAX_DIAGNOSTICS = 128, MAX_CANDIDATES = 16,
        MAX_SEEDS = 96, MAX_PATH = 1024, MARKER_BYTES = 4096, MOUNT_BYTES = 262144;
    private static final Object WORKER_LOCK = new Object();
    private static Thread discoveryWorker;
    private static final Charset UTF8 = Charset.forName("UTF-8");
    private UsbLocator() { }

    /** Methods must only inspect/read and are called exclusively by the worker. */
    public interface Probe {
        Node stat(String path) throws Exception;
        String[] list(String path) throws Exception;
        byte[] read(String path, int maxBytes) throws Exception;
    }
    /** Optional device/inode must come from the filesystem (e.g. Android Os.stat). */
    public static final class Node {
        public final boolean directory, regular;
        public final String canonical;
        public final Long device, inode;
        public Node(boolean directory, boolean regular, String canonical, Long device, Long inode) {
            this.directory = directory; this.regular = regular; this.canonical = canonical;
            boolean known = identity(device, inode);
            this.device = known ? device : null; this.inode = known ? inode : null;
        }
    }
    /** Portable fallback; callers can override stat to supply proven dev/inode. */
    public static class FileProbe implements Probe {
        public Node stat(String path) throws Exception {
            File file = new File(path);
            if (!file.exists()) return null;
            return new Node(file.isDirectory(), file.isFile(), file.getCanonicalPath(), null, null);
        }
        public String[] list(String path) { return new File(path).list(); }
        public byte[] read(String path, int maxBytes) throws Exception {
            InputStream input = new FileInputStream(path);
            try { return readLimited(input, maxBytes); }
            finally { input.close(); }
        }
    }
    public static final class Diagnostic {
        public final String path, state, detail;
        Diagnostic(String path, String state, String detail) {
            this.path = clip(path, MAX_PATH); this.state = state; this.detail = clip(detail, 512);
        }
        JSONObject toJson() throws Exception {
            return new JSONObject().put("path", path).put("state", state).put("detail", detail);
        }
    }
    public static final class Candidate {
        public final String root, folder, canonical;
        /** Alternative marked-folder paths, never grouped by the marker bytes. */
        public final List<String> aliases;
        public final Long device, inode;
        Candidate(Group group) {
            root = group.root; folder = group.folder; canonical = group.canonical;
            device = group.device; inode = group.inode;
            aliases = Collections.unmodifiableList(new ArrayList<String>(group.aliases));
        }
        public JSONObject toJson() throws Exception {
            return new JSONObject().put("root", root).put("folder", folder).put("canonical", canonical)
                .put("aliases", new JSONArray(aliases)).put("device", device == null ? JSONObject.NULL : device)
                .put("inode", inode == null ? JSONObject.NULL : inode)
                .put("identity_scope", device != null && inode != null ? "filesystem_dev_inode" : "exact_canonical_path")
                .put("marker_verified", true).put("write_access_tested", false);
        }
    }
    public static final class Result {
        public final List<Candidate> candidates;
        public final List<Diagnostic> diagnostics;
        public final boolean timedOut, pendingWorker, limited;
        public final int visitedDirectories;
        public final String state;
        Result(State scan, boolean timedOut, String state) {
            synchronized (scan) {
                ArrayList<Candidate> copy = new ArrayList<Candidate>();
                for (Group group : scan.groups) copy.add(new Candidate(group));
                candidates = Collections.unmodifiableList(copy);
                diagnostics = Collections.unmodifiableList(new ArrayList<Diagnostic>(scan.diagnostics));
                limited = scan.limited; visitedDirectories = scan.visited;
            }
            this.timedOut = timedOut; this.pendingWorker = hasPendingDiscovery(); this.state = state;
        }
        public JSONObject toJson() throws Exception {
            JSONArray found = new JSONArray(), observations = new JSONArray();
            for (Candidate candidate : candidates) found.put(candidate.toJson());
            for (Diagnostic diagnostic : diagnostics) observations.put(diagnostic.toJson());
            return new JSONObject().put("schema", "tvbase-usb-locator-1").put("state", state)
                .put("candidates", found).put("diagnostics", observations).put("timed_out", timedOut)
                .put("pending_worker", pendingWorker).put("limited", limited).put("visited_directories", visitedDirectories)
                .put("maximum_depth", MAX_DEPTH).put("maximum_directories", MAX_DIRECTORIES)
                .put("writes_performed", false).put("automatic_selection_performed", false)
                .put("limit", "A matching marker identifies prepared storage, not independently proven physical USB hardware or write permission. Timeout does not kill a blocked filesystem call; its single worker remains reserved until actual exit. Returned directory arrays are capped before processing, but filesystem enumeration can allocate or block before returning.");
        }
    }
    public static boolean hasPendingDiscovery() {
        synchronized (WORKER_LOCK) { return discoveryWorker != null; }
    }
    /** Separate single-worker gate; hardware observation timeouts do not occupy it. */
    public static Result discover(final Probe probe, List<String> volumePaths, Map<String, String> environment, long timeoutMs) throws Exception {
        if (probe == null || timeoutMs < 1 || timeoutMs > 30000) throw new IllegalArgumentException("Invalid discovery options");
        final State scan = new State(probe, timeoutMs);
        // Copy caller collections before scheduling; later results never mutate a
        // returned snapshot, and the worker never receives a report/session writer.
        if (volumePaths != null) {
            if (volumePaths.size() > MAX_SEEDS) scan.limit("volume_paths", "supplied volume count exceeds seed limit");
            for (int i = 0; i < volumePaths.size() && i < MAX_SEEDS; i++) scan.supplied.add(volumePaths.get(i));
        }
        if (environment != null) for (String key : new String[]{"EXTERNAL_STORAGE", "SECONDARY_STORAGE"}) {
            String value = environment.get(key);
            if (value != null) {
                if (value.length() > 16384) { scan.limit(key, "environment path text exceeds limit"); continue; }
                for (String path : value.split(":")) {
                    if (scan.supplied.size() >= MAX_SEEDS) { scan.limit(key, "environment seed count limit reached"); break; }
                    scan.supplied.add(path);
                }
            }
        }
        final FutureTask<Void> task = new FutureTask<Void>(new Callable<Void>() {
            public Void call() {
                try { scan.scan(); }
                catch (Exception error) { scan.diag("discovery", "stopped", error.getClass().getSimpleName()); }
                return null;
            }
        });
        Thread worker = new Thread(new Runnable() {
            public void run() {
                try { task.run(); }
                finally { synchronized (WORKER_LOCK) { if (discoveryWorker == Thread.currentThread()) discoveryWorker = null; } }
            }
        }, "tvbase-usb-discovery");
        worker.setDaemon(true);
        synchronized (WORKER_LOCK) {
            if (discoveryWorker != null) {
                scan.diag("discovery", "skipped_pending_discovery", "No new worker or filesystem read was started");
                return new Result(scan, false, "skipped_pending_discovery");
            }
            discoveryWorker = worker;
            try { worker.start(); }
            catch (Throwable error) { discoveryWorker = null; throw error; }
        }
        boolean timeout = false;
        String state = "finished";
        try { task.get(timeoutMs, TimeUnit.MILLISECONDS); }
        catch (TimeoutException error) {
            task.cancel(true); timeout = true; state = "timed_out";
            scan.diag("discovery", "timeout", "Client stopped waiting; native filesystem work may continue without writers");
        } catch (InterruptedException error) {
            task.cancel(true); Thread.currentThread().interrupt(); throw error;
        } finally { if (task.isDone() && !task.isCancelled()) worker.join(50); }
        return new Result(scan, timeout, state);
    }

    private static final class Group {
        final String root, folder, canonical;
        Long device, inode;
        final ArrayList<String> aliases = new ArrayList<String>();
        Group(String root, String folder, Node node) {
            this.root = root; this.folder = folder; canonical = node.canonical;
            device = node.device; inode = node.inode; aliases.add(folder);
        }
    }
    private static final class State {
        final Probe probe;
        final long deadline;
        final ArrayList<String> supplied = new ArrayList<String>();
        final LinkedHashSet<String> seeds = new LinkedHashSet<String>();
        final LinkedHashSet<String> visitedPaths = new LinkedHashSet<String>();
        final ArrayList<Group> groups = new ArrayList<Group>();
        final ArrayList<Diagnostic> diagnostics = new ArrayList<Diagnostic>();
        boolean limited;
        int visited;
        State(Probe probe, long timeoutMs) { this.probe = probe; deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(timeoutMs); }
        synchronized void diag(String path, String state, String detail) {
            if (diagnostics.size() < MAX_DIAGNOSTICS) diagnostics.add(new Diagnostic(path, state, detail));
            else limited = true;
        }
        synchronized void limit(String path, String detail) { limited = true; diag(path, "limited", detail); }
        boolean room() throws InterruptedException {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedException("Discovery interrupted");
            if (System.nanoTime() >= deadline) { limit("discovery", "cooperative deadline reached"); return false; }
            synchronized (this) { if (visited >= MAX_DIRECTORIES) { limit("discovery", "directory count limit reached"); return false; } }
            return true;
        }
        void seed(String path, String source) {
            String normalized = normalize(path);
            if (normalized == null || !allowed(normalized) || depth(normalized) > MAX_DEPTH) {
                diag(source, "path_excluded", clip(path, MAX_PATH)); return;
            }
            if (seeds.size() >= MAX_SEEDS && !seeds.contains(normalized)) { limit(source, "seed count limit reached"); return; }
            seeds.add(normalized);
        }
        void scan() throws Exception {
            for (String fixed : new String[]{"/storage", "/mnt/media_rw", "/mnt/usb_storage", "/mnt/usbhost0", "/mnt/usbhost1", "/mnt/usb0", "/mnt/usb1", "/mnt/usb", "/udisk"}) seed(fixed, "known_root");
            for (String path : supplied) seed(path, "volume_or_environment");
            // /mnt is listed once solely to discover usb* root names. Other
            // children are never inspected or traversed.
            String[] mnt = list("/mnt");
            if (mnt != null) for (String name : mnt) if (name.matches("usb[A-Za-z0-9_.-]{0,64}")) seed("/mnt/" + name, "mnt_usb_root");
            readMounts("/proc/self/mountinfo", true);
            readMounts("/proc/mounts", false);
            ArrayDeque<String> pending = new ArrayDeque<String>(seeds);
            while (!pending.isEmpty() && room()) {
                String root = pending.removeFirst();
                if (!visitedPaths.add(root)) continue;
                synchronized (this) { visited++; }
                Node rootNode = stat(root);
                if (rootNode == null || !rootNode.directory) continue;
                String canonical = normalize(rootNode.canonical);
                if (canonical == null || !allowed(canonical) || depth(canonical) > MAX_DEPTH) {
                    diag(root, "canonical_excluded", rootNode.canonical); continue;
                }
                if (marker(root)) continue;
                if (depth(root) >= MAX_DEPTH) continue;
                String[] children = list(root);
                if (children == null) continue;
                for (String name : children) {
                    if (!component(name) || forbidden(name) || name.equals(FOLDER)) continue;
                    // At the two volume carrier roots every child may name a
                    // volume. Below them only known OEM mount containers are
                    // considered; arbitrary user directories are never walked.
                    if (!(root.equals("/storage") || root.equals("/mnt/media_rw") || container(name))) continue;
                    String child = root + "/" + name;
                    if (allowed(child) && depth(child) <= MAX_DEPTH && !visitedPaths.contains(child)) {
                        if (pending.size() < MAX_DIRECTORIES) pending.addLast(child);
                        else limit(root, "pending directory count limit reached");
                    }
                }
            }
        }
        void readMounts(String path, boolean mountInfo) throws Exception {
            if (!room()) return;
            try {
                byte[] bytes = probe.read(path, MOUNT_BYTES);
                if (bytes.length > MOUNT_BYTES) { limit(path, "mount text byte limit reached; input ignored"); return; }
                String text = new String(bytes, UTF8);
                if (text.split("\\n", 1025).length > 1024) limit(path, "mount line limit reached; later lines are not processed");
                List<String> mountpoints = mountInfo ? parseMountInfo(text) : parseMounts(text);
                for (String point : mountpoints) seed(point, path);
            } catch (InterruptedException error) { throw error; }
            catch (Exception error) { diag(path, "unavailable", error.getClass().getSimpleName()); }
        }
        Node stat(String path) throws Exception {
            if (!room()) return null;
            try { return probe.stat(path); }
            catch (InterruptedException error) { throw error; }
            catch (Exception error) { diag(path, "unavailable", error.getClass().getSimpleName()); return null; }
        }
        String[] list(String path) throws Exception {
            if (!room()) return null;
            try {
                String[] values = probe.list(path);
                if (values == null) { diag(path, "unavailable", "Directory absent or access denied"); return null; }
                if (values.length > MAX_DIRECTORY_ARRAY) { limit(path, "directory array exceeds processing cap; not traversed"); return null; }
                values = values.clone(); Arrays.sort(values);
                if (values.length > MAX_ENTRIES) { limit(path, "directory entry selection cap reached"); values = Arrays.copyOf(values, MAX_ENTRIES); }
                return values;
            } catch (InterruptedException error) { throw error; }
            catch (Exception error) { diag(path, "unavailable", error.getClass().getSimpleName()); return null; }
        }
        boolean marker(String root) throws Exception {
            String folder = root + "/" + FOLDER;
            Node directory = stat(folder);
            if (directory == null || !directory.directory) return false;
            String expectedCanonical = normalize(directory.canonical);
            String parentCanonical = expectedCanonical != null && expectedCanonical.endsWith("/" + FOLDER)
                ? expectedCanonical.substring(0, expectedCanonical.length() - FOLDER.length() - 1) : null;
            if (expectedCanonical == null || !expectedCanonical.endsWith("/" + FOLDER)
                    || !allowed(parentCanonical) || depth(parentCanonical) > MAX_DEPTH) {
                diag(folder, "marker_folder_excluded", "Canonical marked folder escaped permitted roots"); return false;
            }
            String marker = folder + "/" + MARKER;
            Node file = stat(marker);
            if (file == null || !file.regular) { diag(marker, "marker_unavailable", "Marker is absent, denied or not a regular file"); return false; }
            if (!(expectedCanonical + "/" + MARKER).equals(normalize(file.canonical))) {
                diag(marker, "marker_excluded", "Marker canonical path differs from its marked folder"); return false;
            }
            if (!room()) return false;
            try {
                byte[] bytes = probe.read(marker, MARKER_BYTES);
                if (!validMarker(bytes)) { diag(marker, "marker_rejected", "Schema, ID or strict marker JSON differs"); return false; }
                // Recheck the folder after reading; a changed identity cannot
                // lend a valid marker to a different candidate directory.
                Node after = stat(folder);
                if (!sameNode(directory, after)) { diag(folder, "marker_changed", "Marked directory identity changed during read"); return false; }
                add(root, folder, directory); return true;
            } catch (InterruptedException error) { throw error; }
            catch (Exception error) { diag(marker, "marker_unavailable", error.getClass().getSimpleName()); return false; }
        }
        synchronized void add(String root, String folder, Node node) {
            for (Group group : groups) {
                boolean both = identity(group.device, group.inode) && identity(node.device, node.inode);
                boolean same = both ? group.device.equals(node.device) && group.inode.equals(node.inode) : group.canonical.equals(node.canonical);
                if (same) {
                    if (!group.aliases.contains(folder) && group.aliases.size() < MAX_SEEDS) group.aliases.add(folder);
                    if (!identity(group.device, group.inode) && identity(node.device, node.inode)) { group.device = node.device; group.inode = node.inode; }
                    return;
                }
            }
            if (groups.size() >= MAX_CANDIDATES) { limit(folder, "candidate count limit reached; no automatic choice permitted"); return; }
            groups.add(new Group(root, folder, node));
        }
    }

    private static boolean identity(Long device, Long inode) { return device != null && inode != null && inode.longValue() > 0; }
    private static boolean sameNode(Node before, Node after) {
        if (before == null || after == null || !after.directory || !before.canonical.equals(after.canonical)) return false;
        if (identity(before.device, before.inode) || identity(after.device, after.inode))
            return identity(before.device, before.inode) && identity(after.device, after.inode)
                && before.device.equals(after.device) && before.inode.equals(after.inode);
        return true;
    }
    private static String clip(String value, int max) { return value == null ? "" : value.length() <= max ? value : value.substring(0, max) + " [truncated]"; }
    private static boolean component(String name) {
        if (name == null || name.length() < 1 || name.length() > 128 || name.equals(".") || name.equals("..")) return false;
        for (int i = 0; i < name.length(); i++) if (name.charAt(i) < 32 || name.charAt(i) == 127 || name.charAt(i) == '/' || name.charAt(i) == '\\') return false;
        return true;
    }
    private static boolean forbidden(String name) {
        return name.equalsIgnoreCase("emulated") || name.equalsIgnoreCase("self") || name.equalsIgnoreCase("Android")
            || name.equalsIgnoreCase("obb") || name.equalsIgnoreCase("data");
    }
    private static String normalize(String value) {
        if (value == null || value.length() < 2 || value.length() > MAX_PATH || !value.startsWith("/") || value.indexOf('\\') >= 0) return null;
        while (value.endsWith("/")) value = value.substring(0, value.length() - 1);
        String[] parts = value.substring(1).split("/", -1);
        for (String part : parts) if (!component(part) || forbidden(part)) return null;
        return value;
    }
    private static String anchor(String path) {
        for (String root : new String[]{"/storage", "/mnt/media_rw", "/mnt/usb_storage", "/udisk"})
            if (path.equals(root) || path.startsWith(root + "/")) return root;
        String[] parts = path.split("/");
        if (parts.length >= 3 && parts[1].equals("mnt") && parts[2].matches("usb[A-Za-z0-9_.-]{0,64}")) return "/mnt/" + parts[2];
        return null;
    }
    private static boolean allowed(String path) { return normalize(path) != null && anchor(path) != null; }
    private static int depth(String path) {
        String root = anchor(path);
        if (root == null) return Integer.MAX_VALUE;
        return path.equals(root) ? 0 : path.substring(root.length() + 1).split("/").length;
    }
    private static boolean container(String name) {
        return name.matches("(?i)(USB_DISK[0-9]+|udisk[0-9]*|usbhost[0-9]*|usb_storage|usb[0-9]+|disk[0-9]+|partition[0-9]+)");
    }
    public static boolean validMarker(byte[] bytes) {
        if (bytes == null || bytes.length < 1 || bytes.length > MARKER_BYTES) return false;
        try {
            String text = UTF8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            String ws = "[ \\t\\r\\n]*";
            String schema = "\\\"schema\\\"" + ws + ":" + ws + "\\\"" + SCHEMA + "\\\"";
            String media = "\\\"media_id\\\"" + ws + ":" + ws + "\\\"" + MEDIA_ID + "\\\"";
            return text.matches("\\A" + ws + "\\{" + ws + "(?:" + schema + ws + "," + ws + media + "|" + media + ws + "," + ws + schema + ")" + ws + "\\}" + ws + "\\z");
        } catch (Exception error) { return false; }
    }
    private static String unescapeMount(String value) throws IOException {
        StringBuilder output = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c != '\\') { output.append(c); continue; }
            if (i + 3 >= value.length()) throw new IOException("Truncated mount escape");
            String code = value.substring(i + 1, i + 4);
            if (code.equals("040")) output.append(' ');
            else if (code.equals("011")) output.append('\t');
            else if (code.equals("012")) output.append('\n');
            else if (code.equals("134")) output.append('\\');
            else throw new IOException("Unsupported mount escape");
            i += 3;
        }
        return output.toString();
    }
    public static List<String> parseMountInfo(String text) { return parseMountText(text, true); }
    public static List<String> parseMounts(String text) { return parseMountText(text, false); }
    private static List<String> parseMountText(String text, boolean info) {
        ArrayList<String> values = new ArrayList<String>();
        if (text == null || text.length() > MOUNT_BYTES) return values;
        String[] lines = text.split("\\n", 1025);
        for (int i = 0; i < lines.length && i < 1024 && values.size() < MAX_SEEDS; i++) {
            String line = lines[i].trim();
            if (line.length() == 0 || line.length() > 4096) continue;
            String[] fields = line.split(" +");
            if ((info && (fields.length < 10 || line.indexOf(" - ") < 0)) || (!info && fields.length < 4)) continue;
            try {
                String path = normalize(unescapeMount(fields[info ? 4 : 1]));
                if (path != null && allowed(path) && depth(path) <= MAX_DEPTH && !values.contains(path)) values.add(path);
            } catch (IOException ignored) { }
        }
        return values;
    }
    static byte[] readLimited(InputStream input, int maxBytes) throws IOException {
        if (maxBytes < 1 || maxBytes > MOUNT_BYTES) throw new IOException("Invalid read bound");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096]; int empty = 0;
        while (out.size() <= maxBytes) {
            if (Thread.currentThread().isInterrupted()) throw new IOException("Discovery read interrupted");
            int count = input.read(buffer, 0, Math.min(buffer.length, maxBytes + 1 - out.size()));
            if (count < 0) break;
            if (count == 0) { if (++empty >= 3) throw new IOException("Discovery read made no progress"); continue; }
            empty = 0; out.write(buffer, 0, count);
        }
        return out.toByteArray();
    }
}
