package local.tvbase.inicio;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;

/** Small offline home screen. It has no service, account, network or update permission. */
public class Inicio extends Activity {
    private LinearLayout list;
    private int dp(int n) { return (int)(getResources().getDisplayMetrics().density*n+0.5f); }
    @Override public void onCreate(Bundle state) { super.onCreate(state); }
    @Override public void onResume() { super.onResume(); render(); }
    private void render() {
        ScrollView scroll = new ScrollView(this);
        list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(dp(48),dp(24),dp(48),dp(24));
        list.setBackgroundColor(Color.rgb(19,25,34));
        scroll.setFillViewport(true); scroll.addView(list); setContentView(scroll);
        TextView title = new TextView(this); title.setText("Inicio TV");
        title.setTextSize(28); title.setTextColor(Color.WHITE); list.addView(title);
        TextView hint = new TextView(this); hint.setText("Elegí una aplicación con las flechas y Aceptar.");
        hint.setTextSize(16); hint.setPadding(0,dp(6),0,dp(14)); list.addView(hint);
        Button settings = button("Ajustes del equipo", new Runnable() { public void run() { openSettings(); }});
        PackageManager pm = getPackageManager();
        List<ResolveInfo> apps = new ArrayList<ResolveInfo>();
        for (String category : new String[]{Intent.CATEGORY_LEANBACK_LAUNCHER,Intent.CATEGORY_LAUNCHER}) {
            apps.addAll(pm.queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(category),0));
        }
        Collections.sort(apps,new Comparator<ResolveInfo>() { public int compare(ResolveInfo a,ResolveInfo b) {
            return a.loadLabel(getPackageManager()).toString().compareToIgnoreCase(b.loadLabel(getPackageManager()).toString());
        }});
        HashSet<String> seen = new HashSet<String>();
        for (final ResolveInfo info : apps) {
            if (!info.activityInfo.exported || info.activityInfo.packageName.equals(getPackageName()) || !seen.add(info.activityInfo.packageName)) continue;
            button(info.loadLabel(pm).toString(), new Runnable() { public void run() {
                launch(new Intent(Intent.ACTION_MAIN).setClassName(info.activityInfo.packageName,info.activityInfo.name)
                       .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED));
            }});
        }
        settings.requestFocus();
    }
    private Button button(String label, final Runnable action) {
        Button b=new Button(this); b.setText(label); b.setAllCaps(false); b.setTextSize(20);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(60)); lp.bottomMargin=dp(6);
        list.addView(b,lp); b.setOnClickListener(new View.OnClickListener(){ public void onClick(View v){action.run();}}); return b;
    }
    private void openSettings() {
        // Resolve exported settings activities instead of assuming the vendor's class names.
        Intent base=new Intent(Settings.ACTION_SETTINGS).setPackage("tv.icntv.vendor");
        if(getPackageManager().resolveActivity(base,0)!=null){launch(base);return;}
        Intent vendor=getPackageManager().getLaunchIntentForPackage("tv.icntv.vendor");
        if(vendor!=null){launch(vendor);return;}
        launch(new Intent(Settings.ACTION_SETTINGS));
    }
    private void launch(Intent intent) {
        try { startActivity(intent); }
        catch (RuntimeException e) { Toast.makeText(this,"No se pudo abrir esta función.",Toast.LENGTH_LONG).show(); }
    }
    @Override public void onBackPressed() { /* The home screen stays available. */ }
}
