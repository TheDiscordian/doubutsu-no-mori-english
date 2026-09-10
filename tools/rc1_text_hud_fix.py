"""Apply V1RC1's reported first-player, currency-unit, and clock-edge fixes."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, make_ups, sha256, verified_rom
from apply_translation import write_new
from artwork_matches import converted, data_pointers
from catalogue_names import Image
from map_artwork import compile_commands
from npc_mail_show import relocate_verified_data
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '5ccd35ba077e3abf1d1ab90d919c095343ff404884b504ca14ea709a04ec1dfc'
HUD = 0xA22000
HUD_SHA = 'eb3717446a97c9970c9e87084ec694908789c618687f8ab639af8886880e4e01'
ACTOR, RELOC, RAM = 0x8A1F10, 0x8A4630, 0x809BE720
ACTOR_SHA = '6b8330a8e19b75ef2a1b36595d5f86674b3e1484b61f6b039f757ef6248957e3'
RELOC_SHA = '4849cecf6ea4058b2cc4c49c4a91bee12d09102cd56c40940e13da50b3076c35'
NEW_ACTOR, NEW_RELOC = 0x3E90000, 0x3EA0000
SECTIONS = (9376, 592, 48, 0, 188)
META = 0x80101950 - CODE_RAM
LABEL = b"I'm new"
SOURCE = ROOT/'overlays/rc1_followup/hud.c'


def reference(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied English follow-up source')
    if (symbols.count(b'new_player_str$706 = .data:0x00071010; // type:object size:0x7 ') != 1
            or rel[DATA_BASE+0x71010:DATA_BASE+0x71017] != LABEL):
        raise ValueError('Changed complete GameCube first-time-player label')
    if symbols.count(b'mny_win_beruT_model = .data:0x008972A0; // type:object size:0x30 ') != 1:
        raise ValueError('Changed GameCube currency-label model')
    pointers = data_pointers(rel)
    if pointers.get(0x8972AC) != 0x8968A0 or pointers.get(0x8972BC) != 0x8971A0:
        raise ValueError('Changed bound currency image or quad')
    if model_texture_shape(rel[DATA_BASE+0x8972A8:DATA_BASE+0x8972B0]) != (32, 16, 4, 0):
        raise ValueError('Changed currency donor dimensions or format')


def patch_hud(bank, rel, compiled):
    if sha256(bank) != HUD_SHA:
        raise ValueError('Changed V1RC1 HUD resource')
    # Keep the exact original load except for clamping both tile axes.
    expected = bytearray(bank[0x2B80:0x2BB8])
    for at in (12, 44):
        before = struct.unpack_from('>I', expected, at)[0]
        if before & 0xC0300:
            raise ValueError('Native clock no longer uses wrapping')
        struct.pack_into('>I', expected, at, before | 0x80200)
    if compiled != bytes(expected):
        raise ValueError('Compiled clock changes more than tile clamping')
    if (bank[0x3510:0x3518] != bytes.fromhex('0400340804003488')
            or bank[0xB408:0xB410] != bytes.fromhex('FD9000000400B7D0')
            or bank[0xB438:0xB448] != bytes.fromhex('F20000000007C03C010040080400B2E0')):
        raise ValueError('Changed AM/PM selection or native currency reader')
    changed = bytearray(bank)
    changed[0x2B80:0x2BB8] = compiled
    changed[0xB7D0:0xB8D0] = converted(rel[DATA_BASE+0x8968A0:DATA_BASE+0x8969A0], 32, 16, 'i4', 4)
    # Native amount placement differs from GC. Retain its unit quad/spacing;
    # donor dimensions and UVs already match, so only its English pixels change.
    return bytes(changed)


def patch_player(actor, reloc):
    if (sha256(actor) != ACTOR_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS or len(actor) != sum(SECTIONS[:3])):
        raise ValueError('Changed player-selector owner or relocation')
    if actor[0x2518:0x251C] != bytes.fromhex('19ED2412'):
        raise ValueError('Changed native first-time-player label')
    changed = bytearray(actor + LABEL + bytes(16-len(LABEL)))
    # Only the source address and explicit copy length change. The existing
    # enlarged choice rows, names, selection branches, and stack remain intact.
    for at, before, after in ((0xC34, 0x24A50C38, 0x24A50E40),
                              (0xC40, 0x24060004, 0x24060007)):
        if struct.unpack_from('>I', actor, at)[0] != before:
            raise ValueError('Changed first-time-player source/copy instruction')
        struct.pack_into('>I', changed, at, after)
    new_rel = bytearray(reloc)
    struct.pack_into('>I', new_rel, 8, SECTIONS[2]+16)
    new_sections = struct.unpack_from('>5I', new_rel)
    for base in (0x80200010, 0x80378010):
        before = relocate_verified_data(Image(RAM, len(actor), SECTIONS), actor, reloc, base)
        after = relocate_verified_data(Image(RAM, len(changed), new_sections), changed, new_rel, base)
        allowed = set(range(0xC34, 0xC38)) | set(range(0xC40, 0xC44))
        if any(a != b and at not in allowed for at, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Player fix changes unrelated relocated code/data')
        hi = struct.unpack_from('>I', after, 0xC30)[0] & 65535
        lo = struct.unpack_from('>h', after, 0xC36)[0]
        if (hi << 16) + lo != base+len(actor) or after[len(actor):len(actor)+7] != LABEL:
            raise ValueError('English label pointer fails at a native load address')
    return bytes(changed), bytes(new_rel)


def build(native, base, rel, symbols, compiled):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Follow-up requires the checked post-V1RC1 notice correction')
    reference(rel, symbols)
    files = by_vrom(base)
    hud = patch_hud(files[HUD].extract(base), rel, compiled)
    actor, reloc = patch_player(files[ACTOR].extract(base), files[RELOC].extract(base))
    code = bytearray(files[CODE_VROM].extract(base))
    if struct.unpack_from('>4I', code, META) != (ACTOR, RELOC, RAM, RAM+10016):
        raise ValueError('Changed player-selector allocation metadata')
    struct.pack_into('>4I', code, META, NEW_ACTOR, NEW_ACTOR+len(actor), RAM, RAM+len(actor))
    changes = {HUD: hud, ACTOR: actor, RELOC: reloc, CODE_VROM: bytes(code)}
    image = reconstruct(native, base, changes, resized=(ACTOR,), moves={ACTOR: NEW_ACTOR, RELOC: NEW_RELOC})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Follow-up patch reconstruction failed')
    return image, patch, {'version': 1, 'baseline_sha256': BASE_SHA, 'source_sha256': sha256(native),
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'sources': {name: sha256((ROOT/name).read_bytes()) for name in
                    ('tools/rc1_text_hud_fix.py', 'overlays/rc1_followup/hud.c')},
        'toolchain_image': IMAGE, 'hud_sha256': sha256(hud), 'player_sha256': sha256(actor),
        'player_relocation_sha256': sha256(reloc), 'player_growth_bytes': 16,
        'player_label': LABEL.decode(), 'player_copy_bytes': len(LABEL),
        'relocation_bases': ['80200010', '80378010'],
        'fixed_issues': ['V1-13', 'V1-15', 'V1-16'], 'keyboard_followup': 'pending',
        'rom_bytes': len(image), 'required_ram_bytes': 0x800000, 'save_format_changed': False,
        'hardware_retest': 'pending', 'ordinary_gameplay_test': 'pending'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=ROOT/'build/v1-shop-notice-fix-03/animal-forest-title-preview.z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1rc1-text-hud-fix-01')
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    commands = compile_commands(args.output/'commands', SOURCE, (('clock', 56),))
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        args.base.read_bytes(), (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), commands['clock'])
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(args.output/name, data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
