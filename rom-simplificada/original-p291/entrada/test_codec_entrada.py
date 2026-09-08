"""Host regressions of byte guards, not a simulation of actual boot or writes."""
import unittest
import codec_entrada as c


def env():
    return c.pack_env([('bootcmd',c.ENV_NORMAL),('preboot','run storeargs'),
        ('storeboot','run original_boot'),('recovery_from_flash','run original_recovery'),
        ('recovery_part','recovery'),('recovery_offset','0'),('upgrade_step','2'),
        ('wipe_data','successful'),('wipe_cache','successful'),('untouched','value with = sign')])


class CodecTest(unittest.TestCase):
    def test_env_crc_and_order_roundtrip(self):
        a=env(); self.assertEqual(c.pack_env(c.parse_env(a)),a)

    def test_changes_only_bootcmd_value(self):
        a=env(); b=c.env_menu(a,c.sha(a))
        self.assertEqual([(k,v) for k,v in c.parse_env(a) if k!='bootcmd'],
                         [(k,v) for k,v in c.parse_env(b) if k!='bootcmd'])
        self.assertEqual(c.env_disarm(b,c.sha(b)),a)

    def test_reject_stale_snapshot(self):
        with self.assertRaises(ValueError): c.env_menu(env(),'0'*64)

    def test_reject_corruption(self):
        a=bytearray(env()); a[800]^=1
        with self.assertRaises(ValueError): c.env_menu(bytes(a),c.sha(a))

    def test_reject_duplicate_key(self):
        with self.assertRaises(ValueError): c.pack_env([('a','1'),('a','2')])

    def test_reject_oversize_and_control(self):
        for value in ('a'*65536,'a\tb','x\0y','é'):
            with self.assertRaises((ValueError,UnicodeEncodeError)):
                c.pack_env([('a',value)])

    def test_preserves_original_other_value_lf(self):
        a=c.pack_env(c.parse_env(env())+[('irremote_update','existing\n')])
        b=c.env_menu(a,c.sha(a))
        self.assertEqual(dict(c.parse_env(b))['irremote_update'],'existing\n')
        self.assertNotIn('\n',dict(c.parse_env(b))['bootcmd'])

    def test_reject_armed_and_unknown_disarm(self):
        a=env(); b=c.env_menu(a,c.sha(a))
        with self.assertRaises(ValueError): c.env_menu(b,c.sha(b))
        with self.assertRaises(ValueError): c.env_disarm(a,c.sha(a))

    def test_reject_pending_oem_state(self):
        for key,value in (('upgrade_step','3'),('wipe_data','failed'),('wipe_cache','failed'),
                          ('recovery_part','boot'),('recovery_offset','100')):
            a=c.pack_env([(k,value if k==key else v) for k,v in c.parse_env(env())])
            with self.assertRaises(ValueError): c.env_menu(a,c.sha(a))

    def test_partition_tail_preserved_and_unknown_rejected(self):
        a=env()+bytes(c.PARTITION_SIZE-c.ENV_SIZE)
        b=c.env_partition(a,c.sha(a));self.assertEqual(b[c.ENV_SIZE:],a[c.ENV_SIZE:])
        a=a[:-1]+b'X'
        with self.assertRaises(ValueError): c.env_partition(a,c.sha(a))

    def test_bcb_preserves_all_other_bytes(self):
        a=bytes(range(256))*(c.PARTITION_SIZE//256)
        b=c.bcb_menu(a,c.sha(a))
        self.assertEqual(b[32:64],a[32:64]);self.assertEqual(b[832:],a[832:])
        self.assertEqual(b[64:832],c.MENU_ARGS.ljust(768,b'\0'))
        self.assertNotIn(b'--update_package',b[64:832])

    def test_bcb_disarm_only_owned_request(self):
        a=bytes(c.PARTITION_SIZE);b=c.bcb_menu(a,c.sha(a))
        self.assertEqual(c.bcb_disarm(b,c.sha(b)),a)
        with self.assertRaises(ValueError):c.bcb_disarm(a,c.sha(a))

    def test_lengths(self):
        for a in (b'',bytes(2048),bytes(c.PARTITION_SIZE+1)):
            with self.assertRaises(ValueError):c.bcb_menu(a,c.sha(a))


if __name__=='__main__':
    unittest.main()
