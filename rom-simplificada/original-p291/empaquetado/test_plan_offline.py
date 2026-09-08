"""Exercise the image Plan on a new 16 MiB local ext4 fixture, never on the ROM."""
import hashlib
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
spec=importlib.util.spec_from_file_location('p291_construction_under_test',HERE.parent/'construir.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


def main(output_name):
    assert Path(output_name).name==output_name and output_name.endswith('.json')
    source_hash=builder.sha(HERE.parent/'construir.py')
    private=(ROOT/'privado').resolve();assert private.is_relative_to(ROOT)
    with tempfile.TemporaryDirectory(prefix='fixture-plan-ext4-',dir=private) as generated:
        work=Path(generated).resolve();assert work.is_relative_to(private)
        image=work/'original.img'
        with image.open('xb') as stream:stream.truncate(16<<20)
        builder.run([builder.TOOLS/'mke2fs.exe','-F','-t','ext4','-b','4096','-I','256','-O','^64bit,^metadata_csum',image],work/'mkfs.log')
        old_marker=b'TVBASE_REMOVED_APK_FIXTURE_ONLY_\x00\r\n'
        old=work/'old.bin';old.write_bytes(old_marker*32768)
        firmware=work/'firmware.bin';firmware.write_bytes(b'PRESERVED_FIRMWARE_FIXTURE\0'*1024)
        config=work/'config.txt';config.write_bytes(b'old configuration\n')
        label=work/'label.txt';label.write_bytes(b'u:object_r:system_file:s0\0')
        capability=work/'capability.bin';capability.write_bytes(bytes.fromhex('01000002c0000000000000000000000000000000'))
        opaque=work/'opaque.bin';opaque.write_bytes(b'\0\r\n\xff\"\\opaque-fixture')
        long_label=work/'long-label.bin';long_label.write_bytes(b'u:object_r:hal_allocator_default_exec:s0\0')
        assert long_label.stat().st_size==41
        seed=work/'seed.txt'
        commands=['mkdir /app','mkdir /app/Old','mkdir /etc','mkdir /firmware',
                  'cd /app/Old','write '+builder.quote(old)+' Old.apk','cd /etc',
                  'write '+builder.quote(config)+' config.txt','cd /firmware',
                  'write '+builder.quote(firmware)+' firmware.bin','cd /',
                  'symlink /firmware/driver-link firmware.bin',
                  'ea_set -f '+builder.quote(capability)+' /firmware/firmware.bin security.capability',
                  'ea_set -f '+builder.quote(opaque)+' /firmware/firmware.bin user.fixture']
        for path in ('/app','/app/Old','/etc','/firmware','/app/Old/Old.apk','/etc/config.txt','/firmware/firmware.bin','/firmware/driver-link'):
            commands.append('ea_set -f '+builder.quote(label)+' '+builder.quote(path)+' security.selinux')
        commands.append('ea_set -f '+builder.quote(long_label)+' /firmware/firmware.bin security.selinux')
        seed.write_text('\n'.join(commands)+'\n')
        builder.run([builder.TOOLS/'debugfs.exe','-w','-f',seed,image],work/'seed.log')
        builder.run([builder.TOOLS/'e2fsck.exe','-fn',image],work/'seed-fsck.log')
        display=builder.run([builder.TOOLS/'debugfs.exe','-R','ea_list /firmware/firmware.bin',image],work/'ea41-display.log')
        assert b'  security.selinux (41)\n' in display.replace(b'\r\n',b'\n'),display
        original_sha=builder.sha(image)
        records=[]
        with builder.filesystem(image) as (fs,nodes):
            for path,node in nodes.items():
                row={key:value for key,value in node.items() if key!='raw'};row['path']=path
                if node['modo']&0xf000 in (0x8000,0xa000):row['sha256']=hashlib.sha256(fs.content(node)).hexdigest()
                records.append(row)
        edited_dir=work/'edited';edited_dir.mkdir()
        plan=builder.Plan('fixture',image,records,edited_dir)
        plan.remove_tree('/app/Old')
        plan.put('/etc/config.txt',b'new configuration\n')
        plan.put('/app/New/New.apk',b'new application fixture\0\r\n',context='u:object_r:system_file:s0')
        edited=edited_dir/'edited.img';final=edited_dir/'final.img'
        plan.apply(edited);before=plan.verify(edited)
        assert old_marker in edited.read_bytes(),'Fixture must expose freed old data before sanitization'
        builder.run([builder.TOOLS/'e2image.exe','-ra',edited,final],work/'e2image.log')
        builder.run([builder.TOOLS/'e2fsck.exe','-fn',final],work/'final-fsck.log')
        after=plan.verify(final)
        exact_long_label={'bytes':41,'sha256':builder.sha(long_label)}
        assert plan.xattrs(final,['/firmware/firmware.bin'],'ea41-explicit')['/firmware/firmware.bin']['security.selinux']==exact_long_label
        assert old_marker not in final.read_bytes(),'Removed APK marker survived in final fixture'
        assert final.stat().st_size==image.stat().st_size
        free_blocks=0
        with builder.filesystem(final) as (fs,nodes):
            assert fs.content(nodes['/firmware/firmware.bin'])==firmware.read_bytes()
            assert fs.content(nodes['/etc/config.txt'])==b'new configuration\n'
            superblock=fs.r.read(1024,1024);per_group=struct.unpack_from('<I',superblock,32)[0]
            count=fs.meta['bytes_fs']//fs.bs
            for group in range((count+per_group-1)//per_group):
                descriptor=fs.r.read((fs.first+1)*fs.bs+group*fs.descsize,fs.descsize)
                bitmap_block=struct.unpack_from('<I',descriptor,0)[0]
                if fs.descsize>=64:bitmap_block+=struct.unpack_from('<I',descriptor,32)[0]<<32
                bitmap=fs.r.read(bitmap_block*fs.bs,fs.bs)
                for index in range(min(per_group,count-fs.first-group*per_group)):
                    if not bitmap[index//8]&(1<<(index%8)):
                        number=fs.first+group*per_group+index
                        assert not any(fs.r.read(number*fs.bs,fs.bs)),number
                        free_blocks+=1
        # Each attack modifies a separate small PC fixture. The canonical final
        # fixture and all original/release files remain unchanged.
        different_label=work/'different-label.bin';different_label.write_bytes(b'u:object_r:vendor_file:s0\0')
        different_capability=work/'different-capability.bin';different_capability.write_bytes(bytes.fromhex('01000002c1000000000000000000000000000000'))
        different_opaque=work/'different-opaque.bin';different_opaque.write_bytes(b'\0\r\n\xff\"\\opaque-fixturE')
        different_long_label=work/'different-long-label.bin';different_long_label.write_bytes(b'u:object_r:hal_allocator_default_exeC:s0\0')
        changed_data=work/'different-firmware.bin';changed_data.write_bytes(b'altered preserved firmware\0')
        attacks={
            'new_directory_selinux_missing':['ea_rm /app/New security.selinux'],
            'new_directory_selinux_changed':['ea_set -f '+builder.quote(different_label)+' /app/New security.selinux'],
            'preserved_capability_same_size_changed':['ea_set -f '+builder.quote(different_capability)+' /firmware/firmware.bin security.capability'],
            'preserved_user_attribute_same_size_changed':['ea_set -f '+builder.quote(different_opaque)+' /firmware/firmware.bin user.fixture'],
            'preserved_selinux_41_bytes_changed':['ea_set -f '+builder.quote(different_long_label)+' /firmware/firmware.bin security.selinux'],
            'preserved_attribute_added':['ea_set -f '+builder.quote(opaque)+' /firmware/driver-link user.extra'],
            'preserved_file_mode_changed':['set_inode_field /firmware/firmware.bin mode 0100755'],
            'new_directory_uid_changed':['set_inode_field /app/New uid 1000'],
            'edited_file_gid_changed':['set_inode_field /etc/config.txt gid 1000'],
            'preserved_file_content_changed':['rm /firmware/firmware.bin','cd /firmware','write '+builder.quote(changed_data)+' firmware.bin','cd /'],
            'symlink_target_changed':['rm /firmware/driver-link','symlink /firmware/driver-link other.bin','ea_set -f '+builder.quote(label)+' /firmware/driver-link security.selinux'],
        }
        rejections={}
        final_sha=builder.sha(final)
        for name,commands in attacks.items():
            attacked=edited_dir/(name+'.img');shutil.copyfile(final,attacked)
            command_file=work/(name+'.commands');command_file.write_text('\n'.join(commands)+'\n',encoding='utf8')
            builder.run([builder.TOOLS/'debugfs.exe','-w','-f',command_file,attacked],work/(name+'.log'))
            assert builder.sha(attacked)!=final_sha,'Attack must change the fixture: '+name
            try:plan.verify(attacked)
            except AssertionError as error:rejections[name]={'rejected':True,'reason':str(error)}
            else:rejections[name]={'rejected':False}
        assert builder.sha(final)==final_sha
        # These transport/parser failures must fail before any binary extraction.
        parser_samples={
            'unexpected_error_line':'debugfs: ea_list "/fixture"\nExtended attributes:\nsecurity.selinux (41)\nea_list: bad inode\n',
            'negative_attribute_size':'debugfs: ea_list "/fixture"\nExtended attributes:\nsecurity.selinux (-1)\n',
            'duplicate_attribute':'debugfs: ea_list "/fixture"\nExtended attributes:\nsecurity.selinux (41)\nsecurity.selinux (41)\n',
            'missing_command':'Extended attributes:\nsecurity.selinux (41)\n',
            'wrong_path':'debugfs: ea_list "/other"\nExtended attributes:\nsecurity.selinux (41)\n',
            'truncated_attribute':'debugfs: ea_list "/fixture"\nExtended attributes:\nsecurity.selinux (41\n',
        }
        parser_rejections={}
        for name,output in parser_samples.items():
            with patch.object(builder,'run',return_value=output.encode()) as mocked:
                try:plan.xattrs(final,['/fixture'],'parser-'+name)
                except AssertionError:parser_rejections[name]=True
                else:parser_rejections[name]=False
                assert mocked.call_count==1,'Malformed list reached binary extraction: '+name
        assert builder.sha(image)==original_sha
        assert builder.sha(HERE.parent/'construir.py')==source_hash,'Builder changed while fixture ran'
        result={'fixture_bytes':image.stat().st_size,'source_sha256':source_hash,'original_fixture_unchanged':True,
                'edited_verification':before,'final_verification':after,'free_zero_blocks_verified':free_blocks,
                'removed_apk_marker_absent':True,'firmware_bytes_preserved':True,
                'negative_cases':rejections,'all_negative_cases_rejected':all(v['rejected'] for v in rejections.values()),
                'new_directory_missing_selinux_accepted':not rejections['new_directory_selinux_missing']['rejected'],
                'long_attribute_display_omits_value':True,'long_selinux_attribute_verified':exact_long_label,
                'malformed_parser_cases_rejected':parser_rejections,
                'real_rom_touched':False,'tv_accessed':False,'usb_accessed':False}
    result['test_sha256']=builder.sha(Path(__file__))
    output=HERE/output_name
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    assert result['all_negative_cases_rejected'],'One or more metadata/content mutations passed verification'
    assert all(result['malformed_parser_cases_rejected'].values()),'Malformed attribute list accepted'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',default='EVIDENCIA-PLAN-EA41.json')
    main(parser.parse_args().receipt)
