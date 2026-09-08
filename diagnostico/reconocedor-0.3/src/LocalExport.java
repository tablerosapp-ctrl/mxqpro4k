package com.tvbase.reconocimiento;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.util.UUID;
import org.json.JSONObject;

/** Explicit local fallback. It neither discovers USB nor creates a USB marker. */
public final class LocalExport {
    public static final String FOLDER="TVBASE-PARA-COPIAR";
    private static final long RESERVE=16L*1024*1024;
    public static final class Result {
        public final File zip,receipt;
        public final long bytes;
        public final String sha256;
        public final boolean fileSynced=true,readbackVerified=true,directorySynced=false,usbCopyVerified=false;
        Result(File zip,File receipt,long bytes,String sha256){this.zip=zip;this.receipt=receipt;this.bytes=bytes;this.sha256=sha256;}
    }
    private LocalExport(){}

    private static void directory(File directory)throws Exception {
        if(directory==null||!directory.isAbsolute()||!directory.isDirectory()
                ||!directory.getCanonicalFile().equals(directory.getAbsoluteFile()))
            throw new IOException("Directorio local ausente o redirigido");
    }
    private static void target(File folder,File file)throws Exception {
        directory(folder);
        if(!file.getParentFile().equals(folder)||!file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new IOException("Destino local redirigido");
        if(file.exists()&&!file.isFile())throw new IOException("Destino local ocupado por otro tipo de archivo");
    }
    private static String digest(File file,long expected)throws Exception {
        if(!file.isFile()||file.length()!=expected)throw new IOException("Tamaño local diferente");
        MessageDigest hash=MessageDigest.getInstance("SHA-256");long total=0;
        try(FileInputStream in=new FileInputStream(file)){
            byte[] buffer=new byte[65536];int count;
            while((count=in.read(buffer))!=-1){total+=count;if(total>expected)throw new IOException("Archivo creció durante lectura");hash.update(buffer,0,count);}
        }
        if(total!=expected||file.length()!=expected)throw new IOException("Lectura local incompleta");
        return ReportArchive.hex(hash.digest());
    }
    private static void verify(File folder,File file,long bytes,String sha)throws Exception {
        target(folder,file);
        if(!digest(file,bytes).equals(sha))throw new IOException("SHA-256 local diferente; no se sobrescribió");
        target(folder,file);
    }
    private static void syncExisting(File folder,File file)throws Exception {
        target(folder,file);
        try(FileInputStream in=new FileInputStream(file)){in.getFD().sync();}
        target(folder,file);
    }
    /** Exclusive creation, never truncate an existing path; retain interrupted files. */
    private static void copyNew(File source,File folder,File file,long bytes,String sha)throws Exception {
        target(folder,file);
        if(!file.createNewFile())throw new IOException("El archivo local apareció antes de copiar; no se reemplazó");
        target(folder,file);
        if(file.length()!=0)throw new IOException("El archivo local nuevo cambió");
        MessageDigest hash=MessageDigest.getInstance("SHA-256");long total=0;
        try(FileInputStream in=new FileInputStream(source);FileOutputStream out=new FileOutputStream(file,true)){
            byte[] buffer=new byte[65536];int count;
            while((count=in.read(buffer))!=-1){total+=count;if(total>bytes)throw new IOException("Fuente excede tamaño sellado");hash.update(buffer,0,count);out.write(buffer,0,count);}
            if(total!=bytes||!ReportArchive.hex(hash.digest()).equals(sha))throw new IOException("Fuente difiere del ZIP sellado");
            out.flush();out.getFD().sync();
        }
        verify(folder,file,bytes,sha);
    }
    private static void writeNew(File folder,File file,byte[] content)throws Exception {
        target(folder,file);
        if(!file.createNewFile())throw new IOException("Recibo local existente; no se reemplazó");
        target(folder,file);
        if(file.length()!=0)throw new IOException("El recibo local nuevo cambió");
        try(FileOutputStream out=new FileOutputStream(file,true)){out.write(content);out.flush();out.getFD().sync();}
        verify(folder,file,content.length,ReportArchive.hex(MessageDigest.getInstance("SHA-256").digest(content)));
    }
    private static JSONObject readReceipt(File folder,File proof)throws Exception {
        target(folder,proof);
        if(!proof.isFile()||proof.length()<1||proof.length()>16384)throw new IOException("Recibo local inválido");
        try(FileInputStream in=new FileInputStream(proof);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[1024];int count;
            while((count=in.read(buffer))!=-1){if(out.size()+count>16384)throw new IOException("Recibo local excesivo");out.write(buffer,0,count);}
            return new JSONObject(new String(out.toByteArray(),"UTF-8"));
        }
    }
    private static void checkReceipt(JSONObject receipt,ReportArchive.Result archive)throws Exception {
        if(!"tvbase-recognition-local-export-1".equals(receipt.optString("schema"))
                ||!"android_downloads".equals(receipt.optString("destination"))
                ||!archive.archive.getName().equals(receipt.optString("file"))
                ||receipt.optLong("bytes",-1)!=archive.bytes||!archive.sha256.equals(receipt.optString("sha256"))
                ||!Boolean.FALSE.equals(receipt.opt("usb_copy_verified"))
                ||!Boolean.FALSE.equals(receipt.opt("directory_sync_verified"))
                ||!Boolean.TRUE.equals(receipt.opt("file_sync_verified"))
                ||!Boolean.TRUE.equals(receipt.opt("local_readback_sha256_verified")))
            throw new IOException("Recibo local distinto; no se sobrescribió");
    }
    public static Result save(File downloads,ReportArchive.Result archive)throws Exception {
        directory(downloads);
        if(archive==null||archive.archive==null||archive.bytes<1||archive.bytes>ReportArchive.MAX_TOTAL+RESERVE
                ||archive.sha256==null||!archive.sha256.matches("[a-f0-9]{64}")
                ||!archive.archive.getName().matches("TVBASE-[a-z0-9_-]{1,160}\\.zip"))
            throw new IOException("Se requiere un ZIP de reconocimiento sellado");
        if(!digest(archive.archive,archive.bytes).equals(archive.sha256))throw new IOException("El ZIP sellado local cambió");
        File folder=new File(downloads,FOLDER);
        if(!folder.getCanonicalFile().equals(folder.getAbsoluteFile()))throw new IOException("Carpeta de copia redirigida");
        if(!folder.exists()&&!folder.mkdir())throw new IOException("No se puede crear carpeta en Descargas");
        directory(downloads);directory(folder);
        File zip=new File(folder,archive.archive.getName()),proof=new File(folder,archive.archive.getName()+".local.json");
        target(folder,zip);target(folder,proof);
        // A mismatched/truncated receipt is never silently replaced or bypassed.
        if(proof.exists())checkReceipt(readReceipt(folder,proof),archive);
        if(zip.exists()){
            verify(folder,zip,archive.bytes,archive.sha256);syncExisting(folder,zip);
            verify(folder,zip,archive.bytes,archive.sha256);
        }else{
            if(proof.exists())throw new IOException("Recibo sin ZIP correspondiente; no se completó automáticamente");
            if(folder.getUsableSpace()<archive.bytes*2+RESERVE)throw new IOException("Espacio insuficiente en Descargas");
            File partial=new File(folder,archive.archive.getName()+"."+UUID.randomUUID().toString()+".partial");
            copyNew(archive.archive,folder,partial,archive.bytes,archive.sha256);
            // renameTo may replace a raced destination on Android. Create the
            // final path exclusively instead. A failed final copy has no receipt.
            copyNew(partial,folder,zip,archive.bytes,archive.sha256);
            verify(folder,partial,archive.bytes,archive.sha256);
            if(!partial.delete())throw new IOException("ZIP copiado; no se pudo retirar su temporal local propio");
        }
        if(!proof.exists()){
            JSONObject receipt=new JSONObject().put("schema","tvbase-recognition-local-export-1")
                .put("destination","android_downloads").put("file",zip.getName()).put("bytes",archive.bytes)
                .put("sha256",archive.sha256).put("usb_copy_verified",false).put("file_sync_verified",true)
                .put("local_readback_sha256_verified",true).put("directory_sync_verified",false)
                .put("note","Copia local para trasladar manualmente al USB; no acredita copia ni persistencia en USB.");
            writeNew(folder,proof,(receipt.toString(2)+"\n").getBytes("UTF-8"));
        }
        checkReceipt(readReceipt(folder,proof),archive);syncExisting(folder,proof);
        checkReceipt(readReceipt(folder,proof),archive);
        verify(folder,zip,archive.bytes,archive.sha256);directory(downloads);
        return new Result(zip,proof,archive.bytes,archive.sha256);
    }
}
