"""Fixed-profile integration/negative cases on PC copies of P291 product.

Requires the immutable local original and the preserved failed attempt02.
These are real 128-byte-inode ext4 tests, not a generic repair test harness.
"""
import importlib.util
import json
import shutil
import struct
import sys
import uuid
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
import product_ea
spec=importlib.util.spec_from_file_location('product_ea_builder_test',HERE.parent/'construir.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
SOURCE=ROOT/'privado/TVBASE-respaldo-P291-20260907-194413-6d502965/product.img'
FAILED=HERE.parent/'privado/construccion-0.2.0-intento02/product/product.edited.img'


def main():
    work=ROOT/'privado/original-p291-empaquetado'/('test-product-ea-'+uuid.uuid4().hex[:10]);work.mkdir()
    records=json.loads((HERE.parent/'privado/inventario/product.json').read_text())
    source_sha=builder.sha(SOURCE);failed_sha=builder.sha(FAILED);helper_sha=builder.sha(HERE.parent/'product_ea.py')
    assert source_sha==product_ea.SOURCE_SHA
    assert failed_sha=='5130d9bd50163a89f68e2ca16f6844f494c4a6b635f8e8f844e4aa71156f20b3'

    def setup(name):
        folder=work/name;folder.mkdir()
        image=folder/'product.edited.img';shutil.copyfile(FAILED,image)
        plan=builder.Plan('product',SOURCE,records,folder)
        for path in ('/app/NativeImagePlayer','/app/DLNA','/app/OTAUpgrade','/app/Miracast'):plan.remove_tree(path)
        plan.commands=(FAILED.parent/'debugfs.txt').read_text().splitlines()
        return plan,image

    positive,image=setup('positive')
    result=product_ea.reclaimed(positive,image)
    assert result['post_fsck_exit']==0 and result['all_other_bytes_identical']
    assert result['source_unchanged'] and result['reclaimed_blocks']==list(range(2008,2016))
    negative={}
    for name in ('wrong_source_sha','wrong_bitmap','remaining_owner','wrong_size','wrong_counts','wrong_removed_inode','wrong_commands','wrong_partition'):
        plan,image=setup(name)
        if name=='wrong_source_sha':
            bad=plan.workspace/'wrong-source.img';bad.write_bytes(b'fixture with a wrong source hash');plan.source=bad
        elif name=='wrong_bitmap':
            with image.open('r+b') as stream:stream.seek(37115);stream.write(b'\xfe')
        elif name=='remaining_owner':
            # Retained droidlogic-res APK, inode27, claims an orphan as its EA.
            with image.open('r+b') as stream:stream.seek(41*4096+26*128+104);stream.write(struct.pack('<I',2008))
        elif name=='wrong_size':
            with image.open('r+b') as stream:stream.truncate(product_ea.SIZE-1)
        elif name=='wrong_counts':
            with image.open('r+b') as stream:stream.seek(1036);stream.write(struct.pack('<I',31577))
        elif name=='wrong_removed_inode':
            plan.nodes['/app/NativeImagePlayer']=dict(plan.nodes['/app/NativeImagePlayer'],inode=99)
        elif name=='wrong_commands':plan.commands=[]
        elif name=='wrong_partition':plan.part='system'
        before=builder.sha(image)
        try:product_ea.reclaimed(plan,image)
        except AssertionError as error:negative[name]={'rejected':True,'reason':str(error)}
        else:raise AssertionError('Unexpected accepted mutation '+name)
        assert builder.sha(image)==before,'Negative case wrote its image: '+name
        assert not (plan.workspace/'product-ea-reclamation.commands').exists(),'Negative case reached native mutation'
        negative[name]['image_unchanged']=True
    assert builder.sha(SOURCE)==source_sha and builder.sha(FAILED)==failed_sha
    assert builder.sha(HERE.parent/'product_ea.py')==helper_sha
    evidence={'source_sha256':source_sha,'source_inode_bytes':128,'failed_image_sha256':failed_sha,
              'helper_sha256':helper_sha,'test_sha256':builder.sha(Path(__file__)),
              'positive':result,'negative_cases':negative,'original_and_main_unchanged':True,
              'real_tv_or_usb_accessed':False,'private_evidence':work.relative_to(ROOT).as_posix()}
    with (HERE/'EVIDENCIA-PRODUCT-EA.json').open('w',encoding='utf8') as stream:json.dump(evidence,stream,indent=2);stream.write('\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
