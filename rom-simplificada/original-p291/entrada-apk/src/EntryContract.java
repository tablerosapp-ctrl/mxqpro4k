package local.tvbase.acceso;

import java.io.IOException;

/** All destinations are internal constants or one generated capture nonce. */
final class EntryContract {
    static final String DT="gxlx2_p291_1g";
    static final String BUILD="ampere-userdebug 9 PPR1.180610.011 20250226 test-keys";
    static final String MEDIA="TVBASE-P291-20260906-4dc82786";
    static final String ENV_SHA="49e48fddb963d1a4ebaf5889916bba8b59141bcc1eeef71ac1dad5c6425af775";
    static final String MISC_SHA="c8b5991390836e2f03693d8a4f6f2f4ea2b223c20951a119155fba19cf542549";
    static final String[] CACHE={"command","uncrypt_file","zipinfo","block.map"};

    static String nonce(String value) throws IOException {
        EntryCodec.require(value!=null && value.matches("[0-9a-f]{32}"),"Nonce inválido");return value;
    }

    static String apkPath(String value) throws IOException {
        EntryCodec.require(value!=null && value.length()<=512 && value.startsWith("/data/app/")
                && value.endsWith("/base.apk") && value.matches("[A-Za-z0-9_./=+~\\-]+")
                && !value.contains("/../") && !value.contains("/./"),"Ruta de la APK no admitida");
        return value;
    }

    static String quote(String value) {return "'"+value.replace("'","'\\''")+"'";}

    static String command(String apk,String nonce,String operation) throws IOException {
        apkPath(apk);nonce(nonce);
        EntryCodec.require(operation.equals("launch")||operation.equals("status"),"Operación ADB no permitida");
        String run="CLASSPATH="+quote(apk)+" /system/bin/app_process /system/bin local.tvbase.acceso.PreparationHelper "+operation+" "+nonce;
        String outer="if [ \"$(/system/bin/id -u)\" != 2000 ]; then exit 40; fi; /system/xbin/su 0 /system/bin/sh -c "+quote(run)
                +"; tvbase_rc=$?; printf '\\nTVBASE_EXIT:"+nonce+":%s\\n' \"$tvbase_rc\"; exit \"$tvbase_rc\"";
        String command="/system/bin/sh -c "+quote(outer);
        EntryCodec.require(command.getBytes(java.nio.charset.StandardCharsets.UTF_8).length+6<=4096,"Comando ADB demasiado largo");
        return command;
    }
}
