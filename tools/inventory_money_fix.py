"""Fit inventory money digits to their native bubbles without changing the font."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, verified_rom, sha256, make_ups, apply_ups
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = 'e968d09b30f29283086423fe29367026a70ce11a6272947c0cb92865b4b19c74'
VROM, RAM = 0x785700, 0x8087D480
OWNER_SHA = 'c77467381c689b45ac2170cd8a8e2cc0f8675349cc9cd602d0d5322d89439541'
# The five independent calls already advance 12 pixels. Only their horizontal
# size/origin changes. t0 and t2 both originally hold 255: reuse t0 for alpha,
# leaving t2 available for the X scale bits without adding code or a register.
WORDS = {
    0x808802F4: (0x3C0142F4, 0x3C0142F7),  # first slot X: 122 -> 123.5
    0x80880398: (0x240A00FF, 0x3C0A3FA0),  # t2: duplicate 255 -> float 1.25 bits
    0x8088039C: (0xAFAA0020, 0xAFA80020),  # alpha: t2 -> original t0 (255)
    0x808803BC: (0xE7B6002C, 0xAFAA002C),  # X scale: f22 (.75) -> t2 (1.25)
}


def patch_overlay(data, relocation):
    if sha256(data) != OWNER_SHA:
        raise ValueError('Changed current inventory drawing overlay')
    sections = struct.unpack_from('>5I', relocation)
    # Relocations still use native text/data/rodata sections, not a flattened
    # helper layout. No modified instruction may have a relocation record.
    slots = set()
    for row in struct.unpack_from('>'+str(sections[4])+'I', relocation, 20):
        section = row >> 30
        if section not in (1, 2, 3): raise ValueError('Unknown inventory relocation section')
        slots.add(sum(sections[:section-1])+(row & 0xFFFFFF))
    expected = {0x80880390: 0x240800FF, 0x80880394: 0x2409003C,
                0x808803A4: 0xAFA80014, 0x808803A8: 0x24060001,
                0x808803C0: 0xE7B60030, 0x808803C4: 0x0C0243A6,
                0x808803D8: 0x461AA500, 0x80880318: 0x3C014140,
                0x80880320: 0x3C013F40}
    if any(struct.unpack_from('>I', data, at-RAM)[0] != word for at, word in expected.items()):
        raise ValueError('Changed money scale, colour, native slot, or draw contract')
    changed = bytearray(data)
    for at, (old, new) in WORDS.items():
        if at-RAM in slots or struct.unpack_from('>I', data, at-RAM)[0] != old:
            raise ValueError('Changed or relocated inventory money instruction')
        struct.pack_into('>I', changed, at-RAM, new)
    return bytes(changed)


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Inventory money fix requires the combined notice/tune predecessor')
    files = by_vrom(base)
    changed = patch_overlay(files[VROM].extract(base), files[0x7898C0].extract(base))
    image = reconstruct(native, base, {VROM: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Inventory money patch reconstruction failed')
    report = {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
              'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
              'overlay_vrom': f'{VROM:08X}', 'overlay_sha256': sha256(changed),
              'words': {f'{at:08X}': [f'{a:08X}', f'{b:08X}'] for at, (a, b) in WORDS.items()},
              'x_scale': 1.25, 'y_scale': 0.75, 'x_adjustment': 1.5,
              'slot_step_pixels': 12, 'digit_ink_pixels': 6.25, 'previous_digit_ink_pixels': 3.75,
              'rom_bytes': len(image), 'required_ram_bytes': 0x800000,
              'font_changed': False, 'allocation_changed': False, 'save_format_changed': False,
              'fixed_issues': ['V1-12'], 'hardware_retest': 'pending'}
    return image, patch, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1-notice-tune-fix-01')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-inventory-money-fix-01')
    args = parser.parse_args()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                (args.base/'animal-forest-title-preview.z64').read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
