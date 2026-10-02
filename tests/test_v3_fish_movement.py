"""Current movement choices remain independent of population and match the donor."""
import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,u32
import v3_optional_composition as composer
from v3_creature_choices import options,freshwater_patches,update_report
from v3_furniture_pipeline import Source


class FishMovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(ROOT/'build/v3-freshwater-patrol-installed-06/build-lock.json')
        cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report)
        cls.options=options(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_population_and_movement_are_independent(self):
        self.assertIn('fish-population',[r['id'] for r in self.options])
        self.assertNotIn('coastal-fish-movement',[r['id'] for r in self.options])
        movement=next(r for r in self.options if r['id']=='fish-movement')
        patches=freshwater_patches(self.image,self.report)
        self.assertEqual(len(patches),7)
        original=next(r for r in self.report['equipment_resources']['creature_fish']['owners'] if r['name']=='river')
        files=by_vrom(self.image)
        for population in ('N64','GameCube'):
            for swimming in ('N64','GameCube'):
                values={'fish-population':population,'fish-movement':swimming}
                selected=composer.resolve(self.catalog,['GAFE01-r0/item/3298'],scope='v3-pipeline',
                    report=self.report,behaviour_options=self.options,behaviours=values)
                image,writes,blob=composer.compose(self.image,self.report,self.catalog,selected)
                self.assertEqual(u32(image,movement['offset']),int(swimming=='GameCube'))
                for patch in patches:
                    expected=patch['after'] if swimming=='GameCube' else patch['before']
                    self.assertEqual(image[patch['offset']:patch['offset']+len(bytes.fromhex(expected))].hex(),expected)
                current=by_vrom(image)
                # Both choices retain every native instruction. The donor mode
                # replaces only six table pointers and their relocation records.
                size=original['sections'][0]
                self.assertEqual(current[original['vrom']].extract(image)[:size],files[original['vrom']].extract(self.image)[:size])
                if swimming=='N64':
                    for vrom in (original['vrom'],original['reloc']):
                        self.assertEqual(current[vrom].extract(image),files[vrom].extract(self.image))
                report=copy.deepcopy(self.report);update_report(image,blob,report,selected['behaviours'])
                world=report['equipment_resources']['creature_fish']['world']
                self.assertEqual(world['spawn_mode']['value'],int(population=='GameCube'))
                self.assertEqual(world['patrol_mode']['value'],int(swimming=='GameCube'))
                river=next(r for r in report['equipment_resources']['creature_fish']['owners'] if r['name']=='river')
                self.assertEqual(river['sha256'],sha256(by_vrom(image)[river['vrom']].extract(image)))
        for patch in patches:
            corrupt=bytearray(self.image);corrupt[patch['offset']]^=1
            with self.assertRaisesRegex(ValueError,'freshwater movement'):
                freshwater_patches(corrupt,self.report)

    def test_complete_donor_function_and_equal_elapsed_turns(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        code,proof=source.function(0x233464)
        self.assertEqual(proof['symbol'],'aGTT_swim_speed_change')
        self.assertEqual(sha256(code),'9762d0db93a1a6ec6d7d664a8cc6d3c22c36afb6e173cf7945135832f3b93e57')
        self.assertEqual(struct.unpack_from('>f',source.rel,source.sections[4][0]+37476)[0],0.5)
        wrap=lambda n:(n+32768)%65536-32768
        for heading in (-32768,-25000,-1,0,12345,32767):
            for target in (-32768,-12000,0,20000,32767):
                gc=heading;native=heading;increment=int(wrap(target-heading)/36)
                for frame in range(1,37):
                    for tick in (frame*2-1,frame*2):
                        if tick*2.5>5:gc=wrap(gc+increment)
                    if frame*5>5:native=wrap(native+2*increment)
                    self.assertEqual(native,gc)
                # The original native path makes 35 additions, not 70.
                if increment:self.assertNotEqual(native,wrap(heading+35*increment))

    def test_empty_default_choices_keep_the_translation_baseline(self):
        selection=composer.resolve(self.catalog,[],scope='v3-pipeline',report=self.report,
            behaviour_options=self.options)
        image,_,_=composer.compose(self.image,self.report,self.catalog,selection)
        path,digest,_=composer.stable_reference(self.report)
        self.assertEqual(sha256(image),digest)
        self.assertEqual(image,path.read_bytes())


if __name__=='__main__':unittest.main()
