package local.tvbase.acceso;
import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Checks the exact USB ROM and opens the original local updater menu only. */
public class Acceso extends Activity {
  private TextView info;
  private Button open;
  private boolean attempted;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    attempted=state!=null&&state.getBoolean("attempted",false);
    ScrollView scroll=new ScrollView(this);LinearLayout list=new LinearLayout(this);list.setOrientation(1);list.setPadding(40,24,40,24);scroll.addView(list);setContentView(scroll);
    TextView title=new TextView(this);title.setText("Android TV Base · Actualización local · 0.7");title.setTextSize(25);list.addView(title);
    TextView detail=new TextView(this);detail.setText("Conectá el pendrive TVBASE. Este botón comprueba la ROM y abre el menú original del equipo. Instalar esta APK no instala la ROM.\n\nEn el menú original, usá Select para elegir:\n"+Entrada.ROM+"\nLuego elegí Update y confirmá en ese menú. No necesita WiFi ni Internet.");detail.setTextSize(19);list.addView(detail);
    open=new Button(this);open.setText("Abrir actualización local");open.setAllCaps(false);open.setTextSize(21);list.addView(open,new LinearLayout.LayoutParams(-1,85));open.setEnabled(!attempted);
    open.setOnClickListener(new View.OnClickListener(){public void onClick(View v){access();}});
    info=new TextView(this);info.setText(attempted?"Esta apertura ya se intentó. No se repetirá automáticamente. Para un intento manual nuevo, cerrá esta aplicación y volvé a abrirla.":"La comprobación del archivo puede tardar hasta 5 minutos. Conservá el pendrive conectado; al terminar se abrirá el menú local.");info.setTextSize(17);info.setTextIsSelectable(true);list.addView(info);
  }
  @Override public void onSaveInstanceState(Bundle state){state.putBoolean("attempted",attempted);super.onSaveInstanceState(state);}
  private void access(){
    if(attempted)return;attempted=true;open.setEnabled(false);info.setText("Comprobando el acceso interno y la placa…");
    new Thread(new Runnable(){public void run(){String result;
      try(AdbLocal a=AdbLocal.connect()){
        String id=a.shell("id").trim(),dt=a.shell("cat /proc/device-tree/amlogic-dt-id").replace("\u0000","").trim(),sdk=a.shell("getprop ro.build.version.sdk").trim();
        result=new Entrada().open(a,id,dt,sdk,new Entrada.Progress(){public void stage(final String text){runOnUiThread(new Runnable(){public void run(){info.setText(text);}});}});
      }catch(Exception e){result="No se pudo confirmar la apertura: "+e.getClass().getSimpleName()+" · "+e.getMessage()+"\n\nNo se repetirá automáticamente. Esta aplicación no selecciona el ZIP ni pulsa Update. Si apareció el menú original, la instalación requiere tu selección y confirmación allí.";}
      final String text=result;runOnUiThread(new Runnable(){public void run(){info.setText(text);}});
    }}).start();
  }
}
