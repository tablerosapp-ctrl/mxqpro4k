package local.tvbase.gestion;
import android.content.*;
import android.content.pm.*;
public final class InstallReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c,Intent intent){
        synchronized(ManagerEngine.SESSION_LOCK) {
        SharedPreferences p=c.getSharedPreferences("updates",0);
        int id=p.getInt("sessionId",-1);
        if(id<0 || id!=intent.getIntExtra("tvbaseSession",-2)
                || !p.getString("sessionToken","").equals(intent.getStringExtra("tvbaseToken")))return;
        int status=intent.getIntExtra(PackageInstaller.EXTRA_STATUS,PackageInstaller.STATUS_FAILURE);
        if(status==PackageInstaller.STATUS_PENDING_USER_ACTION){
            if(p.getBoolean("sessionManual",false)){
                Intent confirm=intent.getParcelableExtra(Intent.EXTRA_INTENT);
                if(confirm!=null){confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);try{c.startActivity(confirm);return;}catch(RuntimeException ignored){}}
            }
            try{c.getPackageManager().getPackageInstaller().abandonSession(id);}catch(RuntimeException ignored){}
            p.edit().remove("sessionId").commit();ManagerEngine.record(c,"El sistema exige confirmación local. No se completó la instalación remota.");return;
        }
        if(status==PackageInstaller.STATUS_SUCCESS){
            try{
                PackageInfo actual=c.getPackageManager().getPackageInfo(p.getString("sessionPackage",""),PackageManager.GET_SIGNING_CERTIFICATES);
                if(actual.getLongVersionCode()==p.getLong("sessionVersion",0)
                        && ManagerEngine.certificate(actual).equals(p.getString("sessionCertificate",""))){
                    p.edit().remove("sessionId").remove("readyPackage").commit();
                    new java.io.File(c.getFilesDir(),"updates/ready.apk").delete();
                    ManagerEngine.record(c,"Instalación confirmada: "+actual.packageName+" versión "+actual.getLongVersionCode()+". No se fuerza la apertura de otras aplicaciones.");
                    return;
                }
            }catch(Exception ignored){}
            ManagerEngine.record(c,"El instalador informó éxito, pero falta confirmar versión y certificado. Se conserva la sesión para revisión.");return;
        }
        p.edit().remove("sessionId").commit();
        ManagerEngine.record(c,"El sistema no instaló la actualización. Código "+status+". La descarga se conserva para revisión.");
        }
    }
}
