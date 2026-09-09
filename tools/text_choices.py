"""Approved bounded choice-extension profile and its installed dependencies."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from build_text_extension import CHOICE_IMPORTS
from english_runtime import (ChoiceLayout, GuardedCode, SOURCE_HASHES, QUEST_VROM, PLAYER_SELECT_VROM,
                             make_english_runtime, verify_english_runtime)
from runtime_module import DATE_CALLS, MODULE_VROM, module_command_info
from shop_item_names import jump

ENTRY, END = 0x80065CF8, 0x80065D90
ACTOR_VROMS = (QUEST_VROM, PLAYER_SELECT_VROM)
RESOURCE_HASHES = {
    0x02C00000: '261078b6c8bec7f974255ddffba8c2a570b4a2a0526ea699a3cc62ffc2b4e974',
    0x02E00000: '6af738a7c89ce7fea041897efd8c4f95d85732d32cd3de1a3f99aeca5163f675',
}
PROFILE = {
    'image_bytes': 3040, 'relocation_bytes': 208, 'blob_bytes': 3248, 'loader_bytes': 216,
    'image_sha256': 'bf6f1a6b7d665dc0a3435c607f9325f2f5fac9794ea009f2917756e87723069d',
    'relocation_sha256': '2e6a6bfd924319be6c3edd35193ee27be9fb01117b2f6817758e8207d54755e4',
    'blob_sha256': '8619a986156563d210eb093ba09b17b2113cb33d4b236d14f4e202cf11230ebd',
    'blob_crc32': '3F82DFAB',
    'loader_sha256': '3adffb6605041192e135fa11d11b8f5162f5d1795fc54db65ce336f831b91b77',
}
SYMBOLS = {'af_text_extension_init': 0, 'af_text_fields_init': 236, 'af_choice_expand': 508,
    'af_free_set': 1368, 'insert': 1692, 'af_free_copy': 2212, 'af_free_colour': 2256,
    'hook': 2356, 'af_free_item': 2444, 'af_free_item_nonzero': 2540,
    'af_free_item_colour': 2568, 'CSWTCH.36': 2672, 'colours.0': 2684,
    'valid': 2704, 'rows': 2708}
ELF_SHA = '09311dc5594e1572795e439bf8ee4c8330e35021f1329c2229652af204181b16'


def verify_dependencies(native, replacements, additions, module):
    layout = ChoiceLayout(20, 32, 0x8019A840, 0x8019A8C0)
    verify_english_runtime(native, replacements, layout)
    binary = additions[MODULE_VROM]
    if (struct.unpack_from('>4I', binary, 40) != (20, 32, layout.rows, layout.selected)
            or any(int(module['symbols'].get(name, '0'), 16) != value
                   for name, value in CHOICE_IMPORTS.items())):
        raise ValueError('Choice extension requires the complete resident layout and imports')
    for offset, vrom in ((60, 0x02C00000), (64, 0x02E00000)):
        if (struct.unpack_from('>I', binary, offset)[0] != vrom
                or sha256(additions.get(vrom, b'')) != RESOURCE_HASHES[vrom]):
            raise ValueError('Choice extension requires the approved full name and catchphrase resources')
    # Bind legacy output bounds to native helpers with only approved English
    # layout, town-suffix, and date-call patches, not arbitrary current bytes.
    expected, _ = make_english_runtime(native, {}, layout)
    original = by_vrom(native)[CODE_VROM].extract(native)
    guarded = GuardedCode(original, expected[CODE_VROM], CODE_RAM, SOURCE_HASHES[CODE_VROM])
    guarded.grow_stack(0x8009EF00, 0x8009EF88, 56, 0x34, growth=8)
    guarded.grow_stack(0x8009EF88, 0x8009F010, 56, 0x34, growth=8)
    expected = guarded.data
    for address, _, symbol in DATE_CALLS:
        struct.pack_into('>I', expected, address-CODE_RAM,
                         jump(int(module['symbols'][symbol], 16), link=True))
    code = replacements[CODE_VROM]
    spans = ((0x80065668, END), (0x80102A80, 0x80102C04),
             (0x8009EC88, 0x8009ED14), (0x8009EE78, 0x8009F230),
             (0x8009F428, 0x8009F4A4), (0x8009F50C, 0x8009F5B4))
    for start, end in spans:
        if code[start-CODE_RAM:end-CODE_RAM] != expected[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError(f'Changed choice formatter dependency at {start:08X}')
    info = module_command_info(native)
    for command in range(0x1A, 0x40):
        if info[command][0] != 2:
            raise ValueError('Choice substitution is not a two-byte command')
    return {'entry': f'{ENTRY:08X}', 'capacity': 20, 'temporary_bytes': 32,
            'source_sha256': sha256(original[ENTRY-CODE_RAM:END-CODE_RAM]),
            'legacy_dependencies': {f'{start:08X}': sha256(code[start-CODE_RAM:end-CODE_RAM])
                                    for start, end in spans},
            'resources': {f'{v:08X}': h for v, h in RESOURCE_HASHES.items()},
            'imports': CHOICE_IMPORTS, 'saved_layout_changes': False,
            'failure': 'No destination writes; native random-number state is not rolled back'}
