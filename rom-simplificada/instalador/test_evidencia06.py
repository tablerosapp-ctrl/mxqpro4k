"""Only PC loopback simulations and POSIX fixture checks; never contacts the TV."""
from pathlib import Path
import hashlib,importlib.util,json,socket,struct,subprocess,threading,tempfile,os,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
HOST=HERE/'host-classes-0.6'
SH=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/usr/bin/sh.exe'
SH_ENV=dict(os.environ,PATH=str(SH.parent)+os.pathsep+os.environ.get('PATH',''))
SRC=ROOT/'rom-simplificada/componentes/acceso-usb-0.6'
TOKEN='1234567890abcdef1234567890abcdef'
DIR='/storage/ABCD-1234/TVBASE-evidencia-'+TOKEN
CNXN,OPEN,OKAY,WRTE,CLSE,AUTH=[int.from_bytes(s,'little') for s in (b'CNXN',b'OPEN',b'OKAY',b'WRTE',b'CLSE',b'AUTH')]
def java(*args):
 return subprocess.run([str(JAVA),'-cp',str(HOST),'local.tvbase.acceso.EvidenciaHarness06',*map(str,args)],capture_output=True,timeout=25)
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
commands=[java('dump',n).stdout+b'\0' for n in range(5)]
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
      queries += [(b'shell:'+commands[n],('TVBASE_READY:'+DIR if n==0 else 'ERROR final hash' if n==4 and mode=='final_failure' else f'TVBASE_OK:{n}:{TOKEN}').encode()+b'\n') for n in range(5)]
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

# Real mksh executes the production functions with Android utility bindings
# redirected to deterministic PC fixtures. Its default hash alias stays active.
MKSH=ROOT/'tools/mksh-audit/mksh.exe'
assert MKSH.is_file()
MINGIT=SH.parent.as_posix()
CYG_PATH='/cygdrive/'+MINGIT[0].lower()+MINGIT[2:]
mksh_syntax=[]
for script in sorted((SRC/'scripts').glob('*.sh')):
 p=subprocess.run([str(MKSH),'-n',str(script)],capture_output=True,timeout=10)
 assert p.returncode==0,(script,p.stderr)
 mksh_syntax.append({'path':script.relative_to(ROOT).as_posix(),'passed':True})
alias_result=subprocess.run([str(MKSH),'-c','alias hash'],capture_output=True,timeout=10)
assert alias_result.returncode==0 and b'alias -t' in alias_result.stdout
fixture=Path(tempfile.mkdtemp(prefix='fixture-evidencia-0.6-',dir=HERE))
fixture_tool=fixture/'utility.py'
fixture_tool.write_text('''import hashlib,sys
from pathlib import Path
if sys.argv[1]=='stat':sys.stdout.buffer.write((str(Path(sys.argv[2]).stat().st_size)+'\\n').encode())
else:
 with Path(sys.argv[2]).open('rb') as f:sys.stdout.buffer.write((hashlib.file_digest(f,'sha256').hexdigest()+'  '+sys.argv[2]+'\\n').encode())
''',encoding='utf8')
def shell_case(name,body,expected,files=None,check=None):
 out=fixture/name;out.mkdir();usb=out/'usb';usb.mkdir()
 (usb/'TVBASE-MEDIA.txt').write_text('TVBASE-P291-20260906-4dc82786\n',encoding='utf8',newline='\n')
 target=usb/('TVBASE-evidencia-'+TOKEN);target.mkdir();(target/'INICIO.txt').write_text(TOKEN+'\n',encoding='utf8',newline='\n')
 for filename,contents in (files or {}).items():(target/filename).write_text(contents,encoding='utf8',newline='\n')
 source=out/'binary.dat';source.write_bytes(bytes(range(256))*129+b'\0\xff\xfe\n\r')
 path=out/'case.sh'
 header=f"PATH='{CYG_PATH}'; export PATH\ntv_t='{TOKEN}'; tv_d='{target.as_posix()}'; t_log=\"$tv_d/copy.txt\"\n"
 header+=f'''stat() {{ '{Path(sys.executable).as_posix()}' '{fixture_tool.as_posix()}' stat "$3"; }}
t_fixture_hash() {{ '{Path(sys.executable).as_posix()}' '{fixture_tool.as_posix()}' sha "$@"; }}
sync() {{ return 0; }}
'''
 # Only replace the platform utility path. The tvbase_* function bodies and
 # default mksh hash alias are exactly those used by the APK.
 common=mod.COMMON.replace('/system/bin/toybox sha256sum','t_fixture_hash')
 script=header+common+mod.COPY+f"\nprintf 'TEST\\n' > \"$t_log\"\nt_source='{source.as_posix()}'\n"+body
 path.write_text(script,encoding='utf8',newline='\n')
 p=subprocess.run([str(MKSH),str(path)],capture_output=True,timeout=20)
 assert (p.returncode==0)==expected,(name,p.returncode,p.stdout,p.stderr)
 if check:check(target,source,p)
 return {'case':name,'passed':True,'exit':p.returncode}
