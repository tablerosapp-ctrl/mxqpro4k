package local.tvbase.acceso;

import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;

/** One raw exec stream to the existing loopback adbd; no remote host or AUTH support. */
final class AdbLocal implements Closeable {
    interface Progress {void line(String text)throws IOException;}
    static final int CNXN=0x4e584e43,OPEN=0x4e45504f,OKAY=0x59414b4f,WRTE=0x45545257,CLSE=0x45534c43,AUTH=0x48545541;
    private final Socket socket;private final InputStream in;private final OutputStream out;
    private long deadline;private boolean used;
    static AdbLocal connect()throws IOException{return new AdbLocal("127.0.0.1",5555);}
    AdbLocal(String host,int port)throws IOException{
        if(!host.equals("127.0.0.1"))throw new IOException("Solo se permite el propio TV");
        socket=new Socket();socket.connect(new InetSocketAddress(host,port),3000);socket.setSoTimeout(15000);
        in=socket.getInputStream();out=socket.getOutputStream();deadline=System.nanoTime()+15000000000L;
        try{send(CNXN,0x01000000,4096,"host::tvbase-entry09\0".getBytes(StandardCharsets.UTF_8));Packet p=read();
            if(p.command==AUTH)throw new IOException("ADB exige autenticación; no se cambió la seguridad");
            if(p.command!=CNXN||p.a<0x01000000||p.b<4096)throw new IOException("ADB incompatible");
        }catch(IOException e){socket.close();throw e;}
    }
    static final class Packet{int command,a,b;byte[] data;}
    private static int sum(byte[] data){int sum=0;for(byte b:data)sum+=b&255;return sum;}
    private void exact(byte[] bytes)throws IOException{for(int n=0;n<bytes.length;){long remaining=deadline-System.nanoTime();if(remaining<=0)throw new SocketTimeoutException("Plazo de la preparación agotado");socket.setSoTimeout((int)Math.min(65000,(remaining+999999)/1000000));int got=in.read(bytes,n,bytes.length-n);if(got<0)throw new EOFException("ADB cerró antes del resultado");n+=got;}}
    private Packet read()throws IOException{byte[] header=new byte[24];exact(header);ByteBuffer b=ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);Packet p=new Packet();p.command=b.getInt();p.a=b.getInt();p.b=b.getInt();int length=b.getInt(),crc=b.getInt(),magic=b.getInt();
        if(magic!=(p.command^0xffffffff)||length<0||length>4096)throw new IOException("Cabecera ADB inválida");p.data=new byte[length];exact(p.data);if(sum(p.data)!=crc)throw new IOException("Checksum ADB inválido");return p;}
    private void send(int command,int a,int b,byte[] data)throws IOException{ByteBuffer h=ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN);h.putInt(command).putInt(a).putInt(b).putInt(data.length).putInt(sum(data)).putInt(command^0xffffffff);out.write(h.array());out.write(data);out.flush();}
    String call(String apk,String nonce,String operation,Progress progress)throws IOException{
        if(used)throw new IOException("La conexión no se reutiliza ni reintenta");used=true;
        String command=EntryContract.command(apk,nonce,operation);deadline=System.nanoTime()+30000000000L;
        send(OPEN,1,0,("exec:"+command+"\0").getBytes(StandardCharsets.UTF_8));int remote=0,total=0;boolean accepted=false;ByteArrayOutputStream complete=new ByteArrayOutputStream(),line=new ByteArrayOutputStream();
        for(int packets=0;packets<10000;packets++){
            Packet p=read();if(p.b!=1)throw new IOException("Canal ADB inesperado");
            if(p.command==OKAY&&!accepted){if(p.a==0)throw new IOException("Canal inválido");remote=p.a;accepted=true;continue;}
            if(p.command==OKAY&&accepted&&p.a==remote)continue;
            if(p.command==CLSE){if(!accepted||(p.a!=0&&p.a!=remote))throw new IOException("Servicio no aceptado o cierre inesperado");
                if(line.size()!=0)throw new IOException("Salida final incompleta");return new String(complete.toByteArray(),StandardCharsets.UTF_8);}
            if(p.command==WRTE&&accepted&&p.a==remote){total+=p.data.length;if(total>262144)throw new IOException("Salida excede límite");complete.write(p.data);send(OKAY,1,remote,new byte[0]);
                for(byte value:p.data){if(value==10){progress.line(new String(line.toByteArray(),StandardCharsets.UTF_8));line.reset();}else{line.write(value);if(line.size()>16384)throw new IOException("Línea excede límite");}}
                continue;}
            throw new IOException("Respuesta ADB inesperada");
        }
        throw new IOException("Demasiados paquetes ADB");
    }
    public void close()throws IOException{socket.close();}
}
