"""Only PC loopback simulations and POSIX fixture checks; never contacts the TV."""
from pathlib import Path
import hashlib,importlib.util,json,socket,struct,subprocess,threading,tempfile,os,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
HOST=HERE/'host-classes-0.5'
SH=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/usr/bin/sh.exe'
SH_ENV=dict(os.environ,PATH=str(SH.parent)+os.pathsep+os.environ.get('PATH',''))
SRC=ROOT/'rom-simplificada/componentes/acceso-usb'
TOKEN='1234567890abcdef1234567890abcdef'
DIR='/storage/ABCD-1234/TVBASE-evidencia-'+TOKEN
CNXN,OPEN,OKAY,WRTE,CLSE,AUTH=[int.from_bytes(s,'little') for s in (b'CNXN',b'OPEN',b'OKAY',b'WRTE',b'CLSE',b'AUTH')]
def java(*args):
 return subprocess.run([str(JAVA),'-cp',str(HOST),'local.tvbase.acceso.EvidenciaHarness',*map(str,args)],capture_output=True,timeout=25)
def send(s,cmd,a=0,b=0,data=b'',bad=False,fragment=True):
 p=struct.pack('<6I',cmd,a,b,len(data),sum(data)+(1 if bad else 0),cmd^0xffffffff)+data
 for n in range(0,len(p),3 if fragment else len(p)):s.sendall(p[n:n+(3 if fragment else len(p))])
def exact(s,n):
 b=b''
 while len(b)<n:
  q=s.recv(n-len(b));assert q,'unexpected EOF';b+=q
 return b
def recv(s):
 h=struct.unpack('<6I',exact(s,24));assert h[3]<=4096
 d=exact(s,h[3]);assert h[4]==sum(d) and h[5]==h[0]^0xffffffff
 return h[:3],d
commands=[java('dump',n).stdout+b'\0' for n in range(7)]
assert all(commands) and max(map(len,commands))+6<=4096
def test(mode):
 errors=[];seen=[]
 with socket.socket() as server:
  server.bind(('127.0.0.1',0));server.listen();server.settimeout(15)
  def fake():
   try:
    with server.accept()[0] as s:
     s.settimeout(15);h,d=recv(s);assert h[0]==CNXN
     if mode=='auth':send(s,AUTH,1,0,b'challenge');return
     send(s,CNXN,0x1000000,4096,b'device::\0')
     if mode in ('flow','final_failure'):
      queries=[(b'shell:id\0',b'uid=2000(shell) gid=2000(shell)\n'),(b'shell:cat /proc/device-tree/amlogic-dt-id\0',b'gxlx2_p291_1g\0'),(b'shell:getprop ro.build.version.sdk\0',b'28\n')]
      queries += [(b'shell:'+commands[n],('TVBASE_READY:'+DIR if n==0 else 'ERROR final hash' if n==6 and mode=='final_failure' else f'TVBASE_OK:{n}:{TOKEN}').encode()+b'\n') for n in range(7)]
      for i,(expected,payload) in enumerate(queries):
       h,d=recv(s);assert h[0]==OPEN and d==expected,(i,d[:80]);seen.append('profile' if i<3 else f'evidence-stage-{i-3}')
       assert d.startswith(b'shell:') and b'reboot:' not in d and b'am start' not in d and b'setprop ' not in d
       local=h[1];remote=9+i
       if i:
        send(s,CLSE,0,local-1);send(s,WRTE,remote-1,local-1,b'late data must be discarded')
       send(s,OKAY,remote,local);send(s,WRTE,remote,local,payload);assert recv(s)[0]==(OKAY,local,remote);send(s,CLSE,0 if i%2 else remote,local)
      assert s.recv(1)==b'';return
     h,d=recv(s);assert h[0]==OPEN and d==b'shell:id\0';seen.append('shell:id');local=h[1]
     if mode=='refused':send(s,CLSE,0,local);return
     send(s,OKAY,9,local)
     if mode=='deadline':
      time.sleep(.24)
      s.sendall(struct.pack('<6I',WRTE,9,local,3,294,WRTE^0xffffffff)[:3])
      s.settimeout(2);assert s.recv(1)==b'';return
     if mode=='early_eof':return
     if mode=='unknown_channel':send(s,WRTE,9,local+77,b'wrong');assert s.recv(1)==b'';return
     if mode=='duplicate_ready':send(s,OKAY,9,local)
     if mode=='response_limit':
      for i in range(17):
       send(s,WRTE,9,local,b'x'*4096,fragment=False)
       if i<16:assert recv(s)[0]==(OKAY,local,9)
      assert s.recv(1)==b'';return
     payload=b'uid=2000(shell) gid=2000(shell)\n'
     send(s,WRTE,9,local,payload,bad=mode=='bad_checksum')
     if mode=='bad_checksum':return
     assert recv(s)[0]==(OKAY,local,9);send(s,CLSE,0 if mode=='zero_close' else 9,local);assert s.recv(1)==b''
   except Exception as e:errors.append(repr(e))
  thread=threading.Thread(target=fake);thread.start()
  started=time.monotonic()
  p=java(server.getsockname()[1],*(['flow'] if mode in ('flow','final_failure') else ['deadline'] if mode=='deadline' else []))
  elapsed=time.monotonic()-started
  thread.join(15);assert not thread.is_alive() and not errors,(mode,errors,p.stderr)
  expected=mode in ('shell','zero_close','duplicate_ready','flow')
  assert (p.returncode==0)==expected,(mode,p.stdout,p.stderr)
  if mode=='flow':assert b'guardada y comprobada' in p.stdout and b'late data' not in p.stdout
  if mode=='deadline':assert elapsed<1.5 and b'SocketTimeoutException' in p.stderr,(elapsed,p.stderr)
  return {'case':mode,'passed':True,'observed_services':seen,'exit':p.returncode}
