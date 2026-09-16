"""Shared held-resource startup, native readers, and cartridge ownership."""
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
from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,apply_ups,n64_checksum
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs,reuse_resource_tail
import v3_equipment_runtime as runtime

OUTPUT=ROOT/os.environ.get('V3_EQUIPMENT_BUILD','build/v3-equipment-resources-runtime-03')


class HostTests(unittest.TestCase):
    def sanitized(self,source,extra=(),defines=()):
        with tempfile.TemporaryDirectory(prefix='v3-equipment-') as directory:
            out=Path(directory)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',*defines,
                str(ROOT/'tests'/source),*[str(ROOT/p) for p in extra],'-o',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(out)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('pass',result.stdout)

    def test_resource_readers(self):self.sanitized('v3_equipment_resources_test.c')
    def test_current_startup(self):self.sanitized('v3_equipment_startup_test.c',('runtime/crc32.c',))
    def test_shared_package_startup(self):
        self.sanitized('v3_accessory_startup_test.c',('runtime/crc32.c',),('-DAF_V3_ACCESSORY_BYTES=196608',))


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current held-resource cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.equipment=cls.report['equipment_resources']
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old_blob=cls.before[BLOB].extract(cls.base)

    def test_complete_source_resources_and_native_contract(self):
        source=runtime.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        assets,records,evidence=runtime.prepared_resources(source,ROOT/self.equipment['evidence']['art_directory'])
        self.assertEqual(evidence,self.equipment['evidence']);self.assertEqual(len(records),30)
        self.assertEqual(sum(r['kind']=='static-model' for r in records),14)
        for expected,row in zip(records,self.equipment['records']):
            self.assertEqual(expected,{k:v for k,v in row.items() if k not in ('vrom','blob_offset')})
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],assets[row['source_index']])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        core=self.before[CODE_VROM].extract(self.base)
        self.assertEqual(runtime.native_contract(original,core),self.equipment['native_contract'])
        damaged=bytearray(core);damaged[0x800B167C-CODE_RAM]^=1
        with self.assertRaises(ValueError):runtime.native_contract(original,damaged)

    def test_only_declared_owners_hooks_and_tail_change(self):
        old,tail=reuse_resource_tail(self.base,self.prior,self.old_blob)
        retained=bytearray(self.blob[:len(old)]);retained[4:8]=old[4:8]
        self.assertEqual(retained,old)
        core=bytearray(self.files[CODE_VROM].extract(self.rom));old_core=self.before[CODE_VROM].extract(self.base)
        for hook in self.equipment['hooks']:
            at=hook['entry']-CODE_RAM;self.assertEqual(core[at:at+8].hex(),hook['after'])
            self.assertEqual(old_core[at:at+8].hex(),hook['before']);core[at:at+8]=old_core[at:at+8]
        self.assertEqual(core,old_core)
        for vrom in self.files.keys()-{BLOB,CODE_VROM,MODULE,0x19D40}:
            self.assertEqual(self.files[vrom].extract(self.rom),self.before[vrom].extract(self.base),f'{vrom:08X}')
        expected=bytearray(self.base[DMA_START:DMA_END])
        struct.pack_into('>I',expected,self.before[BLOB].index*16+4,BLOB+len(self.blob))
        for row in self.report['automatic_furniture']['resource_moves']:
            struct.pack_into('>4I',expected,self.before[row['vrom']].index*16,
                row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
        self.assertEqual(self.rom[DMA_START:DMA_END],expected)
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui','display_aliases'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        # A subsequent category installation may reuse only the terminal owners,
        # never these newly installed resources or their resident module.
        stripped,reused=reuse_resource_tail(self.rom,self.report,self.blob)
        self.assertGreaterEqual(len(stripped),self.equipment['blob_offset']+runtime.SIZE)
        self.assertEqual(len(reused['retired_resources']),len(tail['retired_resources']))

    def test_module_layout_startup_crc_and_patch(self):
        r=self.equipment;module=self.blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        self.assertEqual(sha256(module),r['sha256']);self.assertEqual(zlib.crc32(module),r['crc32'])
        self.assertLessEqual(r['code']['bytes'],runtime.TABLE)
        self.assertEqual(sha256(module[:r['code']['bytes']]),r['code']['sha256'])
        self.assertEqual(struct.unpack_from('>4I',module,runtime.TABLE),(runtime.MAGIC,1,50,16))
        self.assertEqual(struct.unpack_from('>4I',module,runtime.SIZE-16),(runtime.GUARD,)*4)
        rows={r['source_index']:r for r in r['records']}
        for index in range(50):
            row=rows.get(index);want=(row['vrom'],row['bytes'],row['pointer'],row['type']) if row else (0,)*4
            self.assertEqual(struct.unpack_from('>4I',module,runtime.TABLE+16+index*16),want)
        resident=bytearray(self.files[MODULE].extract(self.rom));before=self.before[MODULE].extract(self.base)
        startup=self.report['startup'];self.assertLessEqual(startup['bytes'],CONFIG-STARTUP)
        self.assertEqual(sha256(resident[STARTUP:STARTUP+startup['bytes']]),startup['sha256'])
        self.assertEqual(struct.unpack_from('>4I',resident,CONFIG),
            (BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),self.report['runtime_abi']))
        resident[STARTUP:CONFIG+16]=before[STARTUP:CONFIG+16];self.assertEqual(resident,before)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
