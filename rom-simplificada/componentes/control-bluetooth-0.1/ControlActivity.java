package com.tvbase.bluetoothcontrol;

import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.util.UUID;

/** Ordinary Android 9 Bluetooth API; no shell, network, root or hidden API. */
public final class ControlActivity extends Activity {
    private static Controller controller;
    private Button disableButton, restoreButton;
    private TextView report;
    private final Runnable refresh = new Runnable() { public void run() { render(); } };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (controller == null) controller = new Controller(getApplicationContext());
        ScrollView scroll = new ScrollView(this);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(36, 24, 36, 24);
        scroll.addView(column); setContentView(scroll);
        TextView title = new TextView(this);
        title.setText("Control Bluetooth · TV Base · 0.1"); title.setTextSize(25); column.addView(title);
        TextView detail = new TextView(this);
        detail.setText("Desactivar solicita apagar Bluetooth y guarda esa preferencia para los siguientes arranques. Restaurar solicita volver a encenderlo. Es un cambio reversible del ajuste; no reinicia ni instala la ROM. Abrir esta pantalla no cambia Bluetooth.");
        detail.setTextSize(18); column.addView(detail);
        disableButton = button(column, "Desactivar Bluetooth");
        restoreButton = button(column, "Restaurar Bluetooth");
        disableButton.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { controller.request("desactivar"); } });
        restoreButton.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { controller.request("restaurar"); } });
        report = new TextView(this); report.setTextSize(16); report.setTextIsSelectable(true); column.addView(report);
        controller.listener = refresh;
        render();
        // A recreated Activity must never replay the Intent which caused the prior operation.
        if (state == null) consumeIntent(getIntent());
        else getIntent().removeExtra("accion");
    }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent); setIntent(intent); consumeIntent(intent);
    }
    private void consumeIntent(Intent intent) {
        String action = intent == null ? null : intent.getStringExtra("accion");
        if (intent != null) intent.removeExtra("accion");
        if ("desactivar".equals(action) || "restaurar".equals(action)) controller.request(action);
        else if (action != null) { controller.message = "Acción de Intent rechazada."; render(); }
        else controller.observeIfNeeded();
    }
    @Override protected void onResume() { super.onResume(); controller.listener = refresh; render(); }
    @Override protected void onPause() { if (controller.listener == refresh) controller.listener = null; super.onPause(); }
    @Override protected void onSaveInstanceState(Bundle state) { state.putBoolean("accion_consumida", true); super.onSaveInstanceState(state); }
    private Button button(LinearLayout parent, String text) {
        Button b = new Button(this); b.setText(text); b.setTextSize(20); b.setAllCaps(false);
        parent.addView(b, new LinearLayout.LayoutParams(-1, 85)); return b;
    }
    private void render() {
        boolean enabled = Build.VERSION.SDK_INT == 28 && !controller.busy && !controller.uncertainPrior;
        disableButton.setEnabled(enabled); restoreButton.setEnabled(enabled);
        report.setText(controller.message + "\n\nÚltimo estado observado: " + name(controller.observedState)
            + "\nAPI " + Build.VERSION.SDK_INT + "\n\nÚltimo registro:\n" + controller.snapshot());
    }
    private static String name(int state) {
        switch (state) {
            case BluetoothAdapter.STATE_OFF: return "OFF";
            case BluetoothAdapter.STATE_ON: return "ON";
            case BluetoothAdapter.STATE_TURNING_OFF: return "TURNING_OFF";
            case BluetoothAdapter.STATE_TURNING_ON: return "TURNING_ON";
            default: return "NO CONOCIDO (" + state + ")";
        }
    }

    private static final class Controller {
        final SharedPreferences preferences;
        final Handler main = new Handler(Looper.getMainLooper());
        volatile Runnable listener;
        volatile boolean busy, uncertainPrior, observed;
        volatile int observedState = -1;
        volatile JSONObject record = new JSONObject();
        volatile String message = "Preparado. La aceptación de una solicitud y el estado OFF son resultados diferentes.";
        long generation;
        Controller(Context app) {
            preferences = app.getSharedPreferences("resultado", Context.MODE_PRIVATE);
            try { record = new JSONObject(preferences.getString("ultimo", "{}")); }
            catch (Exception ignored) { message = "No se pudo interpretar el registro anterior."; }
            uncertainPrior = record.optBoolean("en_vuelo", false);
            if (uncertainPrior) message = "El proceso anterior terminó con una solicitud pendiente. No se repetirá ni se enviará otra desde esta sesión. Revisar el TV y el registro antes de continuar.";
            app.registerReceiver(new BroadcastReceiver() {
                @Override public void onReceive(Context context, Intent intent) {
                    if (!BluetoothAdapter.ACTION_STATE_CHANGED.equals(intent.getAction())) return;
                    final int value = intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, -1);
                    observedState = value;
                    new Thread(new Runnable() { public void run() {
                        note("estado_broadcast", name(value));
                        note("estado_broadcast_uptime_ms", SystemClock.elapsedRealtime());
                        save(); publish();
                    } }, "tvbase-bt-state").start();
                }
            }, new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED));
        }
        void observeIfNeeded() { if (!observed && !busy && !uncertainPrior) request("consultar"); }
        synchronized void request(final String action) {
            if (!"desactivar".equals(action) && !"restaurar".equals(action) && !"consultar".equals(action)) {
                message = "Acción rechazada: solo desactivar o restaurar."; publish(); return;
            }
            if (Build.VERSION.SDK_INT != 28) { message = "Esta versión solo permite Android 9 / API 28."; publish(); return; }
            if (busy || uncertainPrior) { message = "Hay una solicitud pendiente. No se enviará otra ni se cancela el trabajo del sistema."; publish(); return; }
            busy = true;
            final long operation = ++generation;
            message = "Preparando " + action + "…"; publish();
            main.postDelayed(new Runnable() { public void run() {
                if (busy && generation == operation) {
                    message = "Pasaron 8 segundos. La operación sigue pendiente; el plazo visual no cancela el trabajo del sistema. Los botones permanecerán bloqueados hasta que regrese la llamada.";
                    Log.i("TVBASE_BT", "plazo_visual_8s accion=" + action + " cancelacion_servidor=false"); publish();
                }
            } }, 8000);
            new Thread(new Runnable() { public void run() { perform(action); } }, "tvbase-bt-request").start();
        }
        void perform(String action) {
            final boolean consultation = "consultar".equals(action);
            try {
                if (consultation) {
                    BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
                    if (adapter == null) throw new IllegalStateException("BluetoothAdapter no disponible.");
                    observedState = adapter.getState(); observed = true;
                    note("ultima_lectura_estado", name(observedState));
                    note("ultima_lectura_uptime_ms", SystemClock.elapsedRealtime());
                    message = "Estado leído sin cambiar Bluetooth. Preparado para una solicitud explícita.";
                    return;
                }
                record = new JSONObject();
                note("id", UUID.randomUUID().toString()); note("accion", action);
                note("api", Build.VERSION.SDK_INT); note("inicio_uptime_ms", SystemClock.elapsedRealtime());
                note("en_vuelo", true); note("solicitud_api_invocada", false);
                if (!save()) throw new IllegalStateException("No se pudo guardar el inicio; no se enviará la solicitud.");
                BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
                if (adapter == null) throw new IllegalStateException("BluetoothAdapter no disponible.");
                int before = adapter.getState(); observedState = before; observed = true;
                note("estado_antes", name(before));
                if (!"consultar".equals(action)) {
                    note("solicitud_preparada", true);
                    if (!save()) throw new IllegalStateException("No se pudo guardar la intención; no se enviará la solicitud.");
                    note("solicitud_api_invocada", true);
                    boolean accepted = "desactivar".equals(action) ? adapter.disable() : adapter.enable();
                    note("aceptada_api", accepted);
                    note("aceptacion_uptime_ms", SystemClock.elapsedRealtime());
                    if (!save()) throw new IllegalStateException("La llamada regresó, pero no se pudo guardar su resultado.");
                    message = "La API devolvió " + accepted + ". Comprobando estado; esto no confirma que el controlador haya terminado.";
                    publish();
                }
                observedState = adapter.getState(); note("estado_despues", name(observedState));
                message = "Lectura finalizada. Estado observado: " + name(observedState) + ". Una respuesta de la API o el estado OFF no demuestran que haya cesado la actividad del controlador.";
            } catch (Exception failure) {
                note(consultation ? "error_lectura" : "error", failure.getClass().getSimpleName() + ": " + String.valueOf(failure.getMessage()));
                message = "Resultado con error: " + failure.getClass().getSimpleName() + " · " + String.valueOf(failure.getMessage()) + ". No habrá reintento automático.";
            } finally {
                if (!consultation) { note("en_vuelo", false); note("fin_uptime_ms", SystemClock.elapsedRealtime()); }
                if (!save()) {
                    uncertainPrior = true;
                    message += " No se pudo guardar el cierre. No se permitirán nuevas solicitudes en esta sesión.";
                }
                busy = false; publish();
            }
        }
        synchronized void note(String key, Object value) {
            try { record.put(key, value); } catch (Exception ignored) { }
        }
        synchronized String snapshot() { return record.toString(); }
        synchronized boolean save() {
            String text = record.toString();
            boolean committed = preferences.edit().putString("ultimo", text).commit();
            Log.i("TVBASE_BT", text + " persistido=" + committed);
            return committed;
        }
        void publish() { main.post(new Runnable() { public void run() { Runnable r = listener; if (r != null) r.run(); } }); }
    }
}
