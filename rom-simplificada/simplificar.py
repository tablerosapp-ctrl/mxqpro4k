"""Apply the reviewed recipe to workspace ext4 copies, never physical devices.
debugfs keeps original filesystem layout, ownership and metadata of untouched files.
All removed APKs, payload hashes, filesystem checks and commands are recorded.
"""
import hashlib,importlib.util,json,mmap,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;HERE=ROOT/'rom-simplificada'
WORK=HERE/'trabajo';PAYLOAD=WORK/'payload';PAYLOAD.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('inv',HERE/'inspeccion/inventariar-ext4.py')
inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
report=json.loads((HERE/'inspeccion/inventario-rom.json').read_text(encoding='utf8'))
proof=WORK/'cambios.json'
if proof.exists():raise RuntimeError('Recipe was already applied; preserve that result')
original=json.loads((WORK/'copias-originales.json').read_text())
for p in original:
 path=WORK/(p['particion']+'.raw.img')
 assert path.resolve().is_relative_to(WORK.resolve())
 assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==p['sha256'],'Work copy changed'

remove_packages={
 'com.ktcp.video','com.huya.nftv','com.xiaojie.tv','com.ftyytv.app',
 'com.hw.launcher','com.huawei.market','com.fiberhome.starthome',
 'com.iflytek.xiri','com.iflytek.xiri2.system','com.cmcc.mid.softdetector',
 'com.androidmov.tr069','com.amlogic.tr069','com.fh.tr069',
 'com.fiberhome.fhremotedebugserver','com.cmhi.andlink',
}
removed=[a for a in report['apks'] if a.get('paquete') in remove_packages]
assert remove_packages=={a['paquete'] for a in removed}
inventories={n:json.loads((HERE/'inspeccion'/(n+'-inventario.json')).read_text(encoding='utf8')) for n in ('system','vendor','product')}
commands={n:[] for n in inventories};expected={n:[] for n in inventories};removed_paths={n:set() for n in inventories}
def quote(s):
 s=str(s).replace('\\','/');assert '"' not in s and '\n' not in s;return '"'+s+'"'
for apk in removed:
 n=apk['particion'];path=Path(apk['ruta']).as_posix();parent=Path(path).parent.as_posix()
 prefix=path if parent in ('/app','/usr/share/zoneinfo') else parent
 for e in inventories[n]:
  if e['ruta']==prefix or e['ruta'].startswith(prefix+'/'):removed_paths[n].add(e['ruta'])
for n,paths in removed_paths.items():
 nodes={e['ruta']:e for e in inventories[n]}
 for path in sorted(paths,key=lambda p:(p.count('/'),p),reverse=True):
  cmd='rmdir' if int(nodes[path]['modo'],8)&0xf000==0x4000 else 'rm'
  commands[n].append(cmd+' '+quote(path))

contexts={}
for name,text in [('system','u:object_r:system_file:s0'),('overlay','u:object_r:vendor_overlay_file:s0'),('vendor','u:object_r:vendor_configs_file:s0')]:
 p=PAYLOAD/(name+'.context');p.write_bytes(text.encode()+b'\0');contexts[name]=p
def metadata(n,path,mode,uid,gid,context):
 commands[n].extend(['set_inode_field '+quote(path)+' mode '+mode,'set_inode_field '+quote(path)+' uid '+str(uid),
   'set_inode_field '+quote(path)+' gid '+str(gid),'ea_set -f '+quote(contexts[context])+' '+quote(path)+' security.selinux'])
def mkdir(n,path,context):
 existing={e['ruta'] for e in inventories[n]}
 for parent in reversed([Path(path),*Path(path).parents]):
  p=parent.as_posix()
  if p=='/' or p in existing:continue
  commands[n].append('mkdir '+quote(p));metadata(n,p,'040755',0,0,context)
  inventories[n].append({'ruta':p});existing.add(p)
def put(n,path,source,context='system',mode='0100644',uid=0,gid=0):
 old=next((e for e in inventories[n] if e['ruta']==path),None)
 if old:commands[n].append('rm '+quote(path))
 mkdir(n,Path(path).parent.as_posix(),context)
 # This Cygwin debugfs port treats a full destination path as a literal filename in write.
 # Change filesystem directory first, then use a basename; fsck and readback check the result.
 commands[n].extend(['cd '+quote(Path(path).parent.as_posix()),'write '+quote(source)+' '+quote(Path(path).name),'cd /'])
 metadata(n,path,mode,uid,gid,context)
 expected[n].append({'path':path,'source':str(source),'sha256':hashlib.file_digest(Path(source).open('rb'),'sha256').hexdigest(),
    'mode':mode,'uid':uid,'gid':gid,'context':contexts[context].read_bytes().decode().rstrip('\0')})
def text_payload(name,text):
 p=PAYLOAD/name;p.write_text(text,encoding='utf8',newline='\n');return p

chrome=ROOT/'actualizacion-chrome/chrome-138.0.7204.179-arm32.apk'
assert hashlib.file_digest(chrome.open('rb'),'sha256').hexdigest()=='3d9414001b3e2555831cd014df2c9ae5a6eab10190c4cffce7ecaad3c0f53f23'
put('system','/app/Chrome/Chrome.apk',chrome)
put('system','/app/InicioTV/InicioTV.apk',HERE/'compilacion/inicio/inicio.apk')
put('vendor','/overlay/TVBaseWebView/TVBaseWebView.apk',HERE/'compilacion/webview-overlay/webview-overlay.apk',context='overlay')

