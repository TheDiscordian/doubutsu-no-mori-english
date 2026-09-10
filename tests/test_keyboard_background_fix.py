"""GC frame extraction, retained keyboard source, complete patch, and relocations."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_VROM, CODE_RAM
from catalogue_names import Image
from keyboard_background_fix import BASE_SHA, DRAW_SHA, SPEC, source_hashes, donor, draw_source, POOL_AT, POOL_BEFORE, POOL_EXTRA
from keyboard_grid_labels import LABELS, encode_label
from npc_mail_show import relocate_verified_data

OUT = ROOT/'build/v1-keyboard-background-fix-01'


class BackgroundSourceTests(unittest.TestCase):
    def test_only_the_panel_and_function_name_change_in_the_retained_grid(self):
        original = (ROOT/'overlays/keyboard_grid/draw.c').read_bytes()
        self.assertEqual(sha256(original), DRAW_SHA)
        start = original.index(b'static Gfx *rectangle('); end = original.index(b'void af_grid_editor_draw(', start)
        expected = original[:start]+original[end:]
        expected = expected.replace(b'void af_grid_editor_draw(', b'void af_bg_editor_draw(', 1)
        expected = expected.replace(b'g=rectangle(g,', b'g=af_bg_panel(g,', 1)
        self.assertEqual(draw_source(), b'#include "/source/overlays/keyboard_background/panel.c"\n'+expected)


@unittest.skipUnless((OUT/'fixes.json').is_file(), 'Compiled background candidate required')
class BackgroundArtifactTests(unittest.TestCase):
    def test_gc_frame_bytes_and_native_control_hint_encodings(self):
        report = json.loads((OUT/'fixes.json').read_text())
        frames, profile = donor((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(report['artwork'], profile); self.assertEqual(report['sources'], source_hashes())
        rom = (OUT/'animal-forest-title-preview.z64').read_bytes()
        data = by_vrom(rom)[SPEC['new_vrom']].extract(rom); compiled = report['editor']
        for name, frame in zip(('af_bg_frame_a','af_bg_frame_b'),frames):
            at = compiled['symbols'][name]
            self.assertEqual(at&7, 0); self.assertEqual(data[at:at+1024], frame)
        suffix = data[compiled['previous_resident_bytes']:]
        # Bind the actual compiled material stores, not just the C macro name.
        stores = bytes.fromhex('3C04FC303484FE61AC4400583C0455FE3484F379AC44005C')
        self.assertEqual(suffix.count(stores), 1)
        def cycles(a,b):
            return ((a>>20&15,b>>28&15,a>>15&31,b>>15&7,a>>12&7,b>>12&7,a>>9&7,b>>9&7),
                    (a>>5&15,b>>24&15,a&31,b>>6&7,b>>21&7,b>>3&7,b>>18&7,b&7))
        gc_first = cycles(0xFC30FFFF,0x5FFEF238)[0]
        self.assertEqual(cycles(0xFC30FE61,0x55FEF379),(gc_first,gc_first))
        for _, label in LABELS:
            self.assertEqual(suffix.count(encode_label(label)+b'\0'), 1)
            self.assertNotIn(label+b'\0', suffix)
        self.assertLessEqual(report['shared_growth_bytes'], POOL_EXTRA)
        self.assertLess((POOL_BEFORE&0xFFFF)+POOL_EXTRA,0x8000)

    def test_complete_cartridge_ups_previous_editor_and_relocated_internal_imports(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base = (ROOT/'build/v1-letter-ui-fix-02/animal-forest-title-preview.z64').read_bytes()
        rom = (OUT/'animal-forest-title-preview.z64').read_bytes(); report = json.loads((OUT/'fixes.json').read_text())
        self.assertEqual(sha256(base), BASE_SHA); self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(len(rom),len(base)); self.assertEqual(apply_ups(native,(OUT/'animal-forest-title-preview.ups').read_bytes()),rom)
        old, new = by_vrom(base), by_vrom(rom)
        moves = {SPEC['vrom']:SPEC['new_vrom'], SPEC['reloc']:SPEC['new_reloc']}
        self.assertEqual(set(new),{moves.get(v,v) for v in old})
        changed = {SPEC['vrom'],SPEC['reloc'],0x7749C0,CODE_VROM,0x19D40}
        for v, entry in old.items():
            self.assertEqual(entry.index,new[moves.get(v,v)].index)
            if v not in changed:self.assertEqual(entry.extract(base),new[v].extract(rom),hex(v))
        data, rel = (new[SPEC[k]].extract(rom) for k in ('new_vrom','new_reloc'))
        prior, prior_rel = (old[SPEC[k]].extract(base) for k in ('vrom','reloc'))
        self.assertEqual(sha256(data),report['editor']['overlay_sha256'])
        self.assertEqual(sha256(rel),report['editor']['relocation_sha256'])
        self.assertEqual(sha256(prior),SPEC['sha']); self.assertEqual(sha256(prior_rel),SPEC['reloc_sha'])
        for address in (0x80200010,0x80370010):
            before = relocate_verified_data(Image(SPEC['ram'],len(prior),struct.unpack_from('>5I',prior_rel)),prior,prior_rel,address)
            after = relocate_verified_data(Image(SPEC['ram'],len(data),struct.unpack_from('>5I',rel)),data,rel,address)
            allowed = set(report['editor']['touched_offsets'])
            self.assertFalse(any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))))
            hook = 0x808882D8-SPEC['ram']; target = address+report['editor']['symbols']['af_bg_editor_draw']
            self.assertEqual(after[hook:hook+4],struct.pack('>I',0x0C000000|(target>>2&0x3FFFFFF)))
        owner = bytearray(old[0x7749C0].extract(base)); struct.pack_into('>4I',owner,SPEC['owner_at'],
            SPEC['new_vrom'],SPEC['new_vrom']+len(data),SPEC['ram'],SPEC['ram']+len(data))
        self.assertEqual(new[0x7749C0].extract(rom),bytes(owner))
        code = bytearray(old[CODE_VROM].extract(base)); struct.pack_into('>I',code,POOL_AT-CODE_RAM,POOL_BEFORE+POOL_EXTRA)
        self.assertEqual(new[CODE_VROM].extract(rom),bytes(code))


if __name__ == '__main__': unittest.main()
