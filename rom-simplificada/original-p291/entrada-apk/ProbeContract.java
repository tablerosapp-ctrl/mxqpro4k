package local.tvbase.acceso;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

/** Pure contract; the probe never accepts a path or a command as an argument. */
final class ProbeContract {
    static final String PARENT = "/data/local/tmp";
    static final String DT = "gxlx2_p291_1g";

    static String nonce(String[] args) throws IOException {
        if (args == null || args.length != 1 || args[0] == null
                || !args[0].matches("[0-9a-f]{32}")) {
            throw new IOException("Expected exactly one lowercase 32-hex nonce");
        }
        return args[0];
    }

    static String directory(String nonce) throws IOException {
        nonce(new String[] {nonce});
        return PARENT + "/tvbase-entry-probe-" + nonce;
    }

    static byte[] payload(String nonce) throws IOException {
        nonce(new String[] {nonce});
        return ("TVBASE-P291-ROOT-PROBE-1\nnonce=" + nonce + "\n")
                .getBytes(StandardCharsets.UTF_8);
    }

    static String deviceTree(byte[] data) throws IOException {
        byte[] expected = DT.getBytes(StandardCharsets.US_ASCII);
        if (data.length != expected.length + 1 || data[data.length - 1] != 0) {
            throw new IOException("Device-tree property has an unexpected shape");
        }
        for (int i = 0; i < expected.length; i++) {
            if (data[i] != expected[i]) throw new IOException("Different P291 device tree");
        }
        return DT;
    }
}
