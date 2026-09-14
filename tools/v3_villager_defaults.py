"""Verify pilot clothing identities before enabling their native initializers."""
import struct

from aflib import by_vrom, sha256
from gamecube import rarc_files
from v3_villager_art import native_palette, pack4, untile

TEXTURES, PALETTES = 0xB68000, 0xB88000
BRIDGES = (
    (0x800AA1E0, 0x2F40, 'af_v3_get_looks', (0xAFA40000, 0x3084FFFF)),
    (0x800AA29C, 0x2F50, 'af_v3_set_defaults', (0x27BDFFE8, 0xAFA5001C)),
    (0x800AA218, 0x2F60, 'af_v3_set_info', (0x27BDFFE0, 0xAFB00018)),
    (0x800AD8C4, 0x2F70, 'af_v3_set_index', (0x27BDFFD8, 0xAFB00020)),
)


def pixels(texture, palette):
    colours = struct.unpack('>16H', palette)
    return tuple(colours[index] for byte in texture for index in (byte >> 4, byte & 15))


def clothing(native, first, *, all_villagers=False):
    # Metadata's caller verifies both complete sources before calling here.
    files, members = by_vrom(native), dict(rarc_files(first))
    textures, palettes = (files[v].extract(native) for v in (TEXTURES, PALETTES))
    donor_tex, donor_pal = (members['data/' + name + '.bin'] for name in ('tex_boy', 'pallet_boy'))
    if tuple(map(len, (textures, palettes, donor_tex, donor_pal))) != (131072, 8192, 131072, 8192):
        raise ValueError('Changed clothing bank dimensions')
    native_pixels = [pixels(textures[i * 512:(i + 1) * 512], palettes[i * 32:(i + 1) * 32])
                     for i in range(256)]
    result = {}
    reviewed = ((0x2498, 0x2498), (0x24BF, None))
    if all_villagers:
        reviewed = ((0x241A, None), (0x241B, None)) + reviewed
    for item, approved in reviewed:
        i = item - 0x2400
        raw_tex, raw_pal = donor_tex[i * 512:(i + 1) * 512], donor_pal[i * 32:(i + 1) * 32]
        tex, pal = pack4(untile(raw_tex, 32, 32, 4)), native_palette(raw_pal)
        wanted = pixels(tex, pal)
        matches = [0x2400 + j for j, candidate in enumerate(native_pixels) if candidate == wanted]
        if matches != ([] if approved is None else [approved]):
            raise ValueError('Villager clothing identity no longer matches its reviewed mapping')
        result[item] = {'donor_item_id': f'{item:04X}',
            'native_item_id': f'{approved:04X}' if approved is not None else None,
            'status': 'verified_existing_artwork' if approved else 'new_clothing_import_required',
            'donor_texture_sha256': sha256(raw_tex), 'donor_palette_sha256': sha256(raw_pal),
            'converted_texture_sha256': sha256(tex), 'converted_palette_sha256': sha256(pal),
            'compared_pixels': len(wanted), 'native_candidates_checked': len(native_pixels),
            'native_texture_bank_sha256': sha256(textures), 'native_palette_bank_sha256': sha256(palettes)}
    return result


def imported_outfit(blob, text_report, resource, record, row):
    """Bind Punchy's default to the verified additive garment and save profile."""
    from v3_registry import clothing_slot
    item, index, vrom = clothing_slot(0x24BF)
    slots = [r for r in text_report['imports'] if r['actor_id'] == 'E0ED']
    if len(slots) != 1 or len(blob) != 0xC000:
        raise ValueError('Missing complete Punchy metadata')
    target = slots[0]
    at = 0x2C00 + 19 * 32
    before = bytes(blob[at:at+32])
    outfit = target['clothing_identity']
    if (sha256(before) != target['record_sha256'] or before[30:] != bytes(2)
            or before[:4] != bytes.fromhex('E0ED24BF') or target['initial_defaults_applied']
            or len(resource) != 544 or len(record) != 32
            or sha256(resource[:512]) != outfit['converted_texture_sha256']
            or sha256(resource[512:]) != outfit['converted_palette_sha256']
            or struct.unpack_from('>HHI', record) != (item, index, vrom)
            or record[10:12] != b'\x01\x00' or record[28:] != bytes(4)
            or row['resource_sha256'] != sha256(resource)
            or row['metadata_sha256'] != sha256(record)
            or not blob[0x20 + 160 + (item & 255)//8] & (1 << (item & 7))):
        raise ValueError('Punchy default lacks its complete selected clothing dependency')
    struct.pack_into('>H', blob, at+30, item)
    target.update({'clothing_applied': True, 'initial_defaults_applied': True,
                   'applied_clothing_id': f'{item:04X}', 'record_sha256': sha256(blob[at:at+32])})
    return {'actor_id': 'E0ED', 'donor_clothing_id': '24BF', 'applied_clothing_id': f'{item:04X}',
            'metadata_ram': f'{0x80460000+at:08X}', 'before_sha256': sha256(before),
            'after_sha256': target['record_sha256'], 'resource_sha256': sha256(resource),
            'move_in_enabled': False}
