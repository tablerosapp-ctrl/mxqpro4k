"""Reproduce and test the product external-EA removal on PC-only copies.

Never writes a TV, USB, original backup or main construction image. Each run
creates a distinct private directory and keeps its evidence, including failures.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import uuid
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
spec=importlib.util.spec_from_file_location('product_builder_review',HERE.parent/'construir.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
SOURCE=ROOT/'privado/TVBASE-respaldo-P291-20260907-194413-6d502965/product.img'
FAILED=HERE.parent/'privado/construccion-0.2.0-intento02/product/product.edited.img'
EXPECTED_SOURCE='ef2c71f6208e25fa1cc9d5c12cb04972ac20d772e2c11a76972859403b530075'


def crc16(data):
    value=0xffff
    for byte in data:
        value^=byte
        for _ in range(8):value=(value>>1)^0xa001 if value&1 else value>>1
    return value


def main():
    source_sha=builder.sha(SOURCE);failed_sha=builder.sha(FAILED)
    assert source_sha==EXPECTED_SOURCE and SOURCE.stat().st_size==134217728
    private=(ROOT/'privado/original-p291-empaquetado').resolve()
    assert private.is_relative_to(ROOT)
    work=private/('product-bitmap-'+uuid.uuid4().hex[:10]);work.mkdir()
    receipt={'source_sha256':source_sha,'failed_image_sha256':failed_sha,
             'source_bytes':SOURCE.stat().st_size,'original_or_main_image_modified':False,
             'private_evidence':work.relative_to(ROOT).as_posix()}

    def execute(args,name):
        p=subprocess.run([str(x) for x in args],capture_output=True,timeout=60,creationflags=0x08000000)
        (work/(name+'.stdout')).write_bytes(p.stdout)
        (work/(name+'.stderr')).write_bytes(p.stderr)
        return {'exit':p.returncode,'stdout':p.stdout.decode('utf8','strict').replace('\r\n','\n'),
                'stderr':p.stderr.decode('utf8','strict').replace('\r\n','\n')}

    receipt['fsck_original']=execute([builder.TOOLS/'e2fsck.exe','-fn',SOURCE],'fsck-original')
    receipt['fsck_failed_image']=execute([builder.TOOLS/'e2fsck.exe','-fn',FAILED],'fsck-failed')
    assert receipt['fsck_original']['exit']==0 and receipt['fsck_failed_image']['exit']==4
    assert 'Block bitmap differences:  -(2008--2015)' in receipt['fsck_failed_image']['stdout']
    with builder.filesystem(SOURCE) as (fs,nodes):
        original_nodes={name:dict(node) for name,node in nodes.items()}
        receipt['filesystem']={k:fs.meta[k] for k in ('bloque','bytes_fs','inode_size','feature_compat','feature_incompat','feature_ro_compat')}
        assert fs.bs==4096 and fs.isize==128 and fs.meta['bytes_fs']==SOURCE.stat().st_size
    with builder.filesystem(FAILED) as (fs,nodes):
        failed_nodes={name:dict(node) for name,node in nodes.items()}
    removed=set(original_nodes)-set(failed_nodes)
    assert len(removed)==8 and {original_nodes[name]['inode'] for name in removed}==set(range(17,25))
    assert {original_nodes[name]['acl_block'] for name in removed}==set(range(2008,2016))
    plan=builder.Plan('product-audit',SOURCE,json.loads((HERE.parent/'privado/inventario/product.json').read_text()),work)
    attrs=plan.xattrs(SOURCE,removed,'removed-source')
    assert all(set(value)=={'security.selinux'} for value in attrs.values())
    receipt['removed_nodes']=[{'path':name,'inode':original_nodes[name]['inode'],
                              'external_ea_block':original_nodes[name]['acl_block'],
                              'attributes':attrs[name]} for name in sorted(removed)]
    for name in ('/app/NativeImagePlayer','/app/DLNA','/app/OTAUpgrade','/app/Miracast'):
        plan.remove_tree(name)
    receipt['remaining_before_correction']=plan.verify(FAILED)

    # The standard EA removal API runs while the inode is still linked. No
    # direct bitmap edits and no broad filesystem repair are used here.
    corrected=work/'product-ea-before-removal.img';shutil.copyfile(SOURCE,corrected)
    assert builder.sha(corrected)==source_sha
    previous_commands=(FAILED.parent/'debugfs.txt').read_text()
    command_text=''.join('ea_rm '+builder.quote(name)+' security.selinux\n' for name in sorted(removed))+previous_commands
    command_file=work/'ea-before-removal.commands';command_file.write_text(command_text,encoding='utf8')
    receipt['ea_before_removal']=execute([builder.TOOLS/'debugfs.exe','-w','-f',command_file,corrected],'ea-before-removal')
    assert receipt['ea_before_removal']['exit']==0
    receipt['fsck_corrected_copy']=execute([builder.TOOLS/'e2fsck.exe','-fn',corrected],'fsck-corrected')
    receipt['remaining_after_correction']=plan.verify(corrected)
    receipt['corrected_copy_sha256']=builder.sha(corrected)
    assert corrected.stat().st_size==SOURCE.stat().st_size

    # Compare live inode bytes and directory/file/symlink content with the
    # already-edited main image, rather than just comparing the recipe.
    with builder.filesystem(FAILED) as (old_fs,old_nodes),builder.filesystem(corrected) as (new_fs,new_nodes):
        assert set(old_nodes)==set(new_nodes)
        changed_live_inodes=[];changed_live_content=[]
        for name in old_nodes:
            if old_nodes[name]['raw']!=new_nodes[name]['raw']:changed_live_inodes.append(name)
            if old_fs.content(old_nodes[name])!=new_fs.content(new_nodes[name]):changed_live_content.append(name)
        # fs.walk omits the root directory; explicitly include it as well.
        if old_fs.inode(2)['raw']!=new_fs.inode(2)['raw']:changed_live_inodes.append('/')
        if old_fs.content(old_fs.inode(2))!=new_fs.content(new_fs.inode(2)):changed_live_content.append('/')
        receipt['changed_remaining_inode_bytes']=changed_live_inodes
        receipt['changed_remaining_contents']=changed_live_content
        sb=old_fs.r.read(1024,1024);assert struct.unpack_from('<I',sb,32)[0]==32768
        gd=old_fs.r.read(4096,32);bitmap=struct.unpack_from('<I',gd,0)[0]
        assert bitmap==9
        receipt['bitmap_block']=bitmap
        receipt['bitmap_byte_offset']=bitmap*4096+2008//8
        receipt['failed_bitmap_byte']=old_fs.r.read(receipt['bitmap_byte_offset'],1).hex()
        receipt['corrected_bitmap_byte']=new_fs.r.read(receipt['bitmap_byte_offset'],1).hex()

    before=FAILED.read_bytes();after=corrected.read_bytes()
    changed=[start+i for start in range(0,len(before),4096)
             if before[start:start+4096]!=after[start:start+4096]
             for i,(a,b) in enumerate(zip(before[start:start+4096],after[start:start+4096])) if a!=b]
    receipt['byte_difference_count']=len(changed)
    receipt['changed_image_blocks']=sorted({offset//4096 for offset in changed})
    receipt['byte_differences']=[{'offset':offset,'old':before[offset],'new':after[offset]} for offset in changed] if len(changed)<100 else None
    assert receipt['fsck_corrected_copy']['exit']==4
    assert 'Block bitmap differences:  -(2008--2015)' in receipt['fsck_corrected_copy']['stdout']
    assert not receipt['changed_remaining_inode_bytes'] and not receipt['changed_remaining_contents']

    # The narrowed second experiment changes only the eight orphan bits and
    # their two free-block counters plus the existing GDT_CSUM descriptor CRC.
    assert failed_sha=='5130d9bd50163a89f68e2ca16f6844f494c4a6b635f8e8f844e4aa71156f20b3'
    orphan_blocks=set(range(2008,2016))
    with builder.filesystem(FAILED) as (fs,nodes):
        sb=fs.r.read(1024,1024);gd=fs.r.read(4096,32)
        assert (fs.incompat,fs.ro,fs.bs,fs.isize)==(0x242,0x7b,4096,128)
        assert struct.unpack_from('<I',sb,4)[0]==32768
        free_sb=struct.unpack_from('<I',sb,12)[0]
        free_group=struct.unpack_from('<H',gd,12)[0]
        bitmap=fs.r.read(9*4096,4096)
        marked=sum(x.bit_count() for x in bitmap)
        assert free_sb==free_group==31576 and marked==1192
        assert marked==32768-free_sb
        inode_bitmap=fs.r.read(struct.unpack_from('<I',gd,4)[0]*4096,4096)
        live_inodes=[]
        for number in range(1,32769):
            if inode_bitmap[(number-1)//8]&(1<<((number-1)%8)):
                live_inodes.append(number)
                assert fs.inode(number)['acl_block'] not in orphan_blocks
        assert not set(range(17,25))&set(live_inodes)
        for block in orphan_blocks:
            external=fs.r.read(block*4096,4096)
            assert struct.unpack_from('<II',external)==(0xea020000,1)
        assert receipt['bitmap_byte_offset']==37115 and bitmap[251]==255
        receipt['narrow_bitmap_guards']={'free_blocks_superblock':free_sb,'free_blocks_group':free_group,
            'marked_blocks_before':marked,'expected_marked_after':marked-8,
            'all_allocated_inodes_checked':len(live_inodes),'deleted_inodes_unallocated':True,
            'remaining_inodes_reference_no_orphan_ea':True,'orphan_original_refcount_each':1}
    ownership=execute([builder.TOOLS/'debugfs.exe','-R','icheck 2008 2009 2010 2011 2012 2013 2014 2015',FAILED],'orphan-ownership')
    assert ownership['exit']==0 and ownership['stdout'].count('<block not found>')==8
    uuid_bytes=before[1128:1144]
    descriptor=before[4096:4128]
    assert crc16(uuid_bytes+struct.pack('<I',0)+descriptor[:30])==struct.unpack_from('<H',descriptor,30)[0]
    new_descriptor=bytearray(descriptor);struct.pack_into('<H',new_descriptor,12,31584)
    struct.pack_into('<H',new_descriptor,30,crc16(uuid_bytes+struct.pack('<I',0)+new_descriptor[:30]))
    fields={1036:struct.pack('<I',31584),4108:bytes(new_descriptor[12:14]),4126:bytes(new_descriptor[30:32]),37115:b'\0'}
    patched=work/'product-bitmap-counts.img';shutil.copyfile(FAILED,patched)
    assert builder.sha(patched)==failed_sha
    with patched.open('r+b') as stream:
        stream.seek(37115);assert stream.read(1)==b'\xff'
        for offset,content in fields.items():
            stream.seek(offset);assert stream.write(content)==len(content)
        stream.flush();os.fsync(stream.fileno())
    patched_bytes=patched.read_bytes()
    expected=bytearray(before)
    for offset,content in fields.items():expected[offset:offset+len(content)]=content
    assert patched_bytes==expected
    only_changed=[start+i for start in range(0,len(before),4096)
                  if before[start:start+4096]!=patched_bytes[start:start+4096]
                  for i,(a,b) in enumerate(zip(before[start:start+4096],patched_bytes[start:start+4096])) if a!=b]
    receipt['bitmap_only_patch']={'copy':patched.relative_to(ROOT).as_posix(),'sha256':builder.sha(patched),
        'changed_bytes':[{'offset':offset,'old':before[offset],'new':patched_bytes[offset]} for offset in only_changed],
        'all_other_bytes_identical':True,'live_inodes_and_contents_and_xattrs_unchanged':True,
        'free_counters_adjusted_by':8,'group_descriptor_crc16_recomputed':True,
        'fsck':execute([builder.TOOLS/'e2fsck.exe','-fn',patched],'fsck-bitmap-only'),
        'remaining_verification':plan.verify(patched)}
    assert receipt['bitmap_only_patch']['fsck']['exit']==0
    sanitized=work/'product-bitmap-sanitized.img'
    sanitize=execute([builder.TOOLS/'e2image.exe','-ra',patched,sanitized],'sanitize-bitmap-only')
    assert sanitize['exit']==0 and sanitized.stat().st_size==SOURCE.stat().st_size
    receipt['sanitized_copy']={'sha256':builder.sha(sanitized),
        'fsck':execute([builder.TOOLS/'e2fsck.exe','-fn',sanitized],'fsck-sanitized'),
        'remaining_verification':plan.verify(sanitized)}
    with sanitized.open('rb') as stream:
        for block in orphan_blocks:
            stream.seek(block*4096);assert stream.read(4096)==b'\0'*4096
    receipt['sanitized_copy']['former_ea_blocks_zero']=True
    assert receipt['sanitized_copy']['fsck']['exit']==0
    receipt['inputs_hashes_still_match']=builder.sha(SOURCE)==source_sha and builder.sha(FAILED)==failed_sha
    assert receipt['inputs_hashes_still_match']
    receipt['test_sha256']=builder.sha(Path(__file__))
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2))
    assert not receipt['changed_remaining_inode_bytes'] and not receipt['changed_remaining_contents']


if __name__=='__main__':main()
