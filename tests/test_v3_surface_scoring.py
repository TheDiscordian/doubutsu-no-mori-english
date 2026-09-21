"""Full-index surface HRA integration and unchanged bulk import contracts."""
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_surface_scoring import tables,patch_owner,SOURCES,ENTRY,END
import v3_hra as hra
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-scoring-runtime-01'


class SurfaceScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.before=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old=cls.before[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.items=cls.surface['items'];cls.score=cls.surface['scoring']
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_source_weights_preserve_all_originals_and_full_new_categories(self):
        old=self.before[hra.NEW_VROM].extract(self.base)
        resources=tables(old,self.prior['hra'],self.surface,self.source)
        self.assertEqual([r for _,r in resources],self.score['tables'])
        for (table,row),original_at in zip(resources,(0x809295D8,0x80929598)):
            at=self.items['blob_offset']+row['offset'];self.assertEqual(self.blob[at:at+len(table)],table)
            values=struct.unpack('>256H',table)
            weights=struct.unpack_from('>23I',old,self.prior['hra']['birth_extension']['points_address']-hra.RAM)
            self.assertEqual(values[:64],tuple(weights[c] for c in old[original_at-hra.RAM:original_at-hra.RAM+64]))
            self.assertEqual(values[73:78],(412,51,1000,412,1177))
            self.assertFalse(any(values[64:73]+values[78:]))
        self.assertEqual({(r['name'],r['series'],r['index']) for r in self.score['themes']},
            {('western',55,73),('backyard',56,74),('boxing',58,76)})

    def test_complete_owner_and_relocation_changes_are_bounded(self):
        old=self.before[hra.NEW_VROM].extract(self.base);rel=self.before[hra.NEW_RELOC].extract(self.base)
        data,fixed,hr,receipt=patch_owner(old,rel,self.prior['hra'],self.score['tables'],self.source)
        self.assertEqual(data,self.files[hra.NEW_VROM].extract(self.image));self.assertEqual(fixed,self.files[hra.NEW_RELOC].extract(self.image))
        self.assertEqual(hr,self.report['hra']);self.assertEqual(receipt,self.score)
        window=self.score['window'];a=window['address']-hra.RAM
        allowed=set(range(a,a+window['bytes']))|{r['offset']+2 for r in self.score['themes']}
        for destination in (0x801A0010,0x802F8010,0x803D0010):
            before=relocate_verified_data(Image(hra.RAM,len(old),struct.unpack_from('>5I',rel)),old,rel,destination)
            after=relocate_verified_data(Image(hra.RAM,len(data),struct.unpack_from('>5I',fixed)),data,fixed,destination)
            self.assertTrue(all(i in allowed or x==y for i,(x,y) in enumerate(zip(before,after))))
            self.assertEqual(after[a:a+window['bytes']],bytes.fromhex(window['after']))
        bad=bytearray(old);bad[ENTRY-hra.RAM+4]^=1
        with self.assertRaisesRegex(ValueError,'complete current HRA'):patch_owner(bad,rel,self.prior['hra'],self.score['tables'],self.source)
        self.assertEqual(len(data),len(old));self.assertEqual(len(fixed),len(rel))
        self.assertEqual(data[END-hra.RAM:END-hra.RAM+12],old[END-hra.RAM:END-hra.RAM+12])

    def test_current_resources_profile_composition_and_patch(self):
        at=self.items['blob_offset'];packet=self.blob[at:at+self.items['bytes']]
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        self.assertEqual(packet[:0x3600],self.old[at:at+0x3600])
        self.assertEqual(packet[0x3A00:],self.old[at+0x3A00:at+0x4000])
        for key in ('rows','banks','application','save','menu'):self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for key in ('save_runtime','save_codec','catalogue'):self.assertEqual(self.report[key],self.prior[key])
        self.assertFalse(self.report['saved_format_changed'])
        for vrom in (0x3970000,0x3980000,0x3950000,0x3960000,0x846860,CODE_VROM):
            self.assertEqual(self.files[vrom].extract(self.image),self.before[vrom].extract(self.base))
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.surface['sources'][path])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');choices=composer.catalogue(self.image,self.report)
            self.assertEqual(len(choices),141)
            self.assertEqual(composer.compose(self.image,self.report,choices,composer.resolve(choices,list(choices)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,choices,composer.resolve(choices,[]))[0]),self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