def copied(target,source,p):
 assert (target/'copy.bin').read_bytes()==source.read_bytes()
 digest=hashlib.sha256(source.read_bytes()).hexdigest()
 assert ('sha256_original='+digest) in (target/'copy.txt').read_text()
 assert (target/'copy.bin.sha256').read_text().startswith(digest+'  ')
def absent(target,source,p):assert not (target/'copy.bin').exists()
def seed_failed(target,source,p):assert not (target/'cert-copy-attempted').exists()
copy_command='tvbase_copy "$t_source" copy.bin 2097152\n'
fixtures=[
 shell_case('real_mksh_binary_with_hash_alias',copy_command,True,check=copied),
 shell_case('required_size_limit', 'tvbase_copy "$t_source" copy.bin 32\n',False,check=absent),
 shell_case('no_overwrite','printf "preserved\\n" > "$tv_d/copy.bin"\n'+copy_command,False,check=lambda t,s,p: None if (t/'copy.bin').read_bytes()==b'preserved\n' else (_ for _ in ()).throw(AssertionError())),
 shell_case('sync_failure','sync() { return 1; }\n'+copy_command,False),
 shell_case('raw_sha_empty_success','t_fixture_hash() { return 0; }\n'+copy_command,False,check=absent),
 shell_case('helper_empty_success_external_guard','tvbase_sha() { return 0; }\n'+copy_command,False,check=absent),
 shell_case('raw_sha_malformed_success','t_fixture_hash() { printf "abcd  x\\n"; }\n'+copy_command,False,check=absent),
 shell_case('helper_malformed_external_guard','tvbase_sha() { printf "abcd"; }\n'+copy_command,False,check=absent),
 shell_case('blank_sidecar_rejected','printf "body\\n" > "$tv_d/bad.txt"\nprintf "  %s\\n" "$tv_d/bad.txt" > "$tv_d/bad.txt.sha256"\ntvbase_verify bad.txt\n',False),
 shell_case('incomplete_report','printf "truncated\\n" > "$t_log"\ntvbase_seal copy.txt\n',False),
 shell_case('selftest_wrong_sha_before_certificate','t_fixture_hash() { printf "%064d  x\\n" 0; }\ntvbase_copy() { printf attempted > "$tv_d/cert-copy-attempted"; }\n'+mod.PREFLIGHT,False,check=seed_failed),
 shell_case('selftest_empty_sha_before_certificate','t_fixture_hash() { return 0; }\ntvbase_copy() { printf attempted > "$tv_d/cert-copy-attempted"; }\n'+mod.PREFLIGHT,False,check=seed_failed),
]
# Bind only sources to synthetic files; production selection and verification
# still run. A GMS result must fail, never enumerate/copy its split APKs.
source_adapter=mod.COPY.replace('tvbase_copy()','tvbase_fixture_copy()')+'''
tvbase_copy() {
 case "$1" in
  /system/etc/security/otacerts.zip) printf 'certificados\\n' >> "$tv_d/order.txt";;
  /product/app/OTAUpgrade/OTAUpgrade.apk) printf 'OTA\\n' >> "$tv_d/order.txt";;
  *) tvbase_fail 'fixture: source unexpected';;
 esac
 tvbase_fixture_copy "$t_source" "$2" "$3"
}
'''
apk_fixed=mod.APK.replace('/system/bin/pm path com.droidlogic.otaupgrade','t_fixture_pm')
def priority_ok(t,s,p):
 assert (t/'order.txt').read_text().splitlines()==['certificados','OTA']
 assert (t/'otacerts.zip').read_bytes()==s.read_bytes() and (t/'OTAUpgrade.apk').read_bytes()==s.read_bytes()
