"""Focused checks of the current V2 artifact, without replaying older builds."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from catalogue_names import Image
from keyboard_rc1_fix import metrics
from keyboard_grid_labels import encode_label
from keyboard_v2 import (BASE_SHA,VROM,RELOC,OWNER,PREFIX,RAM,CALL,SPEC,BOTTOM,
                         source_hashes,recover,ASSETS,ART_VROM,draw_source)
from npc_mail_show import relocate_verified_data

OUT=ROOT/'build/v2-keyboard-02'


class KeyboardV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(ROOT/'build/v1-final/Animal Forest English V1 Final.z64').read_bytes()
        cls.image=(OUT/'Animal Forest English V2 Development.z64').read_bytes()
        cls.report=json.loads((OUT/'build.json').read_text())
        cls.files=by_vrom(cls.base); cls.current=by_vrom(cls.image)
        cls.data=cls.current[VROM].extract(cls.image);cls.rel=cls.current[RELOC].extract(cls.image)

    def test_current_receipt_and_complete_patch(self):
        self.assertEqual(sha256(self.base),BASE_SHA)
        self.assertEqual(sha256(self.image),self.report['output_sha256'])
        self.assertEqual(self.report['sources'],source_hashes())
        self.assertEqual(sha256(self.data),self.report['editor']['overlay_sha256'])
        patch=(OUT/'Animal Forest English V2 Development.ups').read_bytes()
        self.assertEqual(sha256(patch),self.report['patch_sha256'])
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,patch),self.image)
        self.assertEqual(len(self.image),len(self.base))
        self.assertFalse(self.report['public_release'])

    def test_only_editor_presentation_and_its_size_metadata_change(self):
        self.assertEqual(set(self.files),set(self.current))
        for v,e in self.files.items():
            self.assertEqual(e.index,self.current[v].index)
            if v not in (VROM,RELOC,OWNER,0x19D40):
                self.assertEqual(e.extract(self.base),self.current[v].extract(self.image),hex(v))
        owner=bytearray(self.files[OWNER].extract(self.base))
        struct.pack_into('>4I',owner,SPEC['owner_at'],VROM,VROM+len(self.data),RAM,RAM+len(self.data))
        self.assertEqual(owner,self.current[OWNER].extract(self.image))
        self.assertLessEqual(self.report['shared_growth_bytes'],8192)
        self.assertEqual(self.report['additional_pool_bytes'],0)

    def test_entire_accepted_input_editor_survives_relocation(self):
        old=self.files[VROM].extract(self.base); rel=self.files[RELOC].extract(self.base)
        recover(old,rel)
        self.assertEqual(self.report['editor']['touched_offsets'],list(range(CALL,CALL+4)))
        for address in (0x80200010,0x80378010):
            before=relocate_verified_data(Image(RAM,len(old),struct.unpack_from('>5I',rel)),old,rel,address)
            after=relocate_verified_data(Image(RAM,len(self.data),struct.unpack_from('>5I',self.rel)),
                                         self.data,self.rel,address)
            self.assertEqual(before[:CALL],after[:CALL])
            self.assertEqual(before[CALL+4:PREFIX],after[CALL+4:PREFIX])
            target=address+self.report['editor']['symbols']['af_bg_editor_draw']
            self.assertEqual(struct.unpack_from('>I',after,CALL)[0],0x0C000000|(target>>2&0x3FFFFFF))
        damaged=bytearray(old);damaged[30000]^=1
        with self.assertRaises(ValueError): recover(bytes(damaged),rel)

    def test_retained_font_metrics_frames_and_native_controller_pixels(self):
        raw,_=metrics(self.base);symbols=self.report['editor']['symbols']
        at=symbols['af_key_origins'];self.assertEqual(self.data[at:at+len(raw)],raw)
        self.assertEqual(self.data[PREFIX:].count(encode_label(BOTTOM)+b'\0'),1)
        self.assertEqual(self.current[ART_VROM].extract(self.image),self.files[ART_VROM].extract(self.base))
        self.assertEqual(len(self.report['native_artwork']),len(ASSETS))
        for flag in ('font_pixels_changed','sound_code_changed','input_code_changed','save_format_changed'):
            self.assertFalse(self.report[flag])
        helper,panel=draw_source()
        self.assertIn(b'g=af_v2_controls(g,dx,dy);',helper)
        self.assertIn(b'225,225,225,255',panel)
        self.assertIn(b'105,110,115,255',panel)
        # The changed source does not alter the accepted grid coordinates.
        self.assertIn(b'60+16*(i%10)+slide[i/10]+dx',helper)
        self.assertIn(b'60+16*cell.column+slide[cell.row]+dx',helper)


if __name__=='__main__': unittest.main()
