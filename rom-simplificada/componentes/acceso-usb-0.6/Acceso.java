package local.tvbase.acceso;
import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Diagnostic-only UI: no updater activity, reboot service, root request or flash path. */
public class Acceso extends Activity {
  private TextView info;
  private Button collect,check;
  private boolean attempted;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    attempted=state!=null&&state.getBoolean("attempted",false);
    ScrollView scroll=new ScrollView(this);LinearLayout list=new LinearLayout(this);list.setOrientation(1);list.setPadding(40,24,40,24);scroll.addView(list);setContentView(scroll);
    TextView title=new TextView(this);title.setText("Archivos pendientes de Android TV Base · 0.6");title.setTextSize(25);list.addView(title);
    TextView detail=new TextView(this);detail.setText("Conectá el pendrive TVBASE. Esta versión completa lo que faltó: el actualizador OTA del equipo, sus certificados públicos y la configuración de arranque. Comprueba los hashes antes de informar éxito. No reinicia, no abre el actualizador y no instala la ROM. No necesita WiFi ni Internet.");detail.setTextSize(18);list.addView(detail);
    collect=button(list,"Guardar archivos que faltan (no reinicia)");collect.setEnabled(!attempted);collect.setOnClickListener(new View.OnClickListener(){public void onClick(View v){access(true);}});
    check=button(list,"Ver estado del acceso");check.setOnClickListener(new View.OnClickListener(){public void onClick(View v){access(false);}});
    info=new TextView(this);info.setText(attempted?"Esta captura ya se intentó. Conservá cualquier carpeta TVBASE-evidencia del pendrive. No se repetirá automáticamente.":"Android "+android.os.Build.VERSION.RELEASE+" · API "+android.os.Build.VERSION.SDK_INT+"\nPreparado para leer evidencia sin reiniciar. Cada etapa tiene un límite de 90 segundos.");info.setTextSize(16);info.setTextIsSelectable(true);list.addView(info);
  }
  @Override public void onSaveInstanceState(Bundle state){state.putBoolean("attempted",attempted);super.onSaveInstanceState(state);}
  private Button button(LinearLayout list,String text){Button b=new Button(this);b.setText(text);b.setAllCaps(false);b.setTextSize(20);list.addView(b,new LinearLayout.LayoutParams(-1,85));return b;}
  private void access(final boolean save){
    if(save&&attempted)return;
    if(save)attempted=true;
    collect.setEnabled(false);check.setEnabled(false);info.setText("Comprobando acceso interno y placa… El TV seguirá encendido.");
    new Thread(new Runnable(){public void run(){String result;
      try(AdbLocal a=AdbLocal.connect()){
        String id=a.shell("id").trim(),dt=a.shell("cat /proc/device-tree/amlogic-dt-id").replace("\u0000","").trim(),sdk=a.shell("getprop ro.build.version.sdk").trim();
        Evidencia.profile(id,dt,sdk);
        if(save)result=new Evidencia().collect(a,id,dt,sdk,new Evidencia.Progress(){public void stage(final String text){runOnUiThread(new Runnable(){public void run(){info.setText(text+"\nHasta 90 segundos por etapa. Conservá el pendrive conectado.");}});}});
        else result="Acceso interno disponible\nPlaca: "+dt+"\nAndroid API: "+sdk+"\n"+id+"\n"+a.shell("cat /proc/partitions");
      }catch(Exception e){result="No se pudo completar la lectura: "+e.getClass().getSimpleName()+" · "+e.getMessage()+"\n\nConservá la carpeta parcial del pendrive y este mensaje. No se solicitó ningún reinicio ni instalación.";}
      final String text=result;runOnUiThread(new Runnable(){public void run(){info.setText(text);check.setEnabled(true);collect.setEnabled(!attempted);}});
    }}).start();
  }
}
