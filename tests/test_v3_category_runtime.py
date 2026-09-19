"""Shared category assets, both native owners, capacity, and unchanged profiles."""
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
from aflib import CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs
from npc_mail_show import relocate_verified_data
import v3_category_runtime as runtime
import tests.test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_CATEGORY_BUILD','build/v3-category-runtime-03')


class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_category_bounds_and_profile_selection(self):self.sanitized('v3_item_categories_test.c')


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current shared category cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.e=cls.report['equipment_resources']
        cls.r=cls.e['item_categories'];at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_complete_artwork_rebases_only_resource_pointers(self):
        source=runtime.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        assets,rows,evidence=runtime.prepared(source,ROOT/self.r['art_directory'])
        for key,value in evidence.items():self.assertEqual(self.r[key],value)
        self.assertEqual(len(rows),9);self.assertEqual(sum(len(x) for x in assets.values()),7344)
        for row in self.r['objects']:
            data=assets[row['source_category']];at=row['offset'];actual=self.module[at:at+len(data)]
            self.assertEqual(sha256(actual),row['installed_sha256']);restored=bytearray(actual)
            self.assertEqual(len(row['pointer_relocations']),3)
            for fix in row['pointer_relocations']:
                p=fix['offset'];self.assertEqual(struct.unpack_from('>I',actual,p)[0],fix['after'])
                self.assertEqual(fix['after'],(row['ram']&0x1FFFFFFF)+(fix['before']&0xFFFFFF))
                self.assertEqual(fix['after']>>24,0)
                struct.pack_into('>I',restored,p,fix['before'])
            self.assertEqual(restored,data)
            bad=bytearray(data);struct.pack_into('>I',bad,row['pointer_relocations'][0]['offset'],0x05000000)
            with self.assertRaises(ValueError):runtime.rebase_art(bad,row,row['ram'])
            with self.assertRaises(ValueError):runtime.rebase_art(data,row,0x80800000)
        self.assertFalse(self.r['ground_installed']);self.assertFalse(self.r['selectable'])

    def test_extended_tables_preserve_all_native_entries_and_source_mapping(self):
        self.assertEqual(self.r['count'],71)
        mapping=self.module[runtime.MAP:runtime.MAP+self.r['map_bytes']]
        self.assertEqual(struct.unpack_from('>4I',mapping),(0x41464354,1,71,53))
        rows={r['source_category']:r for r in self.r['objects']}
        for category,value in enumerate(mapping[16:]):
            self.assertEqual(value,27+category if category in rows else 0)
        for index,t in enumerate(self.r['tables']):
            at=t['offset'];raw=self.module[at:at+t['bytes']]
            self.assertEqual(sha256(raw),t['sha256'])
            for spec in runtime.OWNERS:
                owner=self.before[spec['vrom']].extract(self.base);p=spec['tables'][index]-spec['ram']
                self.assertEqual(raw[:108],owner[p:p+108])
            values=struct.unpack('>71I',raw)
            for category in range(27,71):
                row=rows.get(category-27)
                self.assertEqual(values[category],(row['ram']&0x1FFFFFFF)+row['model_offsets'][t['role']] if row else 0)

    def test_only_declared_native_edits_and_two_loaded_owner_locations(self):
        for spec in self.r['owners']:
            old=self.before[spec['vrom']].extract(self.base);new=self.files[spec['vrom']].extract(self.rom)
            rel=self.files[spec['reloc']].extract(self.rom);restored=bytearray(new)
            self.assertEqual(sha256(new),spec['output_sha256'])
            self.assertEqual(sha256(rel),spec['output_reloc_sha256'])
            for row in spec['patches']:
                self.assertEqual(struct.unpack_from('>I',old,row['offset'])[0],row['before'])
                self.assertEqual(struct.unpack_from('>I',new,row['offset'])[0],row['after'])
                struct.pack_into('>I',restored,row['offset'],row['before'])
            self.assertEqual(restored,old)
            original_rel=self.before[spec['reloc']].extract(self.base)
            before_n=struct.unpack_from('>I',original_rel,16)[0];after_n=struct.unpack_from('>I',rel,16)[0]
            self.assertEqual(after_n,before_n-4)
            self.assertEqual(list(struct.unpack_from('>'+str(after_n)+'I',rel,20)),
                [r for r in struct.unpack_from('>'+str(before_n)+'I',original_rel,20) if r not in spec['removed_relocations']])
            for ram in (0x80200010,0x80378010):
                loaded=relocate_verified_data(SimpleNamespace(ram=spec['ram'],resident_bytes=sum(spec['sections']),
                    sections=struct.unpack_from('>5I',rel)),new,rel,ram)
                for row in spec['patches']:
                    self.assertEqual(struct.unpack_from('>I',loaded,row['offset'])[0],row['after'])
        capacity=self.r['owners'][0]['capacity']
        self.assertEqual((capacity['count'],capacity['actor_growth_bytes'],capacity['stack_bytes']),(71,88,184))
        self.assertEqual(capacity['draw_positions_offset']+257*68+0x174,capacity['item_table_offset'])
        self.assertEqual(capacity['item_table_offset']+0x44,capacity['actor_bytes'])
        self.assertEqual(40+2*capacity['start_indices'],capacity['stack_bytes']-4)
        with self.assertRaises(ValueError):runtime.police_capacity(72)

    def test_current_patch_startup_retained_equipment_and_unrelated_resources(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        changed={BLOB,MODULE,CODE_VROM,0x19D40}|{s[k] for s in runtime.OWNERS for k in ('vrom','reloc')}
        self.assertEqual(self.before.keys(),self.files.keys())
        for v,file in self.before.items():
            self.assertEqual(file.index,self.files[v].index)
            if v not in changed:self.assertEqual(file.extract(self.base),self.files[v].extract(self.rom),hex(v))
        previous=self.prior['equipment_resources'];old_blob=self.before[BLOB].extract(self.base)
        self.assertEqual(self.module[:runtime.CODE],old_blob[previous['blob_offset']:previous['blob_offset']+runtime.CODE])
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.module[-16:],bytes.fromhex('AF48C0DE')*4)
        self.assertEqual(self.blob[0x20:0xE0],old_blob[0x20:0xE0])
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0xA000u',self.report['startup']['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],CONFIG-STARTUP)
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_profile_changed'])


if __name__=='__main__':unittest.main()
