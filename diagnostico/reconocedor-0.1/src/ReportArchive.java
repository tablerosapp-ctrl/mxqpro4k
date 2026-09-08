package com.tvbase.reconocimiento;

import org.json.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;
import java.text.Normalizer;

public final class ReportArchive {
    public static final long MAX_TOTAL=2684354560L, MAX_FILE=134217728L;
    public static final int MAX_ENTRIES=20000;
    public static final class Result {
        public final File archive; public final long bytes; public final String sha256;
        Result(File a,long b,String h){archive=a;bytes=b;sha256=h;}
    }
    public static String hex(byte[] v){StringBuilder b=new StringBuilder();for(byte x:v)b.append(String.format(Locale.US,"%02x",x&255));return b.toString();}
    public static String sha(File f)throws Exception {MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[262144];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}return hex(d.digest());}
    public static void write(File f,String value)throws Exception {
        if(f.exists())throw new IOException("El archivo ya existe: "+f.getName());
        try(FileOutputStream out=new FileOutputStream(f)){out.write(value.getBytes("UTF-8"));out.getFD().sync();}
    }
    static String safePath(File root,File file)throws Exception {
        String base=root.getCanonicalPath()+File.separator, full=file.getCanonicalPath();
        String relative=file.getAbsolutePath().substring(root.getAbsolutePath().length()+1);
        if(!full.startsWith(base)||!full.equals(base+relative))throw new IOException("Enlace o ruta fuera de captura");
        String p=full.substring(base.length()).replace(File.separatorChar,'/');
        if(!p.equals("informe.json")&&!p.equals("details")&&!p.equals("drivers")&&!p.startsWith("details/")&&!p.startsWith("drivers/"))throw new IOException("Ruta no admitida en informe: "+p);
        for(String s:p.split("/",-1)){
            String stem=s.split("\\.",2)[0].toUpperCase(Locale.US);
            if(s.length()==0||s.equals(".")||s.equals("..")||s.endsWith(".")||s.endsWith(" ")||s.matches(".*[\\\\:<>\"|?*\\x00-\\x1f].*")||stem.matches("CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]"))throw new IOException("Nombre de archivo no portable");
        }
        return p;
    }
    static void walk(File root,File dir,List<File> files,Set<String> seen)throws Exception {
        File[] list=dir.listFiles();if(list==null)throw new IOException("No se pudo listar captura");
        Arrays.sort(list,new Comparator<File>(){public int compare(File a,File b){return a.getName().compareTo(b.getName());}});
        for(File f:list){
            String rel=safePath(root,f), key=Normalizer.normalize(rel,Normalizer.Form.NFC).toLowerCase(Locale.ROOT);
            if(!seen.add(key))throw new IOException("Ruta duplicada");
            if(f.isDirectory())walk(root,f,files,seen);
            else if(f.isFile()){files.add(f);if(files.size()>MAX_ENTRIES-1)throw new IOException("Demasiados archivos");}
            else throw new IOException("Archivo no ordinario");
        }
    }
    public static Result build(File session,JSONObject report)throws Exception {
        String profile=report.getString("suggested_profile");
        if(!profile.matches("[a-z0-9][a-z0-9_-]{0,63}"))throw new IOException("Perfil inválido");
        String capture=UUID.fromString(report.getString("capture_id")).toString();
        String device=UUID.fromString(report.getString("device_id")).toString();
        write(new File(session,"informe.json"),report.toString(2));
        List<File> files=new ArrayList<>();walk(session,session,files,new HashSet<String>());
        JSONArray records=new JSONArray();long total=0;
        Map<String,String> expected=new LinkedHashMap<>();Map<String,Long> sizes=new LinkedHashMap<>();
        for(File f:files){long length=f.length();if(length>MAX_FILE||(total+=length)>MAX_TOTAL)throw new IOException("Límite del archivo de captura");String p=safePath(session,f),h=sha(f);records.put(new JSONObject().put("path",p).put("bytes",length).put("sha256",h));expected.put(p,h);sizes.put(p,length);}
        JSONObject manifest=new JSONObject().put("schema","tvbase-recognition-files-1").put("capture_id",capture).put("files",records);
        File mf=new File(session,"manifest.json");write(mf,manifest.toString(2));files.add(mf);
        if(mf.length()>16777216L||total+mf.length()>MAX_TOTAL)throw new IOException("Manifiesto demasiado grande");
        expected.put("manifest.json",sha(mf));sizes.put("manifest.json",mf.length());
        String name="TVBASE-"+profile+"-"+device.substring(0,8)+"-"+capture.substring(0,8)+".zip";
        File archive=new File(session.getParentFile(),name),partial=new File(session.getParentFile(),name+".partial");
        if(archive.exists()||!partial.createNewFile())throw new IOException("No sobrescribir otra captura");
        try(FileOutputStream raw=new FileOutputStream(partial);ZipOutputStream zip=new ZipOutputStream(new BufferedOutputStream(raw,262144))){
            zip.setLevel(1);byte[] buffer=new byte[262144];
            for(File f:files){String path=f==mf?"manifest.json":safePath(session,f);zip.putNextEntry(new ZipEntry(path));
                MessageDigest digest=MessageDigest.getInstance("SHA-256");long count=0;
                try(InputStream in=new FileInputStream(f)){int n;while((n=in.read(buffer))!=-1){zip.write(buffer,0,n);digest.update(buffer,0,n);count+=n;if(count>sizes.get(path))throw new IOException("Archivo cambió durante captura");}}
                zip.closeEntry();if(count!=sizes.get(path)||!hex(digest.digest()).equals(expected.get(path)))throw new IOException("Archivo cambió durante empaquetado");
            }
            zip.finish();zip.flush();raw.getFD().sync();
        }
        try(ZipFile zip=new ZipFile(partial)){
            if(zip.size()!=expected.size())throw new IOException("ZIP incompleto");
            for(Map.Entry<String,String> e:expected.entrySet()){
                ZipEntry entry=zip.getEntry(e.getKey());if(entry==null||entry.getSize()!=sizes.get(e.getKey()))throw new IOException("Tamaño incorrecto en ZIP");
                MessageDigest digest=MessageDigest.getInstance("SHA-256");CRC32 crc=new CRC32();long count=0;
                try(InputStream in=zip.getInputStream(entry)){byte[] buffer=new byte[262144];int n;while((n=in.read(buffer))!=-1){digest.update(buffer,0,n);crc.update(buffer,0,n);count+=n;if(count>sizes.get(e.getKey()))throw new IOException("ZIP excede tamaño");}}
                if(count!=sizes.get(e.getKey())||!hex(digest.digest()).equals(e.getValue())||crc.getValue()!=entry.getCrc())throw new IOException("Verificación del ZIP falló");
            }
        }
        if(!partial.renameTo(archive))throw new IOException("No se pudo finalizar captura local");
        return new Result(archive,archive.length(),sha(archive));
    }
}
