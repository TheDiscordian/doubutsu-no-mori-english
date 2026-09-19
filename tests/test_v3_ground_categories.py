"""Complete seasonal category installation and unchanged composition inputs."""
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum,u32
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs
from npc_mail_show import relocate_verified_data
from v3_player_actions import native_references
import v3_ground_categories as ground
import tests.test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_GROUND_BUILD','build/v3-ground-categories-02')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_all_seasonal_tables_and_loaded_owner_lifetimes(self): self.sanitized('v3_ground_categories_test.c')
    def test_shared_category_selection_and_fallback(self): self.sanitized('v3_item_categories_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current seasonal cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.e=cls.report['equipment_resources']
        cls.r=cls.e['ground_categories'];at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_every_owner_capacity_relocation_and_retained_instruction(self):
        for spec in self.r['owners']:
            old=self.before[spec['vrom']].extract(self.base);data=self.files[spec['vrom']].extract(self.rom)
            rel=self.files[spec['reloc']].extract(self.rom);original=self.before[spec['reloc']].extract(self.base)
            cap=spec['capacity'];restored=bytearray(data)
            self.assertEqual(sha256(data),spec['output_sha256']);self.assertEqual(sha256(rel),spec['output_reloc_sha256'])
            for patch in spec['patches']:
                at=patch['offset'];self.assertEqual(u32(old,at),patch['before']);self.assertEqual(u32(data,at),patch['after'])
                struct.pack_into('>I',restored,at,patch['before'])
            self.assertEqual(restored,old)
            sections=struct.unpack_from('>5I',rel)
            self.assertEqual(tuple(spec['sections'][:3]),sections[:3])
            self.assertEqual(sum(sections[:4]),cap['resident_bytes'])
            self.assertEqual(sections[4],u32(original,16)-1)
            self.assertEqual(list(struct.unpack_from('>'+str(sections[4])+'I',rel,20)),
                [r for r in struct.unpack_from('>'+str(u32(original,16))+'I',original,20) if r not in spec['removed_relocations']])
            for base in (0x80200010,0x80360010):
                moved=relocate_verified_data(SimpleNamespace(ram=spec['ram'],resident_bytes=cap['resident_bytes'],sections=sections),data,rel,base)
                self.assertEqual(u32(moved,sections[0]+16),self.r['code']['symbols']['af_v3_ground_'+spec['role']])
                # Resolve relocated pairs independently of the installer.
                for hi,lo in spec['refs']:
                    address=((u32(moved,hi)&65535)<<16)+struct.unpack_from('>h',moved,lo+2)[0]
                    self.assertEqual(address,base+cap['table_offset'])
                self.assertEqual(moved[len(data):],bytes(cap['bss_bytes']))
            self.assertEqual(cap['count'],spec['count']+44)
            self.assertEqual(cap['actor_bytes'],spec['actor']+4*cap['index_stride'])
            self.assertEqual(cap['stack_bytes'],264)
            self.assertLessEqual(44+cap['count']*2,cap['stack_bytes'])
            # Preserve NONE sentinels, matrix dimensions, and Christmas light strides.
            changed={r['offset'] for r in spec['patches']}
            for at in range(0,spec['sections'][0],4):
                w=u32(old,at)
                if w>>26 in (4,5,10,11) and w&65535==spec['count'] and at!=0x5E2C:
                    self.assertNotIn(at,changed)
            if spec['role']=='xmas':
                for at in (0x80909B08,0x80909B0C,0x80909B10,0x80909B14):
                    self.assertEqual(u32(old,at-spec['ram']),u32(data,at-spec['ram']))

    def test_source_contract_mutations_reject_and_config_matches_owners(self):
        for i,spec in enumerate(ground.OWNERS):
            owner,rel=(self.before[spec[k]].extract(self.base) for k in ('vrom','reloc'))
            cfg,cap,_=ground.layout(owner,rel,spec,71,9)
            self.assertEqual(struct.unpack_from('>9I',self.module,ground.CONFIG+36*i),cfg)
            self.assertEqual(self.r['owners'][i]['capacity'],cap)
            for pos in (0,len(owner)//2,len(owner)-1):
                damaged=bytearray(owner);damaged[pos]^=1
                with self.assertRaises(ValueError):ground.layout(damaged,rel,spec,71,9)
        self.assertEqual(sha256(self.module[ground.CONFIG:ground.CONFIG+self.r['config_bytes']]),self.r['config_sha256'])

    def test_startup_allocation_core_fallback_and_retained_assets(self):
        core=self.files[CODE_VROM].extract(self.rom);old_core=self.before[CODE_VROM].extract(self.base)
        restored=bytearray(core);at=0x800A5630-CODE_RAM
        self.assertEqual(u32(core,at),ground.jump(0x804AA000));restored[at:at+4]=old_core[at:at+4]
        for row in self.r['owners']:
            at=row['allocation_descriptor']-CODE_RAM+12
            self.assertEqual(u32(core,at),row['ram']+row['capacity']['resident_bytes'])
            restored[at:at+4]=old_core[at:at+4]
        self.assertEqual(restored,old_core)
        self.assertIn('-DAF_V3_CATEGORY_ORIGINAL=0x8046744Cu',self.e['item_categories']['code']['flags'])
        old=self.prior['equipment_resources'];oldblob=self.before[BLOB].extract(self.base)
        previous=oldblob[old['blob_offset']:old['blob_offset']+old['bytes']]
        self.assertEqual(self.module[:0x7000],previous[:0x7000])
        self.assertEqual(self.module[0x7200:ground.CODE],previous[0x7200:])
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.module[-16:],bytes.fromhex('AF48C0DE')*4)
        self.assertEqual(self.blob[0x20:0xE0],oldblob[0x20:0xE0])
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0xB000u',self.report['startup']['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],CONFIG-STARTUP)

    def test_patch_checksums_and_unrelated_resources(self):
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        changed={BLOB,MODULE,CODE_VROM,0x19D40}|{s[k] for s in ground.OWNERS for k in ('vrom','reloc')}
        self.assertEqual(self.before.keys(),self.files.keys())
        for v,file in self.before.items():
            self.assertEqual(file.index,self.files[v].index)
            if v not in changed:self.assertEqual(file.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for p in ground.SOURCES:self.assertEqual(sha256((ROOT/p).read_bytes()),self.report['sources'][p])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_profile_changed'])

if __name__=='__main__':unittest.main()
