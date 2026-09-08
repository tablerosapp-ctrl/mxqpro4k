package com.tvbase.reconocimiento;

import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.system.Os;
import android.system.OsConstants;
import android.system.ErrnoException;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;
import org.json.*;

public final class UsbStore {
    public static final String FOLDER="TVBASE-RECONOCIMIENTO", MARKER="MEDIA.json", MEDIA_ID="tvbase-recognition-kingston-20260908-c73d9a14";
    public static final class Result {public String path,mode; public boolean fileSynced,dirSynced;public long bytes;public String hash;}
    static String text(InputStream stream)throws Exception {try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[1024];int n;while((n=in.read(b))!=-1){if(out.size()+n>16384)throw new IOException("Marcador demasiado grande");out.write(b,0,n);}return new String(out.toByteArray(),"UTF-8");}}
    static void marker(String contents)throws Exception {JSONObject j=new JSONObject(contents);if(!j.optString("schema").equals("tvbase-recognition-media-1")||!j.optString("media_id").equals(MEDIA_ID))throw new IOException("No es el pendrive preparado para reconocimiento");}
    private static volatile String discoveryJson="{\"state\":\"not_run\"}";
    private static final UsbLocator.Probe PROBE=new UsbLocator.FileProbe(){
        public UsbLocator.Node stat(String path)throws Exception{
            android.system.StructStat st;
            try{st=Os.stat(path);}catch(ErrnoException e){if(e.errno==OsConstants.ENOENT||e.errno==OsConstants.ENOTDIR)return null;throw e;}
            return new UsbLocator.Node(OsConstants.S_ISDIR(st.st_mode),OsConstants.S_ISREG(st.st_mode),new File(path).getCanonicalPath(),st.st_dev,st.st_ino);
        }
        public byte[] read(String path,int cap)throws Exception{
            android.system.StructStat st=Os.stat(path);
            if(!OsConstants.S_ISREG(st.st_mode))throw new IOException("Fuente de descubrimiento no regular");
            if(path.endsWith("/"+MARKER)&&OsConstants.S_ISLNK(Os.lstat(path).st_mode))throw new IOException("Marcador USB redirigido");
            return super.read(path,cap);
        }
    };
    public static UsbLocator.Result discover()throws Exception{
        Map<String,String> env=new HashMap<String,String>();for(String name:new String[]{"EXTERNAL_STORAGE","SECONDARY_STORAGE"})try{String value=System.getenv(name);if(value!=null)env.put(name,value);}catch(SecurityException ignored){}
        UsbLocator.Result result=UsbLocator.discover(PROBE,Collections.<String>emptyList(),env,8000);
        discoveryJson=result.toJson().toString();return result;
    }
    public static JSONObject lastDiscovery()throws Exception{return new JSONObject(discoveryJson);}
    public static String describe(UsbLocator.Result result){
        StringBuilder text=new StringBuilder("Búsqueda USB: ").append(result.candidates.size()).append(" destino(s) marcado(s), ").append(result.visitedDirectories).append(" carpetas revisadas.");
        if(result.timedOut||result.pendingWorker)text.append(" La lectura no terminó; no se inicia otra búsqueda mientras siga pendiente.");
        else if(result.limited)text.append(" La búsqueda alcanzó un límite; la selección debe ser explícita.");
        if(result.candidates.isEmpty())text.append(" La ficha sigue en Android. Podés guardar en Descargas y copiarla con Archivos.");
        return text.toString();
    }
    public static UsbLocator.Candidate automatic(String preferred)throws Exception{
        UsbLocator.Result result=discover();
        if(result.timedOut||result.pendingWorker)throw new IOException("Búsqueda USB pendiente; usá Guardar en Descargas si no termina");
        if(preferred.length()>0){for(UsbLocator.Candidate c:result.candidates)if(c.folder.equals(preferred)||c.aliases.contains(preferred)){revalidate(c);return c;}throw new IOException("El pendrive seleccionado ya no coincide. Volvé a elegirlo desde TV Base");}
        if(result.candidates.isEmpty())return null;
        if(result.candidates.size()!=1||result.limited)throw new IOException("Elegí explícitamente el pendrive desde TV Base");
        UsbLocator.Candidate c=result.candidates.get(0);revalidate(c);return c;
    }
    static void revalidate(UsbLocator.Candidate c)throws Exception{
        if(c==null)throw new IOException("Falta candidato USB");
        UsbLocator.Node now=PROBE.stat(c.folder);
        if(now==null||!now.directory||!c.canonical.equals(now.canonical)
            ||c.device!=null&&!c.device.equals(now.device)||c.inode!=null&&!c.inode.equals(now.inode))throw new IOException("El destino USB cambió después de identificarlo");
        if(!UsbLocator.validMarker(PROBE.read(c.folder+"/"+MARKER,4096)))throw new IOException("El marcador USB cambió o no es válido");
    }
    public static Result direct(UsbLocator.Candidate target,ReportArchive.Result archive,HardwareCollector.Progress cb)throws Exception{
        revalidate(target);return directFolder(new File(target.folder),archive,cb);
    }
    static Uri child(Context c,Uri parent,String name)throws Exception {
        Uri list=DocumentsContract.buildChildDocumentsUriUsingTree(parent,DocumentsContract.getDocumentId(parent));
        Uri result=null;
        try(Cursor cursor=c.getContentResolver().query(list,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null)){
            if(cursor==null)throw new IOException("El selector no devuelve archivos");
            while(cursor.moveToNext())if(name.equals(cursor.getString(1))){if(result!=null)throw new IOException("Nombre duplicado en USB");result=DocumentsContract.buildDocumentUriUsingTree(parent,cursor.getString(0));}
        }return result;
    }
    public static Uri preparedFolder(Context c,Uri tree)throws Exception {
        Uri root=DocumentsContract.buildDocumentUriUsingTree(tree,DocumentsContract.getTreeDocumentId(tree));
        Uri m=child(c,root,MARKER);
        if(m==null){root=child(c,root,FOLDER);if(root==null)throw new IOException("Elegí TVBASE o la carpeta "+FOLDER);m=child(c,root,MARKER);}
        if(m==null)throw new IOException("Falta marcador del pendrive");marker(text(c.getContentResolver().openInputStream(m)));return root;
    }
    static boolean syncFile(FileDescriptor fd)throws IOException {
        try{Os.fsync(fd);return true;}catch(ErrnoException e){if(e.errno==OsConstants.EINVAL||e.errno==OsConstants.EOPNOTSUPP||e.errno==OsConstants.ENOSYS)return false;throw new IOException("Error real al sincronizar almacenamiento",e);}
    }
    static boolean syncDir(File d)throws IOException {FileDescriptor fd=null;try{fd=Os.open(d.getAbsolutePath(),OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW,0);if(!OsConstants.S_ISDIR(Os.fstat(fd).st_mode))throw new IOException("El destino no es un directorio");return syncFile(fd);}catch(ErrnoException e){throw new IOException("No se puede abrir el directorio para sincronizar",e);}finally{if(fd!=null)try{Os.close(fd);}catch(Exception ignored){}}}
    static void stream(File src,OutputStream out,HardwareCollector.Progress cb)throws Exception {
        try(InputStream in=new FileInputStream(src)){byte[] b=new byte[262144];int n;long total=0,last=0;while((n=in.read(b))!=-1){out.write(b,0,n);total+=n;if(total-last>=4194304){cb.update("Guardando en pendrive: "+(total/1048576)+" MB");last=total;}}if(total!=src.length())throw new IOException("Copia incompleta");out.flush();}
    }
    static void verify(InputStream input,ReportArchive.Result a)throws Exception {
        MessageDigest d=MessageDigest.getInstance("SHA-256");long total=0;
        try(InputStream in=input){byte[] b=new byte[262144];int n;while((n=in.read(b))!=-1){d.update(b,0,n);total+=n;if(total>a.bytes)throw new IOException("Tamaño USB diferente");}}
        if(total!=a.bytes||!ReportArchive.hex(d.digest()).equals(a.sha256))throw new IOException("La lectura del USB no coincide; copia local conservada");
    }
    static JSONObject receipt(ReportArchive.Result a,Result r)throws Exception{return new JSONObject().put("schema","tvbase-recognition-export-1").put("file",a.archive.getName()).put("bytes",a.bytes).put("sha256",a.sha256).put("usb_readback_sha256_verified",true).put("file_sync_verified",r.fileSynced).put("directory_sync_verified",r.dirSynced).put("transport",r.mode).put("hardware_capture_complete",false).put("note","Integridad de exportación; ver informe para alcance de captura. Expulsar almacenamiento antes de retirar.");}
    static void checkReceipt(String value,ReportArchive.Result a)throws Exception {
        JSONObject j=new JSONObject(value);if(!j.optString("schema").equals("tvbase-recognition-export-1")||!j.optString("file").equals(a.archive.getName())||j.optLong("bytes",-1)!=a.bytes||!j.optString("sha256").equals(a.sha256)||!j.optBoolean("usb_readback_sha256_verified",false))throw new IOException("El recibo existente no corresponde; no se sobrescribió");
    }
    static Result finishDirect(File dir,ReportArchive.Result a,Result r)throws Exception {
        r.dirSynced=syncDir(dir);File proof=new File(dir,a.archive.getName()+".export.json");
        if(proof.exists())checkReceipt(text(new FileInputStream(proof)),a);else ReportArchive.write(proof,receipt(a,r).toString(2));
        checkReceipt(text(new FileInputStream(proof)),a);r.dirSynced=syncDir(dir)&&r.dirSynced;return r;
    }
    private static Result directFolder(File folder,ReportArchive.Result a,HardwareCollector.Progress cb)throws Exception {
        marker(text(new FileInputStream(new File(folder,MARKER))));File dir=new File(folder,"INFORMES");
        if(!dir.exists()&&!dir.mkdir())throw new IOException("No se puede crear carpeta de informes; usá Elegir pendrive");
        if(!dir.getCanonicalPath().equals(folder.getCanonicalPath()+"/INFORMES"))throw new IOException("Destino inesperado");
        File dst=new File(dir,a.archive.getName()),partial=new File(dir,a.archive.getName()+".partial");
        Result r=new Result();r.mode="direct";r.bytes=a.bytes;r.hash=a.sha256;r.path=dst.getAbsolutePath();
        if(dst.exists()){verify(new FileInputStream(dst),a);try(FileInputStream in=new FileInputStream(dst)){r.fileSynced=syncFile(in.getFD());}return finishDirect(dir,a,r);}
        if(dir.getUsableSpace()<a.bytes+16777216L)throw new IOException("No queda espacio suficiente en el pendrive");
        if(partial.exists())partial=new File(dir,a.archive.getName()+"."+UUID.randomUUID().toString()+".partial");
        if(!partial.createNewFile())throw new IOException("No se pudo crear otro intento de copia");
        try(FileOutputStream out=new FileOutputStream(partial)){stream(a.archive,out,cb);r.fileSynced=syncFile(out.getFD());}
        cb.update("Releyendo y comprobando el archivo del pendrive…");verify(new FileInputStream(partial),a);
        if(!partial.renameTo(dst))throw new IOException("No se pudo finalizar archivo en USB");
        return finishDirect(dir,a,r);
    }
    static Result finishDocument(Context c,Uri dir,ReportArchive.Result a,Result r)throws Exception {
        String name=a.archive.getName()+".export.json";Uri proof=child(c,dir,name);
        if(proof!=null)checkReceipt(text(c.getContentResolver().openInputStream(proof)),a);
        else{
            proof=DocumentsContract.createDocument(c.getContentResolver(),dir,"application/json",name);if(proof==null)throw new IOException("Informe copiado; falta completar su recibo");
            try(OutputStream out=c.getContentResolver().openOutputStream(proof,"w")){if(out==null)throw new IOException("Recibo no escribible");out.write(receipt(a,r).toString(2).getBytes("UTF-8"));out.flush();}
            checkReceipt(text(c.getContentResolver().openInputStream(proof)),a);
        }
        return r;
    }
    public static Result document(Context c,Uri tree,ReportArchive.Result a,HardwareCollector.Progress cb)throws Exception {
        Uri folder=preparedFolder(c,tree),dir=child(c,folder,"INFORMES");
        if(dir==null)dir=DocumentsContract.createDocument(c.getContentResolver(),folder,DocumentsContract.Document.MIME_TYPE_DIR,"INFORMES");
        if(dir==null)throw new IOException("No se pudo crear carpeta de informes");
        String name=a.archive.getName();Uri existing=child(c,dir,name);
        Result r=new Result();r.mode="document_provider";r.bytes=a.bytes;r.hash=a.sha256;
        if(existing!=null){verify(c.getContentResolver().openInputStream(existing),a);r.path=name;try(ParcelFileDescriptor fd=c.getContentResolver().openFileDescriptor(existing,"r")){if(fd!=null)r.fileSynced=syncFile(fd.getFileDescriptor());}return finishDocument(c,dir,a,r);}
        String partialName=name+".partial";if(child(c,dir,partialName)!=null)partialName=name+"."+UUID.randomUUID().toString()+".partial";
        Uri dst=DocumentsContract.createDocument(c.getContentResolver(),dir,"application/octet-stream",partialName);if(dst==null)throw new IOException("No se pudo crear archivo USB");
        ParcelFileDescriptor pfd=c.getContentResolver().openFileDescriptor(dst,"w");
        if(pfd==null)throw new IOException("No se puede escribir el documento");
        try(ParcelFileDescriptor.AutoCloseOutputStream out=new ParcelFileDescriptor.AutoCloseOutputStream(pfd)){stream(a.archive,out,cb);r.fileSynced=syncFile(out.getFD());}
        cb.update("Releyendo y comprobando el archivo del pendrive…");verify(c.getContentResolver().openInputStream(dst),a);
        Uri renamed=DocumentsContract.renameDocument(c.getContentResolver(),dst,name);if(renamed==null)throw new IOException("El proveedor no permite finalizar la captura; copia local conservada");
        verify(c.getContentResolver().openInputStream(renamed),a);Uri named=child(c,dir,name);if(named==null||!DocumentsContract.getDocumentId(named).equals(DocumentsContract.getDocumentId(renamed)))throw new IOException("El proveedor cambió el nombre solicitado");r.path=name;r.dirSynced=false;
        return finishDocument(c,dir,a,r);
    }
}