fixtures += [
 shell_case('certificates_then_ota_no_candidate_limit',source_adapter+mod.PREFLIGHT+'\nt_fixture_pm() { printf "package:/product/app/OTAUpgrade/OTAUpgrade.apk\\n"; }\n'+apk_fixed,True,check=priority_ok),
 shell_case('gms_path_rejected_without_splits',source_adapter+mod.PREFLIGHT+'\nt_fixture_pm() { printf "package:/data/app/com.google.android.gms/base.apk\\npackage:/data/app/com.google.android.gms/split_config.es.apk\\n"; }\n'+apk_fixed,False,check=lambda t,s,p: None if (t/'order.txt').read_text().splitlines()==['certificados'] else (_ for _ in ()).throw(AssertionError())),
 shell_case('unexpected_ota_path_rejected',source_adapter+mod.PREFLIGHT+'\nt_fixture_pm() { printf "package:/system/app/Other.apk\\n"; }\n'+apk_fixed,False),
 shell_case('mandatory_certificate_missing','tvbase_copy /does-not-exist otacerts.zip 2097152\n',False),
 shell_case('missing_required_report','''for i in 1 2 3; do printf '%s\\n' "$tv_t" > "$tv_d/etapa-$i.ok"; done
for n in autocontrol certificados pm-path actualizador identidad; do printf 'FIN-%s\\n' "$tv_t" > "$tv_d/$n.txt"; tvbase_seal "$n.txt"; done
'''+mod.FINAL,False),
]
final_reports='''for i in 1 2 3; do printf '%s\\n' "$tv_t" > "$tv_d/etapa-$i.ok"; done
for n in autocontrol certificados pm-path actualizador identidad init-y-fstab; do printf 'FIN-%s\\n' "$tv_t" > "$tv_d/$n.txt"; tvbase_seal "$n.txt"; done
'''
def final_binaries(names):
 return 'for n in '+names+'''; do head -c 9 "$t_source" > "$tv_d/$n"; t_v=$(tvbase_sha "$tv_d/$n"); tvbase_hex "$t_v" || tvbase_fail 'fixture digest'; tvbase_rec "$n" "$t_v"; done
'''
fixtures += [
 shell_case('valid_sha_but_wrong_copy','head -c 9 "$t_source" > "$tv_d/copy.bin"\ntvbase_rec copy.bin '+('0'*64)+'\n',False),
 shell_case('final_mandatory_ota_absent',final_reports+final_binaries('autocontrol.bin otacerts.zip')+mod.FINAL,False,check=lambda t,s,p: None if not (t/'COMPLETO.txt').exists() else (_ for _ in ()).throw(AssertionError())),
 shell_case('final_all_required_valid',final_reports+final_binaries('autocontrol.bin otacerts.zip OTAUpgrade.apk')+mod.FINAL,True,check=lambda t,s,p: None if (t/'COMPLETO.txt').exists() and (t/'COMPLETO.txt.sha256').stat().st_size>64 else (_ for _ in ()).throw(AssertionError())),
]
assert '/sys/fs/pstore' not in ''.join(mod.__dict__[x] for x in ['CREATE','COMMON','COPY','PREFLIGHT','APK','CONFIG','FINAL'])
assert '/data/app' not in mod.APK and 'resolve-activity' not in mod.APK
apk=ROOT/'rom-simplificada/compilacion/acceso-usb-0.6/acceso-usb.apk'
with apk.open('rb') as f:apk_hash=hashlib.file_digest(f,'sha256').hexdigest()
sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*.java'))}
state='passed' if all(x['passed'] for x in rows+syntax+mksh_syntax+fixtures) and guards.returncode==0 and outside.returncode!=0 else 'failed'
record={'state':state,'version':'0.6','apk_sha256':apk_hash,'tested_source_sha256':sources,'scope':'PC only; no TV commands executed','adb':rows,'guard_result':guards.stdout.decode().strip(),'external_host_rejected':True,'shell_syntax':syntax,'mksh_syntax':mksh_syntax,'mksh_default_hash_alias':alias_result.stdout.decode().strip(),'shell_fixtures':fixtures,'fixture_adapters':'Real Cygwin mksh R56 and actual tvbase_* function bodies; Android toybox SHA path bound to Python SHA utility, stat to Python, sync success/failure stub. No Android execution or physical USB flush claim.','max_actual_open_bytes':max(map(len,commands))+6,'total_response_limit_bytes':65536,'tv_shell_tested':False,'tv_capture_tested':False}
(HERE/'EVIDENCIA-TESTS-0.6.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,indent=2))
