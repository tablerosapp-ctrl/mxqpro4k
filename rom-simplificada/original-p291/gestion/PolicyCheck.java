package local.tvbase.gestion;
import java.io.*;
public final class PolicyCheck {
    public static void main(String[] args) throws Exception {
        byte[] raw;try(InputStream in=new FileInputStream(args[0])){raw=UpdateCore.readBounded(in,65536);}
        UpdateCore.Policy p=UpdateCore.policy(raw);
        if(args.length>1){
            byte[] envelope;try(InputStream in=new FileInputStream(args[1])){envelope=UpdateCore.readBounded(in,UpdateCore.MAX_DOCUMENT);}
            UpdateCore.Manifest m=UpdateCore.manifest(envelope,p,System.currentTimeMillis()/1000,0,"");
            System.out.println("MANIFEST_VALID="+m.sequence);
        }
        System.out.println("POLICY_VALID enabled="+p.enabled);
    }
}
