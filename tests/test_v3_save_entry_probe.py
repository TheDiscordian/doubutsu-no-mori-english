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


if __name__ == '__main__':
    unittest.main()
