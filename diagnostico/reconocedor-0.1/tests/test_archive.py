"""Runs actual Java ZIP writer and the independent Python reader; host only."""
import importlib.util,json,subprocess,sys,tempfile,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
ECJ=ROOT/'tools/compilar-android/ecj-3.39.0.jar'
JSON=ROOT/'tools/pruebas-reconocedor-json/json-20240303.jar'
def run(args):
    p=subprocess.run([str(x) for x in args],capture_output=True,creationflags=0x08000000)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode('utf8','replace'))
    return p.stdout
def main():
    (HERE/'privado').mkdir(exist_ok=True)
    output=Path(tempfile.mkdtemp(prefix='test-archive-',dir=HERE/'privado'))
    classes=output/'classes';classes.mkdir()
    run([JAVA,'-jar',ECJ,'-8','-encoding','UTF-8','-cp',JSON,'-d',classes,HERE/'src/ReportArchive.java',HERE/'tests/ArchiveHarness.java'])
    result=json.loads(run([JAVA,'-cp',str(classes)+';'+str(JSON),'com.tvbase.reconocimiento.ArchiveHarness',output/'fixture']))
    validation=run([sys.executable,'-X','utf8',HERE/'importar-informes.py','--source',output/'fixture','--verify-only'])
    result['independent_reader_output']=validation.decode('utf8')
    result['java_source_sha256']=hashlib.sha256((HERE/'src/ReportArchive.java').read_bytes()).hexdigest()
    result['scope']='Actual Java archive serialization and PC reader; org.json host implementation. No Android filesystem, UI or USB proof.'
    (output/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({'state':'passed','output':str(output),'archive_bytes':result['bytes'],'unsafe_paths_rejected':result['unsafe_paths_rejected'],'independent_reader_passed':True,'scope':result['scope']},indent=2))
if __name__=='__main__':main()
