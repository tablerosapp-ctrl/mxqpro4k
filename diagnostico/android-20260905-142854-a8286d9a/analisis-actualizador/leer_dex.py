from pathlib import Path
import struct,zipfile,json
p=Path(__file__).resolve().parent
apk=p.parent/'actualizador-del-segundo-tv.apk'
z=zipfile.ZipFile(apk); d=z.read('classes.dex')
def u32(o): return struct.unpack_from('<I',d,o)[0]
def u16(o): return struct.unpack_from('<H',d,o)[0]
def leb(o):
 v=s=0
 while True:
  b=d[o];o+=1;v|=(b&127)<<s;s+=7
  if not b&128:return v,o
strings=[]
for i in range(u32(56)):
 o=u32(u32(60)+4*i);_,o=leb(o);end=d.index(0,o);strings.append(d[o:end].decode('utf-8','replace'))
types=[strings[u32(u32(68)+4*i)] for i in range(u32(64))]
methods=[]
for i in range(u32(88)):
 o=u32(92)+8*i;methods.append(types[u16(o)]+'->'+strings[u32(o+4)])
out=[]
for i in range(u32(96)):
 o=u32(100)+32*i;name=types[u32(o)];cd=u32(o+24)
 if not cd:continue
 counts=[]
 for j in range(4):n,cd=leb(cd);counts.append(n)
 for j in range(counts[0]+counts[1]):_,cd=leb(cd);_,cd=leb(cd)
 for count in counts[2:]:
  idx=0
  for j in range(count):
   diff,cd=leb(cd);idx+=diff;flags,cd=leb(cd);code,cd=leb(cd)
   if not code:continue
   if not any(s in name for s in ['MainActivity','UpdateActivity','Local','FileSelector','UpdateService','LoaderReceiver','PrefUtils','Recovery','InstallPackage','OtaUpgradeUtils']):continue
   words=[u16(code+16+k*2) for k in range(u32(code+12))]
   events=[]
   # Decode instruction boundaries (Dalvik standard dex opcodes).
   widths={0:1,1:1,2:2,3:3,4:1,5:2,6:3,7:1,8:2,9:3,10:1,11:1,12:1,13:1,14:1,15:1,16:1,17:1,18:1,19:2,20:3,21:2,22:2,23:3,24:5,25:2,26:2,27:3,28:2,29:1,30:1,31:2,32:2,33:1,34:2,35:2,36:3,37:3,38:3,39:1,40:1,41:2,42:3,43:3,44:3}
   widths.update({x:2 for x in range(0x2d,0x3e)})
   widths.update({x:2 for x in range(0x44,0x6e)})
   widths.update({x:3 for x in list(range(0x6e,0x73))+list(range(0x74,0x79))})
   widths.update({x:1 for x in range(0x7b,0x90)})
   widths.update({x:2 for x in range(0x90,0xb0)})
   widths.update({x:1 for x in range(0xb0,0xd0)})
   widths.update({x:2 for x in range(0xd0,0xe3)})
   k=0
   while k<len(words):
    w=words[k]
    op=w&255
    if op==0 and w:
     if w==0x100:width=4+words[k+1]*2
     elif w==0x200:width=2+words[k+1]*4
     elif w==0x300:width=4+(words[k+1]*(words[k+2]+(words[k+3]<<16))+1)//2
     else:raise ValueError(('payload',hex(w)))
    else:width=widths.get(op,1)
    if (0x6e<=op<=0x72 or 0x74<=op<=0x78) and words[k+1]<len(methods):events.append([k,'invoke',methods[words[k+1]]])
    if op==0x1a and words[k+1]<len(strings):events.append([k,'const-string',strings[words[k+1]]])
    if op in [0x1c,0x22] and words[k+1]<len(types):events.append([k,'class',types[words[k+1]]])
    k+=width
   out.append({'method':methods[idx],'flags':flags,'code_offset':code,'words':words,'references':events})
(p/'referencias-dex.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
(p/'strings.txt').write_text('\n'.join(strings),encoding='utf-8')
print('\n'.join(z.namelist()))
for m in out:
 if any(t in m['method'] for t in ['MainActivity->onCreate','MainActivity->onClick','MainActivity->init','MainActivity->onResume','UpdateActivity->onCreate']):print(json.dumps(m,ensure_ascii=False,indent=2))
