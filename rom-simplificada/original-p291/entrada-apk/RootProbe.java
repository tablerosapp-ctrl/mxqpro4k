package local.tvbase.acceso;

import android.os.Build;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.ByteArrayOutputStream;
import java.io.FileDescriptor;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;

/** Temporary API28 app_process probe. No network, Binder services or block devices. */
public final class RootProbe {
    private static String phase = "arguments";

    public static void main(String[] args) {
        String nonce = "";
        try {
            nonce = ProbeContract.nonce(args);
            stage(nonce, "identity");
            if (Os.getuid() != 0) throw new IOException("Existing su did not return UID 0");
            if (Build.VERSION.SDK_INT != 28) throw new IOException("Expected API 28");
            String dt = ProbeContract.deviceTree(readLimited(
                    "/proc/device-tree/amlogic-dt-id", 128, false));
            String kernel = new String(readLimited("/proc/version", 8192, false),
                    StandardCharsets.UTF_8).trim();
            if (kernel.length() == 0) throw new IOException("Empty kernel description");
            emit("identity", nonce, "\"uid\":0,\"api\":28,\"dt\":" + quote(dt)
                    + ",\"build\":" + quote(Build.DISPLAY) + ",\"kernel\":" + quote(kernel));

            String directory = ProbeContract.directory(nonce);
            String file = directory + "/probe.bin";
            String passedFields;
            stage(nonce, "open_parent");
            FileDescriptor parent = openDirectory(ProbeContract.PARENT);
            try {
                // mkdir must fail on an existing path, including a symlink. No reuse.
                stage(nonce, "mkdir_exclusive");
                Os.mkdir(directory, 0700);
                stage(nonce, "fsync_parent");
                Os.fsync(parent);
                FileDescriptor dir = openDirectory(directory);
                try {
                    StructStat ds = Os.fstat(dir);
                    if (ds.st_uid != 0 || (ds.st_mode & 0777) != 0700)
                        throw new IOException("Unexpected owner or mode of new directory");
                    byte[] wanted = ProbeContract.payload(nonce);
                    stage(nonce, "create_file_exclusive");
                    FileDescriptor out = Os.open(file, OsConstants.O_WRONLY
                            | OsConstants.O_CREAT | OsConstants.O_EXCL
                            | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0600);
                    StructStat written;
                    try {
                        int offset = 0;
                        while (offset < wanted.length) {
                            int n = Os.write(out, wanted, offset, wanted.length - offset);
                            if (n <= 0) throw new IOException("Incomplete write");
                            offset += n;
                        }
                        stage(nonce, "fsync_file");
                        Os.fsync(out);
                        written = Os.fstat(out);
                        if (!OsConstants.S_ISREG(written.st_mode) || written.st_uid != 0
                                || (written.st_mode & 0777) != 0600
                                || written.st_size != wanted.length)
                            throw new IOException("Unexpected file metadata after write");
                    } finally {
                        Os.close(out);
                    }
                    stage(nonce, "fsync_directory");
                    Os.fsync(dir);
                    stage(nonce, "read_back");
                    byte[] observed = readLimited(file, wanted.length, true);
                    StructStat after = Os.lstat(file);
                    if (after.st_dev != written.st_dev || after.st_ino != written.st_ino
                            || after.st_size != written.st_size
                            || !Arrays.equals(wanted, observed))
                        throw new IOException("Read-back identity or content differs");
                    String digest = sha256(observed);
                    if (!digest.equals(sha256(wanted))) throw new IOException("SHA mismatch");
                    stage(nonce, "fsync_directory_final");
                    Os.fsync(dir);
                    passedFields = "\"uid\":0,\"api\":28,\"dt\":" + quote(dt)
                            + ",\"build\":" + quote(Build.DISPLAY)
                            + ",\"kernel\":" + quote(kernel)
                            + ",\"directory\":" + quote(directory)
                            + ",\"file\":" + quote(file)
                            + ",\"bytes\":" + wanted.length + ",\"sha256\":" + quote(digest)
                            + ",\"file_fsync\":true,\"directory_fsync\":true,\"parent_fsync\":true"
                            + ",\"bcb_accessed\":false,\"block_devices_accessed\":false"
                            + ",\"reset_requested\":false,\"temporary_files_preserved\":true";
                } finally {
                    Os.close(dir);
                }
            } finally {
                Os.close(parent);
            }
            emit("passed", nonce, passedFields);
        } catch (Throwable error) {
            emit("failed", nonce, "\"phase\":" + quote(phase)
                    + ",\"error\":" + quote(error.getClass().getSimpleName() + ": " + error.getMessage())
                    + ",\"automatic_retry\":false");
            System.exit(1);
        }
    }

    private static FileDescriptor openDirectory(String path) throws Exception {
        StructStat before = Os.lstat(path);
        if (!OsConstants.S_ISDIR(before.st_mode)) throw new IOException("Directory is not a direct directory");
        // O_DIRECTORY is not exposed by this API28 SDK. Open read-only without
        // following a final symlink, then require the descriptor itself is a directory.
        FileDescriptor fd = Os.open(path, OsConstants.O_RDONLY
                | OsConstants.O_NOFOLLOW | OsConstants.O_CLOEXEC, 0);
        StructStat opened = Os.fstat(fd);
        if (!OsConstants.S_ISDIR(opened.st_mode)
                || opened.st_dev != before.st_dev || opened.st_ino != before.st_ino) {
            Os.close(fd);
            throw new IOException("Directory identity changed");
        }
        return fd;
    }

    private static byte[] readLimited(String path, int limit, boolean rejectLinks) throws Exception {
        int flags = OsConstants.O_RDONLY | OsConstants.O_CLOEXEC;
        if (rejectLinks) flags |= OsConstants.O_NOFOLLOW;
        FileDescriptor fd = Os.open(path, flags, 0);
        try {
            if (rejectLinks && !OsConstants.S_ISREG(Os.fstat(fd).st_mode))
                throw new IOException("Read-back source is not a regular file");
            ByteArrayOutputStream result = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024];
            for (;;) {
                int n = Os.read(fd, buffer, 0, Math.min(buffer.length, limit + 1 - result.size()));
                if (n == 0) return result.toByteArray();
                if (n < 0) throw new IOException("Unexpected read result");
                result.write(buffer, 0, n);
                if (result.size() > limit) throw new IOException("Read limit exceeded");
            }
        } finally {
            Os.close(fd);
        }
    }

    private static String sha256(byte[] data) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(data);
        StringBuilder result = new StringBuilder();
        for (byte b : digest) result.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return result.toString();
    }

    private static String quote(String value) {
        if (value == null) value = "";
        StringBuilder result = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c == '\\' || c == '"') result.append('\\').append(c);
            else if (c < 32) result.append(String.format(java.util.Locale.ROOT, "\\u%04x", (int)c));
            else result.append(c);
        }
        return result.append('"').toString();
    }

    private static void stage(String nonce, String name) {
        phase = name;
        emit("stage", nonce, "\"phase\":" + quote(name));
    }

    private static void emit(String state, String nonce, String fields) {
        System.out.println("TVBASE_ROOT_PROBE:{\"state\":" + quote(state)
                + ",\"nonce\":" + quote(nonce) + "," + fields + "}");
        System.out.flush();
    }
}
