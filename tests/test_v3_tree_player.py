"""Shared player targeting, query ABI, current relocation, and optionality."""
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,u32
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from npc_mail_show import relocate_verified_data
from v3_import_storage import jump
import v3_scenery_runtime as scenery
import v3_scenery_player as player
import v3_scenery_field as field
import tests.test_v3_equipment_runtime as shared
OUTPUT=ROOT/os.environ.get('V3_TREE_PLAYER_BUILD','build/v3-shared-tree-field-01')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_all_native_and_imported_predicates(self):self.sanitized('v3_tree_player_test.c',defines=('-DAF_V3_TREE_FELLING',))
    def test_field_clearing_and_insect_habitats(self):self.sanitized('v3_tree_field_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current player-tree cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery'];cls.p=cls.r['player_queries']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        cls.original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()

    def test_complete_source_native_retention_and_all_relocated_queries(self):
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        previous=self.prior['equipment_resources']['scenery'].get('player_queries')
        evidence,*_=player.contract(source,self.base,self.original,self.prior['equipment_resources']['player_actions'],previous)
        for k,v in evidence.items():self.assertEqual(json.loads(json.dumps(v)),self.p[k])
        data=self.files[player.VROM].extract(self.rom);before=self.before[player.VROM].extract(self.base)
        rel=self.files[player.RELOC].extract(self.rom);oldrel=self.before[player.RELOC].extract(self.base)
        restored=bytearray(data)
        for p in self.p['patches']:
            at=p['offset'];self.assertEqual(u32(data,at),p['after']);self.assertEqual(u32(before,at),p['before'])
            struct.pack_into('>I',restored,at,p['before'])
        self.assertEqual(restored,before);self.assertEqual(rel[:16],oldrel[:16]);self.assertEqual(len(rel),len(oldrel))
        records=struct.unpack_from('>'+str(u32(oldrel,16))+'I',oldrel,20)
        retained=[v for v in records if not previous or v not in previous['added_relocations']]
        self.assertEqual(struct.unpack_from('>'+str(u32(rel,16))+'I',rel,20),tuple([*retained,*self.p['added_relocations']]))
        self.assertEqual(len(self.p['calls']),12)
        gate=player.gate(self.r['bootstrap']['symbols']['load'],self.r['code']['symbols']['af_v3_tree_player_query'])
        self.assertEqual(data[player.GATE-player.RAM:player.GATE-player.RAM+len(gate)],gate)
        for ram in (0x80200010,0x80300010):
            moved=relocate_verified_data(SimpleNamespace(ram=player.RAM,resident_bytes=self.p['resident_bytes'],
                sections=struct.unpack_from('>5I',rel)),data,rel,ram)
            for row in self.p['calls']:
                at=row['address']-player.RAM
                self.assertEqual(u32(moved,at),jump(ram+player.GATE-player.RAM,link=True))
                self.assertEqual(u32(moved,at+4),player.descriptor(row['source'],row['result'],row['query']))
            self.assertEqual(moved[player.GATE-player.RAM:player.GATE-player.RAM+len(gate)],gate)
        for name in ('player_actions','player_motion'):
            self.assertEqual(self.e[name]['owner_sha256'],sha256(data))
        self.assertEqual(self.e['player_actions']['relocation_sha256'],sha256(rel))
        self.assertEqual(self.e['player_motion']['reloc_sha256'],sha256(rel))

    def test_seasonal_camera_bindings_and_unchanged_height_geometry(self):
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        evidence=player.camera_contract(source,self.base,self.original,self.prior['equipment_resources']['scenery'])
        for k,v in evidence.items():self.assertEqual(json.loads(json.dumps(v)),self.r['felling_camera'][k])
        for variant,(row,binding) in enumerate(zip(self.r['owners'],evidence['owners'],strict=True)):
            data=self.files[row['vrom']].extract(self.rom);rel=self.files[row['reloc']].extract(self.rom)
            target=self.r['code']['symbols'][f'af_v3_tree_talk{variant}']
            before=self.before[row['vrom']].extract(self.base)
            self.assertEqual(data[binding['entry']:binding['move']],before[binding['entry']:binding['move']])
            for ram in (0x80200010,0x80300010):
                moved=relocate_verified_data(SimpleNamespace(ram=row['ram'],resident_bytes=sum(struct.unpack_from('>4I',rel)),
                    sections=struct.unpack_from('>5I',rel)),data,rel,ram)
                hi,lo=u32(moved,binding['hi']),u32(moved,binding['lo'])
                self.assertEqual(((hi&65535)<<16)+struct.unpack('>h',struct.pack('>H',lo&65535))[0],target)
        core=self.files[CODE_VROM].extract(self.rom);old=self.before[CODE_VROM].extract(self.base)
        for a,b in ((0x800A5AC8,0x800A5B4C),(0x8010B478,0x8010B49C)):
            self.assertEqual(core[a-CODE_RAM:b-CODE_RAM],old[a-CODE_RAM:b-CODE_RAM])

    def test_complete_field_consumers_and_relocated_insect_predicate(self):
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        evidence,data,rel,records=field.contract(source,self.base,self.original)
        core=bytearray(self.before[CODE_VROM].extract(self.base))
        changes,receipt=field.install(evidence,data,rel,records,core,self.r['bootstrap'],self.r['code']['symbols'])
        self.assertEqual(json.loads(json.dumps(receipt)),self.r['field_insects'])
        for v,expected in changes.items():self.assertEqual(self.files[v].extract(self.rom),expected)
        actual=bytearray(self.files[CODE_VROM].extract(self.rom));before=self.before[CODE_VROM].extract(self.base)
        for row in self.r['interactions']['daily_owner']['core_hooks']:
            at=row['offset'];self.assertEqual(actual[at:at+len(bytes.fromhex(row['after']))].hex(),row['after'])
            actual[at:at+len(bytes.fromhex(row['before']))]=bytes.fromhex(row['before'])
        for row in receipt['core_hooks']:
            at=row['offset'];self.assertEqual(actual[at:at+12].hex(),row['after']);actual[at:at+12]=bytes.fromhex(row['before'])
        self.assertEqual(actual,before)
        for ram in (0x80200010,0x80300010):
            moved=relocate_verified_data(SimpleNamespace(ram=field.RAM,resident_bytes=evidence['resident_bytes'],
                sections=struct.unpack_from('>5I',changes[field.RELOC])),changes[field.VROM],changes[field.RELOC],ram)
            self.assertEqual(u32(moved,field.MATCH-field.RAM),jump(ram+field.GATE-field.RAM,link=True))
            self.assertEqual(moved[field.GATE-field.RAM:field.GATE-field.RAM+receipt['gate_bytes']],
                             changes[field.VROM][field.GATE-field.RAM:field.GATE-field.RAM+receipt['gate_bytes']])
        for key in ('sections','resident_bytes'):
            self.assertEqual(evidence[key],receipt[key])

    def test_retained_allocations_resources_and_rebound_shared_consumers(self):
        old=self.prior['equipment_resources'];a=scenery.BOOT_RAM-old['ram'];b=scenery.BOOT_END-old['ram'];start=old['blob_offset']
        before=self.oldblob[start:start+old['bytes']];after=self.blob[start:start+self.e['bytes']]
        self.assertEqual(before[:a],after[:a]);self.assertEqual(before[b:],after[b:]);self.assertEqual(len(before),len(after))
        self.assertEqual(self.r['banks'],old['scenery']['banks']);self.assertEqual(len(self.blob),len(self.oldblob))
        self.assertEqual(self.r['additional_fixed_resident_bytes'],12288)
        self.assertEqual(self.p['additional_resident_bytes'],0);self.assertEqual(self.p['additional_scene_resident_bytes'],0)
        code=(OUTPUT/'scenery/code.bin').read_bytes();start=self.r['blob_offset']
        self.assertEqual(self.blob[start:start+len(code)],code);self.assertLessEqual(len(code),12288)
        at=self.r['code']['symbols']['af_v3_tree_player_masks']-self.r['ram']
        self.assertEqual(code[at:at+24],struct.pack('>6I',*(v for row in self.p['masks'] for v in row)))
        for row in (*self.r['owners'],self.r['interactions']['daily_owner']):
            data=self.files[row['vrom']].extract(self.rom);before=self.before[row['vrom']].extract(self.base)
            restored=bytearray(data)
            for p in row['patches']:
                self.assertEqual(u32(data,p['offset']),p['after']);self.assertEqual(u32(before,p['offset']),p['before'])
                struct.pack_into('>I',restored,p['offset'],p['before'])
            self.assertEqual(restored,before)
        for path in scenery.SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])

    def test_complete_patch_optional_profiles_and_save_retention(self):
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        changed={BLOB,MODULE,CODE_VROM,0x19D40,0x970920,0x9754A0,player.VROM,player.RELOC,field.VROM,field.RELOC}|{r[k] for r in self.r['owners'] for k in ('vrom','reloc')}
        for v,e in self.before.items():
            if v not in changed:self.assertEqual(e.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for key in ('save_runtime','save_codec','catalogue','furniture'):self.assertEqual(self.prior[key],self.report[key])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.r['selectable']);self.assertFalse(self.r['acquisition_installed'])
        import v3_optional_composition as composer
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');choices=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(choices),128)
            self.assertEqual(composer.compose(self.rom,self.report,choices,composer.resolve(choices,list(choices)))[0],self.rom)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,choices,composer.resolve(choices,[]))[0]),
                'a09373b051cbcd93991e5dd6cb17a238a2afb1e2e2d7694d75408d24a55d4eee')
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin

if __name__=='__main__':unittest.main()
