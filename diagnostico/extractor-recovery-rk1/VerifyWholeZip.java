import java.nio.file.*;
import java.nio.*;
import java.util.*;
/** Independent PKCS7 parsing and verification by OpenJDK; no Python DER parser. */
public class VerifyWholeZip {
 public static void main(String[] args)throws Exception {
  byte[] zip=Files.readAllBytes(Paths.get(args[0]));
  ByteBuffer f=ByteBuffer.wrap(zip,zip.length-6,6).order(ByteOrder.LITTLE_ENDIAN);
  int start=f.getShort()&65535,magic=f.getShort()&65535,comment=f.getShort()&65535;
  if(magic!=65535||start>comment||start<=6||zip.length<comment+22)throw new Exception("Bad OTA footer");
  byte[] sig=Arrays.copyOfRange(zip,zip.length-start,zip.length-6),content=Arrays.copyOf(zip,zip.length-comment-2);
  Class<?> type=Class.forName("sun.security.pkcs.PKCS7");
  Object pkcs=type.getConstructor(byte[].class).newInstance((Object)sig);
  Object[] signers=(Object[])type.getMethod("getSignerInfos").invoke(pkcs);
  if(signers.length!=1)throw new Exception("One signer required");
  Object digest=signers[0].getClass().getMethod("getDigestAlgorithmId").invoke(signers[0]);
  String name=(String)digest.getClass().getMethod("getName").invoke(digest);
  if(!name.equalsIgnoreCase("SHA-256")&&!name.equalsIgnoreCase("SHA256"))throw new Exception("SHA256 required, got "+name);
  java.security.cert.X509Certificate expected=(java.security.cert.X509Certificate)
   java.security.cert.CertificateFactory.getInstance("X.509").generateCertificate(Files.newInputStream(Paths.get(args[1])));
  java.security.cert.X509Certificate[] certs=(java.security.cert.X509Certificate[])type.getMethod("getCertificates").invoke(pkcs);
  if(certs.length!=1 || !Arrays.equals(certs[0].getEncoded(),expected.getEncoded()))throw new Exception("Untrusted certificate");
  Object[] verified=(Object[])type.getMethod("verify",byte[].class).invoke(pkcs,(Object)content);
  if(verified==null||verified.length!=1)throw new Exception("Whole-file signature NOT verified");
  System.out.println("OpenJDK PKCS7 whole-file RSA/SHA256 signature verified; OEM recovery not executed");
 }
}
