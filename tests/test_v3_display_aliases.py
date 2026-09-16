"""Shared alias records, native wrappers, and current runtime-only installation."""
import copy
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
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_import_storage import ITEMS,PACKAGE,slot
from v3_furniture_install import PACKAGE_SIZE,inputs
import v3_display_aliases as aliases

OUTPUT=ROOT/os.environ.get('V3_DISPLAY_ALIAS_BUILD','build/v3-shared-display-runtime-01')


class HostTests(unittest.TestCase):
    def test_native_shared_readers_with_synthetic_categories(self):
        with tempfile.TemporaryDirectory(prefix='v3-aliases-') as directory:
            binary=Path(directory)/'check'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_display_aliases_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,timeout=20)
            self.assertIn(b'pass',result.stdout)

    def test_index_rejects_ambiguous_recursive_or_excess_records(self):
        row=dict(parent_item_id='2200',display_item_id='318C',runtime_index=1123,native_footprint_item='0000')
        table,metadata=aliases.encode([row])
        self.assertEqual(len(table),240);self.assertEqual(metadata[0x318C],bytes.fromhex('22000000'))
        for rows in ([row,row],[row]*(aliases.CAPACITY+1),
                     [{**row,'parent_item_id':'318F'}],[{**row,'runtime_index':1}],
                     [{**row,'native_footprint_item':'17AD'}],[{**row,'display_item_id':'318D'}],[]):
            with self.assertRaises(ValueError):aliases.encode(rows)


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current shared runtime required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.old_blob=cls.before[BLOB].extract(cls.base)

    def test_records_are_generated_from_current_installed_parents(self):
        r=self.report['display_aliases'];rows=aliases.records(self.prior,self.old_blob)
        self.assertEqual(r['rows'],rows)
        table,metadata=aliases.encode(rows)
        self.assertEqual(self.blob[aliases.OFFSET:aliases.OFFSET+len(table)],table)
        self.assertEqual(r['table_sha256'],sha256(table))
        for item,payload in metadata.items():
            at=ITEMS+slot(item)*32
            self.assertEqual(self.blob[at:at+32],struct.pack('>HH',1024+slot(item),item)+bytes(24)+payload)
        self.assertEqual(len(rows),len(self.report['clothing']['imports']))
        changed=copy.deepcopy(self.prior);changed['clothing']['display']['imports'][0]['pocket_item_id']='341A'
        with self.assertRaises(ValueError):aliases.records(changed,self.old_blob)

    def test_only_the_declared_runtime_and_metadata_change(self):
        blob=bytearray(self.blob);display=self.report['clothing']['display']
        spans=[(4,8),(0xF8,0xFC),(0x6200,0x6208),(0x6270,0x6540),(0x6C00,0x6F00),
               (aliases.OFFSET,aliases.OFFSET+240)]
        for row in display['readers']['item_hooks']+display['readers']['collection_hooks']:
            at=row['entry']-0x80460000
            self.assertEqual(blob[at:at+8].hex(),row['after']);spans.append((at,at+8))
        for row in self.report['display_aliases']['rows']:
            at=ITEMS+slot(int(row['display_item_id'],16))*32;spans.append((at,at+32))
        for lo,hi in spans:blob[lo:hi]=self.old_blob[lo:hi]
        self.assertEqual(blob,self.old_blob)
        core=bytearray(self.files[CODE_VROM].extract(self.rom));old_core=self.before[CODE_VROM].extract(self.base)
        for row in display['conversion']['hooks']:
            at=row['entry']-CODE_RAM
            self.assertEqual(core[at:at+8].hex(),row['after']);core[at:at+8]=old_core[at:at+8]
        self.assertEqual(core,old_core)
        for vrom in self.files.keys()-{BLOB,CODE_VROM,MODULE,0x19D40}:
            self.assertEqual(self.files[vrom].extract(self.rom),self.before[vrom].extract(self.base),f'{vrom:08X}')
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))

    def test_code_bounds_crc_and_reconstruction(self):
        display=self.report['clothing']['display']
        for at,end,code in ((0x6270,0x6380,display['conversion']['code']),
                (0x6380,0x6540,display['roster_code']),(0x6C00,0x6F00,display['readers']['code'])):
            self.assertLessEqual(at+code['bytes'],end)
            self.assertEqual(sha256(self.blob[at:at+code['bytes']]),code['sha256'])
            self.assertFalse(any(self.blob[at+code['bytes']:end]))
        package=self.blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
        self.assertEqual(zlib.crc32(package),struct.unpack_from('>I',self.blob,0xF8)[0])
        module=bytearray(self.files[MODULE].extract(self.rom));before=self.before[MODULE].extract(self.base)
        self.assertEqual(struct.unpack_from('>4I',module,CONFIG),
            (BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),self.report['runtime_abi']))
        self.assertEqual(sha256(module[STARTUP:STARTUP+self.report['startup']['bytes']]),self.report['startup']['sha256'])
        module[STARTUP:CONFIG+16]=before[STARTUP:CONFIG+16];self.assertEqual(module,before)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)

    def test_repeat_install_reuses_the_checked_shared_runtime(self):
        blob=bytearray(self.blob);core=bytearray(self.files[CODE_VROM].extract(self.rom))
        with tempfile.TemporaryDirectory(prefix='v3-alias-repeat-') as directory:
            display,result=aliases.install(self.report,blob,core,Path(directory))
            self.assertFalse(list(Path(directory).iterdir()))
        self.assertEqual(display,self.report['clothing']['display'])
        self.assertEqual(result,self.report['display_aliases']);self.assertEqual(blob,self.blob)
        blob[aliases.OFFSET]^=1
        with self.assertRaises(ValueError):aliases.install(self.report,blob,core,OUTPUT)


if __name__=='__main__':unittest.main()
