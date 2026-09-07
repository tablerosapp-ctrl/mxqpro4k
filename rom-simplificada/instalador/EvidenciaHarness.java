package local.tvbase.acceso;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
public class EvidenciaHarness {
 static final String TOKEN="1234567890abcdef1234567890abcdef";
 static final String DIR="/storage/ABCD-1234/TVBASE-evidencia-"+TOKEN;
 static final Evidencia.Progress QUIET=new Evidencia.Progress(){public void stage(String s){}};
 static final class Fake implements Evidencia.Access {
  List<Integer> seen=new ArrayList<Integer>();int fail=-1;boolean wrongDirectory;
  public String evidenceStep(int n,String d,String t)throws IOException{
   if(n>0&&!d.equals(DIR))throw new IOException("Destination changed");
   String command=EvidenciaScripts.command(n,d,t);
   if(command.contains("reboot:")||command.contains("am start")||command.contains("setprop"))throw new IOException("Unexpected mutation");
   seen.add(n);
   if(n==fail)return "ERROR simulated";
   if(n==0)return "TVBASE_READY:"+(wrongDirectory?"/storage/../bad":DIR);
   return "TVBASE_OK:"+n+":"+t;
  }
 }
 static void require(boolean value,String message)throws Exception{if(!value)throw new Exception(message);}
 static void reject(Evidencia e,Fake f,String id,String dt,String sdk)throws Exception{
  try{e.collect(f,id,dt,sdk,TOKEN,QUIET);throw new Exception("Expected guard failure");}catch(IOException expected){}
 }
 static void guards()throws Exception{
  for(String[] p:new String[][]{{"uid=10001(app)","gxlx2_p291_1g","28"},{"uid=2000(shell)","gxlx_p271_1g","28"},{"uid=2000(shell)","gxlx2_p291_1g","29"}}){
   Fake f=new Fake();reject(new Evidencia(),f,p[0],p[1],p[2]);require(f.seen.isEmpty(),"Rejected profile reached USB");
  }
  for(int n:new int[]{0,1,4,6}){Fake f=new Fake();f.fail=n;reject(new Evidencia(),f,"uid=2000(shell)","gxlx2_p291_1g","28");require(f.seen.size()==n+1,"Failure retried/continued");}
  Fake wrong=new Fake();wrong.wrongDirectory=true;reject(new Evidencia(),wrong,"uid=2000(shell)","gxlx2_p291_1g","28");require(wrong.seen.size()==1,"Changed destination continued");
  Fake f=new Fake();Evidencia e=new Evidencia();String result=e.collect(f,"uid=2000(shell)","gxlx2_p291_1g","28",TOKEN,QUIET);
  require(f.seen.size()==7&&f.seen.get(6)==6&&result.contains("guardada y comprobada"),"Final stage missing");
  reject(e,f,"uid=2000(shell)","gxlx2_p291_1g","28");require(f.seen.size()==7,"Same capture repeated");
  for(String d:new String[]{"/storage/../TVBASE-evidencia-"+TOKEN,"/storage/USB/TVBASE-evidencia-"+TOKEN+";id","/data/TVBASE-evidencia-"+TOKEN}){
   try{EvidenciaScripts.command(1,d,TOKEN);throw new Exception("Unsafe destination accepted");}catch(IOException expected){}
  }
  for(int n=0;n<7;n++){String c=EvidenciaScripts.command(n,n==0?"":DIR,TOKEN);require(c.getBytes("UTF-8").length+7<=4096,"Oversized OPEN");}
  System.out.println("GUARDS_OK: profile x3; stages failure x4; wrong destination; final mandatory; no retry; path injection x3; packet sizes x7");
 }
 public static void main(String[] args)throws Exception{
  if(args[0].equals("guards")){guards();return;}
  if(args[0].equals("dump")){int n=Integer.parseInt(args[1]);System.out.print(EvidenciaScripts.command(n,n==0?"":DIR,TOKEN));return;}
  if(args[0].equals("external_host")){new AdbLocal("198.51.100.100",5555);throw new Exception("External host accepted");}
  try(AdbLocal a=new AdbLocal("127.0.0.1",Integer.parseInt(args[0]))){
   if(args.length>1&&args[1].equals("deadline")){
    java.lang.reflect.Field cap=AdbLocal.class.getDeclaredField("readTimeoutMillis");cap.setAccessible(true);cap.setInt(a,90000);
    java.lang.reflect.Method service=AdbLocal.class.getDeclaredMethod("service",String.class,Long.TYPE);service.setAccessible(true);service.invoke(a,"shell:id",300000000L);
   }else if(args.length>1&&args[1].equals("flow")){
    String id=a.shell("id").trim(),dt=a.shell("cat /proc/device-tree/amlogic-dt-id").replace("\u0000","").trim(),sdk=a.shell("getprop ro.build.version.sdk").trim();
    System.out.println(new Evidencia().collect(a,id,dt,sdk,TOKEN,QUIET));
   }else System.out.println(a.shell("id"));
  }
 }
}
