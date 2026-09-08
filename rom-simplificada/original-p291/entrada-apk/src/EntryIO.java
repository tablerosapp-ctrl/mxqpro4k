package local.tvbase.acceso;

import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileDescriptor;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;

/** Directed file operations; only PreparationHelper chooses constant destinations. */
final class EntryIO {
    interface Progress {void stage(String name) throws Exception;}
    static final class Snapshot {
        final byte[] bytes; final StructStat stat; final String path,sha;
        Snapshot(String path,byte[] bytes,StructStat stat) throws IOException {
            this.path=path;this.bytes=bytes;this.stat=stat;this.sha=EntryCodec.sha(bytes);
        }
    }
    static final class Media {
        final String root;final long device,inode;final String mount;
        Media(String root,StructStat st,String mount) {this.root=root;device=st.st_dev;inode=st.st_ino;this.mount=mount;}
        void verify() throws Exception {
            StructStat st=Os.lstat(root);
            EntryCodec.require(OsConstants.S_ISDIR(st.st_mode)&&st.st_dev==device&&st.st_ino==inode,"Cambió el pendrive");
            EntryCodec.require(mount.equals(mountFor(root)),"Cambió el montaje del pendrive");
            verifyUsbMount(root,mount,st.st_dev);
            marker(root);
        }
    }

