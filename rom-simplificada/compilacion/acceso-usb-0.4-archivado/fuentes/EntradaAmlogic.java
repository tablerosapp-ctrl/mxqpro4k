package local.tvbase.acceso;
import java.io.IOException;

/** Orders the guarded attempt; no retries, root requests, or direct flash commands. */
final class EntradaAmlogic {
  interface Access {
    String diagnose() throws IOException;
    String verifyUSB() throws IOException;
    String updateMode() throws IOException;
  }
  interface Progress { void stage(String text); }
  static String start(Access access,String id,String dt,String sdk,Progress progress)throws IOException{
    if(!dt.equals("gxlx2_p291_1g")||!sdk.equals("28")||(!id.startsWith("uid=2000(")&&!id.startsWith("uid=0(")))throw new IOException("El equipo no coincide con el primer TV P291/Android 9. No se reinició.");
    progress.stage("Guardando informe en el pendrive… Hasta 45 segundos.");
    String report=access.diagnose();
    if(!report.startsWith("Informe guardado en el pendrive:"))throw new IOException(report);
    progress.stage("Informe guardado. Verificando la ROM y el recovery del pendrive… Puede tardar hasta 3 minutos.");
    String verification=access.verifyUSB();
    if(!verification.trim().equals("TVBASE_USB_OK"))throw new IOException(verification);
    progress.stage("Archivos verificados. Solicitando modo de actualización Amlogic… No repetir el botón.");
    return report+"\n"+access.updateMode();
  }
  private EntradaAmlogic(){}
}
