package local.tvbase.acceso;

import android.os.Build;
import android.system.Os;
import android.system.OsConstants;
import java.io.FileDescriptor;
import java.io.File;
import java.io.RandomAccessFile;
import java.io.IOException;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.json.JSONArray;
import org.json.JSONObject;

/** Explicit preparation only. Never resets, requests reboot, invokes uncrypt or wipes data. */
public final class PreparationHelper {
    private static final String ACTIVE="/data/local/tmp/tvbase-entry-in-progress";
    private static String nonce="",phase="arguments",report;
    private static EntryIO.Media media;
    private static boolean bcbStarted,envStarted,bcbVerified,envVerified,cacheStarted,ownsActive;
    private static int renamed,step,statusNumber;
    private static RandomAccessFile processLockFile;
    private static FileLock processLock;
    private static final JSONArray files=new JSONArray();

    public static void main(String[] args) {
        try {
            EntryCodec.require(args.length==2&&(args[0].equals("prepare")||args[0].equals("launch")||args[0].equals("status")),"Operación no permitida");nonce=EntryContract.nonce(args[1]);
            EntryCodec.require(EntryPolicy.METHOD_REVIEWED,"La preparación no está habilitada por la revisión de esta compilación");
            EntryCodec.require(EntryPolicy.ZIP_SHA.matches("[0-9a-f]{64}")&&EntryPolicy.ZIP_BYTES>0,"Falta ROM exacta");
            if(args[0].equals("status")){readStatus();return;}
            stage("Comprobando identidad del primer P291");
            EntryCodec.require(Os.getuid()==0&&Build.VERSION.SDK_INT==28&&EntryContract.BUILD.equals(Build.DISPLAY),"Root/API/build diferente");
            byte[] dt=EntryIO.virtual("/proc/device-tree/amlogic-dt-id",128);
            EntryCodec.require(Arrays.equals(dt,(EntryContract.DT+"\0").getBytes(StandardCharsets.US_ASCII)),"DT diferente");
            EntryCodec.require(Os.uname().release.equals("4.9.113"),"Kernel diferente");
            if(args[0].equals("launch")){launchDetached();return;}
            verifyActiveNonce();ownsActive=true;
            EntryCodec.require(!EntryIO.absent(ACTIVE+"/process.lock"),"Falta lock del proceso");
            processLockFile=new RandomAccessFile(ACTIVE+"/process.lock","rw");processLock=processLockFile.getChannel().tryLock();
            EntryCodec.require(processLock!=null,"Ya existe un proceso de preparación");
            EntryIO.writeNew(ACTIVE+"/started.json",state("started").put("pid",Os.getpid()).toString().getBytes(StandardCharsets.UTF_8),ACTIVE);
            verifyDetached();
            stage("Localizando el único pendrive TVBASE");media=EntryIO.findMedia();media.verify();
            EntryCodec.require(Os.statvfs(media.root).f_bavail*Os.statvfs(media.root).f_frsize>=67108864L,"Falta espacio para el respaldo de preparación");
            report=media.root+"/TVBASE-entrada09-"+nonce;
            stage("Comprobando persistencia real del pendrive");EntryIO.createDirectory(report,media.root);
            save("INICIO.txt",("TVBASE-ENTRY-0.9\nnonce="+nonce+"\n").getBytes(StandardCharsets.UTF_8));
            EntryIO.writeNew(ACTIVE+"/report-path.txt",(report+"\n").getBytes(StandardCharsets.UTF_8),ACTIVE);
            checkpoint("usb_fsync_verified");
            stage("Verificando la ROM 0.2.1 del pendrive");
            EntryIO.verifyZip(media,EntryPolicy.ZIP_NAME,EntryPolicy.ZIP_BYTES,EntryPolicy.ZIP_SHA,new EntryIO.Progress(){public void stage(String text)throws Exception{PreparationHelper.stage(text);}});
            save("rom-verificada.json",new JSONObject().put("name",EntryPolicy.ZIP_NAME).put("bytes",EntryPolicy.ZIP_BYTES).put("sha256",EntryPolicy.ZIP_SHA).toString().getBytes(StandardCharsets.UTF_8));
            checkpoint("rom_verified");
            stage("Respaldando ENV y BCB originales");
            byte[] env=EntryIO.readBlock("env",4),misc=EntryIO.readBlock("misc",7);
            EntryCodec.snapshot(env,EntryContract.ENV_SHA,EntryCodec.PART_SIZE);
            EntryCodec.snapshot(misc,EntryContract.MISC_SHA,EntryCodec.PART_SIZE);
            byte[] envAfter=EntryCodec.envMenu(env,EntryContract.ENV_SHA),miscAfter=EntryCodec.bcbMenu(misc,EntryContract.MISC_SHA);
            EntryCodec.require(EntryCodec.sha(Arrays.copyOf(envAfter,65536)).equals(EntryPolicy.ENV_RECORD_SHA),"El codec ENV no produce el resultado revisado");
            EntryCodec.require(EntryCodec.sha(Arrays.copyOf(miscAfter,2048)).equals(EntryPolicy.BCB_PREFIX_SHA),"El codec BCB no produce el resultado revisado");
            save("env-before.img",env);save("misc-before.img",misc);
            EntryIO.Snapshot[] cache=new EntryIO.Snapshot[EntryContract.CACHE.length];
            JSONArray cacheState=new JSONArray();
            for(int i=0;i<cache.length;i++){
                String name=EntryContract.CACHE[i],path="/cache/recovery/"+name;
                if(EntryIO.absent(path)){cacheState.put(new JSONObject().put("name",name).put("state","absent"));continue;}
                cache[i]=EntryIO.smallFile(path,16777216);save("cache-before-"+name+".bin",cache[i].bytes);
                cacheState.put(new JSONObject().put("name",name).put("state","present").put("bytes",cache[i].bytes.length).put("sha256",cache[i].sha));
            }
            save("cache-before.json",cacheState.toString().getBytes(StandardCharsets.UTF_8));
            save("changes-reviewed.json",new JSONObject().put("env_prefix_bytes",65536).put("env_before_sha256",EntryContract.ENV_SHA)
                    .put("env_after_sha256",EntryCodec.sha(envAfter)).put("env_record_after_sha256",EntryPolicy.ENV_RECORD_SHA)
                    .put("misc_prefix_bytes",2048).put("misc_before_sha256",EntryContract.MISC_SHA).put("misc_after_sha256",EntryCodec.sha(miscAfter))
                    .put("bcb_after_sha256",EntryPolicy.BCB_PREFIX_SHA).put("normal_bootcmd_restore_is_conditional_on_reaching_bootcmd",true)
                    .put("saveenv_atomic_or_rollback_proven",false).put("reset_requested",false).toString().getBytes(StandardCharsets.UTF_8));
            checkpoint("backups_persisted");
            stage("Comprobando estado y sincronización antes de modificar el arranque");
            media.verify();EntryCodec.require(Arrays.equals(env,EntryIO.readBlock("env",4))&&Arrays.equals(misc,EntryIO.readBlock("misc",7)),"Cambió una partición tras su respaldo");
            for(String name:new String[]{"env","misc"}){
                FileDescriptor fd=EntryIO.block(name,name.equals("env")?4:7,OsConstants.O_RDWR,EntryCodec.PART_SIZE);
                try{Os.fsync(fd);}finally{Os.close(fd);}
            }
            EntryIO.syncDirectory("/cache/recovery");
            checkpoint("prewrite_checks_passed");
            stage("Neutralizando las órdenes anteriores con copia conservada");
            for(int i=0;i<cache.length;i++){
                String name=EntryContract.CACHE[i],path="/cache/recovery/"+name;
                if(cache[i]==null){EntryCodec.require(EntryIO.absent(path),"Apareció una orden cache nueva");continue;}
                EntryIO.Snapshot current=EntryIO.smallFile(path,16777216);
                EntryCodec.require(EntryIO.same(cache[i].stat,current.stat)&&cache[i].sha.equals(current.sha),"Cambió orden cache antes de neutralizar");
                String saved="/cache/recovery/tvbase-entry-"+nonce+".saved-"+name;
                EntryCodec.require(EntryIO.absent(saved),"Existe destino de preservación cache");
                cacheStarted=true;checkpoint("cache_rename_about_to_start_"+name);
                media.verify();Os.rename(path,saved);renamed++;EntryIO.syncDirectory("/cache/recovery");
                EntryCodec.require(EntryIO.absent(path)&&EntryIO.smallFile(saved,16777216).sha.equals(cache[i].sha),"No se confirmó la neutralización cache");
                checkpoint("cache_preserved_"+name);
            }
            noPendingCache();checkpoint("cache_neutralized");
            stage("Guardando solicitud de menú recovery en BCB");media.verify();bcbStarted=true;checkpoint("bcb_write_about_to_start");
            EntryIO.replacePrefix("misc",7,misc,miscAfter,2048);bcbVerified=true;checkpoint("bcb_verified");
            stage("Guardando entrada de un solo uso en ENV");noPendingCache();media.verify();envStarted=true;checkpoint("env_write_about_to_start");
            EntryIO.replacePrefix("env",4,env,envAfter,65536);envVerified=true;checkpoint("env_verified");
            noPendingCache();media.verify();
            EntryCodec.require(Arrays.equals(envAfter,EntryIO.readBlock("env",4))&&Arrays.equals(miscAfter,EntryIO.readBlock("misc",7)),"Cambió preparación al verificar el cierre");
            JSONObject finalState=state("ready_to_commit").put("files",files).put("zip_sha256",EntryPolicy.ZIP_SHA)
                    .put("env_after_sha256",EntryCodec.sha(envAfter)).put("misc_after_sha256",EntryCodec.sha(miscAfter))
                    .put("block_device_readback_verified",true).put("physical_recovery_entry_tested",false)
                    .put("power_cycle_required_from_user",true).put("automatic_cache_restore",false);
            String manifestSha=EntryIO.writeNew(report+"/INFORME.json",finalState.toString(2).getBytes(StandardCharsets.UTF_8),report);
            EntryIO.writeNew(ACTIVE+"/candidate.json",state("ready_to_commit").put("manifest_sha256",manifestSha).toString().getBytes(StandardCharsets.UTF_8),ACTIVE);
            EntryIO.writeNew(report+"/COMPLETO.txt",("TVBASE_PREPARED_09\nnonce="+nonce+"\nmanifest_sha256="+manifestSha+"\n").getBytes(StandardCharsets.UTF_8),report);
            EntryIO.syncDirectory(report);EntryIO.syncDirectory(media.root);media.verify();
            JSONObject committed=state("prepared").put("manifest_sha256",manifestSha);
            EntryIO.writeNew(ACTIVE+"/prepared.json",committed.toString().getBytes(StandardCharsets.UTF_8),ACTIVE);
            persistStatus(committed);emit(committed);
        }catch(Throwable error){
            try{
                JSONObject failure=state("incomplete").put("error",error.getClass().getSimpleName()+": "+error.getMessage())
                        .put("safe_to_power_cycle",false).put("automatic_retry",false);
                if(!ownsActive)failure.put("preparation_state_unknown",true).put("env_write_started",JSONObject.NULL)
                        .put("bcb_write_started",JSONObject.NULL).put("cache_mutation_started",JSONObject.NULL);
                if(ownsActive){try{EntryIO.writeNew(ACTIVE+"/INCOMPLETO.json",failure.toString(2).getBytes(StandardCharsets.UTF_8),ACTIVE);persistStatus(failure);}catch(Throwable ignored){failure.put("internal_failure_persistence_confirmed",false);}}
                if(report!=null&&media!=null){try{media.verify();EntryIO.writeNew(report+"/INCOMPLETO.json",failure.toString(2).getBytes(StandardCharsets.UTF_8),report);}catch(Throwable ignored){failure.put("failure_report_persistence_confirmed",false);}}
                emit(failure);
            }catch(Throwable ignored){System.out.println("TVBASE_ENTRY_FATAL");System.out.flush();}
            System.exit(1);
        }finally{
            if(processLock!=null)try{processLock.release();}catch(Exception ignored){}
            if(processLockFile!=null)try{processLockFile.close();}catch(Exception ignored){}
        }
    }
    private static void launchDetached()throws Exception{
        EntryCodec.require(EntryIO.absent(ACTIVE),"Hay una preparación previa pendiente; no se repetirá automáticamente");
        String apk=EntryContract.apkPath(System.getenv("CLASSPATH"));
        EntryIO.createDirectory(ACTIVE,"/data/local/tmp");
        EntryIO.writeNew(ACTIVE+"/nonce.txt",(nonce+"\n").getBytes(StandardCharsets.US_ASCII),ACTIVE);ownsActive=true;
        EntryIO.writeNew(ACTIVE+"/process.log",new byte[0],ACTIVE);EntryIO.writeNew(ACTIVE+"/process.lock",new byte[0],ACTIVE);
        phase="Iniciando proceso independiente";persistStatus(state("stage"));
        ProcessBuilder child=new ProcessBuilder("/system/bin/toybox","setsid","/system/bin/toybox","nohup",
                "/system/bin/app_process","/system/bin","local.tvbase.acceso.PreparationHelper","prepare",nonce);
        child.environment().put("CLASSPATH",apk);
        child.redirectInput(ProcessBuilder.Redirect.from(new File("/dev/null")));
        child.redirectOutput(ProcessBuilder.Redirect.appendTo(new File(ACTIVE+"/process.log")));child.redirectErrorStream(true);
        child.start();emit(state("launched"));
    }
    private static void verifyActiveNonce()throws Exception{
        EntryCodec.require(Os.getuid()==0,"Se requiere UID 0");
        EntryCodec.require(new String(EntryIO.smallFile(ACTIVE+"/nonce.txt",64).bytes,StandardCharsets.US_ASCII).equals(nonce+"\n"),"Nonce activo diferente");
    }
    private static void verifyDetached()throws Exception{
        String stat=EntryIO.text("/proc/self/stat",8192);int close=stat.lastIndexOf(')');EntryCodec.require(close>0,"Formato de proceso inesperado");
        String[] fields=stat.substring(close+2).split(" ");long pid=Os.getpid();
        EntryCodec.require(fields.length>5&&Long.parseLong(fields[2])==pid&&Long.parseLong(fields[3])==pid&&Long.parseLong(fields[4])==0,"Proceso sin sesión aislada o con terminal");
        String ignored=null;for(String line:EntryIO.text("/proc/self/status",65536).split("\n"))if(line.startsWith("SigIgn:"))ignored=line.substring(7).trim();
        EntryCodec.require(ignored!=null&&new java.math.BigInteger(ignored,16).testBit(0),"SIGHUP no está ignorada");
        EntryCodec.require(Os.readlink("/proc/self/fd/0").equals("/dev/null")
                &&Os.readlink("/proc/self/fd/1").equals(ACTIVE+"/process.log")&&Os.readlink("/proc/self/fd/2").equals(ACTIVE+"/process.log"),"Descriptores aún ligados al transporte");
        EntryIO.writeNew(ACTIVE+"/detached.json",state("detached_verified").put("pid",pid).put("session",pid).put("sighup_ignored",true).toString().getBytes(StandardCharsets.UTF_8),ACTIVE);
    }
    private static void readStatus()throws Exception{
        verifyActiveNonce();EntryCodec.require(!EntryIO.absent(ACTIVE+"/process.lock"),"Falta lock activo");
        JSONObject value=new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/status.json",32768).bytes,StandardCharsets.UTF_8));
        EntryCodec.require(value.getString("nonce").equals(nonce),"Estado de otro intento");
        if(!EntryIO.absent(ACTIVE+"/INCOMPLETO.json")){emit(new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/INCOMPLETO.json",32768).bytes,StandardCharsets.UTF_8)));return;}
        if(!value.getString("state").equals("prepared")){
            if(!EntryIO.absent(ACTIVE+"/started.json")){
                JSONObject started=new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/started.json",32768).bytes,StandardCharsets.UTF_8));
                EntryCodec.require(started.getString("nonce").equals(nonce),"Inicio de otro intento");
                int pid=started.getInt("pid");EntryCodec.require(pid>0&&pid<=4194304,"PID registrado inválido");
                if(EntryIO.absent("/proc/"+pid)){
                    // The worker may have committed and exited after our first read.
                    value=new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/status.json",32768).bytes,StandardCharsets.UTF_8));
                    EntryCodec.require(value.getString("nonce").equals(nonce),"Estado final de otro intento");
                    if(!EntryIO.absent(ACTIVE+"/INCOMPLETO.json")){emit(new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/INCOMPLETO.json",32768).bytes,StandardCharsets.UTF_8)));return;}
                    if(!value.getString("state").equals("prepared"))value.put("state","incomplete").put("error","El proceso terminó sin confirmar la preparación; estado indeterminado").put("safe_to_power_cycle",false);
                }
            }
            if(!value.getString("state").equals("prepared")){emit(value);return;}
        }
        // A reader must never take the lock during startup: that could make the
        // worker's initial tryLock fail. Lock only to confirm a terminal commit.
        RandomAccessFile lockFile=new RandomAccessFile(ACTIVE+"/process.lock","rw");FileLock lock=null;
        try{
            lock=lockFile.getChannel().tryLock();
            if(!EntryIO.absent(ACTIVE+"/INCOMPLETO.json"))value=new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/INCOMPLETO.json",32768).bytes,StandardCharsets.UTF_8));
            else {
                if(lock==null)value.put("state","stage").put("phase","Terminando sincronización de la preparación");
                else verifyCommitted(value);
            }
            emit(value);
        }finally{if(lock!=null)lock.release();lockFile.close();}
    }
    private static void verifyCommitted(JSONObject value)throws Exception{
        EntryCodec.require(value.getString("nonce").equals(nonce),"Nonce final distinto");
        JSONObject internal=new JSONObject(new String(EntryIO.smallFile(ACTIVE+"/prepared.json",32768).bytes,StandardCharsets.UTF_8));
        EntryCodec.require(internal.getString("nonce").equals(nonce)&&internal.getString("state").equals("prepared")
                &&internal.getString("manifest_sha256").equals(value.getString("manifest_sha256")),"Recibo interno final distinto");
        EntryIO.Media actual=EntryIO.findMedia();actual.verify();String path=actual.root+"/TVBASE-entrada09-"+nonce;
        EntryCodec.require(value.getString("report").equals(path),"Ruta final distinta");
        EntryCodec.require(EntryIO.absent(path+"/INCOMPLETO.json"),"USB conserva un resultado incompleto");
        String expected=value.getString("manifest_sha256");EntryCodec.require(expected.matches("[0-9a-f]{64}"),"Hash final inválido");
        EntryCodec.require(EntryIO.smallFile(path+"/INFORME.json",262144).sha.equals(expected),"Manifiesto final diferente");
        EntryCodec.require(new String(EntryIO.smallFile(path+"/COMPLETO.txt",256).bytes,StandardCharsets.UTF_8)
                .equals("TVBASE_PREPARED_09\nnonce="+nonce+"\nmanifest_sha256="+expected+"\n"),"Marcador de cierre diferente");
        for(String file:new String[]{path+"/INFORME.json",path+"/COMPLETO.txt",ACTIVE+"/prepared.json",ACTIVE+"/status.json"}){
            FileDescriptor fd=Os.open(file,OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0);try{Os.fsync(fd);}finally{Os.close(fd);}
        }
        EntryIO.syncDirectory(path);EntryIO.syncDirectory(actual.root);EntryIO.syncDirectory(ACTIVE);
        EntryCodec.require(EntryIO.absent(ACTIVE+"/INCOMPLETO.json"),"Apareció un fallo final");actual.verify();
    }
    private static void persistStatus(JSONObject value)throws Exception{
        verifyActiveNonce();String temporary=String.format(java.util.Locale.ROOT,"status-%d-%05d.tmp",Os.getpid(),++statusNumber);
        EntryIO.writeNew(ACTIVE+"/"+temporary,value.toString().getBytes(StandardCharsets.UTF_8),ACTIVE);
        Os.rename(ACTIVE+"/"+temporary,ACTIVE+"/status.json");EntryIO.syncDirectory(ACTIVE);
    }
    private static void noPendingCache()throws Exception{for(String name:EntryContract.CACHE)EntryCodec.require(EntryIO.absent("/cache/recovery/"+name),"Reapareció una orden de actualización: "+name);}
    private static JSONObject state(String status)throws Exception{return new JSONObject().put("state",status).put("nonce",nonce).put("phase",phase)
            .put("report",report==null?JSONObject.NULL:report).put("env_write_started",envStarted).put("env_readback_verified",envVerified)
            .put("bcb_write_started",bcbStarted).put("bcb_readback_verified",bcbVerified).put("cache_files_preserved",renamed)
            .put("cache_mutation_started",cacheStarted)
            .put("reset_requested",false).put("userdata_wiped",false).put("firmware_images_written",false);}
    private static void stage(String text)throws Exception{phase=text;JSONObject value=state("stage");if(ownsActive)persistStatus(value);emit(value);}
    private static void emit(JSONObject value){System.out.println("TVBASE_ENTRY:"+value.toString());System.out.flush();}
    private static void checkpoint(String name)throws Exception{
        String filename=String.format(java.util.Locale.ROOT,"stage-%02d-%s.json",++step,name);byte[] value=state(name).toString().getBytes(StandardCharsets.UTF_8);
        EntryIO.writeNew(ACTIVE+"/"+filename,value,ACTIVE);persistStatus(state("stage").put("checkpoint",name));media.verify();save(filename,value);
    }
    private static void save(String name,byte[] bytes)throws Exception{
        media.verify();String sha=EntryIO.writeNew(report+"/"+name,bytes,report);
        EntryIO.writeNew(report+"/"+name+".sha256",(sha+"\n").getBytes(StandardCharsets.US_ASCII),report);
        files.put(new JSONObject().put("name",name).put("bytes",bytes.length).put("sha256",sha));
    }
}
