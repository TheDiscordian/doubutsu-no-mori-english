"""Complete native player/save gamestate labels while preserving save actions."""
import argparse
import json
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, verified_rom, sha256, make_ups, apply_ups
from apply_translation import write_new
from catalogue_names import Image
from font import WIDTH_TABLE, WIDTH_BRANCH
from npc_mail_show import relocate_verified_data
from rebuild_v1 import checked_output, source_state
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '614e387ee7591d935c091852512f7a60dc181fe25892843a2458c70a69e87037'
WIDTH_SHA = '74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1'
PARTS = {
    'player': (0x747AA0, 0x7485F0, 0x80828830, (2768, 112, 16, 0, 52),
               'bdd45166ed747e6efa385447ed4e68d899f91dbe16c8b1b82330dbf61b40070e',
               '86aa882cd20c8c65be56f66da19e8105002aef91fd7df65a8264a9808982041a'),
    'save': (0x7486E0, 0x749200, 0x80829470, (2560, 256, 32, 0, 50),
             '258e442cc2368b9039dcde039fd7faa8ca879c7bbffb74b95a4257bda7faf9cb',
             '9e0a053b4042d63d637acd5ccd558b32bc75fe348427884bb05e2fbe61e573a7'),
}
SOURCE_FILES = {
    'upstream/af/src/overlays/gamestates/ovl_player_select/player_select.c':
        'bd19474ef4bc4119e12dedc315ef072363538eb74fcac4be61253eb3875dbf0e',
    'upstream/af/src/overlays/gamestates/ovl_save_menu/save_menu.c':
        'cbc4ca7b3dfc0a051a5980ee2b72c972df8c28e368302268334a3613e97ca984',
}
TEXT = {
    'player': (
        (0x80829300, bytes.fromhex('201f1302c00700003ce7010bca1110ca023e00003cec010f0710ca023e000000600e057b000ef715060f0000'),
         b'Select a player<Away>    <Home>   Visitor   '),
        (0x80829358, bytes.fromhex('e4ba90b490200dc30f070000'), b'Unregistered'),
        (0x80829364, bytes.fromhex('edca0215c320202000000000'), b'Resident   \0'),
    ),
    'save': (
        (0x80829F0C, bytes.fromhex(
            '9e90df20b2a68d9050757368204120427574746f6e00000053656c656374205220427574746f6e00'
            '50757368204220427574746f6e20746f2045584954000000466c617368526f6d20159e90df'
            'e28f9820159e90df202020202000000000000000000000'),
         b'Save Menu\0\0\0Push A Button\0\0\0Select R Button\0Push B Button to EXIT\0\0\0'
         b'Save to FlashRAMSave to Pak\0\0\0\0\0'),
    ),
}
WORDS = {
    'player': (
        (0x80828C50, 0x24A59358, 0x24A59300), (0x80828C58, 0x2406000A, 0x2406000F),
        # Retain a complete prefix pointer rather than copying eight characters.
        (0x80828CE8, 0x8DF90000, 0xAFAF00BC), (0x80828CEC, 0x8DF80004, 0),
        (0x80828D04, 0xADD90000, 0), (0x80828D08, 0xADD80004, 0),
        (0x80828D34, 0x27B200A4, 0x27B200A0), (0x80828D3C, 0x24050018, 0x2405001B),
        (0x80828D54, 0x27A500BC, 0x8FA500BC), (0x80828D60, 0x24070008, 0x2407000B),
        (0x80828D6C, 0xA3AA00AA, 0xA3AA00A9), (0x80828DA8, 0x24060018, 0x2406001B),
        # Twelve-byte unregistered label, followed by four spaces in the same row.
        (0x80829088, 0x24A59306, 0x24A59364), (0x80829098, 0x26280006, 0x2628000C),
        (0x808290A8, 0x24639300, 0x24639358), (0x808290D0, 0x24040008, 0x2404000C),
        (0x808290D4, 0x24E20008, 0x24E2000C),
        (0x80829180, 0x24A59314, 0x24A59319), (0x80829190, 0x24A59308, 0x24A5930F),
        (0x808291F8, 0x2484932A, 0x2484932C), (0x808291FC, 0x24639320, 0x24639322),
    ),
    'save': (
        # The nine-byte heading is read directly from its existing owner.
        (0x80829834, 0x8DF90000, 0xAFAF004C), (0x80829838, 0x8DF80004, 0),
        (0x8082983C, 0x27AE004C, 0), (0x80829840, 0xADD90000, 0), (0x80829844, 0xADD80004, 0),
        (0x8082989C, 0x27A5004C, 0x8FA5004C), (0x808298A0, 0x24060008, 0x24060009),
        (0x808298F0, 0x25EF9F14, 0x25EF9F18), (0x808299C0, 0x25EF9F24, 0x25EF9F28),
        (0x80829A90, 0x25EF9F34, 0x25EF9F38), (0x80829B74, 0x25EF9F4C, 0x25EF9F50),
        # The same stack frame has room for both complete choices and padding.
        (0x80829BA8, 0x95F90018, 0x8DF90018), (0x80829BB4, 0xA5D90018, 0xADD90018),
        (0x80829BF4, 0x2406000D, 0x24060010), (0x80829C70, 0x27A5005D, 0x27A50060),
        (0x80829C74, 0x2406000D, 0x2406000B),
    ),
}
# Existing HI/LO pairs and their complete intended targets after the repack.
POINTERS = {
    'player': ((0x80828C1C, 0x80828C50, 0x80829300), (0x80828CD8, 0x80828CDC, 0x80829364),
               (0x80829078, 0x80829088, 0x80829364), (0x808290A4, 0x808290A8, 0x80829358),
               (0x8082917C, 0x80829180, 0x80829319), (0x8082918C, 0x80829190, 0x8082930F),
               (0x808291F0, 0x808291FC, 0x80829322), (0x808291F4, 0x808291F8, 0x8082932C)),
    'save': ((0x8082982C, 0x80829830, 0x80829F0C), (0x808298EC, 0x808298F0, 0x80829F18),
             (0x808299BC, 0x808299C0, 0x80829F28), (0x80829A8C, 0x80829A90, 0x80829F38),
             (0x80829B70, 0x80829B74, 0x80829F50)),
}
METADATA = bytes.fromhex(
    '0000000000747aa0007485f0808288308082938000000000808290148082900800000000000000000000000000000288'
    '00000000007486e0007492008082947080829f900000000080829dc080829db400000000000000000000000000000230')


