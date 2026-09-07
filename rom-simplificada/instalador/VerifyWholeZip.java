import java.nio.file.*;
import java.nio.*;
import java.util.*;
import java.lang.reflect.*;
/** Independent verification using OpenJDK's PKCS7 implementation, not the Python signer/parser. */
public class VerifyWholeZip {
 public static void main(String[] args)throws Exception{
  byte[] zip=Files.readAllBytes(Paths.get(args[0]));ByteBuffer f=ByteBuffer.wrap(zip,zip.length-6,6).order(ByteOrder.LITTLE_ENDIAN);
  int start=f.getShort()&65535,magic=f.getShort()&65535,comment=f.getShort()&65535;if(magic!=65535||start>comment||start<=6)throw new Exception("Bad OTA footer");
  byte[] sig=Arrays.copyOfRange(zip,zip.length-start,zip.length-6),content=Arrays.copyOf(zip,zip.length-comment-2);
  Class<?> type=Class.forName("sun.security.pkcs.PKCS7");Object pkcs=type.getConstructor(byte[].class).newInstance((Object)sig);
  Object[] verified=(Object[])type.getMethod("verify",byte[].class).invoke(pkcs,(Object)content);
  if(verified==null||verified.length!=1)throw new Exception("Whole-file signature NOT verified");
  System.out.println("OpenJDK PKCS7: whole-file SHA256/RSA signature verified");
 }
}
