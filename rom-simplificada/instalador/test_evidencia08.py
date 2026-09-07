"""Only PC loopback simulations and POSIX fixture checks; never contacts the TV."""
from pathlib import Path
import hashlib,importlib.util,json,socket,struct,subprocess,threading,tempfile,os,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
HOST=HERE/'host-classes-0.8'
SH=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/usr/bin/sh.exe'
SH_ENV=dict(os.environ,PATH=str(SH.parent)+os.pathsep+os.environ.get('PATH',''))
SRC=ROOT/'rom-simplificada/componentes/acceso-usb-0.8'
TOKEN='1234567890abcdef1234567890abcdef'
DIR='/storage/ABCD-1234/TVBASE-postintento-'+TOKEN
CNXN,OPEN,OKAY,WRTE,CLSE,AUTH=[int.from_bytes(s,'little') for s in (b'CNXN',b'OPEN',b'OKAY',b'WRTE',b'CLSE',b'AUTH')]
def java(*args):
 return subprocess.run([str(JAVA),'-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-cp',str(HOST),'local.tvbase.acceso.EvidenciaHarness08',*map(str,args)],capture_output=True,timeout=25)
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
commands=[java('dump',n).stdout+b'\0' for n in range(11)]
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
      queries += [(b'shell:'+commands[n],('TVBASE_READY:'+DIR if n==0 else 'ERROR final hash' if n==10 and mode=='final_failure' else f'TVBASE_OK:{n}:{TOKEN}').encode()+b'\n') for n in range(11)]
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

MKSH=ROOT/'tools/mksh-audit/mksh.exe'
MINGIT=SH.parent.as_posix();CYG_PATH='/cygdrive/'+MINGIT[0].lower()+MINGIT[2:]
mksh_syntax=[]
for script in sorted((SRC/'scripts').glob('*.sh')):
 p=subprocess.run([str(MKSH),'-n',str(script)],capture_output=True,timeout=10)
 assert p.returncode==0,(script,p.stderr)
 mksh_syntax.append({'path':script.relative_to(ROOT).as_posix(),'passed':True})
alias_result=subprocess.run([str(MKSH),'-c','alias hash'],capture_output=True,timeout=10)
assert alias_result.returncode==0 and b'alias -t' in alias_result.stdout
fixture=Path(tempfile.mkdtemp(prefix='fixture-evidencia-0.8-',dir=HERE))
utility=fixture/'utility.py'
utility.write_text('''import sys,hashlib,time,subprocess
from pathlib import Path
sys.stdout.reconfigure(newline='\\n')
mode=sys.argv[1]
if mode=='stat': print(Path(sys.argv[2]).stat().st_size)
elif mode=='sha':
 with Path(sys.argv[2]).open('rb') as f: print(hashlib.file_digest(f,'sha256').hexdigest()+'  '+sys.argv[2])
elif mode=='ok': sys.stdout.buffer.write(b'respuesta\\n')
elif mode=='denied': sys.stderr.write('Permission denied\\n'); sys.exit(1)
elif mode=='overflow': sys.stdout.write('x'*4096)
elif mode=='wait': time.sleep(5)
elif mode=='change': Path(sys.argv[2]).write_bytes(b'changed')
elif mode=='timeout':
 p=subprocess.Popen(sys.argv[3:])
 try: sys.exit(p.wait(timeout=float(sys.argv[2])))
 except subprocess.TimeoutExpired:
  p.kill(); p.wait(); sys.exit(137)
''',encoding='utf8')

