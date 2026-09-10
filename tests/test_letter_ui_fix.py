"""Letter UI guards, native relocations, exact installed names, and retained saves."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_VROM, CODE_RAM
from letter_ui_fix import PARTS, BASE_SHA, source_hashes, POOL_AT, POOL_BEFORE, POOL_EXTRA
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from title_start_fix import reconstruct

OUT = ROOT/'build/v1-letter-ui-fix-02'


class LetterUiHostTests(unittest.TestCase):
    def test_limberg_fallback_correct_names_prompts_stock_defaults_and_custom_text(self):
        with tempfile.TemporaryDirectory(prefix='af-letter-ui-') as temp:
            exe = Path(temp)/'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'overlays/letter_ui/address.c'), str(ROOT/'overlays/letter_ui/board.c'),
                str(ROOT/'tests/letter_ui_check.c'), '-o', str(exe)],
                check=True, capture_output=True, text=True, timeout=30)
            r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
            self.assertEqual(r.returncode, 0, r.stdout+r.stderr)


@unittest.skipUnless((OUT/'fixes.json').is_file(), 'Compiled letter UI candidate required')
class LetterUiArtifactTests(unittest.TestCase):
    def test_complete_rom_relocation_ownership_and_unchanged_readers(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base = (ROOT/'build/v1-inventory-money-fix-01/animal-forest-title-preview.z64').read_bytes()
        image = (OUT/'animal-forest-title-preview.z64').read_bytes()
        report = json.loads((OUT/'fixes.json').read_text())
        self.assertEqual(sha256(base), BASE_SHA); self.assertEqual(sha256(image), report['output_sha256'])
        self.assertEqual(source_hashes(), report['sources'])
        self.assertEqual(apply_ups(native, (OUT/'animal-forest-title-preview.ups').read_bytes()), image)
        self.assertEqual(len(image), len(base))
        old, new = by_vrom(base), by_vrom(image)
        moves = {int(v, 16): int(n, 16) for v, n in report['vrom_moves'].items()}
        self.assertEqual(set(new), {moves.get(v, v) for v in old})
        changed = {v for s in PARTS.values() for v in (s['vrom'], s['reloc'])}|{0x7749C0, CODE_VROM, 0x19D40}
        for v, e in old.items():
            self.assertEqual(e.index, new[moves.get(v, v)].index)
            if v not in changed: self.assertEqual(e.extract(base), new[v].extract(image), hex(v))
        for name, spec in PARTS.items():
            p = report['parts'][name]; data = new[spec['new_vrom']].extract(image)
            rel = new[spec['new_reloc']].extract(image)
            self.assertEqual(sha256(data), p['overlay_sha256']); self.assertEqual(sha256(rel), p['relocation_sha256'])
            prior = old[spec['vrom']].extract(base); prior_rel = old[spec['reloc']].extract(base)
            sections = struct.unpack_from('>5I', prior_rel)
            for address in (0x80200010, 0x80370010):
                before = relocate_verified_data(Image(spec['ram'], p['previous_resident_bytes'], sections), prior, prior_rel, address)
                after = relocate_verified_data(Image(spec['ram'], len(data), struct.unpack_from('>5I', rel)), data, rel, address)
                allowed = set(p['touched_offsets'])
                self.assertFalse(any(a != b and at not in allowed for at, (a, b) in enumerate(zip(before, after))))
                for pc, (symbol, _) in spec['calls'].items():
                    self.assertEqual(struct.unpack_from('>I', after, pc-spec['ram'])[0],
                                     0x0C000000 | ((address+p['symbols'][symbol]) >> 2 & 0x3FFFFFF))
            self.assertEqual(struct.unpack_from('>4I', new[0x7749C0].extract(image), spec['owner_at']),
                             (spec['new_vrom'], spec['new_vrom']+len(data), spec['ram'], spec['ram']+len(data)))
        self.assertLessEqual(report['shared_growth_bytes'], POOL_EXTRA)
        at = POOL_AT-CODE_RAM; prior = old[CODE_VROM].extract(base)
        self.assertEqual(new[CODE_VROM].extract(image), prior[:at]+struct.pack('>I', POOL_BEFORE+POOL_EXTRA)+prior[at+4:])
        names = new[0x2C00000].extract(image)
        matches = [i for i in range(216) if names[32+8*i:40+8*i] == b'Limberg ']
        self.assertEqual(len(matches), 1)

    def test_explicit_moves_reject_unknown_colliding_unaligned_and_boot_targets(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base = (ROOT/'build/v1-inventory-money-fix-01/animal-forest-title-preview.z64').read_bytes()
        v = PARTS['address']['vrom']; data = by_vrom(base)[v].extract(base)
        for moves in ({v: 0x3B60000}, {v: 0x3E60001}, {v: 0x1060}, {0x1060: 0x3E60000}):
            with self.assertRaises(ValueError): reconstruct(native, base, {v: data}, moves=moves)


if __name__ == '__main__': unittest.main()
