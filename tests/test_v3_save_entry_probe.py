"""Current distinct-consumer proof coverage; no historical emulator replay."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, yaz0_decode
from v3_save_runtime_smoke import (SAVE_RAM, SAVE_BYTES, decode_current_bank,
                                  diagnostic_arena_checks, entry_proofs, readback_entries)


class SaveEntryProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = Path(os.environ.get('V3_SAVE_ENTRY_BUILD',
            str(ROOT/'build/v3-import-pipeline-profile-17')))
        cls.rom = (directory/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((directory/'build.json').read_bytes())

    def test_all_three_complete_current_consumers_and_real_bank_bindings(self):
        proofs = entry_proofs(self.rom, self.report)
        self.assertEqual(set(proofs), {'af_v3_diary_preflight', 'af_v3_save_sync', 'af_cw_save_sync'})
        self.assertEqual([len(body) for _, body in proofs.values()], [220, 440, 432])
        for receipt in self.report['equipment_resources']['private_save_bank']['consumers']:
            self.assertEqual(sha256(proofs[receipt['name']][1]), receipt['after_sha256'])

    def test_altered_body_rejects_even_with_resealed_metadata(self):
        report = copy.deepcopy(self.report)
        owner = report['equipment_resources']['diaries']['packets']['storage']
        receipt = report['equipment_resources']['private_save_bank']['consumers'][0]
        rom = bytearray(self.rom)
        at = owner['physical']+receipt['first']-owner['ram']
        rom[at+4] ^= 1
        owner['sha256'] = sha256(rom[owner['physical']:owner['physical']+owner['bytes']])
        receipt['after_sha256'] = sha256(rom[at:at+receipt['last']-receipt['first']])
        with self.assertRaisesRegex(ValueError, 'retained save-entry instructions'):
            entry_proofs(rom, report)

    def test_altered_bank_target_and_delay_slot_reject(self):
        for kind in ('target', 'delay'):
            with self.subTest(kind=kind):
                report = copy.deepcopy(self.report)
                owner = report['equipment_resources']['diaries']['packets']['storage']
                receipt = report['equipment_resources']['private_save_bank']['consumers'][0]
                patch = receipt['patches'][0]
                rom = bytearray(self.rom)
                start = owner['physical']+receipt['first']-owner['ram']
                at = owner['physical']+patch['address']-owner['ram']
                if kind == 'target':
                    patch['after'] ^= 1
                    struct.pack_into('>I', rom, at, patch['after'])
                else:
                    rom[at+7] ^= 1
                owner['sha256'] = sha256(rom[owner['physical']:owner['physical']+owner['bytes']])
                receipt['after_sha256'] = sha256(rom[start:start+receipt['last']-receipt['first']])
                with self.assertRaisesRegex(ValueError, 'bank binding or delay slot'):
                    entry_proofs(rom, report)

    def test_full_diagnostic_buffer_admits_only_the_installed_native_play_block(self):
        self.assertEqual(diagnostic_arena_checks(self.report, 0x80200000, 0x4100), ())
        guards = diagnostic_arena_checks(self.report, 0x804227C0, 0x4100)
        self.assertEqual([at for at, _ in guards],
                         [0x80102200, 0x804F4900, 0x80400000, 0x8044FFF0, 0x80400010])
        for at in (0, 0x80400020, 0x8044C000, 0x80460000, 0x80682000, 0x804227C4):
            with self.subTest(at=hex(at)), self.assertRaises(ValueError):
                diagnostic_arena_checks(self.report, at, 0x4100)
        bad = copy.deepcopy(self.report)
        bad['equipment_resources']['scene_arena']['native_main_heap_end'] = 0x80800000
        with self.assertRaises(ValueError):
            diagnostic_arena_checks(bad, 0x804227C0, 0x4100)

    def bank_fixture(self):
        # Read a retained native chip as data; never execute its historical ROM.
        bank = (ROOT/'build/v3-import-pipeline-ordinary-save-03/test.flash').read_bytes()[:65536]
        ext = bank[SAVE_BYTES:]
        length, total = struct.unpack_from('>I', ext, 16)[0], struct.unpack_from('>I', ext, 12)[0]
        stream = bank[20:0x2F68]+bank[0x2F6A:SAVE_BYTES]
        raw = yaz0_decode(b'Yaz0'+struct.pack('>I', total)+bytes(8)+stream[:length])
        canonical = raw[SAVE_BYTES:65536]
        state = bytearray(1232)
        for source, first, last in ((0x18, 0, 160), (0xC0, 192, 704), (0x2C0, 160, 192),
                (0x2E0, 704, 832), (0x360, 832, 880), (0x390, 880, 1200), (0x4D0, 1200, 1232)):
            state[first:last] = canonical[source:source+last-first]
        return bank, raw, state, struct.unpack_from('>I', ext, 8)[0]

    def test_complete_format21_decoder_checks_all_records_and_state_tail(self):
        bank, raw, state, registry = self.bank_fixture()
        console, extra = raw[65536:72064], raw[72064:]
        self.assertEqual(decode_current_bank(bank, console, extra, state, registry), raw[:65536])
        wrong_state = bytearray(state); wrong_state[-1] ^= 1
        for c, e, s, r in ((console[:-1], extra, state, registry),
                (console, extra[:-1], state, registry), (console, extra, state[:-1], registry),
                (console, extra, wrong_state, registry), (console, extra, state, registry+1)):
            with self.subTest(console=len(c), extra=len(e), state=len(s), registry=r):
                with self.assertRaises(ValueError):
                    decode_current_bank(bank, c, e, s, r)

    def test_complete_format21_decoder_rejects_corrupt_chip_and_reserved_data(self):
        bank, raw, state, registry = self.bank_fixture()
        for at in (18, 0x200, SAVE_BYTES+24, SAVE_BYTES+40):
            bad = bytearray(bank); bad[at] ^= 1
            with self.subTest(at=hex(at)), self.assertRaises(ValueError):
                decode_current_bank(bad, raw[65536:72064], raw[72064:], state, registry)

    def readback_fixture(self):
        from unittest.mock import Mock
        export = ROOT/'build/v3-import-pipeline-save-entries-05/native-entry-export'
        bank = (export/'af_cw_save_sync.flash').read_bytes()[:65536]
        ext = bank[SAVE_BYTES:]
        length, total = struct.unpack_from('>I', ext, 16)[0], struct.unpack_from('>I', ext, 12)[0]
        raw = yaz0_decode(b'Yaz0'+struct.pack('>I', total)+bytes(8)+
                         (bank[20:0x2F68]+bank[0x2F6A:SAVE_BYTES])[:length])
        canonical = raw[SAVE_BYTES:65536]
        state = bytearray(1232)
        for source, first, last in ((0x18, 0, 160), (0xC0, 192, 704), (0x2C0, 160, 192),
                (0x2E0, 704, 832), (0x360, 832, 880), (0x390, 880, 1200), (0x4D0, 1200, 1232)):
            state[first:last] = canonical[source:source+last-first]
        e = self.report['equipment_resources']; r = self.report['save_runtime']
        storage = e['console_storage']; code = self.report['save_codec']['active_storage_code']['symbols']
        memory = {SAVE_RAM: raw[:SAVE_BYTES],
            r['state_ram']: struct.pack('>4I', 0xAF535633, 0, 1, int.from_bytes(bank[8:10], 'big')),
            r['state_ram']+16: bytes(state),
            r['state_ram']+r['state_bytes']-16: bytes.fromhex('AF53C0DE')*4,
            storage['state']['ram']+16: raw[65536:72064], 0x8003CE34: bytes(4),
            e['private_save_bank']['workspace']['ram']:
                struct.pack('>4I', 0x41465042, 0, 0xAF53B0DE, 0xAF53B0DE)}
        offset = 72064
        for at, n in ((storage['diary_state']['ram'], 48048), (code['af_v3_fishing_state'], 176),
                (code['af_v3_card_state'], 64), (e['bank']['memory']['account']['ram'], 48)):
            memory[at] = raw[offset:offset+n]; offset += n
        debug = Mock()
        def read(at, n):
            if len(memory[at]) != n:
                raise AssertionError(f'Expected the complete {len(memory[at])}-byte record, not {n}')
            return memory[at]
        debug.read_memory.side_effect = read
        return debug, memory, export, ROOT/'build/v3-import-pipeline-profile-17/animal-forest-v3-asset-loader.z64'

    def test_fresh_readback_checks_complete_current_records_without_native_calls(self):
        debug, memory, export, rom = self.readback_fixture()
        result = readback_entries(debug, rom, export, lambda value: None)
        self.assertTrue(result['native_save_entry_fresh_readback'])
        self.assertFalse(result['emulator_checkpoint_used'])
        self.assertEqual(result['complete_extended_bytes'], 48336)
        debug.call.assert_not_called()
        debug.write_memory.assert_not_called()

    def test_fresh_readback_rejects_changed_town_tail_and_native_fault(self):
        for at in (SAVE_RAM, 0x8003CE34):
            debug, memory, export, rom = self.readback_fixture()
            bad = bytearray(memory[at]); bad[-1] ^= 1; memory[at] = bytes(bad)
            with self.subTest(address=hex(at)), self.assertRaises(ValueError):
                readback_entries(debug, rom, export, lambda value: None)

    def test_native_readback_validates_consumed_complete_bank_and_preserves_import_records(self):
        debug, memory, export, rom = self.readback_fixture()
        bank = (ROOT/'build/v3-import-pipeline-save-entries-readback-04/test.flash').read_bytes()[:65536]
        ext = bank[SAVE_BYTES:]
        length, total = struct.unpack_from('>I', ext, 16)[0], struct.unpack_from('>I', ext, 12)[0]
        raw = yaz0_decode(b'Yaz0'+struct.pack('>I', total)+bytes(8)+
                         (bank[20:0x2F68]+bank[0x2F6A:SAVE_BYTES])[:length])
        memory[SAVE_RAM] = raw[:SAVE_BYTES]
        memory[self.report['equipment_resources']['private_save_bank']['workspace']['bank_ram']] = bank
        debug.call.return_value = dict(return_value=1)
        result = readback_entries(debug, rom, export, lambda value: None, native_reload=True)
        self.assertTrue(result['complete_native_loader_called'])
        self.assertFalse(result['checkpoint_seed_used'])
        debug.call.assert_called_once()
        debug.write_memory.assert_not_called()
        debug.call.return_value = dict(return_value=0)
        with self.assertRaisesRegex(ValueError, 'complete-bank loader failed'):
            readback_entries(debug, rom, export, lambda value: None, native_reload=True)


class ConnectedSaveEvidenceTests(unittest.TestCase):
    """Check actual connected exports and their matching fresh-process loads."""
    @classmethod
    def setUpClass(cls):
        if not all(os.environ.get(k) for k in
                   ('V3_CONNECTED_SAVE_WRITER', 'V3_CONNECTED_SAVE_READER')):
            raise unittest.SkipTest('Explicit connected writer and fresh reader required')
        cls.writer = ROOT/os.environ['V3_CONNECTED_SAVE_WRITER']
        cls.reader = ROOT/os.environ['V3_CONNECTED_SAVE_READER']
        cls.export = cls.writer/'native-entry-export'
        cls.written = json.loads((cls.writer/'results.json').read_bytes())
        cls.loaded = json.loads((cls.reader/'results.json').read_bytes())
        cls.receipt = json.loads((cls.export/'manifest.json').read_bytes())

    def decoded(self, path):
        bank = path.read_bytes()[:65536]
        n, total = (int.from_bytes(bank[SAVE_BYTES+offset:SAVE_BYTES+offset+4], 'big')
                    for offset in (16, 12))
        raw = yaz0_decode(b'Yaz0'+struct.pack('>I', total)+bytes(8)+
                         (bank[20:0x2F68]+bank[0x2F6A:SAVE_BYTES])[:n])
        state = bytearray(1232)
        canonical = raw[SAVE_BYTES:65536]
        for source, first, last in ((0x18, 0, 160), (0xC0, 192, 704), (0x2C0, 160, 192),
                (0x2E0, 704, 832), (0x360, 832, 880), (0x390, 880, 1200), (0x4D0, 1200, 1232)):
            state[first:last] = canonical[source:source+last-first]
        self.assertEqual(decode_current_bank(bank, raw[65536:72064], raw[72064:], state,
            int.from_bytes(bank[SAVE_BYTES+8:SAVE_BYTES+12], 'big')), raw[:65536])
        return raw

    def test_actual_both_writers_and_fresh_process_preserve_complete_imports(self):
        self.assertTrue(self.written[-1]['graceful_shutdown'])
        self.assertTrue(self.loaded[-1]['graceful_shutdown'])
        self.assertTrue(self.receipt['native_distinct_save_entries'])
        self.assertEqual([r['consumer'] for r in self.receipt['complete_single_bank_writers']],
                         ['af_v3_save_sync', 'af_cw_save_sync'])
        images = []
        for receipt in self.receipt['complete_single_bank_writers']:
            path = self.export/receipt['file']
            chip = path.read_bytes()
            self.assertEqual(len(chip), 131072)
            self.assertEqual(sha256(chip), receipt['sha256'])
            self.assertEqual(chip[65536:], b'\xff'*65536)
            raw = self.decoded(path)
            self.assertEqual(raw[:65536],
                (self.export/(receipt['consumer']+'-canonical.bin')).read_bytes())
            self.assertEqual(raw[72064:], (self.export/'initial-extended.bin').read_bytes())
            images.append(raw)
        self.assertEqual(images[0], images[1])
        fresh = next(r for r in self.loaded if r.get('native_save_entry_fresh_readback'))
        self.assertEqual(fresh['rom_sha256'], self.written[0]['rom_sha256'])
        self.assertEqual(fresh['written_chip_sha256'], self.receipt['complete_single_bank_writers'][-1]['sha256'])
        self.assertTrue(fresh['ordinary_controller_load'])
        self.assertTrue(fresh['complete_native_loader_called'])
        self.assertFalse(fresh['checkpoint_seed_used'])
        self.assertEqual((fresh['complete_console_bytes'], fresh['complete_extended_bytes']), (6528, 48336))
        self.assertTrue(any(r.get('original_exported_import_records_preserved') for r in self.loaded))
        seed = json.loads((self.reader/'run.json').read_bytes())['seed_files']
        self.assertEqual(next(r['sha256'] for r in seed if r['file']=='test.flash'), fresh['written_chip_sha256'])
        self.assertFalse(any(r['file'].endswith('.bs1') for r in seed))

    def test_original_reward_letters_or_visitor_console_rows_survive_restart(self):
        from mail_record import unpack
        raw = self.decoded(self.export/'af_cw_save_sync.flash')
        restarted = self.decoded(self.reader/'test.flash')
        self.assertEqual(raw[65536:], restarted[65536:])
        rewards = [r for r in self.written if r.get('hra_reward_for_save')]
        if rewards:
            self.assertEqual(len(rewards), 2)
            self.assertEqual([(r['hra_reward_for_save']['item'], r['hra_reward_for_save']['template'])
                              for r in rewards], [(0x3024, 0x221), (0x3028, 0x222)])
            for delivery in rewards:
                gift, home, slot = delivery['hra_reward_for_save'], delivery['home'], delivery['slot']
                first = 0x3A00+home*0xB48+slot*164
                mail = raw[first:first+164]
                self.assertEqual(restarted[first:first+164], mail)
                self.assertEqual(mail[:16], raw[0x3588+home*0xB48:0x3598+home*0xB48])
                self.assertEqual(int.from_bytes(mail[36:38], 'big'), gift['item'])
                snapshot = unpack(mail[42:], expected_catalog=4)
                self.assertEqual(snapshot.templates, (gift['template'],))
                self.assertEqual(snapshot.fields[0][1].text, f'{gift["points"]:,}'.rjust(10).encode())
                flag = 0x35A4+home*0xB48
                self.assertEqual(raw[flag] & gift['flag'], gift['flag'])
                self.assertEqual(restarted[flag], raw[flag])
        else:
            initial = self.decoded(self.export/'initial.flash')
            self.assertNotEqual(raw[65536:65536+0x660], initial[65536:65536+0x660])
            self.assertEqual(raw[65536+0x660:72064], initial[65536+0x660:72064])
            returned = [r for r in self.written if r.get('console_native_world_return')=='passed']
            self.assertEqual(len(returned), 2)
            for result in returned:
                self.assertEqual((result['actor'], result['source_save_player']), (4, 0))
                self.assertTrue(result['nes_save_rows_retained'])
            self.assertTrue(any(r.get('native_host_acquaintance_renewal') for r in self.written))


if __name__ == '__main__':
    unittest.main()
