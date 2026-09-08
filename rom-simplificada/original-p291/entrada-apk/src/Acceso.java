package local.tvbase.acceso;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.IOException;
import java.util.UUID;

/** Explicit USB preparation. No background entry, broadcast receiver or reboot API. */
public final class Acceso extends Activity {
    private TextView info;private Button prepare,observe;private SharedPreferences prefs;private boolean observing;
    @Override public void onCreate(Bundle saved){super.onCreate(saved);prefs=getSharedPreferences("entry09",MODE_PRIVATE);
        ScrollView scroll=new ScrollView(this);LinearLayout list=new LinearLayout(this);list.setOrientation(1);list.setPadding(40,24,40,24);scroll.addView(list);setContentView(scroll);
        TextView title=new TextView(this);title.setText("Preparar instalación por USB · TV Base · 0.9");title.setTextSize(25);list.addView(title);
        TextView details=new TextView(this);details.setText("Conectá el pendrive TVBASE con la ROM 0.2.1. Esta preparación verifica la ROM, guarda el estado de arranque y programa una entrada de un solo uso al menú recovery. Reemplaza las órdenes de actualización anteriores. No instala la ROM ni reinicia automáticamente. No necesita WiFi ni Internet.");details.setTextSize(18);list.addView(details);
        prepare=new Button(this);prepare.setText("Preparar entrada a recovery");prepare.setAllCaps(false);prepare.setTextSize(21);list.addView(prepare,new LinearLayout.LayoutParams(-1,95));
        prepare.setEnabled(EntryPolicy.METHOD_REVIEWED&&!prefs.getBoolean("attempted",false));prepare.setOnClickListener(new View.OnClickListener(){public void onClick(View v){confirm();}});
        observe=new Button(this);observe.setText("Ver estado de esta preparación");observe.setAllCaps(false);list.addView(observe,new LinearLayout.LayoutParams(-1,85));
        observe.setEnabled(prefs.getString("nonce","").matches("[0-9a-f]{32}"));observe.setOnClickListener(new View.OnClickListener(){public void onClick(View v){monitor(false,prefs.getString("nonce",""));}});
        info=new TextView(this);info.setTextSize(17);info.setTextIsSelectable(true);list.addView(info);
        info.setText(prefs.getString("last","Preparado para verificar el pendrive. La operación puede tardar varios minutos; conservá la alimentación y el USB conectados."));
        if(!EntryPolicy.METHOD_REVIEWED)info.setText("Compilación de revisión: la modificación de ENV/BCB está deshabilitada.");
        else if(prefs.getBoolean("attempted",false))info.append("\n\nEsta preparación ya se intentó. No se repetirá automáticamente. Si quedó incompleta, conservá el pendrive y revisá el informe desde la PC.");
    }
    private void confirm(){new AlertDialog.Builder(this).setTitle("Modificar el arranque del primer P291")
        .setMessage("Se guardarán copias de ENV y BCB en el pendrive y se modificarán sus datos de arranque. Una interrupción o un fallo al escribir ENV puede impedir iniciar Android; la restauración por USB no está probada.\n\nEl siguiente encendido intentará abrir recovery y restablecer el arranque normal antes. La instalación de la ROM será un paso posterior y borrará los datos internos mediante su instalador.\n\nNo desconectes la alimentación durante la preparación. ¿Preparar ahora?")
        .setNegativeButton("Volver",null).setPositiveButton("Preparar",new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int which){start();}}).show();}
    private void start(){if(prefs.getBoolean("attempted",false))return;prepare.setEnabled(false);
        final String nonce=UUID.randomUUID().toString().replace("-","");
        if(!prefs.edit().putBoolean("attempted",true).putString("nonce",nonce).putString("last","Preparación iniciada; esperando estado.").commit()){info.setText("No se pudo guardar el estado de la aplicación. No se inició la preparación.");return;}
        info.setText("Comprobando acceso interno… Conservá la alimentación y el pendrive conectados.");
        observe.setEnabled(true);monitor(true,nonce);}
    private void monitor(final boolean launch,final String nonce){
        if(observing||!nonce.matches("[0-9a-f]{32}"))return;observing=true;observe.setEnabled(false);prepare.setEnabled(false);
        final String apk=getApplicationInfo().sourceDir;
        new Thread(new Runnable(){public void run(){String result;
            try{
                if(launch){JSONObject started=call(apk,nonce,"launch");if(!started.getString("state").equals("launched"))throw new IOException("No se confirmó lanzamiento: "+started.optString("error"));}
                long deadline=System.nanoTime()+1200000000000L;int failures=0;JSONObject terminal=null;
                while(System.nanoTime()<deadline){
                    try{JSONObject current=call(apk,nonce,"status");failures=0;String state=current.getString("state");
                        if(state.equals("incomplete"))throw new TerminalFailure(current.optString("error")+"\nInforme: "+current.optString("report","estado interno"));
                        if(state.equals("prepared")){terminal=current;break;}
                        if(!state.equals("stage"))throw new TerminalFailure("Estado no reconocido: "+state);
                    }catch(TerminalFailure stop){throw stop;}catch(IOException transientRead){
                        if(++failures>=5)throw transientRead;update("Esperando confirmación del proceso independiente… No se repetirá ni se cancelará la preparación.");
                    }
                    Thread.sleep(2000);
                }
                if(terminal==null)throw new IOException("Se agotó el plazo de observación; el proceso podría continuar");
                if(!terminal.getBoolean("env_readback_verified")||!terminal.getBoolean("bcb_readback_verified")||!terminal.getString("manifest_sha256").matches("[0-9a-f]{64}"))throw new IOException("Falta verificación final del arranque");
                result="Preparación guardada y leída. La ROM todavía no se instaló.\n\nDesconectá la alimentación durante 10 segundos y volvé a conectarla, manteniendo el pendrive. El siguiente arranque intentará abrir recovery; puede no mostrar imagen si la entrada falla.\n\nSi aparece recovery, elegí instalar desde USB y seleccioná "+EntryPolicy.ZIP_NAME+". Si el control remoto no responde, usá un teclado USB. No selecciones paquetes antiguos. Si no aparece o muestra un error, no repitas la preparación: conservá el mensaje y el pendrive.\n\nInforme: "+terminal.getString("report");
            }catch(Exception e){result="Preparación incompleta o sin confirmación: "+e.getClass().getSimpleName()+" · "+e.getMessage()+"\n\nNo se solicitó reinicio. No cortes la alimentación ni vuelvas a preparar hasta revisar el informe: ENV/BCB podrían haber quedado modificados. La pérdida de conexión o un plazo vencido no detienen el proceso independiente. Conservá el pendrive conectado. Podés consultar nuevamente el estado.";}
            final String text=result;prefs.edit().putString("last",text).commit();runOnUiThread(new Runnable(){public void run(){observing=false;if(!isFinishing()){info.setText(text);observe.setEnabled(true);}}});
        }}).start();
    }
    private static final class TerminalFailure extends IOException{TerminalFailure(String message){super(message);}}
    private JSONObject call(String apk,final String nonce,String operation)throws Exception{
        final JSONObject[] last={null};final boolean[] exitSeen={false};
        try(AdbLocal adb=AdbLocal.connect()){
            adb.call(apk,nonce,operation,new AdbLocal.Progress(){public void line(String line)throws IOException{
                try{
                    if(line.startsWith("TVBASE_ENTRY:")){
                        if(exitSeen[0])throw new IOException("Respuesta posterior al código final");
                        JSONObject obj=new JSONObject(line.substring(13));if(!nonce.equals(obj.getString("nonce")))throw new IOException("Nonce de respuesta diferente");
                        String state=obj.getString("state");if(!state.equals("stage")&&!state.equals("launched")&&!state.equals("prepared")&&!state.equals("incomplete"))throw new IOException("Estado inesperado");
                        if(last[0]!=null&&!last[0].getString("state").equals("stage"))throw new IOException("Dos resultados terminales");last[0]=obj;
                        if(state.equals("stage"))update(obj.optString("phase")+"\nConservá la alimentación y el USB conectados.");
                    }else if(line.startsWith("TVBASE_EXIT:")){
                        if(exitSeen[0]||!line.equals("TVBASE_EXIT:"+nonce+":0"))throw new IOException("El comando no terminó correctamente: "+line+(last[0]==null?"":"\n"+last[0].optString("error")));exitSeen[0]=true;
                    }
                }catch(IOException e){throw e;}catch(Exception e){throw new IOException("Respuesta no interpretable",e);}
            }});
        }
        if(!exitSeen[0]||last[0]==null)throw new IOException("Falta resultado y código remoto verificados");return last[0];
    }
    private void update(final String text){runOnUiThread(new Runnable(){public void run(){if(!isFinishing())info.setText(text);}});}
}
