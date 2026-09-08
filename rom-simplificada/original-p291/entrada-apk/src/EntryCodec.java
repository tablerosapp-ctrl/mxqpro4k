package local.tvbase.acceso;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.zip.CRC32;

/** Pure byte codec. No device, file, command or network operation. */
final class EntryCodec {
    static final int ENV_SIZE = 65536, PART_SIZE = 8388608;
    static final String NORMAL = "run storeboot";
    static final String MENU_ONCE = "if setenv bootcmd 'run storeboot'; then if saveenv; then "
            + "run recovery_from_flash; run storeboot; else run storeboot; fi; else run storeboot; fi";
    static final byte[] MENU_ARGS = "recovery\n--show_text\n".getBytes(StandardCharsets.US_ASCII);

    static void require(boolean value, String message) throws IOException {
        if (!value) throw new IOException(message);
    }

    static String sha(byte[] value) throws IOException {
        try {
            StringBuilder out = new StringBuilder();
            for (byte b : MessageDigest.getInstance("SHA-256").digest(value))
                out.append(String.format(java.util.Locale.ROOT,"%02x", b & 255));
            return out.toString();
        } catch (java.security.NoSuchAlgorithmException e) { throw new IOException(e); }
    }

    static void snapshot(byte[] value, String expected, int size) throws IOException {
        require(value != null && value.length == size, "Longitud de snapshot inesperada");
        require(expected != null && expected.matches("[0-9a-f]{64}"), "SHA esperado inválido");
        require(sha(value).equals(expected), "El estado de origen cambió");
    }

    static LinkedHashMap<String,String> parseEnv(byte[] record) throws IOException {
        require(record.length == ENV_SIZE, "ENV requiere 64 KiB exactos");
        long expected = 0;
        for (int i=0; i<4; i++) expected |= (long)(record[i] & 255) << (8*i);
        CRC32 crc = new CRC32(); crc.update(record,4,record.length-4);
        require(crc.getValue() == expected, "CRC de ENV incorrecto");
        int end=-1;
        for (int i=4; i+1<record.length; i++) if (record[i]==0 && record[i+1]==0) { end=i; break; }
        require(end>4, "Falta terminador doble de ENV");
        for (int i=end+2; i<record.length; i++) require(record[i]==0, "Padding ENV desconocido");
        LinkedHashMap<String,String> out = new LinkedHashMap<String,String>();
        for (int start=4; start<end;) {
            int stop=start; while (stop<end && record[stop]!=0) stop++;
            int equals=start; while (equals<stop && record[equals]!='=') equals++;
            require(equals>start && equals<stop, "Entrada ENV sin clave/igual");
            String key = new String(record,start,equals-start,StandardCharsets.US_ASCII);
            require(key.matches("[A-Za-z0-9_]+") && !out.containsKey(key), "Clave ENV inválida o duplicada");
            // The exact pinned original contains an inherited LF in irremote_update.
            // Preserve that byte; the new bootcmd itself contains no LF.
            for (int i=equals+1;i<stop;i++) require(record[i]==10 || (record[i]>=32 && record[i]<=126), "Valor ENV no admitido");
            out.put(key,new String(record,equals+1,stop-equals-1,StandardCharsets.US_ASCII));
            start=stop+1;
        }
        return out;
    }

    static byte[] packEnv(LinkedHashMap<String,String> values) throws IOException {
        ByteArrayOutputStream body = new ByteArrayOutputStream();
        for (Map.Entry<String,String> entry:values.entrySet()) {
            byte[] text=(entry.getKey()+"="+entry.getValue()).getBytes(StandardCharsets.US_ASCII);
            body.write(text,0,text.length);body.write(0);
        }
        body.write(0);
        require(body.size()<=ENV_SIZE-4,"ENV excede capacidad");
        byte[] result=new byte[ENV_SIZE];System.arraycopy(body.toByteArray(),0,result,4,body.size());
        CRC32 crc=new CRC32();crc.update(result,4,result.length-4);
        for (int i=0;i<4;i++) result[i]=(byte)(crc.getValue() >>> (8*i));
        require(parseEnv(result).equals(values),"ENV no conserva sus valores");
        return result;
    }

    static byte[] envMenu(byte[] partition,String expected) throws IOException {
        snapshot(partition,expected,PART_SIZE);
        for(int i=ENV_SIZE;i<partition.length;i++) require(partition[i]==0,"Cola ENV desconocida");
        LinkedHashMap<String,String> values=parseEnv(Arrays.copyOf(partition,ENV_SIZE));
        require(NORMAL.equals(values.get("bootcmd")),"bootcmd ya preparado o diferente");
        require("recovery".equals(values.get("recovery_part")) && "0".equals(values.get("recovery_offset")),"Origen recovery distinto");
        require("2".equals(values.get("upgrade_step")),"Actualización OEM pendiente");
        require("successful".equals(values.get("wipe_data")) && "successful".equals(values.get("wipe_cache")),"Borrado OEM pendiente");
        require(values.containsKey("recovery_from_flash") && values.containsKey("storeboot") && values.containsKey("preboot"),"Faltan variables de arranque");
        values.put("bootcmd",MENU_ONCE);
        byte[] result=partition.clone();System.arraycopy(packEnv(values),0,result,0,ENV_SIZE);
        return result;
    }

    static byte[] bcbMenu(byte[] partition,String expected) throws IOException {
        snapshot(partition,expected,PART_SIZE);
        byte[] result=partition.clone();Arrays.fill(result,0,32,(byte)0);Arrays.fill(result,64,832,(byte)0);
        byte[] command="boot-recovery".getBytes(StandardCharsets.US_ASCII);
        System.arraycopy(command,0,result,0,command.length);System.arraycopy(MENU_ARGS,0,result,64,MENU_ARGS.length);
        require(Arrays.equals(Arrays.copyOfRange(result,32,64),Arrays.copyOfRange(partition,32,64))
                && Arrays.equals(Arrays.copyOfRange(result,832,result.length),Arrays.copyOfRange(partition,832,partition.length)),"BCB modificó campos ajenos");
        return result;
    }
}
