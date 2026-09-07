package local.tvbase.acceso;
import java.io.IOException;
import java.util.ArrayList;

public class EntradaHarness {
  static final class Fake implements EntradaAmlogic.Access {
    ArrayList<String> calls=new ArrayList<String>();String report="Informe guardado en el pendrive:\n/storage/test/TVBASE-diagnostico.txt\n",usb="TVBASE_USB_OK\n";boolean failure;
    public String diagnose(){calls.add("report");return report;}
    public String verifyUSB(){calls.add("verify");return usb;}
    public String updateMode()throws IOException{calls.add("update");if(failure)throw new IOException("reboot failed");return "requested";}
  }
  public static void main(String[] args)throws Exception{
    int cases=0;
    for(String scenario:new String[]{"ok","wrong_board","wrong_api","wrong_uid","report_failed","usb_failed","update_failed"}){
      Fake fake=new Fake();String dt="gxlx2_p291_1g",sdk="28",id="uid=2000(shell)";
      if(scenario.equals("wrong_board"))dt="gxlx_p271_1g";
      if(scenario.equals("wrong_api"))sdk="29";
      if(scenario.equals("wrong_uid"))id="uid=10001(app)";
      if(scenario.equals("report_failed"))fake.report="ERROR: no USB";
      if(scenario.equals("usb_failed"))fake.usb="ERROR: checksum";
      if(scenario.equals("update_failed"))fake.failure=true;
      boolean success=false;
      try{EntradaAmlogic.start(fake,id,dt,sdk,new EntradaAmlogic.Progress(){public void stage(String text){}});success=true;}catch(IOException expected){}
      if(success!=scenario.equals("ok"))throw new Exception("Unexpected result: "+scenario);
      String expected=scenario.startsWith("wrong_")?"[]":scenario.equals("report_failed")?"[report]":scenario.equals("usb_failed")?"[report, verify]":"[report, verify, update]";
      if(!fake.calls.toString().equals(expected))throw new Exception("Unexpected operation order/retry: "+scenario+fake.calls);
      cases++;
    }
    System.out.println(cases+" guarded-entry cases passed: no reboot on mismatched TV/report/USB and no retries");
  }
}
