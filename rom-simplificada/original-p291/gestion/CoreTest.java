package local.tvbase.gestion;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Host JVM regression tests. No Android stubs are executed and no network is used. */
public final class CoreTest {
    private static int passed=0;
    private static final long NOW=1800000000L;
    private static KeyPair keys;
    interface Checked { void run() throws Exception; }
    private static void ok(String name,Checked test) throws Exception {test.run();passed++;System.out.println("PASS "+name);}
    private static void fail(String name,Checked test) throws Exception {
        try{test.run();}catch(Exception expected){passed++;System.out.println("PASS "+name);return;}
        throw new AssertionError("Expected rejection: "+name);
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static String repeated(char c){char[] v=new char[64];Arrays.fill(v,c);return new String(v);}
    private static String policyText(){
        return "TVBASE-OWNER-1\nenabled=true\nmanifestUrl=https://updates.invalid/manifest\npublicKey="
            +Base64.getEncoder().encodeToString(keys.getPublic().getEncoded())
            +"\nhosts=updates.invalid\nautoApps=true\nautoBrowser=true\npollHours=24\nmaintenanceStartUtc=23:30\nmaintenanceMinutes=120"
            +"\npackages=local.test.app\npackage.local.test.app.certificate="+repeated('a')+"\npackage.local.test.app.role=browser\n";
    }
    private static String payload(){
        return "TVBASE-UPDATES-1\nsequence=8\nissuedAt="+(NOW-60)+"\nexpiresAt="+(NOW+3600)
            +"\ncount=1\napk.0.package=local.test.app\napk.0.versionCode=9\napk.0.minSdk=28\napk.0.maxSdk=28"
            +"\napk.0.abis=armeabi-v7a\napk.0.bytes=123\napk.0.sha256="+repeated('b')
            +"\napk.0.certificateSha256="+repeated('a')+"\napk.0.url=https://updates.invalid/app.apk\n";
    }
    private static byte[] signed(String payload,KeyPair key) throws Exception {
        Signature s=Signature.getInstance("SHA256withRSA");s.initSign(key.getPrivate());s.update(bytes(payload));
        return bytes("TVBASE-SIGNED-1\npayload="+Base64.getEncoder().encodeToString(bytes(payload))
                +"\nsignature="+Base64.getEncoder().encodeToString(s.sign())+"\n");
    }
    private static UpdateCore.Manifest parse(String value,UpdateCore.Policy p) throws Exception {
        return UpdateCore.manifest(signed(value,keys),p,NOW,0,"");
    }
    public static void main(String[] args) throws Exception {
        KeyPairGenerator gen=KeyPairGenerator.getInstance("RSA");gen.initialize(2048);keys=gen.generateKeyPair();
        final UpdateCore.Policy p=UpdateCore.policy(bytes(policyText()));
        ok("disabled contains no endpoint",()->UpdateCore.require(!UpdateCore.policy(bytes("TVBASE-OWNER-1\nenabled=false\n")).enabled,"enabled"));
        fail("disabled rejects hidden endpoint",()->UpdateCore.policy(bytes("TVBASE-OWNER-1\nenabled=false\nmanifestUrl=https://updates.invalid/\n")));
        ok("valid signed manifest",()->UpdateCore.require(parse(payload(),p).apks.size()==1,"count"));
        fail("unsigned fields do not replace signature",()->UpdateCore.manifest(bytes("TVBASE-SIGNED-1\npayload=YQ==\nsignature=YQ==\n"),p,NOW,0,""));
        final KeyPair other=gen.generateKeyPair();
        fail("wrong owner key",()->UpdateCore.manifest(signed(payload(),other),p,NOW,0,""));
        fail("expired",()->parse(payload().replace("expiresAt="+(NOW+3600),"expiresAt="+NOW),p));
        fail("future issue time",()->parse(payload().replace("issuedAt="+(NOW-60),"issuedAt="+(NOW+301)),p));
        fail("excess lifetime",()->parse(payload().replace("expiresAt="+(NOW+3600),"expiresAt="+(NOW+2678401)),p));
        fail("rollback sequence",()->UpdateCore.manifest(signed(payload(),keys),p,NOW,9,""));
        final UpdateCore.Manifest first=parse(payload(),p);
        ok("same sequence identical payload retry",()->UpdateCore.manifest(signed(payload(),keys),p,NOW,8,first.payloadHash));
        fail("same sequence different content",()->UpdateCore.manifest(signed(payload().replace("versionCode=9","versionCode=10"),keys),p,NOW,8,first.payloadHash));
        fail("duplicate field",()->parse(payload()+"sequence=9\n",p));
        fail("unknown field",()->parse(payload()+"command=reboot\n",p));
        fail("unknown package",()->parse(payload().replace("local.test.app","local.other.app"),p));
        fail("changed certificate",()->parse(payload().replace("certificateSha256="+repeated('a'),"certificateSha256="+repeated('c')),p));
        fail("different host",()->parse(payload().replace("https://updates.invalid/app.apk","https://other.invalid/app.apk"),p));
        fail("HTTP download",()->parse(payload().replace("https://updates.invalid/app.apk","http://updates.invalid/app.apk"),p));
        fail("URL credentials",()->parse(payload().replace("https://updates.invalid/app.apk","https://secret@updates.invalid/app.apk"),p));
        fail("APK size limit",()->parse(payload().replace("bytes=123","bytes=536870913"),p));
        fail("SDK incompatible",()->UpdateCore.platform(first.apks.get(0),29,new String[]{"armeabi-v7a"}));
        fail("ABI incompatible",()->UpdateCore.platform(first.apks.get(0),28,new String[]{"arm64-v8a"}));
        ok("SDK and ABI compatible",()->UpdateCore.platform(first.apks.get(0),28,new String[]{"armeabi-v7a"}));
        fail("invalid UTF8",()->UpdateCore.fields(new byte[]{(byte)255},"TVBASE-UPDATES-1"));
        fail("short RSA key",()->{
            KeyPairGenerator small=KeyPairGenerator.getInstance("RSA");small.initialize(1024);
            UpdateCore.policy(bytes(policyText().replace(Base64.getEncoder().encodeToString(keys.getPublic().getEncoded()),
                    Base64.getEncoder().encodeToString(small.generateKeyPair().getPublic().getEncoded()))));
        });
        ok("window wraps midnight",()->{
            Calendar t=Calendar.getInstance(TimeZone.getTimeZone("UTC"));t.set(2026,8,7,0,15,0);
            UpdateCore.require(p.automatic("local.test.app",t.getTimeInMillis()/1000),"window");
        });
        ok("outside maintenance stops browser automation",()->{
            Calendar t=Calendar.getInstance(TimeZone.getTimeZone("UTC"));t.set(2026,8,7,12,0,0);
            UpdateCore.require(!p.automatic("local.test.app",t.getTimeInMillis()/1000),"window");
        });
        ok("browser automation independent of disabled app automation",()->{
            UpdateCore.Policy one=UpdateCore.policy(bytes(policyText().replace("autoApps=true","autoApps=false")));
            UpdateCore.PackagePolicy app=new UpdateCore.PackagePolicy();app.name="local.test.second";app.role="app";
            one.packages.put(app.name,app);
            UpdateCore.require(!one.automaticRole(app.name) && one.automaticRole("local.test.app"),"roles");
        });
        fail("expiry rechecked at commit boundary",()->UpdateCore.beforeCommit(first,p,first.apks.get(0),NOW+3600,true,false));
        fail("cancellation rechecked at commit boundary",()->UpdateCore.beforeCommit(first,p,first.apks.get(0),NOW,true,true));
        fail("window rechecked at commit boundary",()->{
            UpdateCore.Policy one=UpdateCore.policy(bytes(policyText()));
            Calendar at=Calendar.getInstance(TimeZone.getTimeZone("UTC"));at.setTimeInMillis(NOW*1000L);
            one.maintenanceStart=(at.get(Calendar.HOUR_OF_DAY)*60+at.get(Calendar.MINUTE)+300)%1440;
            one.maintenanceMinutes=30;
            UpdateCore.beforeCommit(first,one,first.apks.get(0),NOW,false,false);
        });
        if(args.length>0){
            final UpdateCore.ApkMetadata apk=UpdateCore.inspectApk(new File(args[0]));
            ok("real compiled APK metadata",()->UpdateCore.require(apk.packageName.equals("local.tvbase.gestion")
                    && apk.versionCode==1 && apk.minSdk==28 && apk.abis.equals(Collections.singleton("none")),"metadata"));
            final UpdateCore.Artifact expected=new UpdateCore.Artifact();
            expected.packageName=apk.packageName;expected.versionCode=1;expected.minSdk=28;expected.maxSdk=28;expected.abis=Collections.singleton("none");
            ok("real APK matches signed platform metadata",()->UpdateCore.matchApk(expected,apk,28,new String[]{"armeabi-v7a"}));
            fail("APK actual version mismatch",()->{
                expected.versionCode=2;try{UpdateCore.matchApk(expected,apk,28,new String[]{"armeabi-v7a"});}finally{expected.versionCode=1;}
            });
            fail("APK actual minSdk mismatch",()->{
                expected.minSdk=27;try{UpdateCore.matchApk(expected,apk,28,new String[]{"armeabi-v7a"});}finally{expected.minSdk=28;}
            });
            fail("APK actual ABI mismatch",()->{
                expected.abis=Collections.singleton("armeabi-v7a");try{UpdateCore.matchApk(expected,apk,28,new String[]{"armeabi-v7a"});}finally{expected.abis=Collections.singleton("none");}
            });
        }
        if(args.length>1){
            byte[] owner;try(InputStream in=new FileInputStream(args[1])){owner=UpdateCore.readBounded(in,65536);}
            final byte[] config=owner;
            ok("build policy is valid",()->UpdateCore.policy(config));
        }
        System.out.println("PASSED="+passed);
    }
}
