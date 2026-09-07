package local.tvbase.acceso;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
public class EntradaHarness07 {
 static final String TOKEN="1234567890abcdef1234567890abcdef",DIR="/storage/ABCD-1234";
 static final Entrada.Progress QUIET=new Entrada.Progress(){public void stage(String s){}};
 static final class Fake implements Entrada.Access {
  List<Integer> seen=new ArrayList<Integer>();int fail=-1;String directory=DIR;
  public String entryStep(int n,String d,String t)throws IOException {
   if(n>0&&!d.equals(DIR))throw new IOException("Changed destination");
   String cmd=EntradaScripts.command(n,d,t);
   if(cmd.contains("reboot:")||cmd.contains("setprop")||cmd.contains("setupBcb")||cmd.contains(" --es "))throw new IOException("Forbidden action");
   seen.add(n);if(n==fail)return "ERROR simulated";
   return n==0?"TVBASE_MEDIA:"+directory:"TVBASE_OPEN_OK:"+t;
  }
 }
 static void require(boolean x,String m)throws Exception{if(!x)throw new Exception(m);}
 static void reject(Entrada e,Fake f,String id,String dt,String sdk)throws Exception{
  try{e.open(f,id,dt,sdk,TOKEN,QUIET);throw new Exception("Expected guard failure");}catch(IOException expected){}
 }
 static void guards()throws Exception {
  for(String[] p:new String[][]{{"uid=0(root)","gxlx2_p291_1g","28"},{"uid=10001(app)","gxlx2_p291_1g","28"},{"uid=2000(shell)","gxlx_p271_1g","28"},{"uid=2000(shell)","gxlx2_p291_1g","29"}}){Fake f=new Fake();reject(new Entrada(),f,p[0],p[1],p[2]);require(f.seen.isEmpty(),"Invalid profile used USB");}
  for(int n=0;n<2;n++){Fake f=new Fake();f.fail=n;Entrada e=new Entrada();reject(e,f,"uid=2000(shell)","gxlx2_p291_1g","28");require(f.seen.size()==n+1,"Continued after failure");reject(e,f,"uid=2000(shell)","gxlx2_p291_1g","28");require(f.seen.size()==n+1,"Failure retried");}
  for(String d:new String[]{"/storage/../bad","/storage/USB;id","/data/local","/storage/emulated","/storage/USB/extra"}){Fake f=new Fake();f.directory=d;reject(new Entrada(),f,"uid=2000(shell)","gxlx2_p291_1g","28");require(f.seen.size()==1,"Invalid media opened updater");try{EntradaScripts.command(1,d,TOKEN);throw new Exception("Unsafe path accepted");}catch(IOException expected){}}
  Fake f=new Fake();Entrada e=new Entrada();String result=e.open(f,"uid=2000(shell)","gxlx2_p291_1g","28",TOKEN,QUIET);require(result.contains("Menú local abierto")&&f.seen.size()==2,"Missing opening");reject(e,f,"uid=2000(shell)","gxlx2_p291_1g","28");require(f.seen.size()==2,"Repeated opening");
  for(int n=0;n<2;n++)require(EntradaScripts.command(n,n==0?"":DIR,TOKEN).getBytes("UTF-8").length+7<=4096,"Oversize OPEN");
  for(String token:new String[]{"",TOKEN+";id","ABCDEF"})try{EntradaScripts.command(0,"",token);throw new Exception("Unsafe token");}catch(IOException expected){}
  System.out.println("GUARDS_OK: profile x4; failure stop/no retry x2; path rejection x5; token x3; exact two-stage opening; OPEN limits");
 }
 public static void main(String[] args)throws Exception {
  if(args[0].equals("guards")){guards();return;}
  if(args[0].equals("dump")){int n=Integer.parseInt(args[1]);System.out.print(EntradaScripts.command(n,n==0?"":DIR,TOKEN));return;}
  if(args[0].equals("external_host")){new AdbLocal("198.51.100.100",5555);throw new Exception("External host accepted");}
  try(AdbLocal a=new AdbLocal("127.0.0.1",Integer.parseInt(args[0]))){
   if(args.length>1&&args[1].equals("deadline")){
    java.lang.reflect.Field cap=AdbLocal.class.getDeclaredField("readTimeoutMillis");cap.setAccessible(true);cap.setInt(a,300000);
    java.lang.reflect.Method service=AdbLocal.class.getDeclaredMethod("service",String.class,Long.TYPE);service.setAccessible(true);service.invoke(a,"shell:id",300000000L);
   }else if(args.length>1&&args[1].equals("flow")){
    String id=a.shell("id").trim(),dt=a.shell("cat /proc/device-tree/amlogic-dt-id").replace("\u0000","").trim(),sdk=a.shell("getprop ro.build.version.sdk").trim();
    System.out.println(new Entrada().open(a,id,dt,sdk,TOKEN,QUIET));
   }else System.out.println(a.shell("id"));
  }
 }
}
