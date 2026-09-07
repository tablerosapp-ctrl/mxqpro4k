"""Only PC loopback simulations and POSIX fixture checks; never contacts the TV."""
from pathlib import Path
import hashlib,importlib.util,json,socket,struct,subprocess,threading,tempfile,os,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
HOST=HERE/'host-classes-0.7'
SH=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/usr/bin/sh.exe'
SH_ENV=dict(os.environ,PATH=str(SH.parent)+os.pathsep+os.environ.get('PATH',''))
SRC=ROOT/'rom-simplificada/componentes/acceso-usb-0.7'
TOKEN='1234567890abcdef1234567890abcdef'
DIR='/storage/ABCD-1234'
CNXN,OPEN,OKAY,WRTE,CLSE,AUTH=[int.from_bytes(s,'little') for s in (b'CNXN',b'OPEN',b'OKAY',b'WRTE',b'CLSE',b'AUTH')]
def java(*args):
 return subprocess.run([str(JAVA),'-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-cp',str(HOST),'local.tvbase.acceso.EntradaHarness07',*map(str,args)],capture_output=True,timeout=25)
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
commands=[java('dump',n).stdout+b'\0' for n in range(2)]
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
      queries += [(b'shell:'+commands[n],('TVBASE_MEDIA:'+DIR if n==0 else 'ERROR final hash' if n==1 and mode=='final_failure' else f'TVBASE_OPEN_OK:{TOKEN}').encode()+b'\n') for n in range(2)]
      for i,(expected,payload) in enumerate(queries):
       h,d=recv(s);assert h[0]==OPEN and d==expected,(i,d[:80]);seen.append('profile' if i<3 else f'entry-stage-{i-3}')
       assert d.startswith(b'shell:') and b'reboot:' not in d and b'setupBcb' not in d and b'setprop ' not in d
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
  if mode=='flow':assert 'Menú local abierto'.encode() in p.stdout and b'late data' not in p.stdout
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

# Execute actual production functions with mksh's default alias still enabled.
# Only Android paths/utilities and the large ROM fixture's size/digest are bound
# to local deterministic files. The final am command is a recording stub only.
MKSH=ROOT/'tools/mksh-audit/mksh.exe'
MINGIT=SH.parent.as_posix();CYG_PATH='/cygdrive/'+MINGIT[0].lower()+MINGIT[2:]
mksh_syntax=[]
for script in sorted((SRC/'scripts').glob('*.sh')):
 p=subprocess.run([str(MKSH),'-n',str(script)],capture_output=True,timeout=10);assert p.returncode==0,(script,p.stderr)
 mksh_syntax.append({'path':script.relative_to(ROOT).as_posix(),'passed':True})
alias_result=subprocess.run([str(MKSH),'-c','alias hash'],capture_output=True,timeout=10)
assert alias_result.returncode==0 and b'alias -t' in alias_result.stdout
fixture=Path(tempfile.mkdtemp(prefix='fixture-entrada-0.7-',dir=HERE))
utility=fixture/'utility.py'
utility.write_text('''import hashlib,sys
from pathlib import Path
if sys.argv[1]=='corrupt':
 with Path(sys.argv[2]).open('r+b') as f:f.write(b'Z')
 sys.exit(0)
if sys.argv[1]=='stat':
 st=Path(sys.argv[3]).stat();v=str(st.st_size) if sys.argv[2]=='%s' else f'{st.st_size}:{int(st.st_mtime)}:{st.st_ino}'
else:
 if len(sys.argv)>2:
  with Path(sys.argv[2]).open('rb') as f:v=hashlib.file_digest(f,'sha256').hexdigest()+'  '+sys.argv[2]
 else:v=hashlib.sha256(sys.stdin.buffer.read()).hexdigest()+'  -'
sys.stdout.buffer.write((v+'\\n').encode())
''',encoding='utf8')
assert mod.ROM_SHA=='e7279a7901bc0b513ccc5d3a66a1b5bf483908a4cffd30f34f5d8d463fc95205'
assert mod.OTA_SHA=='9ffb822fc76974ee9df8c5493f0929638b69140f71506946cb410bab489a1d9c'
assert '573089164' in mod.VERIFY and '190988' in mod.VERIFY

