package com.tvbase.reconocimiento;

import java.io.ByteArrayInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.json.JSONObject;

/** Virtual-filesystem fixtures: no physical storage or Android calls. */
public final class UsbLocatorHarness {
    private static final ArrayList<String> passed = new ArrayList<String>();
    private static final String VALID = "{\"schema\":\"" + UsbLocator.SCHEMA + "\",\"media_id\":\"" + UsbLocator.MEDIA_ID + "\"}\n";
    private static void require(boolean value, String reason) { if (!value) throw new AssertionError(reason); }
    private static class Fake implements UsbLocator.Probe {
        final Map<String, UsbLocator.Node> nodes = new LinkedHashMap<String, UsbLocator.Node>();
        final Map<String, String[]> listings = new HashMap<String, String[]>();
        final Map<String, byte[]> files = new HashMap<String, byte[]>();
        final List<String> calls = Collections.synchronizedList(new ArrayList<String>());
        Fake() { dir("/mnt"); dir("/storage"); dir("/mnt/media_rw"); }
        void dir(String path, String... children) {
            nodes.put(path, new UsbLocator.Node(true, false, path, null, null)); listings.put(path, children);
        }
        void marked(String root, long device, long inode) throws Exception { marked(root, root + "/" + UsbLocator.FOLDER, Long.valueOf(device), Long.valueOf(inode)); }
        void marked(String root, String canonical, Long device, Long inode) throws Exception {
            dir(root); String folder = root + "/" + UsbLocator.FOLDER, marker = folder + "/MEDIA.json";
            nodes.put(folder, new UsbLocator.Node(true, false, canonical, device, inode));
            nodes.put(marker, new UsbLocator.Node(false, true, canonical + "/MEDIA.json", device, inode == null ? null : Long.valueOf(inode.longValue() + 1)));
            files.put(marker, VALID.getBytes("UTF-8"));
        }
        public UsbLocator.Node stat(String path) throws Exception { calls.add("stat " + path); return nodes.get(path); }
        public String[] list(String path) throws Exception { calls.add("list " + path); return listings.get(path); }
        public byte[] read(String path, int maximum) throws Exception {
            calls.add("read " + path);
            byte[] value = files.get(path); if (value == null) throw new FileNotFoundException("fixture missing"); return value;
        }
    }
    private static UsbLocator.Result scan(Fake fake, String... paths) throws Exception {
        return UsbLocator.discover(fake, Arrays.asList(paths), Collections.<String, String>emptyMap(), 3000);
    }
    private static void nestedOemPath() throws Exception {
        Fake fake = new Fake();
        fake.dir("/mnt", "usb_storage", "data");
        fake.dir("/mnt/usb_storage", "USB_DISK0");
        fake.dir("/mnt/usb_storage/USB_DISK0", "udisk0");
        fake.marked("/mnt/usb_storage/USB_DISK0/udisk0", 71, 101);
        UsbLocator.Result result = scan(fake);
        require(!result.timedOut && result.candidates.size() == 1, "OEM nested marker not found");
        require(result.candidates.get(0).root.equals("/mnt/usb_storage/USB_DISK0/udisk0"), "wrong OEM root");
        require(result.candidates.get(0).folder.endsWith("/TVBASE-RECONOCIMIENTO"), "wrong marked folder");
        require(!fake.calls.contains("stat /mnt/data"), "unrelated /mnt directory was inspected");
        passed.add("nested_oem_path");
    }
    private static void mountParsersAndEnvironment() throws Exception {
        String info = "31 1 8:1 / /storage/USB\\040Drive rw,nosuid shared:1 - vfat /dev/block/sda1 rw\n"
            + "32 1 8:2 / /mnt/usbhost9 rw - vfat /dev/block/sdb1 rw\n"
            + "33 1 0:1 / /storage/emulated/0 rw - fuse /dev/fuse rw\n"
            + "broken mount line\n";
        List<String> paths = UsbLocator.parseMountInfo(info);
        require(paths.equals(Arrays.asList("/storage/USB Drive", "/mnt/usbhost9")), "mountinfo escape/filter failed");
        require(UsbLocator.parseMounts("/dev/sda /mnt/usb7 vfat rw 0 0\n/dev/a /data ext4 rw 0 0\n").equals(Arrays.asList("/mnt/usb7")), "mounts parsing failed");
        Fake fake = new Fake();
        fake.files.put("/proc/self/mountinfo", info.getBytes("UTF-8"));
        fake.marked("/storage/USB Drive", 7, 70);
        fake.marked("/mnt/usb3", 8, 80);
        Map<String, String> environment = new HashMap<String, String>();
        environment.put("SECONDARY_STORAGE", "/mnt/usb3:/storage/emulated/0");
        environment.put("EXTERNAL_STORAGE", "/data/secret");
        UsbLocator.Result result = UsbLocator.discover(fake, Collections.<String>emptyList(), environment, 3000);
        require(result.candidates.size() == 2, "mount/environment hints did not discover two volumes");
        require(!fake.calls.contains("stat /data/secret") && !fake.calls.contains("stat /storage/emulated/0"), "excluded environment path inspected");
        passed.add("mount_parsers_environment_and_spaces");
    }
    private static void storageVolumeHintAndUsbRootWildcard() throws Exception {
        Fake fake = new Fake(); fake.dir("/mnt", "usbhost42"); fake.marked("/mnt/usbhost42", 1, 11);
        fake.marked("/storage/VOLUME_HINT", 2, 22);
        UsbLocator.Result result = scan(fake, "/storage/VOLUME_HINT");
        require(result.candidates.size() == 2, "StorageVolume hint or usb* wildcard root missing");
        passed.add("volume_hint_and_usb_root_wildcard");
    }
    private static void twoVolumesSameMarkerStaySeparate() throws Exception {
        Fake fake = new Fake(); fake.marked("/storage/A", 1, 10); fake.marked("/storage/B", 2, 10);
        UsbLocator.Result result = scan(fake, "/storage/A", "/storage/B");
        require(result.candidates.size() == 2, "identical marker bytes merged distinct filesystem volumes");
        require(!result.toJson().getBoolean("automatic_selection_performed"), "locator chose a volume");
        passed.add("same_marker_different_volumes_not_merged");
    }
    private static void provenAliasesMerge() throws Exception {
        Fake fake = new Fake(); fake.marked("/storage/A", 9, 91); fake.marked("/mnt/media_rw/A", 9, 91);
        UsbLocator.Result result = scan(fake, "/storage/A", "/mnt/media_rw/A");
        require(result.candidates.size() == 1 && result.candidates.get(0).aliases.size() == 2, "dev/inode aliases did not merge");
        Fake canonical = new Fake();
        canonical.marked("/storage/A", "/mnt/media_rw/A/" + UsbLocator.FOLDER, null, null);
        canonical.marked("/mnt/media_rw/A", "/mnt/media_rw/A/" + UsbLocator.FOLDER, null, null);
        require(scan(canonical, "/storage/A", "/mnt/media_rw/A").candidates.size() == 1, "exact canonical fallback did not merge");
        Fake conflict = new Fake();
        conflict.marked("/storage/A", "/mnt/media_rw/A/" + UsbLocator.FOLDER, 1L, 10L);
        conflict.marked("/mnt/media_rw/A", "/mnt/media_rw/A/" + UsbLocator.FOLDER, 2L, 20L);
        require(scan(conflict, "/storage/A", "/mnt/media_rw/A").candidates.size() == 2, "conflicting known identities merged by canonical path");
        passed.add("dev_inode_and_canonical_alias_rules");
    }
    private static void markerValidation() throws Exception {
        require(UsbLocator.validMarker(VALID.getBytes("UTF-8")), "valid marker rejected");
        require(UsbLocator.validMarker((" { \"media_id\" : \"" + UsbLocator.MEDIA_ID + "\", \"schema\" : \"" + UsbLocator.SCHEMA + "\" } ").getBytes("UTF-8")), "reversed marker order rejected");
        for (String wrong : new String[]{VALID.replace(UsbLocator.MEDIA_ID, "other"), VALID + "{}",
                VALID.replace("}", ",\"media_id\":\"" + UsbLocator.MEDIA_ID + "\"}"), "[]", "null", "{}",
                VALID.replace("}", ",\"unexpected\":true}")})
            require(!UsbLocator.validMarker(wrong.getBytes("UTF-8")), "invalid marker accepted");
        require(!UsbLocator.validMarker(new byte[UsbLocator.MARKER_BYTES + 1]), "oversized marker accepted");
        require(!UsbLocator.validMarker(new byte[]{(byte) 0xff}), "invalid UTF-8 marker accepted");
        Fake fake = new Fake(); fake.marked("/storage/A", 1, 1);
        fake.files.put("/storage/A/" + UsbLocator.FOLDER + "/MEDIA.json", "{}".getBytes("UTF-8"));
        require(scan(fake, "/storage/A").candidates.isEmpty(), "wrong marker discovered");
        passed.add("strict_marker_schema_id_size_and_duplicates");
    }
    private static void noUserDataTraversal() throws Exception {
        Fake fake = new Fake();
        fake.dir("/storage", "emulated", "self", "A");
        fake.dir("/storage/A", "DCIM", "Downloads", "Android", "obb", "Documents", "usb0");
        fake.dir("/storage/A/usb0", "usb1"); fake.dir("/storage/A/usb0/usb1", "usb2");
        fake.marked("/storage/A/usb0/usb1/usb2", 2, 10);
        UsbLocator.Result result = scan(fake, "/storage/A/Android/data", "/storage/A/../B", "/data/media/0");
        require(result.candidates.isEmpty(), "depth-exceeding marker was reached");
        for (String call : fake.calls) {
            require(!call.contains("/DCIM") && !call.contains("/Downloads") && !call.contains("/Android")
                && !call.contains("/obb") && !call.contains("/Documents") && !call.contains("emulated")
                && !call.contains("/usb2") && !call.contains("/data/media"), "user/deep tree traversed: " + call);
        }
        passed.add("depth_three_and_no_user_data_tree");
    }
    private static void canonicalEscapeAndChangingFolder() throws Exception {
        Fake escape = new Fake(); escape.marked("/storage/A", 1, 1);
        escape.nodes.put("/storage/A", new UsbLocator.Node(true, false, "/data/media/0", null, null));
        require(scan(escape, "/storage/A").candidates.isEmpty(), "canonical escape accepted");
        Fake markerEscape = new Fake(); markerEscape.marked("/storage/A", 1, 1);
        String marker = "/storage/A/" + UsbLocator.FOLDER + "/MEDIA.json";
        markerEscape.nodes.put(marker, new UsbLocator.Node(false, true, "/storage/B/MEDIA.json", 1L, 2L));
        require(scan(markerEscape, "/storage/A").candidates.isEmpty(), "marker link escaped its marked folder");
        Fake changed = new Fake() {
            public byte[] read(String path, int maximum) throws Exception {
                byte[] data = super.read(path, maximum);
                if (path.endsWith("/MEDIA.json")) {
                    String folder = path.substring(0, path.length() - "/MEDIA.json".length());
                    nodes.put(folder, new UsbLocator.Node(true, false, folder, 99L, 999L));
                }
                return data;
            }
        };
        changed.marked("/storage/A", 1, 1);
        require(scan(changed, "/storage/A").candidates.isEmpty(), "changed folder identity borrowed a valid marker");
        passed.add("canonical_escape_and_identity_change_rejected");
    }
    private static void deniedAndLimits() throws Exception {
        Fake denied = new Fake() {
            public UsbLocator.Node stat(String path) throws Exception { throw new SecurityException("fixture denied"); }
        };
        UsbLocator.Result no = scan(denied);
        require(no.candidates.isEmpty() && !no.diagnostics.isEmpty(), "denial not reported");
        Fake large = new Fake(); large.listings.put("/storage", new String[UsbLocator.MAX_DIRECTORY_ARRAY + 1]);
        UsbLocator.Result limited = scan(large);
        require(limited.limited && limited.candidates.isEmpty(), "large directory was not bounded");
        Fake entries = new Fake(); String[] names = new String[80];
        for (int i = 0; i < names.length; i++) { names[i] = String.format("v%03d", i); entries.dir("/storage/" + names[i]); }
        entries.dir("/storage", names);
        UsbLocator.Result selected = scan(entries);
        require(selected.limited && selected.visitedDirectories <= UsbLocator.MAX_DIRECTORIES, "entry/directory caps not enforced");
        require(selected.diagnostics.size() <= UsbLocator.MAX_DIAGNOSTICS, "diagnostics grew past their cap");
        passed.add("denials_directory_arrays_entries_and_diagnostics_bounded");
    }
    private static void blockedDiscoveryDoesNotSpawnOrMutateSnapshot() throws Exception {
        final CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1);
        Fake blocked = new Fake() {
            public String[] list(String path) throws Exception {
                if (path.equals("/mnt")) {
                    entered.countDown();
                    for (;;) { try { release.await(); break; } catch (InterruptedException ignored) { } }
                }
                return super.list(path);
            }
        };
        blocked.marked("/storage/A", 1, 10);
        UsbLocator.Result early = UsbLocator.discover(blocked, Arrays.asList("/storage/A"), null, 30);
        require(entered.getCount() == 0 && early.timedOut && early.pendingWorker, "blocked discovery did not return a tracked timeout");
        String snapshot = early.toJson().toString();
        final AtomicInteger duplicateCalls = new AtomicInteger();
        Fake duplicate = new Fake() {
            public String[] list(String path) { duplicateCalls.incrementAndGet(); return null; }
        };
        for (int i = 0; i < 20; i++) require(UsbLocator.discover(duplicate, null, null, 30).state.equals("skipped_pending_discovery"), "second worker started");
        require(duplicateCalls.get() == 0, "pending calls reached filesystem");
        release.countDown();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
        while (UsbLocator.hasPendingDiscovery() && System.nanoTime() < deadline) Thread.sleep(1);
        require(!UsbLocator.hasPendingDiscovery(), "slot never released after true worker completion");
        require(snapshot.equals(early.toJson().toString()), "late worker changed previously returned result");
        require(scan(new Fake()).state.equals("finished"), "slot not reusable after completion");
        passed.add("timeout_retains_single_worker_and_snapshot_is_immutable");
    }
    private static void readCapsAndMalformedMounts() throws Exception {
        for (int count : new int[]{0, 1, 7, 8, 30}) require(UsbLocator.readLimited(new ByteArrayInputStream(new byte[count]), 7).length == Math.min(count, 8), "read cap sentinel differs");
        try {
            UsbLocator.readLimited(new InputStream() { public int read() { return 0; } public int read(byte[] b, int off, int len) { return 0; } }, 7);
            throw new AssertionError("zero progress accepted");
        } catch (IOException expected) { }
        require(UsbLocator.parseMountInfo("1 2 3:4 / /storage/A\\999 rw - vfat /dev/a rw\n").isEmpty(), "invalid mount escape accepted");
        require(UsbLocator.parseMounts("/dev/a /storage/A\\011B vfat rw 0 0\n").isEmpty(), "control-character mount path accepted");
        passed.add("bounded_reads_and_malformed_mounts");
    }
    public static void main(String[] arguments) throws Exception {
        nestedOemPath(); mountParsersAndEnvironment(); storageVolumeHintAndUsbRootWildcard();
        twoVolumesSameMarkerStaySeparate(); provenAliasesMerge(); markerValidation(); noUserDataTraversal();
        canonicalEscapeAndChangingFolder(); deniedAndLimits(); blockedDiscoveryDoesNotSpawnOrMutateSnapshot(); readCapsAndMalformedMounts();
        System.out.println(new JSONObject().put("state", "passed").put("cases", passed.size()).put("case_ids", passed)
            .put("scope", "host virtual filesystem and real Java worker gate; no Android, USB or device probe"));
    }
}
