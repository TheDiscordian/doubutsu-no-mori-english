"""Current cartridge bindings and the complete category's passport round trip."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,CODE_RAM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_creature_save import DEFINES
import v3_optional_composition as composer
import v3_browser_composition as browser
import v3_creature_choices as choices
import test_v3_creature_selection as selection_tests

OUT=ROOT/os.environ.get('V3_CREATURE_TRAVEL_BUILD','build/v3-creature-world-work-01/connected-15')


class CreatureTravelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json');cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report);cls.plan=browser.rules(cls.image,cls.report)
        cls.fish=[k for k,v in cls.catalog.items() if v['kind']=='fish']
        cls.behaviours=choices.options(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.previous

    def test_connected_host_travel(self):
        with tempfile.TemporaryDirectory(prefix='af-creature-travel-') as directory:
            target=Path(directory)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-fno-pie','-no-pie',*['-D'+f for f in DEFINES],
                '-DAF_V3_CREATURE_VISITORS=1']
            result=subprocess.run(['cc',*flags,str(ROOT/'tests/v3_creature_travel_test.c'),
                str(ROOT/'overlays/v3/creature_collection.c'),'-o',str(target)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(target)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('all 17 records, four residents',result.stdout)

    def test_installed_transport_and_retained_resources(self):
        base,prior=inputs(OUT/'base-lock.json');f=by_vrom(self.image);b=f[BLOB].extract(self.image)
        oldb=by_vrom(base)[BLOB].extract(base);e=self.report['equipment_resources'];old=prior['equipment_resources']
        w=e['creature_fish']['world'];p=w['packet'];travel=w['creature_travel'];code=travel['code']
        packet=b[p['blob_offset']:p['blob_offset']+p['bytes']];raw=packet[0xB000:0xB000+code['bytes']]
        self.assertEqual(p['bytes'],0xC000);self.assertLessEqual(len(raw),0xFC0)
        self.assertEqual(sha256(raw),code['sha256']);self.assertEqual(packet[0xB000:0xB000+len(raw)],raw)
        self.assertEqual(packet[0xBFC0:0xBFF0],bytes(48))
        self.assertEqual(packet[-16:],struct.pack('>4I',*([0xAF465748]*4)))
        self.assertEqual(self.report['save_codec'],prior['save_codec'])
        self.assertEqual(self.report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertEqual(self.report['physical_resources'],prior['physical_resources'])
        self.assertEqual(e['creature_items']['packet'],old['creature_items']['packet'])
        core=f[CODE_VROM].extract(self.image);original=by_vrom(base)[CODE_VROM].extract(base)
        normal=bytearray(core)
        retained=bool(old['creature_fish']['world'].get('creature_travel'))
        retail=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        native=by_vrom(retail)[CODE_VROM].extract(retail)
        for r in travel['patches']:
            pos=r['address']-CODE_RAM
            self.assertEqual(core[pos:pos+8].hex(),r['after'])
            self.assertEqual(sha256(native[pos:pos+r['bytes']]),r['function_sha256'])
            normal[pos:pos+8]=bytes.fromhex(r['before'])
        self.assertEqual(core if retained else normal,original)
        r=travel['collection_redirect'];pos=r['address']-p['ram'];normalized=bytearray(packet[:0xB000])
        self.assertEqual(normalized[pos:pos+8].hex(),r['after']);normalized[pos:pos+8]=bytes.fromhex(r['before'])
        op=old['creature_fish']['world']['packet']
        self.assertEqual(packet if retained else normalized,oldb[op['blob_offset']:op['blob_offset']+op['bytes']])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),self.image)
        self.assertEqual(len(self.catalog),176)
        self.assertIn('passport readers do not understand this extension',self.plan['save_compatibility'])
        for path in ('overlays/v3/creature_travel.c','overlays/v3/creature_collection.c','overlays/v3/creature_travel.ld'):
            self.assertEqual(sha256((ROOT/path).read_bytes()),e['creature_fish']['sources'][path])
        # The entry stays fixed: existing catches, completion and UI calls still
        # reach the replaced reader without relinking their unchanged owners.
        for owner in w['manager_owners']:
            if owner['name']=='completion':continue
            self.assertEqual(f[owner['vrom']].extract(self.image),by_vrom(base)[owner['vrom']].extract(base))
        self.assertEqual(w['pocket_icons'],old['creature_fish']['world']['pocket_icons'])
        self.assertEqual(w['ui'],old['creature_fish']['world']['ui'])

    def test_source_house_evaluation_for_complete_category(self):
        from v3_furniture_pipeline import Source
        import v3_hra as hra
        import v3_feng_shui as feng
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        base,prior=inputs(OUT/'base-lock.json');record=self.report['equipment_resources']['creature_items']['room_scoring']
        self.assertEqual(len(record['rows']),17);self.assertEqual(len(record['installed_identities']),9)
        for key,tool,width,donor_at,field in (('hra',hra,4,0x4FAFC,'native_hra_hex'),
                ('feng_shui',feng,2,0x4EBF0,'feng_hex')):
            data=by_vrom(self.image)[tool.NEW_VROM].extract(self.image)
            old=by_vrom(base)[tool.NEW_VROM].extract(base);normalized=bytearray(data)
            at=self.report[key]['metadata_address']-tool.RAM
            for row in record['rows']:
                n=donor_at+row['source_index']*width
                self.assertEqual(source.data[n:n+width].hex(),row['donor_hra_hex' if width==4 else 'feng_hex'])
                pos=at+row['runtime_index']*width
                expected=bytes.fromhex(row[field]) if row['installed'] else bytes.fromhex('fc000000') if width==4 else bytes(2)
                self.assertEqual(data[pos:pos+width],expected)
                normalized[pos:pos+width]=old[pos:pos+width]
            self.assertEqual(normalized,old)

    # Reuse the same six all/empty/partial/behaviour cases on the changed packet;
    # there is no replay of historical cartridge or native fixtures.
    test_browser_profiles=selection_tests.CreatureSelectionTests.test_browser_offline_complete_partial_and_behaviour_profiles


if __name__=='__main__':unittest.main()
