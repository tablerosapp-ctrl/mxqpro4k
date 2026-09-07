"""Exercise fragmented ADB packets, authentication rejection and direct reboot errors on loopback only."""
import json,socket,struct,subprocess,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
JAVA=ROOT/'tools/verificacion-apk/java21/jdk-21.0.12.1+1-jre/bin/java.exe'
CNXN,OPEN,OKAY,WRTE,CLSE,AUTH=[int.from_bytes(s,'little') for s in (b'CNXN',b'OPEN',b'OKAY',b'WRTE',b'CLSE',b'AUTH')]
def send(s,cmd,a=0,b=0,data=b'',bad=False):
 p=struct.pack('<6I',cmd,a,b,len(data),sum(data)+(1 if bad else 0),cmd^0xffffffff)+data
 for n in range(0,len(p),3):s.sendall(p[n:n+3])
def exact(s,n):
 b=b''
 while len(b)<n:
  q=s.recv(n-len(b));assert q,'unexpected EOF';b+=q
 return b
def recv(s):
 h=struct.unpack('<6I',exact(s,24));d=exact(s,h[3]);assert h[4]==sum(d) and h[5]==h[0]^0xffffffff;return h[:3],d
def test(mode):
 errors=[];seen=[]
 with socket.socket() as server:
  server.bind(('127.0.0.1',0));server.listen();server.settimeout(12)
  def fake():
   try:
    with server.accept()[0] as s:
     s.settimeout(10);h,d=recv(s);assert h[0]==CNXN
     if mode=='auth':send(s,AUTH,1,0,b'challenge');return
     send(s,CNXN,0x1000000,4096,b'device::\0')
     if mode in ('flow','update_flow'):
      queries=[(b'shell:id\0',b'uid=2000(shell) gid=2000(shell)\n'),(b'shell:cat /proc/device-tree/amlogic-dt-id\0',b'gxlx2_p291_1g\0'),(b'shell:getprop ro.build.version.sdk\0',b'28\n')]
      for i,(query,payload) in enumerate(queries):
       h,d=recv(s);assert h[0]==OPEN and d==query,(h,d);seen.append(d.decode());local=h[1];remote=9+i
       if i:
        send(s,CLSE,0,local-1);send(s,WRTE,remote-1,local-1,b'late data must not enter the next result')
       send(s,OKAY,remote,local);send(s,WRTE,remote,local,payload);assert recv(s)[0]==(OKAY,local,remote)
       send(s,CLSE,0 if i==1 else remote,local)
      if mode=='update_flow':
       for expected_prefix,reply in [(b'shell:tvbase_out=',b'Informe guardado en el pendrive:\n/storage/test/TVBASE-diagnostico.txt\n'),(b'shell:tvbase_found=',b'TVBASE_USB_OK\n')]:
        h,d=recv(s);assert h[0]==OPEN and d.startswith(expected_prefix) and len(d)<=4096,(h,d[:100]);seen.append(expected_prefix.decode());local=h[1];remote+=1
        send(s,OKAY,remote,local);send(s,WRTE,remote,local,reply);assert recv(s)[0]==(OKAY,local,remote);send(s,CLSE,remote,local)
      h,d=recv(s);assert h[0]==OPEN and d==(b'reboot:update\0' if mode=='update_flow' else b'reboot:recovery\0'),(h,d);seen.append(d.decode());send(s,CLSE,remote,local);send(s,OKAY,remote+1,h[1]);return
     h,d=recv(s);assert h[0]==OPEN;seen.append(d.decode());local=h[1]
     send(s,OKAY,9,local)
     if mode in ('reboot_closed','update_closed'):return
     if mode=='unknown_channel':send(s,WRTE,9,local+77,b'wrong channel');assert s.recv(1)==b'';return
     if mode=='duplicate_ready':send(s,OKAY,9,local)
     payload=b'reboot failed\n' if mode in ('reboot_error','update_error') else b'uid=2000(shell) gid=2000(shell)\n'
     send(s,WRTE,9,local,payload,bad=mode=='bad_checksum')
     if mode=='bad_checksum':return
     assert recv(s)[0]==(OKAY,local,9);send(s,CLSE,0 if mode=='zero_close' else 9,local);assert s.recv(1)==b'', 'CLSE must not be acknowledged'
   except Exception as e:errors.append(repr(e))
  t=threading.Thread(target=fake);t.start()
  p=subprocess.run([str(JAVA),'-cp',str(HERE/'host-classes'),'local.tvbase.acceso.AdbHarness',str(server.getsockname()[1]),*([mode] if mode in ('flow','update_flow') else ['update'] if mode.startswith('update') else ['reboot'] if mode.startswith('reboot') else [])],capture_output=True,timeout=20)
  t.join(12);assert not t.is_alive() and not errors,errors
  expected=mode in ('shell','reboot_closed','flow','zero_close','duplicate_ready','update_closed','update_flow');assert (p.returncode==0)==expected,(mode,p.stdout,p.stderr)
  if mode=='flow':assert b'late data' not in p.stdout and b'gxlx2_p291_1g' in p.stdout and b'28' in p.stdout
  if mode.startswith('reboot'):assert seen==['reboot:recovery\0'],seen
  if mode in ('update_closed','update_error'):assert seen==['reboot:update\0'],seen
  return {'case':mode,'passed':True,'observed_service':seen,'exit':p.returncode}
rows=[test(x) for x in ['shell','auth','bad_checksum','reboot_closed','reboot_error','flow','zero_close','unknown_channel','duplicate_ready','update_closed','update_error','update_flow']]
(HERE/'ADB-TESTS-0.4.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