def pointer(data, hi, lo):
    return ((struct.unpack_from('>I', data, hi)[0] & 65535) << 16) + struct.unpack_from('>h', data, lo+2)[0]


def patch_owner(name, old, reloc):
    _, _, ram, sections, owner_sha, reloc_sha = PARTS[name]
    if (sha256(old) != owner_sha or sha256(reloc) != reloc_sha
            or struct.unpack_from('>5I', reloc) != sections):
        raise ValueError('Changed native gamestate owner or relocation')
    changed, allowed = bytearray(old), set()
    for address, before, after in TEXT[name]:
        at = address-ram
        if len(before) != len(after) or old[at:at+len(before)] != before:
            raise ValueError('Changed gamestate label storage or incomplete replacement')
        changed[at:at+len(before)] = after
        allowed.update(range(at, at+len(before)))
    for address, before, after in WORDS[name]:
        at = address-ram
        if struct.unpack_from('>I', old, at)[0] != before or any(i in allowed for i in range(at, at+4)):
            raise ValueError('Changed or overlapping gamestate reader instruction')
        struct.pack_into('>I', changed, at, after)
        allowed.update(range(at, at+4))
    entries = set(struct.unpack_from('>'+str(sections[4])+'I', reloc, 20))
    for hi, lo, target in POINTERS[name]:
        if (not {0x45000000 | (hi-ram), 0x46000000 | (lo-ram)} <= entries
                or pointer(changed, hi-ram, lo-ram) != target):
            raise ValueError('Missing original pointer relocation or wrong complete text target')
    for base in (0x801A0010, 0x802F8010, 0x803D0010):
        spec = Image(ram, len(old), sections)
        before = relocate_verified_data(spec, old, reloc, base)
        after = relocate_verified_data(spec, bytes(changed), reloc, base)
        if any(a != b and at not in allowed for at, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Gamestate text changes unrelated relocated code or data')
        for hi, lo, target in POINTERS[name]:
            if pointer(after, hi-ram, lo-ram) != base+target-ram:
                raise ValueError('Relocated gamestate reader selects wrong text')
    return bytes(changed)


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Gamestate labels require the exact committed title-warning baseline')
    if any(sha256((ROOT/name).read_bytes()) != digest for name, digest in SOURCE_FILES.items()):
        raise ValueError('Changed native gamestate source definitions')
    files = by_vrom(base)
    code = files[CODE_VROM].extract(base)
    if (code[WIDTH_BRANCH:WIDTH_BRANCH+4] != bytes(4)
            or sha256(code[WIDTH_TABLE:WIDTH_TABLE+256]) != WIDTH_SHA
            or code[0x80106F40-CODE_RAM:0x80106FA0-CODE_RAM] != METADATA):
        raise ValueError('Changed gamestate metadata or installed font')
    changes = {v: patch_owner(name, files[v].extract(base), files[r].extract(base))
               for name, (v, r, *_rest) in PARTS.items()}
    image = reconstruct(native, base, changes)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Gamestate text patch reconstruction differs')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'source_builder_sha256': sha256(Path(__file__).read_bytes()), 'source_definitions': SOURCE_FILES,
        'changed_files': {f'{v:08X}': sha256(data) for v, data in changes.items()},
        'labels': ['Unregistered', '<Away>', '<Home>', 'Visitor', 'Select a player', 'Resident {native slot} ',
                   'Save Menu', 'Save to FlashRAM', 'Save to Pak'],
        'allocation_changed': False, 'relocation_changed': False, 'stack_frames_changed': False,
        'menu_access_changed': False, 'menu_actions_changed': False, 'saved_format_changed': False,
        'save_readers_writers_changed': False, 'saved_names_changed': False,
        'required_ram_bytes': 0x800000, 'prior_title_warning_and_rc6_corrections_retained': True,
        'ordinary_reachability_verified': False, 'native_rendering_verified': False, 'original_hardware_verified': False,
        'status': 'Complete native gamestate labels installed; appearance/access acceptance pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/title-warning-text-01/animal-forest-title-warning.z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = checked_output(args.output)
    state = source_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), args.base.read_bytes())
    if state['worktree_modified'] != source_state()['worktree_modified']:
        raise ValueError('Source state changed during gamestate text construction')
    report.update(source_revision=revision, worktree_modified=state['worktree_modified'])
    out.mkdir(parents=True, exist_ok=False)
    for name, content in {'animal-forest-gamestate-text.z64': image, 'animal-forest-gamestate-text.ups': patch,
                          'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, content)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
