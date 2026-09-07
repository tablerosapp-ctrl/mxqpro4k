package local.tvbase.acceso;
public class AdbHarness {
 public static void main(String[] args)throws Exception{
  if(args[0].equals("commands")){System.out.print(Diagnostico.COMMAND+"\n\n"+Diagnostico.VERIFY_USB);return;}
  if(args[0].equals("limits")){if(Diagnostico.COMMAND.getBytes("UTF-8").length+7>4096||Diagnostico.VERIFY_USB.getBytes("UTF-8").length+7>4096)throw new Exception("ADB command exceeds negotiated packet size");System.out.println("Both commands fit 4096-byte ADB OPEN packets");return;}
  try(AdbLocal a=new AdbLocal("127.0.0.1",Integer.parseInt(args[0]))){
   if(args.length>1&&args[1].equals("update_flow")){
    String id=a.shell("id").trim(),dt=a.shell("cat /proc/device-tree/amlogic-dt-id").replace("\u0000","").trim(),sdk=a.shell("getprop ro.build.version.sdk").trim();
    System.out.println(EntradaAmlogic.start(a,id,dt,sdk,new EntradaAmlogic.Progress(){public void stage(String text){}}));
   }else if(args.length>1&&args[1].equals("flow")){
    System.out.println(a.shell("id"));System.out.println(a.shell("cat /proc/device-tree/amlogic-dt-id"));System.out.println(a.shell("getprop ro.build.version.sdk"));System.out.println(a.recovery());
   }else if(args.length>1&&args[1].equals("update"))System.out.println(a.updateMode());
   else System.out.println(args.length>1?a.recovery():a.shell("id"));
  }
 }
}
