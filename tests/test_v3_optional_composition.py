"""Current-cartridge dependency selection, bounded writes, and save profiles."""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, n64_checksum, sha256
import v3_optional_composition as composer
from v3_save_clothing import PROFILE, STATE
from tests.test_v3_save_clothing import reference_pack

MAELLE, PUNCHY, CHERI = (f'GAFE01-r0/villager/{index:04X}' for index in (216,235,232))


class OptionalCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.report = composer.inputs()
        cls.catalog = composer.catalogue(cls.base, cls.report)
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-optional-composition-')
        library = Path(cls.temp.name)/'codec.so'
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
            '-DAF_V3_CLOTHING_PROFILE=1',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(library)],
            check=True, capture_output=True, text=True)
        cls.codec = c.CDLL(str(library))
        cls.codec.af_v3_save_check.argtypes = (c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def select(self, *selected):
        return composer.resolve(self.catalog, list(selected))

    def test_actual_house_and_outfit_dependencies_not_just_names(self):
        self.assertEqual(len(self.catalog),59)
        self.assertEqual(self.select(PUNCHY)['required'],
                         ['GAFE01-r0/item/24BF','GAFE01-r0/item/3350'])
        self.assertEqual(self.select(CHERI)['required'],
                         ['GAFE01-r0/item/3224','GAFE01-r0/item/32B8'])
        self.assertEqual(self.select(MAELLE)['required'],['GAFE01-r0/item/241A'])
        self.assertEqual(self.select('GAFE01-r0/item/24BF')['required'],[])
        profile = bytes.fromhex(self.select(PUNCHY)['profile_hex'])
        self.assertEqual(len(profile),192)
        self.assertTrue(profile[183]&0x80)  # Cherry clothing.
        self.assertTrue(profile[119]&0x80)  # Its placed mannequin.
        self.assertTrue(profile[58]&0x10)   # Speed bag, not unrelated barrels.
        self.assertFalse(profile[49]&2)

    def test_order_duplicates_and_removal_resolve_from_requested_set(self):
        self.assertEqual(self.select(PUNCHY,MAELLE,PUNCHY),self.select(MAELLE,PUNCHY))
        both = self.select(PUNCHY,MAELLE)
        only = self.select(MAELLE)
        self.assertNotIn('GAFE01-r0/item/3350',only['enabled'])
        self.assertIn('GAFE01-r0/item/3350',both['enabled'])
        for key in only['enabled']:
            self.assertEqual(self.catalog[key]['id'],key)
        for bad in ('GAFE01-r0/item/3AFC','GAFE01-r0/item/3352','GAFE01-r0/villager/00EC',
                    'GAFE01-r0/item/1234','GAFE01-r1/villager/00EB'):
            with self.assertRaises(ValueError): self.select(bad)
        with self.assertRaises(ValueError): composer.resolve(self.catalog,'all')

    def test_subset_toggles_actual_native_enable_fields_and_nothing_else(self):
        selection = self.select(MAELLE,PUNCHY)
        result,writes,blob = composer.compose(self.base,self.report,self.catalog,selection)
        self.assertEqual(blob[0x20:0xE0].hex(),selection['profile_hex'])
        for key,row in self.catalog.items():
            at,width = row['enable_offset'],row['enable_bytes']
            self.assertEqual(int.from_bytes(blob[at:at+width],'big'),key in selection['enabled'])
            if row['kind']=='villager':
                self.assertEqual(blob[row['town_flag_offset']],key in selection['enabled'])
            if row['kind']=='clothing':
                self.assertEqual(struct.unpack_from('>I',blob,row['display_enable_offset'])[0],
                                 key in selection['enabled'])
        files = by_vrom(result)
        module = files[composer.MODULE].extract(result)
        self.assertEqual(struct.unpack_from('>4I',module,composer.CONFIG),
                         (composer.BLOB,0xC000,zlib.crc32(blob[:0xC000]),composer.ABI))
        self.assertEqual(struct.unpack_from('>4I', blob, 0xF0),
                         (composer.BLOB + composer.PACKAGE, composer.PACKAGE_SIZE,
                          zlib.crc32(blob[composer.PACKAGE:composer.PACKAGE + composer.PACKAGE_SIZE]),
                          composer.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>2I',result,0x10),n64_checksum(result))
        self.assertEqual(len(result),len(self.base))
        reverse = [{**row,'before':row['after'],'after':row['before']} for row in writes]
        self.assertEqual(composer.apply_writes(result,reverse),self.base)
        base_files = by_vrom(self.base)
        self.assertEqual(files,base_files)  # No directory, allocation, or ID changes.
        # Outside the prefix, only the static profile enable words and the
        # selected catalogue ordering/count fields may change. Assets stay put.
        restored_blob = bytearray(blob)
        original_blob = base_files[composer.BLOB].extract(self.base)
        for row in writes:
            at = row['offset'] - files[composer.BLOB].pstart
            if 0 <= at < len(blob): restored_blob[at:at + len(bytes.fromhex(row['before']))] = bytes.fromhex(row['before'])
        self.assertEqual(restored_blob, original_blob)
        self.assertEqual(composer.compose(self.base,self.report,self.catalog,
                         self.select(PUNCHY,MAELLE))[0],result)

    def test_all_and_empty_reproduce_exact_pinned_cartridges(self):
        full = self.select(*self.catalog)
        result,writes,_ = composer.compose(self.base,self.report,self.catalog,full)
        self.assertEqual(result,self.base)
        self.assertEqual(writes,[])
        self.assertEqual(full['profile_hex'],self.report['save_runtime']['profile_hex'])
        result,writes,blob = composer.compose(self.base,self.report,self.catalog,self.select())
        self.assertEqual(sha256(result),composer.STABLE_SHA)
        self.assertEqual(writes,[])
        self.assertIsNone(blob)

    def test_nonprefix_new_items_and_last_shirt_pack_counts_and_preserve_fixed_ids(self):
        from v3_catalogue import VROM, RAM
        from v3_clothing_catalogue import COUNT
        chosen = ['GAFE01-r0/item/31F8', 'GAFE01-r0/item/322C', 'GAFE01-r0/item/241B']
        selection = self.select(*chosen)
        self.assertEqual(selection['required'], [])
        image, _, blob = composer.compose(self.base, self.report, self.catalog, selection)
        cat = self.report['catalogue']
        data = by_vrom(image)[VROM].extract(image)
        table = cat['code']['symbols']['af_v3_catalogue_order'] - RAM
        self.assertEqual(struct.unpack_from('>4H', data, table + 436 * 4), (2174, 0, 2187, 0))
        total = self.report['catalogue']['total_rows']
        self.assertEqual(data[table + 438 * 4:table + total * 4], bytes((total - 438) * 4))
        for address, opcode in ((0x808A6600, 0x24050000), (0x808A9460, 0x24140000), (0x808AF7A8, 0)):
            self.assertEqual(struct.unpack_from('>I', data, address - RAM)[0], opcode | 438)
        table = cat['code']['symbols']['af_v3_catalogue_clothing_order'] - RAM
        self.assertEqual(data[table + 490:table + 496], struct.pack('>3H', (0x386C - 0x1000) // 4, 0, 0))
        self.assertEqual(struct.unpack_from('>I', data, COUNT - RAM)[0], 246)
        for item in ('31F8', '322C'):
            row = self.catalog['GAFE01-r0/item/' + item]
            self.assertTrue(composer.STATIC_ROWS <= row['enable_offset'] < composer.STATIC_ROWS + composer.STATIC_COUNT * 80)
            self.assertEqual(row['enable_offset'] - composer.PACKAGE,
                             row['enable_ram'] - composer.PACKAGE_RAM)
            self.assertEqual(blob[row['enable_offset']:row['enable_offset'] + 4], b'\0\0\0\1')

    def test_bad_overlapping_and_tampered_writes_fail_without_source_changes(self):
        source = b'12345678'
        row = {'offset':2,'before':b'34'.hex(),'after':b'AB'.hex()}
        self.assertEqual(composer.apply_writes(source,[row]),b'12AB5678')
        for edits in ([row,row],[{**row,'offset':-1}],[{**row,'offset':8}],
                      [{**row,'before':'ffff'}],[{**row,'after':'00'}]):
            with self.assertRaises(ValueError): composer.apply_writes(source,edits)
        self.assertEqual(source,b'12345678')
        tampered = self.select(PUNCHY);tampered['enabled'].remove('GAFE01-r0/item/3350')
        with self.assertRaises(ValueError):
            composer.compose(self.base,self.report,self.catalog,tampered)
        altered = {key: dict(value) for key, value in self.catalog.items()}
        altered['GAFE01-r0/item/31F8']['enable_offset'] += 4
        with self.assertRaisesRegex(ValueError, 'actual installed bindings'):
            composer.compose(self.base, self.report, altered, self.select('GAFE01-r0/item/31F8'))

    def test_actual_codec_equal_superset_and_missing_dependency_profiles(self):
        source = (ROOT/'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        profile = bytes.fromhex(self.select(PUNCHY)['profile_hex'])
        state = profile+bytes(STATE-PROFILE)
        packed = bytes(reference_pack(source,state))
        def buffer(data): return (c.c_ubyte*len(data)).from_buffer_copy(data)
        for wanted,expected in ((profile,1),
                (bytes.fromhex(self.select(PUNCHY,MAELLE)['profile_hex']),1),
                (bytes.fromhex(self.select(MAELLE)['profile_hex']),-7),
                (bytes.fromhex(self.select('GAFE01-r0/item/24BF')['profile_hex']),-7)):
            bank,current,out = buffer(packed),buffer(wanted),buffer(b'\xA5'*STATE)
            self.assertEqual(self.codec.af_v3_save_check(bank,len(packed),current,out),expected)
            self.assertEqual(bytes(bank),packed)
            self.assertEqual(bytes(current),wanted)
            self.assertEqual(bytes(out),wanted+bytes(STATE-PROFILE) if expected==1 else b'\xA5'*STATE)

    def test_individual_garden_subset_last_row_and_profile_requirement(self):
        from v3_catalogue import VROM, RAM
        keys = ['GAFE01-r0/item/3294', 'GAFE01-r0/item/32A4']
        selected = self.select(*keys)
        self.assertEqual(selected['required'], [])
        image, _, blob = composer.compose(self.base, self.report, self.catalog, selected)
        self.assertEqual(image, composer.compose(self.base, self.report, self.catalog, self.select(*reversed(keys)))[0])
        for key, row in self.catalog.items():
            if row['kind'] == 'furniture':
                self.assertEqual(int.from_bytes(blob[row['enable_offset']:row['enable_offset'] + 4], 'big'), key in keys)
        last = self.catalog[keys[-1]]
        self.assertEqual(last['enable_offset'], composer.STATIC_ROWS + (0x32A4 - 0x3000) // 4 * 80 + 4)
        cat = self.report['catalogue']
        data = by_vrom(image)[VROM].extract(image)
        at = cat['code']['symbols']['af_v3_catalogue_order'] - RAM
        self.assertEqual(data[at + 436 * 4:at + 438 * 4], struct.pack('>4H',
            (0x32A4 - 0x1000) // 4, 0, (0x3294 - 0x1000) // 4, 0))
        total = self.report['catalogue']['total_rows']
        self.assertEqual(data[at + 438 * 4:at + total * 4], bytes((total - 438) * 4))
        # Same codec, actual newly assigned profile bits: an older selection
        # must reject the new saved dependencies without touching any buffer.
        source = (ROOT / 'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        profile = bytes.fromhex(selected['profile_hex'])
        packed = bytes(reference_pack(source, profile + bytes(STATE - PROFILE)))
        for wanted, expected in ((profile, 1), (bytes.fromhex(self.select(*self.catalog)['profile_hex']), 1),
                                 (bytes.fromhex(self.select(PUNCHY)['profile_hex']), -7)):
            buffer = lambda b: (c.c_ubyte * len(b)).from_buffer_copy(b)
            bank, current, out = buffer(packed), buffer(wanted), buffer(b'\xA5' * STATE)
            self.assertEqual(self.codec.af_v3_save_check(bank, len(packed), current, out), expected)
            self.assertEqual(bytes(bank), packed)
            self.assertEqual(bytes(current), wanted)
            self.assertEqual(bytes(out), wanted + bytes(STATE - PROFILE) if expected == 1 else b'\xA5' * STATE)

    def test_unselected_furniture_cannot_inflate_group_totals_or_recommendations(self):
        import v3_hra as hra
        chosen = ['GAFE01-r0/item/3294', 'GAFE01-r0/item/32A4']
        selection = self.select(*chosen)
        result, _, _ = composer.compose(self.base, self.report, self.catalog, selection)
        data = by_vrom(result)[hra.NEW_VROM].extract(result)
        old = by_vrom(self.base)[hra.NEW_VROM].extract(self.base)
        table = self.report['hra']['metadata_address'] - hra.RAM
        restored = bytearray(data)
        for row in self.report['hra']['imports']:
            at = table + row['runtime_index'] * 4
            key = 'GAFE01-r0/item/' + row['item_id']
            self.assertEqual(data[at:at + 4], bytes.fromhex(row['metadata'] if key in chosen else 'fc000000'))
            restored[at:at + 4] = old[at:at + 4]
        self.assertEqual(restored, old)
        self.assertEqual(sum(data[table + i * 4] >> 2 == 56 for i in range(2051)), 1)
        self.assertEqual(sum(data[table + i * 4] >> 2 == 58 for i in range(2051)), 0)

    def test_western_event_subset_last_profile_and_safe_saved_dependencies(self):
        import v3_catalogue as cat_tool
        import v3_hra as hra
        chosen = ['GAFE01-r0/item/32BC', 'GAFE01-r0/item/3334']
        selected = self.select(*chosen)
        self.assertEqual(selected['required'], [])
        image, _, blob = composer.compose(self.base, self.report, self.catalog, selected)
        self.assertEqual(image, composer.compose(self.base, self.report, self.catalog,
                         self.select(*reversed(chosen)))[0])
        self.assertEqual(self.catalog[chosen[-1]]['enable_offset'], composer.STATIC_ROWS + (0x3334 - 0x3000) // 4 * 80 + 4)
        for key, row in self.catalog.items():
            if row['kind'] == 'furniture':
                self.assertEqual(int.from_bytes(blob[row['enable_offset']:row['enable_offset'] + 4], 'big'), key in chosen)
        files = by_vrom(image)
        data = files[cat_tool.VROM].extract(image)
        at = self.report['catalogue']['code']['symbols']['af_v3_catalogue_order'] - cat_tool.RAM
        self.assertEqual(struct.unpack_from('>4H', data, at + 436 * 4), (2223, 0, 2253, 0))
        total = self.report['catalogue']['total_rows']
        self.assertEqual(data[at + 438 * 4:at + total * 4], bytes((total - 438) * 4))
        data = files[hra.NEW_VROM].extract(image)
        table = self.report['hra']['metadata_address'] - hra.RAM
        self.assertEqual(sum(data[table + i * 4] >> 2 == 55 for i in range(2051)), 2)
        for row in self.report['western']['imports']:
            at = table + row['runtime_index'] * 4
            self.assertEqual(data[at:at + 4], bytes.fromhex(row['native_hra_hex']
                if row['id'] in chosen else 'fc000000'))
        source = (ROOT / 'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        profile = bytes.fromhex(selected['profile_hex'])
        packed = bytes(reference_pack(source, profile + bytes(STATE - PROFILE)))
        for wanted, expected in ((profile, 1), (bytes.fromhex(self.select(*self.catalog)['profile_hex']), 1),
                                 (bytes.fromhex(self.select(chosen[0])['profile_hex']), -7)):
            buffer = lambda b: (c.c_ubyte * len(b)).from_buffer_copy(b)
            bank, current, out = buffer(packed), buffer(wanted), buffer(b'\xA5' * STATE)
            self.assertEqual(self.codec.af_v3_save_check(bank, len(packed), current, out), expected)
            self.assertEqual(bytes(bank), packed)
            self.assertEqual(bytes(current), wanted)
            self.assertEqual(bytes(out), wanted + bytes(STATE - PROFILE) if expected == 1 else b'\xA5' * STATE)

    def test_camping_subset_keeps_fixed_slots_and_unorderable_donor_preview(self):
        import v3_catalogue as cat_tool
        import v3_hra as hra
        chosen = ['GAFE01-r0/item/3364', 'GAFE01-r0/item/33A8']
        selected = self.select(*chosen)
        self.assertEqual(selected['required'], [])
        image, _, blob = composer.compose(self.base, self.report, self.catalog, selected)
        self.assertEqual(image, composer.compose(self.base, self.report, self.catalog,
                         self.select(*reversed(chosen)))[0])
        for key in chosen:
            row = self.catalog[key]
            item = int(row['item_id'], 16)
            self.assertEqual(row['enable_offset'], composer.STATIC_ROWS + (item - 0x3000) // 4 * 80 + 4)
            self.assertEqual(blob[row['enable_offset']:row['enable_offset'] + 4], b'\0\0\0\1')
        data = by_vrom(image)[cat_tool.VROM].extract(image)
        cat = self.report['catalogue']
        at = cat['code']['symbols']['af_v3_catalogue_order'] - cat_tool.RAM
        self.assertEqual(struct.unpack_from('>4H', data, at + 436 * 4), (2265, 0, 2282, 0))
        self.assertEqual(data[at + 438 * 4:at + cat['total_rows'] * 4], bytes((cat['total_rows'] - 438) * 4))
        rows = [r for r in cat['imports'] if composer.item_key(int(r['item_id'], 16)) in chosen]
        self.assertTrue(all(not r['catalogue_orderable'] for r in rows))
        self.assertEqual(rows[-1]['donor_preview_mode'], 24)
        data = by_vrom(image)[hra.NEW_VROM].extract(image)
        table = self.report['hra']['metadata_address'] - hra.RAM
        for row in self.report['camping']['imports']:
            at = table + row['runtime_index'] * 4
            self.assertEqual(data[at:at + 4], bytes.fromhex(row['native_hra_hex'] if row['id'] in chosen else 'fc000000'))
        source = (ROOT / 'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        profile = bytes.fromhex(selected['profile_hex'])
        packed = bytes(reference_pack(source, profile + bytes(STATE - PROFILE)))
        for wanted, expected in ((profile, 1), (bytes.fromhex(self.select(*self.catalog)['profile_hex']), 1),
                                 (bytes.fromhex(self.select(chosen[0])['profile_hex']), -7)):
            buffer = lambda b: (c.c_ubyte * len(b)).from_buffer_copy(b)
            bank, current, out = buffer(packed), buffer(wanted), buffer(b'\xA5' * STATE)
            self.assertEqual(self.codec.af_v3_save_check(bank, len(packed), current, out), expected)
            self.assertEqual(bytes(bank), packed)
            self.assertEqual(bytes(out), wanted + bytes(STATE - PROFILE) if expected == 1 else b'\xA5' * STATE)

    def test_full_sized_western_subset_retains_two_cell_records_and_preview_mapping(self):
        import v3_catalogue as cat_tool
        import v3_hra as hra
        from v3_import_storage import ITEMS, TABLE_END
        chosen = ['GAFE01-r0/item/32C4', 'GAFE01-r0/item/32D4', 'GAFE01-r0/item/241A']
        selected = self.select(*chosen)
        self.assertEqual(selected['required'], [])
        image, _, blob = composer.compose(self.base, self.report, self.catalog, selected)
        self.assertEqual(image, composer.compose(self.base, self.report, self.catalog,
                         self.select(*reversed(chosen)))[0])
        self.assertEqual(self.catalog['GAFE01-r0/item/32D8']['enable_offset'], composer.STATIC_ROWS + (0x32D8 - 0x3000) // 4 * 80 + 4)
        for key, row in self.catalog.items():
            if row['kind'] == 'furniture':
                self.assertEqual(int.from_bytes(blob[row['enable_offset']:row['enable_offset'] + 4], 'big'), key in chosen)
        original_blob = by_vrom(self.base)[composer.BLOB].extract(self.base)
        self.assertEqual(blob[ITEMS:TABLE_END], original_blob[ITEMS:TABLE_END])
        self.assertEqual([blob[ITEMS + (item - 0x3000) // 4 * 32 + 6] for item in (0x32C4, 0x32D4, 0x32D8)], [1, 1, 1])
        data = by_vrom(image)[cat_tool.VROM].extract(image)
        at = self.report['catalogue']['code']['symbols']['af_v3_catalogue_order'] - cat_tool.RAM
        self.assertEqual(struct.unpack_from('>4H', data, at + 436 * 4), (2229, 0, 2225, 0))
        total = self.report['catalogue']['total_rows']
        self.assertEqual(data[at + 438 * 4:at + total * 4], bytes((total - 438) * 4))
        # New compiled framing stays intact; the selected profile gates it.
        start = self.report['catalogue']['code']['symbols']['af_v3_catalogue_furniture_init'] - cat_tool.RAM
        previous = by_vrom(self.base)[cat_tool.VROM].extract(self.base)
        self.assertEqual(data[start:start + 192], previous[start:start + 192])
        data = by_vrom(image)[hra.NEW_VROM].extract(image)
        table = self.report['hra']['metadata_address'] - hra.RAM
        self.assertEqual(sum(data[table + i * 4] >> 2 == 55 for i in range(2051)), 2)
        source = (ROOT / 'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        profile = bytes.fromhex(selected['profile_hex'])
        packed = bytes(reference_pack(source, profile + bytes(STATE - PROFILE)))
        for wanted, expected in ((profile, 1), (bytes.fromhex(self.select(*self.catalog)['profile_hex']), 1),
                                 (bytes.fromhex(self.select(chosen[0])['profile_hex']), -7)):
            buffer = lambda b: (c.c_ubyte * len(b)).from_buffer_copy(b)
            bank, current, out = buffer(packed), buffer(wanted), buffer(b'\xA5' * STATE)
            self.assertEqual(self.codec.af_v3_save_check(bank, len(packed), current, out), expected)
            self.assertEqual(bytes(bank), packed)
            self.assertEqual(bytes(current), wanted)
            self.assertEqual(bytes(out), wanted + bytes(STATE - PROFILE) if expected == 1 else b'\xA5' * STATE)
