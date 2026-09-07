package local.tvbase.acceso;

import java.io.IOException;
import java.util.UUID;

/** One read-only acquisition. The chosen USB directory is never rediscovered or reused. */
final class Evidencia {
  interface Access { String evidenceStep(int step,String directory,String token) throws IOException; }
  interface Progress { void stage(String text); }
  private boolean attempted;
  static void profile(String id,String dt,String sdk)throws IOException {
    if(!"gxlx2_p291_1g".equals(dt)||!"28".equals(sdk)||!id.startsWith("uid=2000("))
      throw new IOException("El equipo no coincide con el primer TV P291 / Android 9.");
  }
  static boolean validToken(String token){return token!=null&&token.matches("[0-9a-f]{32}");}
  static boolean validDirectory(String directory,String token){
    return validToken(token)&&directory!=null&&directory.matches("/(storage|mnt/media_rw)/[A-Za-z0-9_-]{1,64}/TVBASE-postintento-"+token);
  }
  String collect(Access access,String id,String dt,String sdk,Progress progress)throws IOException {
    return collect(access,id,dt,sdk,UUID.randomUUID().toString().replace("-",""),progress);
  }
  String collect(Access access,String id,String dt,String sdk,String token,Progress progress)throws IOException {
    if(attempted)throw new IOException("Esta captura ya se intentó. No se repetirá automáticamente.");
    attempted=true;profile(id,dt,sdk);
    if(!validToken(token))throw new IOException("Identificador de captura inválido.");
    progress.stage("1/11 · Creando una carpeta nueva en el pendrive TVBASE… El TV no se reiniciará.");
    String reply=access.evidenceStep(0,"",token).trim();
    if(!reply.startsWith("TVBASE_READY:"))throw new IOException(reply);
    String directory=reply.substring("TVBASE_READY:".length());
    if(!validDirectory(directory,token))throw new IOException("El pendrive devolvió una ruta inesperada.");
    String[] stages={"2/11 · Comprobando SHA y estado del arranque…","3/11 · Guardando pstore de console y pmsg…","4/11 · Leyendo logs del arranque anterior…","5/11 · Leyendo fases de cierre registradas…","6/11 · Consultando WiFi con plazo…","7/11 · Consultando Bluetooth con plazo…","8/11 · Consultando batería con plazo…","9/11 · Midiendo espacio de data y cache…","10/11 · Consultando proveedor WebView…","11/11 · Verificando los archivos guardados…"};
    for(int step=1;step<=10;step++){
      progress.stage(stages[step-1]+" El TV no se reiniciará.");
      reply=access.evidenceStep(step,directory,token).trim();
      if(!reply.equals("TVBASE_OK:"+step+":"+token))throw new IOException("Captura incompleta (etapa "+(step+1)+"): "+reply);
    }
    return "Evidencia guardada y comprobada en el pendrive:\n"+directory+"\n\nSe conservaron las denegaciones, los tiempos de espera y los códigos de salida. El recorrido completo no significa que todos los servicios respondieron. No se reinició el TV ni se abrió el actualizador. Conectá el pendrive a la PC para analizar esta carpeta.";
  }
}
