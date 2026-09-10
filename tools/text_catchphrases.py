"""Pinned display-only canonical fallback for the one ambiguous borrowed key."""
import struct
from aflib import sha256
from build_text_extension import BORROWED_IMPORTS
from runtime_module import MODULE_RAM, MODULE_VROM
from text_choices import RESOURCE_HASHES

CALL = 0x801953C4
PROFILE = {
    'image_bytes': 3808, 'relocation_bytes': 224, 'blob_bytes': 4032, 'loader_bytes': 216,
    'image_sha256': 'c888f311374bf07ae678e690440b298a8fcd40f4c01f27263de40c6f97289950',
    'relocation_sha256': '3c196c9433126a3425aca21725a75422a211ac32e8775885d252cb44bc110eb8',
    'blob_sha256': '988be57c76de3d72435818fe27cd384a6f42366fa52fb6d28031ac0ed7851c96',
    'blob_crc32': 'CC436501',
    'loader_sha256': '4cd298af8b749b2e5773280c1f5b8a5163f5c45a9412e6b21919ea80b195e769',
}
SYMBOLS = {'af_text_extension_init': 0, 'af_text_names_init': 160, 'af_text_choices_init': 320,
    'af_text_fields_init': 556, 'af_borrowed_catchphrase': 828, 'af_identity_name': 1128,
    'af_choice_expand': 1272, 'af_free_set': 2132, 'insert': 2456, 'af_free_copy': 2976,
    'af_free_colour': 3020, 'hook': 3120, 'af_free_item': 3208, 'af_free_item_nonzero': 3304,
    'af_free_item_colour': 3332, 'CSWTCH.36': 3436, 'colours.0': 3448, 'valid': 3472, 'rows': 3476}
ELF_SHA = '1a7c80054918fba5ba507459765222f4ec0a4b9e3a713f87e85df1bc931551f5'


def verify_dependencies(additions, module):
    binary, resource = additions[MODULE_VROM], additions[0x02E00000]
    if (struct.unpack_from('>2I', binary, CALL-MODULE_RAM) != (0x0C065487, 0x02C02025)
            or any(int(module['symbols'].get(name, '0'), 16) != value for name, value in BORROWED_IMPORTS.items())
            or sha256(resource) != RESOURCE_HASHES[0x02E00000]):
        raise ValueError('Changed borrowed-catchphrase getter, caller, or reference resource')
    rows = [resource[i:i+16] for i in range(32, len(resource), 16)]
    matches = [row for row in rows if row[:4] == bytes.fromhex('d0902020')]
    expected = [bytes.fromhex('d0902020e014')+b'zzzzzz    ', bytes.fromhex('d0902020e0c5')+b'bingo     ']
    if matches != expected: raise ValueError('Changed canonical borrowed-catchphrase policy')
    return {'call': f'{CALL:08X}', 'saved_key': 'D0902020', 'canonical_owner': 'E014',
            'canonical_english': 'zzzzzz', 'own_ids_retained': ['E014', 'E0C5'],
            'resource_sha256': sha256(resource), 'new_saved_bytes': 0,
            'policy': 'First native owner for an ambiguous borrowed copy; no donor identity is inferred'}
