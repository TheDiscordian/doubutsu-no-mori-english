"""Focused source and native mappings for displacement-driven rig imports."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source,prepare
from v3_furniture_motion import CATEGORY,native_contract
from v3_furniture_install import inputs

class MotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_motion_and_changed_code_rejection(self):
        profile=prepare(self.source,0x3018)[0];a=profile['callback_adapter'];r=a['rolling']
        self.assertEqual(a['category'],CATEGORY);self.assertEqual(a['pending_callbacks'],[])
        self.assertEqual(r['duration'],100);self.assertEqual(r['native_push_states'],[9,11,14,1])
        self.assertEqual(r['native_pull_states'],[10,12,2]);self.assertEqual(len(profile['models']),2)
        for row in [a['functions']['move'],r['source_initializer'],r['helpers']['fTMny_GetSpeed'],r['helpers']['aMR_GetContactInfoLayer1']]:
            changed=copy.copy(self.source);changed.rel=bytearray(changed.rel)
            changed.rel[changed.sections[1][0]+row['offset']]^=1
            with self.assertRaises(ValueError):prepare(changed,0x3018)
        for at in (0,4,0x20,0x30,49736):
            changed=copy.copy(self.source);changed.rel=bytearray(changed.rel)
            changed.rel[changed.sections[4][0]+at]^=1
            with self.assertRaisesRegex(ValueError,'constant'):prepare(changed,0x3018)

    def test_rolling_motion_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-rolling-') as temporary:
            binary=Path(temporary)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_rolling_test.c'),
                '-lm','-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('instance guards',result.stdout)

    def test_current_motion_contract_and_relocated_packet(self):
        from aflib import by_vrom,sha256
        from v3_asset_loader import BLOB
        from v3_room_rig_runtime import packet_layout,encode_packet,EXTENDED_RAM,EXTENDED_TABLE,EXTENDED_BYTES
        out=ROOT/os.environ.get('V3_IMPORTED_RIG_BUILD','build/v3-rolling-category-auto-02/cartridge')
        image,report=inputs(out/'build-lock.json');files=by_vrom(image)
        blob=files[BLOB].extract(image);rigs=report['equipment_resources']['room_rigs']
        native=native_contract(image)
        self.assertEqual(native,rigs['motion_contract']['native'])
        self.assertEqual(packet_layout(rigs),(EXTENDED_RAM,EXTENDED_TABLE,EXTENDED_BYTES))
        p=rigs['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(raw),p['sha256'])
        self.assertEqual(raw[EXTENDED_TABLE-EXTENDED_RAM:],
            encode_packet(rigs['rows'],rigs['sound_rows'],rigs['material_rows']))
        e=report['equipment_resources'];password=e['passwords']
        self.assertLessEqual(password['ram']+password['bytes'],EXTENDED_RAM)
        self.assertLessEqual(EXTENDED_RAM+EXTENDED_BYTES,report['furniture']['bank_pool']['start'])
        # Moving the rig packet must not consume the scroll or surface ranges.
        self.assertLessEqual(rigs['scrolling']['packet']['ram']+rigs['scrolling']['packet']['bytes'],EXTENDED_RAM)
        self.assertEqual(e['room_rigs']['sound_table'],EXTENDED_TABLE+0xC10)
        self.assertEqual(e['room_rigs']['material_table'],EXTENDED_TABLE+0xE20)
        for entry,address in ((files[0x1060],0x80033470-0x80025C60),
                              (files[0x82D7F0],0x8094D0F4-0x80936710)):
            self.assertFalse(entry.pend)
            changed=bytearray(image);changed[entry.pstart+address]^=1
            with self.assertRaisesRegex(ValueError,'native'):native_contract(changed)

    def test_changed_shared_motion_and_sound_callbacks_under_sanitizers(self):
        from v3_room_movement import encode
        from v3_furniture_scroll import encode_lifecycles
        out=ROOT/os.environ.get('V3_IMPORTED_RIG_BUILD','build/v3-rolling-category-auto-02/cartridge')
        _,report=inputs(out/'build-lock.json');scroll=report['equipment_resources']['room_rigs']['scrolling']
        # Reuse the established C checks against current data, not old builds.
        fixtures=(('contact',None),('categories',None),('movement',encode(scroll['movement']['rows'])),
            ('scroll_lifecycle',encode_lifecycles([r for r in scroll['lifecycle_rows'] if r['mode'] in (1,2)])))
        with tempfile.TemporaryDirectory(prefix='v3-motion-consumers-') as temporary:
            directory=Path(temporary)
            for name,data in fixtures:
                with self.subTest(callback=name):
                    binary=directory/name
                    run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                        str(ROOT/f'tests/v3_room_{name}_test.c'),'-o',str(binary)],
                        capture_output=True,text=True,timeout=30)
                    self.assertEqual(run.returncode,0,run.stderr)
                    arguments=[str(binary)]
                    if data is not None:
                        table=directory/(name+'.bin');table.write_bytes(data);arguments.append(str(table))
                    run=subprocess.run(arguments,capture_output=True,text=True,timeout=20)
                    self.assertEqual(run.returncode,0,run.stderr)
