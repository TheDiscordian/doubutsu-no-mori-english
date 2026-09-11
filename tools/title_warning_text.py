"""Translate native title controller/erase wording without changing title actions."""
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
BASE_SHA = '800c7e9d4e6a4b81db05d0a8258d151417d02c9edc47806cf3429e3d144fab09'
OWNER, RELOC, RAM = 0x3C00000, 0x3C50000, 0x80A9FC70
OWNER_SHA = 'b2ee139e3b57411e3cb6bae925ad2e9303bc205f3e314b5c60b9a547ce2f6e36'
RELOC_SHA = 'f8b4f4361dd9812f0bd7af8d744199f57a7e6fbfc0fb7507f7cfa983c7b042e9'
WIDTH_SHA = '74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1'
SECTIONS = (292320, 0, 0, 0, 174)
START, END, ERASE = 0x80AA2118-RAM, 0x80AA2154-RAM, 0x80AA205E-RAM
SOURCE = bytes.fromhex(
    '9abda4bb90b731e70a0acc12011e0dc381202020'
    '1dc30f0118f4c3eac3c206cc12057b8420202020'
    '9abda4bb90b731c20d11f0070b1207f10a018120')
ERASE_SOURCE = bytes.fromhex('20202020209e90dfdb90a020080c2020202020')
ERASE_TEXT = b'  Erase Save Data  '
# Complete text, source/new offset, HI/LO/count/X/call, original X high-half.
ROWS = (
    (b'Controller 1 is not', START, START, 0x918, 0x94C, 0x954, 0x958, 0x96C, 0x425C),
    (b'connected. Power off,', START+20, START+19, 0x984, 0x9B8, 0x9C0, 0x9C4, 0x9D8, 0x4280),
    (b'then connect it.', START+40, START+40, 0x9F0, 0xA24, 0xA2C, 0xA30, 0xA44, 0x4248),
)
# Instruction columns above are offsets from 80AA0000, not the overlay base.
CODE_BIAS = 0x80AA0000-RAM


def pointer(data, high, low):
    return ((struct.unpack_from('>I', data, high)[0] & 65535) << 16) + struct.unpack_from('>h', data, low+2)[0]


def patch_owner(old, reloc, widths):
    if (sha256(old) != OWNER_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or old[START:END] != SOURCE or old[ERASE:ERASE+19] != ERASE_SOURCE):
        raise ValueError('Changed complete title owner, relocation, or native wording')
    if sha256(widths) != WIDTH_SHA:
        raise ValueError('Changed installed title font advances')
    # Retained ordinary draw branch: check controller one, then call the warning.
    branch = bytes.fromhex('3c0c8013918c7950558000068e0d02ac0c2a823902202025100000138fa40020')
    if old[0x80AA1AF4-RAM:0x80AA1B14-RAM] != branch:
        raise ValueError('Changed native missing-controller route')
    entries = set(struct.unpack_from('>174I', reloc, 20))
    changed = bytearray(old)
    changed[START:END] = b''.join(row[0] for row in ROWS).ljust(60, b'\0')
    changed[ERASE:ERASE+19] = ERASE_TEXT
    if len(changed) != len(old) or len(ERASE_TEXT) != 19:
        raise ValueError('Complete title wording exceeds its original storage')
    allowed = set(range(START, END)) | set(range(ERASE, ERASE+19))
    records = []
    for text, source, target, hi, lo, count, x_at, call, old_x in ROWS:
        hi, lo, count, x_at, call = (at+CODE_BIAS for at in (hi, lo, count, x_at, call))
        expected = ((hi, 0x3C0580AA), (lo, 0x24A50000 | ((RAM+source) & 65535)),
                    (count, 0x24060014), (x_at, 0x3C070000 | old_x), (call, 0x0C024387))
        if (any(struct.unpack_from('>I', old, at)[0] != word for at, word in expected)
                or not {0x45000000 | hi, 0x46000000 | lo} <= entries
                or not START <= target < target+len(text) <= END):
            raise ValueError('Changed actual title warning pointer, count, X, call, or relocation')
        width = sum(12-widths[c] for c in text)
        x = 160-width/2
        bits = struct.unpack('>I', struct.pack('>f', x))[0]
        if bits & 65535 or not 40 <= x < x+width <= 280:
            raise ValueError('Complete warning cannot be centred with the native instruction')
        for at, word in ((lo, 0x24A50000 | ((RAM+target) & 65535)),
                         (count, 0x24060000 | len(text)), (x_at, 0x3C070000 | (bits >> 16))):
            struct.pack_into('>I', changed, at, word)
            allowed.update(range(at, at+4))
        records.append({'text': text.decode(), 'offset': target, 'length': len(text),
                        'width': width, 'x': x, 'y': 120+20*len(records),
                        'font_call': f'{RAM+call:08X}'})
    if [row['width'] for row in records] != [108, 123, 93]:
        raise ValueError('Unexpected complete warning widths')
    spec = Image(RAM, len(old), SECTIONS)
    for base in (0x801A0010, 0x802C0010, 0x80400010):
        before = relocate_verified_data(spec, old, reloc, base, memory_end=0x80800000)
        after = relocate_verified_data(spec, bytes(changed), reloc, base, memory_end=0x80800000)
        if any(a != b and at not in allowed for at, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Title warning changes unrelated relocated title code or artwork')
        for text, _, target, hi, lo, count, _, call, _ in ROWS:
            hi, lo, count, call = (at+CODE_BIAS for at in (hi, lo, count, call))
            if (pointer(after, hi, lo) != base+target or after[target:target+len(text)] != text
                    or struct.unpack_from('>I', after, count)[0] != 0x24060000 | len(text)
                    or struct.unpack_from('>I', after, call)[0] != 0x0C024387):
                raise ValueError('Relocated title warning loses complete English')
    return bytes(changed), records


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Title warning requires the exact complete RC6 cartridge')
    files = by_vrom(base)
    code = files[CODE_VROM].extract(base)
    if code[WIDTH_BRANCH:WIDTH_BRANCH+4] != bytes(4):
        raise ValueError('Missing proportional font reader')
    changed, rows = patch_owner(files[OWNER].extract(base), files[RELOC].extract(base),
                               code[WIDTH_TABLE:WIDTH_TABLE+256])
    image = reconstruct(native, base, {OWNER: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Title warning patch reconstruction differs')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'owner_sha256': sha256(changed),
        'source_builder_sha256': sha256(Path(__file__).read_bytes()), 'strings': rows,
        'erase_label': ERASE_TEXT.decode().strip(),
        'translation_source': 'Project translation of N64-only title wording',
        'allocation_changed': False, 'relocation_changed': False, 'controller_detection_changed': False,
        'menu_actions_changed': False, 'saved_format_changed': False, 'save_readers_writers_changed': False,
        'required_ram_bytes': 0x800000, 'prior_rc6_corrections_retained': True,
        'native_rendering_verified': False, 'original_hardware_verified': False,
        'status': 'Complete title warning installed; ordinary appearance pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc6/Animal Forest English V1RC6.z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = checked_output(args.output)
    state = source_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), args.base.read_bytes())
    if state['worktree_modified'] != source_state()['worktree_modified']:
        raise ValueError('Source state changed during title-warning construction')
    report.update(source_revision=revision, worktree_modified=state['worktree_modified'])
    out.mkdir(parents=True, exist_ok=False)
    for name, content in {'animal-forest-title-warning.z64': image, 'animal-forest-title-warning.ups': patch,
                          'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, content)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
