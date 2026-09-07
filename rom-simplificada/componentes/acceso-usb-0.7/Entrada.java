package local.tvbase.acceso;
import java.io.IOException;
import java.util.UUID;

/** One explicit menu opening; every failure stops and no destination is retried. */
final class Entrada {
  static final String ROM="TVBASE-P291-A9-0.1.1-RECOVERY.zip";
  interface Access { String entryStep(int step,String directory,String token)throws IOException; }
  interface Progress { void stage(String text); }
  private boolean attempted;
  static void profile(String id,String dt,String sdk)throws IOException {
    if(!"gxlx2_p291_1g".equals(dt)||!"28".equals(sdk)||id==null||!id.startsWith("uid=2000("))
      throw new IOException("El acceso no coincide con UID shell / primer TV P291 / Android 9.");
  }
  static boolean validToken(String token){return token!=null&&token.matches("[0-9a-f]{32}");}
  static boolean validDirectory(String directory){return directory!=null&&directory.matches("/(storage|mnt/media_rw)/[A-Za-z0-9_-]{1,64}")&&!directory.equals("/storage/emulated")&&!directory.equals("/storage/self");}
  String open(Access access,String id,String dt,String sdk,Progress progress)throws IOException{return open(access,id,dt,sdk,UUID.randomUUID().toString().replace("-",""),progress);}
  String open(Access access,String id,String dt,String sdk,String token,Progress progress)throws IOException {
    if(attempted)throw new IOException("Esta apertura ya se intentó.");attempted=true;
    profile(id,dt,sdk);if(!validToken(token))throw new IOException("Identificador inválido.");
    progress.stage("Localizando el pendrive TVBASE…");
    String result=access.entryStep(0,"",token).trim();
    if(!result.startsWith("TVBASE_MEDIA:"))throw new IOException(result);
    String directory=result.substring("TVBASE_MEDIA:".length());
    if(!validDirectory(directory))throw new IOException("Ruta de pendrive inesperada.");
    progress.stage("Comprobando la ROM completa y el actualizador original… Puede tardar hasta 5 minutos. Al terminar se abrirá el menú local; mantené el pendrive conectado.");
    result=access.entryStep(1,directory,token).trim();
    if(!result.equals("TVBASE_OPEN_OK:"+token))throw new IOException(result);
    return "Menú local abierto. Elegí Select → "+ROM+" → Update y confirmá en el menú original. Esta APK todavía no instaló la ROM.";
  }
}
