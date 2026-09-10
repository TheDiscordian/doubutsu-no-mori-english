"""Pinned identity-name variant of the complete persistent text extension."""
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from build_text_extension import IDENTITY_IMPORTS

BRIDGE = 0x800BB708
PROFILE = {
    'image_bytes': 3344, 'relocation_bytes': 224, 'blob_bytes': 3568, 'loader_bytes': 216,
    'image_sha256': 'c6a333db09027b9a2602128b0a3057e6066e27734accc336dad9585e3aa1f787',
    'relocation_sha256': 'cf1cc52fd82413740d075137b88072ad4e704f294585678a2c5269a3ae67241b',
    'blob_sha256': '59b483326e2edd9ec49d820eb167c675371d788eae04ec1ad61c8281d9811e1e',
    'blob_crc32': 'B5DCF6F5',
    'loader_sha256': '9f58e4f6794c9659babefcbe1619c8613d30ab94f182aaadbb68426c64259244',
}
SYMBOLS = {'af_text_extension_init': 0, 'af_text_choices_init': 160, 'af_text_fields_init': 396,
    'af_identity_name': 668, 'af_choice_expand': 812, 'af_free_set': 1672, 'insert': 1996,
    'af_free_copy': 2516, 'af_free_colour': 2560, 'hook': 2660, 'af_free_item': 2748,
    'af_free_item_nonzero': 2844, 'af_free_item_colour': 2872, 'CSWTCH.36': 2976,
    'colours.0': 2988, 'valid': 3008, 'rows': 3012}
ELF_SHA = '6597d1e490063ae83d0fda0f07a0fbf1f6c4ba939338593ba9bc4e9c6f6c4ac2'


def verify_dependencies(native, replacements, module):
    original = by_vrom(native)[CODE_VROM].extract(native); code = replacements[CODE_VROM]
    if (code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM] != original[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM]
            or code[BRIDGE-CODE_RAM:BRIDGE-CODE_RAM+8] != bytes.fromhex('27a4001c0c0259d0')
            or int(module['symbols'].get('af_load_display_name', '0'), 16) != IDENTITY_IMPORTS['af_load_display_name']):
        raise ValueError('Changed identity display fallback or bridge')
    return {'bridge': f'{BRIDGE:08X}', 'name_bytes': 8, 'native_name_bytes': 6,
            'valid_ids': ['E000', 'E0D7'], 'saved_layout_changes': False}


def bridge_profile(blob):
    from text_catchphrases import PROFILE as borrowed_profile
    return {p['blob_sha256']: p for p in (PROFILE, borrowed_profile)}.get(sha256(blob))


def verify_installed_bridge(built):
    # Layered secret-letter verification has only its own report. Bind the
    # complete startup variant directly; the whole-build verifier checks sources.
    from text_extension import VROM, SETTER
    files = by_vrom(built); code = files[CODE_VROM].extract(built)
    profile = bridge_profile(files[VROM].extract(built)) if VROM in files else None
    if (profile is None
            or sha256(code[SETTER-CODE_RAM:SETTER-CODE_RAM+profile['loader_bytes']]) != profile['loader_sha256']):
        raise ValueError('Conversation name reader lacks its complete startup bridge')
