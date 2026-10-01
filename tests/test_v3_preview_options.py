"""Focused checks of the current V3 house/ocean composition, not old builds."""
import copy
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256, n64_checksum
import v3_optional_composition as composer
import v3_creature_choices as choices
import v3_starting_diary as diary


class PreviewOptionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(ROOT/'build/v3-nook-font-repaired-02/build-lock.json')
        cls.image,cls.report = composer.inputs()
        cls.catalog = composer.catalogue(cls.image,cls.report)
        cls.choices = choices.options(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI = cls.saved

    def select(self, requested, modes):
        return composer.resolve(self.catalog,requested,behaviours=modes,
            behaviour_options=self.choices,scope='v3-pipeline',report=self.report)

    def test_source_house_contract_and_automatic_requirements(self):
        option = next(row for row in self.choices if row['id']=='starting-diary')
        self.assertEqual(option['source']['main_cell'],[1,1])
        self.assertEqual(option['source']['secondary_cell'],[1,1])
        self.assertEqual(option['source']['sha256'],diary.DONOR_ROOM_SHA)
        selected = self.select([],{'starting-diary':'GameCube'})
        self.assertEqual(selected['requested'],[])
        self.assertEqual(selected['required'],['GAFE01-r0/item/2B00','GAFE01-r0/item/30F8'])
        for key in selected['required']:
            self.assertEqual(selected['dependency_reasons'][key],['starting-diary'])
        self.assertEqual(self.select([],{} )['enabled'],[])
        changed = copy.deepcopy(self.report)
        next(row for row in changed['furniture']['imports'] if row['id']==diary.BOX)['profile']['profile_symbol']='other'
        with self.assertRaises(ValueError):diary.option(self.image,changed)
        for patch in option['patches']:
            bad = bytearray(self.image);bad[patch['offset']]^=1
            with self.assertRaises(ValueError):diary.option(bad,self.report)

    def test_modes_change_only_declared_writes_and_repair_checksums(self):
        modes={'starting-diary':'GameCube','coastal-fish-movement':'GameCube'}
        selected = self.select([],modes)
        output,writes,blob = composer.compose(self.image,self.report,self.catalog,selected)
        self.assertIsNotNone(blob)
        expected = composer.apply_writes(self.image,writes)
        self.assertEqual(output,expected)
        self.assertEqual(output[0x10:0x18],struct.pack('>2I',*n64_checksum(output)))
        for field in choices.checksum_fields(self.image,self.report):
            self.assertEqual(struct.unpack_from('>I',output,field['offset'])[0],
                zlib.crc32(output[field['start']:field['start']+field['length']]))
        for option in self.choices:
            if option['id'] not in modes:continue
            for patch in option['patches']:
                size=len(patch['before'])//2
                self.assertEqual(output[patch['offset']:patch['offset']+size].hex(),patch['after'])
                self.assertEqual(self.image[patch['offset']:patch['offset']+size].hex(),patch['before'])
        forged = copy.deepcopy(selected);forged['enabled'].remove(diary.BOX)
        with self.assertRaises(ValueError):composer.compose(self.image,self.report,self.catalog,forged)

    def test_default_all_and_empty_keep_existing_cartridge_pins(self):
        from v3_import_scope import requested_options
        all_selected=self.select(requested_options(self.catalog,self.report),{})
        output,_,_=composer.compose(self.image,self.report,self.catalog,all_selected)
        self.assertEqual(sha256(output),'2f0431103dbcc49d346957f82edcebd5e476bf24886188c2c7977f1f2e8421e9')
        empty,_,_=composer.compose(self.image,self.report,self.catalog,self.select([],{}))
        self.assertEqual(sha256(empty),'0e81d5c62548c3a759cc89d63eba0975b1c336a3a941211a3000e317b9243bf2')


if __name__=='__main__':unittest.main()