def shell_case(name,overrides='',expected=False,launch_count=0):
 out=fixture/name;out.mkdir();usb=out/'usb';usb.mkdir()
 marker=usb/'TVBASE-MEDIA.txt';marker.write_text(mod.MARKER+'\n',encoding='ascii',newline='\n')
 rom=usb/mod.ROM;rom.write_bytes(bytes(range(256))*5+b'\0\xff\xfeROM')
 ota=out/'OTAUpgrade.apk';ota.write_bytes(bytes(range(256))*746+b'OTA')
 dt=out/'dt';dt.write_bytes(b'gxlx2_p291_1g\0')
 calls=out/'calls.txt';path=out/'case.sh'
 header=f'''PATH='{CYG_PATH}'; export PATH
tv_t='{TOKEN}';tv_d='{usb.as_posix()}'
t_fixture_rom='{rom.as_posix()}';t_fixture_ota='{ota.as_posix()}';t_fixture_dt='{dt.as_posix()}'
id() {{ printf '2000\\n'; }}
getprop() {{ printf '28\\n'; }}
stat() {{ '{Path(sys.executable).as_posix()}' '{utility.as_posix()}' stat "$2" "$3"; }}
t_fixture_sha() {{ '{Path(sys.executable).as_posix()}' '{utility.as_posix()}' sha "$@"; }}
t_fixture_pm() {{ printf 'package:%s\\n' "$t_fixture_ota"; }}
t_fixture_am() {{ printf 'am\\n' >> '{calls.as_posix()}'; printf 'Starting: Intent {{ cmp=com.droidlogic.otaupgrade/.MainActivity }}\\nStatus: ok\\nActivity: com.droidlogic.otaupgrade/.MainActivity\\nComplete\\n'; }}
'''
 common=mod.COMMON.replace('/system/bin/toybox sha256sum','t_fixture_sha').replace('/proc/device-tree/amlogic-dt-id',dt.as_posix())
 verify=mod.VERIFY.replace('/system/bin/pm path com.droidlogic.otaupgrade','t_fixture_pm').replace(mod.OTA,ota.as_posix()).replace('573089164',str(rom.stat().st_size)).replace('190988',str(ota.stat().st_size)).replace(mod.ROM_SHA,hashlib.sha256(rom.read_bytes()).hexdigest()).replace(mod.OTA_SHA,hashlib.sha256(ota.read_bytes()).hexdigest())
 launch=mod.LAUNCH.replace('/system/bin/am start -W -n com.droidlogic.otaupgrade/.MainActivity','t_fixture_am')
 path.write_text(header+common+overrides+'\n'+verify+launch,encoding='utf8',newline='\n')
 p=subprocess.run([str(MKSH),str(path)],capture_output=True,timeout=20)
 count=len(calls.read_text().splitlines()) if calls.exists() else 0
 assert count==launch_count,(name,count,p.stdout,p.stderr)
 assert (p.returncode==0)==expected,(name,p.returncode,p.stdout,p.stderr)
 assert (('TVBASE_OPEN_OK:'+TOKEN).encode() in p.stdout)==expected,(name,p.stdout)
 # Read-only preflight must not create or copy another file on the USB.
 assert {x.name for x in usb.iterdir()}=={'TVBASE-MEDIA.txt',mod.ROM},name
 return {'case':name,'passed':True,'exit':p.returncode,'stub_menu_opens':count,'stdout':p.stdout.decode('utf8','replace').strip(),'physical_device':False}

