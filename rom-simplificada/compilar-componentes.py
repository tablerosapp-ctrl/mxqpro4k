"""Build small ROM components locally; no device access or system installation."""
import argparse,hashlib,json,os,secrets,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'rom-simplificada';BUILD=HERE/'compilacion';BUILD.mkdir(exist_ok=True)
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
KEYTOOL=JAVA.with_name('keytool.exe')
TOOLS=ROOT/'tools/verificacion-apk/build-tools-37/android-37.0'
SDK=ROOT/'tools/compilar-android/android-28.jar'
ECJ=ROOT/'tools/compilar-android/ecj-3.39.0.jar'
KEYS=HERE/'claves-desarrollo';KEYS.mkdir(exist_ok=True)
def run(args):
 p=subprocess.run([str(a) for a in args],capture_output=True,creationflags=0x08000000)
 with (BUILD/'compilacion.log').open('ab') as f:f.write(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(p.stderr.decode('utf8','replace'))
 return p.stdout
secret=KEYS/'password.txt'
if not secret.exists():secret.write_text(secrets.token_urlsafe(32),encoding='ascii')
key=KEYS/'componentes.jks'
if not key.exists():
 run([KEYTOOL,'-genkeypair','-keystore',key,'-storepass:file',secret,'-keypass:file',secret,'-alias','tvbase-development','-keyalg','RSA','-keysize','3072','-validity','3650','-dname','CN=TV Base Development','-storetype','JKS'])
parser=argparse.ArgumentParser();parser.add_argument('--only',choices=['inicio','webview-overlay','acceso-usb']);options=parser.parse_args()
records=[]
for name in ([options.only] if options.only else ['inicio','webview-overlay']):
 src=HERE/'componentes'/name;out=BUILD/name;out.mkdir(exist_ok=True)
 apk=out/'unsigned.apk'
 args=[TOOLS/'aapt2.exe','link','-I',SDK,'--manifest',src/'AndroidManifest.xml','-o',apk,'--min-sdk-version','28','--target-sdk-version','28','--no-resource-deduping','--no-resource-removal']
 if name=='webview-overlay':
  run([TOOLS/'aapt2.exe','compile','--dir',src/'res','-o',out/'resources.zip']);args.append(out/'resources.zip')
 run(args)
 if name!='webview-overlay':
  classes=out/'classes';classes.mkdir(exist_ok=True)
  run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-bootclasspath',SDK,'-d',classes,*sorted(src.glob('*.java'))])
  dex=out/'dex';dex.mkdir(exist_ok=True)
  run([JAVA,'-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',SDK,'--output',dex,*sorted(classes.rglob('*.class'))])
  with zipfile.ZipFile(apk,'a') as z:z.write(dex/'classes.dex','classes.dex')
 aligned=out/'aligned.apk'
 run([TOOLS/'zipalign.exe','-f','4',apk,aligned])
 final=out/(name+'.apk')
 run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','tvbase-development','--ks-pass','file:'+str(secret),'--out',final,aligned])
 proof=run([JAVA,'-jar',TOOLS/'lib/apksigner.jar','verify','--verbose','--print-certs','--min-sdk-version','28','--max-sdk-version','28',final])
 (out/'firma.txt').write_bytes(proof)
 records.append({'component':name,'path':str(final.relative_to(ROOT)),'bytes':final.stat().st_size,'sha256':hashlib.file_digest(final.open('rb'),'sha256').hexdigest()})
print(json.dumps(records,indent=2));(BUILD/((options.only+'-componente.json') if options.only else 'componentes.json')).write_text(json.dumps(records,indent=2),encoding='utf8')
