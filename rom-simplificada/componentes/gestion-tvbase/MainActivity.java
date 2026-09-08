package local.tvbase.gestion;
import android.Manifest;
import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.*;

public final class MainActivity extends Activity {
    private TextView status; private ManagerEngine engine;
    @Override public void onCreate(Bundle saved){super.onCreate(saved);engine=new ManagerEngine(this);render();ManagerEngine.schedule(this);}
    @Override public void onResume(){super.onResume();if(status!=null)refresh();}
    private void render(){
        ScrollView scroll=new ScrollView(this);LinearLayout body=new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);body.setPadding(40,24,40,24);body.setBackgroundColor(Color.rgb(19,25,34));
        scroll.addView(body);setContentView(scroll);
        TextView title=new TextView(this);title.setText("Actualizaciones TV Base");title.setTextSize(26);title.setTextColor(Color.WHITE);body.addView(title);
        status=new TextView(this);status.setTextColor(Color.WHITE);status.setTextSize(18);status.setPadding(0,16,0,20);body.addView(status);
        Button first=button(body,"Buscar y preparar actualización",new Runnable(){public void run(){background(false);}});
        button(body,"Instalar actualización preparada",new Runnable(){public void run(){background(true);}});
        button(body,"Eliminar solamente la descarga preparada",new Runnable(){public void run(){engine.discard();refresh();}});
        button(body,"Ajustes del equipo",new Runnable(){public void run(){startActivity(new Intent(Settings.ACTION_SETTINGS));}});
        button(body,"Permiso de instalación local",new Runnable(){public void run(){
            startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+getPackageName())));
        }});
        first.requestFocus();refresh();
    }
    private Button button(LinearLayout body,String label,final Runnable r){
        Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(18);body.addView(b,new LinearLayout.LayoutParams(-1,64));
        b.setOnClickListener(new View.OnClickListener(){public void onClick(View v){try{r.run();}catch(RuntimeException e){Toast.makeText(MainActivity.this,"Función no disponible en este equipo.",Toast.LENGTH_LONG).show();}}});return b;
    }
    private void background(final boolean install){
        status.setText("Trabajando. Podés volver a Inicio; el resultado quedará guardado.");
        new Thread(new Runnable(){public void run(){
            if(install)engine.installReady();else engine.check(false);
            runOnUiThread(new Runnable(){public void run(){if(!isFinishing())refresh();}});
        }},"tvbase-update").start();
    }
    private void refresh(){
        String config;
        try{
            UpdateCore.Policy p=ManagerEngine.policy(this);
            config=p.enabled?"Servidor del dueño configurado. Mantenimiento en UTC; las descargas y actualizaciones requieren conexión."
                    :"Sin servidor configurado. No se realizan conexiones ni actualizaciones automáticas.";
        }catch(Exception e){config="Configuración inválida. Actualizaciones detenidas.";}
        boolean privileged=checkSelfPermission(Manifest.permission.INSTALL_PACKAGES)==PackageManager.PERMISSION_GRANTED;
        status.setText(config+"\n"+(privileged?"Permiso de instalación remota concedido.":"Instalación remota no habilitada; la instalación local requiere permiso y confirmación del sistema.")
                +"\nActualizar el navegador puede cerrar aplicaciones que usan WebView. No se garantiza reanudar video.\n\n"+ManagerEngine.status(this));
    }
}
