"""Build OEM menu entry 0.7 in a fresh output; never sign with a new key implicitly."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,sys
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'rom-simplificada/componentes/acceso-usb-0.7'
OUT=ROOT/'rom-simplificada/compilacion/acceso-usb-0.7'
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
TOOLS=ROOT/'tools/verificacion-apk/build-tools-37/android-37.0'
SDK=ROOT/'tools/compilar-android/android-28.jar'
ECJ=ROOT/'tools/compilar-android/ecj-3.39.0.jar'
KEYS=ROOT/'rom-simplificada/claves-desarrollo'
assert (KEYS/'componentes.jks').is_file() and (KEYS/'password.txt').is_file()
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,creationflags=0x08000000)
 with (OUT/'compilacion.log').open('ab') as f:f.write(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(p.stderr.decode('utf8','replace'))
 return p.stdout
OUT.mkdir(exist_ok=True)
run([sys.executable,SRC/'generar-scripts.py'])
classes=OUT/'classes'
assert not classes.exists(),"Use a new version/output after a compiled release; do not retain stale classes."
classes.mkdir()
sources=sorted(SRC.glob('*.java'))
run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-bootclasspath',SDK,'-d',classes,*sources])
dex=OUT/'dex';dex.mkdir(exist_ok=True)
run([JAVA,'-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',SDK,'--output',dex,*sorted(classes.rglob('*.class'))])
apk=OUT/'unsigned.apk'
run([TOOLS/'aapt2.exe','link','-I',SDK,'--manifest',SRC/'AndroidManifest.xml','-o',apk,'--min-sdk-version','28','--target-sdk-version','28'])
with zipfile.ZipFile(apk,'a') as z:z.write(dex/'classes.dex','classes.dex')
aligned=OUT/'aligned.apk'
run([TOOLS/'zipalign.exe','-f','4',apk,aligned])
final=OUT/'acceso-usb.apk'
run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','sign','--ks',KEYS/'componentes.jks','--ks-key-alias','tvbase-development','--ks-pass','file:'+str(KEYS/'password.txt'),'--out',final,aligned])
proof=run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','verify','--verbose','--print-certs','--min-sdk-version','28','--max-sdk-version','28',final])
assert b'd2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613' in proof
(OUT/'firma.txt').write_bytes(proof)
badging=run([TOOLS/'aapt2.exe','dump','badging',final])
assert b"versionCode='7'" in badging and b"versionName='0.7'" in badging
(OUT/'badging.txt').write_bytes(badging)
with zipfile.ZipFile(final) as z:
 dexbytes=z.read('classes.dex')
 assert dexbytes.count(b'am start -W -n com.droidlogic.otaupgrade/.MainActivity')==1
 assert b'reboot:recovery' not in dexbytes and b'reboot:update' not in dexbytes and b'EntradaAmlogic' not in dexbytes and b'startActivity' not in dexbytes
record={'component':'acceso-usb','version':'0.7','path':final.relative_to(ROOT).as_posix(),'bytes':final.stat().st_size,'sha256':hashlib.file_digest(final.open('rb'),'sha256').hexdigest(),'signer_sha256':'d2136c0e519d477d2be34b55590d9e548137682f9c2573f330a0a6e91833b613','purpose':'entrada_actualizador_oem','tv_tested':False}
(OUT/'componente.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
host=ROOT/'rom-simplificada/instalador/host-classes-0.7';host.mkdir(exist_ok=True)
run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-d',host,*[p for p in sources if p.name!='Acceso.java'],ROOT/'rom-simplificada/instalador/EntradaHarness07.java'])
print(json.dumps(record,indent=2))
