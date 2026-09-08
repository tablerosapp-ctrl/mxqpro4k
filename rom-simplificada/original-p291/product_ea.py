"""Reclaim only the eight proven orphan EA blocks of original P291 product.

debugfs 1.44.5 rm/rmdir leaves the external-EA allocation bits of these removed
128-byte inodes. The source filesystem is healthy. This is a fixed recipe for
this source and these eight removals, not a generic filesystem repair.

All edits use native debugfs operations on a local construction copy. No
checksum implementation, mounts, device paths, network, or broad fsck repair.
The caller still runs its final fsck/content/xattr/zero-free-space checks.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
TOOLS=ROOT/'tools/ext4-cygwin/bin'
SOURCE_SHA='ef2c71f6208e25fa1cc9d5c12cb04972ac20d772e2c11a76972859403b530075'
SIZE=134217728
ORPHANS=set(range(2008,2016))
OWNERS={
    '/app/NativeImagePlayer':(17,2008),
    '/app/NativeImagePlayer/NativeImagePlayer.apk':(18,2009),
    '/app/DLNA':(19,2010),
    '/app/DLNA/DLNA.apk':(20,2011),
    '/app/OTAUpgrade':(21,2012),
    '/app/OTAUpgrade/OTAUpgrade.apk':(22,2013),
    '/app/Miracast':(23,2014),
    '/app/Miracast/Miracast.apk':(24,2015),
}
NATIVE_COMMANDS=('freeb 2008 8\nset_super_value free_blocks_count 31584\n'
                 'set_bg 0 free_blocks_count 31584\nset_bg 0 checksum calc\n')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _u16(data,offset):
    return struct.unpack_from('<H',data,offset)[0]


def _u32(data,offset):
    return struct.unpack_from('<I',data,offset)[0]


def _geometry(data):
    assert len(data)==SIZE,'Unexpected product byte count'
    assert _u16(data,1080)==0xef53,'Not the expected ext4 filesystem'
    assert (_u32(data,1028),_u32(data,1044),_u32(data,1048),_u32(data,1056),
            _u32(data,1064),_u16(data,1112))==(32768,0,2,32768,32768,128),'Unexpected product geometry'
    assert (_u32(data,1116),_u32(data,1120),_u32(data,1124))==(0x38,0x242,0x7b),'Unexpected ext4 features'
    assert (_u32(data,4096),_u32(data,4100),_u32(data,4104))==(9,25,41),'Unexpected metadata locations'


def _inode(data,number):
    assert 1<=number<=32768
    offset=41*4096+(number-1)*128
    return data[offset:offset+128]


def _allocated_inodes(data):
    bitmap=data[25*4096:26*4096]
    return [number for number in range(1,32769) if bitmap[(number-1)//8]&(1<<((number-1)%8))]


def _execute(args,workspace,label):
    completed=subprocess.run([str(a) for a in args],capture_output=True,timeout=60,creationflags=0x08000000)
    (workspace/(label+'.stdout')).write_bytes(completed.stdout)
    (workspace/(label+'.stderr')).write_bytes(completed.stderr)
    return completed.returncode,completed.stdout.decode('utf8','strict').replace('\r\n','\n'),completed.stderr.decode('utf8','strict').replace('\r\n','\n')


def reclaimed(plan,edited):
    """Apply this exact reclamation to the caller's product construction copy.

    Fails before mutation for another source, plan, geometry, bitmap, owner or
    filesystem error. Never retries. A post-edit failure preserves the copy and
    native logs for review; callers must not publish or use that image.
    """
    assert plan.part=='product','Product-only correction'
    source=Path(plan.source).resolve();edited=Path(edited).resolve();workspace=Path(plan.workspace).resolve()
    assert edited.parent==workspace and workspace.is_relative_to(ROOT)
    assert workspace.is_relative_to(HERE/'privado') or workspace.is_relative_to(ROOT/'privado/original-p291-empaquetado')
    assert edited!=source and not edited.samefile(source),'Never modify the original source'
    assert stat.S_ISREG(edited.stat().st_mode) and edited.stat().st_nlink==1,'Construction must be a regular unshared file'
    assert set(plan.removed)==set(OWNERS) and not plan.edits and not plan.added_dirs,'Unexpected product change set'
    expected_commands=[('rmdir' if not name.endswith('.apk') else 'rm')+' "'+name+'"'
                       for name in sorted(OWNERS,key=lambda p:(p.count('/'),p),reverse=True)]
    assert plan.commands==expected_commands,'Unexpected product removal commands'
    original=source.read_bytes();assert digest(original)==SOURCE_SHA,'Unexpected original product SHA256'
    before=edited.read_bytes();_geometry(original);_geometry(before)
    assert before[1128:1144]==original[1128:1144],'Product UUID changed from verified source'
    for name,(number,block) in OWNERS.items():
        record=plan.nodes[name]
        assert (record['inode'],record['acl_block'])==(number,block),'Unexpected removal owner'
        assert _u32(_inode(original,number),104)==block
        assert struct.unpack_from('<III',original,block*4096)==(0xea020000,1,1),'Unexpected original external EA header'
        assert before[block*4096:(block+1)*4096]==original[block*4096:(block+1)*4096],'External EA bytes changed before correction'
    allocated=_allocated_inodes(before)
    assert len(allocated)==24 and not set(range(17,25))&set(allocated),'Deleted inodes still allocated'
    for number in allocated:
        node=_inode(before,number)
        assert _u32(node,104) not in ORPHANS,'A live inode still owns an external EA block'
    bitmap=before[9*4096:10*4096]
    assert bitmap[251]==255,'Expected eight orphan bits are not all set'
    assert sum(byte.bit_count() for byte in bitmap)==1192,'Unexpected allocated block count'
    assert _u32(before,1036)==_u16(before,4108)==31576,'Unexpected free-block counters'
    assert _u32(before,1040)==_u16(before,4110)==32744,'Unexpected free-inode counters'
    # Existing content/metadata/xattr verifier independently compares all live
    # nodes against the known source before any allocation bits can be changed.
    preserved_before=plan.verify(edited)
    code,out,err=_execute([TOOLS/'e2fsck.exe','-fn',edited],workspace,'product-ea-before-fsck')
    expected=('Pass 1: Checking inodes, blocks, and sizes\nPass 2: Checking directory structure\n'
              'Pass 3: Checking directory connectivity\nPass 4: Checking reference counts\n'
              'Pass 5: Checking group summary information\nBlock bitmap differences:  -(2008--2015)\n'
              'Fix? no\n\n\nproduct: ********** WARNING: Filesystem still has errors **********\n\n'
              'product: 24/32768 files (4.2% non-contiguous), 1192/32768 blocks\n')
    assert code==4 and out==expected and err=='e2fsck 1.44.5 (15-Dec-2018)\n','Unexpected filesystem error; not corrected'
    code,out,err=_execute([TOOLS/'debugfs.exe','-R','icheck 2008 2009 2010 2011 2012 2013 2014 2015',edited],workspace,'product-ea-owners')
    assert code==0 and out=='Block\tInode number\n'+''.join(str(n)+'\t<block not found>\n' for n in sorted(ORPHANS))
    assert err=='debugfs 1.44.5 (15-Dec-2018)\n'
    receipt_path=workspace/'product-ea-reclamation.json'
    assert not receipt_path.exists(),'Reclamation has already been recorded; do not repeat'
    command_file=workspace/'product-ea-reclamation.commands'
    with command_file.open('x',encoding='utf8') as stream:stream.write(NATIVE_COMMANDS)
    assert source.read_bytes()==original and edited.read_bytes()==before,'Input changed before reclamation'
    started=int(time.time())
    code,out,err=_execute([TOOLS/'debugfs.exe','-w','-f',command_file,edited],workspace,'product-ea-native')
    ended=int(time.time())
    expected_native=''.join('debugfs: '+line+'\n' for line in NATIVE_COMMANDS.splitlines())+'Checksum set to 0x886c\n'
    assert code==0 and out==expected_native
    assert err=='debugfs 1.44.5 (15-Dec-2018)\n'
    # Flush native writes before reading the result back through the filesystem.
    with edited.open('r+b') as stream:stream.flush();os.fsync(stream.fileno())
    after=edited.read_bytes();_geometry(after)
    assert after[1128:1144]==original[1128:1144] and _u16(after,4126)==0x886c
    assert _u32(after,1036)==_u16(after,4108)==31584 and after[37115]==0
    assert sum(byte.bit_count() for byte in after[9*4096:10*4096])==1184
    assert started-2<=_u32(after,1072)<=ended+2,'Unexpected native write timestamp'
    allowed=set(range(1036,1040))|set(range(1072,1076))|set(range(4108,4110))|set(range(4126,4128))|{37115}
    changes=[]
    for start in range(0,SIZE,4096):
        if before[start:start+4096]!=after[start:start+4096]:
            for index,(a,b) in enumerate(zip(before[start:start+4096],after[start:start+4096])):
                if a!=b:
                    offset=start+index
                    assert offset in allowed,('Unexpected byte changed',offset)
                    changes.append({'offset':offset,'old':a,'new':b})
    code,out,err=_execute([TOOLS/'e2fsck.exe','-fn',edited],workspace,'product-ea-after-fsck')
    assert code==0,'Exact reclamation did not result in clean ext4'
    preserved_after=plan.verify(edited)
    assert source.read_bytes()==original,'Original changed during reclamation'
    assert edited.read_bytes()==after,'Read-only verification changed the copy'
    result={'source_sha256':SOURCE_SHA,'before_sha256':digest(before),'after_sha256':digest(after),
            'reclaimed_blocks':sorted(ORPHANS),'native_commands':NATIVE_COMMANDS.splitlines(),
            'changed_bytes':changes,'all_other_bytes_identical':True,'native_wtime_only_extra_metadata':True,
            'remaining_before':preserved_before,'remaining_after':preserved_after,'post_fsck_exit':code,
            'source_unchanged':True,'tv_accessed':False,'usb_accessed':False}
    with receipt_path.open('x',encoding='utf8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    return result
