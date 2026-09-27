"""Changed collection/message path; no replay of old native scenarios."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,u32
from textbanks import Bank
from v3_asset_loader import BLOB
from v3_creature_ui import DATA,RAM,FIRST,MESSAGE,TABLE,CHOICES,CHOICE_TABLE
from v3_furniture_install import inputs
OUT=ROOT/os.environ.get('V3_CREATURE_UI_BUILD','build/v3-creature-world-work-01/connected-10')


class CreatureUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        # Preserve the UI's original source comparison even when a later stage
        # only adds composer bindings. This is not execution of an old ROM.
        cls.base,cls.prior=inputs(ROOT/'build/v3-creature-world-work-01/connected-09/base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.world=cls.report['equipment_resources']['creature_fish']['world'];cls.ui=cls.world['ui']

    def test_all_collection_and_catch_message_paths(self):
        blob=self.files[BLOB].extract(self.image);p=self.world['packet']
        first=p['blob_offset']+DATA-p['ram'];data=blob[first:first+0xF0]
        with tempfile.TemporaryDirectory(prefix='af-creature-ui-') as directory:
            out=Path(directory)
            (out/'ui_data.h').write_text('const unsigned char af_creature_ui_data[]={'+
                ','.join(str(n) for n in data)+'};\n')
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I',str(out),str(ROOT/'tests/v3_creature_ui_test.c'),
                str(ROOT/'overlays/v3/creature_ui.c'),'-o',str(out/'check')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(out/'check')],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('All 81 collection identities',result.stdout)

    def test_installed_grid_text_hooks_and_preservation(self):
        from v3_creature_ui import messages,layout
        from v3_furniture_pipeline import Source,rig_import_plan
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        extra,text=messages(self.base,source);data,grid=layout(self.base,source,text)
        self.assertEqual(grid,self.ui['grid']);self.assertEqual(len(extra),17)
        def bank(image,files):return Bank('messages',0,0,files[MESSAGE].extract(image),files[TABLE].extract(image)).entries()
        old=bank(self.base,self.oldfiles);new=bank(self.image,self.files)
        self.assertEqual(len(old),FIRST);self.assertEqual(new,old+extra)
        self.assertEqual(text['rows'],self.ui['text']['rows'])
        self.assertEqual(text['provenance_entries'],self.ui['text']['provenance_entries'])
        for v in (self.report['import_storage']['choice_vrom'],CHOICE_TABLE):
            self.assertEqual(self.files[v].extract(self.image),self.oldfiles[v].extract(self.base))
        p=self.world['packet'];blob=self.files[BLOB].extract(self.image)
        oldp=self.prior['equipment_resources']['creature_fish']['world']['packet']
        oldblob=self.oldfiles[BLOB].extract(self.base)
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']];restored=bytearray(packet)
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(zlib.crc32(packet),p['crc32'])
        self.assertEqual(packet[DATA-p['ram']:DATA-p['ram']+len(data)],data)
        code=self.ui['code'];self.assertEqual(sha256(packet[RAM-p['ram']:RAM-p['ram']+code['bytes']]),code['sha256'])
        for at,n in ((RAM,code['bytes']),(DATA,len(data))):restored[at-p['ram']:at-p['ram']+n]=bytes(n)
        self.assertEqual(restored,oldblob[oldp['blob_offset']:oldp['blob_offset']+oldp['bytes']])
        for owner in self.ui['owners']:
            current=self.files[owner['vrom']].extract(self.image);old=self.oldfiles[owner['vrom']].extract(self.base)
            self.assertEqual(sha256(current),owner['sha256']);restored=bytearray(current)
            for row in owner['patches']:
                at=row['address']-owner['ram'];self.assertEqual(u32(current,at),row['after'])
                struct.pack_into('>I',restored,at,row['before'])
            self.assertEqual(restored,old)
            if 'reloc' in owner:
                before=self.oldfiles[owner['reloc']].extract(self.base);after=self.files[owner['reloc']].extract(self.image)
                self.assertEqual(sha256(after),owner['reloc_sha256'])
                records=struct.unpack_from('>'+str(u32(before,16))+'I',before,20)
                kept=[r for r in records if r not in owner['removed_relocations']]
                self.assertEqual(list(struct.unpack_from('>'+str(u32(after,16))+'I',after,20)),kept)
        tag=self.files[0x3950000].extract(self.image);ram=0x8086F310
        self.assertEqual(struct.unpack_from('>HHII',tag,0x80878A54-ram),(9,5,DATA+0x70,DATA+0x84))
        self.assertEqual(u32(tag,0x8087499C-ram),0xACC80038)
        self.assertEqual(u32(tag,0x80874990-ram),0x24030007) # Table ID stays seven.
        # Native generic movement consumes the descriptor; its full code stays unchanged.
        self.assertEqual(tag[0x80874680-ram:0x80874770-ram],
            self.oldfiles[0x3950000].extract(self.base)[0x80874680-ram:0x80874770-ram])
        self.assertEqual(set(grid['fish']),set(range(41)));self.assertEqual(set(grid['insects']),set(range(40)))
        for address,word in ((0x8009E3A4,0x2A010000),(0x8009E668,0x28A10000)):
            self.assertEqual(u32(self.files[CODE_VROM].extract(self.image),address-CODE_RAM),word|(FIRST+17))
        # Assembly keeps the constructor's argument delay slot, player stack slot,
        # and original return address. Both compiled trampolines are checked here.
        symbols=code['symbols']
        for kind in ('fish','insect'):
            pos=symbols[f'af_v3_creature_{kind}_message_call']-p['ram']
            self.assertEqual(struct.unpack_from('>3I',packet,pos),
                (0x00802825,0x08000000|(symbols[f'af_v3_creature_{kind}_message']>>2&0x3FFFFFF),0x8FA40050))
        e=self.report['equipment_resources'];before=self.prior['equipment_resources']
        for key in ('creature_items','creature_field','console_images','room_goods','room_carry'):
            self.assertEqual(e[key]['packet'],before[key]['packet'])
        self.assertEqual(self.report['physical_resources'],self.prior['physical_resources'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        inv=dict(rows=[dict(item_id=r['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=r['source']['profile']) for r in e['creature_items']['profiles']])
        self.assertTrue(rig_import_plan(inv,self.prior,{},category='creature-profile-assets',source=source)['creature_fish'])
        self.assertNotIn('creature_fish',rig_import_plan(inv,self.report,{},category='creature-profile-assets',source=source))
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_current_optional_composition_preserves_baseline(self):
        import v3_optional_composition as composer
        saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalogue=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalogue),167)
            self.assertEqual(composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,[]))[0]),
                self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=saved


if __name__=='__main__':unittest.main()