def shell_case(name,body,expected=True,check=None,setup=None,create=False,prefix=''):
 out=fixture/name;out.mkdir();usb=out/'usb';usb.mkdir()
 (usb/'TVBASE-MEDIA.txt').write_text('TVBASE-P291-20260906-4dc82786\n',encoding='utf8',newline='\n')
 target=usb/('TVBASE-postintento-'+TOKEN)
 if not create:
  target.mkdir();(target/'INICIO.txt').write_text(TOKEN+'\n',encoding='utf8',newline='\n')
 pst=out/'pstore';pst.mkdir();(pst/'console-ramoops-0').write_bytes(b'[42.000000@0] test\n')
 dt=out/'dt';dt.write_bytes(b'gxlx2_p291_1g\0')
 if setup:setup(target,pst,usb,dt)
 py=Path(sys.executable).as_posix();u=utility.as_posix()
 header=f"PATH='{CYG_PATH}'; export PATH\ntv_t='{TOKEN}';tv_d='{target.as_posix()}'\n"
 header+=f'''id() {{ printf '2000\\n'; }}
getprop() {{ printf '28\\n'; }}
stat() {{ '{py}' '{u}' stat "$3"; }}
t_fixture_hash() {{ '{py}' '{u}' sha "$1"; }}
t_tool() {{
 case "$1" in
 timeout)
  t_limit=$4; shift 4
  if [ "$1" = t_tool ]; then
   if [ "$2" = sleep ]; then return 137; fi
   "$@"
  else '{py}' '{u}' timeout "$t_limit" "$@"; fi;;
 sha256sum) shift; t_fixture_hash "$@";;
 *) "$@";;
 esac
}}
'''
 text=header+prefix+('' if create else mod.COMMON+mod.RUN)+body
 text=text.replace('/system/bin/toybox','t_tool').replace('/proc/device-tree/amlogic-dt-id',dt.as_posix()).replace('/sys/fs/pstore',pst.as_posix())
 if create:text=text.replace('/storage/* /mnt/media_rw/*',"'"+usb.as_posix()+"'")
 path=out/'case.sh';path.write_text(text,encoding='utf8',newline='\n')
 started=time.monotonic();p=subprocess.run([str(MKSH),str(path)],capture_output=True,timeout=90)
 assert (p.returncode==0)==expected,(name,p.returncode,p.stdout,p.stderr)
 if check:check(target,pst,p)
 return {'case':name,'passed':True,'exit':p.returncode,'seconds':round(time.monotonic()-started,3)}

def command(mode):return "'"+Path(sys.executable).as_posix()+"' '"+utility.as_posix()+"' "+mode
def status(t,name):return (t/(name+'.estado')).read_text()
def assert_true(value):assert value
def verify_report(t,pst,p):
 assert (t/'sample.txt').read_bytes()==b'respuesta\n'
 assert 'exit=0' in status(t,'sample') and 'truncado=no' in status(t,'sample')
 assert (t/'sample.txt.sha256').read_text().strip()==hashlib.sha256(b'respuesta\n').hexdigest()

