"""Mailbox/repayment source pixels, safe repacking, and complete cartridge retention."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups
from service_artwork import MAIL,REPAY,MAIL_DONOR,ROWS,commands,patch_assets,build,expected_load
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/service-artwork-01/build.json').is_file(),'Local service artwork required')
class ServiceArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/catalogue-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/catalogue-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.image=(ROOT/'build/service-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/service-artwork-01/build.json').read_text())
        cls.compiled={row[0]:(ROOT/'build/service-artwork-commands'/f'{row[0]}.bin').read_bytes() for row in ROWS}

    def test_complete_images_and_unchanged_border_and_numeric_geometry(self):
        changed,profile=patch_assets(self.native,self.rel,self.symbols,self.compiled)
        self.assertEqual(profile,self.report['service_artwork']);files=by_vrom(self.native)
        mail=changed[MAIL];old_mail=files[MAIL].extract(self.native)
        self.assertEqual(decode(mail[0x35B0:0x37B0],64,16,'i4'),
            decode(self.rel[DATA_BASE+MAIL_DONOR.gc:DATA_BASE+MAIL_DONOR.gc+512],64,16,'i4',gamecube=True))
        self.assertEqual(mail[:0x35B0],old_mail[:0x35B0]);self.assertEqual(mail[0x37B0:],old_mail[0x37B0:])
        data=changed[REPAY];old=files[REPAY].extract(self.native)
        allowed=set(range(0x1288,0x1888))|set(range(0x2A08,0x2C08))|set(range(0x2088,0x2188))|set(range(0xA84,0xA88))
        regions=[(0x1488,0x1508)]
        for name,donor,width,original,target,load,quad,old_width in ROWS:
            self.assertEqual(decode(data[target:target+width*8],width,16,'i4'),
                decode(self.rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*8],width,16,'i4',gamecube=True))
            self.assertTrue(all(target>=b or a>=target+width*8 for a,b in regions));regions.append((target,target+width*8))
            self.assertEqual(data[load:load+56],expected_load(target,width))
            allowed.update(range(load,load+56))
            if name=='bells':
                self.assertEqual(data[quad:quad+192],old[quad:quad+192])
            else:
                for at in range(quad,quad+64,16):
                    a=struct.unpack_from('>3hH2h4B',old,at);b=struct.unpack_from('>3hH2h4B',data,at)
                    self.assertEqual(b[0],-12 if a[0]==-12 else -12-width*3//4)
                    self.assertEqual(b[4],a[4]*width//old_width)
                    self.assertEqual((a[1:4],a[5:]),(b[1:4],b[5:]))
                allowed.update(range(quad,quad+64))
        self.assertEqual(data[0x1488:0x1508],old[0x2B88:0x2C08])
        self.assertEqual(data[0x1508:0x1588],bytes(128))
        self.assertEqual(data[0xA84:0xA88],bytes.fromhex('0C001488'))
        self.assertEqual(len(data),len(old))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))

    def test_independent_compiled_commands_and_source_rejection(self):
        with tempfile.TemporaryDirectory(prefix='af-service-artwork-') as directory:
            self.assertEqual(commands(Path(directory)),self.compiled)
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+b'\n')):
            with self.assertRaises(ValueError):patch_assets(self.native,rel,symbols,self.compiled)
        bad=dict(self.compiled);bad['owe']=bytes(56)
        with self.assertRaises(ValueError):patch_assets(self.native,self.rel,self.symbols,bad)

    def test_complete_cartridge_retains_owners_money_and_all_previous_artwork(self):
        image,patch,report=build(self.native,self.base,self.prior,self.rel,self.symbols,self.compiled)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        old,new=by_vrom(self.base),by_vrom(image)
        self.assertEqual(set(old),set(new));self.assertEqual(len(image),len(self.base))
        for address,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[address].index,new[address].size))
            if address not in (MAIL,REPAY,0x19D40):self.assertEqual(entry.extract(self.base),new[address].extract(image))
        from keyboard_grid_overlay import verify_owned_parts
        verify_owned_parts(image,self.native,report['keyboard_grid'],report['apology_input'])


if __name__=='__main__':unittest.main()
