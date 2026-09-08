package local.tvbase.gestion;

import android.Manifest;
import android.app.PendingIntent;
import android.app.job.*;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import android.system.*;
import android.util.AtomicFile;
import java.io.*;
import java.net.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.net.ssl.HttpsURLConnection;

/** HTTPS client and PackageInstaller adapter; never executes shell or changes partitions. */
public final class ManagerEngine {
    private static final AtomicBoolean BUSY = new AtomicBoolean(false);
    static final Object SESSION_LOCK = new Object();
    static final int POLL_JOB=73110, WINDOW_JOB=73111;
    public final AtomicBoolean cancelled = new AtomicBoolean(false);
    private final Context context;
    private volatile HttpsURLConnection connection;
    private final File directory;
    private final SharedPreferences state;
    public ManagerEngine(Context c) {
        context=c.getApplicationContext(); directory=new File(context.getFilesDir(),"updates");
        state=context.getSharedPreferences("updates",Context.MODE_PRIVATE);
    }
    public static UpdateCore.Policy policy(Context c) throws Exception {
        try(InputStream in=c.getAssets().open("owner.conf")) { return UpdateCore.policy(UpdateCore.readBounded(in,65536)); }
    }
    public static String status(Context c) {
        return c.getSharedPreferences("updates",0).getString("status","Sin comprobaciones realizadas.");
    }
    static void record(Context c,String message) {
        synchronized(SESSION_LOCK) {
        SharedPreferences p=c.getSharedPreferences("updates",0);
        String event=System.currentTimeMillis()+" "+message.replace('\n',' ')+"\n";
        String old=p.getString("events","");
        if(old.length()>12000) old=old.substring(old.indexOf('\n',old.length()-12000)+1);
        p.edit().putString("status",message).putString("events",old+event).commit();
        }
    }
    private void save(SharedPreferences.Editor e) throws IOException {
        UpdateCore.require(e.commit(),"No se pudo guardar el estado; operación detenida");
    }
    public void cancel() { cancelled.set(true); HttpsURLConnection c=connection; if(c!=null)c.disconnect(); }
    private void running(long deadline) throws IOException {
        UpdateCore.require(!cancelled.get() && SystemClock.elapsedRealtime()<deadline,"Operación cancelada o plazo agotado");
    }
    private void ensureDirectory() throws IOException {
        UpdateCore.require(directory.isDirectory() || directory.mkdirs(),"No se pudo crear almacenamiento privado");
    }
    private static void syncDirectory(File dir) throws Exception {
        UpdateCore.require(dir.isDirectory(),"Directorio de persistencia ausente");
        java.io.FileDescriptor fd=Os.open(dir.getAbsolutePath(),OsConstants.O_RDONLY,0);
        try { Os.fsync(fd); } finally { Os.close(fd); }
    }
    private void atomic(File file,byte[] bytes) throws Exception {
        AtomicFile a=new AtomicFile(file); FileOutputStream out=null;
        try { out=a.startWrite(); out.write(bytes); out.getFD().sync(); a.finishWrite(out); out=null; syncDirectory(directory); }
        finally { if(out!=null)a.failWrite(out); }
    }
    private HttpsURLConnection open(URI uri,long deadline) throws Exception {
        running(deadline);
        HttpsURLConnection c=(HttpsURLConnection)uri.toURL().openConnection(); connection=c;
        c.setConnectTimeout(15000); c.setReadTimeout(20000); c.setInstanceFollowRedirects(false);
        c.setUseCaches(false); c.setRequestProperty("Accept-Encoding","identity");
        c.setRequestProperty("User-Agent","TVBaseGestion/0.1");
        int status=c.getResponseCode();
        UpdateCore.require(status==200,"Servidor sin respuesta HTTP 200; no se siguen redirecciones");
        String encoding=c.getContentEncoding();
        UpdateCore.require(encoding==null || "identity".equalsIgnoreCase(encoding),"Codificación de descarga no admitida");
        return c;
    }
    private byte[] downloadManifest(UpdateCore.Policy p,long deadline) throws Exception {
        HttpsURLConnection c=null;
        try {
            c=open(p.manifest,deadline);
            try(InputStream in=c.getInputStream()) {
                ByteArrayOutputStream out=new ByteArrayOutputStream(); byte[] b=new byte[8192]; int n;
                while((n=in.read(b))!=-1) {
                    running(deadline); UpdateCore.require(out.size()<=UpdateCore.MAX_DOCUMENT-n,"Manifiesto demasiado grande");
                    out.write(b,0,n);
                }
                return out.toByteArray();
            }
        } finally { if(c!=null)c.disconnect();connection=null; }
    }
    private File downloadApk(UpdateCore.Artifact a,long deadline) throws Exception {
        File temp=new File(directory,"download.part"), target=new File(directory,"ready.apk");
        if(temp.exists())UpdateCore.require(temp.delete(),"No se pudo retirar una descarga parcial");
        StatFs fs=new StatFs(directory.getAbsolutePath());
        UpdateCore.require(fs.getAvailableBytes()>a.bytes*2+67108864L,"Espacio insuficiente para descarga e instalación");
        HttpsURLConnection c=null;
        try {
            c=open(a.url,deadline);
            long declared=c.getContentLengthLong();
            UpdateCore.require(declared<0 || declared==a.bytes,"Tamaño HTTP distinto del manifiesto");
            MessageDigest digest=MessageDigest.getInstance("SHA-256"); long total=0;
            try(InputStream in=c.getInputStream(); FileOutputStream out=new FileOutputStream(temp)) {
                byte[] b=new byte[65536]; int n;
                while((n=in.read(b))!=-1) {
                    running(deadline); UpdateCore.require(total<=a.bytes-n,"Descarga excede el tamaño firmado");
                    total+=n; digest.update(b,0,n); out.write(b,0,n);
                }
                out.getFD().sync();
            }
            UpdateCore.require(total==a.bytes && UpdateCore.hex(digest.digest()).equals(a.sha256),"Integridad de APK incorrecta");
            UpdateCore.require(temp.renameTo(target),"No se pudo conservar la descarga"); syncDirectory(directory); return target;
        } finally { if(c!=null)c.disconnect();connection=null; }
    }
    private UpdateCore.Manifest verifyManifest(byte[] data,UpdateCore.Policy p) throws Exception {
        return UpdateCore.manifest(data,p,System.currentTimeMillis()/1000L,state.getLong("sequence",0),state.getString("payloadHash",""));
    }
    private long installedVersion(String name,String certificate) throws Exception {
        try {
            PackageInfo installed=context.getPackageManager().getPackageInfo(name,PackageManager.GET_SIGNING_CERTIFICATES);
            UpdateCore.require(certificate.equals(certificate(installed)),"Certificado instalado distinto: "+name);
            return installed.getLongVersionCode();
        } catch(PackageManager.NameNotFoundException absent) { return 0; }
    }
    static String certificate(PackageInfo info) throws Exception {
        UpdateCore.require(info!=null && info.signingInfo!=null && !info.signingInfo.hasMultipleSigners(),"Se requiere un único firmante APK");
        android.content.pm.Signature[] signers=info.signingInfo.getApkContentsSigners();
        UpdateCore.require(signers!=null && signers.length==1,"Certificado APK ausente");
        return UpdateCore.sha(signers[0].toByteArray());
    }
    private void validateApk(File apk,UpdateCore.Artifact a) throws Exception {
        UpdateCore.require(apk.isFile() && apk.length()==a.bytes && UpdateCore.sha(apk).equals(a.sha256),"Descarga preparada alterada o incompleta");
        UpdateCore.ApkMetadata meta=UpdateCore.inspectApk(apk);
        UpdateCore.matchApk(a,meta,Build.VERSION.SDK_INT,Build.SUPPORTED_ABIS);
        PackageInfo pi=context.getPackageManager().getPackageArchiveInfo(apk.getAbsolutePath(),PackageManager.GET_SIGNING_CERTIFICATES);
        UpdateCore.require(pi!=null && pi.applicationInfo!=null && a.minSdk==pi.applicationInfo.minSdkVersion
                && a.packageName.equals(pi.packageName) && a.versionCode==pi.getLongVersionCode()
                && a.certificate.equals(certificate(pi)),"Firma o identidad APK no autorizada");
        UpdateCore.require(a.versionCode>installedVersion(a.packageName,a.certificate),"La versión ya está instalada o es anterior");
    }
    private boolean reconcile() throws Exception {
        synchronized(SESSION_LOCK) {
        int id=state.getInt("sessionId",-1); if(id<0)return false;
        String name=state.getString("sessionPackage",""), cert=state.getString("sessionCertificate","");
        long expected=state.getLong("sessionVersion",0);
        UpdateCore.require(expected>0,"Estado de sesión incompleto");
        if(installedVersion(name,cert)==expected) {
            save(state.edit().remove("sessionId").remove("readyPackage"));
            new File(directory,"ready.apk").delete();
            record(context,"Instalación confirmada: "+name+" versión "+expected+". La reanudación de otras aplicaciones depende de ellas.");
            return false;
        }
        PackageInstaller.SessionInfo session=context.getPackageManager().getPackageInstaller().getSessionInfo(id);
        if(session==null) {
            save(state.edit().remove("sessionId"));
            record(context,"La sesión terminó sin instalación confirmada. Se conserva el paquete para revisión."); return false;
        }
        record(context,"Hay una instalación pendiente del sistema. No se enviará otra."); return true;
        }
    }
    public boolean check(boolean automatic) {
        if(!BUSY.compareAndSet(false,true))return false;
        try {
            UpdateCore.Policy p=policy(context);
            if(!p.enabled) { record(context,"Actualizaciones sin configurar. No se realizan conexiones."); return true; }
            ensureDirectory(); if(reconcile())return true;
            long deadline=SystemClock.elapsedRealtime()+540000L;
            byte[] envelope=downloadManifest(p,Math.min(deadline,SystemClock.elapsedRealtime()+60000L));
            UpdateCore.Manifest m=verifyManifest(envelope,p);
            save(state.edit().putLong("sequence",m.sequence).putString("payloadHash",m.payloadHash));
            UpdateCore.Artifact selected=null;
            for(UpdateCore.Artifact a:m.apks) {
                if(automatic && (p.autoApps || p.autoBrowser) && !p.automaticRole(a.packageName))continue;
                try { UpdateCore.platform(a,Build.VERSION.SDK_INT,Build.SUPPORTED_ABIS); }
                catch(IOException incompatible) { continue; }
                if(a.versionCode>installedVersion(a.packageName,a.certificate)) { selected=a; break; }
            }
            if(selected==null) { record(context,"No hay una versión nueva compatible autorizada para este modo."); return true; }
            File apk=downloadApk(selected,deadline); validateApk(apk,selected);
            atomic(new File(directory,"manifest.signed"),envelope);
            save(state.edit().putString("readyPackage",selected.packageName));
            record(context,"Preparada: "+selected.packageName+" versión "+selected.versionCode+".");
            if(automatic && p.automatic(selected.packageName,System.currentTimeMillis()/1000L)) {
                if(context.checkSelfPermission(Manifest.permission.INSTALL_PACKAGES)==PackageManager.PERMISSION_GRANTED) installPrepared(p,false);
                else record(context,"Paquete preparado. Falta el permiso privilegiado para instalar a distancia.");
            }
        } catch(Exception e) { record(context,"Comprobación detenida: "+safe(e)); }
        finally { HttpsURLConnection c=connection;if(c!=null)c.disconnect();connection=null;BUSY.set(false); }
        return true;
    }
    public void installReady() {
        if(!BUSY.compareAndSet(false,true))return;
        try { UpdateCore.Policy p=policy(context);UpdateCore.require(p.enabled,"Actualizaciones sin configurar");ensureDirectory();if(!reconcile())installPrepared(p,true); }
        catch(Exception e) { record(context,"Instalación detenida: "+safe(e)); }
        finally { BUSY.set(false); }
    }
    private void installPrepared(UpdateCore.Policy p,boolean manual) throws Exception {
        String wanted=state.getString("readyPackage","");
        byte[] raw; try(InputStream in=new FileInputStream(new File(directory,"manifest.signed"))) { raw=UpdateCore.readBounded(in,UpdateCore.MAX_DOCUMENT); }
        UpdateCore.Manifest m=verifyManifest(raw,p); UpdateCore.Artifact a=null;
        for(UpdateCore.Artifact one:m.apks)if(one.packageName.equals(wanted))a=one;
        UpdateCore.require(a!=null,"No hay un paquete preparado");
        if(!manual)UpdateCore.require(p.automatic(a.packageName,System.currentTimeMillis()/1000L),"Fuera de la política o ventana de mantenimiento");
        File apk=new File(directory,"ready.apk");validateApk(apk,a);
        UpdateCore.require(!cancelled.get(),"Instalación cancelada antes de enviar");
        if(context.checkSelfPermission(Manifest.permission.INSTALL_PACKAGES)!=PackageManager.PERMISSION_GRANTED)
            UpdateCore.require(manual && context.getPackageManager().canRequestPackageInstalls(),"Autorizar este instalador desde Ajustes del equipo");
        PackageInstaller installer=context.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams params=new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        params.setAppPackageName(a.packageName);params.setSize(a.bytes);
        int id=installer.createSession(params);boolean committed=false;
        try(PackageInstaller.Session session=installer.openSession(id)) {
            MessageDigest digest=MessageDigest.getInstance("SHA-256");long total=0;
            try(InputStream in=new FileInputStream(apk);OutputStream out=session.openWrite("base.apk",0,a.bytes)) {
                byte[] b=new byte[65536];int n;
                while((n=in.read(b))!=-1){UpdateCore.require(!cancelled.get(),"Instalación cancelada");digest.update(b,0,n);total+=n;out.write(b,0,n);}
                session.fsync(out);
            }
            UpdateCore.require(total==a.bytes && UpdateCore.hex(digest.digest()).equals(a.sha256),"APK cambió al transferir a PackageInstaller");
            String token=UUID.randomUUID().toString();
            synchronized(SESSION_LOCK) {
            // Copying may take minutes: recheck the trust/time window at the actual commit boundary.
            verifyManifest(raw,p);
            UpdateCore.require(!cancelled.get(),"Instalación cancelada antes de enviar");
            if(!manual)UpdateCore.require(p.automatic(a.packageName,System.currentTimeMillis()/1000L),"Terminó la ventana de mantenimiento antes de instalar");
            save(state.edit().putInt("sessionId",id).putString("sessionToken",token).putString("sessionPackage",a.packageName)
                    .putLong("sessionVersion",a.versionCode).putString("sessionCertificate",a.certificate).putBoolean("sessionManual",manual));
            Intent result=new Intent(context,InstallReceiver.class).setAction("local.tvbase.gestion.INSTALL_RESULT");
            result.putExtra("tvbaseSession",id);result.putExtra("tvbaseToken",token);
            PendingIntent callback=PendingIntent.getBroadcast(context,id,result,PendingIntent.FLAG_UPDATE_CURRENT);
            record(context,"Paquete enviado al instalador. Esperando resultado confirmado.");
            UpdateCore.beforeCommit(m,p,a,System.currentTimeMillis()/1000L,manual,cancelled.get());
            session.commit(callback.getIntentSender());committed=true;
            }
        } finally {
            if(!committed){
                try{installer.abandonSession(id);}catch(RuntimeException ignored){}
                synchronized(SESSION_LOCK){if(state.getInt("sessionId",-1)==id)state.edit().remove("sessionId").commit();}
            }
        }
    }
    public void discard() {
        if(!BUSY.compareAndSet(false,true))return;
        try {
            synchronized(SESSION_LOCK) {
            UpdateCore.require(state.getInt("sessionId",-1)<0,"Hay una instalación pendiente");
            for(String name:new String[]{"ready.apk","download.part","manifest.signed"}) {
                File f=new File(directory,name);UpdateCore.require(!f.exists() || f.delete(),"No se pudo retirar "+name);
            }
            save(state.edit().remove("readyPackage")); record(context,"Descarga preparada eliminada. Aplicaciones y datos conservados.");
            }
        } catch(Exception e){record(context,"No se eliminó la descarga: "+safe(e));}
        finally{BUSY.set(false);}
    }
    static String safe(Exception e) { String m=e.getMessage();return m==null?e.getClass().getSimpleName():m; }
    public static void schedule(Context c) {
        schedule(c,false);
    }
    static void schedule(Context c,boolean windowConsumed) {
        JobScheduler jobs=(JobScheduler)c.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        try {
            UpdateCore.Policy p=policy(c);
            if(!p.enabled){jobs.cancel(POLL_JOB);jobs.cancel(WINDOW_JOB);return;}
            ComponentName service=new ComponentName(c,UpdateJob.class);
            PersistableBundle extras=new PersistableBundle();extras.putString("policyHash",p.fingerprint);
            JobInfo poll=jobs.getPendingJob(POLL_JOB);
            if(poll==null || !p.fingerprint.equals(poll.getExtras().getString("policyHash"))) jobs.schedule(new JobInfo.Builder(POLL_JOB,service)
                    .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setPersisted(true)
                    .setExtras(extras).setPeriodic(p.pollHours*3600000L).build());
            if(p.autoApps || p.autoBrowser) {
                JobInfo window=jobs.getPendingJob(WINDOW_JOB);
                if(window!=null && !windowConsumed && p.fingerprint.equals(window.getExtras().getString("policyHash")))return;
                Calendar now=Calendar.getInstance(TimeZone.getTimeZone("UTC"));
                Calendar next=(Calendar)now.clone();next.set(Calendar.HOUR_OF_DAY,p.maintenanceStart/60);
                next.set(Calendar.MINUTE,p.maintenanceStart%60);next.set(Calendar.SECOND,0);next.set(Calendar.MILLISECOND,0);
                if(!windowConsumed && p.window(now.getTimeInMillis()/1000L))next.setTimeInMillis(now.getTimeInMillis()+1000L);
                else if(!next.after(now))next.add(Calendar.DAY_OF_YEAR,1);
                jobs.schedule(new JobInfo.Builder(WINDOW_JOB,service).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
                        .setPersisted(true).setExtras(extras).setMinimumLatency(Math.max(1000L,next.getTimeInMillis()-now.getTimeInMillis())).build());
            } else jobs.cancel(WINDOW_JOB);
        } catch(Exception e){jobs.cancel(POLL_JOB);jobs.cancel(WINDOW_JOB);record(c,"Configuración inválida: "+safe(e));}
    }
}