fixtures=[
 shell_case('create_profile_and_timeout_preflight',mod.CREATE,create=True,check=lambda t,s,p:assert_true(t.is_dir())),
 shell_case('create_no_usb',mod.CREATE,False,create=True,setup=lambda t,s,u,d:(u/'TVBASE-MEDIA.txt').write_text('wrong')),
 shell_case('create_timeout_missing',mod.CREATE,False,create=True,prefix='t_tool() { return 127; }\n'),
 shell_case('root_profile_rejected','true\n',False,prefix="id() { printf '0\\n'; }\n"),
 shell_case('wrong_dt_rejected','true\n',False,setup=lambda t,s,u,d:d.write_bytes(b'gxlx_p271_1g\0')),
 shell_case('wrong_marker_rejected','true\n',False,setup=lambda t,s,u,d:(u/'TVBASE-MEDIA.txt').write_text('wrong')),
 shell_case('selftest_with_mksh_hash_alias',mod.SETUP,check=lambda t,s,p:assert_true((t/'autocontrol.bin').read_bytes()==b'abc')),
 shell_case('empty_sha_rejected','t_fixture_hash() { return 0; }\n'+mod.SETUP,False),
 shell_case('malformed_sha_rejected',"t_fixture_hash() { printf 'abc x\\n'; }\n"+mod.SETUP,False),
 shell_case('sidecar_empty_rejected','printf x > "$tv_d/bad"\nprintf "" > "$tv_d/bad.sha256"\ntvbase_verify bad\n',False),
 shell_case('report_ok','tvbase_run sample 2 64 '+command('ok')+'\n',check=verify_report),
 shell_case('denial_preserved','tvbase_run sample 2 64 '+command('denied')+'\n',check=lambda t,s,p:assert_true('exit=1' in status(t,'sample'))),
 shell_case('real_timeout_preserved','tvbase_run sample 0.2 64 '+command('wait')+'\n',check=lambda t,s,p:assert_true('exit=137' in status(t,'sample'))),
 shell_case('truncation_explicit','tvbase_run sample 2 64 '+command('overflow')+'\n',check=lambda t,s,p:assert_true('truncado=si' in status(t,'sample') and (t/'sample.txt').stat().st_size==65)),
 shell_case('no_overwrite','printf preserved > "$tv_d/sample.txt"\ntvbase_run sample 2 64 '+command('ok')+'\n',False,check=lambda t,s,p:assert_true((t/'sample.txt').read_bytes()==b'preserved')),
 shell_case('pstore_origin_and_copy_sha',mod.PSTORE,check=lambda t,s,p:assert_true((t/'console-ramoops-0.bin').read_bytes()==(s/'console-ramoops-0').read_bytes())),
 shell_case('pstore_empty_helper_rejected','tvbase_sha() { return 0; }\n'+mod.PSTORE,False),
 shell_case('pstore_size_limit_recorded',mod.PSTORE,setup=lambda t,s,u,d:(s/'console-ramoops-0').write_bytes(b'x'*2097153),check=lambda t,s,p:assert_true('TAMANO_NO_ADMITIDO' in (t/'pstore.txt').read_text() and not (t/'console-ramoops-0.bin').exists())),
 shell_case('final_missing_stage',mod.FINAL,False),
]
full=mod.SETUP+mod.PSTORE
for i,name in enumerate(('log-anterior','log-actual','wifi','bluetooth','bateria','espacio','webview'),3):
 full+=f'tvbase_run {name} 2 128 '+command('ok')+f'\ntvbase_done {i}\n'
fixtures += [
 shell_case('full_capture_and_final_hashes',full+mod.FINAL,check=lambda t,s,p:assert_true((t/'COMPLETO.txt').exists())),
 shell_case('final_detects_changed_report',full+command('change')+' "$tv_d/wifi.txt"\n'+mod.FINAL,False,check=lambda t,s,p:assert_true(not (t/'COMPLETO.txt').exists())),
]
apk=ROOT/'rom-simplificada/compilacion/acceso-usb-0.8/acceso-usb.apk'
sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*')) if p.is_file()}
for path in sorted((SRC/'scripts').glob('*.sh')):sources[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
for body in [x.read_text(encoding='utf8') for x in (SRC/'scripts').glob('*.sh')]:
 for banned in ('am start','setprop ','svc wifi','svc bluetooth','reboot:', 'setupBcb','/dev/block'):
  assert banned not in body,banned
record={'state':'passed','version':'0.8','apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'tested_source_sha256':sources,'scope':'PC only; no TV commands executed','adb':rows,'guard_result':guards.stdout.decode('utf8').strip(),'external_host_rejected':True,'shell_syntax':syntax,'mksh_syntax':mksh_syntax,'mksh_default_hash_alias':alias_result.stdout.decode().strip(),'shell_fixtures':fixtures,'fixture_adapters':'Real Cygwin mksh with active hash alias; Android paths/profile/SHA/stat mapped to fixtures. Python adapter exercises direct child termination; Android toybox source inspected and device runtime preflight required. No TV or physical flush proof.','max_actual_open_bytes':max(map(len,commands))+6,'tv_capture_tested':False}
(HERE/'EVIDENCIA-TESTS-0.8.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps({'state':'passed','adb':len(rows),'mksh_fixtures':len(fixtures),'syntax':len(syntax),'max_open':record['max_actual_open_bytes'],'apk_sha256':record['apk_sha256']},indent=2))
