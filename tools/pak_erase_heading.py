"""Translate the N64-only Pak note-deletion instruction; retain all Pak actions."""
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
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '5f85299d975858017f6d822664933bc332908cde17adf7ff0f4b175e941b1f13'
OWNER, RELOC, RAM = 0x7A10E0, 0x7A2820, 0x808A4780
OWNER_SHA = 'f9a10c58f1e989df18a9f0b5ab6622792e0f01b50a56336711f54ca5950bf22f'
RELOC_SHA = '1ff54bf2a6f16665ae24a532b3d3e50fbdc1ba3cd568bc230b0c86f09300f02d'
WIDTH_SHA = '74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1'
SECTIONS = (5808, 144, 0, 368, 44)
TEXT = b'Erase a Pak note'
SOURCE = bytes.fromhex('9abda4bb90b7e28f981806c007c2080b1e0c0000')
EDITS = ((0x138C, 0x3C0141C8, 0x3C01429B), (0x1404, 0x24060012, 0x24060010))


def patch_owner(old, reloc, widths):
    if (sha256(old) != OWNER_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS or old[0x171C:0x1730] != SOURCE
            or old[0x1730:0x1738] != bytes.fromhex('00b1a00000b29fa0')):
        raise ValueError('Changed native Pak heading, owner, relocation, or asset binding')
    if sha256(widths) != WIDTH_SHA or len(TEXT) != 16 or sum(12-widths[c] for c in TEXT) != 96:
        raise ValueError('Changed complete Pak heading wording or proportional metrics')
    for at, expected in ((0x1378, 0x3C013F60), (0x13CC, 0x3C05808A),
                         (0x13FC, 0x24A55E9C), (0x1418, 0x0C0243A6)):
        if struct.unpack_from('>I', old, at)[0] != expected:
            raise ValueError('Changed actual Pak instruction reader or scale')
    if not {0x450013CC, 0x460013FC} <= set(struct.unpack_from('>44I', reloc, 20)):
        raise ValueError('Missing original Pak heading pointer relocation')
    changed = bytearray(old)
    changed[0x171C:0x1730] = TEXT+bytes(20-len(TEXT))
    allowed = set(range(0x171C, 0x1730))
    for at, before, after in EDITS:
        if struct.unpack_from('>I', old, at)[0] != before:
            raise ValueError('Changed native heading count or X origin')
        struct.pack_into('>I', changed, at, after)
        allowed.update(range(at, at+4))
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        spec = Image(RAM, len(old)+SECTIONS[3], SECTIONS)
        before = relocate_verified_data(spec, old, reloc, address)
        after = relocate_verified_data(spec, bytes(changed), reloc, address)
        if any(a != b and at not in allowed for at, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Pak heading alters unrelated relocated code, data, or BSS')
        hi = struct.unpack_from('>I', after, 0x13CC)[0] & 65535
        lo = struct.unpack_from('>h', after, 0x13FE)[0]
        if hi*65536+lo != address+0x171C or after[0x171C:0x172C] != TEXT:
            raise ValueError('Relocated heading loses the complete English instruction')
    return bytes(changed)


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Pak heading requires the exact complete tune-confirmation baseline')
    files = by_vrom(base)
    code = files[CODE_VROM].extract(base)
    if code[WIDTH_BRANCH:WIDTH_BRANCH+4] != bytes(4):
        raise ValueError('Missing proportional font reader')
    changed = patch_owner(files[OWNER].extract(base), files[RELOC].extract(base),
                          code[WIDTH_TABLE:WIDTH_TABLE+256])
    image = reconstruct(native, base, {OWNER: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Pak heading patch reconstruction differs')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'owner_sha256': sha256(changed),
        'source_builder_sha256': sha256(Path(__file__).read_bytes()),
        'text': TEXT.decode(), 'translation_source': 'Project N64-specific translation; no GC screen counterpart',
        'text_width': 96, 'display_width': 84, 'x': 117.5, 'centre_x': 159.5,
        'allocation_changed': False, 'relocation_changed': False, 'pak_operations_changed': False,
        'saved_format_changed': False, 'save_readers_writers_changed': False,
        'required_ram_bytes': 0x800000, 'prior_rc5_and_tune_corrections_retained': True,
        'ordinary_screen_verified': False, 'original_hardware_verified': False,
        'status': 'English Pak instruction installed; ordinary appearance pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/tune-confirmation-01/animal-forest-tune-confirmation.z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = checked_output(args.output)
    state = source_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), args.base.read_bytes())
    if state['worktree_modified'] != source_state()['worktree_modified']:
        raise ValueError('Source state changed during Pak heading construction')
    report.update(source_revision=revision, worktree_modified=state['worktree_modified'])
    out.mkdir(parents=True, exist_ok=False)
    for name, content in {'animal-forest-menu-followup.z64': image, 'animal-forest-menu-followup.ups': patch,
                          'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, content)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
