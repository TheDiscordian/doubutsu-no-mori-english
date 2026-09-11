"""Install complete GC town-tune confirmation in the existing native text area."""
import argparse
import json
from pathlib import Path
import struct
import subprocess

from aflib import CODE_VROM, by_vrom, verified_rom, sha256, make_ups, apply_ups
from apply_translation import write_new
from catalogue_names import Image
from font import WIDTH_TABLE, WIDTH_BRANCH
from npc_mail_show import relocate_verified_data
from rebuild_v1 import checked_output, source_state
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4'
OWNER, RELOC, RAM, SHARED = 0x79C020, 0x79D8B0, 0x808988F0, 0xA6B000
OWNER_SHA = '458215a2da1132b4cd30d24d4fdaacc656986f2d730c5825ddb41e13994e0459'
RELOC_SHA = '2dd574142cde5d74fc66a80e4a4c2dd505b9808b76310e3e29dfbf94904c360f'
SHARED_SHA = 'f4ed3a45636109c5834d63d889fabe8b3398bfe58791ee6db2cb9db6e32aa194'
WIDTH_SHA = '74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1'
SECTIONS = (5712, 544, 32, 48, 97)
SOURCE_TEXT = bytes.fromhex('aebda4153f00000002c300005dccfb5d247d0000')
# Source symbol, donor, old offset/count, new offset, complete text, HI/LO/count/call.
ROWS = (
    ('mMS_str_title', 0x80D98, 0x1844, 5, 0x1844, b'Are you sure?', 0x12CC, 0x12F8, 0x1304, 0x131C),
    ('mMS_str_ok', 0x80DA8, 0x184C, 2, 0x1851, b'Yes', 0x1358, 0x136C, 0x137C, 0x13A4),
    ('mMS_str_cancel', 0x80DAC, 0x1850, 6, 0x1854, b'No', 0x13C0, 0x13EC, 0x140C, 0x1418),
)


def pointer(data, high, low):
    return ((struct.unpack_from('>I', data, high)[0] & 65535) << 16) + struct.unpack_from('>h', data, low+2)[0]


