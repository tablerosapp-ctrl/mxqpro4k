package local.tvbase.acceso;

import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/** Single-stream legacy ADB client. Only the loopback device is reachable from the app. */
final class AdbLocal implements Closeable,Entrada.Access {
  static final int CNXN=0x4e584e43,OPEN=0x4e45504f,OKAY=0x59414b4f,WRTE=0x45545257,CLSE=0x45534c43,AUTH=0x48545541;
  private final Socket socket; private final InputStream in; private final OutputStream out;
  private long deadline; private int next=1;
  private int readTimeoutMillis=5000;
  private int responseRemaining=65536;
  private final Map<Integer,Integer> closed=new HashMap<Integer,Integer>();
  private static final byte[] EMPTY=new byte[0];
  static AdbLocal connect() throws IOException { return new AdbLocal("127.0.0.1",5555); }
  // Test-only harness can use another loopback port; never accepts non-loopback addresses.
  AdbLocal(String host,int port) throws IOException {
    if(!"127.0.0.1".equals(host))throw new IOException("Solo se permite el propio TV");
    socket=new Socket();socket.connect(new InetSocketAddress(host,port),3000);socket.setSoTimeout(5000);
    in=socket.getInputStream();out=socket.getOutputStream();deadline=System.nanoTime()+15000000000L;
    try {send(CNXN,0x01000000,4096,"host::tvbase\0".getBytes(StandardCharsets.UTF_8));Packet p=read();
      if(p.command==AUTH)throw new IOException("El TV exige autenticar ADB. No se reinició ni se cambió la seguridad.");
      if(p.command!=CNXN||p.a<0x01000000||p.b<4096)throw new IOException("Respuesta ADB incompatible");
    }catch(IOException e){socket.close();throw e;}
  }
  static final class Packet {int command,a,b;byte[] data;}
  private static int sum(byte[] b){int s=0;for(byte v:b)s+=v&255;return s;}
  private void exact(byte[] b)throws IOException{int n=0;while(n<b.length){long remaining=deadline-System.nanoTime();if(remaining<=0)throw new SocketTimeoutException("Tiempo máximo de respuesta");socket.setSoTimeout((int)Math.min(readTimeoutMillis,(remaining+999999L)/1000000L));int got=in.read(b,n,b.length-n);if(got<0)throw new EOFException("El TV cerró la conexión");n+=got;}}
  private Packet read()throws IOException{
    byte[] h=new byte[24];exact(h);ByteBuffer x=ByteBuffer.wrap(h).order(ByteOrder.LITTLE_ENDIAN);Packet p=new Packet();p.command=x.getInt();p.a=x.getInt();p.b=x.getInt();int len=x.getInt(),crc=x.getInt(),magic=x.getInt();
    if(magic!=(p.command^0xffffffff)||len<0||len>4096)throw new IOException("Cabecera ADB inválida");p.data=new byte[len];exact(p.data);if(sum(p.data)!=crc)throw new IOException("Checksum ADB inválido");return p;
  }
  private void send(int cmd,int a,int b,byte[] data)throws IOException{
    ByteBuffer h=ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN);h.putInt(cmd).putInt(a).putInt(b).putInt(data.length).putInt(sum(data)).putInt(cmd^0xffffffff);out.write(h.array());out.write(data);out.flush();
  }
  String shell(String command)throws IOException{
    if(!command.equals("id")&&!command.equals("cat /proc/device-tree/amlogic-dt-id")&&!command.equals("getprop ro.build.version.sdk")&&!command.equals("cat /proc/partitions"))throw new IOException("Consulta no permitida");
    return service("shell:"+command,15000000000L);
  }
  public String entryStep(int step,String directory,String token)throws IOException {
    String command=EntradaScripts.command(step,directory,token);
    readTimeoutMillis=step==1?300000:15000;
    try{return service("shell:"+command,step==1?300000000000L:15000000000L);}finally{readTimeoutMillis=5000;socket.setSoTimeout(5000);}
  }
  private String service(String name,long timeout)throws IOException{
    if(!name.startsWith("shell:")||(name+"\0").getBytes(StandardCharsets.UTF_8).length>4096)throw new IOException("Servicio o tamaño ADB no permitido");
    deadline=System.nanoTime()+timeout;int local=next++,remote=0;boolean accepted=false;ByteArrayOutputStream data=new ByteArrayOutputStream();send(OPEN,local,0,(name+"\0").getBytes(StandardCharsets.UTF_8));
    for(int count=0;count<1000;count++){
      Packet p;
      p=read();
      if(p.b!=local){
        // Android can leave replies in flight after a previous service has closed.
        // Only discard packets for a channel completed on this same connection.
        Integer previous=closed.get(p.b);
        if(previous!=null&&(p.command==OKAY||p.command==WRTE||p.command==CLSE)&&(p.a==previous.intValue()||(p.command==CLSE&&p.a==0)))continue;
        throw new IOException("Canal ADB inesperado: recibido "+p.a+"/"+p.b+", esperado "+remote+"/"+local+", comando "+Integer.toHexString(p.command));
      }
      if(p.command==OKAY&&!accepted){if(p.a==0)throw new IOException("Canal ADB inválido");remote=p.a;accepted=true;continue;}
      if(p.command==OKAY&&accepted&&p.a==remote)continue;
      // AOSP protocol: never acknowledge CLSE. Older adbd also sends CLSE(0,id)
      // for successful closures, accepted only for this connection's live stream.
      if(p.command==CLSE){if(accepted&&p.a!=remote&&p.a!=0)throw new IOException("Cierre ADB inesperado");closed.put(local,remote);if(!accepted)throw new IOException("Consulta rechazada por el TV");return new String(data.toByteArray(),StandardCharsets.UTF_8);}
      if(p.command==WRTE&&accepted&&p.a==remote){if(p.data.length>responseRemaining)throw new IOException("Respuestas superan el límite total de 64 KiB");responseRemaining-=p.data.length;data.write(p.data);send(OKAY,local,remote,EMPTY);continue;}
      throw new IOException("Respuesta ADB inesperada");
    }throw new IOException("Demasiadas respuestas ADB");
  }
  public void close()throws IOException{socket.close();}
}
