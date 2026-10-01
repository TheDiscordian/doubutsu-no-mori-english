"""Complete console payload/save conversion and guarded category discovery."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, yaz0_decode
from gamecube import rarc_files
import v3_console_games as games
from v3_furniture_pipeline import Source


def tags(*rows):
    return b''.join(name.encode()+bytes([len(data)])+data for name, data in
        [('GID', b'TS'), ('GNM', b'Test'), ('GNO', b'\x00'), *rows, ('END', b'')])


class FormatTests(unittest.TestCase):
    def test_complete_images_and_unknown_or_incomplete_formats(self):
        image = b'NES\x1a'+bytes([1, 1, 0, 0])+bytes(8)+bytes(24576)
        self.assertEqual(games.image_info(image)['mapper'], 0)
        for bad in (image[:-1], image+b'\0', image[:7]+b'\x08'+image[8:],
                    image[:8]+b'\x01'+image[9:], b'NES\x1a', bytes(65536)):
            with self.subTest(header=bad[:16]), self.assertRaises(ValueError):
                games.image_info(bad)
        trained = image[:6]+b'\x04'+image[7:]+bytes(512)
        self.assertEqual(games.image_info(trained)['trainer_bytes'], 512)

    def test_save_operations_keep_offsets_defaults_flags_and_source_order(self):
        raw = tags(('OFS', b'\x00\x10'), ('HSC', b'\x87\x00\x01\x02'),
                   ('OFS', b'\x00\x20'), ('BBR', b'\x00\x02\x00\x03'), ('SPE', b'\x01'))
        row, converted = games.save_recipe(raw, bytes(65536))
        self.assertEqual(converted, raw)
        self.assertEqual(row['payload_extent'], 35)
        self.assertEqual(row['operations'][0], dict(kind='HSC', source_offset=0x8700,
            save_offset=16, bytes=2, default_hex='0102'))
        self.assertEqual([op['kind'] for op in row['operations']], ['HSC', 'BBR', 'SPE'])
        for bad in (raw[:-1], raw+b'\0', tags(('XYZ', b'')),
                    tags(('HSC', b'\x00\x00\x01')),
                    tags(('OFS', b'\x00\x00'), ('HSC', b'\x07\xFF\x00\x00')),
                    tags(('OFS', b'\x00\x00'), ('BBR', b'\x1F\xFF\x00\x02')),
                    tags(('OFS', b'\x00\x00'), ('QDS', b'\x00\xFF\xFF\x00\x02')),
                    tags(('OFS', b'\x00\x00'), ('SPE', b'\x02'))):
            with self.subTest(tags=bad.hex()), self.assertRaises(ValueError):
                games.save_recipe(bad, bytes(65536))


class DonorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.dol, cls.archive = games.read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.report, cls.blob = games.build_bundle(cls.dol, cls.archive)

    def test_original_visitor_console_owner_and_room_save_rules(self):
        # Check complete compiled functions, not just the station wrappers:
        # the room itself loads/saves the current town's NES file for visitors.
        for address, size, digest in (
            (0x80043C54,0xD7C,'5efa64d552e7ac9c7b972643c8b3d9a899d27e87e8420659f8cf47907c7fa97b'),
            (0x80041F04,0x278,'fa91713f7e9617c3bfc90fb21b7305787e46c154d3313b5806d2afd82ea2ba01'),
            (0x8004618C,0x144,'22e542ff8c20e981881b79f38789b6b0bf17294f53aee340858ab55e67b12bc5'),
            (0x800462D0,0x1DC,'124f35e256ee8901ae7d74a1e0b6464015f1d403409f08a159935f5bf676363c'),
            (0x80046670,0xAC,'b335db7ebef62d395abdcda9acd4dfe12c3d3e6a817bbfd9eccfba8ac0ed646f')):
            self.assertEqual(sha256(self.dol.read(address,size)),digest)
        for offset, name, size, digest in (
            (0x90570,'mCD_GetLandSlotNo_code_com',448,'2df361a4caa4756790069a4273dd7636660c8514987fa5a3b01b6f4494d6047a'),
            (0x90730,'mCD_GetThisLandSlotNo_code',128,'8eb2db6019d2079600d095243fc4e4b99dfb730f5cd935a4da490b7db63d5664'),
            (0x104130,'aMR_SetEmulatorStartMessage',504,'2808dc2c2d6affc75f5e07069fecc3fc7a0c41e22244951ea0e06b5bb22f86ec'),
            (0x10675C,'aMR_MsgControlSaveFamicom',600,'ddb77737d7b2077cc039835c4fce696020aa59374791ae27da4c9360018bb9cb'),
            (0x106B28,'aMR_MessageControl',716,'e2b173bc0b532a44611ec217cc0a2d29a6205784e80733ea28a3fee7de44984e')):
            raw, receipt=self.source.function(offset)
            self.assertEqual((receipt['symbol'],len(raw),sha256(raw)),(name,size,digest))
        self.assertEqual(self.source.function(0x104130)[1]['relocations'][56],
                         (10,0,4,0x8004618C))
        self.assertEqual(self.source.function(0x10675C)[1]['relocations'][96],
                         (10,0,4,0x800462D0))

    def test_complete_bundle_retains_every_game_and_each_save_dependency(self):
        r, blob = self.report, self.blob
        self.assertEqual(len(r['rows']), 19)
        self.assertEqual(r['save_payload_bytes'], 1623)
        self.assertEqual(struct.unpack_from('>4s7I', blob),
            (b'AFNE', 1, 19, 64, 1248, 1623, 8, len(blob)))
        originals = [(p, yaz0_decode(d)) for p, d in rarc_files(self.archive) if p.startswith('game/')]
        save_bits, used, op_count = set(), set(), 0
        for row, (path, payload) in zip(r['rows'], originals):
            self.assertEqual(row['path'], path)
            self.assertEqual(blob[row['payload_offset']:row['payload_offset']+row['bytes']], payload)
            self.assertEqual(row['sha256'], sha256(payload))
            entry = struct.unpack_from('>16I', blob, 32+(row['game_index']-1)*64)
            self.assertEqual(entry[:4], (row['game_index'], 2 if row['image']['format']=='QD' else 1,
                                        row['image']['mapper'] if row['image']['mapper'] is not None else 0xFFFFFFFF, 0))
            self.assertEqual(entry[4:6], (row['payload_offset'], row['bytes']))
            original = self.dol.read(row['tags_address'], entry[7])
            self.assertEqual(blob[entry[6]:entry[6]+entry[7]], original)
            recipe, converted = games.save_recipe(original, payload)
            self.assertEqual(blob[entry[8]:entry[8]+entry[9]], converted)
            self.assertEqual(entry[10:14], (row['operations_offset'], len(recipe['operations']),
                                          recipe['game_number'], recipe['payload_extent']))
            self.assertNotIn(recipe['game_number'], save_bits)
            save_bits.add(recipe['game_number'])
            for i, op in enumerate(recipe['operations']):
                code, parameter, n, dest, source, default = struct.unpack_from('>BBHIII', blob, entry[10]+16*i)
                self.assertEqual((code, parameter, n, dest, source),
                    (('HSC', 'BBR', 'QDS', 'SPE').index(op['kind'])+1, op.get('parameter', 0),
                     op['bytes'], op['save_offset'], op['source_offset']))
                if op['default_hex']:
                    self.assertEqual(blob[default:default+n], bytes.fromhex(op['default_hex']))
                else:
                    self.assertEqual(default, 0)
                addresses = set(range(dest, dest+n))
                self.assertFalse(used & addresses)
                used |= addresses
                op_count += 1
        self.assertEqual(op_count, 60)
        self.assertEqual(self.report['rows'][12]['save']['game_number'], 13)
        self.assertEqual(self.report['rows'][13]['save']['game_number'], 12)
        self.assertFalse(r['runtime_installed'])
        self.assertFalse(r['choice_eligible'])

    def test_malformed_source_length_has_one_exact_bounded_correction(self):
        row = self.report['rows'][8]
        original = self.dol.read(row['tags_address'], 27)
        recipe, converted = games.save_recipe(original, b'')
        self.assertEqual(sha256(original), games.BAD_NAME_TAG_SHA)
        self.assertEqual([i for i, (a, b) in enumerate(zip(original, converted)) if a != b], [9])
        self.assertEqual(len(recipe['corrections']), 1)
        self.assertEqual(recipe['game_number'], 8)
        self.assertEqual(recipe['operations'], [])
        with self.assertRaises(ValueError):
            games.save_recipe(original[:4]+b'X'+original[5:], b'')

    def test_shared_launch_bindings_include_missing_payload_and_reject_changed_tables(self):
        for i, item in enumerate(range(0x1DA8, 0x1DF4, 4), 1):
            p = self.source.profile(item)['callback_adapter']
            self.assertEqual(p['console_launch']['game_index'], i)
            self.assertEqual(p['console_launch']['payload_status'], 'present')
            self.assertEqual(p['pending_callbacks'], ['move'])
            self.assertFalse(p['console_launch']['runtime_installed'])
        missing = self.source.profile(0x1FBC)['callback_adapter']['console_launch']
        self.assertEqual(missing['game_index'], 20)
        self.assertEqual(missing['payload_status'], 'absent-from-donor')
        self.assertNotIn('console_launch', self.source.profile(0x3280)['callback_adapter'])
        a = self.source.profile(0x1DC4)['callback_adapter']
        functions = copy.deepcopy(a['functions'])
        functions['move']['relocations'].pop(0x4E)
        with self.assertRaisesRegex(ValueError, 'changed callback dependencies'):
            games.launch_binding(self.source, functions, 0x371)
        for index in (0, 0x369, 0x37E, 1265):
            binding = games.launch_binding(self.source, a['functions'], index)
            self.assertEqual(binding['game_index'], 1)
            self.assertEqual(binding['selection']['selected_index'], 0)

    def test_original_emulator_receipt_does_not_claim_mapper_execution(self):
        receipt = games.native_contract((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        self.assertEqual(receipt['original_game_count'], 7)
        self.assertEqual([r['mapper'] for r in receipt['mapper_rows']], [0, 1, 4, 9])
        self.assertTrue(all(not r['execution_verified'] for r in receipt['mapper_rows']))
        self.assertEqual(len(receipt['pending']), 4)


if __name__ == '__main__':
    unittest.main()