def patch_owner(old, reloc, widths, shared, rel, symbols):
    if (sha256(old) != OWNER_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or old[0x1844:0x1858] != SOURCE_TEXT):
        raise ValueError('Changed native town-tune owner, text, or relocation')
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied town-tune confirmation reference')
    if sha256(widths) != WIDTH_SHA or sha256(shared) != SHARED_SHA:
        raise ValueError('Changed installed font widths or confirmation background')
    # Bind the actual four background quads, not an assumed generic menu width.
    for load, vertices in ((0x46A8, 0x43F0), (0x46F8, 0x4430), (0x4748, 0x4470), (0x4798, 0x44B0)):
        if struct.unpack_from('>II', shared, load) != (0x01004008, 0x0C000000+vertices):
            raise ValueError('Changed confirmation background vertex reader')
    xyz = [struct.unpack_from('>3h', shared, at) for at in range(0x43F0, 0x44F0, 16)]
    sx, sy = struct.unpack_from('>ff', old, 0x1880)
    if ({p[0] for p in xyz} != {-68, 0, 68} or {p[1] for p in xyz} != {-64, 0, 64}
            or {p[2] for p in xyz} != {0} or abs(sx-0.897059) > 0.000001 or abs(sy-0.708333) > 0.000001):
        raise ValueError('Changed native confirmation window bounds')
    entries = set(struct.unpack_from('>97I', reloc, 20))
    data = bytearray(old)
    data[0x1844:0x1858] = bytes(20)
    allowed = set(range(0x1844, 0x1858))
    records = []
    for name, donor, offset, count, target, text, high, low, length, call in ROWS:
        symbol = f'{name} = .data:0x{donor:08X}; // type:object size:0x{len(text):X} '.encode()
        if symbols.count(symbol) != 1 or rel[DATA_BASE+donor:DATA_BASE+donor+len(text)] != text:
            raise ValueError('Missing complete GC tune-confirmation wording')
        if (struct.unpack_from('>I', old, high)[0] != 0x3C05808A
                or struct.unpack_from('>I', old, low)[0] != 0x24A50000 | ((RAM+offset) & 65535)
                or struct.unpack_from('>I', old, length)[0] != 0x24060000 | count
                or struct.unpack_from('>I', old, call)[0] != 0x0C0243A6
                or not {0x45000000 | high, 0x46000000 | low} <= entries
                or not 0x1844 <= target < target+len(text) <= 0x1858):
            raise ValueError('Changed actual tune-confirmation pointer, count, call, or slot')
        width = sum(12-widths[c] for c in text)
        # Relative to the native window centre; opening scales every term equally.
        if not -68*sx+12 <= -32 < -32+width <= 68*sx-12:
            raise ValueError('Complete English tune prompt escapes its native window')
        data[target:target+len(text)] = text
        struct.pack_into('>I', data, low, 0x24A50000 | ((RAM+target) & 65535))
        struct.pack_into('>I', data, length, 0x24060000 | len(text))
        allowed.update(range(low, low+4))
        allowed.update(range(length, length+4))
        records.append({'text': text.decode(), 'offset': target, 'length': len(text), 'width': width,
                        'donor': f'{donor:08X}', 'font_call': f'{RAM+call:08X}'})
    if [row['width'] for row in records] != [78, 18, 12]:
        raise ValueError('Unexpected complete English confirmation widths')
    spec = Image(RAM, len(old)+SECTIONS[3], SECTIONS)
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(spec, old, reloc, address)
        after = relocate_verified_data(spec, bytes(data), reloc, address)
        if any(a != b and at not in allowed for at, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Confirmation changes unrelated relocated code, data, or BSS')
        for _, _, _, _, target, text, high, low, length, call in ROWS:
            if (pointer(after, high, low) != address+target
                    or after[target:target+len(text)] != text
                    or struct.unpack_from('>I', after, length)[0] != 0x24060000 | len(text)
                    or struct.unpack_from('>I', after, call)[0] != 0x0C0243A6):
                raise ValueError('Relocated confirmation does not select its complete English')
    return bytes(data), records


def build(native, base, rel, symbols):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Tune confirmation requires the exact complete RC5 baseline')
    files = by_vrom(base)
    code = files[CODE_VROM].extract(base)
    if code[WIDTH_BRANCH:WIDTH_BRANCH+4] != bytes(4):
        raise ValueError('Missing shared proportional font reader')
    changed, rows = patch_owner(files[OWNER].extract(base), files[RELOC].extract(base),
        code[WIDTH_TABLE:WIDTH_TABLE+256], files[SHARED].extract(base), rel, symbols)
    image = reconstruct(native, base, {OWNER: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Tune confirmation patch reconstruction differs')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'owner_sha256': sha256(changed),
        'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'source_builder_sha256': sha256(Path(__file__).read_bytes()), 'strings': rows,
        'allocation_changed': False, 'relocation_changed': False, 'choice_handlers_changed': False,
        'saved_format_changed': False, 'save_readers_writers_changed': False,
        'melody_and_sound_changed': False, 'screen_geometry_changed': False,
        'required_ram_bytes': 0x800000, 'prior_rc5_corrections_retained': True,
        'ordinary_screen_verified': False, 'original_hardware_verified': False,
        'status': 'Complete tune confirmation installed; ordinary appearance pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc5/Animal Forest English V1RC5.z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = checked_output(args.output)
    state = source_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        args.base.read_bytes(), (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if state['worktree_modified'] != source_state()['worktree_modified']:
        raise ValueError('Source state changed during tune-confirmation construction')
    report.update(source_revision=revision, worktree_modified=state['worktree_modified'])
    out.mkdir(parents=True, exist_ok=False)
    for name, content in {'animal-forest-tune-confirmation.z64': image, 'animal-forest-tune-confirmation.ups': patch,
                          'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, content)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
