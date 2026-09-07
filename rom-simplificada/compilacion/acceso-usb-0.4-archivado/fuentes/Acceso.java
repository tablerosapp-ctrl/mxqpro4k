package local.tvbase.acceso;
import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.view.View;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.concurrent.TimeUnit;

/** Save evidence, verify the USB, then request the distinct Amlogic update boot mode. */
public class Acceso extends Activity {
  private LinearLayout list;
  private TextView info;
  private Button enter,check,report;
  private boolean accessStarted;
  private boolean updateRequested;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);list.setPadding(40,24,40,24);scroll.addView(list);setContentView(scroll);
    TextView title=new TextView(this);title.setText("Acceso al instalador de Android TV Base · 0.4");title.setTextSize(25);list.addView(title);
    TextView detail=new TextView(this);detail.setText("Conectá el pendrive TVBASE. El primer botón guarda un informe, verifica los archivos y solicita el modo de actualización Amlogic para cargar el instalador desde USB. Si aparece el menú, elegí Apply update from EXT y TVBASE-P291-A9-0.1.1-RECOVERY.zip. No necesita WiFi ni Internet.");detail.setTextSize(18);list.addView(detail);
    enter=button("Guardar informe y abrir instalador USB (reinicia)");enter.setOnClickListener(new View.OnClickListener(){public void onClick(View v){access(2);}});
    report=button("Solo guardar informe (no reinicia)");report.setOnClickListener(new View.OnClickListener(){public void onClick(View v){access(1);}});
    check=button("Ver estado del acceso");check.setOnClickListener(new View.OnClickListener(){public void onClick(View v){access(0);}});
    info=new TextView(this);info.setText("Leyendo datos de acceso…");info.setTextSize(16);info.setTextIsSelectable(true);list.addView(info);
    new Thread(new Runnable(){public void run(){
      final StringBuilder text=new StringBuilder("Android "+android.os.Build.VERSION.RELEASE+" · API "+android.os.Build.VERSION.SDK_INT+"\n");
      for(String key:new String[]{"ro.product.device","ro.product.board","ro.build.display.id","service.adb.tcp.port","persist.adb.tcp.port","ro.adb.secure"})text.append(key).append(": ").append(property(key)).append("\n");
      runOnUiThread(new Runnable(){public void run(){if(!accessStarted)info.setText(text.toString());}});
    }}).start();
  }
  private Button button(String label){Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(20);list.addView(b,new LinearLayout.LayoutParams(-1,80));return b;}
  private void access(final int action){
    accessStarted=true;
    enter.setEnabled(false);check.setEnabled(false);report.setEnabled(false);info.setText("Comprobando acceso interno y placa…");
    new Thread(new Runnable(){public void run(){String result;
      try(AdbLocal a=AdbLocal.connect()){
        String id=a.shell("id").trim(),dt=a.shell("cat /proc/device-tree/amlogic-dt-id").replace("\u0000", "").trim(),sdk=a.shell("getprop ro.build.version.sdk").trim();
        result="Acceso interno disponible\nPlaca: "+dt+"\nAndroid API: "+sdk+"\n"+id;
        if(action==2){
          result+="\n\n"+EntradaAmlogic.start(a,id,dt,sdk,new EntradaAmlogic.Progress(){public void stage(final String message){
            runOnUiThread(new Runnable(){public void run(){info.setText(message);if(message.startsWith("Archivos verificados."))updateRequested=true;}});
          }});
        }else if(action==1){if(!dt.equals("gxlx2_p291_1g")||!sdk.equals("28")||(!id.startsWith("uid=2000(")&&!id.startsWith("uid=0(")))throw new java.io.IOException("El equipo no coincide con el primer TV P291/Android 9.\n"+result);
          runOnUiThread(new Runnable(){public void run(){info.setText("Guardando informe en el pendrive… Puede tardar hasta 45 segundos. El TV no se reiniciará.");}});
          result+="\n\n"+a.diagnose();
        }else result+="\n"+a.shell("cat /proc/partitions");
      }catch(Exception e){result="No se pudo completar el acceso: "+e.getClass().getSimpleName()+" · "+e.getMessage()+"\nNo vuelvas a usar el ZIP vacío ni cambies la seguridad del TV.";}
      final String text=result;runOnUiThread(new Runnable(){public void run(){info.setText(text);check.setEnabled(true);report.setEnabled(true);enter.setEnabled(!updateRequested);}});
    }}).start();
  }
  private void addEntry(String label,final ComponentName component){
    Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(20);list.addView(b,new LinearLayout.LayoutParams(-1,70));
    try{
      ActivityInfo a=getPackageManager().getActivityInfo(component,0);
      if(!a.enabled||!a.exported||(a.permission!=null&&checkSelfPermission(a.permission)!=0))throw new SecurityException();
      b.setOnClickListener(new View.OnClickListener(){public void onClick(View v){try{startActivity(new Intent().setComponent(component));}catch(RuntimeException e){Toast.makeText(Acceso.this,"El sistema bloqueó este acceso.",1).show();}}});
    }catch(Exception e){b.setEnabled(false);b.setText(label+" — no disponible");}
  }
  private String property(String key){
    Process p=null;
    try{
      p=new ProcessBuilder("/system/bin/getprop",key).redirectErrorStream(true).start();
      if(!p.waitFor(2,TimeUnit.SECONDS)){p.destroy();return "sin respuesta";}
      BufferedReader r=new BufferedReader(new InputStreamReader(p.getInputStream()));String s=r.readLine();r.close();return s==null||s.length()==0?"no definido":s;
    }catch(Exception e){return "no accesible";}finally{if(p!=null)p.destroy();}
  }
}