rows=[test(x) for x in ['shell','auth','bad_checksum','early_eof','refused','zero_close','unknown_channel','duplicate_ready','response_limit','flow','final_failure','deadline']]
guards=java('guards');assert guards.returncode==0,guards.stderr
outside=java('external_host');assert outside.returncode!=0 and 'Solo se permite'.encode() in outside.stderr
spec=importlib.util.spec_from_file_location('evscripts',SRC/'generar-scripts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
syntax=[]
for script in sorted((SRC/'scripts').glob('*.sh')):
 p=subprocess.run([str(SH),'-n',str(script)],capture_output=True,timeout=10,env=SH_ENV);assert p.returncode==0,(script,p.stderr)
 syntax.append({'path':script.relative_to(ROOT).as_posix(),'passed':True})
# Run the exact common + copy functions against synthetic binary files on the PC.
fixture=Path(tempfile.mkdtemp(prefix='fixture-evidencia-0.5-',dir=HERE))
fixture_tool=fixture/'fixture_tool.py'
fixture_tool.write_text('''import hashlib,sys
from pathlib import Path
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if sys.argv[1]=='stat':print(Path(sys.argv[2]).stat().st_size)
elif sys.argv[2]=='-c':
 for line in Path(sys.argv[3]).read_text().splitlines():
  expected,path=line.split('  ',1)
  if sha(path)!=expected:sys.exit(1)
else:print(sha(sys.argv[2])+'  '+sys.argv[2])
''',encoding='utf8')
def shell_case(name,body,expected,files=None,expected_packages=None):
 out=fixture/name;out.mkdir()
 usb=out/'usb';usb.mkdir()
 (usb/'TVBASE-MEDIA.txt').write_text('TVBASE-P291-20260906-4dc82786\n')
 target=usb/('TVBASE-evidencia-'+TOKEN);target.mkdir();(target/'INICIO.txt').write_text(TOKEN+'\n')
 for filename,contents in (files or {}).items():(target/filename).write_text(contents,encoding='utf8',newline='\n')
 source=out/'binary.dat';source.write_bytes(bytes(range(256))*129+b'\0\xff\xfe\n\r')
 path=out/'case.sh'
 header=f"tv_t='{TOKEN}'; tv_d='{target.as_posix()}';\n"
 # MinGit lacks these three utilities. The shim supplies deterministic fixtures,
 # not an assertion that Android toybox or physical USB flushes have run.
 header+=f'''stat() {{ '{Path(sys.executable).as_posix()}' '{fixture_tool.as_posix()}' stat "$3"; }}
sha256sum() {{ '{Path(sys.executable).as_posix()}' '{fixture_tool.as_posix()}' hash "$@"; }}
sync() {{ return 0; }}
'''
 script=header+mod.COMMON+mod.COPY+f"\ntv_log=\"$tv_d/copy.txt\"; printf 'TEST\\n' > \"$tv_log\"\ntv_source='{source.as_posix()}'\n"+body
 path.write_text(script,encoding='utf8',newline='\n')
 p=subprocess.run([str(SH),str(path)],capture_output=True,timeout=15,env=SH_ENV)
 assert (p.returncode==0)==expected,(name,p.returncode,p.stdout,p.stderr)
 if name=='binary_copy':
  assert (target/'copy.bin').read_bytes()==source.read_bytes()
  assert hashlib.sha256(source.read_bytes()).hexdigest().encode() in (target/'copy.txt').read_bytes()
 if name=='size_limit':assert not (target/'copy.bin').exists()
 if name=='noclobber':assert (target/'copy.bin').read_bytes()==b'preserved\n'
 if expected_packages is not None:assert (target/'paquetes.txt').read_text().splitlines()==expected_packages+['FIN-'+TOKEN]
 if name=='no_apk_available':assert 'rutas_APK_devuelvas=0' in (target/'apk-y-certificados.txt').read_text()
 if name=='missing_required_report':assert b'falta informe obligatorio' in p.stdout
 return {'case':name,'passed':True,'exit':p.returncode}
fixtures=[
 shell_case('binary_copy','copy_one "$tv_source" copy.bin 2097152\nprintf "FIN-%s\\n" "$tv_t" >> "$tv_log"\nseal copy.txt\n',True),
 shell_case('size_limit','copy_one "$tv_source" copy.bin 32\n',True),
 shell_case('noclobber','printf "preserved\\n" > "$tv_d/copy.bin"\ncopy_one "$tv_source" copy.bin 2097152\n',False),
 shell_case('sync_failure','sync() { return 1; }\ncopy_one "$tv_source" copy.bin 2097152\n',False),
 shell_case('hash_failure','sha256sum() { return 1; }\ncopy_one "$tv_source" copy.bin 2097152\n',False),
 shell_case('incomplete_report','printf "truncated\\n" >> "$tv_log"\nseal copy.txt\n',False),
 shell_case('resolved_package',mod.SELECT,True,{'resolucion.txt':'com.vendor.update/.Main\n'},['com.vendor.update','com.droidlogic.otaupgrade']),
 shell_case('resolved_fallback_deduplicated',mod.SELECT,True,{'resolucion.txt':'com.droidlogic.otaupgrade/.Main\n'},['com.droidlogic.otaupgrade']),
 shell_case('malicious_component',mod.SELECT,True,{'resolucion.txt':'com.vendor.update/.Main;setprop sys.powerctl reboot\n'},['com.droidlogic.otaupgrade']),
 shell_case('ambiguous_components',mod.SELECT,True,{'resolucion.txt':'com.one/.Main\ncom.two/.Main\n'},['com.droidlogic.otaupgrade']),
 shell_case('no_component',mod.SELECT,True,{'resolucion.txt':'No activity found\n'},['com.droidlogic.otaupgrade']),
 shell_case('android_resolver',mod.SELECT,True,{'resolucion.txt':'android/com.android.internal.app.ResolverActivity\n'},['com.droidlogic.otaupgrade']),
 shell_case('no_apk_available','copy_one() { printf "FIXTURE OPTIONAL COPY %s\\n" "$1" >> "$tv_log"; }\n'+mod.UPDATER,True,{'pm-path.txt':'FIN-'+TOKEN+'\n'}),
 shell_case('four_apk_global_limit','copy_one() { printf "FIXTURE COPY %s\\n" "$1" >> "$tv_log"; }\n'+mod.UPDATER,False,{'pm-path.txt':''.join('package:/system/Updater%d.apk\n'%i for i in range(5))+'FIN-'+TOKEN+'\n'}),
 shell_case('missing_required_report','''for i in 1 2 3 4 5; do printf '%s\\n' "$tv_t" > "$tv_d/etapa-$i.ok"; done
for n in pstore resolucion paquetes actualizador pm-path apk-y-certificados init-y-fstab; do printf 'FIN-%s\\n' "$tv_t" > "$tv_d/$n.txt"; sha256sum "$tv_d/$n.txt" > "$tv_d/$n.txt.sha256"; done
'''+mod.FINAL,False),
]
assert '/sys/fs/pstore/dmesg-ramoops*' in mod.PSTORE
apk=ROOT/'rom-simplificada/compilacion/acceso-usb-0.5/acceso-usb.apk'
with apk.open('rb') as f:apk_hash=hashlib.file_digest(f,'sha256').hexdigest()
sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*.java'))}
state='passed' if all(x['passed'] for x in rows+syntax+fixtures) and guards.returncode==0 and outside.returncode!=0 else 'failed'
record={'state':state,'version':'0.5','apk_sha256':apk_hash,'tested_source_sha256':sources,'scope':'PC only; no TV commands executed','adb':rows,'guard_result':guards.stdout.decode().strip(),'external_host_rejected':True,'shell_syntax':syntax,'shell_fixtures':fixtures,'fixture_adapters':'MinGit has no stat/sha256sum/sync: Python implements size/SHA, sync is a success/failure stub. Tests cover control flow and binary bytes, not Android toybox or physical flushing.','max_actual_open_bytes':max(map(len,commands))+6,'total_response_limit_bytes':65536,'tv_shell_tested':False,'tv_capture_tested':False,'flush':'checked sync exit plus SHA readback; no claim of physical USB hardware durability'}
(HERE/'EVIDENCIA-TESTS-0.5.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,indent=2))
