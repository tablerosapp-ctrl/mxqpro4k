package com.tvbase.reconocimiento;

import android.Manifest;
import android.app.Activity;
import android.content.*;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

public final class MainActivity extends Activity {
    private TextView state; private EditText label; private Button scan,choose,save,local;
    private static volatile boolean busy;
    private static volatile String phase="Listo. Elegí Capturar y guardar este equipo.";
    private static volatile long began;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler ui=new Handler(Looper.getMainLooper());
    private SharedPreferences prefs;
    private String deviceId;
    private final Runnable refresh=new Runnable(){public void run(){
        scan.setText("basic_checkpoint".equals(prefs.getString("last_stage",""))?"Completar inventario desde la ficha inicial":"Capturar y guardar este equipo");
        state.setText(phase+(busy?"\nTiempo transcurrido: "+((SystemClock.elapsedRealtime()-began)/1000)+" s":""));
        scan.setEnabled(!busy&&!HardwareCollector.hasPendingReads());choose.setEnabled(!busy);save.setEnabled(!busy);local.setEnabled(!busy);label.setEnabled(!busy);
        ui.postDelayed(this,1000);
    }};
    void message(String text){phase=text;}
    void running(boolean value){if(value&&!busy)began=SystemClock.elapsedRealtime();busy=value;}
    Button button(LinearLayout column,String title){Button b=new Button(this);b.setText(title);b.setTextSize(18);b.setAllCaps(false);column.addView(b,new LinearLayout.LayoutParams(-1,Math.round(52*getResources().getDisplayMetrics().density)));return b;}
    public void onCreate(Bundle saved){
        super.onCreate(saved);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefs=getSharedPreferences("recognition",MODE_PRIVATE);deviceId=prefs.getString("device_id",null);
        if(deviceId==null){deviceId=UUID.randomUUID().toString();if(!prefs.edit().putString("device_id",deviceId).commit())throw new IllegalStateException("No se pudo guardar identidad local");}
        LinearLayout column=new LinearLayout(this);column.setOrientation(LinearLayout.VERTICAL);column.setPadding(26,18,26,12);column.setBackgroundColor(0xff182337);
        TextView title=new TextView(this);title.setText("Reconocimiento TV Base · 0.3");title.setTextColor(0xffffffff);title.setTextSize(24);column.addView(title);
        TextView intro=new TextView(this);intro.setText("Primero guarda una ficha inicial; luego el inventario. Elegí USB o copia manual.\nLa copia profunda se prepara por separado desde recovery. No instala una ROM.");intro.setTextColor(0xffe1e7f0);intro.setTextSize(16);column.addView(intro);
        label=new EditText(this);label.setSingleLine(true);label.setTextColor(0xffffffff);label.setHintTextColor(0xffbfc9dc);label.setHint("Nombre opcional; la placa se identifica por sus datos");label.setText(prefs.getString("display_name",""));column.addView(label);
        choose=button(column,"Elegir pendrive (si no se detecta automáticamente)");scan=button(column,"Capturar y guardar este equipo");save=button(column,"Volver a guardar la última ficha terminada");local=button(column,"Guardar en Descargas para copiar al USB");
        ScrollView scroll=new ScrollView(this);state=new TextView(this);state.setTextColor(0xffc6eeff);state.setTextSize(17);scroll.addView(state);column.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(column);
        choose.setOnClickListener(new View.OnClickListener(){public void onClick(View v){if(!busy)selectUsb();}});
        scan.setOnClickListener(new View.OnClickListener(){public void onClick(View v){startCapture();}});
        save.setOnClickListener(new View.OnClickListener(){public void onClick(View v){exportLast();}});
        local.setOnClickListener(new View.OnClickListener(){public void onClick(View v){manualExport();}});
        if(Build.VERSION.SDK_INT>=23&&checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,Manifest.permission.WRITE_EXTERNAL_STORAGE},9);
        ui.post(refresh);scan.requestFocus();
    }
    void selectUsb(){
        if(busy)return;running(true);message("Buscando el pendrive preparado con el selector de TV Base…");
        worker.execute(new Runnable(){public void run(){try{
            final UsbLocator.Result found=UsbStore.discover();
            runOnUiThread(new Runnable(){public void run(){if(isFinishing()||isDestroyed()){message("Búsqueda terminada. Volvé a abrir Elegir pendrive en la aplicación.");return;}try{showUsbChoices(found);}catch(Exception e){message("No se pudo abrir la selección de USB: "+error(e));}}});
        }catch(Exception e){message("No se pudo buscar el USB: "+error(e)+"\nPodés guardar en Descargas para copiarlo con Archivos.");}finally{running(false);}}});
    }
    void showUsbChoices(final UsbLocator.Result found){
        String[] names=new String[found.candidates.size()];for(int i=0;i<names.length;i++)names[i]="Pendrive preparado: "+found.candidates.get(i).root;
        android.app.AlertDialog.Builder dialog=new android.app.AlertDialog.Builder(this).setTitle("Elegir pendrive desde TV Base").setNegativeButton("Cerrar",null);
        if(names.length>0&&!found.timedOut&&!found.pendingWorker){dialog.setItems(names,new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int index){
            String path=found.candidates.get(index).folder;
            if(!prefs.edit().putString("direct_usb",path).remove("usb_tree").putBoolean("manual_downloads",false).commit()){message("No se guardó la selección.");return;}
            message("Pendrive seleccionado. Pulsá Completar inventario o Volver a guardar. Si Android impide escribir, usá Guardar en Descargas.");
        }});}else dialog.setMessage("No se encontró un pendrive marcado accesible, o su consulta no terminó. La ficha local sigue conservada. Podés usar Guardar en Descargas y copiar la carpeta al USB con Archivos.");
        Intent systemPicker=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        if(systemPicker.resolveActivity(getPackageManager())!=null)dialog.setNeutralButton("Selector de Android",new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int n){systemPicker();}});
        message(UsbStore.describe(found));dialog.show();
    }
    void systemPicker(){try{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION|Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);startActivityForResult(i,7);}catch(Exception e){message("El selector de Android no está disponible. Usá el selector de TV Base o Guardar en Descargas.");}}
    void manualExport(){
        if(busy)return;
        if(!prefs.edit().putBoolean("manual_downloads",true).commit()){message("No se guardó el modo manual.");return;}
        if("basic_checkpoint".equals(prefs.getString("last_stage",""))&&!HardwareCollector.hasPendingReads())resumeInventory();
        else if(prefs.getString("last_archive","").length()>0)exportLast();
        else startCapture();
    }
    protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=7||result!=RESULT_OK||data==null||data.getData()==null||busy)return;
        final Uri uri=data.getData();try{getContentResolver().takePersistableUriPermission(uri,data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION));}catch(Exception ignored){}
        running(true);message("Comprobando el pendrive elegido…");worker.execute(new Runnable(){public void run(){try{UsbStore.preparedFolder(MainActivity.this,uri);if(!prefs.edit().putString("usb_tree",uri.toString()).remove("direct_usb").putBoolean("manual_downloads",false).commit())throw new IOException("No se guardó la carpeta");message("Pendrive reconocido. Elegí Capturar o Volver a guardar.");}catch(Exception e){message("No se reconoció el pendrive: "+error(e));}finally{running(false);}}});
    }
    static String error(Throwable e){return e.getClass().getSimpleName()+": "+String.valueOf(e.getMessage());}
    JSONObject androidInfo()throws Exception{return new JSONObject().put("api",Build.VERSION.SDK_INT).put("release",Build.VERSION.RELEASE).put("manufacturer",Build.MANUFACTURER).put("brand",Build.BRAND).put("model",Build.MODEL).put("board",Build.BOARD).put("hardware",Build.HARDWARE).put("device",Build.DEVICE).put("product",Build.PRODUCT).put("fingerprint",Build.FINGERPRINT).put("abis",new JSONArray(Arrays.asList(Build.SUPPORTED_ABIS)));}
    String dt(){for(String path:new String[]{"/proc/device-tree/amlogic-dt-id","/sys/firmware/devicetree/base/amlogic-dt-id","/proc/device-tree/compatible","/sys/firmware/devicetree/base/compatible"})try(InputStream in=new FileInputStream(path)){byte[] b=new byte[4096];int n=in.read(b);if(n>0){String value=new String(b,0,n,"UTF-8").replace('\0',' ');if(value.trim().length()>0)return value.trim();}}catch(Exception ignored){}return "";}
    static String profile(String identity){String s=identity.toLowerCase(Locale.US);if(s.matches("(?s).*\\bp291\\b.*")||s.contains("_p291_"))return "p291";if(s.matches("(?s).*\\bp271\\b.*")||s.contains("_p271_"))return "p271";
        java.util.regex.Matcher m=java.util.regex.Pattern.compile("rk[0-9]{4}[a-z0-9]*").matcher(s);if(m.find())return "rockchip-"+m.group();
        if(s.contains("rockchip")||s.contains("rk30board"))return "rockchip-desconocido";if(s.contains("amlogic")||s.contains("meson"))return "amlogic-desconocido";return "desconocido";}
    JSONObject report(String capture,String name,String profile,String dt,String stage)throws Exception {
        return new JSONObject().put("schema","tvbase-recognition-1").put("recognizer_version","0.3")
            .put("capture_id",capture).put("device_id",deviceId).put("device_id_scope","application_installation_not_proof_of_physical_identity")
            .put("display_name",name).put("suggested_profile",profile).put("profile_confidence",profile.contains("desconocido")?"unknown":"declared")
            .put("profile_source",dt.length()>0?"device_tree_and_android_build":"android_build").put("dt_identity",dt)
            .put("install_authorized_by_profile",false).put("captured_wall_time_ms",System.currentTimeMillis()).put("wall_clock_trusted",false)
            .put("uptime_ms",SystemClock.elapsedRealtime()).put("android",androidInfo()).put("capture_state",stage)
            .put("hardware",new JSONObject().put("state","not_collected_in_basic_checkpoint"))
            .put("webview",new JSONObject().put("state","not_collected_in_basic_checkpoint"))
            .put("export_limits",new JSONObject().put("full_rom_backup",false).put("root_requested",false).put("adb_used",false)
                .put("network_permission",false).put("private_app_data_copied",false).put("binary_driver_copy",false)
                .put("protected_sources_may_be_unreadable",true).put("maximum_zip_uncompressed_bytes",ReportArchive.MAX_TOTAL)
                .put("usb_durability","See separate export receipt; document providers may not support directory fsync"));
    }
    ReportArchive.Result seal(File session,JSONObject report)throws Exception {
        ReportArchive.Result a=ReportArchive.build(session,report);
        if(!UsbStore.syncDir(a.archive.getParentFile()))throw new IOException("No se acreditó cierre local");
        if(!prefs.edit().putString("last_archive",a.archive.getAbsolutePath()).putString("last_hash",a.sha256).putString("last_stage",report.getString("capture_state")).commit())throw new IOException("Archivo creado sin guardar su referencia");
        return a;
    }
    void startCapture(){
        if(busy)return;if(HardwareCollector.hasPendingReads()){message("Una consulta anterior sigue pendiente dentro de Android. Conservá la ficha guardada; no se iniciará otra lectura. Podés volver a guardarla.");return;}
        if("basic_checkpoint".equals(prefs.getString("last_stage",""))){resumeInventory();return;}
        final String nickname=label.getText().toString().trim();if(nickname.length()>100){message("Usá un nombre de hasta 100 caracteres.");return;}
        if(!prefs.edit().putString("display_name",nickname).commit()){message("No se pudo guardar el nombre.");return;}
        running(true);message("Preparando ficha inicial, sin copiar drivers…");
        worker.execute(new Runnable(){public void run(){
            final boolean[] baselineExported={false};
            try{
                if(getFilesDir().getUsableSpace()<33554432L)throw new IOException("Menos de 32 MB libres en Android. No se borró nada.");
                final File captures=new File(getFilesDir(),"captures");if(!captures.exists()&&!captures.mkdir())throw new IOException("No se puede crear almacenamiento local");
                String found="",dtState="observed";
                try{found=HardwareCollector.readBounded("profile_dt",3000,new Callable<String>(){public String call(){return dt();}});if(found.length()==0)dtState="unavailable";}catch(Exception e){dtState="unavailable_"+e.getClass().getSimpleName();}
                final String identity=found,identityState=dtState;
                final String profile=profile(identity+" "+Build.HARDWARE+" "+Build.BOARD+" "+Build.DEVICE);
                final String name=nickname.length()>0?nickname:profile.toUpperCase(Locale.US)+" · "+deviceId.substring(0,8);
                final String baselineId=UUID.randomUUID().toString();
                CaptureSequence.run(new CaptureSequence.Steps(){
                    ReportArchive.Result baseline,inventory;
                    public void saveBaseline()throws Exception {
                        File session=new File(captures,baselineId);if(!session.mkdir())throw new IOException("Ficha ya existente");
                        JSONObject basic=report(baselineId,name,profile,identity,"basic_checkpoint").put("dt_read_state",identityState);
                        message("Cerrando y verificando ficha inicial…");baseline=seal(session,basic);
                    }
                    public void exportBaseline()throws Exception {
                        exportArchive(baseline,name,false);baselineExported[0]=true;
                    }
                    public void saveInventory()throws Exception {
                        message("Ficha inicial guardada. Consultando inventario…");
                        inventory=collectInventory(report(baselineId,name,profile,identity,"basic_checkpoint").put("dt_read_state",identityState));
                    }
                    public void exportInventory()throws Exception {exportArchive(inventory,name,true);}
                });
            }catch(Throwable e){message("Guardado detenido: "+error(e)+"\n"+(baselineExported[0]?"La ficha inicial ya fue guardada en el destino elegido. ":"")+"Podés usar Volver a guardar la última ficha terminada. No se instala ni borra nada. Si Android niega el USB, usá Guardar en Descargas.");}
            finally{running(false);}
        }});
    }
    ReportArchive.Result collectInventory(JSONObject base)throws Exception {
        String id=UUID.randomUUID().toString();File session=new File(new File(getFilesDir(),"captures"),id);
        if(!session.mkdir())throw new IOException("Inventario ya existente");
        JSONObject hardware=HardwareCollector.collect(MainActivity.this,session,new HardwareCollector.Progress(){public void update(String text){message("Ficha inicial guardada.\n"+text);}});
        hardware.put("graphics_probe",new JSONObject().put("state","deferred").put("reason","No EGL driver initialization in fast recognition; declared capabilities are recorded."));
        JSONObject full=report(id,base.getString("display_name"),base.getString("suggested_profile"),base.getString("dt_identity"),"inventory_with_explicit_limits")
            .put("parent_capture_id",base.getString("capture_id")).put("dt_read_state",base.optString("dt_read_state","unknown"))
            .put("hardware",hardware).put("webview",browserInfo()).put("outstanding_read",HardwareCollector.hasPendingReads())
            .put("usb_discovery",UsbStore.lastDiscovery()).put("export_method_requested",prefs.getBoolean("manual_downloads",false)?"local_manual_copy":"usb");
        message("Cerrando inventario. La ficha inicial ya está conservada…");return seal(session,full);
    }
    ReportArchive.Result lastArchive()throws Exception {
        String path=prefs.getString("last_archive","");File a=new File(path),parent=new File(getFilesDir(),"captures");
        if(path.length()==0||!a.isFile()||!a.getCanonicalFile().getParentFile().equals(parent.getCanonicalFile()))throw new IOException("No hay ficha local terminada");
        String sha=ReportArchive.sha(a);if(!sha.equals(prefs.getString("last_hash","")))throw new IOException("La copia local cambió");
        return new ReportArchive.Result(a,a.length(),sha);
    }
    JSONObject readBaseline(ReportArchive.Result archive)throws Exception {
        try(java.util.zip.ZipFile zip=new java.util.zip.ZipFile(archive.archive)){
            java.util.zip.ZipEntry entry=zip.getEntry("informe.json");if(entry==null||entry.getSize()<1||entry.getSize()>1048576)throw new IOException("Ficha inicial inválida");
            ByteArrayOutputStream out=new ByteArrayOutputStream();
            try(InputStream in=zip.getInputStream(entry)){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>1048576)throw new IOException("Ficha inicial excesiva");out.write(b,0,n);}}
            JSONObject base=new JSONObject(new String(out.toByteArray(),"UTF-8"));
            if(!"basic_checkpoint".equals(base.getString("capture_state"))||!("0.2".equals(base.getString("recognizer_version"))||"0.3".equals(base.getString("recognizer_version")))||!deviceId.equals(base.getString("device_id")))throw new IOException("La ficha no corresponde a esta instalación");
            return base;
        }
    }
    void resumeInventory(){
        running(true);message("Verificando ficha inicial conservada, sin repetir su lectura…");
        worker.execute(new Runnable(){public void run(){try{
            ReportArchive.Result basic=lastArchive();JSONObject base=readBaseline(basic);
            exportArchive(basic,base.getString("display_name"),false);
            ReportArchive.Result inventory=collectInventory(base);exportArchive(inventory,base.getString("display_name"),true);
        }catch(Throwable e){message("No se completó el inventario: "+error(e)+"\nLa ficha inicial permanece conservada. Podés volver a guardar la última ficha terminada.");}finally{running(false);}}});
    }
    JSONObject browserInfo()throws Exception {
        try{return HardwareCollector.readBounded("webview_package",6000,new Callable<JSONObject>(){public JSONObject call()throws Exception {
            JSONObject j=new JSONObject().put("scope","framework_selected_package_without_loading_webview_not_user_apk");
            if(Build.VERSION.SDK_INT<26)return j.put("state","api_not_available");
            PackageInfo p=WebView.getCurrentWebViewPackage();
            if(p==null)return j.put("state","unavailable");
            return j.put("state","observed").put("package",p.packageName).put("version",p.versionName).put("version_code",p.versionCode);
        }});}catch(Exception e){return new JSONObject().put("state","unavailable").put("error_type",e.getClass().getSimpleName());}
    }
    void exportArchive(ReportArchive.Result a,String name,boolean terminal)throws Exception {
        if(prefs.getBoolean("manual_downloads",false)){
            message("Guardando copia local en Descargas; todavía no está en USB…");
            File downloads=Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getCanonicalFile();
            if(!downloads.exists()&&!downloads.mkdir())throw new IOException("Android no permite crear Descargas");
            LocalExport.Result localResult=LocalExport.save(downloads,a);
            if(terminal)message("GUARDADO LOCAL PARA COPIAR AL USB\n"+("basic_checkpoint".equals(prefs.getString("last_stage",""))?"Ficha inicial; el inventario puede quedar pendiente.\n":"Inventario con límites de acceso.\n")+name+"\n"+localResult.zip.getAbsolutePath()+"\nAbrí Archivos y copiá la carpeta TVBASE-PARA-COPIAR completa desde Descargas al pendrive. Esta copia local NO acredita guardado en USB."+(HardwareCollector.hasPendingReads()?"\nUna consulta de Android sigue pendiente; no se iniciará otra captura.":""));
            return;
        }
        final boolean initial="basic_checkpoint".equals(prefs.getString("last_stage",""));
        final String prefix=initial?"Guardando ficha inicial":"Guardando inventario";
        HardwareCollector.Progress cb=new HardwareCollector.Progress(){public void update(String m){message(prefix+"\n"+m);}};
        message(prefix+"…");UsbStore.Result result;String tree=prefs.getString("usb_tree","");
        if(tree.length()>0)result=UsbStore.document(this,Uri.parse(tree),a,cb);
        else{UsbLocator.Candidate target=UsbStore.automatic(prefs.getString("direct_usb",""));if(target==null)throw new IOException("Ficha local lista. Usá Elegir pendrive desde TV Base, o Guardar en Descargas para copiar al USB");result=UsbStore.direct(target,a,cb);}
        if(terminal)message((initial?"FICHA INICIAL GUARDADA Y RELEÍDA\n":"INVENTARIO GUARDADO Y RELEÍDO\n")+name+"\n"+a.archive.getName()+" · "+a.bytes+" bytes\nInventario con límites; no es una copia de la ROM.\n"+(result.fileSynced&&result.dirSynced?"Archivos y carpeta sincronizados. ":"El proveedor no acredita toda la sincronización. ")+(initial?"Para seguir, pulsá Completar inventario desde la ficha inicial. ":"")+"Expulsá el USB desde Android antes de retirarlo."+(HardwareCollector.hasPendingReads()?"\nUna consulta de Android sigue pendiente: no se repetirán lecturas.":""));
    }
    void exportLast(){if(busy)return;running(true);message("Verificando la última ficha local…");worker.execute(new Runnable(){public void run(){try{
        String p=prefs.getString("last_archive","");File a=new File(p),parent=new File(getFilesDir(),"captures");
        if(p.length()==0||!a.isFile()||!a.getCanonicalFile().getParentFile().equals(parent.getCanonicalFile()))throw new IOException("Todavía no hay ficha local terminada");
        String h=ReportArchive.sha(a);if(!h.equals(prefs.getString("last_hash","")))throw new IOException("La copia local cambió");
        exportArchive(new ReportArchive.Result(a,a.length(),h),"Última ficha conservada (puede ser inicial)",true);
    }catch(Throwable e){message("No se completó la copia: "+error(e));}finally{running(false);}}});}
    public void onBackPressed(){if(busy){message("La tarea sigue en curso. Esperá el resultado; el tiempo transcurrido sigue visible.");return;}super.onBackPressed();}
    protected void onDestroy(){ui.removeCallbacks(refresh);worker.shutdown();super.onDestroy();}
}
