"""Exact classic adapters with independently validated retained font/creator prefixes."""
from copy import deepcopy
import json
import struct

from aflib import sha256
from accent_mail_overlays import Overlay
from build_classic_letters import source_hashes
from npc_mail_show import relocate_verified_data

PROFILES = {
    'font': ('9062cb5f6eaf140b37048a58de15435d40a84ecec346497831678f5dcde15018',
             '62b84f16a8d36f2bd65162844f3826e6541f6878a5f02d64583f2a99ac6b0f42',
             '3c1304a9b3c064e97a92e24bf589a8db0e19df9f6c95cf151e467fd60f09c3e5'),
    'creator': ('30a49c8eee4b80315a1b34802be6b6988946f65573b4f15ee11005df4eab1fd5',
                '9e9bc02396cbec107e50fa5e88f95f8483f672aa6e3dd7b825bc44247f198b5b',
                'e14e2aa2d6594789f0b09fd4bb42de42c6bf1229e0d595345687477673fdfc26'),
}


def wrap(extension):
    result = deepcopy(extension['previous_profile'])
    result.update(bytes=extension['bytes'], relocation_bytes=extension['relocation_bytes'],
                  relocation_sha256=extension['relocation_sha256'], classic_letters=extension)
    result['sha256' if extension['kind'] == 'font' else 'overlay_sha256'] = extension['sha256']
    for name, offset in extension['symbols'].items():
        if name.startswith('af_classic_'):
            result['symbols'][name] = offset
    return result


def validate(kind, data, reloc, report):
    extension = report.get('classic_letters')
    if not isinstance(extension, dict) or kind not in PROFILES:
        raise ValueError('Missing exact classic-letter profile')
    encoded = json.dumps(extension, sort_keys=True, separators=(',', ':')).encode()
    if ((sha256(encoded), sha256(data), sha256(reloc)) != PROFILES[kind]
            or extension.get('sources') != source_hashes() or report != wrap(extension)):
        raise ValueError('Changed approved classic-letter '+kind+' code, sources, or metadata')
    prefix = extension['prefix_bytes']
    original = bytearray(data[:prefix])
    for patch in extension['patches']:
        at = patch['at']
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if len(before) != len(after) or data[at:at+len(after)] != after:
            raise ValueError('Missing classic-letter entry patch')
        original[at:at+len(before)] = before
    original = bytes(original)
    previous_reloc = bytes.fromhex(extension['previous_relocation'])
    if (sha256(original) != extension['previous_sha256']
            or sha256(previous_reloc) != extension['previous_relocation_sha256']):
        raise ValueError('Classic-letter adapter alters its retained prefix')
    old = extension['previous_profile']
    if kind == 'font':
        from extended_font_cartridge import validate as validate_font
        validate_font(original, previous_reloc, old)
    else:
        from accent_mail_overlay_profile import validate as validate_creator
        validate_creator('creator', original, previous_reloc, old)
    spec = Overlay(report['ram'], len(data), struct.unpack_from('>5I', reloc))
    for base in (0x801A0010, 0x802F8010):
        moved = relocate_verified_data(spec, data, reloc, base)
        if kind == 'font':
            from extended_font_cartridge import relocate as relocate_font
            retained = relocate_font(original, previous_reloc, base, mail_literals=True)
            expected_entry = struct.pack('>2I', 0x08000000 | (((base+extension['entry_offset']) >> 2) & 0x3FFFFFF), 0)
            if moved[:8] != expected_entry:
                raise ValueError('Classic-letter startup jump relocates incorrectly')
        else:
            retained = relocate_verified_data(Overlay(report['ram'], prefix, struct.unpack_from('>5I', previous_reloc)),
                                               original, previous_reloc, base)
        first = 8 if kind == 'font' else 0
        if moved[first:prefix] != retained[first:prefix]:
            raise ValueError('Classic-letter relocation alters retained code, glyphs, or mutable state')
    return original, previous_reloc, old
