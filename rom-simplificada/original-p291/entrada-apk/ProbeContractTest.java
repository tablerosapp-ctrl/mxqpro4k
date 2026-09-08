package local.tvbase.acceso;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class ProbeContractTest {
    private static int checks;
    private static void require(boolean condition) {
        checks++;
        if (!condition) throw new AssertionError("Check " + checks);
    }
    private static void reject(String[] args) throws Exception {
        try { ProbeContract.nonce(args); }
        catch (IOException expected) { checks++; return; }
        throw new AssertionError("Accepted invalid arguments");
    }
    public static void main(String[] args) throws Exception {
        String n = "00112233445566778899aabbccddeeff";
        require(ProbeContract.nonce(new String[]{n}).equals(n));
        require(ProbeContract.directory(n).equals("/data/local/tmp/tvbase-entry-probe-"+n));
        require(new String(ProbeContract.payload(n), StandardCharsets.UTF_8).equals("TVBASE-P291-ROOT-PROBE-1\nnonce="+n+"\n"));
        reject(null); reject(new String[0]); reject(new String[]{null});
        reject(new String[]{n,"/data/other"}); reject(new String[]{"../"+n});
        reject(new String[]{n.toUpperCase(java.util.Locale.ROOT)});
        reject(new String[]{n+";id"}); reject(new String[]{n+"\n"});
        reject(new String[]{n.substring(1)});
        require(ProbeContract.deviceTree((ProbeContract.DT+"\0").getBytes(StandardCharsets.US_ASCII)).equals(ProbeContract.DT));
        for (String bad : new String[]{ProbeContract.DT,ProbeContract.DT+"\0\0","gxlx_p271_1g\0",ProbeContract.DT+"\n"}) {
            try { ProbeContract.deviceTree(bad.getBytes(StandardCharsets.US_ASCII)); }
            catch (IOException expected) { checks++; continue; }
            throw new AssertionError("Accepted wrong device-tree shape");
        }
        System.out.println("Probe contract: "+checks+" host checks passed; no Android APIs executed");
    }
}
