"""Current complete font pages, unchanged saved owner, and corruption rejection."""
import copy
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import DMA_START,by_vrom,sha256
from v3_asset_loader import MODULE
from v3_furniture_install import inputs
from v3_nook_font import VROM,PIXEL_PAGES,check_pixel_layout,retained_ram
from v3_furniture_pipeline import Source
from v3_password_acquisition import checked
from npc_mail_show import relocate_verified_data
from catalogue_names import Image

BUILD=ROOT/os.environ.get('V3_NOOK_FONT_REPAIR','build/v3-nook-font-repaired-01')


class FontRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(BUILD/'build-lock.json')
        cls.base,cls.prior=inputs(BUILD/'base-lock.json')
        cls.font=cls.report['equipment_resources']['passwords']['nook']['font']
        cls.old=cls.prior['equipment_resources']['passwords']['nook']['font']
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_artwork_and_guarded_disjoint_pages(self):
        f=self.font;p=f['physical_resource']
        self.assertEqual(p,self.old['physical_resource'])
        self.assertEqual(f['glyphs'],self.old['glyphs'])
        raw=self.image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual(raw,self.base[p['physical']:p['physical']+p['bytes']])
        self.assertEqual(len(raw),61728)
        self.assertEqual(sum(n for _,n in PIXEL_PAGES),len(raw))
        rebuilt=b''.join(raw[r['source_offset']:r['source_offset']+r['bytes']] for r in f['pixel_pages'])
        self.assertEqual(raw,rebuilt)
        check_pixel_layout(self.report,f)
        self.assertEqual(f['pixel_pages'][1]['bytes']//144,192)
        self.assertEqual(f['pixel_pages'][2]['bytes']//144,64)
        self.assertEqual(f['additional_resident_bytes'],61728)
        self.assertLessEqual(f['bytes']+f['relocation_bytes'],0x7FE0)
        from v3_console_disk_install import reservations
        spans=set(reservations(self.report))
        for page in f['pixel_pages']:
            self.assertIn((page['front_guard'],page['end_guard']+16),spans)

    def test_current_native_frontend_and_saved_owners(self):
        binding=checked(self.source,self.image,self.report)
        self.assertTrue(binding['native_delivery_installed'])
        self.assertFalse(binding['ordinary_gameplay_tested'])
        for k in ('save_codec','save_runtime','clothing','room_surfaces'):
            self.assertEqual(self.report[k],self.prior[k],k)
        for k in ('bank','private_save_bank','scene_arena','seasonal_stock'):
            self.assertEqual(self.report['equipment_resources'][k],self.prior['equipment_resources'][k],k)
        old=by_vrom(self.base);new=by_vrom(self.image)
        changed=[v for v in old if old[v].extract(self.base)!=new[v].extract(self.image)]
        # Shared bootstrap ABI/checksums also change; native shop owners do not.
        from v3_asset_loader import BLOB
        self.assertEqual(set(changed),{VROM,MODULE,BLOB,0x19D40})
        core_a=old[0x19D40].extract(self.base);core_b=new[0x19D40].extract(self.image)
        # Moving a complete font updates only its native DMA directory row.
        directory=DMA_START-0x19D40+old[VROM].index*16
        self.assertEqual(core_a[:directory],core_b[:directory])
        self.assertEqual(core_a[directory+16:],core_b[directory+16:])
        config=struct.unpack_from('>8I',new[MODULE].extract(self.image),0x68)
        self.assertEqual(config,tuple(self.font['configuration']))
        self.assertEqual(config[6],zlib.crc32(new[VROM].extract(self.image)))

    def test_retained_prefix_relocations_and_title_are_unchanged(self):
        old=by_vrom(self.base)[VROM].extract(self.base)
        new=by_vrom(self.image)[VROM].extract(self.image)
        touched={i for p in self.font['patches'] for i in range(p['at'],p['at']+8)}
        for ram in (0x801A0010,0x80450010):
            def relocate(data,r):
                n=r['bytes'];rel=data[n:]
                return relocate_verified_data(Image(r['ram'],n,struct.unpack_from('>5I',rel)),
                    data[:n],rel,ram,memory_end=0x80800000)
            a=relocate(old,self.old);b=relocate(new,self.font)
            self.assertEqual(bytes(a[i] for i in range(27744) if i not in touched),
                bytes(b[i] for i in range(27744) if i not in touched))
        self.assertEqual(self.font['title_buffer'],self.old['title_buffer'])

    def test_old_collision_and_new_owner_conflicts_reject(self):
        with self.assertRaisesRegex(ValueError,'overlaps a retained RAM owner'):
            check_pixel_layout(self.prior,self.old)
        for page in self.font['pixel_pages']:
            r=copy.deepcopy(self.report)
            r['new_retained_owner']=dict(ram=page['ram'],bytes=16)
            with self.assertRaisesRegex(ValueError,'overlaps a retained RAM owner'):
                check_pixel_layout(r,self.font)
        r=copy.deepcopy(self.report)
        r['equipment_resources']['private_save_bank']['retained_state']['title_buffer']['ram']+=16
        with self.assertRaisesRegex(ValueError,'title-buffer alias'):
            list(retained_ram(r,self.font))
        f=copy.deepcopy(self.font);f['pixel_pages'][2]['source_offset']-=144
        with self.assertRaisesRegex(ValueError,'source-ordered font page layout'):
            check_pixel_layout(self.report,f)


if __name__=='__main__':unittest.main()
