package com.tvbase.reconocimiento;

import android.Manifest;
import android.app.Activity;
import android.content.*;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.opengl.*;
import android.os.*;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

public final class MainActivity extends Activity {
    private TextView state; private EditText label;private Button scan,choose,save;
    private static volatile boolean busy=false;private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private SharedPreferences prefs;private ReportArchive.Result last;
    private JSONObject webview=new JSONObject();private WebView probe;
    private String deviceId;
    void message(final String s){runOnUiThread(new Runnable(){public void run(){state.setText(s);}});}
    void running(final boolean on){busy=on;runOnUiThread(new Runnable(){public void run(){scan.setEnabled(!on);choose.setEnabled(!on);save.setEnabled(!on);label.setEnabled(!on);}});}
    Button button(LinearLayout column,String title){Button b=new Button(this);b.setText(title);b.setTextSize(18);b.setAllCaps(false);column.addView(b,new LinearLayout.LayoutParams(-1,Math.round(52*getResources().getDisplayMetrics().density)));return b;}
    public void onCreate(Bundle b){
        super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefs=getSharedPreferences("recognition",MODE_PRIVATE);deviceId=prefs.getString("device_id",null);
        if(deviceId==null){deviceId=UUID.randomUUID().toString();prefs.edit().putString("device_id",deviceId).commit();}
        LinearLayout column=new LinearLayout(this);column.setOrientation(LinearLayout.VERTICAL);column.setPadding(26,18,26,12);column.setBackgroundColor(0xff182337);
        TextView title=new TextView(this);title.setText("Reconocimiento TV Base · 0.1");title.setTextColor(0xffffffff);title.setTextSize(24);column.addView(title);
        TextView intro=new TextView(this);intro.setText("Guardá una captura por equipo. Conserva las anteriores y no instala una ROM.\nNo necesita Internet. Dejá esta aplicación abierta hasta terminar.");intro.setTextColor(0xffe1e7f0);intro.setTextSize(16);column.addView(intro);
        label=new EditText(this);label.setSingleLine(true);label.setTextColor(0xffffffff);label.setHintTextColor(0xffbfc9dc);label.setHint("Nombre opcional; se asigna automáticamente si lo dejás vacío");label.setText(prefs.getString("display_name",""));column.addView(label);
        choose=button(column,"Elegir pendrive (si no se detecta automáticamente)");scan=button(column,"Capturar y guardar este equipo");save=button(column,"Volver a guardar la última captura, sin repetir lecturas");
        ScrollView scroll=new ScrollView(this);state=new TextView(this);state.setTextColor(0xffc6eeff);state.setTextSize(17);scroll.addView(state);column.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(column);
        choose.setOnClickListener(new View.OnClickListener(){public void onClick(View v){selectUsb();}});
        scan.setOnClickListener(new View.OnClickListener(){public void onClick(View v){startCapture();}});
        save.setOnClickListener(new View.OnClickListener(){public void onClick(View v){exportLast();}});
        message("Listo. Equipo identificado en esta instalación como "+deviceId.substring(0,8)+".\nLa captura guarda hardware declarado y archivos accesibles; informa los límites. No es un respaldo completo de la ROM.");
        if(Build.VERSION.SDK_INT>=23&&checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,Manifest.permission.WRITE_EXTERNAL_STORAGE},9);
        running(busy);scan.requestFocus();
    }
    void selectUsb(){try{Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION|Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);startActivityForResult(intent,7);}catch(Exception e){message("Este Android no tiene selector de carpetas. Se intentará detectar el pendrive preparado. Detalle: "+e.getClass().getSimpleName());}}
    protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==7&&result==RESULT_OK&&data!=null&&data.getData()!=null){
        final Uri uri=data.getData();try{getContentResolver().takePersistableUriPermission(uri,data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION));}catch(Exception ignored){}
        running(true);worker.execute(new Runnable(){public void run(){try{UsbStore.preparedFolder(MainActivity.this,uri);prefs.edit().putString("usb_tree",uri.toString()).commit();message("Pendrive preparado reconocido. Ahora elegí Capturar y guardar este equipo.");}catch(Exception e){message("No se seleccionó el pendrive preparado: "+error(e));}finally{running(false);}}});}}
    static String error(Throwable e){return e.getClass().getSimpleName()+": "+String.valueOf(e.getMessage());}
    JSONObject androidInfo()throws Exception{return new JSONObject().put("api",Build.VERSION.SDK_INT).put("release",Build.VERSION.RELEASE).put("manufacturer",Build.MANUFACTURER).put("brand",Build.BRAND).put("model",Build.MODEL).put("board",Build.BOARD).put("hardware",Build.HARDWARE).put("device",Build.DEVICE).put("product",Build.PRODUCT).put("fingerprint",Build.FINGERPRINT).put("abis",new JSONArray(Arrays.asList(Build.SUPPORTED_ABIS)));}
    String dt(){for(String path:new String[]{"/proc/device-tree/amlogic-dt-id","/sys/firmware/devicetree/base/amlogic-dt-id","/proc/device-tree/compatible","/sys/firmware/devicetree/base/compatible"})try(InputStream in=new FileInputStream(path)){byte[] b=new byte[4096];int n=in.read(b);if(n>0){String value=new String(b,0,n,"UTF-8").replace('\0',' ');if(value.trim().length()>0)return value.trim();}}catch(Exception ignored){}return "";}
    static String profile(String identity){String s=identity.toLowerCase(Locale.US);if(s.matches("(?s).*\\bp291\\b.*")||s.contains("_p291_"))return "p291";if(s.matches("(?s).*\\bp271\\b.*")||s.contains("_p271_"))return "p271";
        java.util.regex.Matcher m=java.util.regex.Pattern.compile("rk[0-9]{4}[a-z0-9]*").matcher(s);if(m.find())return "rockchip-"+m.group();
        if(s.contains("rockchip")||s.contains("rk30board"))return "rockchip-desconocido";if(s.contains("amlogic")||s.contains("meson"))return "amlogic-desconocido";return "desconocido";}
    void startCapture(){
        if(busy)return;final String nickname=label.getText().toString().trim();if(nickname.length()>100){message("Usá un nombre de hasta 100 caracteres.");return;}
        prefs.edit().putString("display_name",nickname).commit();running(true);message("Preparando ficha y WebView local…");
        webview=new JSONObject();
        try{
            if(probe!=null)probe.destroy();probe=new WebView(this);probe.getSettings().setJavaScriptEnabled(false);probe.loadData("<html><body>TV Base</body></html>","text/html","UTF-8");
            webview.put("state","observed").put("scope","loaded_in_recognition_process_not_user_apk").put("user_agent",probe.getSettings().getUserAgentString());
            if(Build.VERSION.SDK_INT>=26){PackageInfo pi=WebView.getCurrentWebViewPackage();if(pi!=null)webview.put("package",pi.packageName).put("version",pi.versionName).put("version_code",pi.versionCode);else webview.put("package_state","not_available");}
            else webview.put("package_state","api_not_available");
        }catch(Throwable e){try{webview.put("state","failed").put("error",error(e));}catch(Exception ignored){}}
        final JSONObject browser=webview;
        worker.execute(new Runnable(){public void run(){
            try{
                if(getFilesDir().getUsableSpace()<100663296L)throw new IOException("Menos de 96 MB libres en Android. No se borró nada.");
                String captureId=UUID.randomUUID().toString();File captures=new File(getFilesDir(),"captures");if(!captures.exists()&&!captures.mkdir())throw new IOException("No se puede crear almacenamiento local");
                File session=new File(captures,captureId);if(!session.mkdir())throw new IOException("Captura ya existente");
                String dt=dtBounded(),profile=profile(dt+" "+Build.HARDWARE+" "+Build.BOARD+" "+Build.DEVICE);
                String name=nickname.length()>0?nickname:profile.toUpperCase(Locale.US)+" · "+deviceId.substring(0,8);
                JSONObject hardware=HardwareCollector.collect(MainActivity.this,session,new HardwareCollector.Progress(){public void update(String m){message(m);}});
                hardware.put("graphics_probe",graphicsBounded());
                JSONObject report=new JSONObject().put("schema","tvbase-recognition-1").put("capture_id",captureId).put("device_id",deviceId).put("device_id_scope","application_installation_not_proof_of_physical_identity").put("display_name",name).put("suggested_profile",profile).put("profile_confidence",profile.contains("desconocido")?"unknown":"declared").put("profile_source",dt.length()>0?"device_tree_and_android_build":"android_build").put("dt_identity",dt).put("install_authorized_by_profile",false).put("captured_wall_time_ms",System.currentTimeMillis()).put("wall_clock_trusted",false).put("uptime_ms",SystemClock.elapsedRealtime()).put("android",androidInfo()).put("hardware",hardware).put("webview",browser).put("capture_state","inventory_with_explicit_limits").put("export_limits",new JSONObject().put("full_rom_backup",false).put("root_requested",false).put("adb_used",false).put("network_permission",false).put("private_app_data_copied",false).put("protected_sources_may_be_unreadable",true).put("maximum_zip_uncompressed_bytes",ReportArchive.MAX_TOTAL).put("usb_durability","See separate export receipt; document providers may not support directory fsync"));
                message("Empaquetando y verificando los archivos capturados…");last=ReportArchive.build(session,report);
                if(!UsbStore.syncDir(last.archive.getParentFile()))throw new IOException("No se pudo acreditar el cierre del archivo local");
                if(!prefs.edit().putString("last_archive",last.archive.getAbsolutePath()).putString("last_hash",last.sha256).commit())throw new IOException("Archivo local creado, pero no se guardó su referencia");
                exportArchive(last,name);
            }catch(Throwable e){message("No se completó el guardado: "+error(e)+"\nSi se terminó la captura local, podés elegir el pendrive y usar Volver a guardar. No repitas lecturas por rutina.");}finally{running(false);}
        }});
    }
    void exportArchive(ReportArchive.Result a,String name)throws Exception {
        HardwareCollector.Progress cb=new HardwareCollector.Progress(){public void update(String m){message(m);}};
        UsbStore.Result result;String tree=prefs.getString("usb_tree","");
        if(tree.length()>0)result=UsbStore.document(this,Uri.parse(tree),a,cb);
        else {File folder=UsbStore.automatic();if(folder==null)throw new IOException("Captura local lista. Elegí el pendrive y pulsá Volver a guardar la última captura");result=UsbStore.direct(folder,a,cb);}
        message("GUARDADO Y RELEÍDO EN EL PENDRIVE\n"+name+"\n"+a.archive.getName()+" · "+(a.bytes/1048576)+" MB\nCaptura de datos accesibles; las restricciones quedan en el informe.\n"+(result.fileSynced&&result.dirSynced?"Archivos y carpeta sincronizados. ":"El proveedor no acredita toda la sincronización. ")+"Expulsá el USB desde Android antes de retirarlo. Después podés pasar al siguiente TV.");
    }
    void exportLast(){if(busy)return;running(true);worker.execute(new Runnable(){public void run(){try{
        String p=prefs.getString("last_archive","");File a=new File(p),parent=new File(getFilesDir(),"captures");
        if(p.length()==0||!a.isFile()||!a.getCanonicalFile().getParentFile().equals(parent.getCanonicalFile()))throw new IOException("Todavía no hay captura local terminada");
        String hash=ReportArchive.sha(a);if(!hash.equals(prefs.getString("last_hash","")))throw new IOException("La copia local cambió");last=new ReportArchive.Result(a,a.length(),hash);exportArchive(last,"Última captura conservada");
    }catch(Throwable e){message("No se completó la copia: "+error(e));}finally{running(false);}}});}
    String dtBounded()throws Exception {
        FutureTask<String> task=new FutureTask<String>(new Callable<String>(){public String call(){return dt();}});Thread t=new Thread(task,"recognition-profile");t.setDaemon(true);t.start();
        try{return task.get(3,TimeUnit.SECONDS);}catch(TimeoutException timeout){task.cancel(true);return "";}
    }
    static JSONObject graphicsBounded()throws Exception {
        FutureTask<JSONObject> task=new FutureTask<JSONObject>(new Callable<JSONObject>(){public JSONObject call(){return graphics();}});
        Thread t=new Thread(task,"recognition-egl");t.setDaemon(true);t.start();
        try{return task.get(6,TimeUnit.SECONDS);}catch(TimeoutException timeout){task.cancel(true);return new JSONObject().put("state","timed_out").put("scope","Client stopped waiting; a blocked driver call may continue. No retry.");}
    }
    static JSONObject graphics(){JSONObject j=new JSONObject();android.opengl.EGLDisplay d=EGL14.EGL_NO_DISPLAY;android.opengl.EGLContext c=EGL14.EGL_NO_CONTEXT;android.opengl.EGLSurface s=EGL14.EGL_NO_SURFACE;
        try{d=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);int[] versions=new int[2];if(!EGL14.eglInitialize(d,versions,0,versions,1))throw new IOException("EGL initialize");
            android.opengl.EGLConfig[] config=new android.opengl.EGLConfig[1];int[] count=new int[1];if(!EGL14.eglChooseConfig(d,new int[]{EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_PBUFFER_BIT,EGL14.EGL_NONE},0,config,0,1,count,0)||count[0]<1)throw new IOException("EGL config");
            c=EGL14.eglCreateContext(d,config[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);s=EGL14.eglCreatePbufferSurface(d,config[0],new int[]{EGL14.EGL_WIDTH,1,EGL14.EGL_HEIGHT,1,EGL14.EGL_NONE},0);
            if(!EGL14.eglMakeCurrent(d,s,s,c))throw new IOException("EGL current");j.put("state","observed").put("vendor",GLES20.glGetString(GLES20.GL_VENDOR)).put("renderer",GLES20.glGetString(GLES20.GL_RENDERER)).put("version",GLES20.glGetString(GLES20.GL_VERSION)).put("extensions",GLES20.glGetString(GLES20.GL_EXTENSIONS)).put("scope","EGL GLES2 pbuffer; no video performance claim");
        }catch(Throwable e){try{j.put("state","failed").put("error",error(e));}catch(Exception ignored){}}
        finally{if(d!=EGL14.EGL_NO_DISPLAY){EGL14.eglMakeCurrent(d,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT);if(s!=EGL14.EGL_NO_SURFACE)EGL14.eglDestroySurface(d,s);if(c!=EGL14.EGL_NO_CONTEXT)EGL14.eglDestroyContext(d,c);EGL14.eglTerminate(d);}}return j;
    }
    public void onBackPressed(){if(busy){message("Captura en curso. Conservá la aplicación abierta hasta ver el resultado.");return;}super.onBackPressed();}
    protected void onDestroy(){if(!busy)worker.shutdown();super.onDestroy();}
}