fixtures=[
 shell_case('preflight_then_single_menu_open',expected=True,launch_count=1),
 shell_case('profile_wrong_uid','id() { printf "0\\n"; }'),
 shell_case('profile_wrong_sdk','getprop() { printf "29\\n"; }'),
 shell_case('profile_wrong_dt','printf gxlx_p271_1g > "$t_fixture_dt"'),
 shell_case('marker_wrong_before_hash','printf WRONG > "$tv_d/TVBASE-MEDIA.txt"'),
 shell_case('raw_sha_empty_success','t_fixture_sha() { return 0; }'),
 shell_case('raw_sha_nonhex_success','t_fixture_sha() { printf "%064s  x\\n" z; }'),
 shell_case('helper_empty_external_guard','tvbase_sha() { return 0; }'),
 shell_case('helper_nonhex_external_guard','tvbase_sha() { printf "%064s" z; }'),
 shell_case('selftest_mismatched','t_fixture_sha() { printf "%064d  x\\n" 0; }'),
 shell_case('rom_size_wrong','printf X >> "$t_fixture_rom"'),
 shell_case('rom_digest_wrong',f''' '{Path(sys.executable).as_posix()}' '{utility.as_posix()}' corrupt "$t_fixture_rom" || exit 8'''),
 shell_case('ota_digest_wrong',f''' '{Path(sys.executable).as_posix()}' '{utility.as_posix()}' corrupt "$t_fixture_ota" || exit 8'''),
 shell_case('pm_unexpected_path','t_fixture_pm() { printf "package:/system/app/Other.apk\\n"; }'),
 shell_case('pm_multiple_paths','t_fixture_pm() { printf "package:%s\\npackage:/data/app/split.apk\\n" "$t_fixture_ota"; }'),
 shell_case('pm_denied','t_fixture_pm() { printf "Permission denied\\n"; return 1; }'),
 shell_case('rom_changed_during_hash',f'''t_fixture_sha() {{ '{Path(sys.executable).as_posix()}' '{utility.as_posix()}' sha "$@"; [ "$1" != "$t_fixture_rom" ] || printf X >> "$t_fixture_rom"; }}'''),
 shell_case('marker_changed_after_hash',f'''t_fixture_sha() {{ '{Path(sys.executable).as_posix()}' '{utility.as_posix()}' sha "$@"; [ "$1" != "$t_fixture_ota" ] || printf WRONG > "$tv_d/TVBASE-MEDIA.txt"; }}'''),
 shell_case('am_nonzero','t_fixture_am() { printf "rejected\\n"; return 1; }'),
 shell_case('am_zero_without_status','t_fixture_am() { printf "Error: Activity not started\\n"; }'),
 shell_case('am_wrong_activity','t_fixture_am() { printf "Status: ok\\nActivity: com.android.settings/.Settings\\n"; }'),
 shell_case('am_duplicate_status','t_fixture_am() { printf "Status: ok\\nStatus: ok\\nActivity: com.droidlogic.otaupgrade/.MainActivity\\n"; }'),
 shell_case('am_full_component','t_fixture_am() { printf "Status: ok\\nActivity: com.droidlogic.otaupgrade/com.droidlogic.otaupgrade.MainActivity\\n"; }',expected=True),
]
# The source stage has exactly one menu command, with no selection extras or
# persistent installation actions. Responses must never cause an automatic retry.
assert mod.LAUNCH.count('/system/bin/am start')==1
assert all(x not in mod.COMMON+mod.VERIFY+mod.LAUNCH for x in ['reboot:', 'setupBcb','--wipe_', ' --es ', ' --ez ', 'keyevent','input tap','/cache/recovery/command','setprop'])
apk=ROOT/'rom-simplificada/compilacion/acceso-usb-0.7/acceso-usb.apk'
with apk.open('rb') as f:apk_hash=hashlib.file_digest(f,'sha256').hexdigest()
sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*.java'))}
state='passed' if all(x['passed'] for x in rows+syntax+mksh_syntax+fixtures) and guards.returncode==0 and outside.returncode!=0 else 'failed'
record={'state':state,'version':'0.7','apk_sha256':apk_hash,'tested_source_sha256':sources,'scope':'PC only; OEM opening is stubbed; no TV or USB operations','adb':rows,'guard_result':guards.stdout.decode('utf8').strip(),'external_host_rejected':True,'shell_syntax':syntax,'mksh_syntax':mksh_syntax,'mksh_default_hash_alias':alias_result.stdout.decode().strip(),'shell_fixtures':fixtures,'fixture_adapters':'Real Cygwin mksh R56 and production tvbase_* guards; Android utility/path bindings to Python/local deterministic fixture files; ROM fixture size/digest substituted, production constants asserted; OEM am command recording stub only. No Android execution.','max_actual_open_bytes':max(map(len,commands))+6,'total_response_limit_bytes':65536,'zip_preflight_deadline_seconds':300,'tv_shell_tested':False,'tv_menu_tested':False}
(HERE/'ENTRADA-TESTS-0.7.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,indent=2))
