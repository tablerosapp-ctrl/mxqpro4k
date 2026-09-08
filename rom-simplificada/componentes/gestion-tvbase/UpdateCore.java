package local.tvbase.gestion;

import java.io.*;
import java.net.URI;
import java.nio.*;
import java.nio.charset.*;
import java.security.*;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.util.*;
import java.util.zip.*;

/** Platform independent trust policy. No network, installer, shell or Android API. */
public final class UpdateCore {
    public static final int MAX_DOCUMENT = 131072;
    public static final long MAX_APK = 536870912L;
    private UpdateCore() {}
    public static void require(boolean yes, String message) throws IOException {
        if (!yes) throw new IOException(message);
    }
    public static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder();
        for (byte b : bytes) out.append(String.format(Locale.US, "%02x", b & 255));
        return out.toString();
    }
    public static String sha(byte[] bytes) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    public static String sha(File f) throws Exception {
        MessageDigest d = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(f)) {
            byte[] b = new byte[65536]; int n;
            while ((n = in.read(b)) != -1) d.update(b, 0, n);
        }
        return hex(d.digest());
    }
    public static byte[] readBounded(InputStream in, int max) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] b = new byte[8192]; int n;
        while ((n = in.read(b)) != -1) {
            require(out.size() <= max - n, "Documento demasiado grande");
            out.write(b, 0, n);
        }
        return out.toByteArray();
    }
    public static Map<String,String> fields(byte[] data, String magic) throws Exception {
        require(data.length <= MAX_DOCUMENT, "Documento demasiado grande");
        String s = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(data)).toString();
        require(s.indexOf('\r') < 0 && s.indexOf('\0') < 0, "Formato de texto inválido");
        String[] lines = s.split("\n", -1);
        require(lines.length > 1 && lines[0].equals(magic), "Formato no admitido");
        Map<String,String> m = new LinkedHashMap<String,String>();
        for (int i = 1; i < lines.length; i++) {
            if (i == lines.length - 1 && lines[i].isEmpty()) continue;
            int eq = lines[i].indexOf('=');
            require(eq > 0, "Campo inválido");
            String k = lines[i].substring(0, eq), v = lines[i].substring(eq + 1);
            require(k.matches("[A-Za-z0-9_.]+") && !v.isEmpty() && v.equals(v.trim()), "Campo inválido");
            require(!m.containsKey(k), "Campo repetido: " + k);
            m.put(k, v);
        }
        return m;
    }
    private static String take(Map<String,String> m, String k) throws IOException {
        String v = m.remove(k); require(v != null, "Falta " + k); return v;
    }
    private static long number(String v, long min, long max) throws IOException {
        require(v.matches("0|[1-9][0-9]*"), "Número inválido");
        try { long n = Long.parseLong(v); require(n >= min && n <= max, "Número fuera de rango"); return n; }
        catch (NumberFormatException e) { throw new IOException("Número fuera de rango"); }
    }
    private static boolean bool(String v) throws IOException {
        require(v.equals("true") || v.equals("false"), "Booleano inválido"); return v.equals("true");
    }
    private static Set<String> csv(String value) throws IOException {
        Set<String> out = new LinkedHashSet<String>();
        for (String s : value.split(",", -1)) require(!s.isEmpty() && out.add(s), "Lista inválida");
        return out;
    }
    private static String digest(String s) throws IOException {
        require(s.matches("[0-9a-f]{64}"), "SHA256 inválido"); return s;
    }
    public static final class PackagePolicy {
        public String name, certificate, role;
    }
    public static final class Policy {
        public boolean enabled, autoApps, autoBrowser;
        public String fingerprint;
        public URI manifest;
        public PublicKey key;
        public int pollHours, maintenanceStart, maintenanceMinutes;
        public final Set<String> hosts = new LinkedHashSet<String>();
        public final Map<String,PackagePolicy> packages = new LinkedHashMap<String,PackagePolicy>();
        public boolean window(long nowSeconds) {
            Calendar c = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
            c.setTimeInMillis(nowSeconds * 1000L);
            int t = c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE);
            return (t - maintenanceStart + 1440) % 1440 < maintenanceMinutes;
        }
        public boolean automatic(String packageName, long nowSeconds) {
            return automaticRole(packageName) && window(nowSeconds);
        }
        public boolean automaticRole(String packageName) {
            PackagePolicy p = packages.get(packageName);
            return p != null && (p.role.equals("browser") ? autoBrowser : autoApps);
        }
    }
    public static URI https(String value, Set<String> hosts) throws Exception {
        URI u = new URI(value);
        require("https".equals(u.getScheme()) && u.getHost() != null && u.getRawUserInfo() == null
                && u.getRawFragment() == null && (u.getPort() == -1 || u.getPort() == 443), "Se requiere HTTPS sin credenciales ni redirecciones");
        require(u.getHost().equals(u.getHost().toLowerCase(Locale.US)), "Host debe estar en minúsculas");
        require(hosts == null || hosts.contains(u.getHost()), "Host de descarga no autorizado");
        return u;
    }
    public static Policy policy(byte[] data) throws Exception {
        Map<String,String> m = fields(data, "TVBASE-OWNER-1"); Policy p = new Policy();
        p.fingerprint = sha(data);
        p.enabled = bool(take(m, "enabled"));
        if (!p.enabled) { require(m.isEmpty(), "Configuración desactivada debe carecer de destino"); return p; }
        p.manifest = https(take(m, "manifestUrl"), null);
        byte[] der = Base64.getDecoder().decode(take(m, "publicKey"));
        p.key = KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(der));
        int bits = ((RSAPublicKey)p.key).getModulus().bitLength();
        require(bits >= 2048 && bits <= 8192, "Clave RSA fuera de rango");
        p.hosts.addAll(csv(take(m, "hosts")));
        for (String h : p.hosts) {
            URI u = https("https://" + h + "/", null);
            require(u.getHost().equals(h), "Host inválido");
        }
        require(p.hosts.contains(p.manifest.getHost()), "Host del manifiesto no autorizado");
        p.autoApps = bool(take(m, "autoApps")); p.autoBrowser = bool(take(m, "autoBrowser"));
        p.pollHours = (int)number(take(m, "pollHours"), 1, 168);
        String start = take(m, "maintenanceStartUtc");
        require(start.matches("[0-2][0-9]:[0-5][0-9]"), "Horario UTC inválido");
        int hour = Integer.parseInt(start.substring(0, 2));
        require(hour < 24, "Horario UTC inválido");
        p.maintenanceStart = hour * 60 + Integer.parseInt(start.substring(3));
        p.maintenanceMinutes = (int)number(take(m, "maintenanceMinutes"), 15, 240);
        for (String name : csv(take(m, "packages"))) {
            require(name.matches("[a-zA-Z][a-zA-Z0-9_]*(\\.[a-zA-Z][a-zA-Z0-9_]*)+"), "Paquete inválido");
            PackagePolicy one = new PackagePolicy(); one.name = name;
            one.certificate = digest(take(m, "package." + name + ".certificate"));
            one.role = take(m, "package." + name + ".role");
            require(one.role.equals("app") || one.role.equals("browser"), "Rol inválido");
            p.packages.put(name, one);
        }
        require(p.packages.size() <= 16 && m.isEmpty(), "Campos o paquetes no admitidos");
        return p;
    }
    public static final class Artifact {
        public String packageName, sha256, certificate;
        public URI url;
        public long versionCode, bytes;
        public int minSdk, maxSdk;
        public Set<String> abis;
    }
    public static final class Manifest {
        public long sequence, issuedAt, expiresAt;
        public String payloadHash;
        public final List<Artifact> apks = new ArrayList<Artifact>();
    }
    public static Manifest manifest(byte[] envelope, Policy policy, long now, long previous, String previousHash) throws Exception {
        require(policy.enabled, "Actualizaciones sin configurar");
        Map<String,String> e = fields(envelope, "TVBASE-SIGNED-1");
        byte[] payload = Base64.getDecoder().decode(take(e, "payload"));
        byte[] signed = Base64.getDecoder().decode(take(e, "signature"));
        require(e.isEmpty() && payload.length <= 65536, "Sobre inválido");
        Signature verify = Signature.getInstance("SHA256withRSA"); verify.initVerify(policy.key);
        verify.update(payload); require(verify.verify(signed), "Firma del manifiesto inválida");
        Map<String,String> m = fields(payload, "TVBASE-UPDATES-1"); Manifest out = new Manifest();
        out.sequence = number(take(m, "sequence"), 1, Long.MAX_VALUE);
        out.issuedAt = number(take(m, "issuedAt"), 1, 4102444800L);
        out.expiresAt = number(take(m, "expiresAt"), 1, 4102444800L);
        require(out.issuedAt <= now + 300 && now < out.expiresAt
                && out.expiresAt > out.issuedAt && out.expiresAt - out.issuedAt <= 2678400L, "Manifiesto vencido o reloj incorrecto");
        out.payloadHash = sha(payload);
        require(out.sequence >= previous, "Secuencia anterior rechazada");
        require(out.sequence != previous || out.payloadHash.equals(previousHash), "Una secuencia no puede cambiar contenido");
        int count = (int)number(take(m, "count"), 1, 16);
        Set<String> packages = new HashSet<String>();
        for (int i = 0; i < count; i++) {
            String prefix = "apk." + i + "."; Artifact a = new Artifact();
            a.packageName = take(m, prefix + "package");
            PackagePolicy rule = policy.packages.get(a.packageName);
            require(rule != null && packages.add(a.packageName), "Paquete repetido o no autorizado");
            a.versionCode = number(take(m, prefix + "versionCode"), 1, Long.MAX_VALUE);
            a.minSdk = (int)number(take(m, prefix + "minSdk"), 1, 1000);
            a.maxSdk = (int)number(take(m, prefix + "maxSdk"), a.minSdk, 1000);
            a.bytes = number(take(m, prefix + "bytes"), 1, MAX_APK);
            a.sha256 = digest(take(m, prefix + "sha256"));
            a.certificate = digest(take(m, prefix + "certificateSha256"));
            require(a.certificate.equals(rule.certificate), "Certificado fuera de la política del dueño");
            a.url = https(take(m, prefix + "url"), policy.hosts);
            a.abis = csv(take(m, prefix + "abis"));
            for (String abi : a.abis) require(Arrays.asList("none","armeabi-v7a","arm64-v8a","x86","x86_64").contains(abi), "ABI no admitida");
            require(!a.abis.contains("none") || a.abis.size() == 1, "ABI universal mezclada");
            out.apks.add(a);
        }
        require(m.isEmpty(), "Campos de manifiesto no admitidos"); return out;
    }
    public static void platform(Artifact a, int sdk, String[] supported) throws Exception {
        require(sdk >= a.minSdk && sdk <= a.maxSdk, "API fuera del rango firmado");
        require(a.abis.contains("none") || !Collections.disjoint(a.abis, Arrays.asList(supported)), "ABI incompatible");
    }
    public static void beforeCommit(Manifest m, Policy p, Artifact a, long now, boolean manual, boolean cancelled) throws Exception {
        require(!cancelled, "Instalación cancelada antes de enviar");
        require(m.issuedAt <= now + 300 && now < m.expiresAt, "El manifiesto venció antes de instalar");
        if (!manual) require(p.automatic(a.packageName, now), "Terminó la ventana de mantenimiento antes de instalar");
    }
    public static final class ApkMetadata {
        public String packageName;
        public long versionCode;
        public int minSdk = 1, maxSdk = 1000;
        public final Set<String> abis = new HashSet<String>();
    }
    public static ApkMetadata inspectApk(File file) throws Exception {
        ApkMetadata info;
        try (ZipFile z = new ZipFile(file)) {
            ZipEntry manifest = z.getEntry("AndroidManifest.xml");
            require(manifest != null, "APK sin manifiesto");
            try (InputStream in = z.getInputStream(manifest)) { info = axml(readBounded(in, 4194304)); }
            Set<String> names = new HashSet<String>();
            Enumeration<? extends ZipEntry> entries = z.entries();
            while (entries.hasMoreElements()) {
                ZipEntry e = entries.nextElement(); String name = e.getName();
                require(names.add(name) && !name.startsWith("/") && name.indexOf('\\') < 0
                        && !Arrays.asList(name.split("/", -1)).contains(".."), "Entrada ZIP ambigua");
                if (name.startsWith("lib/") && name.endsWith(".so")) {
                    String[] path = name.split("/");
                    require(path.length == 3, "Biblioteca nativa inválida"); info.abis.add(path[1]);
                }
            }
        }
        if (info.abis.isEmpty()) info.abis.add("none");
        return info;
    }
    public static void matchApk(Artifact a, ApkMetadata actual, int sdk, String[] supported) throws Exception {
        platform(a, sdk, supported);
        require(a.packageName.equals(actual.packageName) && a.versionCode == actual.versionCode, "Paquete o versión real distintos");
        require(a.minSdk == actual.minSdk && sdk <= actual.maxSdk && sdk >= actual.minSdk, "API del APK distinta o incompatible");
        require(actual.abis.equals(a.abis), "ABI declarada distinta del APK");
    }
    private static int u16(ByteBuffer b, int at) throws IOException {
        require(at >= 0 && at <= b.limit() - 2, "AXML truncado"); return b.getShort(at) & 65535;
    }
    private static int integer(ByteBuffer b, int at) throws IOException {
        require(at >= 0 && at <= b.limit() - 4, "AXML truncado"); return b.getInt(at);
    }
    private static String str(List<String> strings, int index) throws IOException {
        require(index >= 0 && index < strings.size(), "Índice AXML inválido"); return strings.get(index);
    }
    private static int len8(byte[] data, int[] at, int end) throws IOException {
        require(at[0] < end, "Cadena AXML truncada"); int v = data[at[0]++] & 255;
        if ((v & 128) != 0) { require(at[0] < end, "Cadena AXML truncada"); v = ((v & 127) << 8) | (data[at[0]++] & 255); }
        return v;
    }
    private static ApkMetadata axml(byte[] data) throws Exception {
        ByteBuffer b = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        require(u16(b,0) == 3 && u16(b,2) == 8 && integer(b,4) == data.length, "Manifiesto AXML inválido");
        List<String> strings = new ArrayList<String>(); ApkMetadata out = new ApkMetadata();
        boolean root = false, sdkSeen = false;
        for (int pos = 8; pos < data.length;) {
            int type = u16(b,pos), header = u16(b,pos+2), size = integer(b,pos+4);
            require(header >= 8 && size >= header && size <= data.length-pos, "Chunk AXML inválido");
            int end = pos + size;
            if (type == 1) {
                require(strings.isEmpty() && header >= 28, "String pool inválido");
                int count=integer(b,pos+8), flags=integer(b,pos+16), start=integer(b,pos+20);
                require(count >= 0 && count <= 65536 && header + (long)count*4 <= size && start >= header && start < size, "String pool fuera de rango");
                for (int i=0;i<count;i++) {
                    int off=integer(b,pos+header+i*4), at=pos+start+off;
                    require(off>=0 && at>=pos && at<end, "Offset de cadena inválido");
                    if ((flags & 256)!=0) {
                        int[] cursor={at}; len8(data,cursor,end); int n=len8(data,cursor,end);
                        require(n <= end-cursor[0]-1 && data[cursor[0]+n]==0, "UTF8 AXML truncado");
                        strings.add(StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                                .decode(ByteBuffer.wrap(data,cursor[0],n)).toString());
                    } else {
                        int n=u16(b,at); at+=2;
                        if ((n&32768)!=0) { n=((n&32767)<<16)|u16(b,at); at+=2; }
                        require(n>=0 && (long)n*2 <= end-at-2 && u16(b,at+n*2)==0, "UTF16 AXML truncado");
                        strings.add(new String(data,at,n*2,StandardCharsets.UTF_16LE));
                    }
                }
            } else if (type == 0x102) {
                require(header==16 && size>=36, "Elemento AXML inválido");
                String tag=str(strings,integer(b,pos+20));
                int start=u16(b,pos+24), width=u16(b,pos+26), count=u16(b,pos+28);
                require(start>=20 && width==20 && 16L+start+(long)width*count<=size, "Atributos AXML fuera de rango");
                require(!tag.equals("uses-split"), "Los APK divididos no están admitidos");
                if (tag.equals("manifest")) { require(!root,"Manifest repetido"); root=true; }
                if (tag.equals("uses-sdk")) { require(!sdkSeen,"SDK repetido"); sdkSeen=true; }
                Set<String> seen=new HashSet<String>();
                for (int i=0;i<count;i++) {
                    int a=pos+16+start+i*width;
                    int nsId=integer(b,a), typeId=data[a+15]&255, value=integer(b,a+16);
                    String ns=nsId==-1?"":str(strings,nsId), name=str(strings,integer(b,a+4));
                    require(seen.add(ns+"|"+name),"Atributo repetido");
                    boolean android=ns.equals("http://schemas.android.com/apk/res/android");
                    if (tag.equals("manifest") && ns.isEmpty() && name.equals("package")) {
                        require(typeId==3,"Paquete no literal"); out.packageName=str(strings,value);
                    } else if (tag.equals("manifest") && name.equals("split")) {
                        throw new IOException("Solo se admiten APK base independientes");
                    } else if (android && name.equals("isSplitRequired")) {
                        require(value==0,"El APK requiere splits");
                    } else if (tag.equals("manifest") && android && name.equals("versionCode")) {
                        require(typeId==0x10 || typeId==0x11,"Versión no literal"); out.versionCode=(out.versionCode&0xffffffff00000000L)|(value&0xffffffffL);
                    } else if (tag.equals("manifest") && android && name.equals("versionCodeMajor")) {
                        require(typeId==0x10 || typeId==0x11,"Versión no literal"); out.versionCode=(out.versionCode&0xffffffffL)|((long)value<<32);
                    } else if (tag.equals("uses-sdk") && android && (name.equals("minSdkVersion") || name.equals("maxSdkVersion"))) {
                        require((typeId==0x10 || typeId==0x11) && value>0 && value<1000,"API no literal o fuera de rango");
                        if(name.equals("minSdkVersion"))out.minSdk=value;else out.maxSdk=value;
                    }
                }
            }
            pos=end;
        }
        require(root && out.packageName!=null && out.versionCode>0,"Manifiesto incompleto"); return out;
    }
}