noop=text_payload('preinstall.sh','#!/system/bin/sh\n# TV Base: no bundled third-party application installation.\nexit 0\n')
for path in ('/bin/preinstall.sh','/bin/opt/etc/preinstall.sh'):
 put('system',path,noop,mode='0100755',gid=2000)
# Stop marks services disabled in AOSP 9, preventing class_start main from launching them.
services=['upgradeserver','onekeycollect','softdetector','xiriservice','stbdetector','user','bootvideo']
rc='# TV Base experimental: disable operator management, diagnostics and startup promotion.\n'
for trigger in ('post-fs-data','boot'):
 rc+='on '+trigger+'\n'+''.join('    stop '+s+'\n' for s in services)+'\n'
put('system','/etc/init/tvbase.rc',text_payload('tvbase.rc',rc))
vendor_rc=(HERE/'inspeccion/metadatos/vendor/etc/init/hw/init.amlogic.rc').read_text(encoding='utf8')
assert vendor_rc.count('    start stbdetector')==1
vendor_rc=vendor_rc.replace('    start stbdetector','    # TV Base: operator detector disabled')
put('vendor','/etc/init/hw/init.amlogic.rc',text_payload('init.amlogic.rc',vendor_rc),context='vendor')

# Keep hardware/configuration initialization but remove the factory telnet branch and operator account rewrites.
common=(HERE/'inspeccion/metadatos/system/bin/opt/etc/init.common.sh').read_text(encoding='utf8')
start=common.index('CONSOLEABLE=');end=common.index('DEF_FILE=',start)
common=common[:start]+'# TV Base: factory remote shell startup removed.\n\n'+common[end:]
put('system','/bin/opt/etc/init.common.sh',text_payload('init.common.sh',common),mode='0100755',gid=2000)
fh=text_payload('init.fhservice.sh','#!/system/bin/sh\n# Retain hardware detection; omit operator account setup.\n/system/bin/opt/etc/hw.detect.sh\n')
put('system','/bin/opt/etc/init.fhservice.sh',fh,mode='0100755',gid=2000)

props=(HERE/'inspeccion/metadatos/system/build.prop').read_text(encoding='utf8')
for key,value in {'ro.build.display.id':'TVBASE-P291-A9-0.1-experimental','ro.product.locale':'es-AR',
 'ro.product.locale.language':'es','ro.product.locale.region':'AR','persist.sys.language':'es','persist.sys.country':'AR'}.items():
 props,count=re.subn(r'^'+re.escape(key)+r'=.*$',key+'='+value,props,flags=re.M);assert count==1,key
put('system','/build.prop',text_payload('build.prop',props))
manifest={'version':'0.1-experimental','board_profile':'gxlx2_p291_1g','android_api':28,
 'chrome_version':'138.0.7204.179','runtime_validated':False,'usb_install_entry_validated':False,
 'own_remote_updater_implemented':False,'original_webview_retained_as_fallback':True}
put('system','/etc/tvbase.json',text_payload('tvbase.json',json.dumps(manifest,indent=2)+'\n'))

results={'manifest':manifest,'removed_apks':removed,'services_disabled_in_init':services,'added_or_replaced':expected,'removed_paths':{n:sorted(p) for n,p in removed_paths.items()},'partitions':{}}
for n in ('system','vendor'):
 image=WORK/(n+'.raw.img');cmdfile=WORK/(n+'-debugfs.txt');cmdfile.write_text('\n'.join(commands[n])+'\n',encoding='utf8')
 p=subprocess.run([str(ROOT/'tools/ext4-cygwin/bin/debugfs.exe'),'-w','-f',str(cmdfile),str(image)],capture_output=True,creationflags=0x08000000)
 (WORK/(n+'-edicion.log')).write_bytes(p.stdout+p.stderr)
 assert p.returncode==0,p.stderr.decode('utf8','replace')
 check=subprocess.run([str(ROOT/'tools/ext4-cygwin/bin/e2fsck.exe'),'-fn',str(image)],capture_output=True,creationflags=0x08000000)
 (WORK/(n+'-fsck.log')).write_bytes(check.stdout+check.stderr);assert check.returncode==0,check.stdout.decode('utf8','replace')
 with image.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
  fs=inv.Ext4(inv.Sparse(data,0,len(data)));nodes={p:node for p,node in fs.walk()}
  assert not (removed_paths[n]&set(nodes)), 'An intended removal failed'
  for item in expected[n]:
   node=nodes[item['path']];assert hashlib.sha256(fs.content(node)).hexdigest()==item['sha256'],item['path']
   assert node['modo']==int(item['mode'],8) and node['uid']==item['uid'] and node['gid']==item['gid'],item['path']
  results['partitions'][n]={'bytes':len(data),'free_bytes':fs.meta['bloques_libres']*fs.bs,'fsck_exit':check.returncode,
   'sha256':hashlib.sha256(data).hexdigest(),'modified_files_verified':len(expected[n])}
proof.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'removed_apks':len(removed),'services_disabled':services,'partitions':results['partitions']},indent=2))