    static boolean absent(String path) throws Exception {
        try {Os.lstat(path);return false;}
        catch(ErrnoException e) {if(e.errno==OsConstants.ENOENT)return true;throw e;}
    }
    static FileDescriptor directory(String path) throws Exception {
        StructStat st=Os.lstat(path);EntryCodec.require(OsConstants.S_ISDIR(st.st_mode),"Directorio con enlace o tipo inesperado");
        FileDescriptor fd=Os.open(path,OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0);
        boolean accepted=false;
        try {StructStat now=Os.fstat(fd);EntryCodec.require(OsConstants.S_ISDIR(now.st_mode)&&same(st,now),"Cambió directorio");accepted=true;return fd;}
        finally {if(!accepted)Os.close(fd);}
    }
    static boolean same(StructStat a,StructStat b) {return a.st_dev==b.st_dev&&a.st_ino==b.st_ino&&a.st_size==b.st_size&&a.st_mtime==b.st_mtime&&a.st_mode==b.st_mode;}
    static void syncDirectory(String path) throws Exception {
        FileDescriptor fd=directory(path);try{Os.fsync(fd);}finally{Os.close(fd);}
    }
    static void createDirectory(String path,String parent) throws Exception {
        EntryCodec.require(path.startsWith(parent+"/")&&path.indexOf('/',parent.length()+1)<0,"Directorio fuera de su padre");
        FileDescriptor fd=directory(parent);
        try{Os.mkdir(path,0700);Os.fsync(fd);}finally{Os.close(fd);}
        syncDirectory(path);
    }
    static Snapshot smallFile(String path,int limit) throws Exception {
        StructStat before=Os.lstat(path);EntryCodec.require(OsConstants.S_ISREG(before.st_mode),"Origen no es archivo regular: "+path);
        EntryCodec.require(before.st_size>=0&&before.st_size<=limit,"Archivo excede límite: "+path);
        FileDescriptor fd=Os.open(path,OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0);
        try {
            EntryCodec.require(same(before,Os.fstat(fd)),"Cambió origen al abrir");
            byte[] value=read(fd,limit);
            EntryCodec.require(value.length==before.st_size&&same(before,Os.fstat(fd))&&same(before,Os.lstat(path)),"Cambió archivo durante lectura");
            return new Snapshot(path,value,before);
        }finally{Os.close(fd);}
    }
    static byte[] virtual(String path,int limit) throws Exception {
        FileDescriptor fd=Os.open(path,OsConstants.O_RDONLY|OsConstants.O_CLOEXEC,0);
        try{return read(fd,limit);}finally{Os.close(fd);}
    }
    static byte[] read(FileDescriptor fd,int limit) throws Exception {
        ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[65536];
        for(;;){int n=Os.read(fd,buf,0,Math.min(buf.length,limit+1-out.size()));if(n==0)return out.toByteArray();
            EntryCodec.require(n>0,"Resultado de lectura inválido");out.write(buf,0,n);EntryCodec.require(out.size()<=limit,"Lectura excede límite");}
    }
    static String writeNew(String path,byte[] data,String parent) throws Exception {
        EntryCodec.require(path.startsWith(parent+"/")&&path.indexOf('/',parent.length()+1)<0,"Archivo fuera del directorio permitido");
        FileDescriptor dir=directory(parent);
        FileDescriptor fd=Os.open(path,OsConstants.O_WRONLY|OsConstants.O_CREAT|OsConstants.O_EXCL|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0600);
        try{
            write(fd,data,data.length);Os.fsync(fd);
            EntryCodec.require(OsConstants.S_ISREG(Os.fstat(fd).st_mode)&&Os.fstat(fd).st_size==data.length,"Escritura incompleta");
        }finally{try{Os.close(fd);}finally{Os.close(dir);}}
        syncDirectory(parent);
        Snapshot read=smallFile(path,data.length);
        EntryCodec.require(Arrays.equals(data,read.bytes),"Copia leída diferente: "+path);
        return read.sha;
    }
    static void write(FileDescriptor fd,byte[] bytes,int length) throws Exception {
        for(int at=0;at<length;){int n=Os.write(fd,bytes,at,length-at);EntryCodec.require(n>0,"Escritura incompleta");at+=n;}
    }
    static String text(String path,int limit) throws Exception {return new String(virtual(path,limit),StandardCharsets.UTF_8);}
    static String mountFor(String path) throws Exception {
        String found=null;
        for(String line:text("/proc/self/mountinfo",1048576).split("\n")){
            String[] fields=line.split(" ");if(fields.length<10||!fields[4].equals(path))continue;
            int separator=-1;for(int i=6;i<fields.length;i++)if(fields[i].equals("-")){separator=i;break;}
            EntryCodec.require(separator>0&&separator+3<fields.length,"Montaje no interpretable");
            EntryCodec.require(fields[separator+1].equals("vfat")&&Arrays.asList(fields[5].split(",")).contains("rw"),"Se requiere pendrive FAT32 montado en escritura");
            EntryCodec.require(found==null,"Dos montajes coinciden con el volumen");found=line;
        }
        EntryCodec.require(found!=null,"No existe montaje físico FAT32 para el volumen");return found;
    }
    static void verifyUsbMount(String path,String mount,long device)throws Exception{
        String[] fields=mount.split(" ");String[] numbers=fields[2].split(":");
        EntryCodec.require(numbers.length==2&&numbers[0].matches("[0-9]{1,5}")&&numbers[1].matches("[0-9]{1,7}"),"Identidad de montaje no interpretable");
        long major=Long.parseLong(numbers[0]),minor=Long.parseLong(numbers[1]);
        EntryCodec.require(((device>>>8)&0xfff)==major&&((device&0xff)|((device>>>12)&0xfffff00L))==minor,"Dispositivo del volumen difiere de mountinfo");
        String sys="/sys/dev/block/"+major+":"+minor;
        String canonical=new File(sys).getCanonicalPath();
        EntryCodec.require(canonical.startsWith("/sys/devices/")&&canonical.contains("/usb"),"El volumen no proviene de una ruta física USB");
        EntryCodec.require(text(sys+"/dev",64).trim().equals(major+":"+minor),"Identidad sysfs del USB diferente");
        int separator=-1;for(int i=6;i<fields.length;i++)if(fields[i].equals("-")){separator=i;break;}
        EntryCodec.require(separator>0&&fields[separator+2].startsWith("/dev/block/"),"Origen de montaje USB desconocido");
        StructStat node=Os.stat(fields[separator+2]);
        EntryCodec.require(OsConstants.S_ISBLK(node.st_mode)&&((node.st_rdev>>>8)&0xfff)==major
                &&((node.st_rdev&0xff)|((node.st_rdev>>>12)&0xfffff00L))==minor,"Nodo de origen USB no coincide");
    }
    static void marker(String root) throws Exception {
        byte[] data=smallFile(root+"/TVBASE-MEDIA.txt",128).bytes;
        String value=new String(data,StandardCharsets.US_ASCII);
        EntryCodec.require(value.equals(EntryContract.MEDIA)||value.equals(EntryContract.MEDIA+"\n")||value.equals(EntryContract.MEDIA+"\r\n"),"Marcador USB diferente");
    }
    static Media findMedia() throws Exception {
        File[] volumes=new File("/mnt/media_rw").listFiles();EntryCodec.require(volumes!=null,"No se pueden enumerar volúmenes físicos");
        List<Media> found=new ArrayList<Media>();
        for(File file:volumes){String name=file.getName();if(!name.matches("[A-Za-z0-9_-]{1,64}"))continue;
            String path="/mnt/media_rw/"+name;StructStat st=Os.lstat(path);if(!OsConstants.S_ISDIR(st.st_mode))continue;
            if(absent(path+"/TVBASE-MEDIA.txt"))continue;
            marker(path);String mount=mountFor(path);verifyUsbMount(path,mount,st.st_dev);found.add(new Media(path,st,mount));
        }
        EntryCodec.require(found.size()==1,"Debe existir un único pendrive TVBASE físico; encontrados: "+found.size());
        return found.get(0);
    }
    static String verifyZip(Media media,String filename,long size,String expected,Progress progress) throws Exception {
        media.verify();String path=media.root+"/"+filename;StructStat before=Os.lstat(path);
        EntryCodec.require(OsConstants.S_ISREG(before.st_mode)&&before.st_size==size,"ZIP ausente, enlace o tamaño diferente");
        FileDescriptor fd=Os.open(path,OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");long total=0,next=16777216;byte[] buf=new byte[1048576];
        try{EntryCodec.require(same(before,Os.fstat(fd)),"ZIP cambió al abrir");for(;;){int n=Os.read(fd,buf,0,buf.length);if(n==0)break;
                EntryCodec.require(n>0,"Lectura ZIP inválida");total+=n;EntryCodec.require(total<=size,"ZIP creció");digest.update(buf,0,n);
                if(total>=next){progress.stage("Verificando ROM: "+(total*100/size)+" %");next+=16777216;}}
            EntryCodec.require(total==size&&same(before,Os.fstat(fd))&&same(before,Os.lstat(path)),"ZIP cambió durante la lectura");
        }finally{Os.close(fd);}
        StringBuilder result=new StringBuilder();for(byte b:digest.digest())result.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        EntryCodec.require(result.toString().equals(expected),"SHA de la ROM no coincide");media.verify();return path;
    }
    static FileDescriptor block(String name,int minor,int flags,int expectedSize) throws Exception {
        EntryCodec.require(name.equals("env")||name.equals("misc"),"Partición no permitida");
        String path="/dev/block/"+name;StructStat st=Os.lstat(path);
        EntryCodec.require(OsConstants.S_ISBLK(st.st_mode),"Alias no es nodo de bloque directo");
        long major=(st.st_rdev>>>8)&0xfff,observedMinor=(st.st_rdev&0xff)|((st.st_rdev>>>12)&0xfffff00L);
        EntryCodec.require(major==179&&observedMinor==minor,"Identidad de partición diferente");
        String sectors=text("/sys/dev/block/179:"+minor+"/size",64).trim();
        EntryCodec.require(sectors.matches("[0-9]{1,12}")&&Long.parseLong(sectors)*512L==expectedSize,"Tamaño de partición diferente");
        FileDescriptor fd=Os.open(path,flags|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0);StructStat opened=Os.fstat(fd);
        if(!OsConstants.S_ISBLK(opened.st_mode)||opened.st_rdev!=st.st_rdev){Os.close(fd);throw new IOException("Partición cambió al abrir");}
        return fd;
    }
    static byte[] readBlock(String name,int minor) throws Exception {
        FileDescriptor fd=block(name,minor,OsConstants.O_RDONLY,EntryCodec.PART_SIZE);
        try{byte[] data=read(fd,EntryCodec.PART_SIZE);EntryCodec.require(data.length==EntryCodec.PART_SIZE,"Lectura de partición corta");return data;}finally{Os.close(fd);}
    }
    static void replacePrefix(String name,int minor,byte[] before,byte[] after,int length) throws Exception {
        EntryCodec.require((name.equals("env")&&length==65536)||(name.equals("misc")&&length==2048),"Alcance de escritura no permitido");
        EntryCodec.require(before.length==EntryCodec.PART_SIZE&&after.length==EntryCodec.PART_SIZE,"Tamaño de snapshot inválido");
        EntryCodec.require(Arrays.equals(Arrays.copyOfRange(before,length,before.length),Arrays.copyOfRange(after,length,after.length)),"Cambios fuera del prefijo");
        FileDescriptor fd=block(name,minor,OsConstants.O_RDWR,EntryCodec.PART_SIZE);
        try{
            EntryCodec.require(Arrays.equals(before,read(fd,EntryCodec.PART_SIZE)),"Origen cambió antes de escribir "+name);
            EntryCodec.require(Os.lseek(fd,0,OsConstants.SEEK_SET)==0,"No se pudo ubicar prefijo");
            write(fd,after,length);Os.fsync(fd);
            EntryCodec.require(Os.lseek(fd,0,OsConstants.SEEK_SET)==0,"No se pudo ubicar lectura posterior");
            EntryCodec.require(Arrays.equals(after,read(fd,EntryCodec.PART_SIZE)),"La lectura posterior de "+name+" difiere");
        }finally{Os.close(fd);}
    }
}
