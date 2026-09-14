"""Actual boxing metadata, complete native loop growth, and current cartridge."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, u32
from v3_asset_loader import BLOB, compose
import v3_hra as hra
import v3_hra_series as series

OUTPUT = ROOT/os.environ.get('AF_V3_TEST_OUTPUT', 'build/v3-speed-bag-hra-01')


class SeriesSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_verified_boxing_and_preserved_native_definitions(self):
        resources = series.prepare(self.base, self.rel, self.symbols)
        old, _ = hra.sources(self.base)
        for name, address, width in (('info', series.INFO, 3), ('names', series.NAMES, 10)):
            result = resources['af_v3_hra_series_'+name]
            self.assertEqual(len(result), series.COUNT*width)
            self.assertEqual(result[:55*width], old[address-hra.RAM:address-hra.RAM+55*width])
        self.assertEqual(resources['af_v3_hra_series_info'][55*3:], bytes.fromhex('FF00FF')*3+bytes.fromhex('0200FF'))
        self.assertEqual(resources['af_v3_hra_series_names'][58*10:], b'boxing    ')
        self.assertEqual(resources['af_v3_hra_series_search'], bytes(59*4))
        self.assertEqual((series.COUNT-3) % 4, 0)
        self.assertEqual((series.COUNT-1) % 2, 0)
        damaged = bytearray(self.rel); damaged[-1] ^= 1
        with self.assertRaises(ValueError): series.prepare(self.base, damaged, self.symbols)

    def test_boxing_metadata_is_not_substituted_or_added_to_other_profiles(self):
        original, _ = hra.table(self.base, self.rel, self.symbols, [])
        selected, rows = hra.table(self.base, self.rel, self.symbols, [], speed_bag=True)
        self.assertEqual(original[1236*4:1237*4], bytes.fromhex('FC000000'))
        self.assertEqual(selected[1236*4:1237*4], bytes.fromhex('E8050000'))
        self.assertEqual(selected[:1236*4]+selected[1237*4:], original[:1236*4]+original[1237*4:])
        self.assertEqual((rows[0]['series'], rows[0]['birth_category']), (58, 0))
        with self.assertRaises(ValueError):
            hra.table(self.base, self.rel, self.symbols, [{'item_id':'3350','runtime_index':1236}])


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current boxing HRA cartridge required')
class SeriesCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files = by_vrom(cls.rom)

    def test_complete_expanded_owner_relocation_and_loop_inventory(self):
        hr = self.report['hra']; sr = hr['series']
        self.assertEqual(sr['count'], 59)
        self.assertEqual({p['low']: p['before'] for p in sr['pointer_changes']}, series.POINTERS)
        self.assertEqual(set(sr['counter_sites']), set(series.COUNTERS))
        old, _ = hra.sources(self.base); wanted = bytearray(old)
        for patch in hr['patches']:
            at = patch['address']-hra.RAM
            self.assertEqual(u32(wanted, at), patch['before'])
            struct.pack_into('>I', wanted, at, patch['after'])
        actual = self.files[hra.NEW_VROM].extract(self.rom)
        self.assertEqual(actual[:hra.SIZE], wanted)
        self.assertEqual(actual[hra.SIZE:hra.START], bytes(hra.START-hra.SIZE))
        self.assertEqual(actual[hra.START:], (OUTPUT/'hra/code.bin').read_bytes())
        self.assertLessEqual(len(actual), 0x8000)
        for address, before in series.COUNTERS.items():
            self.assertEqual(u32(actual, address-hra.RAM), before & 0xFFFF0000 | (58 if address==0x80927800 else 59))
        metadata = actual[hr['metadata_address']-hra.RAM:hr['metadata_address']-hra.RAM+hr['metadata_rows']*4]
        self.assertEqual(metadata[1236*4:1237*4], bytes.fromhex('E8050000'))
        self.assertEqual(sha256(metadata), hr['metadata_sha256'])
        self.assertEqual(sha256(actual), hr['output_sha256'])

    def test_current_composition_and_disabled_save_profile(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        moved = {int(v,16):int(t,16) for v,t in self.report['relocated_resources'].items()}
        changes = {int(v,16):self.files[moved.get(int(v,16),int(v,16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v,16):self.files[int(v,16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v,16) for v in self.report['resized_resources'])
        self.assertEqual(compose(native,self.base,changes,added,resized=resized,relocated=moved),self.rom)
        self.assertEqual(compose(native,self.base,{},{}),self.base)
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        prefix = self.files[BLOB].extract(self.rom)[:0xC000]
        self.assertEqual(u32(prefix,0x7134),0)
        self.assertFalse(self.report['speed_bag']['enabled'])
        self.assertFalse(self.report['speed_bag']['saved_profile_included'])
        previous = json.loads((ROOT/'build/v3-speed-bag-runtime-03/build.json').read_text())
        self.assertEqual(self.report['save_runtime']['profile_hex'],previous['save_runtime']['profile_hex'])
        # Source-only development must not change the patcher or V2 payload.
        self.assertEqual(sha256(self.base),'8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507')


if __name__ == '__main__':
    unittest.main()
